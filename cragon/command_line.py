import click
import datetime
import os
import sys

from cragon import context
from cragon import execution


def err_exit(err_msg):
    click.echo(err_msg, err=True)
    sys.exit(2)


dmtcp_launch_file_name = "dmtcp_launch"
dmtcp_command_file_name = "dmtcp_command"
dmtcp_file_check = [dmtcp_launch_file_name, dmtcp_command_file_name]


@click.command()
@click.option('-p', '--dmtcp-path', type=click.Path(exists=True),
              help="DMTCP binary path")
@click.option('-i', '--intervals', type=click.FLOAT,
              help=("Time in second(s) between checkpoints"
                    " in the naive checkpoint algorithm."))
@click.option(
    '-w', '--working-directory', type=click.Path(exists=True),
    help=("cragon working directory where"
          " checkpoint images and logs are stored"))
@click.argument('commands', nargs=-1)
def cli(**args):
    "Checkpoint and restore tool."

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
    context.dmtcp_launch = os.path.join(dmtcp_path, dmtcp_launch_file_name)
    context.dmtcp_command = os.path.join(dmtcp_path, dmtcp_command_file_name)

    # get commands to execute
    commands = args["commands"]
    if not commands:
        err_exit("Please specify command to run, or start with checkpoint directory")

    # check working directory
    if not args["working_directory"]:
        date_str = datetime.datetime.now().strftime(context.file_date_format)
        context.working_dir = os.path.join(
            context.cwd, "cragon_{}_{}".format(commands[0], date_str))
        os.mkdir(context.working_dir)
    else:
        context.working_dir = args["working_directory"]

    # check ckpt algorihtms
    if args["intervals"]:
        context.ckpt_intervals = float(args["intervals"])

    # check system
    context.check()

    # start all
    execution.system_set_up()
    with execution.FirstRun(commands) as r:
        r.run()
    execution.system_tear_down()


def main():
    cli()


if __name__ == '__main__':
    main()
