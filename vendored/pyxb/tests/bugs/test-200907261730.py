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
  <xs:element name="uri" type="xs:anyURI"/>
  <xs:complexType name="uri_attr_t">
    <xs:simpleContent>
      <xs:extension base="xs:anyURI">
        <xs:attribute name="attr"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:element name="uri_attr" type="uri_attr_t"/>
  <xs:simpleType name="uri_union_st">
    <xs:union memberTypes="xs:time xs:dateTime xs:anyURI xs:decimal"/>
  </xs:simpleType>
  <xs:complexType name="uri_union_t">
    <xs:simpleContent>
      <xs:extension base="uri_union_st">
        <xs:attribute name="attr"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:element name="uri_union" type="uri_union_t"/>

</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_200907261730 (unittest.TestCase):
    def testBasic (self):
        instance = CreateFromDocument('<uri>test</uri>')
        self.assertEqual(instance, 'test')
        instance = CreateFromDocument('<uri_attr>test</uri_attr>')
        self.assertEqual(instance.value(), 'test')
        instance = CreateFromDocument('<uri_union>test</uri_union>')
        self.assertEqual(instance.value(), 'test')

    def testEmpty (self):
        instance = CreateFromDocument('<uri></uri>')
        self.assertEqual(instance, '')
        instance = CreateFromDocument('<uri/>')
        self.assertEqual(instance, '')
        instance = CreateFromDocument('<uri_attr></uri_attr>')
        self.assertEqual(instance.value(), '')
        instance = CreateFromDocument('<uri_attr/>')
        self.assertEqual(instance.value(), '')
        instance = CreateFromDocument('<uri_union></uri_union>')
        self.assertEqual(instance.value(), '')
        instance = CreateFromDocument('<uri_union/>')
        self.assertEqual(instance.value(), '')

if __name__ == '__main__':
    unittest.main()
