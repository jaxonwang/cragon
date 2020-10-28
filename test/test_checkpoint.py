import os
import hashlib

from cragon import checkpoint_manager

from . import integrated_test


def test_checkpoint_pi_estimation_py_no_checkpoint(tmpdir, capfd,
                                                   print_log_if_fail):
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


def test_checkpoint_pi_estimation_no_checkpoint(tmpdir, capfd, build_test,
                                                print_log_if_fail):
    binary_path = os.path.join(
        integrated_test.checkpoint_bin_dir, "PiEst")

    cmd = ["run", "-w", str(tmpdir), binary_path, "1000000"]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode == 0

    out, _ = capfd.readouterr()
    pi = float(out.strip())
    assert pi < 3.2 and pi > 3.1


def test_checkpoint_pi_estimation(capfd, build_test,
                                  print_log_if_fail, image_prepare):

    # check the output from restart is the same
    working_dir, pi1 = image_prepare
    ret = integrated_test.restart_latest(working_dir)
    assert ret.returncode == 0
    integrated_test.assert_nothing_intercepted(working_dir)

    pi2, _ = capfd.readouterr()

    assert pi1 == pi2


def test_restart_from_specific_iamge(capfd, build_test, print_log_if_fail,
                                     image_prepare):

    wdir, pi1 = image_prepare
    ckpt_dir = integrated_test.get_ckpt_dir(wdir)
    images = checkpoint_manager.images_in_dir(ckpt_dir)
    assert len(images) >= 1

    cmd = ["restart", os.path.join(ckpt_dir, images[0])]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode == 0
    integrated_test.assert_nothing_intercepted(wdir)

    pi2, err = capfd.readouterr()

    assert pi1 == pi2


def test_seg_fault(tmpdir, capfd, build_test, print_log_if_fail):
    working_dir = str(tmpdir)
    binary_path = os.path.join(
        integrated_test.checkpoint_bin_dir, "SegFault")
    cmd = ["run", "-w", working_dir, binary_path]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode != 0

    _, err = capfd.readouterr()
    assert err == "Process recevied signal: Segmentation fault\n"


# ckpt when writing is not implemented
"""
def test_huge_append(tmpdir, build_test, print_log_if_fail):
    working_dir = os.path.join(str(tmpdir), "happ")
    os.mkdir(working_dir)
    binary_path = os.path.join(
        integrated_test.checkpoint_bin_dir, "HugeAppend")
    filename = os.path.join(working_dir, "hugeappend")
    cmd = ["run", "-i", "1", "-w", working_dir, binary_path, filename]
    ret = integrated_test.run_cragon_cli_kill_after(cmd, 2)
    assert ret.returncode != 0

    sha256 = "809fb596ba861cc3b0ebc7b09519be2a8f4fb9ecc81bdef6dc5a0f65038247ec"

    def filesha(fn):
        m = hashlib.sha256()
        with open(fn, "rb") as f:
            m.update(f.read())
        return m.hexdigest()

    # incomplete run
    assert filesha(filename) != sha256

    cmd = ["restart", "-w", working_dir]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode == 0

    import pdb;pdb.set_trace()
    # restart get correct output
    assert filesha(filename) == sha256
"""
