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
<xs:complexType name="tAddress">
  <xs:choice>
    <xs:sequence>
      <xs:element name="Line1" type="xs:string"/>
      <xs:element name="Line2" type="xs:string"/>
    </xs:sequence>
    <xs:sequence>
      <xs:element name="Missing" type="xs:string"/>
    </xs:sequence>
  </xs:choice>
</xs:complexType>
<xs:complexType name="tOther">
  <xs:sequence>
    <xs:element name="Header" type="xs:string"/>
    <xs:choice>
      <xs:sequence>
        <xs:element name="Special" type="tAddress"/>
        <xs:element name="Common" type="tAddress" minOccurs="0"/>
      </xs:sequence>
      <xs:sequence>
        <xs:element name="Common" type="tAddress"/>
      </xs:sequence>
    </xs:choice>
  </xs:sequence>
</xs:complexType>
<xs:element name="elt" type="tOther"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0033a (unittest.TestCase):
    def test (self):
        xml = '<elt><Header/><Common><Line1/><Line2/></Common></elt>'
        instance = CreateFromDocument(xml)

if __name__ == '__main__':
    unittest.main()
