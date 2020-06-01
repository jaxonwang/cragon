import threading
import copy
import enum
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


access_lock = threading.Lock()


class State(enum.Enum):
    INIT = 0
    STARTUP = 1
    TEARDOWN = 2
    PROCESS_RUNNING = 3
    PROCESS_FINISHED = 4
    CHECKPOINTING = 5


__current = State.INIT


def log_callback(from_s, to_s):
    logger.debug("The system's state changed from %s to %s." % (from_s.name,
                                                                to_s.name))


__callbacks = [log_callback]


def add_callback(func):
    # not thread safe
    __callbacks.append(func)


class Globalstate(object):
    pass


def __transform(from_s, to_s):
    global __current
    with access_lock:
        from_cpy = copy.copy(__current)
        to_cpy = copy.copy(to_s)
        assert __current in from_s
        __current = to_s
    for f in __callbacks:
        f(from_cpy, to_cpy)


def get_current_state():
    global __current
    with access_lock:
        ret = copy.deepcopy(__current)
    return ret


def setStartUp():
    __transform([State.INIT], State.STARTUP)


def setTearDwon():
    __transform([State.PROCESS_FINISHED], State.TEARDOWN)


def setProcessRunning():
    __transform([State.STARTUP, State.CHECKPOINTING], State.PROCESS_RUNNING)


def setProcessFinished():
    __transform([State.PROCESS_RUNNING, State.CHECKPOINTING],
                State.PROCESS_FINISHED)


def setCheckpointing():
    __transform([State.PROCESS_RUNNING], State.CHECKPOINTING)


def isCheckpointing():
    with access_lock:
        return __current == State.CHECKPOINTING
