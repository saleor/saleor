# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import unittest
import pyxb.binding.datatypes as xsd
import datetime

class Test_date (unittest.TestCase):

    def verifyTime (self, dt, with_usec=True, with_adj=(0,0), with_tzinfo=True):
        self.assertEqual(2002, dt.year)
        self.assertEqual(10, dt.month)
        self.assertEqual(27, dt.day)
        self.assertEqual(with_tzinfo, dt.tzinfo is not None)

    def testBad (self):
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.date, '2002-10-27T')

    def testFromText (self):
        self.verifyTime(xsd.date('  2002-10-27', _from_xml=True), with_usec=False, with_tzinfo=False)
        self.verifyTime(xsd.date('2002-10-27  ', _from_xml=True), with_usec=False, with_tzinfo=False)
        self.verifyTime(xsd.date('2002-10-27'), with_usec=False, with_tzinfo=False)

    def testYear (self):
        # This test can't succeed because Python doesn't support negative years.
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.date, '-0024-01-01')

    def testArguments (self):
        self.assertRaises(TypeError, xsd.date)
        self.assertRaises(TypeError, xsd.date, 2002)
        self.assertRaises(TypeError, xsd.date, 2002, 10)
        self.verifyTime(xsd.date(2002, 10, 27), with_tzinfo=False)

    def testXsdLiteral (self):
        dt = xsd.date('2002-10-27')
        self.assertEqual('2002-10-27', dt.xsdLiteral())

    def testTimezoned (self):
        dt = xsd.date('2002-10-10Z')
        self.assertEqual('2002-10-10T00:00:00+00:00', dt.isoformat())
        self.assertEqual('2002-10-10Z', dt.xsdLiteral())

        dt = xsd.date('2002-10-10+13:00')
        self.assertEqual('2002-10-10T00:00:00+13:00', dt.isoformat())
        self.assertEqual('2002-10-09-11:00', dt.xsdLiteral())
        dt = xsd.date('2002-10-09-11:00')
        self.assertEqual('2002-10-09T00:00:00-11:00', dt.isoformat())
        self.assertEqual('2002-10-09-11:00', dt.xsdLiteral())

        dt = xsd.date('2002-10-10+14:00')
        self.assertEqual('2002-10-10T00:00:00+14:00', dt.isoformat())
        self.assertEqual('2002-10-09-10:00', dt.xsdLiteral())
        dt = xsd.date('2002-10-09-10:00')
        self.assertEqual('2002-10-09T00:00:00-10:00', dt.isoformat())
        self.assertEqual('2002-10-09-10:00', dt.xsdLiteral())

        dt = xsd.date('2002-10-10-14:00')
        self.assertEqual('2002-10-10T00:00:00-14:00', dt.isoformat())
        self.assertEqual('2002-10-11+10:00', dt.xsdLiteral())
        dt = xsd.date('2002-10-11+10:00')
        self.assertEqual('2002-10-11T00:00:00+10:00', dt.isoformat())
        self.assertEqual('2002-10-11+10:00', dt.xsdLiteral())

if __name__ == '__main__':
    unittest.main()
