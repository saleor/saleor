# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils

import os.path

from pyxb.exceptions_ import *

import unittest

class TestIncludeDD (unittest.TestCase):
    def testDefault (self):
        schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-include-dcu.xsd'))
        self.assertRaises(pyxb.SchemaValidationError, pyxb.binding.generate.GeneratePython, schema_location=schema_path)

if __name__ == '__main__':
    unittest.main()
