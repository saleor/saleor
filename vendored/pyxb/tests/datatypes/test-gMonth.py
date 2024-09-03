# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import unittest
import pyxb.binding.datatypes as xsd

class Test_gMonth (unittest.TestCase):

    def testBasic (self):
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.gMonth, 0)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.gMonth, 13)
        v = xsd.gMonth('--10')
        self.assertEqual(v.month, 10)
        v = xsd.gMonth(10)
        self.assertEqual(v.month, 10)

    def testXSDLiteral (self):
        v = xsd.gMonth(10)
        self.assertEqual('--10', v.xsdLiteral())

    def testTimezoned (self):
        dt = xsd.gMonth('--08Z')
        self.assertEqual('1900-08-01T00:00:00+00:00', dt.isoformat())
        self.assertEqual('--08Z', dt.xsdLiteral())

        dt = xsd.gMonth('--08-14:00')
        self.assertEqual('1900-08-01T00:00:00-14:00', dt.isoformat())
        self.assertEqual('--08-14:00', dt.xsdLiteral())

        dt = xsd.gMonth('--08+14:00')
        self.assertEqual('1900-08-01T00:00:00+14:00', dt.isoformat())
        self.assertEqual('--08+14:00', dt.xsdLiteral())

    def XtestAccessor (self):
        v = xsd.gMonth(10)
        self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)


if __name__ == '__main__':
    unittest.main()
