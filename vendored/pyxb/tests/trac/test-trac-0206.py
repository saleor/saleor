# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.utils.utility
import pyxb.binding.datatypes as xsd

import unittest

class TestTrac0206 (unittest.TestCase):
    Time = "2013-08-30T11:56:45+04:00" # = 2013-08-30T07:56:45Z

    def setUp (self):
        self.__pitz = pyxb.PreserveInputTimeZone()
        self.__ltz = xsd.dateTime._LocalTimeZone
        xsd.dateTime._LocalTimeZone = pyxb.utils.utility.UTCOffsetTimeZone(120)

    def tearDown (self):
        pyxb.PreserveInputTimeZone(self.__pitz)
        xsd.dateTime._LocalTimeZone = self.__ltz

    def testBasic (self):
        self.assertFalse(pyxb.PreserveInputTimeZone())
        dt = xsd.dateTime(self.Time)
        self.assertEqual('2013-08-30 07:56:45+00:00', str(dt))
        self.assertEqual('2013-08-30 09:56:45+02:00', str(dt.aslocal()))

    def testPreserve (self):
        pyxb.PreserveInputTimeZone(True)
        self.assertTrue(pyxb.PreserveInputTimeZone())
        dt = xsd.dateTime(self.Time)
        self.assertEqual('2013-08-30 11:56:45+04:00', str(dt))
        self.assertEqual('2013-08-30 09:56:45+02:00', str(dt.aslocal()))

if __name__ == '__main__':
    unittest.main()
