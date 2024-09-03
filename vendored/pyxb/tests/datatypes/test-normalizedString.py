# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_normalizedString (unittest.TestCase):
    Cases = [ ("with\nnewline", 'with newline'),
              ("with\rreturn", 'with return'),
              ("with\ttab", 'with tab'),
              ("\n\nleading newline", '  leading newline'),
              ("trailing newline\n\n", 'trailing newline  '),
              ]

    def testValid (self):
        for (lexical, value) in self.Cases:
            self.assertEqual(value, xsd.normalizedString(value))
            self.assertEqual(value, xsd.normalizedString(lexical, _from_xml=True))

    def testInvalid (self):
        for (lexical, value) in self.Cases:
            self.assertRaises(SimpleTypeValueError, xsd.normalizedString, lexical)

if __name__ == '__main__':
    unittest.main()
