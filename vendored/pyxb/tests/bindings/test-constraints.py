# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
#import pyxb.binding.facets as facets
#import pyxb.binding.datatypes as datatypes
import pyxb.binding
import pyxb.binding.facets as facets
import pyxb.binding.datatypes as datatypes
from pyxb.utils import six
import sys

# 4.3.1 length
# 4.3.2 minLength
# 4.3.3 maxLength
# NEED 4.3.4 pattern
# 4.3.5 enumeration
# 4.3.6 whiteSpace
# 4.3.7 maxInclusive
# 4.3.8 maxExclusive
# 4.3.9 minExclusive
# 4.3.10 minInclusive
# 4.3.11 totalDigits
# 4.3.12 fractionDigits

class TLA (datatypes.string):
    pass
TLA._CF_length =  facets.CF_length(super_facet=datatypes.string._CF_length, value=datatypes.nonNegativeInteger(3))
TLA._InitializeFacetMap(TLA._CF_length)

class Password (datatypes.string):
    pass
Password._CF_minLength =  facets.CF_minLength(super_facet=datatypes.string._CF_minLength, value=datatypes.nonNegativeInteger(8))
Password._CF_maxLength =  facets.CF_maxLength(super_facet=datatypes.string._CF_maxLength, value=facets.CF_maxLength._ValueDatatype(15))
Password._InitializeFacetMap(Password._CF_minLength, Password._CF_maxLength)

class AFew (pyxb.binding.basis.STD_list):
    _ItemType = datatypes.integer
    pass
AFew._CF_minLength =  facets.CF_minLength(super_facet=datatypes.string._CF_minLength, value=datatypes.nonNegativeInteger(2))
AFew._CF_maxLength =  facets.CF_maxLength(super_facet=datatypes.string._CF_maxLength, value=facets.CF_maxLength._ValueDatatype(4))
AFew._InitializeFacetMap(AFew._CF_minLength, AFew._CF_maxLength)

class Hand (datatypes.NMTOKENS):
    pass
Hand._CF_length =  facets.CF_length(super_facet=datatypes.string._CF_length, value=datatypes.nonNegativeInteger(5))
Hand._InitializeFacetMap(Hand._CF_length)

class Cardinals (datatypes.string, facets._Enumeration_mixin):
    pass
Cardinals._CF_enumeration = facets.CF_enumeration(value_datatype=Cardinals, super_facet=datatypes.string._CF_enumeration, enum_prefix=None)
Cardinals.one = Cardinals._CF_enumeration.addEnumeration(unicode_value=six.u('one'))
Cardinals.two = Cardinals._CF_enumeration.addEnumeration(unicode_value=six.u('two'))
Cardinals.three = Cardinals._CF_enumeration.addEnumeration(unicode_value=six.u('three'))
Cardinals._InitializeFacetMap(Cardinals._CF_enumeration)

class ExclusiveFloat (datatypes.float):
    pass
ExclusiveFloat._CF_minExclusive =  facets.CF_minExclusive(super_facet=datatypes.float._CF_minExclusive, value_datatype=datatypes.float, value=datatypes.float(-5))
ExclusiveFloat._CF_maxExclusive =  facets.CF_maxExclusive(super_facet=datatypes.float._CF_maxExclusive, value_datatype=datatypes.float, value=datatypes.float(7))
ExclusiveFloat._InitializeFacetMap(ExclusiveFloat._CF_minExclusive, ExclusiveFloat._CF_maxExclusive)

class FixedPoint (datatypes.decimal):
    pass
FixedPoint._CF_totalDigits =  facets.CF_totalDigits(super_facet=datatypes.decimal._CF_totalDigits, value=facets.CF_totalDigits._ValueDatatype(5))
FixedPoint._CF_fractionDigits =  facets.CF_fractionDigits(super_facet=datatypes.decimal._CF_maxExclusive, value=facets.CF_fractionDigits._ValueDatatype(2))
FixedPoint._InitializeFacetMap(FixedPoint._CF_totalDigits, FixedPoint._CF_fractionDigits)

class ReplaceString (datatypes.string):
    pass
ReplaceString._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.replace, super_facet=datatypes.string._CF_whiteSpace)
ReplaceString._InitializeFacetMap(ReplaceString._CF_whiteSpace)

