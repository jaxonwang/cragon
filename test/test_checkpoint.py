import os

from . import integrated_test


def test_checkpoint_pi_estimation_py_no_checkpoint(tmpdir, capfd):
    binary_path = os.path.join(
        integrated_test.test_cases_dir,
        "checkpoint",
        "pi_est.py")

    cmd = ["run", "-w", str(tmpdir), "python", binary_path, "100000"]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode == 0

    out, err = capfd.readouterr()
    pi = float(out.strip())
    assert pi < 3.2 and pi > 3.1


def test_checkpoint_pi_estimation_no_checkpoint(tmpdir, capfd):
    binary_path = os.path.join(
        integrated_test.checkpoint_bin_dir, "PiEst")

    cmd = ["run", "-w", str(tmpdir), binary_path, "1000000"]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode == 0

    out, err = capfd.readouterr()
    pi = float(out.strip())
    assert pi < 3.2 and pi > 3.1


def test_checkpoint_pi_estimation(tmpdir, capfd):
    interval = 0.03
    working_dir = str(tmpdir)
    binary_path = os.path.join(
        integrated_test.checkpoint_bin_dir, "PiEst")

    cmd = ["run", "-i", str(interval), "-w", working_dir, binary_path,
           "500000"]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode == 0
    integrated_test.assert_nothing_intercepted(working_dir)

    pi1, err = capfd.readouterr()

    # check the output from restart is the same
    ret = integrated_test.restart_latest(working_dir)
    assert ret.returncode == 0
    integrated_test.assert_nothing_intercepted(working_dir)

    pi2, err = capfd.readouterr()

    assert pi1 == pi2
