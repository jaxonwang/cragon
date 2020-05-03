#include "dmtcp.h"
#include <atomic>
#include <type_traits>

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

#define _EXTC extern "C"

const int LOG_BUF_SIZE = 256;

static thread_local atomic_flag trapped = ATOMIC_FLAG_INIT;

const char *LOGGING_FD_ENV_VAR = "DMTCP_PLUGIN_EXEINFO";
const char LOGGING_FIELD_SEPERATOR = ',';

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
      return ret;
    }
    _len -= ret;
  }
  return len;
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
#ifdef DEBUG
#define CREATE_WRAPPER(func_name, ret_type, args, arg_names...)                \
  _EXTC ret_type func_name args {                                              \
    if (trapped.test_and_set()) {                                              \
      return NEXT_FNC(func_name)(arg_names);                                   \
    }                                                                          \
    ret_type ret;                                                              \
    ret = NEXT_FNC(func_name)(arg_names);                                      \
    int stored_errno = errno;                                                  \
    log_call("DEBUG", #func_name, stored_errno, ret,                          \
             arg_names); /* log all calls */                                   \
    after_##func_name(stored_errno, ret, arg_names);                           \
    errno = stored_errno;                                                      \
    trapped.clear();                                                           \
    return ret;                                                                \
  }
#else
#define CREATE_WRAPPER(func_name, ret_type, args, arg_names...)                \
  _EXTC ret_type func_name args {                                              \
    if (trapped.test_and_set()) {                                              \
      return NEXT_FNC(func_name)(arg_names);                                   \
    }                                                                          \
    ret_type ret;                                                              \
    ret = NEXT_FNC(func_name)(arg_names);                                      \
    int stored_errno = errno;                                                  \
    after_##func_name(stored_errno, ret, arg_names);                           \
    errno = stored_errno;                                                      \
    trapped.clear();                                                           \
    return ret;                                                                \
  }
#endif

template <class T> const char *get_format() {
  static_assert(!is_same<T, T>::value, "Not able to fomart this type.");
  return "";
}

template <> const char *get_format<int>() { return "%d"; }
template <> const char *get_format<char *>() { return "%s"; }
template <> const char *get_format<const char *>() { return "%s"; }
template <> const char *get_format<void *>() { return "%p"; }
template <> const char *get_format<long>() { return "%ld"; }
template <> const char *get_format<long long>() { return "%lld"; }
template <> const char *get_format<unsigned long>() { return "%lu"; }

inline void _arg_format(char *, int) {}

template <class Arg, class... Args>
inline void _arg_format(char *buf, int bufsize, Arg first, Args... args) {
  const char *format = get_format<Arg>();
  snprintf(buf, bufsize, format, first);
  int len = strlen(buf);
  buf += len;
  bufsize -= len;
  if (sizeof...(args) != 0) {
    *buf++ = LOGGING_FIELD_SEPERATOR;
    bufsize--;
  }
  _arg_format(buf, bufsize, args...);
}

template <class... Args> inline void log_call(Args... args) {
  char buf[LOG_BUF_SIZE] = {0};
  _arg_format(buf, LOG_BUF_SIZE - 1, args...);
  log(1, buf);
}

void after_mmap(int errnum, void *ret, void *addr, size_t length, int prot,
                int flags, int fd, off_t offset) {
  if (ret == (void *)-1) {
    log_call("mmap", errnum, ret, addr, length, prot, flags, fd, offset);
  }
}

CREATE_WRAPPER(mmap, void *,
               (void *addr, size_t length, int prot, int flags, int fd,
                off_t offset),
               addr, length, prot, flags, fd, offset)

void after_brk(int errnum, int ret, void *addr) {
  if (ret == -1) {
    log_call("brk", errnum, ret, addr);
  }
}

CREATE_WRAPPER(brk, int, (void *addr), addr)

void after_sbrk(int errnum, void *ret, intptr_t increment) {
  if (ret == (void *)-1) {
    log_call("sbrk", errnum, ret, increment);
  }
}

CREATE_WRAPPER(sbrk, void *, (intptr_t increment), increment)

inline void after_malloc(int errnum, void *ret, size_t size) {
  if (ret == NULL) {
    log_call("malloc", errnum, ret, size);
  }
}

CREATE_WRAPPER(malloc, void *, (size_t size), size)

inline void after_calloc(int errnum, void *ret, size_t nmemb, size_t size) {
  if (ret == NULL) {
    log_call("calloc", errnum, ret, nmemb, size);
  }
}

CREATE_WRAPPER(calloc, void *, (size_t nmemb, size_t size), nmemb, size)

void after_realloc(int errnum, void *ret, void *ptr, size_t size) {
  if (ret == NULL) {
    log_call("realloc", errnum, ret, ptr, size);
  }
}

CREATE_WRAPPER(realloc, void *, (void *ptr, size_t size), ptr, size)

void after_reallocarray(int errnum, void *ret, void *ptr, size_t nmemb,
                        size_t size) {
  if (ret == NULL) {
    log_call("reallocarray", errnum, ret, ptr, nmemb, size);
  }
}
CREATE_WRAPPER(reallocarray, void *, (void *ptr, size_t nmemb, size_t size),
               ptr, nmemb, size)

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
