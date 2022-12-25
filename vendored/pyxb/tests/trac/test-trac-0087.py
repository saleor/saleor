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
<schema xmlns="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:tgt" xmlns:tgt="urn:tgt">
  <simpleType name="def">
    <restriction base="string">
      <length value="3"/>
    </restriction>
  </simpleType>
  <complexType name="class">
    <attribute  name="and" type="string"/>
    <attribute  name="value" type="string"/>
  </complexType>
  <element name="global" type="tgt:class"/>
</schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

# Note: The generation phase should have printed:
#   Simple type {urn:tgt}def renamed to def_
#   Complex type {urn:tgt}class renamed to class_
#   Attribute {urn:tgt}class.and renamed to and_
#   Attribute {urn:tgt}class.value renamed to value_
#   Element {urn:tgt}global renamed to global_
class TestTrac_0087 (unittest.TestCase):
    def testReservedWords (self):
        # Element global
        self.assertTrue(isinstance(global_, pyxb.binding.basis.element))
        # Complex type class
        self.assertTrue(issubclass(class_, pyxb.binding.basis.complexTypeDefinition))
        # Simple type def
        self.assertTrue(issubclass(def_, pyxb.binding.datatypes.string))

    def testPyxbSymbols (self):
        xmls = '<tgt:global value="text" xmlns:tgt="urn:tgt"/>'
        instance = CreateFromDocument(xmls)
        self.assertTrue(isinstance(instance, class_))
        self.assertEqual(instance.value_, "text")

if __name__ == '__main__':
    unittest.main()
