import os
import json
import datetime
import getpass
import socket

from cragon.algorithms import Periodic
from cragon import checkpoint_manager

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

file_date_format = '%Y-%m-%d_%H:%M:%S,%f'

cwd = os.getcwd()
working_dir = None
ckpt_dir_name = "checkpoint_images"
ckpt_dir = None
log_file_name = "cragon.log"
intercepted_log_name = "intercepted.log"
ckpt_info_file_name = "checkpoint_info"

current_host_name = None
current_user_name = None

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

ckpt_intervals = 60
ckpt_algorihtm = None

command = None
image_dir_to_restart = None
images_to_restart = None
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


def check_working_directory_legal(wdir):
    # check if a existing working directory is created by cragon
    if not os.path.isdir(wdir):
        return False
    checkpoint_dir = os.path.join(wdir, ckpt_dir_name)
    if not os.path.isdir(checkpoint_dir):
        return False
    cragon_log_file = os.path.join(wdir, log_file_name)
    if not os.path.isfile(cragon_log_file):
        return False
    return True


def check_image_directory_legal(idir):
    if not checkpoint_manager.image_files_in_dir(idir):
        return False
    if not os.path.isfile(os.path.join(idir, ckpt_info_file_name)):
        return False
    return True


def create_working_directory_in_cwd(command):
    global working_dir
    date_str = datetime.datetime.now().strftime(file_date_format)
    # get the correct command file
    cmdname = os.path.basename(command)
    working_dir = os.path.join(
        cwd, "cragon_{}_{}".format(cmdname, date_str))
    os.mkdir(working_dir)


def check():
    global dmtcp_plugins, ckpt_dir, ckpt_algorihtm, ckpt_intervals
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
        # existance has been checked in cli module
        raise RuntimeError(
            "The working directory: %s does not exist." %
            working_dir)
    if not ckpt_dir:
        ckpt_dir = os.path.join(working_dir, ckpt_dir_name)

    # check user and hostname
    global current_host_name, current_user_name
    current_host_name = socket.gethostname()
    current_user_name = getpass.getuser()

    # check algorithms
    if ckpt_intervals:
        ckpt_algorihtm = Periodic

    # TODO move to cli check when more algorithms are introduced in the future
    if not ckpt_algorihtm:
        check_failed("Should at least specity a ckpt algorithm or intervals.")
    if ckpt_algorihtm is Periodic:
        if not ckpt_intervals:
            check_failed(
                "Periodic checkpoint should specify intervals option.")


def load_last_ckpt_info(ckpt_image_dir):
    global last_ckpt_info
    ckpt_info_file_path = os.path.join(ckpt_image_dir, ckpt_info_file_name)
    if not os.path.isfile(ckpt_info_file_path):
        check_failed(("Can not find checkpoint info file: %s."
                      " Did you give correct --working-directory"
                      " or image directory to restart?") %
                     ckpt_info_file_path)
    with open(ckpt_info_file_path, "r") as f:
        last_ckpt_info = json.load(f)


def ckpt_info_check(ckpt_image_dir):
    global last_ckpt_info, command, fifo_path
    if not last_ckpt_info:
        load_last_ckpt_info(ckpt_image_dir)
    fifo_path = last_ckpt_info["data"]["fifo_path"]

    # should be cleaned from last execution
    if os.path.exists(fifo_path):
        check_failed("Fifo file %s exists." % fifo_path)

    # record the command
    command = last_ckpt_info["command"]


def restart_check():
    global images_to_restart, dmtcp_restart, image_dir_to_restart

    bad_working_dir_s = \
        ("The images to restart can not be found. Did you give correct"
         "--working-directory or image directory to restart?")

    # dmtcp restart binary
    dmtcp_restart = os.path.join(dmtcp_path, dmtcp_restart_file_name)

    if not image_dir_to_restart:
        image_dir_to_restart = checkpoint_manager.latest_image_dir()
    if not image_dir_to_restart:
        check_failed(bad_working_dir_s)
    ckpt_info_check(image_dir_to_restart)
    images_to_restart = checkpoint_manager.\
        image_files_in_dir(image_dir_to_restart)
    if not images_to_restart:
        check_failed(bad_working_dir_s)
