import os

from . import integrated_test


def test_c_memory(tmpdir, capfd, build_test):
    binary_name = "CtestMemory"
    binary_path = os.path.join(integrated_test.dmtcp_plugin_test_bin_dir,
                               binary_name)

    cmd = ["run", "-w", str(tmpdir), binary_path]
    ret = integrated_test.run_cragon_cli(cmd)

    assert ret.returncode == 0
    record_file = integrated_test.get_intercepted_log_path(tmpdir)
    assert os.path.isfile(record_file)
    with open(record_file) as f:
        # no memory error is found
        s = f.read()
    assert s == ""


def test_bad_memory_call(tmpdir, capfd, build_test):
    "Check all the failed memory call should be intercepted"

    """
    dmtcp_launch --with-plugin libcragon_exeinfo.so bin/BadMemoryCall
    Set RLIMIT_DATA to 20971520 bytes.
    LOGGING_FD_ENV_VAR is empty! Log to stdout.
    40000,40000:mmap,12,0xffffffffffffffff,(nil),41943040,3,34,-1,0 # plugin
    mmap,12,0xffffffffffffffff,(nil),41943040,3,34,-1,0 # expected
    40000,40000:mremap,12,0xffffffffffffffff,0x7fd3b2025000,4096,41943040,1
    mremap,12,0xffffffffffffffff,0x7fd3b2025000,4096,41943040,1
    """

    binary_name = "BadMemoryCall"
    binary_path = os.path.join(integrated_test.dmtcp_plugin_test_bin_dir,
                               binary_name)

    cmd = ["run", "-w", str(tmpdir), binary_path]
    ret = integrated_test.run_cragon_cli(cmd)

    assert ret.returncode == 0
    record_file = integrated_test.get_intercepted_log_path(tmpdir)
    assert os.path.isfile(record_file)

    with open(record_file) as f:
        intercepted = f.read()

    out = capfd.readouterr().out
    expected = [i for i in out.split("\n")[1:] if i]
    intercepted = [i.split(":")[1] for i in intercepted.split("\n") if i]
    assert expected == intercepted
