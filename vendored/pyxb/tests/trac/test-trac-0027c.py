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

xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:attributeGroup name="optional">
    <xs:attribute name="attr" type="xs:int"/>
    <xs:attribute name="attr_def" type="xs:int" default="10"/>
    <xs:attribute name="attr_fixed" type="xs:int" fixed="20"/>
  </xs:attributeGroup>
  <xs:complexType name="complexBase">
    <xs:simpleContent>
      <xs:restriction base="xs:string">
        <xs:attribute name="attr"/>
      </xs:restriction>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="complexSub1">
    <xs:simpleContent>
      <xs:restriction base="complexBase">
        <xs:attributeGroup ref="optional"/>
      </xs:restriction>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="complexSub2">
    <xs:simpleContent>
      <xs:restriction base="complexBase">
        <xs:attributeGroup ref="optional"/>
      </xs:restriction>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="baseElt" type="complexBase"/>
  <xs:element name="subElt1" type="complexSub1"/>
  <xs:element name="subElt2" type="complexSub2"/>
<!--
  <xs:group name="baseGroup">
    <xs:sequence>
    </xs:sequence>
  </xs:group>
  <xs:element name="elt1">
    <xs:complexType>
      <xs:sequence>
        <xs:group ref="baseGroup"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
-->
</xs:schema>'''

#open('test.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0027b (unittest.TestCase):
    def testBasic (self):
        instance = baseElt("test")
        self.assertTrue(instance.attr is None)

    def testSub1 (self):
        instance = subElt1("test")
        self.assertEqual(instance.attr_def, 10)
        self.assertEqual(instance.attr_fixed, 20)
        self.assertTrue(instance.attr is None)

    def testSub2 (self):
        instance = subElt2("test")
        self.assertEqual(instance.attr_def, 10)
        self.assertEqual(instance.attr_fixed, 20)
        self.assertTrue(instance.attr is None)

if __name__ == '__main__':
    unittest.main()
