import pytest
import os
import subprocess

from . import integrated_test


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # copied from pytest doc
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="session")
def build_test():
    print("Compiling test binaries")
    p = subprocess.run(["make", "-C", integrated_test.dmtcp_plugin_test_dir])
    p.check_returncode()
    p = subprocess.run(["make", "-C", integrated_test.checkpoint_test_dir])
    p.check_returncode()
    return None


@pytest.fixture(scope="function")
def print_log_if_fail(request, tmpdir):
    yield
    if request.node.rep_call.failed:
        print("*****"*10 + " " + str(request.node.name) + " log " + "*****"*10)
        log_path = integrated_test.get_cragon_log_path(tmpdir)
        if not os.path.isfile(log_path):
            return
        with open(log_path, "r") as f:
            print(f.read())


@pytest.fixture(scope="session")
def image_prepare(tmpdir_factory):
    fn = tmpdir_factory.mktemp("checkpoint_test")
    interval = 0.02
    working_dir = str(fn)
    binary_path = os.path.join(
        integrated_test.checkpoint_bin_dir, "PiEst")

    cmd = ["run", "-i", str(interval), "-w", working_dir, binary_path,
           "800000"]
    p = subprocess.run(["cragon"] + cmd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    assert p.returncode == 0
    assert not p.stderr
    integrated_test.assert_nothing_intercepted(working_dir)
    return str(fn), p.stdout.decode("ascii")
