import click
import os
import sys
import context
import execution


def err_exit(err_msg):
    click.echo(err_msg, err=True)
    sys.exit(2)


dmtcp_launch_file_name = "dmtcp_launch"
dmtcp_command_file_name = "dmtcp_command"
dmtcp_file_check = [dmtcp_launch_file_name, dmtcp_command_file_name]


@click.command()
@click.option('-p', '--dmtcp-path', type=click.Path(exists=True),
              help="DMTCP binary path")
@click.argument('commands', nargs=-1)
def cli(**args):
    "Checkpoint and restore tool."
    dmtcp_path = args["dmtcp_path"]
    if not dmtcp_path:
        dmtcp_path = os.path.join(context.ROOT_DIR, "bin")
    dmtcp_path = os.path.abspath(dmtcp_path)

    files_to_check = [os.path.join(dmtcp_path, f)
                      for f in dmtcp_file_check]
    for f in files_to_check:
        if not os.path.isfile(f):
            err_exit("File: {} not found".format(f))
    context.dmtcp_path = dmtcp_path
    context.dmtcp_launch = os.path.join(dmtcp_path, dmtcp_launch_file_name)
    context.dmtcp_command = os.path.join(dmtcp_path, dmtcp_launch_file_name)

    commands = args["commands"]
    if not commands:
        err_exit("Please specify command to run, or start with checkpoint directory")

    context.check()
    execution.FirstRun(commands)


def main():
    cli()


if __name__ == '__main__':
    main()
