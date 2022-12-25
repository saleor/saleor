# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
import gc

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="name">
    <xs:restriction base="xs:string" />
  </xs:simpleType>
  <xs:element name="Container">
    <xs:complexType>
      <xs:attribute name="name" type="name"/>
      <xs:attribute name="name2" type="name"/>
    </xs:complexType>
  </xs:element>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue0027 (unittest.TestCase):
    def testAll (self):
        st = name
        self.assertTrue(issubclass(st, xs.string))
        et = Container.typeDefinition()
        atu = et._AttributeMap.get('name')
        self.assertEqual(st, atu.dataType())
        atu = et._AttributeMap.get('name2')
        self.assertEqual(st, atu.dataType())

if __name__ == '__main__':
    unittest.main()
