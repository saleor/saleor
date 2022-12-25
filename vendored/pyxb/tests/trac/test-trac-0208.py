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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:trac-0208">
  <xs:complexType name="BaseComplex">
    <xs:complexContent mixed="false">
      <xs:extension base="xs:anyType"/>
    </xs:complexContent>
  </xs:complexType>
  <xs:complexType name="ChildComplex">
    <xs:complexContent mixed="false">
      <xs:extension xmlns:tns="urn:trac-0208" base="tns:BaseComplex"/>
    </xs:complexContent>
  </xs:complexType>
  <xs:simpleType name="BaseSimple">
    <xs:restriction base="xs:int"/>
  </xs:simpleType>
  <xs:simpleType name="ChildSimple">
    <xs:restriction xmlns:tns="urn:trac-0208" base="tns:BaseSimple"/>
  </xs:simpleType>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0208 (unittest.TestCase):

    def testBasic (self):
        pass

if __name__ == '__main__':
    unittest.main()
