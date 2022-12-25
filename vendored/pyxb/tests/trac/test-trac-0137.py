# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import xml.dom

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>

<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="stype">
     <xs:restriction base="xs:string"/>
  </xs:simpleType>
  <xs:element name="selt" type="stype"/>
  <xs:complexType name="wrapper">
    <xs:sequence>
      <xs:element name="first" minOccurs="0"/>
      <xs:element name="second" minOccurs="0"/>
      <xs:any namespace="##any" minOccurs="0" maxOccurs="3" processContents="lax"/>
    </xs:sequence>
    <xs:attribute name="myattr" use="optional" type="xs:boolean"/>
    <xs:anyAttribute namespace="##any" processContents="lax"/>
  </xs:complexType>
  <xs:element name="wrapper" type="wrapper"/>
</xs:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0137 (unittest.TestCase):
    def setUp (self):
        # Hide the warning about failure to convert DOM node {}third
        # to a binding
        self.__basis_log = logging.getLogger('pyxb.binding.basis')
        self.__basis_loglevel = self.__basis_log.level
        self.__basis_log.setLevel(logging.ERROR)

    def tearDown (self):
        pyxb.RequireValidWhenParsing(True)
        self.__basis_log.level = self.__basis_loglevel

    def validate (self):
        xmls = '<wrapper><first/><second/><third><selt>text</selt></third></wrapper>'
        doc = pyxb.utils.domutils.StringToDOM(xmls)
        instance = wrapper.createFromDOM(doc.documentElement)
        self.assertEqual(1, len(instance.wildcardElements()))
        third = instance.wildcardElements()[0]
        self.assertTrue(isinstance(third, xml.dom.Node))
        self.assertEqual(xml.dom.Node.ELEMENT_NODE, third.nodeType)
        self.assertEqual('third', third.localName)

    def testWithValidation (self):
        pyxb.RequireValidWhenParsing(True)
        self.validate()

    def testWithoutValidation (self):
        pyxb.RequireValidWhenParsing(False)
        self.validate()

if __name__ == '__main__':
    unittest.main()
