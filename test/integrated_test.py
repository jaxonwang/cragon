import tempfile
import os
import shutil

from pathlib import Path

from cragon import context
from cragon import execution


test_dir = None
test_working_dir = None
project_dir = str(Path(context.ROOT_DIR).parent.absolute())
dmtcp_path = os.path.join(project_dir, "dmtcp/bin")
dmtcp_plugin_path = os.path.join(
    project_dir,
    "dmtcp_plugin")

dmtcp_plugins = os.path.join(dmtcp_plugin_path,
                             context.dmtcp_plugin_name)

dmtcp_plugin_test_path = os.path.join(dmtcp_plugin_path, "test")
dmtcp_plugin_test_bin = os.path.join(dmtcp_plugin_test_path, "bin")


def compile_test_cases():
    os.system("make -C " + dmtcp_plugin_test_path)


def env_set_up():
    global test_dir, test_working_dir
    global dmtcp_path, dmtcp_plugins
    # make test dir
    test_dir = tempfile.mkdtemp()

    # compile everything
    compile_test_cases()

    # set dmtcp_path and dmtcp exes
    context.dmtcp_path = dmtcp_path
    dmtcp_launch_file_name = "dmtcp_launch"
    dmtcp_command_file_name = "dmtcp_command"
    context.dmtcp_launch = os.path.join(dmtcp_path, dmtcp_launch_file_name)
    context.dmtcp_command = os.path.join(dmtcp_path, dmtcp_command_file_name)

    # set dmtcp_plugins in context
    context.dmtcp_plugins = dmtcp_plugins

    # make working dir
    test_working_dir = os.path.join(test_dir, "workingdir")
    os.mkdir(test_working_dir)

    # set working dir in context
    context.working_dir = test_working_dir

    context.check()
    execution.system_set_up()


def env_tear_down():
    execution.system_tear_down()

    shutil.rmtree(test_working_dir)
    os.rmdir(test_dir)
