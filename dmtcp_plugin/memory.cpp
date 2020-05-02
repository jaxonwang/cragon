#include "dmtcp.h"
#include <atomic>

#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <unistd.h>

#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <sys/types.h>

using namespace std;

static atomic<void *> handle{nullptr};

#define _EXTC extern "C"

const int LOG_BUF_SIZE = 256;

static thread_local atomic_flag trapped = ATOMIC_FLAG_INIT;

const char *LOGGING_FD_ENV_VAR = "DMTCP_PLUGIN_EXEINFO";

ssize_t _stderr(const char *s) { return write(STDERR_FILENO, s, strlen(s)); }

void _perror(const char *s, int errnum) {
  const size_t PERROR_BUF_SIZE = 512;
  static char perrbuf[PERROR_BUF_SIZE];

  const size_t len = strlen(s);
  strncpy(perrbuf, s, PERROR_BUF_SIZE); // will pad zeros to back
  snprintf(perrbuf + len, PERROR_BUF_SIZE - len, " errono: %d\n", errnum);
  _stderr(perrbuf);
}

int get_logging_fd() {
  static int logging_fd = -1;
  if (logging_fd == -1) {
    char *evar = secure_getenv(LOGGING_FD_ENV_VAR);
    if (!evar) {
      _stderr("LOGGING_FD_ENV_VAR is empty! Log to stdout.\n");
      logging_fd = STDOUT_FILENO;
      return logging_fd;
    }
    errno = 0;
    int fd_temp = strtol(evar, NULL, 10);
    if (fd_temp < 0 || fd_temp > INT_MAX) {
      _stderr("Bad LOGGING_FD_ENV_VAR! Log to stdout.\n");
      logging_fd = STDOUT_FILENO;
    }
    logging_fd = fd_temp;
  }
  return logging_fd;
}

inline ssize_t _write(int fd, const void *buf, size_t len) {
  ssize_t ret;
  ssize_t _len = len;
  while (_len != 0 && (ret = write(fd, buf, len)) != 0) {
    if (ret == -1) {
      if (errno == EINTR) {
        continue;
      }
      _perror("write", errno);
      goto stop;
    }
    _len -= ret;
  }
  ret = len;
stop:
  return ret;
}

static int min_log_level = 0;

void log(int level, const char *s) {
  if (level < min_log_level) {
    return;
  }
  const int BUFSIZE = 512;
  char buf[BUFSIZE] = {0};

  char *buf_ptr = buf;
  int re = BUFSIZE;

  pid_t tid = syscall(SYS_gettid);
  snprintf(buf_ptr, re, "%d,%d:%s\n", getpid(), tid, s);

  int lg_fd = get_logging_fd();

  static atomic_flag logging_lock = ATOMIC_FLAG_INIT;
  while (logging_lock.test_and_set())
    ; // spin
  _write(lg_fd, buf, strlen(buf));
  logging_lock.clear();
}

void mmap_log(int errnum, void *ret, void *addr, size_t length, int prot,
              int flags, int fd, off_t offset) {
  char buf[LOG_BUF_SIZE] = {0};
  snprintf(buf, LOG_BUF_SIZE, "%d,mmap,%p,%p,%lu,%d,%d,%d,%ld", errnum, ret,
           addr, length, prot, flags, fd, offset);
  log(1, buf);
}

_EXTC void *mmap(void *addr, size_t length, int prot, int flags, int fd,
                 off_t offset) {
  void *ret;
  if (!trapped.test_and_set()) {
    ret = NEXT_FNC(mmap)(addr, length, prot, flags, fd, offset);
    int stored_errno = errno;

    mmap_log(stored_errno, ret, addr, length, prot, flags, fd, offset);
    if (ret == MAP_FAILED) {
      perror("mall");
    }

    errno = stored_errno;
    trapped.clear();

  } else {
    ret = NEXT_FNC(mmap)(addr, length, prot, flags, fd, offset);
  }
  return ret;
}

void brk_log(int errnum, int ret, void *addr) {
  char buf[LOG_BUF_SIZE] = {0};
  snprintf(buf, LOG_BUF_SIZE, "%d,brk,%d,%p", errnum, ret, addr);
  log(1, buf);
}

