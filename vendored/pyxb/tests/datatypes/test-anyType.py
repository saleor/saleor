# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb.binding.datatypes as xsd

class subAny (xsd.anyType):
    pass

class Test_anyType (unittest.TestCase):
    def testUrType (self):
        self.assertFalse(xsd.anySimpleType._IsUrType())
        self.assertTrue(xsd.anyType._IsUrType())
        self.assertFalse(subAny._IsUrType())

    def testConstructor (self):
        # Just verify you can construct them.  If you want to do
        # anything with them, you should have picked a type.
        s = xsd.anyType('string')
        i = xsd.anyType(43)

if __name__ == '__main__':
    unittest.main()
