import signal
import ctypes
import sys


def c_strsignal(signum):
    libc = ctypes.cdll.LoadLibrary("libc.so.6")
    c_signum = ctypes.c_int(signum)
    libc.strsignal.restype = ctypes.c_char_p
    ret = libc.strsignal(c_signum)
    return ret.decode("ascii")


strsignal = None

if sys.version_info.minor >= 8:
    strsignal = signal.strsignal
else:
    strsignal = c_strsignal
