# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node
import pyxb.namespace

import os.path
xst = '''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:ns1="urn:issue13.1" xmlns:ns2="urn:issue13.2">
  <xs:simpleType name="tQNE">
    <xs:restriction base="xs:QName">
      <xs:enumeration value="ns1:one"/>
      <xs:enumeration value="ns1:two"/>
      <xs:enumeration value="ns2:un"/>
      <xs:enumeration value="ns2:dau"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="qne">
    <xs:complexType mixed="true">
      <xs:simpleContent>
        <xs:extension base="tQNE">
          <xs:attr name="qna" type="tQNE"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>
  <xs:element name="qn" type="xs:QName"/>
</xs:schema>
'''

ns1 = pyxb.namespace.Namespace("urn:issue13.1")
ns2 = pyxb.namespace.Namespace("urn:issue13.2")

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue13 (unittest.TestCase):
    def testEnumerations (self):
        instance = CreateFromDocument(six.u('<qne xmlns:ns1="urn:issue13.1">ns1:one</qne>'))
        self.assertEqual(instance.value(), ns1.createExpandedName('one'))
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            instance = CreateFromDocument(six.u('<qne xmlns:ns1="urn:issue13.1">ns1:un</qne>'))
        self.assertEqual('Type tQNE enumeration constraint violated by value {urn:issue13.1}un', str(cm.exception))
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            instance = CreateFromDocument(six.u('<qne xmlns:ns1="urn:issue13.2">ns1:one</qne>'))
        self.assertEqual('Type tQNE enumeration constraint violated by value {urn:issue13.2}one', str(cm.exception))

    def testElements (self):
        instance = CreateFromDocument(six.u('<qn>nons</qn>'))
        self.assertEqual(six.u('nons'), instance)
        self.assertEqual(six.u('<qn>nons</qn>').encode('utf-8'), instance.toxml('utf-8',root_only=True))
        instance = CreateFromDocument(six.u('<qn>xml:nons</qn>'))
        self.assertTrue(isinstance(instance, pyxb.namespace.ExpandedName))
        self.assertEqual(pyxb.namespace.XML, instance.namespace())
        self.assertEqual(pyxb.namespace.XML.createExpandedName('nons'), instance)
        xmld = instance.toxml('utf-8',root_only=True)
        self.assertEqual(instance, CreateFromDocument(xmld))
        self.assertEqual(six.u('<qn xmlns:xml="http://www.w3.org/XML/1998/namespace">xml:nons</qn>').encode('utf-8'), xmld)

if __name__ == '__main__':
    unittest.main()
