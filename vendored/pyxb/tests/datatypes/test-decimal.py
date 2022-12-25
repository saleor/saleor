# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import sys
import unittest
import pyxb.binding.datatypes as xsd
from decimal import Decimal
import decimal
from pyxb.exceptions_ import *

class Test_decimal (unittest.TestCase):
    def assertAlmostEqual (self, v1, v2, *args, **kw):
        if (isinstance(v1, Decimal)
            or isinstance(v2, Decimal)):
            if not isinstance(v1, Decimal):
                v1 = Decimal(str(v1))
            if not isinstance(v2, Decimal):
                v2 = Decimal(str(v2))
        return super(Test_decimal, self).assertAlmostEqual(v1, v2, *args, **kw)

    def testPythonDecimal (self):
        self.assertEqual(7, Decimal('321e5').adjusted())
        self.assertEqual(-1, Decimal('0.123').adjusted())
        self.assertEqual(-1, Decimal('0.12300').adjusted())
        self.assertEqual((0, (3, 2, 1), 5), Decimal('321e5').as_tuple())
        self.assertEqual((0, (3, 2, 1, 0, 0, 0, 0, 0), 0), Decimal('32100000').as_tuple())
        self.assertEqual(Decimal('32100000'), Decimal('321e5'))
        self.assertEqual((0, (1, 2, 3), -3), Decimal('0.123').as_tuple())
        self.assertEqual((0, (1, 2, 3), -3), Decimal('000.123').as_tuple())
        self.assertEqual((0, (1, 2, 3, 0, 0), -5), Decimal('0.12300').as_tuple())
        self.assertEqual((0, (1, 2, 3, 0, 0), -7), Decimal('0.0012300').as_tuple())
        self.assertNotEqual(1.2, Decimal('1.2'))
        self.assertEqual((0, (1, 2), -1), Decimal('1.2').as_tuple())
        self.assertAlmostEqual(1.2, Decimal('1.2'))
        self.assertEqual(0, Decimal((0, (0,), 0)))
        self.assertEqual(0, Decimal((0, (), 0)))
        self.assertEqual(0, Decimal((0, (), 5)))
        self.assertEqual(0, Decimal((1, (), 5)))
        self.assertEqual(0, Decimal())

    def testLiteral (self):
        self.assertEqual('12.0', xsd.decimal.XsdLiteral(Decimal((0, (1, 2), 0))))
        self.assertEqual('1.2', xsd.decimal.XsdLiteral(Decimal((0, (1, 2), -1))))
        self.assertEqual('120.0', xsd.decimal.XsdLiteral(Decimal((0, (1, 2), 1))))
        self.assertEqual('0.012', xsd.decimal.XsdLiteral(Decimal((0, (1, 2), -3))))
        self.assertEqual('12000.0', xsd.decimal.XsdLiteral(Decimal((0, (1, 2), 3))))
        self.assertEqual('0.12', xsd.decimal.XsdLiteral(Decimal((0, (1, 2), -2))))
        self.assertEqual('0.0', xsd.decimal.XsdLiteral(Decimal((0, (), 0))))
        self.assertEqual('-0.0', xsd.decimal.XsdLiteral(Decimal((1, (), 0))))

    def testCreation (self):
        self.assertEqual(Decimal('100'), xsd.decimal('100.00'))
        self.assertEqual(Decimal('100'), xsd.decimal(100))
        self.assertEqual(Decimal('1.2'), xsd.decimal('1.2'))
        self.assertEqual(Decimal('1.2'), xsd.decimal(1.2))
        if sys.version_info[:2] >= (2, 7):
            self.assertNotEqual(Decimal('1.2'), Decimal(1.2))
        self.assertAlmostEqual(1.2, xsd.decimal(1.2))

    def testValidation (self):
        one = xsd.decimal('1')
        zero = xsd.decimal('0')
        self.assertTrue(one.validateBinding())
        self.assertTrue(zero.validateBinding())
        self.assertEqual('1.0', one.xsdLiteral())

    def testInvalidConstruction (self):
        self.assertRaises(SimpleTypeValueError, xsd.decimal, 'bogus')

        nan = Decimal('NaN')
        self.assertTrue(nan.is_nan())
        self.assertEqual('NaN', str(nan))
        self.assertRaises(SimpleTypeValueError, xsd.decimal, nan)
        self.assertRaises(SimpleTypeValueError, xsd.decimal, 'NaN')

        inf = Decimal('Infinity')
        self.assertTrue(inf.is_infinite())
        self.assertEqual('Infinity', str(inf))
        self.assertRaises(SimpleTypeValueError, xsd.decimal, inf)
        self.assertRaises(SimpleTypeValueError, xsd.decimal, 'Infinity')


if __name__ == '__main__':
    unittest.main()
