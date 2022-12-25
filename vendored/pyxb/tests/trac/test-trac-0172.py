# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.fac
import sys

import os.path
xsd='''
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified" attributeFormDefault="unqualified">
  <!-- Essentially: (a*)* -->
  <xsd:element name="a" type="xsd:string"/>
  <xsd:complexType name="parametersType">
    <xsd:sequence minOccurs="0" maxOccurs="unbounded">
      <xsd:choice>
        <xsd:element ref="a" minOccurs="0" maxOccurs="unbounded"/>
      </xsd:choice>
    </xsd:sequence>
  </xsd:complexType>
  <xsd:element name="parameters" type="parametersType"/>
</xsd:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0172 (unittest.TestCase):
    def testBase (self):
        instance = parametersType()
        cfg = instance._automatonConfiguration()
        self.assertEqual(1, cfg.nondeterminismCount())
        # Step once
        a_ed = parametersType._UseForTag('a')
        cfg.step('a', a_ed)
        self.assertEqual(1, cfg.nondeterminismCount())
        # There are two ways to re-enter a: loop within a, or exit the
        # choice and re-enter.  Same destination, same element
        # declaration, two update instruction sets.
        cfg.step('a', a_ed)
        self.assertEqual(2, cfg.nondeterminismCount())
        # But there's a problem here, which is now trac/173
        cfg.step('a', a_ed)
        self.assertEqual(4, cfg.nondeterminismCount())
        self.assertTrue(4 < cfg.PermittedNondeterminism)
        cfg.PermittedNondeterminism = 4
        with self.assertRaises(pyxb.ContentNondeterminismExceededError) as cm:
            cfg.step('a', a_ed)

if __name__ == '__main__':
    unittest.main()
