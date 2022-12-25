# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xsd
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-ctd-simple.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestCTDSimple (unittest.TestCase):

    def testClause4 (self):
        self.assertTrue(clause4._IsSimpleTypeContent())
        self.assertTrue(clause4._TypeDefinition == xsd.string)
        self.assertEqual(None, clause4._TypeDefinition._CF_length.value())

    def testClause3 (self):
        self.assertTrue(clause3._IsSimpleTypeContent())
        self.assertTrue(issubclass(clause3, clause4))
        self.assertTrue(clause3._TypeDefinition == xsd.string)

    def testClause2 (self):
        self.assertTrue(clause2._IsSimpleTypeContent())
        self.assertTrue(issubclass(clause2, ctype))
        self.assertTrue(issubclass(clause2._TypeDefinition, xsd.string))
        self.assertEqual(6, clause2._TypeDefinition._CF_length.value())

    def testClause1_1 (self):
        self.assertTrue(clause1_1._IsSimpleTypeContent())
        self.assertTrue(issubclass(clause1_1, clause4))
        self.assertTrue(issubclass(clause1_1._TypeDefinition, xsd.string))
        self.assertEqual(2, clause1_1._TypeDefinition._CF_minLength.value())
        self.assertEqual(4, clause1_1._TypeDefinition._CF_maxLength.value())

    def testClause1_2 (self):
        self.assertTrue(clause1_2._IsSimpleTypeContent())
        self.assertTrue(issubclass(clause1_2, clause4))
        self.assertTrue(issubclass(clause1_2._TypeDefinition, xsd.string))
        self.assertEqual(6, clause1_2._TypeDefinition._CF_length.value())

if __name__ == '__main__':
    unittest.main()
