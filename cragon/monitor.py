import os
import logging

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
