import os
import subprocess
import time
import tempfile
import logging

from cragon import context
from cragon import states
from cragon import algorithms
from cragon import monitor
from cragon import utils
from cragon import checkpoint_manager
from cragon import signals

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DMTCPCmdOption(object):

    def __init__(self):
        """Generate cmd options for DMTCP."""
        self.options = {}

    def set_new_coordinator(self):
        self.options["--new-coordinator"] = ""

    def set_plugin(self):
        if not context.dmtcp_plugins:
            raise RuntimeError("DMTCP plugin is missing!")
        self.options["--with-plugin"] = context.dmtcp_plugins

    def disable_internal_alloc(self):
        # disable dmtcp internal alloc wrap
        # https://github.com/dmtcp/dmtcp/issues/847
        self.options["--disable-alloc-plugin"] = ""

    def gen_options(self):
        opts = []
        for key, value in self.options.items():
            opts.append(key)
            if value:
                opts.append(value)
        return opts


class DMTCPfirstrun(DMTCPCmdOption):
    def gen_options(self):
        self.set_new_coordinator()
        self.disable_internal_alloc()
        self.set_plugin()
        return super().gen_options()


class DMTCPrestart(DMTCPCmdOption):
    def gen_options(self):
        self.set_new_coordinator()
        return super().gen_options()


class Execution(object):

    def start(self):
        pass


def start_all(is_restart):

    # check system
    context.check()
    if is_restart:
        context.restart_check()

    # start all
    system_set_up(is_restart)
    retcode = 1
    try:
        with FirstRun(restart=is_restart) as r:
            r.run()
            retcode = r.returncode
    finally:
        system_tear_down()

    # return result of subprocess
    exit(retcode)


def system_set_up(is_restart):
    # config root logger
    log_file_path = \
        context.DirStructure.working_dir_to_log_file(context.working_dir)
    handler = logging.FileHandler(log_file_path)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logging.basicConfig(handlers=[handler])

    # change state
    states.setStartUp()

    # init tmp dir
    context.tmp_dir = tempfile.mkdtemp()
    context.tmp_file_created.append(context.tmp_dir)
    logger.debug("Temp folder: %s created." % context.tmp_dir)

    # init ckpt dir
    utils.create_dir_unless_exist(context.ckpt_dir)

    # restore directory to create fifo
    if context.fifo_path:
        logger.debug("Restoring directories for %s" % context.fifo_path)
        dirs = context.fifo_path.split(os.sep)[1:-1]
        start = ""
        for d in dirs:
            start += os.sep + d
            if not os.path.isdir(start):
                os.mkdir(start)
                context.tmp_file_created.append(start)

    # init image maneger
    # for restart image_dir_to_restart will be non-emtpy
    # for firstrun, it will be emtpy and ignored
    # this implicity is a bad design
    if is_restart:
        checkpoint_manager.CkptManager(checkpoint_manager.KeepLatestN,
                                       context.image_dir_to_restart)
    else:
        checkpoint_manager.CkptManager(checkpoint_manager.KeepLatestN)


def system_tear_down():
    for f in context.tmp_file_created[::-1]:
        logger.debug("Trying to delete :%s if exist." % f)
        utils.safe_clean_file(f)
    logger.info("System stopped.")


