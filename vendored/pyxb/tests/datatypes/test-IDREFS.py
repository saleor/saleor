# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_IDREFS (unittest.TestCase):
    def testBasicLists (self):
        v = xsd.IDREFS([ "one", "two", "three" ])
        self.assertEqual(3, len(v))
        self.assertTrue(isinstance(v[0], xsd.IDREF))
        self.assertEqual("one", v[0])

    def testStringLists (self):
        v = xsd.IDREFS("one two three")
        self.assertEqual(3, len(v))
        self.assertEqual("one", v[0])
        self.assertTrue(isinstance(v[0], xsd.IDREF))
        self.assertRaises(SimpleTypeValueError, xsd.IDREFS, 'string with b@d id')

if __name__ == '__main__':
    unittest.main()
