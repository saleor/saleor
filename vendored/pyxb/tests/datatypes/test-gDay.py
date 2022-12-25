# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import unittest
import pyxb.binding.datatypes as xsd

class Test_gDay (unittest.TestCase):
    def testBasic (self):
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.gDay, 0)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.gDay, 42)
        v = xsd.gDay('---27')
        self.assertEqual(v.day, 27)
        v = xsd.gDay(27)
        self.assertEqual(v.day, 27)

    def testXSDLiteral (self):
        v = xsd.gDay(27)
        self.assertEqual('---27', v.xsdLiteral())

    def testTimezoned (self):
        dt = xsd.gDay('---31Z')
        self.assertEqual('1900-01-31T00:00:00+00:00', dt.isoformat())
        self.assertEqual('---31Z', dt.xsdLiteral())

        dt = xsd.gDay('---31-14:00')
        self.assertEqual('1900-01-31T00:00:00-14:00', dt.isoformat())
        self.assertEqual('---31-14:00', dt.xsdLiteral())

        dt = xsd.gDay('---31+14:00')
        self.assertEqual('1900-01-31T00:00:00+14:00', dt.isoformat())
        self.assertEqual('---31+14:00', dt.xsdLiteral())

    def XtestAccessor (self):
        v = xsd.gDay(27)
        self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)


if __name__ == '__main__':
    unittest.main()
