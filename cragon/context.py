import os
import json
import getpass
import socket

from cragon.algorithms import Periodic
from cragon import images

dmtcp_path = None
dmtcp_launch = None
dmtcp_command = None
dmtcp_plugins = None
dmtcp_restart = None

dmtcp_launch_file_name = "dmtcp_launch"
dmtcp_command_file_name = "dmtcp_command"
dmtcp_restart_file_name = "dmtcp_restart"

tmp_dir = None

dmtcp_plugin_name = "libcragon_exeinfo.so"
cragon_lib_dirname = "lib"

file_date_format = '%Y-%m-%d_%H:%M:%S'

cwd = os.getcwd()
working_dir = None
image_dir_name = "checkpoint_images"
image_dir = None
log_file_name = "cragon.log"
intercepted_log_name = "intercepted.log"
ckpt_info_file_name = "checkpoint_info"

current_host_name = None
current_user_name = None

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

ckpt_intervals = 60
ckpt_algorihtm = None

image_to_restart = None
fifo_path = None  # guarenteed to be absolute
# fifo need to restored exactly as last execution, will be init if
# restart from ckpt in restart_check TODO: should I use another flag to
# indicate is restart?

# these tmp files will be deleted reversily whe system tear down
# this should not be access by multiple thread
tmp_file_created = []

# the checkpoint info of last run
last_ckpt_info = None


class StartUpCheckError(RuntimeError):
    "Raise when fatal error during start up check"
    pass


def check_failed(msg):
    raise StartUpCheckError(msg)


def check():
    global dmtcp_plugins, image_dir, ckpt_algorihtm, ckpt_intervals
    global dmtcp_launch, dmtcp_command

    # check dmtcp binary path
    dmtcp_launch = os.path.join(dmtcp_path, dmtcp_launch_file_name)
    dmtcp_command = os.path.join(dmtcp_path, dmtcp_command_file_name)

    # check plugin exist
    if not dmtcp_plugins:
        dmtcp_plugin_dir = os.path.join(ROOT_DIR, cragon_lib_dirname)
        dmtcp_plugin_path = os.path.join(dmtcp_plugin_dir, dmtcp_plugin_name)
        dmtcp_plugins = dmtcp_plugin_path
    if not os.path.isfile(dmtcp_plugins):
        check_failed("Plugin: {} doesn't exist.".format(dmtcp_plugin_path))

    # check working directory
    if not os.path.isdir(working_dir):
        raise RuntimeError(
            "The working directory: %s does not exist." %
            working_dir)
    if not image_dir:
        image_dir = os.path.join(working_dir, image_dir_name)

    # check user and hostname
    global current_host_name, current_user_name
    current_host_name = socket.gethostname()
    current_user_name = getpass.getuser()

    # check algorithms
    if ckpt_intervals:
        ckpt_algorihtm = Periodic

    if not ckpt_algorihtm:
        check_failed("Should at least specity a ckpt algorithm or intervals.")
    if ckpt_algorihtm is Periodic:
        if not ckpt_intervals:
            check_failed(
                "Periodic checkpoint should specify intervals option.")


def ckpt_info_check(ckpt_image_dir):
    global last_ckpt_info

    ckpt_info_file_path = os.path.join(ckpt_image_dir, ckpt_info_file_name)
    if not os.path.isfile(ckpt_info_file_path):
        check_failed("The checkpoint info file: %s is missing" %
                     ckpt_info_file_path)
    with open(ckpt_info_file_path, "r") as f:
        last_ckpt_info = json.load(f)

    global fifo_path
    fifo_path = last_ckpt_info["data"]["fifo_path"]
    # should be cleaned from last execution
    if os.path.exists(fifo_path):
        check_failed("Fifo file %s exist." % fifo_path)


def restart_check():
    global image_to_restart, dmtcp_restart

    # dmtcp restart binary
    dmtcp_restart = os.path.join(dmtcp_path, dmtcp_restart_file_name)

    image_dir = images.latest_image_dir()
    ckpt_info_check(image_dir)
    image_to_restart = images.latest_image()
    if not image_to_restart:
        check_failed("The images to restart can not be found.")
