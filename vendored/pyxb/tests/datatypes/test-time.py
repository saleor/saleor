# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import unittest
import pyxb.binding.datatypes as xsd
import datetime

class Test_time (unittest.TestCase):

    def verifyTime (self, tm, with_usec=True, with_adj=(0,0), with_tzinfo=True):
        (hour_adj, minute_adj) = with_adj
        self.assertEqual(12 + hour_adj, tm.hour)
        self.assertEqual(14 + minute_adj, tm.minute)
        self.assertEqual(32, tm.second)
        if with_usec:
            self.assertEqual(123400, tm.microsecond)
        self.assertEqual(with_tzinfo, tm.tzinfo is not None)

    def testBad (self):
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.time, '12: 14: 32')
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.time, '12:14:32.Z')
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.time, '12:14:32.123405:00')
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.time, '12:14:32.1234+05')

    def testFromText (self):
        self.verifyTime(xsd.time('12:14:32'), with_usec=False, with_tzinfo=False)
        self.verifyTime(xsd.time('12:14:32.1234'), with_tzinfo=False)
        self.verifyTime(xsd.time('12:14:32Z'), with_usec=False)
        self.verifyTime(xsd.time('12:14:32.1234Z'))
        self.verifyTime(xsd.time('12:14:32.1234+05:00'), with_adj=(-5,0))
        self.verifyTime(xsd.time('12:14:32.1234Z'))
        self.verifyTime(xsd.time('  12:14:32', _from_xml=True), with_usec=False, with_tzinfo=False)
        self.verifyTime(xsd.time('12:14:32  ', _from_xml=True), with_usec=False, with_tzinfo=False)

    def testArguments (self):
        self.verifyTime(xsd.time(12, 14, 32), with_usec=False, with_tzinfo=False)
        self.verifyTime(xsd.time(12, 14, 32, 123400), with_tzinfo=False)

    def testXsdLiteral (self):
        dt = xsd.time('12:14:32Z')
        self.assertEqual('12:14:32Z', dt.xsdLiteral())
        self.assertTrue(dt.tzinfo is not None)
        self.assertEqual('07:14:32Z', xsd.time('12:14:32+05:00').xsdLiteral())
        self.assertEqual('17:14:32Z', xsd.time('12:14:32-05:00').xsdLiteral())
        self.assertEqual('17:14:32.1234Z', xsd.time('12:14:32.123400-05:00').xsdLiteral())
        # No zone info
        dt = xsd.time('12:14:32')
        self.assertEqual('12:14:32', dt.xsdLiteral())
        self.assertFalse(dt.tzinfo is not None)

if __name__ == '__main__':
    unittest.main()