class FirstRun(Execution):

    def init_pipe(self):
        if self.isrestart:
            self.fifo_path = context.fifo_path
        else:
            self.fifo_path = context.DirStructure.tmp_dir_to_fifo_path(
                context.tmp_dir)
        os.mkfifo(self.fifo_path, 0o600)
        os.environ["DMTCP_PLUGIN_EXEINFO_LOGGING_PIPE"] = self.fifo_path

    def init_dmtcp_coordinator(self):
        # using random port num for dmtcp coordinator
        self.dmtcp_port_file_name = "dmtcp_port_file.tmp"
        self.dmtcp_port_file_path = context.DirStructure.tmp_dir_to_port_file(
                context.tmp_dir)

    def init_ckpt_command(self, host, port):
        self.ckpt_command = [context.dmtcp_command]
        self.ckpt_command += ["--coord-host", host, "--coord-port", port]
        self.ckpt_command.append("-bc")

    def init_ckpt_algorithm(self):
        def ckpt_func(): return FirstRun.checkpoint(self)
        def stop_ckpt_func(): return FirstRun.stop_checkpoint(self)
        # TODO: this line sucks
        if context.ckpt_algorihtm is algorithms.Periodic:
            self.ckpt_algorithm = context.ckpt_algorihtm(
                ckpt_func, stop_ckpt_func, context.ckpt_intervals)

    def init_common_cmd(self):
        self.dmtcp_cmd += ["--ckptdir", context.ckpt_dir]

        # built in options
        # using random port num for dmtcp coordinator
        self.init_dmtcp_coordinator()
        self.dmtcp_cmd += ["--coord-port", "0",
                           "--port-file", self.dmtcp_port_file_path]

    def init_first_run_cmd(self):
        self.dmtcp_cmd = [context.dmtcp_launch]
        self.dmtcp_cmd += DMTCPfirstrun().gen_options()

        self.init_common_cmd()

        for c in self.command_to_run:
            self.dmtcp_cmd.append(c)

    def init_restart_cmd(self):
        self.dmtcp_cmd = [context.dmtcp_restart]
        self.dmtcp_cmd += DMTCPrestart().gen_options()

        self.init_common_cmd()

        self.dmtcp_cmd += context.images_to_restart

    def __init__(self, restart=False):
        """A huge class to manage the execution of subprocess to be
        checkpointed
        """
        # the ret code of process to be checkpointed
        self.returncode = None
        # using localhost as coordinator
        self.dmtcp_coordinator_host = "127.0.0.1"
        # will be init after execution
        self.intercept_monitor = None
        # monitor the system usage
        self.metrics_monitor = None
        # record isrestart
        self.isrestart = restart
        # the command of process to run
        self.command_to_run = context.command
        # ckpt process, saved for easy manipulation
        self.ckpt_process = None

        # init cmd
        if self.isrestart:
            self.init_restart_cmd()
        else:
            self.init_first_run_cmd()

        # init algorithm
        self.ckpt_algorithm = None
        self.init_ckpt_algorithm()

        # init pipe
        self.init_pipe()

    def start_intercept_monitor(self):
        self.intercept_monitor = monitor.InterceptedCallMonitor(
            self.fifo_path, context.DirStructure.get_monitor_record_dir())
        self.intercept_monitor.start()

    def start_metrics_monitor(self):
        # todo allow setting intervals from cli
        self.metrics_monitor = monitor.MetricMonitor(
            context.default_metrics_interval,
            context.DirStructure.get_monitor_record_dir())
        self.metrics_monitor.start()

    def wait_for_port_file_available(self):
        wait_interval = 0.001
        max_interval = 0.05
        trial_times = 0
        max_trail = 40
        port = None
        logger.debug(
            "Waiting for the port specified in file: %s" %
            self.dmtcp_port_file_path)
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
            utils.FATAL(("Reading dmtcp port number error,"
                         " dmtcp does not start normally"), e)
        self.dmtcp_port = port
        logger.debug("Suceesfully retrieved port: %s", self.dmtcp_port)

    def __enter__(self):
        """Context manager to assure the resource cleanning."""
        return self

    def __exit__(self, exc_type, value, traceback):
        """Do the clean up work."""
        # should never raise here, clean carefully
        states.setTearDwon()

        if self.metrics_monitor:
            self.metrics_monitor.stop()
            del self.metrics_monitor

        if self.intercept_monitor:
            self.intercept_monitor.stop()
            del self.intercept_monitor

        logger.debug("Deleting fifo file: %s" % self.fifo_path)
        utils.safe_clean_file(self.fifo_path)
        logger.debug("Deleting temp port file: %s" % self.dmtcp_port_file_path)
        utils.safe_clean_file(self.dmtcp_port_file_path)

        if not value:
            return True
        else:
            return False

    def start_process(self):
        logger.info("Start executing: %s" % " ".join(self.command_to_run))
        logger.debug("Run DMTCP: %s" % " ".join(self.dmtcp_cmd))

        states.setProcessRunning()

        self.process_dmtcp_wrapped = subprocess.Popen(self.dmtcp_cmd,
                                                      shell=False)

    def wait_process(self):

        siginfo = os.waitid(os.P_PID, self.process_dmtcp_wrapped.pid,
                            os.WEXITED | os.WNOWAIT)
        self.process_dmtcp_wrapped.wait()

        states.setProcessFinished()

        CLD_KILLED = 3

        if siginfo.si_code == CLD_KILLED:
            utils.stderr_and_log("Process recevied signal: %s" %
                                 signals.strsignal(siginfo.si_status), logger)

        self.returncode = self.process_dmtcp_wrapped.returncode
        logger.info(
            "Process to be checkpointed finished with ret code :%d." %
            self.returncode)

    def run(self):
        # collect metrics before running
        self.start_metrics_monitor()
        # start
        self.start_process()

        self.wait_for_port_file_available()
        self.init_ckpt_command(self.dmtcp_coordinator_host, self.dmtcp_port)

        self.start_intercept_monitor()

        self.ckpt_algorithm.start()

        # finish
        self.wait_process()

        # TODO: should we put stop in __exit__?
        self.ckpt_algorithm.stop()

    def gen_ckpt_info(self, ckpt_timestamp=None):
        ckpt_info = {}
        ckpt_info["command"] = self.command_to_run
        ckpt_info["hostname"] = context.current_host_name
        ckpt_info["user"] = context.current_user_name
        ckpt_info["data"] = {}
        ckpt_info["data"]["fifo_path"] = self.fifo_path
        if ckpt_timestamp:
            ckpt_info["checkpint_timestamp"] = ckpt_timestamp

        return ckpt_info

    def checkpoint(self):
        # this fun is called in another thread
        try:
            states.setCheckpointing()
        except AssertionError:
            # either system is checkpointing or process has finished
            logger.info("The system is in state %s. Do not checkpoint." %
                        states.get_current_state().name)
            return

        logger.debug(
            "Running checkpoint subprocess: %s." % " ".join(self.ckpt_command))
        self.ckpt_process = subprocess.Popen(self.ckpt_command, shell=False,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        self.ckpt_process.wait()
        logger.debug("Checkpoint subprocess: %s finished with ret code:%d." % (
            " ".join(self.ckpt_command), self.ckpt_process.returncode))

        out, err = self.ckpt_process.stdout, self.ckpt_process.stderr
        if self.ckpt_process.returncode != 0:
            logger.warn("Checkpoint subprocess failed with return code: %d" %
                        self.ckpt_process.returncode)
            logger.warn("Checkpoint subprocess stdout: %s\n" % out)
            logger.warn("Checkpoint subprocess stderr: %s\n" % err)
        else:
            # TODO add event of ckpt finished
            time_ckpt_finished = time.time()
            checkpoint_manager.CkptManager().make_checkpoint(
                self.gen_ckpt_info(ckpt_timestamp=time_ckpt_finished))

        self.ckpt_process = None

        try:
            # revert state
            states.setProcessRunning()
        except AssertionError:
            # can be finished or enter another checkpoint
            pass

    def stop_checkpoint(self):
        # stop the running checkpoint process
        if self.ckpt_process and self.ckpt_process.poll() is None:
            # still running
            self.ckpt_process.terminate()
            logger.debug((
                "Kill the running checkpointing"
                " since the process has finished."))
