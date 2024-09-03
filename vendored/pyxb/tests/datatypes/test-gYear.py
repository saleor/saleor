# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import unittest
import pyxb.binding.datatypes as xsd

class Test_gYear (unittest.TestCase):
    def testBasic (self):
        v = xsd.gYear('1234')
        self.assertEqual(v.year, 1234)
        v = xsd.gYear(1234)
        self.assertEqual(v.year, 1234)

    def testXSDLiteral (self):
        v = xsd.gYear(1234)
        self.assertEqual('1234', v.xsdLiteral())

    def testTimezoned (self):
        dt = xsd.gYear('2002Z')
        self.assertEqual('2002-01-01T00:00:00+00:00', dt.isoformat())
        self.assertEqual('2002Z', dt.xsdLiteral())

        dt = xsd.gYear('2002-14:00')
        self.assertEqual('2002-01-01T00:00:00-14:00', dt.isoformat())
        self.assertEqual('2002-14:00', dt.xsdLiteral())

        dt = xsd.gYear('2002+14:00')
        self.assertEqual('2002-01-01T00:00:00+14:00', dt.isoformat())
        self.assertEqual('2002+14:00', dt.xsdLiteral())

    def XtestAccessor (self):
        v = xsd.gYear(1234)
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)


if __name__ == '__main__':
    unittest.main()
