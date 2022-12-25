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
  <xs:simpleType name="tvColorCode">
    <xs:annotation>
      <xs:documentation>The standard color codes used to denote the color scheme used by a TV program (eg. Color, B &amp; W ...).</xs:documentation>
    </xs:annotation>
    <xs:restriction base="xs:string">
      <xs:enumeration value="B &amp; W">
        <xs:annotation>
          <xs:documentation xml:lang="en">Indicates that the program is begin telecast in Black and White.</xs:documentation>
        </xs:annotation>
      </xs:enumeration>
      <xs:enumeration value="Color">
        <xs:annotation>
          <xs:documentation xml:lang="en">Indicates that the program being telecast is in color.</xs:documentation>
        </xs:annotation>
      </xs:enumeration>
      <xs:enumeration value="Colorized">
        <xs:annotation>
          <xs:documentation xml:lang="en">Indicates that the program being telecast is a colorised version of the original program.</xs:documentation>
        </xs:annotation>
      </xs:enumeration>
      <xs:enumeration value="Color and B &amp; W">
        <xs:annotation>
          <xs:documentation xml:lang="en">Indicates that the program being telecast is partly in color and partly in Black and White.</xs:documentation>
        </xs:annotation>
      </xs:enumeration>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="colorCode" type="tvColorCode"/>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_200908161024 (unittest.TestCase):
    def testParsing (self):
        self.assertEqual('B & W', tvColorCode.B__W)
        self.assertEqual(tvColorCode.B__W, CreateFromDocument('<colorCode>B &amp; W</colorCode>'))

if __name__ == '__main__':
    unittest.main()
