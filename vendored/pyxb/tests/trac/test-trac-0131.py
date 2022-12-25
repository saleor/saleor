# Coding declaration for unicode strings
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
# See also:
# http://www.evanjones.ca/python-utf8.html
# http://bytes.com/topic/python/answers/41153-xml-unicode-what-am-i-doing-wrong

import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
import xml.sax
import io

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">
    <xs:element name="foo" type="xs:string"/>
    <xs:element name="bar">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="e" type="xs:string" minOccurs="0"/>
            </xs:sequence>
            <xs:attribute name="a" type="xs:string"/>
        </xs:complexType>
    </xs:element>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0131 (unittest.TestCase):
    # Unicode string, UTF-8 encoding (per declaration at script top)
    strt = 'Sign of Leser-Trélat'
    strd = strt.encode('utf-8')
    base_xmlt = '<bar><e>' + strt + '</e></bar>'
    declared_xmlt = '<?xml version="1.0" encoding="UTF-8"?>' + base_xmlt

    def setUp (self):
        self.__xmlStyle = pyxb._XMLStyle

    def tearDown (self):
        pyxb._SetXMLStyle(self.__xmlStyle)

    def testRepresentation (self):
        self.assertEqual(self.strd, b'Sign of Leser-Tr\xc3\xa9lat')

    def testBasicParse (self):
        xmlt = self.base_xmlt
        xmld = xmlt.encode('utf-8')
        self.assertTrue(isinstance(xmlt, six.text_type))
        self.assertTrue(isinstance(xmld, six.binary_type))
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxer)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.strt)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.strt)
        pyxb._SetXMLStyle(pyxb.XMLStyle_minidom)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.strt)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.strt)
        # saxdom can handle Unicode representation
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxdom)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.strt)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.strt)

    def testDeclaredParse (self):
        xmlt = self.declared_xmlt
        xmld = xmlt.encode('utf-8')
        self.assertTrue(isinstance(xmlt, six.text_type))
        self.assertTrue(isinstance(xmld, six.binary_type))
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxer)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.strt)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.strt)
        pyxb._SetXMLStyle(pyxb.XMLStyle_minidom)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.strt)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.strt)
        # saxdom can handle Unicode representation
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxdom)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.strt)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.strt)

    def testElementEncode (self):
        instance = bar()
        instance.e = self.strt
        self.assertEqual(instance.e, self.strt)

    def testAttributeEncode (self):
        instance = bar()
        instance.a = self.strt
        self.assertEqual(instance.a, self.strt)

    def testuEncode (self):
        instance = foo(self.strt)
        self.assertEqual(instance, self.strt)

if __name__ == '__main__':
    unittest.main()
