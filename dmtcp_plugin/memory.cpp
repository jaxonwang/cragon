#include "dmtcp.h"
#include <atomic>

#include <cerrno>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <climits>
#include <dlfcn.h>
#include <unistd.h>

#include <sys/mman.h>
#include <sys/time.h>

using namespace std;

static atomic<void *> handle{nullptr};

#define CALL_REAL(func)                                                        \
  ({                                                                           \
    static __typeof(&func) _real_##func = nullptr;                             \
    if (!_real_##func) {                                                       \
      if (!handle.load()) {                                                    \
        handle.store(dlopen("libc.so.6", RTLD_NOW));                           \
      }                                                                        \
      _real_##func = (__typeof__(_real_##func))dlsym(handle.load(), #func);    \
    }                                                                          \
    _real_##func;                                                              \
  })

#define _EXTC extern "C"

static __thread atomic_flag trapped = ATOMIC_FLAG_INIT;

const char *LOGGING_FD_ENV_VAR = "DMTCP_PLUGIN_EXEINFO";

ssize_t _stderr(const char *s){
  return write(STDERR_FILENO, s, strlen(s));
}

void _perror(const char *s, int errnum) {
  const size_t PERROR_BUF_SIZE = 512;
  static char perrbuf[PERROR_BUF_SIZE];

  const size_t len = strlen(s);
  strncpy(perrbuf, s, PERROR_BUF_SIZE); // will pad zeros to back
  snprintf(perrbuf + len, PERROR_BUF_SIZE - len, " errono: %d\n", errnum);
  _stderr(perrbuf);
}

int get_logging_fd(){
    static int logging_fd = -1;
    if(logging_fd == -1){
        char * evar = secure_getenv(LOGGING_FD_ENV_VAR);
        if(!evar){
            _stderr("LOGGING_FD_ENV_VAR is empty! Log to stdout.\n");
            logging_fd = STDOUT_FILENO;
        }
        errno = 0;
        long int fd_temp = strtol(evar, NULL, 10);
        if( fd_temp <0 || fd_temp > INT_MAX ){
            _stderr("Bad LOGGING_FD_ENV_VAR! Log to stdout.\n");
            logging_fd = STDOUT_FILENO;
        }
        logging_fd = fd_temp;
    }
    return logging_fd;
}

inline ssize_t _write(int fd, const void *buf, size_t len) {
  ssize_t ret, nr;
  ssize_t total = 0;
  while (len != 0 && (ret = write(fd, buf, len)) != 0) {
    total += ret;
    if (ret == -1) {
      if (errno == EINTR) {
        total++;
        continue;
      }
      _perror("write", errno);
      goto stop;
    }
  }
  ret = total;
stop:
  return ret;
}

void log(int level, const char * s){
    _write(get_logging_fd(), s, strlen(s));
}

inline bool first_trapped() { return false; }
_EXTC void *mmap(void *addr, size_t length, int prot, int flags, int fd,
                 off_t offset) {
  void *ret;
  int stored_errno;
  if (!trapped.test_and_set()) {
    ret = CALL_REAL(mmap)(addr, length, prot, flags, fd, offset);
    stored_errno = errno;
    // log(1, "hajhhsdafdsafsda");
    _write(1, "sdaf\n", 5);
    if (errno != 0) {
      if (ret == MAP_FAILED)
        perror("mall");
    }
    errno = stored_errno;
    trapped.clear();

  } else {
    ret = CALL_REAL(mmap)(addr, length, prot, flags, fd, offset);
  }
  return ret;
}
