# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:redefine/>
</xs:schema>'''

from pyxb.exceptions_ import *

import unittest

class TestTrac_0093 (unittest.TestCase):
    def testRedefine (self):
        self.assertRaises(pyxb.IncompleteImplementationError, pyxb.binding.generate.GeneratePython, schema_text=xsd)

if __name__ == '__main__':
    unittest.main()
