import pytest
import subprocess

from . import integrated_test


@pytest.fixture(scope="session")
def build_test():
    print("Compiling test binaries")
    p = subprocess.run(["make", "-C", integrated_test.dmtcp_plugin_test_dir])
    p.check_returncode()
    return None
