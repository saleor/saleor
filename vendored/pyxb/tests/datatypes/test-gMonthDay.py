# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb.binding.datatypes as xsd

class Test_gMonthDay (unittest.TestCase):
    def testBasic (self):
        v = xsd.gMonthDay('--10-27')
        #self.assertEqual(v.year, 2002)
        self.assertEqual(v.month, 10)
        self.assertEqual(v.day, 27)
        v = xsd.gMonthDay(10, 27)
        #self.assertEqual(v.year, 2002)
        self.assertEqual(v.month, 10)
        self.assertEqual(v.day, 27)
        self.assertRaises(TypeError, xsd.gMonthDay, 2002)

    def testXSDLiteral (self):
        v = xsd.gMonthDay(10, 27)
        self.assertEqual('--10-27', v.xsdLiteral())


    def testTimezoned (self):
        dt = xsd.gMonthDay('--10-10Z')
        self.assertEqual('1900-10-10T00:00:00+00:00', dt.isoformat())
        self.assertEqual('--10-10Z', dt.xsdLiteral())

        dt = xsd.gMonthDay('--10-10+13:00')
        self.assertEqual('1900-10-10T00:00:00+13:00', dt.isoformat())
        self.assertEqual('--10-10+13:00', dt.xsdLiteral())
        dt = xsd.gMonthDay('--10-09-11:00')
        self.assertEqual('1900-10-09T00:00:00-11:00', dt.isoformat())
        self.assertEqual('--10-09-11:00', dt.xsdLiteral())

        dt = xsd.gMonthDay('--10-10+14:00')
        self.assertEqual('1900-10-10T00:00:00+14:00', dt.isoformat())
        self.assertEqual('--10-10+14:00', dt.xsdLiteral())
        dt = xsd.gMonthDay('--10-09-10:00')
        self.assertEqual('1900-10-09T00:00:00-10:00', dt.isoformat())
        self.assertEqual('--10-09-10:00', dt.xsdLiteral())

        dt = xsd.gMonthDay('--10-10-14:00')
        self.assertEqual('1900-10-10T00:00:00-14:00', dt.isoformat())
        self.assertEqual('--10-10-14:00', dt.xsdLiteral())
        dt = xsd.gMonthDay('--10-11+10:00')
        self.assertEqual('1900-10-11T00:00:00+10:00', dt.isoformat())
        self.assertEqual('--10-11+10:00', dt.xsdLiteral())

    def XtestAccessor (self):
        v = xsd.gMonthDay(10, 27)
        self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)

if __name__ == '__main__':
    unittest.main()
