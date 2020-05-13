import logging
import os
import sys
import threading

logger = logging.getLogger()

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def create_dir_unless_exist(path):
    try:
        os.makedirs(path)
    except FileExistsError as e:
        if os.path.isdir(path):
            pass
        elif os.path.isfile(path):
            FATAL("Can not create dir: {}".format(path), e)

def INFO(msg):
    logger.info(msg)


def DEBUG(msg):
    logger.debug(msg)


def WARNING(msg):
    logger.warning(msg)


def ERROR(msg):
    logger.error(msg)


def FATAL(msg=None, e=None):
    if msg:
        ERROR(msg)
    if not e:
        raise RuntimeError("FATAL:" + msg)
    else:
        ERROR(e.message)
        raise(e)


class AutoStopService(object):

    def __init__(self):
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.body)
        self.thread.start()

    def wait(self):
        self.thread.join()

    def stop(self):
        self.wait()


class StoppableService(object):

    def __init__(self):
        self.stop_flag = threading.Event()

    def start(self):
        self.thread = threading.Thread(target=self.loop_body)
        self.thread.start()

    def task(self):
        pass

    def loop_body(self):
        while(True):
            if(not self.stop_flag.isSet()):
                self.task()
            break

    def stop(self):
        self.stop_flag.set()
        self.thread.join()
