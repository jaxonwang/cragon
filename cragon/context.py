import os
from utils import ERROR

dmtcp_path = None
dmtcp_launch = None
dmtcp_command = None

dmtcp_plugins = None

dmtcp_plugin_name = "libcragon_exeinfo.so"
cragon_lib_dirname = "lib"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class StartUpCheckError(RuntimeError):
    "Raise when fatal error during start up check"
    pass


def check_failed(msg):
    ERROR(msg)
    raise StartUpCheckError(msg)


def check():
    global dmtcp_plugins
    dmtcp_plugin_dir = os.path.join(ROOT_DIR, cragon_lib_dirname)
    dmtcp_plugin_path = os.path.join(dmtcp_plugin_dir, dmtcp_plugin_name)
    if not os.path.isfile(dmtcp_plugin_path):
        check_failed("Plugin: {} doesn't exist.".format(dmtcp_plugin_path))
    dmtcp_plugins = dmtcp_plugin_path
