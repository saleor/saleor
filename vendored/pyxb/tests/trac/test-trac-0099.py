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
  <xs:element name="uncs" type="xs:string"/>
  <xs:element name="defs" default="value" type="xs:string"/>
  <xs:element name="defi" default="32" type="xs:int"/>
  <xs:element name="fixs" fixed="fixed" type="xs:string"/>
  <xs:element name="fixi" fixed="21" type="xs:int"/>
  <xs:element name="complex">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="uncs" minOccurs="0"/>
        <xs:element ref="defs" minOccurs="0"/>
        <xs:element ref="defi" minOccurs="0"/>
        <xs:element ref="fixs" minOccurs="0"/>
        <xs:element ref="fixi" minOccurs="0"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <!-- A tricky complex type example from the OpenGIS Catalogue Service (CSW) -->
  <xs:element name="ElementSetName" type="ElementSetNameType" id="ElementSetName" default="summary"/>
  <xs:complexType name="ElementSetNameType" id="ElementSetNameType">
    <xs:simpleContent>
      <xs:extension base="ElementSetType">
        <xs:attribute name="attr" type="xs:string" default="val"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:simpleType name="ElementSetType" id="ElementSetType">
    <xs:restriction base="xs:string">
      <xs:enumeration value="brief"/>
      <xs:enumeration value="summary"/>
      <xs:enumeration value="full"/>
    </xs:restriction>
  </xs:simpleType>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest
import sys

class TestTrac0099 (unittest.TestCase):
    def testCtor (self):
        i = defs()
        self.assertEqual('value', i)
        i = defs('other')
        self.assertEqual('other', i)
        i = fixs()
        self.assertEqual('fixed', i)
        i = fixs('fixed')
        self.assertEqual('fixed', i)
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.ElementChangeError, fixs, 'other')
            return
        with self.assertRaises(pyxb.ElementChangeError) as cm:
            i = fixs('other')
        e = cm.exception
        self.assertEqual(e.value, 'other')
        self.assertEqual('Value other for element fixs incompatible with fixed content', str(e))

    def testComplexCtor (self):
        i = complex(defi=52)
        self.assertEqual(None, i.uncs)
        self.assertEqual(None, i.defs)
        self.assertEqual(52, i.defi)
        self.assertEqual(None, i.fixs)
        self.assertEqual(None, i.fixi)

        self.assertEqual('value', i._UseForTag('defs').defaultValue())
        self.assertEqual(32, i._UseForTag('defi').defaultValue())
        self.assertEqual('fixed', i._UseForTag('fixs').defaultValue())
        self.assertEqual(21, i._UseForTag('fixi').defaultValue())

        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.ElementChangeError, complex, fixs='hi')
            return
        with self.assertRaises(pyxb.ElementChangeError) as cm:
            i = complex(fixs='hi')
        e = cm.exception
        self.assertEqual(e.value, 'hi')

    def testAssign (self):
        i = complex()
        # Can assign the fixed value
        i.fixs = 'fixed'
        if sys.version_info[:2] < (2, 7):
            return
        # Cannot assign a non-fixed value
        with self.assertRaises(pyxb.ElementChangeError) as cm:
            i.fixs = 'hi'
        e = cm.exception
        self.assertEqual(e.value, 'hi')

    def testCSW (self):
        i = ElementSetName('brief')
        self.assertEqual('brief', i.value())
        self.assertEqual('val', i.attr)
        i = ElementSetName()
        self.assertEqual('summary', i.value())
        self.assertEqual('val', i.attr)
        i = ElementSetName(attr='other')
        self.assertEqual('summary', i.value())
        self.assertEqual('other', i.attr)

if __name__ == '__main__':
    unittest.main()
