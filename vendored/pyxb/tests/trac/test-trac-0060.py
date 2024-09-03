# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
from pyxb.utils import six
from pyxb.namespace.builtin import XMLSchema_instance as XSI

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
<xs:complexType name="BaseT" abstract="true"/>
<xs:complexType name="String">
  <xs:complexContent>
    <xs:extension base="BaseT">
      <xs:sequence>
        <xs:element name="child" type="xs:string"/>
      </xs:sequence>
    </xs:extension>
  </xs:complexContent>
</xs:complexType>
<xs:complexType name="Integer">
  <xs:complexContent>
    <xs:extension base="BaseT">
      <xs:sequence>
        <xs:element name="child" type="xs:integer"/>
      </xs:sequence>
    </xs:extension>
  </xs:complexContent>
</xs:complexType>
<xs:complexType name="Foreign">
  <xs:sequence>
    <xs:element name="child" type="xs:string"/>
  </xs:sequence>
</xs:complexType>
<xs:element name="base" type="BaseT"/>
<xs:element name="string" type="String"/>
<xs:element name="integer" type="Integer"/>
<xs:element name="wildcard">
  <xs:complexType>
    <xs:sequence>
      <xs:any/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0060 (unittest.TestCase):
    def setUp (self):
        self.__basis_log = logging.getLogger('pyxb.binding.basis')
        self.__basis_loglevel = self.__basis_log.level

    def tearDown (self):
        self.__basis_log.level = self.__basis_loglevel
        XSI.ProcessTypeAttribute(XSI.PT_strict)

    AString = 'hi'
    NotAnInteger = 'not an integer'
    AnInteger = 34
    BaseUntyped = '<base><child>%s</child></base>' % (NotAnInteger,)
    BaseString = '<base xsi:type="String" xmlns:xsi="%s"><child>%s</child></base>' % (XSI.uri(), NotAnInteger)
    BaseInteger = '<base xsi:type="Integer" xmlns:xsi="%s"><child>%d</child></base>' % (XSI.uri(), AnInteger)
    BaseForeign = '<base xsi:type="Foreign" xmlns:xsi="%s"><child>%s</child></base>' % (XSI.uri(), NotAnInteger)
    BaseUnknown = '<base xsi:type="Unknown" xmlns:xsi="%s"><child>%s</child></base>' % (XSI.uri(), NotAnInteger)
    CorrectString = '<string><child>%s</child></string>' % (AString,)
    CorrectInteger = '<integer><child>%d</child></integer>' % (AnInteger,)
    BadInteger = '<integer><child>%s</child></integer>' % (NotAnInteger,)
    ConflictString = '<integer xsi:type="String" xmlns:xsi="%s"><child>%s</child></integer>' % (XSI.uri(), NotAnInteger)
    ConflictStringInteger = '<integer xsi:type="String" xmlns:xsi="%s"><child>%d</child></integer>' % (XSI.uri(), AnInteger)
    UntypedIntegerElement = '<element><child>%d</child></element>' % (AnInteger,)
    TypedElement = '<element xsi:type="Integer" xmlns:xsi="%s"><child>%d</child></element>' % (XSI.uri(), AnInteger)
    # There is no type Float in the schema
    BogusTypedElement = '<element xsi:type="Float" xmlns:xsi="%s"><child>%d</child></element>' % (XSI.uri(), AnInteger)
    BogusTypedInteger = '<integer xsi:type="Float" xmlns:xsi="%s"><child>%d</child></integer>' % (XSI.uri(), AnInteger)

    def makeWC (self, body):
        return '<wildcard>%s</wildcard>' % (body,)

    def testWildcardString (self):
        xmls = '<wildcard>%s</wildcard>' % (self.CorrectString,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual(self.AString, instance.child)

    def testWildcardInteger (self):
        xmls = '<wildcard>%s</wildcard>' % (self.CorrectInteger,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertTrue(isinstance(instance.child, six.long_type))
        self.assertEqual(self.AnInteger, instance.child)

    def testWildcardIntegerBad (self):
        xmls = '<wildcard>%s</wildcard>' % (self.BadInteger,)
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDocument, xmls)

    def testWildcardUntyped (self):
        # Inhibit warning about conversion; we get a DOM node out of this.
        self.__basis_log.level = logging.ERROR
        xmls = '<wildcard>%s</wildcard>' % (self.UntypedIntegerElement,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertFalse(isinstance(instance, pyxb.binding.basis._TypeBinding_mixin))

    def testWildcardTyped (self):
        xmls = '<wildcard>%s</wildcard>' % (self.TypedElement,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))

    def testBase (self):
        xmls = self.makeWC(self.BaseString)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual(self.NotAnInteger, instance.child)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual(self.NotAnInteger, instance.child)

        xmls = '<wildcard>%s</wildcard>' % (self.BaseInteger,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertTrue(isinstance(instance.child, six.long_type))
        self.assertEqual(self.AnInteger, instance.child)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertTrue(isinstance(instance.child, six.long_type))
        self.assertEqual(self.AnInteger, instance.child)

    def testStrict (self):
        self.assertEqual(XSI.ProcessTypeAttribute(), XSI.PT_strict)
        xmls = '<wildcard>%s</wildcard>' % (self.ConflictString,)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDOM, dom)

        xmls = '<wildcard>%s</wildcard>' % (self.ConflictStringInteger,)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDOM, dom)

        xmls = '<wildcard>%s</wildcard>' % (self.BogusTypedElement,)
        # This only raises with saxer, which treats the bogus xsi:type as
        # a content failure.  With saxdom and minidom, that error gets
        # lost by the code that thinks it's ok to pass a DOM node where
        # no binding could be created.  This should be reconciled.
        self.assertRaises(pyxb.BadDocumentError, CreateFromDocument, xmls)

        xmls = '<wildcard>%s</wildcard>' % (self.BogusTypedInteger,)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDocument, xmls)

        xmls = self.makeWC(self.BaseUntyped)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, dom)

        xmls = self.makeWC(self.BaseForeign)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDOM, dom)

        xmls = self.makeWC(self.BaseUnknown)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.BadDocumentError, CreateFromDOM, dom)

    def testLax (self):
        # Lax won't convert DOM nodes
        self.__basis_log.level = logging.ERROR
        self.assertEqual(XSI.ProcessTypeAttribute(), XSI.PT_strict)
        XSI.ProcessTypeAttribute(XSI.PT_lax)
        xmls = '<wildcard>%s</wildcard>' % (self.ConflictString,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual(self.NotAnInteger, instance.child)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual(self.NotAnInteger, instance.child)

        xmls = '<wildcard>%s</wildcard>' % (self.ConflictStringInteger,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual('%d' % (self.AnInteger,), instance.child)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual('%d' % (self.AnInteger,), instance.child)

        xmls = '<wildcard>%s</wildcard>' % (self.BogusTypedElement,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertFalse(isinstance(instance, pyxb.binding.basis._TypeBinding_mixin))
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertFalse(isinstance(instance, pyxb.binding.basis._TypeBinding_mixin))

        xmls = '<wildcard>%s</wildcard>' % (self.BogusTypedInteger,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertTrue(isinstance(instance.child, six.long_type))
        self.assertEqual(self.AnInteger, instance.child)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertTrue(isinstance(instance.child, six.long_type))
        self.assertEqual(self.AnInteger, instance.child)

        xmls = self.makeWC(self.BaseUntyped)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, dom)

        xmls = self.makeWC(self.BaseForeign)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Foreign))
        self.assertEqual(self.NotAnInteger, instance.child)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Foreign))
        self.assertEqual(self.NotAnInteger, instance.child)

        xmls = self.makeWC(self.BaseUnknown)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, dom)


    def testSkip (self):
        # Skip won't convert DOM nodes
        self.__basis_log.level = logging.ERROR
        self.assertEqual(XSI.ProcessTypeAttribute(), XSI.PT_strict)
        XSI.ProcessTypeAttribute(XSI.PT_skip)

        # skip uses element name to force to integer, which content doesn't match
        xmls = '<wildcard>%s</wildcard>' % (self.ConflictString,)
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDOM, dom)

        xmls = '<wildcard>%s</wildcard>' % (self.ConflictStringInteger,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertEqual(self.AnInteger, instance.child)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertEqual(self.AnInteger, instance.child)

        xmls = '<wildcard>%s</wildcard>' % (self.BogusTypedElement,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertFalse(isinstance(instance, pyxb.binding.basis._TypeBinding_mixin))
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertFalse(isinstance(instance, pyxb.binding.basis._TypeBinding_mixin))

        xmls = '<wildcard>%s</wildcard>' % (self.BogusTypedInteger,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertTrue(isinstance(instance.child, six.long_type))
        self.assertEqual(self.AnInteger, instance.child)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        wc = CreateFromDOM(dom)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertTrue(isinstance(instance.child, six.long_type))
        self.assertEqual(self.AnInteger, instance.child)

        xmls = self.makeWC(self.BaseUntyped)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, dom)

        xmls = self.makeWC(self.BaseString)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, dom)

        xmls = self.makeWC(self.BaseInteger)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, dom)

        xmls = self.makeWC(self.BaseForeign)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, dom)

        xmls = self.makeWC(self.BaseUnknown)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDocument, xmls)
        dom = pyxb.utils.domutils.StringToDOM(xmls)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, dom)

if __name__ == '__main__':
    unittest.main()
