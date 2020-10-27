import time

from cragon import algorithms
from cragon import context


def test_ckpt_estimation():
    p = algorithms.Periodic(None, None, 10)
    p.update_estimation(1)
    assert p.sckpt == 1
    assert p.ckptvar == 1 / 2
    p.update_estimation(2)
    p.update_estimation(3)
    p.update_estimation(4)
    p.update_interval()
    assert p.sckpt > 3.752 and p.sckpt < 3.753
    assert p.ckptvar < 1.23 and p.ckptvar > 1.21


def test_ckpt_approching():
    stored = context.execution_walltime
    p = algorithms.Periodic(None, None, 5)
    try:
        p.update_estimation(1)
        p.update_estimation(1)
        p.update_estimation(1)
        p.update_interval()
        assert p.interval == 9  # ckpt_time / (interval + ckpt_time) == 0.1

        p = algorithms.Periodic(None, None, 1)
        context.execution_walltime = time.time() + 2
        p.update_estimation(0.1)
        p.update_estimation(0.1)
        p.update_estimation(0.1)
        time.sleep(0.5)
        p.update_estimation(0.1)
        p.update_interval()
        # remain time > interval, no change
        assert p.interval == 1
        # remain time < interval
        time.sleep(0.6)
        p.update_estimation(0.1)
        p.update_interval()
        # interval changes
        assert p.interval != 1
        assert p.interval + 0.1 < context.execution_walltime - time.time()

        i = p.interval
        time.sleep(0.8)
        p.update_estimation(0.1)
        p.update_interval()
        # time remain too small, no change
        assert i == p.interval

    finally:
        context.execution_walltime = stored
