# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class _TestIntegerType (object):
    """Base class for testing any datatype that descends from integer.

    Subclasses should define class variables:
    THIS_TYPE = the xsd datatype class
    PARENT_TYPE = the next dominating type in the hierarchy
    MIN_IN_RANGE = the minimum expressible value
    MAX_IN_RANGE = the maximum expressible value

    Optional values to set:
    ZERO_IN_RANGE = False if zero not valid for subclass; default is True

    """

    MIN_IN_RANGE = None
    ZERO_IN_RANGE = True
    MAX_IN_RANGE = None

    def testParentage (self):
        self.assertTrue(self.PARENT_TYPE == self.THIS_TYPE.XsdSuperType())

    def testRange (self):
        if self.MIN_IN_RANGE is not None:
            if not ((self.MIN_IN_RANGE-1) in self.PARENT_EXCLUDE):
                self.assertRaises(SimpleTypeValueError, self.THIS_TYPE, self.MIN_IN_RANGE - 1)
            self.assertEqual(self.MIN_IN_RANGE, self.THIS_TYPE(self.MIN_IN_RANGE))
        if self.ZERO_IN_RANGE:
            self.assertEqual(0, self.THIS_TYPE(0))
        if self.MAX_IN_RANGE is not None:
            self.assertEqual(self.MAX_IN_RANGE, self.THIS_TYPE(self.MAX_IN_RANGE))
            if not ((self.MAX_IN_RANGE+1) in self.PARENT_EXCLUDE):
                self.assertRaises(SimpleTypeValueError, self.THIS_TYPE, self.MAX_IN_RANGE+1)

    PARENT_EXCLUDE = []

    def testStringConversion (self):
        numbers = [ ]
        if self.MIN_IN_RANGE is not None:
            numbers.extend([self.MIN_IN_RANGE-1, self.MIN_IN_RANGE])
        if self.ZERO_IN_RANGE:
            numbers.append(0)
        if self.MAX_IN_RANGE is not None:
            numbers.extend([self.MAX_IN_RANGE, self.MAX_IN_RANGE+1])
        for n in numbers:
            s = '%d' % (n,)
            p = None
            if not (n in self.PARENT_EXCLUDE):
                p = self.PARENT_TYPE(n)
                self.assertEqual(n, p)
            if ((self.MIN_IN_RANGE is None) or (self.MIN_IN_RANGE <= n)) \
               and ((self.MAX_IN_RANGE is None) or (n <= self.MAX_IN_RANGE)):
                bs = self.THIS_TYPE(s)
                self.assertEqual(n, bs)
                self.assertEqual(s, bs.xsdLiteral())
                bp = self.THIS_TYPE(p)
                self.assertEqual(n, bp)
            else:
                self.assertRaises(SimpleTypeValueError, self.THIS_TYPE, s)
                if p is not None:
                    self.assertRaises(SimpleTypeValueError, self.THIS_TYPE, p)

class Test_byte (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.byte
    PARENT_TYPE = xsd.short
    MIN_IN_RANGE = -128
    MAX_IN_RANGE = 127

class Test_unsignedByte (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.unsignedByte
    PARENT_TYPE = xsd.unsignedShort
    PARENT_EXCLUDE = [ -1 ]
    MIN_IN_RANGE = 0
    MAX_IN_RANGE = 255

class Test_short (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.short
    PARENT_TYPE = xsd.int
    MIN_IN_RANGE = -32768
    MAX_IN_RANGE = 32767

class Test_unsignedShort (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.unsignedShort
    PARENT_TYPE = xsd.unsignedInt
    PARENT_EXCLUDE = [ -1 ]
    MIN_IN_RANGE = 0
    MAX_IN_RANGE = 65535

class Test_int (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.int
    PARENT_TYPE = xsd.long
    MIN_IN_RANGE = -2147483648
    MAX_IN_RANGE = 2147483647

class Test_unsignedInt (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.unsignedInt
    PARENT_TYPE = xsd.unsignedLong
    PARENT_EXCLUDE = [ -1 ]
    MIN_IN_RANGE = 0
    MAX_IN_RANGE = 4294967295

class Test_long (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.long
    PARENT_TYPE = xsd.integer
    MIN_IN_RANGE = -9223372036854775808
    MAX_IN_RANGE = 9223372036854775807

class Test_unsignedLong (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.unsignedLong
    PARENT_TYPE = xsd.nonNegativeInteger
    PARENT_EXCLUDE = [ -1 ]
    MIN_IN_RANGE = 0
    MAX_IN_RANGE = 18446744073709551615

class Test_negativeInteger (unittest.TestCase, _TestIntegerType):
    ZERO_IN_RANGE = False
    THIS_TYPE = xsd.negativeInteger
    PARENT_TYPE = xsd.nonPositiveInteger
    MAX_IN_RANGE = -1

class Test_nonPositiveInteger (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.nonPositiveInteger
    PARENT_TYPE = xsd.integer
    MAX_IN_RANGE = 0

class Test_nonNegativeInteger (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.nonNegativeInteger
    PARENT_TYPE = xsd.integer
    MIN_IN_RANGE = 0

class Test_positiveInteger (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.positiveInteger
    PARENT_TYPE = xsd.nonNegativeInteger
    MIN_IN_RANGE = 1
    ZERO_IN_RANGE = False

if __name__ == '__main__':
    unittest.main()
