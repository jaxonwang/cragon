import os

from . import integrated_test


def test_checkpoint_pi_estimation(tmpdir, capfd):
    binary_path = os.path.join(
        integrated_test.test_cases_dir,
        "checkpoint",
        "pi_est.py")

    cmd = ["-w", str(tmpdir), "python", binary_path, "100000"]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode == 0

    out, err = capfd.readouterr()
    pi = float(out.strip())
    assert pi < 3.2 and pi > 3.1
