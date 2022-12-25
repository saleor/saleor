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
  <xs:element type="xs:int" name="eOne"/>
  <xs:element type="xs:int" name="eTwo"/>
  <xs:complexType name="tElt">
    <xs:sequence>
      <xs:element ref="eOne" minOccurs="0"/>
      <xs:any namespace="##any" minOccurs="0" maxOccurs="3" processContents="lax"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="elt" type="tElt"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0182 (unittest.TestCase):
    def testOne (self):
        ia = eOne(1)
        ib = eTwo(2)
        content = [ ia, ib ]
        i = elt(*content)
        xmls = '<elt><eOne>1</eOne><eTwo>2</eTwo></elt>'
        xmld = xmls.encode('utf-8')
        self.assertEqual(i.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(i.eOne, ia)
        self.assertEqual(1, len(i.wildcardElements()))
        self.assertEqual(ib, i.wildcardElements()[0])
        self.assertEqual(i.orderedContent()[0].value, ia)
        self.assertEqual(i.orderedContent()[1].value, ib)

if __name__ == '__main__':
    unittest.main()
