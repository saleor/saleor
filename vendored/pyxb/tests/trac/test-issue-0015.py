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
xst = '''<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="var_test">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="data" type="xs:anyType"/>
      </xs:sequence>
   </xs:complexType>
  </xs:element>
  <xs:simpleType name="tSimple">
     <xs:restriction base="xs:string"/>
  </xs:simpleType>
  <xs:complexType name="tComplex">
    <xs:sequence>
      <xs:element name="logstring">
        <xs:simpleType>
          <xs:restriction base="xs:string"/>
        </xs:simpleType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue15 (unittest.TestCase):
    def testSimple (self):
        vt = var_test()
        vt.data = tSimple("s")
        instance = CreateFromDOM(vt.toDOM())
        self.assertIsInstance(instance.data, tSimple)

    def testComplex (self):
        vt = var_test()
        vt.data = tComplex("c")
        instance = CreateFromDOM(vt.toDOM())
        self.assertIsInstance(instance.data, tComplex)

if __name__ == '__main__':
    unittest.main()
