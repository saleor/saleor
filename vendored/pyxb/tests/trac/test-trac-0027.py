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
  <xs:attributeGroup name="required">
    <xs:attribute name="rattr" use="required" type="xs:int"/>
    <xs:attribute name="rattr_fixed" type="xs:int" fixed="30" use="required"/>
  </xs:attributeGroup>
  <xs:attributeGroup name="optional">
    <xs:attribute name="attr" type="xs:int"/>
    <xs:attribute name="attr_def" type="xs:int" default="10"/>
    <xs:attribute name="attr_fixed" type="xs:int" fixed="20"/>
  </xs:attributeGroup>
  <xs:complexType name="opt_struct">
    <xs:attributeGroup ref="optional"/>
  </xs:complexType>
  <xs:complexType name="req_struct">
    <xs:attributeGroup ref="required"/>
  </xs:complexType>
  <xs:element name="ireq_struct" type="req_struct"/>
  <xs:element name="iopt_struct" type="opt_struct"/>
  <xs:complexType name="opt_def">
    <!-- This does have three attributes; it just changes one of the ones it inherits -->
    <xs:complexContent>
      <xs:restriction base="opt_struct">
        <xs:attribute name="attr" type="xs:int" default="5"/>
      </xs:restriction>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="iopt_def" type="opt_def"/>
  <xs:complexType name="opt_pro">
    <xs:complexContent>
      <xs:restriction base="opt_struct">
        <xs:attribute name="attr" use="prohibited"/>
        <xs:attribute name="attr_def" use="prohibited"/>
      </xs:restriction>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="iopt_pro" type="opt_pro"/>
  <xs:complexType name="opt_rest">
    <xs:complexContent>
      <xs:restriction base="opt_struct">
        <xs:attribute name="attr" type="xs:byte"/>
      </xs:restriction>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="iopt_rest" type="opt_rest"/>

<!-- TEST: Cannot put back an attribute that was removed.
  <xs:complexType name="opt_pro_ext">
    <xs:complexContent>
      <xs:extension base="opt_pro">
        <xs:attribute name="attr" type="xs:float"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
-->
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0027 (unittest.TestCase):
    def setRattr_fixed (self, instance, value):
        instance.rattr_fixed = value

    def setAttr_fixed (self, instance, value):
        instance.attr_fixed = value

    def setAttr (self, instance, value):
        instance.attr = value

    def testRequired (self):
        self.assertEqual(2, len(req_struct._AttributeMap))
        i = ireq_struct()
        self.assertRaises(pyxb.MissingAttributeError, i.validateBinding)
        self.assertTrue(i.rattr is None)
        i.rattr = -4
        self.assertEqual(-4, i.rattr)
        self.assertTrue(i._AttributeMap['rattr'].provided(i))

        self.assertRaises(pyxb.MissingAttributeError, i.validateBinding) # Should fail because rattr_fixed was not explicitly set

        self.assertFalse(i._AttributeMap['rattr_fixed'].provided(i))
        self.assertEqual(30, i.rattr_fixed)

        self.assertRaises(pyxb.AttributeChangeError, self.setRattr_fixed, i, 41)
        self.assertFalse(i._AttributeMap['rattr_fixed'].provided(i))

        i.rattr_fixed = 30
        self.assertTrue(i._AttributeMap['rattr_fixed'].provided(i))
        self.assertEqual(30, i.rattr_fixed)
        self.assertTrue(i.validateBinding())

        self.assertRaises(pyxb.AttributeChangeError, self.setRattr_fixed, i, 41)

    def testRequiredCTor (self):
        i = ireq_struct(rattr=11, rattr_fixed=30)
        self.assertTrue(i.validateBinding())

        self.assertRaises(pyxb.AttributeChangeError, ireq_struct, rattr=11, rattr_fixed=31)

    def testOptional (self):
        self.assertEqual(3, len(opt_struct._AttributeMap))
        i = iopt_struct()

        self.assertTrue(i.attr is None)

        self.assertEqual(i._AttributeMap['attr'].dataType(), xs.int)

        self.assertFalse(i._AttributeMap['attr_def'].provided(i))
        self.assertEqual(10, i.attr_def)
        i.attr_def = 11
        self.assertEqual(11, i.attr_def)
        self.assertTrue(i._AttributeMap['attr_def'].provided(i))

        self.assertFalse(i._AttributeMap['attr_fixed'].provided(i))
        self.assertEqual(20, i.attr_fixed)

        self.assertRaises(pyxb.AttributeChangeError, self.setAttr_fixed, i, 21)
        self.assertFalse(i._AttributeMap['attr_fixed'].provided(i))
        self.assertEqual(20, i.attr_fixed)

        i.attr_fixed = 20
        self.assertTrue(i._AttributeMap['attr_fixed'].provided(i))
        self.assertEqual(20, i.attr_fixed)

        i.attr = 1000
        self.assertEqual(1000, i.attr)

    def testOptionalCtor (self):
        self.assertEqual(3, len(opt_struct._AttributeMap))
        self.assertRaises(pyxb.AttributeChangeError, opt_struct, attr_fixed=21)

        i = iopt_struct(attr=1, attr_def=2, attr_fixed=20)
        self.assertTrue(i.validateBinding())

        self.assertEqual(1, i.attr)
        self.assertEqual(2, i.attr_def)

    def testOptDef (self):
        self.assertEqual(3, len(opt_def._AttributeMap))
        self.assertNotEqual(opt_struct._AttributeMap['attr'], opt_def._AttributeMap['attr'])
        self.assertEqual(opt_struct._AttributeMap['attr'].key(), opt_def._AttributeMap['attr'].key())
        self.assertEqual(opt_struct._AttributeMap['attr_def'], opt_def._AttributeMap['attr_def'])
        self.assertEqual(opt_struct._AttributeMap['attr_fixed'], opt_def._AttributeMap['attr_fixed'])
        i = opt_def()
        self.assertEqual(5, i.attr)

    def testOptPro (self):
        self.assertEqual(3, len(opt_pro._AttributeMap))
        self.assertNotEqual(opt_struct._AttributeMap['attr'], opt_pro._AttributeMap['attr'])
        self.assertTrue(opt_pro._AttributeMap['attr'].prohibited())
        self.assertNotEqual(opt_struct._AttributeMap['attr_def'], opt_pro._AttributeMap['attr_def'])
        self.assertTrue(opt_pro._AttributeMap['attr_def'].prohibited())
        self.assertEqual(opt_struct._AttributeMap['attr_fixed'], opt_pro._AttributeMap['attr_fixed'])
        i = opt_pro()
        self.assertRaises(pyxb.ProhibitedAttributeError, lambda: i.attr)

    def testOptProCtor (self):
        self.assertRaises(pyxb.ProhibitedAttributeError, opt_pro, attr=1)

    def testOptRest (self):
        self.assertEqual(3, len(opt_rest._AttributeMap))
        i = opt_rest()

        self.assertEqual(i._AttributeMap['attr'].dataType(), xs.byte)
        self.assertNotEqual(opt_struct._AttributeMap['attr'], opt_rest._AttributeMap['attr'])
        self.assertEqual(opt_struct._AttributeMap['attr_def'], opt_rest._AttributeMap['attr_def'])
        self.assertEqual(opt_struct._AttributeMap['attr_fixed'], opt_rest._AttributeMap['attr_fixed'])

        self.assertRaises(pyxb.SimpleTypeValueError, self.setAttr, i, 1000)

if __name__ == '__main__':
    unittest.main()
