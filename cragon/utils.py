import sys
import logging

logger = logging.getLogger()


def INFO(msg):
    logger.info(msg)


def DEBUG(msg):
    logger.debug(msg)


def WARNING(msg):
    logger.warning(msg)


def ERROR(msg):
    logger.error(msg)


def FATAL(msg):
    ERROR(msg)
    raise RuntimeError("FATAL:" + msg)