class CollapseString (datatypes.string):
    pass
CollapseString._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse, super_facet=datatypes.string._CF_whiteSpace)
CollapseString._InitializeFacetMap(CollapseString._CF_whiteSpace)

class testMaxInclusive (unittest.TestCase):
    def test (self):
        self.assertEqual(5, datatypes.byte(5))
        self.assertRaises(SimpleTypeValueError, datatypes.byte, 256)
        self.assertRaises(SimpleTypeValueError, datatypes.byte, 255)
        self.assertEqual(127, datatypes.byte(127))
        self.assertRaises(SimpleTypeValueError, datatypes.byte, -150)
        self.assertRaises(SimpleTypeValueError, datatypes.byte, -129)
        self.assertEqual(-128, datatypes.byte(-128))

class testMinMaxExclusive (unittest.TestCase):
    def test (self):
        self.assertRaises(SimpleFacetValueError, ExclusiveFloat, -10.0)
        self.assertRaises(SimpleFacetValueError, ExclusiveFloat, -5.0)
        self.assertEqual(-4.0, ExclusiveFloat(-4.0))
        self.assertEqual(0.0, ExclusiveFloat(0.0))
        self.assertEqual(6.875, ExclusiveFloat(6.875))
        self.assertRaises(SimpleFacetValueError, ExclusiveFloat, 7.0)

class testLength (unittest.TestCase):
    def test (self):
        self.assertEqual('one', TLA('one'))
        self.assertRaises(SimpleFacetValueError, TLA, 'three')
        self.assertRaises(SimpleFacetValueError, TLA, 'un')

    def testList (self):
        t = datatypes.NMTOKEN('card')
        self.assertRaises(SimpleFacetValueError, Hand, 4 * [t])
        self.assertEqual(5, len(Hand(5 * [t])))
        self.assertRaises(SimpleFacetValueError, Hand, 6 * [t])

class testMinMaxLength (unittest.TestCase):
    def test (self):
        self.assertRaises(SimpleFacetValueError, Password, 7*'x')
        self.assertEqual(8 * 'x', Password(8*'x'))
        self.assertEqual(15 * 'x', Password(15*'x'))
        self.assertRaises(SimpleFacetValueError, Password, 16*'x')

    def testList (self):
        i = datatypes.integer(2)
        self.assertRaises(SimpleFacetValueError, AFew, [])
        self.assertRaises(SimpleFacetValueError, AFew, [i])
        self.assertEqual(2, len(AFew(2 * [i])))
        self.assertEqual(3, len(AFew(3 * [i])))
        self.assertEqual(4, len(AFew(4 * [i])))
        self.assertRaises(SimpleFacetValueError, AFew, 5 * [i])

class testEnumeration (unittest.TestCase):
    def test (self):
        self.assertEqual(Cardinals.one, Cardinals('one'))
        self.assertEqual(Cardinals.one, Cardinals(six.u('one')))
        self.assertEqual(Cardinals.three, Cardinals('three'))
        self.assertEqual(Cardinals.three, Cardinals(six.u('three')))
        self.assertRaises(SimpleFacetValueError, Cardinals, 'One')
        self.assertRaises(SimpleFacetValueError, Cardinals, 'four')
        if sys.version_info[:2] >= (2, 7):
            with self.assertRaises(SimpleFacetValueError) as cm:
                Cardinals('four')
            self.assertEqual(cm.exception.facet, Cardinals._CF_enumeration)