_EXTC int brk(void *addr) {
  int ret;
  if (!trapped.test_and_set()) {
    ret = NEXT_FNC(brk)(addr);
    int stored_errno = errno;
    brk_log(stored_errno, ret, addr);

    if (ret == -1) {
      perror("mall");
    }
    errno = stored_errno;

    trapped.clear();
  } else {
    ret = NEXT_FNC(brk)(addr);
  }
  return ret;
}

void sbrk_log(int errnum, void *ret, intptr_t increment) {
  char buf[LOG_BUF_SIZE] = {0};
  snprintf(buf, LOG_BUF_SIZE, "%d,sbrk,%p,%ld", errnum, ret, increment);
  log(1, buf);
}

_EXTC void *sbrk(intptr_t increment) {
  void *ret;
  if (!trapped.test_and_set()) {
    ret = NEXT_FNC(sbrk)(increment);
    int stored_errno = errno;
    sbrk_log(stored_errno, ret, increment);

    if (ret == (void *)-1) {
      perror("mall");
    }
    errno = stored_errno;

    trapped.clear();
  } else {
    ret = NEXT_FNC(sbrk)(increment);
  }
  return ret;
}

void malloc_log(int errnum, void *ret, size_t size) {
  char buf[LOG_BUF_SIZE] = {0};
  snprintf(buf, LOG_BUF_SIZE, "%d,malloc,%p,%ld", errnum, ret, size);
  log(1, buf);
}

_EXTC void *malloc(size_t size) {
  void *ret;
  if (!trapped.test_and_set()) {
    ret = NEXT_FNC(malloc)(size);
    int stored_errno = errno;
    malloc_log(stored_errno, ret, size);

    if (ret == NULL) {
      perror("mall");
    }
    errno = stored_errno;
    trapped.clear();
  } else {
    ret = NEXT_FNC(malloc)(size);
  }
  return ret;
}

void calloc_log(int errnum, void * ret, size_t nmemb,size_t size){
  char buf[LOG_BUF_SIZE] = {0};
  snprintf(buf, LOG_BUF_SIZE, "%d,calloc,%p,%ld, %ld", errnum, ret,
  nmemb,size); log(1, buf);
}

_EXTC void *calloc(size_t nmemb, size_t size){
  void *ret;
  if (!trapped.test_and_set()) {
    ret = NEXT_FNC(calloc)(nmemb, size);
    int stored_errno = errno;
    calloc_log(stored_errno, ret, nmemb, size);

    if (ret == NULL) {
      perror("mall");
    }
    errno = stored_errno;
    trapped.clear();
  } else {
    ret = NEXT_FNC(calloc)(nmemb, size);
  }
  return ret;
}

void realloc_log(int errnum, void * ret, void * ptr,size_t size){
  char buf[LOG_BUF_SIZE] = {0};
  snprintf(buf, LOG_BUF_SIZE, "%d,realloc,%p,%p, %ld", errnum, ret,
  ptr,size); log(1, buf);
}

_EXTC void *realloc(void * ptr, size_t size){
  void *ret;
  if (!trapped.test_and_set()) {
    ret = NEXT_FNC(realloc)(ptr, size);
    int stored_errno = errno;
    realloc_log(stored_errno, ret, ptr, size);

    if (ret == NULL) {
      perror("mall");
    }
    errno = stored_errno;
    trapped.clear();
  } else {
    ret = NEXT_FNC(realloc)(ptr, size);
  }
  return ret;
}

// static void eventHook(DmtcpEvent_t event, DmtcpEventData_t *data) {
//   switch (event) {
//   case DMTCP_EVENT_INIT:
//       if(!handle.load()){
//         handle.store(dlopen("libc.so.6", RTLD_NOW));                        
//       }
//     break;
//   }
// }
//
// DmtcpPluginDescriptor_t exeinfo_plugin = {
//     DMTCP_PLUGIN_API_VERSION,
//     DMTCP_PACKAGE_VERSION,
//     "exeinfo",
//     "JX Wang",
//     "jxwang92@gmail.com",
//     "Get execution info by wrapping glibc calls",
//     eventHook};
//
// DMTCP_DECL_PLUGIN(exeinfo_plugin);
