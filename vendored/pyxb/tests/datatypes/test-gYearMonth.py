# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb.binding.datatypes as xsd

class Test_gYearMonth (unittest.TestCase):
    def testBasic (self):
        v = xsd.gYearMonth('2002-10')
        self.assertEqual(v.year, 2002)
        self.assertEqual(v.month, 10)
        v = xsd.gYearMonth(2002, 10)
        self.assertEqual(v.year, 2002)
        self.assertEqual(v.month, 10)
        self.assertRaises(TypeError, xsd.gYearMonth, 2002)

    def testXSDLiteral (self):
        v = xsd.gYearMonth(2002, 10)
        self.assertEqual('2002-10', v.xsdLiteral())

    def testTimezoned (self):
        dt = xsd.gYearMonth('2002-10Z')
        self.assertEqual('2002-10-01T00:00:00+00:00', dt.isoformat())
        self.assertEqual('2002-10Z', dt.xsdLiteral())

        dt = xsd.gYearMonth('2002-10+13:00')
        self.assertEqual('2002-10-01T00:00:00+13:00', dt.isoformat())
        self.assertEqual('2002-10+13:00', dt.xsdLiteral())
        dt = xsd.gYearMonth('2002-10-11:00')
        self.assertEqual('2002-10-01T00:00:00-11:00', dt.isoformat())
        self.assertEqual('2002-10-11:00', dt.xsdLiteral())

        dt = xsd.gYearMonth('2002-10+14:00')
        self.assertEqual('2002-10-01T00:00:00+14:00', dt.isoformat())
        self.assertEqual('2002-10+14:00', dt.xsdLiteral())
        dt = xsd.gYearMonth('2002-10-10:00')
        self.assertEqual('2002-10-01T00:00:00-10:00', dt.isoformat())
        self.assertEqual('2002-10-10:00', dt.xsdLiteral())

        dt = xsd.gYearMonth('2002-10-14:00')
        self.assertEqual('2002-10-01T00:00:00-14:00', dt.isoformat())
        self.assertEqual('2002-10-14:00', dt.xsdLiteral())
        dt = xsd.gYearMonth('2002-10+10:00')
        self.assertEqual('2002-10-01T00:00:00+10:00', dt.isoformat())
        self.assertEqual('2002-10+10:00', dt.xsdLiteral())

    def XtestAccessor (self):
        v = xsd.gYearMonth(2002, 10)
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)

if __name__ == '__main__':
    unittest.main()
