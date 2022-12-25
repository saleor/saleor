# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="f13p8">
    <xs:restriction base="xs:decimal">
      <xs:totalDigits value="13"/>
      <xs:fractionDigits value="8"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="e13p8" type="f13p8"/>
  <xs:simpleType name="f15p5">
    <xs:restriction base="xs:decimal">
      <xs:totalDigits value="15"/>
      <xs:fractionDigits value="5"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="e15p5" type="f15p5"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0091 (unittest.TestCase):
    def assertAlmostEqual (self, v1, v2, *args, **kw):
        from decimal import Decimal
        if (isinstance(v1, Decimal)
            or isinstance(v2, Decimal)):
            if not isinstance(v1, Decimal):
                v1 = Decimal(str(v1))
            if not isinstance(v2, Decimal):
                v2 = Decimal(str(v2))
        return super(TestTrac_0091, self).assertAlmostEqual(v1, v2, *args, **kw)

    def testBasic (self):
        if sys.version_info[:2] >= (2, 7):
            # Prior to 2.7 float/Decimal comparisons returned invalid results.
            self.assertEqual(1.0, e13p8(1.0))
            self.assertEqual(1.0, e13p8('1.0'))
            self.assertEqual(1234567890123.0, e13p8('1234567890123'))
            self.assertEqual(1234567890123.0, CreateFromDocument('<e13p8>1234567890123</e13p8>'))
        self.assertRaises(SimpleFacetValueError, e13p8, '12345678901234')
        self.assertAlmostEqual(1.00000001, e13p8('1.00000001'))
        self.assertRaises(SimpleFacetValueError, e13p8, '1.000000001')

    def testBadCase (self):
        # Prior to fix, this raised a facet violation due to rounding
        self.assertAlmostEqual(0.00790287, e13p8('0.00790287'))

    def test15_5 (self):
        from decimal import Decimal
        # For compatibility in Python 2.6 PyXB will convert the float
        # to a string before invoking the underlying decimal.Decimal
        fv = e15p5(1234.56789)
        self.assertTrue(fv.validateBinding())
        dv = Decimal('1234.56789')
        self.assertEqual(fv, dv)
        # In Python 2.7 decimal.Decimal will create from the float,
        # which will already be in a form that won't validate
        if sys.version_info[:2] >= (2, 7):
            self.assertRaises(SimpleFacetValueError, e15p5, Decimal(1234.56789))
        sv = e15p5('1234.56789')
        self.assertEqual(sv, dv)
        self.assertTrue(sv.validateBinding())
        self.assertTrue(e15p5('1000000.0').validateBinding())

    def testRanges (self):
        from decimal import Decimal
        o14o = [1] + ([0] * 12) + [1]
        self.assertEqual(14, len(o14o))
        o15o = [1] + ([0] * 13) + [1]
        self.assertEqual(15, len(o15o))
        o16o = [1] + ([0] * 14) + [1]
        self.assertEqual(16, len(o16o))

        self.assertTrue(e15p5(Decimal((0, o14o, 0))).validateBinding())
        self.assertTrue(e15p5(Decimal((0, o15o, 0))).validateBinding())

        # Negative exponents do not reduce total digit count
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            e15p5(Decimal((0, o16o, 0)))
        self.assertEqual(cm.exception.facet, f15p5._CF_totalDigits)
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            e15p5(Decimal((0, o16o, -1)))
        self.assertEqual(cm.exception.facet, f15p5._CF_totalDigits)

        # Positive exponents add to total digit count
        self.assertTrue(e15p5(Decimal((0, o14o, 1))).validateBinding())
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            e15p5(Decimal((0, o15o, 1)))
        self.assertEqual(cm.exception.facet, f15p5._CF_totalDigits)
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            e15p5(Decimal((0, o14o, 2)))
        self.assertEqual(cm.exception.facet, f15p5._CF_totalDigits)

        # Negative exponents affect fractionDigits only
        self.assertTrue(e15p5(Decimal((0, o15o, -1))).validateBinding())
        self.assertTrue(e15p5(Decimal((0, o15o, -5))).validateBinding())
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            e15p5(Decimal((0, o15o, -6)))
        self.assertEqual(cm.exception.facet, f15p5._CF_fractionDigits)

if __name__ == '__main__':
    unittest.main()
