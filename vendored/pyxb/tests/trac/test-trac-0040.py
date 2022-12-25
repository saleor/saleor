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
  <xs:simpleType name="tEnum">
    <xs:restriction base="xs:string">
      <xs:enumeration value="one"/>
      <xs:enumeration value="two"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="tUnion">
    <xs:union memberTypes="xs:int tEnum"/>
  </xs:simpleType>
  <xs:element name="union" type="tUnion"/>
  <xs:simpleType name="tListUnion">
    <xs:list itemType="tUnion"/>
  </xs:simpleType>
  <xs:element name="lu" type="tListUnion"/>
  <xs:complexType name="tAggregate">
    <xs:sequence>
      <xs:element ref="lu"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="aggregate" type="tAggregate"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

def SET_lu (instance, v):
    instance.lu = v

class TestTrac0040 (unittest.TestCase):
    """Storage of non-plural simple lists broken"""
    def testBasic (self):
        instance = aggregate()
        instance.lu = [1,'two',3]
        self.assertEqual(3, len(instance.lu))
        self.assertEqual(1, len(instance.orderedContent()))
        self.assertTrue(instance.validateBinding())
        # This is really the only thing that tests #40, but there
        self.assertEqual(instance.lu.xsdLiteral(), '1 two 3')

        # These also caught a missed TypeError to PyXBException conversion
        self.assertRaises(pyxb.SimpleTypeValueError, SET_lu, instance, 1)
        self.assertRaises(pyxb.SimpleTypeValueError, SET_lu, instance, [[1,'two',3], ['two',3,4]])

        instance = aggregate([1,'two',3])
        self.assertEqual(3, len(instance.lu))
        self.assertEqual(1, len(instance.orderedContent()))
        self.assertTrue(instance.validateBinding())

        instance = aggregate(lu=[1,'two',3])
        self.assertEqual(3, len(instance.lu))
        self.assertEqual(1, len(instance.orderedContent()))
        self.assertTrue(instance.validateBinding())

        instance = aggregate()
        instance.lu = []
        instance.lu.append(1)
        instance.lu.append('two')
        instance.lu.append(3)
        self.assertEqual(3, len(instance.lu))
        # Yes, the content is a single value; the members of the
        # simple type list are not visible at the content model level.
        self.assertEqual(1, len(instance.orderedContent()))
        self.assertTrue(instance.validateBinding())


if __name__ == '__main__':
    unittest.main()
