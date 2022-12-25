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
  <xs:complexType name="tDescription" mixed="true">
    <xs:sequence>
      <xs:element ref="sub-description" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="sub-description" type="xs:string"/>
  <xs:element name="description" type="tDescription"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_200907231924 (unittest.TestCase):
    # This verifies that we do not improperly interpret non-element
    # content as being the content of a nested element.
    def testSub (self):
        xml = '<sub-description>Floor</sub-description>'
        instance = CreateFromDocument(xml)
        self.assertEqual(instance, 'Floor')

    def testMain (self):
        xml = '<description>Main Office</description>'
        instance = CreateFromDocument(xml)
        self.assertEqual(1, len(instance.orderedContent()))
        self.assertTrue(instance.sub_description is None)
        self.assertEqual(instance.orderedContent()[0].value, 'Main Office')

    def testMainSub (self):
        xml = '<description>Main Office<sub-description>Floor</sub-description>State</description>'
        instance = CreateFromDocument(xml)
        self.assertTrue(instance.sub_description is not None)
        self.assertEqual(instance.sub_description, 'Floor')
        self.assertEqual(3, len(instance.orderedContent()))
        self.assertEqual(instance.orderedContent()[0].value, 'Main Office')
        self.assertEqual(instance.orderedContent()[2].value, 'State')

if __name__ == '__main__':
    unittest.main()
