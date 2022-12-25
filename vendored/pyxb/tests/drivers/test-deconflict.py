# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-deconflict.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestDeconflict (unittest.TestCase):
    def testAttributes (self):
        self.assertEqual(2, len(CTD_empty._ElementMap))
        ef = CTD_empty._ElementMap['content']
        self.assertEqual('content_', ef.id())
        self.assertFalse(ef.isPlural())
        self.assertTrue(ef.defaultValue() is None)
        ef = CTD_empty._ElementMap['Factory']
        self.assertEqual('Factory_', ef.id())
        self.assertFalse(ef.isPlural())
        self.assertTrue(ef.defaultValue() is None)
        self.assertEqual(2, len(CTD_empty._AttributeMap))
        self.assertEqual('toDOM_', CTD_empty._AttributeMap['toDOM'].id())
        self.assertEqual('Factory_2', CTD_empty._AttributeMap['Factory'].id())

if __name__ == '__main__':
    unittest.main()
