import logging
import sys

logger = logging.getLogger()

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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
