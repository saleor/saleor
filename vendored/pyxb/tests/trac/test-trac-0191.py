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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:trac0191" xmlns="urn:trac0191" attributeFormDefault="qualified">
  <xs:complexType name="tElt">
    <xs:attribute  name="Namespace" type="xs:string"/>
    <xs:attribute  name="More" type="xs:string"/>
  </xs:complexType>
  <xs:element name="elt" type="tElt"/>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

# Note: The generation phase should have printed:
#   Attribute {urn:trac0191}tElt.{urn:trac0191}Namespace renamed to Namespace_
class TestTrac_0191 (unittest.TestCase):
    def testPyxbSymbols (self):
        xmls = '<ns1:elt ns1:Namespace="one" xmlns:ns1="urn:trac0191"/>'
        i = CreateFromDocument(xmls)
        self.assertEqual(i.Namespace_, 'one')

if __name__ == '__main__':
    unittest.main()