class testDigits (unittest.TestCase):
    # FixedPoint is 5.2 (-999.99 through 999.99 for fractional)
    def assertAlmostEqual (self, v1, v2, *args, **kw):
        if (isinstance(v1, datatypes.decimal)
            or isinstance(v2, datatypes.decimal)):
            if not isinstance(v1, datatypes.decimal):
                v1 = datatypes.decimal(str(v1))
            if not isinstance(v2, datatypes.decimal):
                v2 = datatypes.decimal(str(v2))
        return super(testDigits, self).assertAlmostEqual(v1, v2, *args, **kw)

    def testTotalDigits (self):
        self.assertRaises(SimpleFacetValueError, FixedPoint, '0.001')
        self.assertAlmostEqual(0.01, FixedPoint('0.01'))
        self.assertAlmostEqual(0.12, FixedPoint('0.12'))
        self.assertRaises(SimpleFacetValueError, FixedPoint, '12.345')
        self.assertAlmostEqual(123.45, FixedPoint('123.45'))
        self.assertAlmostEqual(1, FixedPoint('1'))
        self.assertAlmostEqual(12, FixedPoint('12'))
        self.assertAlmostEqual(123, FixedPoint('123'))
        self.assertAlmostEqual(1234, FixedPoint('1234'))
        self.assertAlmostEqual(12345, FixedPoint('12345'))
        self.assertRaises(SimpleFacetValueError, FixedPoint, '123000')
        self.assertRaises(SimpleFacetValueError, FixedPoint, '123456')
        self.assertRaises(SimpleFacetValueError, FixedPoint, '1234567')
        self.assertRaises(SimpleFacetValueError, FixedPoint, '-0.001')
        self.assertAlmostEqual(-0.01, FixedPoint('-0.01'))
        self.assertAlmostEqual(-0.12, FixedPoint('-0.12'))
        self.assertRaises(SimpleFacetValueError, FixedPoint, '-12.345')
        self.assertAlmostEqual(-123.45, FixedPoint('-123.45'))
        self.assertAlmostEqual(-1, FixedPoint('-1'))
        self.assertAlmostEqual(-12, FixedPoint('-12'))
        self.assertAlmostEqual(-123, FixedPoint('-123'))
        self.assertAlmostEqual(-1234, FixedPoint('-1234'))
        self.assertAlmostEqual(-12345, FixedPoint('-12345'))
        self.assertRaises(SimpleFacetValueError, FixedPoint, '-123000')
        self.assertRaises(SimpleFacetValueError, FixedPoint, '-123456')
        self.assertRaises(SimpleFacetValueError, FixedPoint, '-1234567')

    def testFractionDigits (self):
        self.assertAlmostEqual(1, FixedPoint('1'))
        self.assertAlmostEqual(1.2, FixedPoint('1.2'))
        self.assertAlmostEqual(1.23, FixedPoint('1.23'))
        self.assertRaises(SimpleFacetValueError, FixedPoint, '1.234')
        self.assertAlmostEqual(12, FixedPoint('12'))
        self.assertAlmostEqual(12.3, FixedPoint('12.3'))
        self.assertAlmostEqual(12.34, FixedPoint('12.34'))
        self.assertRaises(SimpleFacetValueError, FixedPoint, '12.345')
        self.assertAlmostEqual(-1, FixedPoint('-1'))
        self.assertAlmostEqual(-1.2, FixedPoint('-1.2'))
        self.assertAlmostEqual(-1.23, FixedPoint('-1.23'))
        self.assertRaises(SimpleFacetValueError, FixedPoint, '-1.234')
        self.assertAlmostEqual(-12, FixedPoint('-12'))
        self.assertAlmostEqual(-12.3, FixedPoint('-12.3'))
        self.assertAlmostEqual(-12.34, FixedPoint('-12.34'))
        self.assertRaises(SimpleFacetValueError, FixedPoint, '-12.345')

    def testLexical (self):
        self.assertEqual('1.0', FixedPoint('1').xsdLiteral())
        self.assertEqual('0.1', FixedPoint('0.1').xsdLiteral())
        self.assertEqual('1.0', FixedPoint('1.0000').xsdLiteral())
        self.assertEqual('0.1', FixedPoint('0000.10000').xsdLiteral())
        self.assertEqual('1.0', FixedPoint('+1').xsdLiteral())
        self.assertEqual('-1.0', FixedPoint('-1').xsdLiteral())

