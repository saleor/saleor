# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="str" type="xs:string">
    <xs:annotation><xs:documentation>elt str</xs:documentation></xs:annotation>
  </xs:element>
  <xs:element name="anon">
    <xs:complexType>
      <xs:sequence minOccurs="0" maxOccurs="unbounded">
        <xs:element ref="str"/>
      </xs:sequence>
    </xs:complexType>
    <xs:annotation><xs:documentation>elt anon</xs:documentation></xs:annotation>
  </xs:element>
  <xs:complexType name="cpl">
    <xs:annotation><xs:documentation>ctd cpl</xs:documentation></xs:annotation>
    <xs:sequence minOccurs="0" maxOccurs="unbounded">
      <xs:element name="text" type="xs:string">
        <xs:annotation><xs:documentation>elt cpl.text</xs:documentation></xs:annotation>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0079 (unittest.TestCase):
    def testDocumentation (self):
        self.assertEqual(str.documentation(), six.u('elt str'))
        self.assertEqual(anon.documentation(), six.u('elt anon'))
        self.assertEqual(cpl.__doc__, six.u('ctd cpl'))
        self.assertEqual(cpl.text.__doc__, six.u('elt cpl.text'))
        self.assertEqual(anon.typeDefinition().__doc__, six.u('elt anon'))

if __name__ == '__main__':
    unittest.main()
