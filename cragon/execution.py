import context
import os
import subprocess
import time
import tempfile

import algorithms

from utils import FATAL, INFO


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

    def init_dmtcp_coordinator(self):
        # using random port num for dmtcp coordinator
        self.dmtcp_port_file_name = "dmtcp_port_file.tmp"
        self.dmtcp_port_file_path = os.path.join(
            context.tmp_dir, self.dmtcp_port_file_name)

    def init_ckpt_command(self, host, port):
        self.ckpt_command = [context.dmtcp_command]
        self.ckpt_command += ["--coord-host", host, "--coord-port", port]
        self.ckpt_command.append("-bc")

    def __init__(self, command_to_run):
        self.dmtcp_coordinator_host = "127.0.0.1"
        self.command_to_run = command_to_run
        self.dmtcp_cmd = [context.dmtcp_launch]
        self.dmtcp_cmd += DMTCPrun().gen_options()
        # TODO
        self.dmtcp_cmd += ["--ckptdir", "/tmp/wtf"]

        # built in options
        # using random port num for dmtcp coordinator
        self.init_dmtcp_coordinator()
        self.dmtcp_cmd += ["--coord-port", "0",
                           "--port-file", self.dmtcp_port_file_path]
        for c in command_to_run:
            self.dmtcp_cmd.append(c)

        self.init_pipe()

    def wait_for_port_file_available(self):
        wait_interval = 0.001
        max_interval = 0.05
        trial_times = 0
        max_trail = 40
        port = None
        while(trial_times < max_trail):
            if os.path.isfile(self.dmtcp_port_file_path):
                with open(self.dmtcp_port_file_path, "r") as f:
                    content = f.read()
                if port == content:
                    break
                else:
                    port = content
            time.sleep(wait_interval)

            if 2 * wait_interval <= max_interval:
                wait_interval *= 2
            trial_times += 1
        try:
            int(port)
        except Exception as e:
            FATAL("Reading dmtcp port number error", e)
        self.dmtcp_port = port

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.unlink(self.fifo_path)
        os.unlink(self.dmtcp_port_file_path)
        return True

    def run(self):
        self.process_dmtcp_wrapped = subprocess.Popen(self.dmtcp_cmd)
        self.wait_for_port_file_available()
        self.init_ckpt_command(self.dmtcp_coordinator_host, self.dmtcp_port)

        with open(self.fifo_path, "r") as f:
            for line in f:
                print(line, end="")

        def ckpt_func(): return FirstRun.check_point(self)
        ckpt_algorithm = algorithms.Periodic(ckpt_func, 1)
        ckpt_algorithm.start()

        self.process_dmtcp_wrapped.wait()

        ckpt_algorithm.stop()

    def check_point(self):
        INFO("Start checkpointing...")
        # print(" ".join(self.ckpt_command))
        ckpt_process = subprocess.Popen(self.ckpt_command)
        ckpt_process.wait()
        INFO("Checkpoint done.")
