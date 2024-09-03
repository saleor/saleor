# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node
import pyxb.binding.datatypes as xs

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="wrapper">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="holding">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="optional" minOccurs="0">
                <xs:complexType>
                  <xs:simpleContent>
                    <xs:extension base="xs:int">
                      <xs:attribute name="deep" type="xs:int"/>
                    </xs:extension>
                  </xs:simpleContent>
                </xs:complexType>
              </xs:element>
              <xs:element name="required">
                <xs:complexType>
                  <xs:simpleContent>
                    <xs:extension base="xs:string">
                      <xs:attribute name="deep" type="xs:int"/>
                    </xs:extension>
                  </xs:simpleContent>
                </xs:complexType>
              </xs:element>
            </xs:sequence>
            <xs:attribute name="inner" type="xs:int"/>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
      <xs:attribute name="outer" type="xs:int"/>
    </xs:complexType>
  </xs:element>
  <xs:element name="shallow">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="optional" minOccurs="0">
          <xs:complexType>
            <xs:simpleContent>
              <xs:extension base="xs:int">
                <xs:attribute name="deep" type="xs:int"/>
              </xs:extension>
            </xs:simpleContent>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
      <xs:attribute name="outer" type="xs:int"/>
    </xs:complexType>
  </xs:element>
</xs:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *
from pyxb import BIND

import unittest

def SET_optional (instance, value):
    instance.optional = value

class TestTrac0039 (unittest.TestCase):
    """Creating nested anonymous elements"""
    def testShallowSet (self):
        w = shallow()
        w.optional = 4
        self.assertEqual(w.optional.value(), 4)
        self.assertTrue(w.optional.deep is None)
        w.optional = BIND(5)
        self.assertEqual(w.optional.value(), 5)
        self.assertTrue(w.optional.deep is None)
        self.assertTrue(isinstance(w.optional.value(), xs.int))
        self.assertRaises(pyxb.SimpleTypeValueError, SET_optional, w, BIND('string'))
        w.optional = BIND(6, deep=1)
        self.assertEqual(w.optional.value(), 6)
        self.assertEqual(w.optional.deep, 1)

    def testShallowCTOR (self):
        w = shallow(BIND(5))
        self.assertTrue(isinstance(w.optional.value(), xs.int))
        self.assertEqual(w.optional.value(), 5)
        w = shallow(6)
        self.assertTrue(isinstance(w.optional.value(), xs.int))
        self.assertEqual(w.optional.value(), 6)
        self.assertRaises(pyxb.UnrecognizedContentError, shallow, BIND('string'))

    def testDeep (self):
        w = wrapper(BIND(BIND(4, deep=4), BIND('hi')))
        xmlt = six.u('<wrapper><holding><optional deep="4">4</optional><required>hi</required></holding></wrapper>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(w.toxml("utf-8", root_only=True), xmld)
        w = wrapper(BIND(BIND('hi', deep=2)))
        xmlt = six.u('<wrapper><holding><required deep="2">hi</required></holding></wrapper>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(w.toxml("utf-8", root_only=True), xmld)

if __name__ == '__main__':
    unittest.main()
