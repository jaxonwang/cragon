import unittest
import os

from . import integrated_test

from cragon import execution
from cragon import context


class TestC(unittest.TestCase):
    binary_name = "CtestMemory"
    binary_path = os.path.join(integrated_test.dmtcp_plugin_test_bin,
                               binary_name)

    def test_run(self):
        with execution.FirstRun([self.binary_path]) as r:
            r.run()

        record_file = os.path.join(context.working_dir, "intercepted.log")
        with open(record_file) as f:
            print(f.read())


test_cases = (TestC,)


def setUpModule():
    integrated_test.env_set_up()


def tearDownModule():
    integrated_test.env_tear_down()
