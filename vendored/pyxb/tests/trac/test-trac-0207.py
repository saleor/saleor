# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.utils.utility
import pyxb.binding.datatypes as xsd
from pyxb.utils.six.moves import cPickle as pickle

import unittest

class TestTrac0207 (unittest.TestCase):

    def testDuration (self):
        dur = xsd.duration("P10675199DT2H48M5.4775807S")
        self.assertEqual(dur.days, 10675199)
        self.assertEqual(dur.seconds, 10085)
        self.assertEqual(dur.microseconds, 477580)
        serialized = pickle.dumps(dur)
        xdur = pickle.loads(serialized)
        self.assertEqual(dur, xdur)

    def testDateTime (self):
        now = xsd.dateTime.now()
        serialized = pickle.dumps(now)
        xnow = pickle.loads(serialized)
        self.assertEqual(now, xnow)

if __name__ == '__main__':
    unittest.main()
