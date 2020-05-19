import logging
import time

from cragon import utils
from .testcases import TestCase


@utils.singleton
class Sgt(object):
    def __init__(self):
        pass


@utils.init_once_singleton
class ISgt(object):
    def __init__(self, value=1):
        self.value = value


class TestSingleton(TestCase):

    def test_singleton(self):
        s1 = Sgt()
        s2 = Sgt()
        s3 = Sgt()
        self.assertEqual(id(s1), id(s2))
        self.assertEqual(id(s3), id(s2))

    def test_init_singleton(self):
        msg = "The class ISgt has not initialized. Please specify the args."
        self.assertRaisesRegex(Exception, msg, ISgt)
        msg = "The class ISgt has been initialized."

        s1 = ISgt(1234)
        self.assertRaisesRegex(Exception, msg, ISgt, 321)
        s2 = ISgt()
        s3 = ISgt()
        self.assertEqual(id(s1), id(s2))
        self.assertEqual(id(s3), id(s2))


class TestLoggin(TestCase):

    def test_fatal(self):
        logger = utils.logger
        msg = "this is a message"
        with self.assertLogs(logger, logging.CRITICAL) as cm:
            self.assertRaises(RuntimeError, utils.FATAL)
            self.assertRaisesRegex(
                RuntimeError, "^FATAL:" + msg, utils.FATAL, msg)
            self.assertRaisesRegex(
                Exception,
                msg,
                utils.FATAL,
                None,
                Exception(msg))
            self.assertRaisesRegex(
                Exception,
                msg,
                utils.FATAL,
                "123",
                Exception(msg))
        self.assertTrue(msg in cm.output[0])
        self.assertTrue("123" in cm.output[1])


class JustAutoStopService(utils.AutoStopService):

    def __init__(self, do):
        super().__init__()
        self.do = do

    def body(self):
        self.do()


class LoopService(utils.StoppableService):

    def __init__(self, do):
        super().__init__()
        self.do = do

    def task(self):
        self.do()


class TestService(TestCase):
    def test_auto_stop(self):

        flag = False

        def set_flag():
            nonlocal flag
            flag = True
        s = JustAutoStopService(set_flag)
        s.start()
        s.stop()
        self.assertTrue(flag)

    def test_loop_service(self):
        count = 0

        def inc():
            nonlocal count
            count += 17
        s = LoopService(inc)
        s.start()
        time.sleep(0.005)
        s.stop()
        self.assertTrue(count > 17 and count % 17 == 0)
