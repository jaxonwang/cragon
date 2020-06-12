import os
import subprocess

from pathlib import Path

from cragon import context


test_cases_dir = str(Path(__file__).parent.absolute())
dmtcp_plugin_test_dir = os.path.join(test_cases_dir, "dmtcp_plugin")
dmtcp_plugin_test_bin_dir = os.path.join(dmtcp_plugin_test_dir, "bin")

checkpoint_test_dir = os.path.join(test_cases_dir, "checkpoint")
checkpoint_bin_dir = os.path.join(checkpoint_test_dir, "bin")

project_dir = str(Path(context.ROOT_DIR).parent.absolute())
dmtcp_path = os.path.join(project_dir, "dmtcp/bin")
dmtcp_plugin_path = os.path.join(
    project_dir,
    "dmtcp_plugin")

dmtcp_plugins = os.path.join(dmtcp_plugin_path,
                             context.dmtcp_plugin_name)


def run_cragon_cli(args):
    p = subprocess.run(["cragon"] + args)
    return p


def get_intercepted_log_path(working_dir):
    return os.path.join(str(working_dir), context.intercepted_log_name)


def get_cragon_log_path(working_dir):
    return os.path.join(str(working_dir), context.log_file_name)


def get_ckpt_image_dir(working_dir):
    return os.path.join(str(working_dir), context.log_file_name)


def assert_nothing_intercepted(working_dir):
    with open(get_intercepted_log_path(working_dir)) as f:
        assert f.read() == ""


def restart_latest(working_dir):
    cmd = ["restart", "-w", working_dir]
    return run_cragon_cli(cmd)


def get_metrics_log_path(record_dir):
    return os.path.join(record_dir, context.metrics_file_name)
