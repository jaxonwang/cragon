import click
import pathlib
import os
import sys

from cragon import utils
from cragon import context
from cragon import execution
from cragon import checkpoint_manager


def bad_args_exit(err_msg):
    click.echo(err_msg, err=True)
    sys.exit(2)


dmtcp_file_check = [
    context.dmtcp_launch_file_name,
    context.dmtcp_command_file_name,
    context.dmtcp_restart_file_name]

example_str = \
    """
Examples:

    To start a command:
        cragon command arg1 arg2 arg3 ...
    To restart from the latest checkpoint in Cragon working directory:
        cragon -w cragon_command_YYYY-mm-dd_HH:MM:SS/
    To restart from a specific checkpoint:
        cragon cragon_working_dir/{ckpt_dir_name}/id_user@host/
""".format(ckpt_dir_name=context.ckpt_dir_name)


@click.group()
def cli(**args):
    "Checkpoint and restore tool."


@click.option('-p', '--dmtcp-path', type=click.Path(exists=True),
              help="DMTCP binary path")
@click.option('-i', '--intervals', type=click.FLOAT,
              help=("Time in second(s) between checkpoints"
                    " in the naive checkpoint algorithm."))
def common_options(f):
    # hack to reuse options
    param_list = common_options.__click_params__
    if isinstance(f, click.Command):
        f.params += param_list
    else:
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        f.__click_params__ += param_list
    return f

def check_dmtcp_path(dmtcp_path):
    dmtcp_path = dmtcp_path
    if not dmtcp_path:
        dmtcp_path = os.path.join(context.ROOT_DIR, "bin")
    dmtcp_path = os.path.abspath(dmtcp_path)

    files_to_check = [os.path.join(dmtcp_path, f)
                      for f in dmtcp_file_check]
    for f in files_to_check:
        if not os.path.isfile(f):
            if not dmtcp_path:
                bad_args_exit(
                    "File: {} not found. Please specify --dmtcp-path PATH.".format(f))
            else:
                bad_args_exit("File: {} not found.".format(f))
    context.dmtcp_path = dmtcp_path

@cli.command()
@click.option('-w', '--working-directory', type=click.Path(exists=True),
              help=("Cragon working directory where"
                    " checkpoint images and logs are stored. If not specified,"
                    "Cragon will create a new directory in current working "
                    "directory"))
@click.argument('command', nargs=1, required=True)
@click.argument('args', nargs=-1)
@common_options
def run(**args):
    "Run the command to be automatically checkpointed."

    check_dmtcp_path(args["dmtcp_path"])

    # get commands to execute
    command = [args["command"]] + list(args["args"])
    context.command = command

    # check working directory
    if not args["working_directory"]:
        cmd_basename = utils.get_command_basename(args["command"])
        context.create_working_directory_in_cwd(cmd_basename)
    else:
        context.working_dir = args["working_directory"]

    # check ckpt algorihtms
    if args["intervals"]:
        context.ckpt_intervals = float(args["intervals"])

    execution.start_all(is_restart=False)

@cli.command()
@click.option('-w', '--working-directory', type=click.Path(exists=True),
              help=("Cragon working directory where"
                    " checkpoint images and logs are stored. If not given "
                    "images, Cragon will find the latest checkpoint in the "
                    "working directory to restart"))
@click.argument('image_dir', nargs=1, required=False,
                type=click.Path(exists=True))
@common_options
def restart(**args):
    "Restart from a chekpoint."

    check_dmtcp_path(args["dmtcp_path"])

    image_dir = args["image_dir"]
    wdir = args["working_directory"]
    # check working directory
    if not image_dir and not wdir:
        bad_args_exit(("Please working directory or checkpoint directory "
                 "from which Cragon start."))
    elif not wdir:
        # check image to restart, and fetch the commands to create wdir
        if not context.check_image_directory_legal(image_dir):
            bad_args_exit("%s doesn't seem to be a Cragon image directory." %
                        wdir)

        # check whether image is in cragon working directory
        p = str(pathlib.Path(image_dir).parent.parent.absolute())
        if not context.check_working_directory_legal(p):
            context.load_last_ckpt_info(image_dir)
            cmd_basename = utils.get_command_basename(
                context.last_ckpt_info["command"])
            context.create_working_directory_in_cwd(cmd_basename)
        else:
            context.working_dir = p
        context.image_dir_to_restart = image_dir
    else:
        # find latest
        if not context.check_working_directory_legal(wdir):
            bad_args_exit("%s doesn't seem to be a Cragon working directoy." %
                        wdir)
        context.working_dir=wdir

    # check ckpt algorihtms
    if args["intervals"]:
        context.ckpt_intervals = float(args["intervals"])

    execution.start_all(is_restart=True)

if __name__ == '__main__':
    cli()
