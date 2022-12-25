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
 <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">

  <xsd:complexType name="tAny">
    <xsd:all minOccurs="0">
      <xsd:element type="xsd:int" name="a" minOccurs="1"/>
      <xsd:element type="xsd:int" name="b" minOccurs="1"/>
    </xsd:all>
  </xsd:complexType>
  <xsd:element name="eAny" type="tAny"/>
</xsd:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0179 (unittest.TestCase):
    def testBasic (self):
        instance = CreateFromDocument("<eAny/>")
        self.assertTrue(instance.a is None)
        self.assertTrue(instance.b is None)
        instance = CreateFromDocument("<eAny><a>1</a><b>2</b></eAny>")
        self.assertEqual(instance.a, 1)
        self.assertEqual(instance.b, 2)
        instance = CreateFromDocument("<eAny><b>2</b><a>1</a></eAny>")
        self.assertEqual(instance.a, 1)
        self.assertEqual(instance.b, 2)
        self.assertRaises(pyxb.IncompleteElementContentError, CreateFromDocument, "<eAny><a>1</a></eAny>")

if __name__ == '__main__':
    unittest.main()
