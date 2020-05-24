import pytest
import subprocess

from . import integrated_test


@pytest.fixture(scope="module")
def build_test():
    p = subprocess.run(["make", "-C", integrated_test.dmtcp_plugin_test_path])
    p.check_returncode()
