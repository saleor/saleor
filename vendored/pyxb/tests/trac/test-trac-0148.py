# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
import pyxb.utils.utility
from pyxb.utils.utility import MakeIdentifier

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
   <xs:complexType name="simple_type">
      <xs:simpleContent>
         <xs:extension base="xs:string"/>
      </xs:simpleContent>
      <!-- attribute cannot be here, must be in xs:extension -->
      <xs:attribute name="is_clean" type="xs:boolean"/>
   </xs:complexType>
   <xs:element name="simple_element" type="simple_type"/>
</xs:schema>'''

import unittest

class TestTrac0148 (unittest.TestCase):
    def testProcessing (self):
        self.assertRaises(pyxb.SchemaValidationError, pyxb.binding.generate.GeneratePython, schema_text=xsd)

if __name__ == '__main__':
    unittest.main()
