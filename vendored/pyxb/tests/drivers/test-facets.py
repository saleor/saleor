# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-facets.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestFacets (unittest.TestCase):
    def testQuantity (self):
        xml = '<quantity xmlns="URN:test-facets">35</quantity>'
        instance = CreateFromDOM(pyxb.utils.domutils.StringToDOM(xml).documentElement)
        self.assertEqual(35, instance)
        self.assertTrue(isinstance(instance, quantity.typeDefinition()))
        self.assertRaises(Exception, quantity, -52)
        self.assertRaises(Exception, quantity, 100)

if __name__ == '__main__':
    unittest.main()
