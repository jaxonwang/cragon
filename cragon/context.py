import os
import getpass
import socket
from utils import ERROR

dmtcp_path = None
dmtcp_launch = None
dmtcp_command = None
dmtcp_plugins = None

tmp_dir = None

dmtcp_plugin_name = "libcragon_exeinfo.so"
cragon_lib_dirname = "lib"

file_date_format = '%Y-%m-%d_%H:%M:%S'

cwd = os.getcwd()
working_dir = None
image_dir_name = "checkpoint_images"
image_dir = None

current_host_name = None
current_user_name = None

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class StartUpCheckError(RuntimeError):
    "Raise when fatal error during start up check"
    pass


def check_failed(msg):
    ERROR(msg)
    raise StartUpCheckError(msg)


def check():
    global dmtcp_plugins, image_dir
    dmtcp_plugin_dir = os.path.join(ROOT_DIR, cragon_lib_dirname)
    dmtcp_plugin_path = os.path.join(dmtcp_plugin_dir, dmtcp_plugin_name)
    if not os.path.isfile(dmtcp_plugin_path):
        check_failed("Plugin: {} doesn't exist.".format(dmtcp_plugin_path))
    dmtcp_plugins = dmtcp_plugin_path

    # check working directory
    os.path.isdir(working_dir)
    image_dir = os.path.join(working_dir, image_dir_name)

    # check user and hostname
    global current_host_name, current_user_name
    current_host_name = socket.gethostname()
    current_user_name = getpass.getuser()
