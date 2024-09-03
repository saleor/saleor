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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">

    <xs:simpleType name="TestEnum">
        <xs:restriction base="xs:string">
            <xs:enumeration value="foo"/>
            <xs:enumeration value="bar"/>
        </xs:restriction>
    </xs:simpleType>

    <xs:element name="root" type="TestEnum" nillable="true"/>

</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0195 (unittest.TestCase):

    def testValidNil (self):
        xmls = '<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="file:test_enum.xsd" xsi:nil="true"/>'
        instance = CreateFromDocument(xmls)
        self.assertTrue(instance._isNil())

    def testNotNil (self):
        xmls = '<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="file:test_enum.xsd" xsi:nil="true">foo</root>'
        self.assertRaises(pyxb.ContentInNilInstanceError, CreateFromDocument, xmls)

    def testInvalidNil (self):
        xmls = '<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="file:test_enum.xsd"/>'
        self.assertRaises(pyxb.SimpleFacetValueError, CreateFromDocument, xmls)

    def testValidNotNil (self):
        xmls = '<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="file:test_enum.xsd">foo</root>'
        instance = CreateFromDocument(xmls)
        self.assertFalse(instance._isNil())
        self.assertEqual('foo', instance)


if __name__ == '__main__':
    unittest.main()
