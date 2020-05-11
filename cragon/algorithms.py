
import threading


class CkptAlgorithms(object):
    def start(self):
        self.thread = threading.Thread(target=self.loop_body)
        self.thread.start()

    def stop(self):
        self.stop_flag.set()
        self.thread.join()


class Periodic(CkptAlgorithms):

    def __init__(self, do_ckpt_func, interval):
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
                finished but stop not called yet"""
                self.do_ckpt_func()
