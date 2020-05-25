import os

from . import integrated_test


def test_c_memory(tmpdir, capfd, build_test):
    binary_name = "CtestMemory"
    binary_path = os.path.join(integrated_test.dmtcp_plugin_test_bin_dir,
                               binary_name)

    cmd = ["-w", str(tmpdir), binary_path]
    ret = integrated_test.run_cragon_cli(cmd)

    assert ret.returncode == 0
    record_file = integrated_test.get_intercepted_log_path(tmpdir)
    assert os.path.isfile(record_file)
    with open(record_file) as f:
        # no memory error is found
        s = f.read()
    assert s == ""
