import sys
import os
import subprocess
import time
import tempfile
import logging

from cragon import context
from cragon import algorithms
from cragon import monitor
from cragon import utils
from cragon import images

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DMTCPCmdOption(object):

    def __init__(self):
        self.options = {}

    def set_new_coordinator(self):
        self.options["--new-coordinator"] = ""

    def set_plugin(self):
        if not context.dmtcp_plugins:
            raise RuntimeError("DMTCP plugin is missing!")
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
    # config root logger
    log_file_path = os.path.join(context.working_dir, context.log_file)
    handler = logging.FileHandler(log_file_path)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logging.basicConfig(handlers=[handler])

    # init tmp dir
    context.tmp_dir = tempfile.mkdtemp()

    # init image dir
    utils.create_dir_unless_exist(context.image_dir)


def system_tear_down():
    utils.safe_clean_file(context.tmp_dir)


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
        self.dmtcp_cmd += ["--ckptdir", context.image_dir]

        # will be init after execution
        self.intercept_monitor = None

        # built in options
        # using random port num for dmtcp coordinator
        self.init_dmtcp_coordinator()
        self.dmtcp_cmd += ["--coord-port", "0",
                           "--port-file", self.dmtcp_port_file_path]
        for c in command_to_run:
            self.dmtcp_cmd.append(c)

        self.init_pipe()

    def start_intercept_monitor(self):
        self.intercept_monitor = monitor.InterceptedCallMonitor(
            self.fifo_path, context.working_dir)
        self.intercept_monitor.start()

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
                    # TODO correctness: using fifo?
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
            utils.FATAL("Reading dmtcp port number error", e)
        self.dmtcp_port = port

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # should never raise here, clean carefully
        if self.intercept_monitor:
            self.intercept_monitor.stop()
            del self.intercept_monitor

        utils.safe_clean_file(self.fifo_path)
        utils.safe_clean_file(self.dmtcp_port_file_path)

        return True

    def run(self):
        self.process_dmtcp_wrapped = subprocess.Popen(self.dmtcp_cmd)
        self.wait_for_port_file_available()
        self.init_ckpt_command(self.dmtcp_coordinator_host, self.dmtcp_port)

        self.start_intercept_monitor()

        def ckpt_func(): return FirstRun.check_point(self)
        ckpt_algorithm = algorithms.Periodic(ckpt_func, 1)
        ckpt_algorithm.start()

        self.process_dmtcp_wrapped.wait()

        ckpt_algorithm.stop()

    def check_point(self):
        # this fun is called in another thread
        logger.info("Start checkpointing...")
        ckpt_process = subprocess.Popen(self.ckpt_command)
        ckpt_process.wait()
        time_ckpt_finished = time.time()  # TODO assign id to ckpt images
        images.archive_current_image(
            time_ckpt_finished, self.command_to_run[0])
        logger.info("Checkpoint done.")
