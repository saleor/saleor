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
  <xs:complexType name="reqType">
    <xs:sequence>
      <xs:element name="conf" type="confType" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="confType">
    <xs:simpleContent>
      <xs:extension base="xs:string"/>
    </xs:simpleContent>
  </xs:complexType>
  <xs:element name="req" type="reqType"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue0047 (unittest.TestCase):
    def tearDown (self):
        pyxb.RequireValidWhenGenerating(True)

    def testOne (self):
        inst = req('c1');
        self.assertEqual(six.b('<req><conf>c1</conf></req>'), inst.toxml('utf-8', root_only=True));
        pyxb.RequireValidWhenGenerating(False);
        self.assertEqual(six.b('<req><conf>c1</conf></req>'), inst.toxml('utf-8', root_only=True));

    def testTwo (self):
        inst = req('c1', 'c2');
        self.assertTrue(pyxb.RequireValidWhenGenerating());
        self.assertEqual(six.b('<req><conf>c1</conf><conf>c2</conf></req>'), inst.toxml('utf-8', root_only=True));
        pyxb.RequireValidWhenGenerating(False);
        self.assertEqual(six.b('<req><conf>c1</conf><conf>c2</conf></req>'), inst.toxml('utf-8', root_only=True));

if __name__ == '__main__':
    unittest.main()
