import threading
import time
import logging

from cragon import utils
from cragon import context

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ratio_a = 0.8
ratio_b = 0.8


class CkptAlgorithms(utils.StoppableService):

    def stop(self):
        super().stop()
        logger.info("Checkpoint algorithm is stopped.")


class Periodic(CkptAlgorithms):

    def __init__(self, do_ckpt_func, stop_ckpt_func, interval):
        """Periodically call the checkpoint call back function.

        Arguments:
        do_ckpt_func -- callback function to do checkpoint
        stop_ckpt_func -- callback function to stop a running ckpt process
        interval -- interval between the checkpoints
        """
        super().__init__()
        self.user_interval = interval
        self.interval = self.user_interval
        self.stop_flag = threading.Event()
        self.do_ckpt_func = do_ckpt_func
        self.stop_ckpt_func = stop_ckpt_func
        self.thread = None

        self.sckpt = None  # soft checkpoint time
        self.ckptvar = None  # mean deviation of checkpoint
        self.lnct = None  # longest next ckpt time
        self.firstckpt = True

    def update_estimation(self, ckpt_time):
        if self.firstckpt:
            self.sckpt = ckpt_time
            self.ckptvar = ckpt_time / 2
            self.firstckpt = False
        else:
            E = abs(ckpt_time - self.sckpt)
            self.sckpt = (1 - ratio_a) * self.sckpt + ratio_a * ckpt_time
            self.ckptvar = (1 - ratio_b) * self.ckptvar + ratio_b * E

        self.lnct = self.sckpt + 2 * self.ckptvar

    def update_interval(self):
        # mantain the max ckpt ratio
        if self.sckpt / (self.interval + self.sckpt) > context.ckpt_maxratio:
            newinterval = self.sckpt*(1/context.ckpt_ratio - 1)
            logger.info(
                "interval {} too small regarding to the ckpt time {}, increase to {}".format(
                self.interval, self.sckpt, newinterval))
            self.interval = newinterval
        # need to ajust the interval when we are approching
        if context.execution_walltime:
            now = time.time()
            maxfinish = self.interval + self.lnct + now
            nextsleep = context.execution_walltime - now - self.lnct
            if maxfinish < context.execution_walltime:
                pass  # still enough time do nothing
            elif nextsleep > self.interval / 2:
                # nextsleep should be long enough to make the
                # checkpoint safe user time
                self.interval = nextsleep

    def loop_body(self):
        while(True):
            # TODO take ckpt time into account
            self.stop_flag.wait(self.interval)
            if(self.stop_flag.isSet()):
                break
            else:
                # TODO deal with the instant when process
                # TODO: when the process is sleeping?
                # finished but stop not called yet
                self.checkpoint()

    def checkpoint(self):
        logger.info("Start checkpointing...")
        time_ckpt_start = time.time()
        self.do_ckpt_func()
        duration = time.time() - time_ckpt_start
        self.update_estimation(duration)
        self.update_interval()
        logger.info("Checkpoint done.")

    def stop(self):
        # kill the checkpointing first
        self.stop_ckpt_func()
        super().stop()
