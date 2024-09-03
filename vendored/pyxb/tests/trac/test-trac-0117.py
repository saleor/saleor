# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="tABCD">
    <xs:restriction base="xs:normalizedString">
      <xs:enumeration value="A"/>
      <xs:enumeration value="B"/>
      <xs:enumeration value="C"/>
      <xs:enumeration value="D"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="Element">
   <xs:complexType>
     <xs:attribute name="attr" type="tABCD"/>
     <xs:attribute name="Required" type="xs:string" use="required"/>
   </xs:complexType>
  </xs:element>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0117 (unittest.TestCase):
    def tearDown (self):
        pyxb.RequireValidWhenGenerating(True)
        pyxb.RequireValidWhenParsing(True)

    def testRequired (self):
        xmls = '<Element/>'
        pyxb.RequireValidWhenParsing(True)
        self.assertRaises(MissingAttributeError, CreateFromDocument, xmls)
        pyxb.RequireValidWhenParsing(False)
        self.assertFalse(pyxb._ParsingRequiresValid)
        instance = CreateFromDocument(xmls)
        self.assertEqual(None, instance.attr)

    def testEnumeration (self):
        pyxb.RequireValidWhenParsing(True)
        xmls = '<Element Required="true" attr="Q"/>'
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDocument, xmls)
        pyxb.RequireValidWhenParsing(False)
        instance = CreateFromDocument(xmls)
        self.assertEqual('Q', instance.attr)

    def testGood (self):
        pyxb.RequireValidWhenParsing(True)
        xmls = '<Element Required="true" attr="D"/>'
        instance = CreateFromDocument(xmls)
        self.assertEqual('D', instance.attr)
        self.assertTrue(instance.Required)

if __name__ == '__main__':
    unittest.main()
