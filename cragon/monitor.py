import os
import logging
import psutil
import time
import csv

from cragon import utils
from cragon import context

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class InterceptedCallMonitor(utils.StoppableService):
    term_token = "this is a very long termination token\n"

    def __init__(self, fifo_path, record_dir):
        super().__init__()
        self.fifo_path = fifo_path
        self.record_file = os.path.join(
            record_dir, context.intercepted_log_name)

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
                        if line != self.term_token:
                            rf.write(line)
                        else:
                            logger.info(
                                "Receved termination token. Monitor stopped.")
                            return

    def stop(self):
        with open(self.fifo_path, "w") as f:
            f.write(self.term_token)
        self.thread.join()

    def __del__(self):
        pass


class MetricMonitor(utils.StoppableService):

    def __init__(self, interval, record_dir):
        super().__init__()
        self.interval = interval
        self.record_file = os.path.join(
            record_dir, context.metrics_file_name)

        self.metrics_getters = []
        self.metrics = []

        # order matters here
        self.init_metrics_getters()
        self.init_metrics_name()

    def init_metrics_getters(self):
        self.metrics_getters = []
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

        def time_stamp():
            return {"timestamp": time.time()}

        # TODO: add process level usage

        self.metrics_getters = [cpu_indexed_metrics, memory_metrics,
                                time_stamp]

    def init_metrics_name(self):
        self.metrics = list(self.get_current_metrics().keys())
        self.metrics.sort()
        return self.metrics

    def start(self):
        logger.info("Starting interception monitor.")
        logger.debug("Recording system resources metrics to %s." %
                     self.record_file)
        if not os.path.exists(self.record_file):
            with open(self.record_file, "w") as csv_f:
                writer = csv.DictWriter(csv_f, fieldnames=self.metrics)
                writer.writeheader()
        super().start()

    def loop_body(self):
        with open(self.record_file, "a") as csv_f:
            writer = csv.DictWriter(csv_f, fieldnames=self.metrics)
            while(True):
                if(not self.stop_flag.isSet()):
                    # sleep first to give enough interval for the first run
                    # of the psutil cpu percentage
                    time.sleep(self.interval)
                    writer.writerow(self.get_current_metrics())
                else:
                    break

    def get_current_metrics(self):
        # return list of metrics
        metrics = {}
        [metrics.update(i()) for i in self.metrics_getters]
        return metrics
