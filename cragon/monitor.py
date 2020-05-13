import os
import utils


class InterceptedCallMonitor(utils.AutoStopService):

    def __init__(self, fifo_path, record_dir):
        super().__init__()
        self.fifo_path = fifo_path
        self.record_file = os.path.join(record_dir, "intercepted.log")

    def body(self):
        with open(self.record_file, "a") as rf:
            with open(self.fifo_path, "r") as f:  # will eventually stop
                for line in f:
                    rf.write(line)

    def __del__(self):
        pass
