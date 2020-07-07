import os
import json
import logging
import psutil
import time
import csv

from cragon import utils
from cragon import context
from cragon import states

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class InterceptedCallMonitor(utils.StoppableService):
    term_mark = "this is a very long termination token\n"

    def __init__(self, fifo_path, record_dir):
        """Monitor to catch all intercepted log from subprocess."""
        super().__init__()
        self.fifo_path = fifo_path
        self.record_file = context.DirStructure.record_dir_to_intercept_log(
            record_dir)

    def start(self):
        logger.info("Starting interception monitor.")
        logger.debug("Reading from fifo: %s." % self.fifo_path)
        logger.debug("Memory access logging to: %s." % self.record_file)
        super().start()

    def loop_body(self):
        with open(self.record_file, "a") as rf:
            while True:
                with open(self.fifo_path, "r") as f:
                    for line in f:
                        if line != self.term_mark:
                            rf.write(line)
                        else:
                            logger.info(
                                "Receved termination token. Monitor stopped.")
                            return

    def stop(self):
        with open(self.fifo_path, "w") as f:
            f.write(self.term_mark)
        self.thread.join()


class MetricMonitor(utils.StoppableService):

    def __init__(self, interval, record_dir):
        """Monitor to collect system resource usage metrics."""
        super().__init__()
        self.interval = interval
        self.system_metrics_file = \
            context.DirStructure.record_dir_to_system_metrics_file(record_dir)
        self.process_metrics_file = \
            context.DirStructure.record_dir_to_process_metrics_file(record_dir)
        self.sys_metrics_fobj = None
        self.prcs_metrics_fobj = None

        self.pid = os.getpid()

        # csv writer
        self.sys_m_writer = None

        self.system_metrics_getters = []
        self.process_metrics_getters = []
        self.system_metrics = []

        # monitor will try to record process metrics if below is non-empty
        self.is_collecting_prcs = False

        # order matters here
        self.init_metrics_getters()
        self.init_metrics_name()

        # trigger the process metrices collection when state change to running
        self.add_callback()

    def add_callback(self):

        def collect_process_metrics(from_s, to_s):
            # when process start
            if from_s == states.State.STARTUP \
                    and to_s == states.State.PROCESS_RUNNING:
                self.start_process_metrices_collect()
            # when process stop
            elif to_s == states.State.PROCESS_FINISHED:
                self.stop_process_metrices_collect()
            else:
                return

        states.add_callback(collect_process_metrics)

    def start_process_metrices_collect(self):
        self.is_collecting_prcs = True

        logger.debug("Start recording metrics for process-level")
        logger.debug("Process metrics recorded to %s" %
                     str(self.process_metrics_file))

        self.prcs_metrics_fobj = open(self.process_metrics_file, "a")

    def stop_process_metrices_collect(self):
        self.is_collecting_prcs = False
        logger.debug("Stop collecting process metrics.")

    def init_metrics_getters(self):
        cpu_indexes = ["cpu%d" % i for i in range(psutil.cpu_count())]

        def dict_add_prefix(prefix, dictionary):
            # {"user":10} => {"cpu0_user":10}
            return {"%s_%s" % (prefix, k): v for k, v in dictionary.items()}

        def cpu_indexed_metrics():
            cpu_t_p = psutil.cpu_times_percent(percpu=True)
            c_ms = [i._asdict() for i in cpu_t_p]

            indexed = {}
            for cpu_i, c_m in zip(cpu_indexes, c_ms):
                indexed.update(dict_add_prefix(cpu_i, c_m))
            return indexed

        def memory_metrics():
            m_ms = psutil.virtual_memory()._asdict()
            return dict_add_prefix("mem", m_ms)

        def per_process_metrics(p):
            # could be still low posibility process stop after is_running test,
            # then raise exception
            if not p.is_running():
                return {}
            try:
                with p.oneshot():
                    cpu = p.cpu_times()
                    mem = p.memory_full_info()
            except Exception:
                return {}
            ret = {}
            ret.update(cpu._asdict())
            ret.update(mem._asdict())
            ret = {"%d_%s" % (p.pid, k): v for k, v in ret.items()}
            return ret

        def process_metrics():
            # subprocesses can start and stop at any time
            processes = psutil.Process(pid=self.pid).children(recursive=True)
            all_prcs_m = {}
            for p in processes:
                all_prcs_m.update(per_process_metrics(p))
            return all_prcs_m

        self.system_metrics_getters = [cpu_indexed_metrics, memory_metrics]
        # different sematic since this will change by time
        self.process_metrics_getters = process_metrics

    def init_metrics_name(self):
        self.system_metrics = list(self.get_current_system_metrics().keys())
        self.system_metrics.sort()
        self.system_metrics.append("timestamp")
        return self.system_metrics

    def start(self):
        logger.info("Starting metrics collector.")
        logger.debug("Recording system resources metrics to %s." %
                     self.system_metrics_file)
        first_wirte = not os.path.exists(self.system_metrics_file)
        self.sys_metrics_fobj = open(self.system_metrics_file, "w")
        self.sys_m_writer = csv.DictWriter(self.sys_metrics_fobj,
                                           fieldnames=self.system_metrics)
        if first_wirte:
            self.sys_m_writer.writeheader()
        super().start()

    def loop_body(self):
        while(True):
            # wait for interval, if waken by stop flag, break
            self.stop_flag.wait(self.interval)
            if(not self.stop_flag.isSet()):
                # sleep first to give enough interval for the first run
                # of the psutil cpu percentage

                timestamp = time.time()
                sys_ms = self.get_current_system_metrics()
                sys_ms["timestamp"] = timestamp
                self.sys_m_writer.writerow(sys_ms)
                # if processes not empty, collect process metrics
                if self.is_collecting_prcs:
                    prcs_ms = self.get_current_process_metrics()
                    prcs_ms["timestamp"] = timestamp
                    self.prcs_metrics_fobj.write(json.dumps(prcs_ms))
                    self.prcs_metrics_fobj.write("\n")
            else:
                break

    def get_current_system_metrics(self):
        # return list of metrics
        metrics = {}
        for i in self.system_metrics_getters:
            metrics.update(i())
        return metrics

    def get_current_process_metrics(self):
        # return list of metrics
        return self.process_metrics_getters()

    def stop(self):
        # stop will be call in execution __exit__
        super().stop()
        if self.sys_metrics_fobj:
            self.sys_metrics_fobj.close()
        if self.prcs_metrics_fobj:
            self.prcs_metrics_fobj.close()
        logger.info("Metrics collector stopped.")
