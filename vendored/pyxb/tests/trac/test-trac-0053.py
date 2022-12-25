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
<xs:complexType name="tBase">
  <xs:sequence>
    <xs:any minOccurs="0" maxOccurs="unbounded"/>
  </xs:sequence>
  <xs:attribute name="attr" type="xs:NMTOKENS" use="optional"/>
</xs:complexType>
<xs:complexType name="tExt">
  <xs:complexContent>
   <xs:restriction base="tBase">
     <xs:attribute name="eattr" type="xs:string" use="required"/>
     <xs:attribute name="attr" type="xs:NMTOKENS" use="prohibited"/>
   </xs:restriction>
  </xs:complexContent>
</xs:complexType>
<xs:element name="base" type="tBase"/>
<xs:element name="ext" type="tExt"/>
</xs:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest
import xml.dom

class TestTrac_0053 (unittest.TestCase):
    def testBase (self):
        xmls = '<base attr="value"/>'
        instance = CreateFromDocument(xmls)
        self.assertTrue(isinstance(instance.attr, list))
        self.assertEqual(1, len(instance.attr))
        self.assertEqual("value", instance.attr[0])

    def testExt (self):
        xmls = '<ext eattr="value"/>'
        instance = CreateFromDocument(xmls)
        self.assertEqual("value", instance.eattr)
        # Creation from DOM takes a different code path
        domn = pyxb.utils.domutils.StringToDOM(xmls)
        instance = CreateFromDOM(domn)
        self.assertEqual("value", instance.eattr)

    def testExtMissingRequired (self):
        xmls = '<ext/>'
        self.assertRaises(pyxb.MissingAttributeError, CreateFromDocument, xmls)
        # Creation from DOM takes a different code path
        domn = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.MissingAttributeError, CreateFromDOM, domn)

if __name__ == '__main__':
    unittest.main()
