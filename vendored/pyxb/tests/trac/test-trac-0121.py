# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.datatypes as xsd
import datetime
import copy

import unittest

class TestTrac0121 (unittest.TestCase):
    def testPythonDT (self):
        v = datetime.datetime.now()
        c = copy.copy(v)
        self.assertEqual(c, v)

    def testDateTime (self):
        v = xsd.dateTime.now()
        c = copy.copy(v)
        self.assertEqual(c, v)

    def testDate (self):
        v = xsd.date(datetime.date.today())
        c = copy.copy(v)
        self.assertEqual(c, v)

    def testTime (self):
        v = xsd.time()
        c = copy.copy(v)
        self.assertEqual(c, v)


if __name__ == '__main__':
    unittest.main()
