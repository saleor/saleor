# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_boolean (unittest.TestCase):
    def testTrue (self):
        self.assertTrue(xsd.boolean(True))
        self.assertTrue(xsd.boolean("true"))
        self.assertTrue(xsd.boolean(1))
        self.assertTrue(xsd.boolean("1"))

    def testFalse (self):
        self.assertFalse(xsd.boolean(False))
        self.assertFalse(xsd.boolean("false"))
        self.assertFalse(xsd.boolean(0))
        self.assertFalse(xsd.boolean("0"))
        self.assertFalse(xsd.boolean())

    def testInvalid (self):
        self.assertRaises(SimpleTypeValueError, xsd.boolean, "True")
        self.assertRaises(SimpleTypeValueError, xsd.boolean, "FALSE")

if __name__ == '__main__':
    unittest.main()
