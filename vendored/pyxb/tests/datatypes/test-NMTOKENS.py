# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_NMTOKENS (unittest.TestCase):
    def testBasicLists (self):
        v = xsd.NMTOKENS([ "one", "_two", "three" ])
        self.assertEqual(3, len(v))
        self.assertTrue(isinstance(v[0], xsd.NMTOKEN))
        self.assertEqual("one", v[0])

    def testStringLists (self):
        v = xsd.NMTOKENS("one _two three")
        self.assertEqual(3, len(v))
        self.assertEqual("one", v[0])
        self.assertTrue(isinstance(v[0], xsd.NMTOKEN))
        self.assertRaises(SimpleTypeValueError, xsd.NMTOKENS, 'string with b@d id')

    def testInsertion (self):
        tup = ('a', 'b', 'c')
        v = xsd.NMTOKENS(tup)
        self.assertEqual(tup, tuple(v))
        v[1] = 'B'
        self.assertEqual(('a', 'B', 'c'), tuple(v))
        v[1:2] = ['B', 'b']
        self.assertEqual(('a', 'B', 'b', 'c'), tuple(v))

if __name__ == '__main__':
    unittest.main()
