# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
import operator
import functools
from xml.dom import Node
from pyxb.utils.six.moves import xrange

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
 <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="eST" type="xs:int"/>
  <xs:element name="eCT">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:int">
          <xs:attribute name="units" type="xs:string" use="optional"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>
  <xs:element name="eSTs">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="eST" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:element name="eCTs">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="eCT" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0175 (unittest.TestCase):
    def testBasic (self):
        s = eST(1)
        self.assertEqual(s, 1)
        c = eCT(2)
        self.assertEqual(c.value(), 2)
        instance = eSTs(1,2,3,4)
        self.assertEqual(4, len(instance.eST))
        self.assertTrue(functools.reduce(operator.iand, map(lambda _i: operator.eq(1+_i, instance.eST[_i]), xrange(len(instance.eST))), True))
        instance = eCTs(1,2,3,4)
        self.assertEqual(4, len(instance.eCT))
        self.assertTrue(functools.reduce(operator.iand, map(lambda _i: operator.eq(1+_i, instance.eCT[_i].value()), xrange(len(instance.eCT))), True))

if __name__ == '__main__':
    unittest.main()
