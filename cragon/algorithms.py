import threading
import logging

from cragon import utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CkptAlgorithms(utils.StoppableService):

    def stop(self):
        super().stop()
        logger.info("Checkpoint algorithm is stopped.")


class Periodic(CkptAlgorithms):

    def __init__(self, do_ckpt_func, stop_ckpt_func, interval):
        super().__init__()
        self.interval = interval
        self.stop_flag = threading.Event()
        self.do_ckpt_func = do_ckpt_func
        self.stop_ckpt_func = stop_ckpt_func
        self.thread = None

    def loop_body(self):
        while(True):
            # TODO take ckpt time into account
            self.stop_flag.wait(self.interval)
            if(self.stop_flag.isSet()):
                break
            else:
                """ TODO deal with the instant when process
                TODO: when the process is sleeping?
                finished but stop not called yet"""
                self.checkpoint()

    def checkpoint(self):
        logger.info("Start checkpointing...")
        self.do_ckpt_func()
        logger.info("Checkpoint done.")

    def stop(self):
        # kill the checkpointing first
        self.stop_ckpt_func()
        super().stop()
