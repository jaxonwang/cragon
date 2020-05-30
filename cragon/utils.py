import logging
import os
import threading

logger = logging.getLogger(__name__)


def singleton(c):
    instance = None

    def getinstance(*args, **kargs):
        nonlocal instance
        if "reset_the_singeton" in kargs:
            instance = None
            return None
        if not instance:
            instance = c()
        return instance
    return getinstance


def init_once_singleton(c):
    # a singleton that should be called with init args before use
    # and after that should be only called without int args
    instance = None

    def getinstance(*args, **kargs):
        nonlocal instance
        # allow reset for test
        if "reset_the_singeton" in kargs:
            instance = None
            return None
        if instance:
            if args or kargs:
                raise Exception(
                    "The class %s has been initialized." %
                    c.__name__)
            return instance
        else:
            if not args and not kargs:
                raise Exception(
                    ("The class %s has not initialized."
                     " Please specify the args.") %
                    c.__name__)
            else:
                instance = c(*args, **kargs)
                return instance
    return getinstance


def safe_clean_file(file_path):
    if not file_path:
        return
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            os.rmdir(file_path)
        else:
            os.unlink(file_path)


def create_dir_unless_exist(path):
    try:
        os.makedirs(path)
    except FileExistsError as e:
        if os.path.isdir(path):
            pass
        elif os.path.isfile(path):
            FATAL("Can not create dir: {}".format(path), e)


def get_command_basename(cmd):
    return os.path.basename(cmd)


def FATAL(msg="", e=None):
    """
    system encounters an fatal error, log it before rasie
    """
    if msg:
        logger.critical(msg)
    if not e:
        e = RuntimeError("FATAL:" + msg)
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
            else:
                break

    def stop(self):
        self.stop_flag.set()
        self.thread.join()
