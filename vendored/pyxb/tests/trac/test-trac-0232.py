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
  <xs:complexType name="tNumber">
    <xs:simpleContent>
      <xs:extension base="xs:double">
        <xs:attribute name="scale" type="xs:int"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:element name="number" type="tNumber"/>
  <xs:element name="numbers">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="number"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0232 (unittest.TestCase):
    def testValid (self):
        instance = CreateFromDocument('<numbers><number scale="2">1.5</number></numbers>')
        self.assertEqual(1.5, instance.number.value())
        self.assertEqual(2, instance.number.scale)

    def testInvalidElement (self):
        with self.assertRaises(pyxb.SimpleTypeValueError) as cm:
            instance = CreateFromDocument('''<numbers>
<number>1x5</number>
</numbers>''')
        e = cm.exception
        # NB: Location is the start tag of the containing element
        if e.location is not None:
            self.assertEqual(2, e.location.lineNumber)
            self.assertEqual(0, e.location.columnNumber)

    def testInvalidAttribute (self):
        with self.assertRaises(pyxb.SimpleTypeValueError) as cm:
            instance = CreateFromDocument('''<numbers><number scale="c">1.5</number></numbers>''')
        e = cm.exception
        # NB: Location is the start tag of the containing element
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(9, e.location.columnNumber)

if __name__ == '__main__':
    unittest.main()
