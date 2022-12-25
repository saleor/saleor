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
      <xsd:element type="xsd:int" name="c" minOccurs="1"/>
      <xsd:element type="xsd:int" name="d" minOccurs="1"/>
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

class TestTrac0181 (unittest.TestCase):
    def getInstance (self):
        instance = eAny()
        vc = instance._validationConfig.copy()
        instance._setValidationConfig(vc)
        instance.a = 1
        instance.d = 2
        instance.c = 3
        instance.b = 4
        return instance

    def testNEVER (self):
        i = self.getInstance()
        vc = i._validationConfig
        vc._setContentInfluencesGeneration(vc.NEVER)
        # Uses declaration order for sub-automata (alphabetic)
        xmls = '<eAny><a>1</a><b>4</b><c>3</c><d>2</d></eAny>'
        xmld = xmls.encode('utf-8')
        self.assertEqual(i.toxml('utf-8', root_only=True), xmld)

    def testALWAYS (self):
        i = self.getInstance()
        vc = i._validationConfig
        vc._setContentInfluencesGeneration(vc.ALWAYS)
        # Uses assignment order for sub-automata (numeric)
        xmls = '<eAny><a>1</a><d>2</d><c>3</c><b>4</b></eAny>'
        xmld = xmls.encode('utf-8')
        self.assertEqual(i.toxml('utf-8', root_only=True), xmld)

if __name__ == '__main__':
    unittest.main()
