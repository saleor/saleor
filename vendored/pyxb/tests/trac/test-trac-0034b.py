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
  <xs:element name="a"/>
  <xs:element name="b"/>
  <xs:element name="c"/>
  <xs:element name="d"/>
  <xs:element name="e"/>
  <xs:group name="Cabc">
    <xs:choice>
      <xs:element ref="a"/>
      <xs:element ref="b"/>
      <xs:element ref="c"/>
    </xs:choice>
  </xs:group>
  <xs:group name="Cbcd">
    <xs:choice>
      <xs:element ref="b"/>
      <xs:element ref="c"/>
      <xs:element ref="d"/>
    </xs:choice>
  </xs:group>
  <xs:group name="Cbe">
    <xs:choice>
      <xs:element ref="b"/>
      <xs:element ref="e"/>
    </xs:choice>
  </xs:group>
  <xs:group name="CabcPCbcdPCbe">
    <xs:sequence>
      <xs:group ref="Cabc"/>
      <xs:group ref="Cbcd"/>
      <xs:group ref="Cbe"/>
    </xs:sequence>
  </xs:group>
  <xs:group name="CbcdPCbe">
    <xs:sequence>
      <xs:group ref="Cbcd"/>
      <xs:group ref="Cbe"/>
    </xs:sequence>
  </xs:group>
  <xs:complexType name="aBCde">
    <xs:sequence>
      <xs:group ref="CabcPCbcdPCbe"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="Bcde">
    <xs:sequence>
      <xs:group ref="CbcdPCbe"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="aBCDE">
    <xs:sequence>
      <xs:group ref="CabcPCbcdPCbe"/>
      <xs:group ref="CbcdPCbe"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0034 (unittest.TestCase):
    def test_aBCde (self):
        instance = aBCde()
        self.assertEqual(None, instance.a)
        self.assertEqual([], instance.b)
        self.assertEqual([], instance.c)
        self.assertEqual(None, instance.d)
        self.assertEqual(None, instance.e)

    def test_Bcde (self):
        instance = Bcde()
        self.assertEqual([], instance.b)
        self.assertEqual(None, instance.c)
        self.assertEqual(None, instance.d)
        self.assertEqual(None, instance.e)

    def test_aBCDE (self):
        instance = aBCDE()
        self.assertEqual(None, instance.a)
        self.assertEqual([], instance.b)
        self.assertEqual([], instance.c)
        self.assertEqual([], instance.d)
        self.assertEqual([], instance.e)

if __name__ == '__main__':
    unittest.main()
