#include <iostream>
#include <atomic>
#include <dlfcn.h>
#include "dmtcp.h"

static void *handle = nullptr;

#define CALL_REAL(func)  \
({\
    static __typeof(&func) _real_ ## func = nullptr;\
    if(! _real_ ## func){\
        if (!handle) {\
            handle = dlopen("libc.so.6", RTLD_NOW);\
        }\
        _real_ ## func = (__typeof__( _real_ ## func))dlsym(handle, # func);\
    }\
    _real_ ## func;\
 })

#define _EXTC extern "C"

using namespace std;

static __thread atomic_flag trapped = ATOMIC_FLAG_INIT;

inline bool first_trapped(){
    return false;
}
_EXTC void *mmap(void *addr, size_t length, int prot, int flags,
                  int fd, off_t offset){
    // if not trap{
    //     trap
    //     dobefore;
    //     funccall;
    //     doafter;
    //     untrap
    //
    // }else{
    //     return funccall;
    // }
    cout << "call mmap "<< addr << " " << length << " " << prot << " " << flags << " " <<fd << " " <<offset
        << endl;
    void *ret = CALL_REAL(mmap)(addr, length, prot, flags, fd, offset);
    // cout << "return: " << ret;
    return ret;
}

