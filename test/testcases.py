import unittest
import logging


class TestCase(unittest.TestCase):

    def assertFatal(self, call, *args, **kwds):
        logging.disable(logging.DEBUG)
        self.assertRaises(RuntimeError, call, *args, **kwds)
        logging.disable(logging.NOTSET)

    def assertFatalRegex(self, call, regex, *args, **kwds):
        logging.disable(logging.DEBUG)
        regex = "^FATAL:" + regex
        self.assertRaisesRegex(RuntimeError, regex, *args, **kwds)
        logging.disable(logging.NOTSET)