class testWhitespace (unittest.TestCase):
    __Preserve = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.preserve)
    def testPreserve (self):
        cases = [ "test", "  test", "  test", "\ttest", "\ttest\n\rtoo\n" ]
        for c in cases:
            self.assertEqual(c, self.__Preserve.normalizeString(c))

    def testPreserveString (self):
        cases = [ "test", "  test", "  test", "\ttest", "\ttest\n\rtoo\n" ]
        for c in cases:
            self.assertEqual(c, datatypes.string(c))
            self.assertEqual(c, datatypes.string(six.text_type(c)))

    __Replace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.replace)
    def testReplace (self):
        self.assertEqual("test", self.__Replace.normalizeString("test"))
        self.assertEqual("  test", self.__Replace.normalizeString("  test"))
        self.assertEqual(" test", self.__Replace.normalizeString("\ttest"))
        self.assertEqual(" test  ", self.__Replace.normalizeString("\ttest\n\r"))
        self.assertEqual(" test  too ", self.__Replace.normalizeString("\ttest\n\rtoo\n"))
        self.assertEqual("test", self.__Replace.normalizeString(six.u("test")))
        self.assertEqual("  test", self.__Replace.normalizeString(six.u("  test")))
        self.assertEqual(" test", self.__Replace.normalizeString(six.u("\ttest")))
        self.assertEqual(" test  ", self.__Replace.normalizeString(six.u("\ttest\n\r")))
        self.assertEqual(" test  too ", self.__Replace.normalizeString(six.u("\ttest\n\rtoo\n")))

    def testReplaceString (self):
        self.assertEqual("test", ReplaceString("test", _from_xml=True))
        self.assertEqual("  test", ReplaceString("  test", _from_xml=True))
        self.assertEqual(" test", ReplaceString("\ttest", _from_xml=True))
        self.assertEqual(" test  ", ReplaceString("\ttest\n\r", _from_xml=True))
        self.assertEqual(" test  too ", ReplaceString("\ttest\n\rtoo\n", _from_xml=True))
        self.assertEqual("test", ReplaceString(six.u("test"), _from_xml=True))
        self.assertEqual("  test", ReplaceString(six.u("  test"), _from_xml=True))
        self.assertEqual(" test", ReplaceString(six.u("\ttest"), _from_xml=True))
        self.assertEqual(" test  ", ReplaceString(six.u("\ttest\n\r"), _from_xml=True))
        self.assertEqual(" test  too ", ReplaceString(six.u("\ttest\n\rtoo\n"), _from_xml=True))

    __Collapse = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
    def testCollapse (self):
        self.assertEqual("test", self.__Collapse.normalizeString("test"))
        self.assertEqual("test", self.__Collapse.normalizeString("  test"))
        self.assertEqual("test", self.__Collapse.normalizeString("\ttest"))
        self.assertEqual("test", self.__Collapse.normalizeString("\ttest\n\r"))
        self.assertEqual("test too", self.__Collapse.normalizeString("\ttest\n\rtoo\n"))
        self.assertEqual("test", self.__Collapse.normalizeString(six.u("test")))
        self.assertEqual("test", self.__Collapse.normalizeString(six.u("  test")))
        self.assertEqual("test", self.__Collapse.normalizeString(six.u("\ttest")))
        self.assertEqual("test", self.__Collapse.normalizeString(six.u("\ttest\n\r")))
        self.assertEqual("test too", self.__Collapse.normalizeString(six.u("\ttest\n\rtoo\n")))

    def testCollapseString (self):
        # The way it will work if from DOM content:
        self.assertEqual("test", CollapseString("test", _from_xml=True))
        self.assertEqual("test", CollapseString("  test", _from_xml=True))
        self.assertEqual("test", CollapseString("\ttest", _from_xml=True))
        self.assertEqual("test", CollapseString("\ttest\n\r", _from_xml=True))
        self.assertEqual("test too", CollapseString("\ttest\n\rtoo\n", _from_xml=True))
        self.assertEqual("test", CollapseString(six.u("test"), _from_xml=True))
        self.assertEqual("test", CollapseString(six.u("  test"), _from_xml=True))
        self.assertEqual("test", CollapseString(six.u("\ttest"), _from_xml=True))
        self.assertEqual("test", CollapseString(six.u("\ttest\n\r"), _from_xml=True))
        self.assertEqual("test too", CollapseString(six.u("\ttest\n\rtoo\n"), _from_xml=True))

    def testApplyWhitespace (self):
        goal = 'one two'
        source = '  one    two   '
        self.assertEqual(goal, CollapseString(goal, _from_xml=True))
        self.assertEqual(goal, CollapseString(source, _from_xml=True))
        self.assertEqual(source, CollapseString(source, _apply_whitespace_facet=False, _from_xml=True))

if __name__ == '__main__':
    unittest.main()
