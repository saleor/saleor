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
  <xs:simpleType name="intList">
    <xs:list itemType="xs:int"/>
  </xs:simpleType>
  <xs:element name="li" type="intList"/>
  <xs:complexType name="tAggregate">
    <xs:sequence>
      <xs:element ref="li"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="aggregate" type="tAggregate"/>
  <xs:complexType name="tMultiAggregate">
    <xs:sequence>
      <xs:element ref="li" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="multi" type="tMultiAggregate"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_200908041708 (unittest.TestCase):
    # This verifies that we can invoke xsdLiteral even when the value
    # stored in the content doesn't descend from _TypeBinding_mixin
    # (as long as it's compatible).
    def testSub (self):
        instance = aggregate(li=[])
        instance.li.append(1)
        self.assertTrue(instance.validateBinding())
        xmld = '<aggregate><li>1</li></aggregate>'.encode('utf-8')
        self.assertEqual(instance.toxml("utf-8", root_only=True), xmld)

if __name__ == '__main__':
    unittest.main()
