# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
# Undeclared XML namespace
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.utils.domutils
from xml.dom import Node

import os.path


import unittest

class TestIssue0006 (unittest.TestCase):

    local_xsd = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="ce">
    <xs:complexType name="cet">
      <xs:sequence>
        <xs:element name="s" type="xs:string"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
'''

    top_xsd = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:complexType name="cet">
    <xs:sequence>
      <xs:element name="s" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
'''

    def testNamedLocal (self):
        with self.assertRaises(pyxb.SchemaValidationError) as cm:
            code = pyxb.binding.generate.GeneratePython(schema_text=self.local_xsd)
        e = cm.exception

    def testUnnamedLocal (self):
        fixed = self.local_xsd.replace('name="cet"', '')
        code = pyxb.binding.generate.GeneratePython(schema_text=fixed)

    def testNamedTop (self):
        code = pyxb.binding.generate.GeneratePython(schema_text=self.top_xsd)

    def testUnnamedTop (self):
        broken = self.top_xsd.replace('name="cet"', '')
        with self.assertRaises(pyxb.SchemaValidationError) as cm:
            code = pyxb.binding.generate.GeneratePython(schema_text=broken)
        e = cm.exception

if __name__ == '__main__':
    unittest.main()
