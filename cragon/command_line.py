import click
import datetime
import os
import sys

from cragon import context
from cragon import execution


def err_exit(err_msg):
    click.echo(err_msg, err=True)
    sys.exit(2)


dmtcp_file_check = [
    context.dmtcp_launch_file_name,
    context.dmtcp_command_file_name,
    context.dmtcp_restart_file_name]


@click.command()
@click.option('-p', '--dmtcp-path', type=click.Path(exists=True),
              help="DMTCP binary path")
@click.option('-i', '--intervals', type=click.FLOAT,
              help=("Time in second(s) between checkpoints"
                    " in the naive checkpoint algorithm."))
@click.option('-r', '--restart', is_flag=True, default=False,
              help=("If specified, cragon will rerun from current directory or"
                    " working directory specified in -w/--working-directory"))
@click.option('-w', '--working-directory', type=click.Path(exists=True),
              help=("cragon working directory where"
                    " checkpoint images and logs are stored"))
@click.argument('commands', nargs=-1)
def cli(**args):
    "Checkpoint and restore tool."

    is_restart = args["restart"]

    # check execution path
    dmtcp_path = args["dmtcp_path"]
    if not dmtcp_path:
        dmtcp_path = os.path.join(context.ROOT_DIR, "bin")
    dmtcp_path = os.path.abspath(dmtcp_path)

    files_to_check = [os.path.join(dmtcp_path, f)
                      for f in dmtcp_file_check]
    for f in files_to_check:
        if not os.path.isfile(f):
            if not args["dmtcp_path"]:
                err_exit(
                    "File: {} not found. Please specify --dmtcp-path PATH.".format(f))
            else:
                err_exit("File: {} not found.".format(f))
    context.dmtcp_path = dmtcp_path

    # get commands to execute
    commands = args["commands"]
    if not is_restart and not commands:
        err_exit("Please specify command to run, or start with checkpoint directory")

    # check working directory
    if is_restart and not args["working_directory"]:
        err_exit("Please working directory from which cragon start.")
    elif not args["working_directory"]:
        date_str = datetime.datetime.now().strftime(context.file_date_format)
        # get the correct command file
        cmdname = os.path.basename(commands[0])
        context.working_dir = os.path.join(
            context.cwd, "cragon_{}_{}".format(cmdname, date_str))
        os.mkdir(context.working_dir)
    else:
        context.working_dir = args["working_directory"]

    # check ckpt algorihtms
    if args["intervals"]:
        context.ckpt_intervals = float(args["intervals"])

    # check system
    context.check()
    if is_restart:
        context.restart_check()

    # start all
    execution.system_set_up()
    retcode = 1
    try:
        with execution.FirstRun(cmd=commands, restart=is_restart) as r:
            r.run()
            retcode = r.returncode
    finally:
        execution.system_tear_down()

    # return result of subprocess
    exit(retcode)


def main():
    cli()


if __name__ == '__main__':
    main()
