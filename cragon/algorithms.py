import threading

from cragon import utils

class CkptAlgorithms(utils.StoppableService):
    pass


class Periodic(CkptAlgorithms):

    def __init__(self, do_ckpt_func, interval):
        super().__init__()
        self.interval = interval
        self.stop_flag = threading.Event()
        self.do_ckpt_func = do_ckpt_func
        self.thread = None

    def loop_body(self):
        while(True):
            self.stop_flag.wait(self.interval)
            if(self.stop_flag.isSet()):
                break
            else:
                """ TODO deal with the instant when process
                TODO: when the process is sleeping?
                finished but stop not called yet"""
                self.do_ckpt_func()
