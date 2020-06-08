
from cragon import signals


def test_strsingal():
    cases = {1: 'Hangup',
             2: 'Interrupt',
             3: 'Quit',
             4: 'Illegal instruction',
             5: 'Trace/breakpoint trap',
             6: 'Aborted',
             7: 'Bus error',
             8: 'Floating point exception',
             9: 'Killed',
             10: 'User defined signal 1',
             11: 'Segmentation fault',
             12: 'User defined signal 2',
             13: 'Broken pipe',
             14: 'Alarm clock',
             15: 'Terminated',
             16: 'Stack fault',
             17: 'Child exited',
             18: 'Continued',
             19: 'Stopped (signal)'}

    for k, v in cases.items():
        assert v == signals.strsignal(k)
