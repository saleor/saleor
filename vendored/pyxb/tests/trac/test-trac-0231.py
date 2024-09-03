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
  <xs:simpleType name="rDateTime">
    <xs:restriction base="xs:dateTime">
      <xs:minInclusive value="2010-01-01T00:00:00Z"/>
      <xs:maxInclusive value="2011-01-01T00:00:00Z"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="rDate">
    <xs:restriction base="xs:date">
      <xs:minInclusive value="2010-01-01"/>
      <xs:maxInclusive value="2011-01-01"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="rGmonthDay">
    <xs:restriction base="xs:gMonthDay">
      <xs:minInclusive value="--01-01"/>
      <xs:maxInclusive value="--02-01"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="rTime">
    <xs:restriction base="xs:time">
      <xs:minInclusive value="00:00:00Z"/>
      <xs:maxInclusive value="01:00:00Z"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="rDecimal">
    <xs:restriction base="xs:decimal">
      <xs:minInclusive value="0"/>
      <xs:maxInclusive value="2340"/>
    </xs:restriction>
  </xs:simpleType>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0231 (unittest.TestCase):
    def testFacets (self):
        self.assertEqual('2010-01-01T00:00:00Z', rDateTime._CF_minInclusive.value().xsdLiteral())
        self.assertEqual('2010-01-01', rDate._CF_minInclusive.value().xsdLiteral())
        self.assertEqual('--01-01', rGmonthDay._CF_minInclusive.value().xsdLiteral())
        self.assertEqual('00:00:00Z', rTime._CF_minInclusive.value().xsdLiteral())
        self.assertEqual('2340.0', rDecimal._CF_maxInclusive.value().xsdLiteral())

if __name__ == '__main__':
    unittest.main()
