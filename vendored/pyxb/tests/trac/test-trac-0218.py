# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xst = '''<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="topLevel">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="item" type="xs:int" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0218 (unittest.TestCase):
    def testBasic (self):
        instance = topLevel()
        self.assertTrue(instance.item is not None)
        self.assertFalse(instance.item is None)
        self.assertTrue(instance.item != None)
        self.assertTrue(None != instance.item)
        self.assertFalse(instance.item)
        instance.item.extend([1,2,3,4])
        self.assertTrue(instance.item is not None)
        self.assertFalse(instance.item is None)
        self.assertTrue(instance.item != None)
        self.assertTrue(None != instance.item)
        self.assertTrue(instance.item)

if __name__ == '__main__':
    unittest.main()
