# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-typeinf.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

import unittest

class TestTypeInference (unittest.TestCase):
    def testBasic (self):
        e = anyType(4) # should be int
        self.assertEqual(e.int, 4)
        self.assertTrue(e.float is None)
        self.assertTrue(e.str is None)
        e = anyType(4.4)
        self.assertTrue(e.int is None)
        self.assertEqual(e.float, 4.4)
        self.assertTrue(e.str is None)
        e = anyType("3")
        self.assertTrue(e.int is None)
        self.assertTrue(e.float is None)
        self.assertEqual(e.str, "3")

if __name__ == '__main__':
    unittest.main()
