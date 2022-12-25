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
  <xs:element name="a" type="xs:string"/>
  <xs:complexType name="mType">
   <xs:sequence>
     <xs:element ref="a" minOccurs="0" maxOccurs="unbounded"/>
   </xs:sequence>
  </xs:complexType>
  <xs:element name="m" type="mType"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0201 (unittest.TestCase):
    def testBasicList (self):
        lst = []
        lst.insert(0, 'one')
        lst.insert(0, 'zero')
        self.assertEqual(lst, ['zero', 'one'])

    def testElementList (self):
        i = m()
        i.a.insert(0, 'one')
        i.a.insert(0, 'zero')
        self.assertEqual(i.a, ['zero', 'one'])

if __name__ == '__main__':
    unittest.main()
