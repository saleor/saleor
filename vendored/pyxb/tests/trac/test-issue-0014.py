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
import xml.dom.minidom as minidom

import os.path
xst = '''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:complexType name="tWildcard">
    <xs:sequence>
      <xs:element name="elt" minOccurs="0" type="xs:string"/>
      <xs:any namespace="##any" minOccurs="0" maxOccurs="3" processContents="lax"/>
    </xs:sequence>
    <xs:attribute name="attr" use="optional" type="xs:boolean"/>
    <xs:anyAttribute namespace="##any" processContents="lax"/>
  </xs:complexType>
  <xs:element name="wildcard" type="tWildcard"/>
</xs:schema>
'''

ns1 = pyxb.namespace.Namespace("urn:issue14.1")
ns2 = pyxb.namespace.Namespace("urn:issue14.2")
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns1, 'n1')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns2, 'n2')

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue14 (unittest.TestCase):
    def testAddAttributes (self):
        x = wildcard()
        self.assertEqual(six.u('<wildcard/>'), x.toxml('utf-8', root_only=True).decode('utf-8'))
        x.attr = False
        self.assertEqual(six.u('<wildcard attr="false"/>').encode('utf-8'), x.toxml('utf-8', root_only=True))
        x._setAttribute(ns1.createExpandedName('w1'), 'val')
        self.assertEqual(six.u('<wildcard attr="false" n1:w1="val" xmlns:n1="urn:issue14.1"/>').encode('utf-8'), x.toxml('utf-8', root_only=True))

    def testAddElements (self):
        bds = pyxb.utils.domutils.BindingDOMSupport()
        elt = bds.createChildElement(ns2.createExpandedName('e2'))
        bds.appendTextChild('content', elt)
        x = wildcard()
        self.assertEqual(six.u('<wildcard/>').encode('utf-8'), x.toxml('utf-8', root_only=True))
        x._appendWildcardElement(elt)
        self.assertEqual(six.u('<wildcard xmlns:n2="urn:issue14.2"><n2:e2>content</n2:e2></wildcard>').encode('utf-8'), x.toxml('utf-8', root_only=True))


if __name__ == '__main__':
    unittest.main()
