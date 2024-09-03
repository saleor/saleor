# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_ENTITIES (unittest.TestCase):
    def testBasicLists (self):
        v = xsd.ENTITIES([ "one", "two", "three" ])
        self.assertEqual(3, len(v))
        self.assertTrue(isinstance(v[0], xsd.ENTITY))
        self.assertEqual("one", v[0])

    def testStringLists (self):
        v = xsd.ENTITIES("one two three")
        self.assertEqual(3, len(v))
        self.assertEqual("one", v[0])
        self.assertTrue(isinstance(v[0], xsd.ENTITY))
        self.assertRaises(SimpleTypeValueError, xsd.ENTITIES, 'string with b@d id')

if __name__ == '__main__':
    unittest.main()
