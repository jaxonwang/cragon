import context
import os
import subprocess
import tempfile

from utils import FATAL


class DMTCPCmdOption(object):

    def __init__(self):
        self.options = {}

    def set_new_coordinator(self):
        self.options["--new-coordinator"] = ""

    def set_plugin(self):
        if not context.dmtcp_plugins:
            FATAL("DMTCP plugin is missing!")
        self.options["--with-plugin"] = context.dmtcp_plugins

    def gen_options(self):
        opts = []
        for key, value in self.options.items():
            opts.append(key)
            if value:
                opts.append(value)
        return opts


class DMTCPrun(DMTCPCmdOption):
    def gen_options(self):
        self.set_new_coordinator()
        self.set_plugin()
        return super().gen_options()


class Execution(object):

    def start(self):
        pass


def system_set_up():
    context.tmp_dir_obj = tempfile.TemporaryDirectory()
    context.tmp_dir = context.tmp_dir_obj.name


def system_tear_down():
    del context.tmp_dir_obj


class FirstRun(Execution):

    def init_pipe(self):
        self.fifo_path = os.path.abspath(os.path.join(context.tmp_dir,
                                                      "logging.fifo"))
        os.mkfifo(self.fifo_path, 0o600)
        os.environ["DMTCP_PLUGIN_EXEINFO_LOGGING_PIPE"] = self.fifo_path

    def __init__(self, command_to_run):
        self.command_to_run = command_to_run
        self.dmtcp_cmd = [context.dmtcp_launch]
        self.dmtcp_cmd += DMTCPrun().gen_options()
        for c in command_to_run:
            self.dmtcp_cmd.append(c)

        self.init_pipe()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.unlink(self.fifo_path)
        return True

    def run(self):
        self.process_dmtcp_wrapped = subprocess.Popen(self.dmtcp_cmd)
        with open(self.fifo_path, "r") as f:
            print(f.read())
        self.process_dmtcp_wrapped.wait()
