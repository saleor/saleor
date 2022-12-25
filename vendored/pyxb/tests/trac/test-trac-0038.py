# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node
import pyxb.binding.datatypes as xs

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="digits">
    <xs:restriction base="xs:byte">
      <xs:minInclusive value="1"/>
      <xs:maxInclusive value="3"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="english">
    <xs:restriction base="xs:string">
      <xs:enumeration value="one"/>
      <xs:enumeration value="two"/>
      <xs:enumeration value="three"/>
      <xs:enumeration value="b@d"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="welsh">
    <xs:restriction base="xs:string">
      <xs:enumeration value="un"/>
      <xs:enumeration value="dau"/>
      <xs:enumeration value="tri"/>
      <xs:enumeration value="b/d"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="tUnion">
    <xs:union memberTypes="digits english welsh">
      <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:enumeration value="ichi"/>
          <xs:enumeration value="ni"/>
          <xs:enumeration value="san"/>
          <xs:enumeration value="b?d"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:union>
  </xs:simpleType>
  <xs:element name="union" type="tUnion"/>
  <xs:simpleType name="bad">
    <xs:restriction base="xs:string">
      <xs:enumeration value="b@d"/>
      <xs:enumeration value="b/d"/>
      <xs:enumeration value="b?d"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="moreBad">
    <xs:union memberTypes="bad tUnion"/>
  </xs:simpleType>

</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

def SET_lu (instance, v):
    instance.lu = v

class TestTrac0038 (unittest.TestCase):
    """Visibility of enumerations within unions"""
    def testBasic (self):
        d = union('1')
        self.assertTrue(isinstance(d, digits))
        e = union('one')
        self.assertTrue(isinstance(e, english))
        self.assertEqual(e, english.one)
        self.assertEqual(e, tUnion.one)
        w = union('dau')
        self.assertTrue(isinstance(w, welsh))
        self.assertEqual(w, welsh.dau)
        self.assertEqual(w, tUnion.dau)
        self.assertRaises(pyxb.SimpleTypeValueError, union, 'deux')
        n = union('ni')
        self.assertEqual(n, tUnion.ni)

if __name__ == '__main__':
    unittest.main()
