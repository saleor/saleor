# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node

import os.path
xst = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="ival" type="xs:int"/>
  <xs:element name="sval" type="xs:string"/>
  <xs:complexType name="tInt">
    <xs:simpleContent>
      <xs:extension base="xs:int">
        <xs:attribute name="units" type="xs:string"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:element name="Int" type="tInt"/>
  <xs:complexType name="tStr">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attribute name="version" type="xs:int"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:element name="Str" type="tStr"/>
  <xs:complexType name="tMixed" mixed="true">
    <xs:sequence>
      <xs:element name="mString" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="Mixed" type="tMixed"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0211 (unittest.TestCase):
    def testInvalidComplex (self):
        # Various values all being 4.
        bsv4 = ival(4)
        usv4 = ival.typeDefinition()(4)
        cv4 = Int(4)
        self.assertEqual(bsv4, 4)
        self.assertEqual(bsv4, usv4)
        self.assertEqual(bsv4, cv4.value())

        # Disallow creation from XML
        xmlt = six.u('<Int><ival>4</ival></Int>')
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.NonElementValidationError, CreateFromDocument, xmlt)
        else:
            with self.assertRaises(pyxb.NonElementValidationError) as cm:
                instance = CreateFromDocument(xmlt)
            e = cm.exception
            self.assertTrue(isinstance(e.element, (ival.typeDefinition(), Node)))

        # Allow creation from unbound simple value
        instance = Int(usv4)
        self.assertEqual(instance.value(), 4)

        # Allow creation from bound simple value.  For now.
        instance = Int(bsv4)
        self.assertEqual(instance.value(), 4)

        # Disallow creation from complex value.
        self.assertRaises(pyxb.NonElementValidationError, Int, cv4)

    def testInvalidSimple (self):
        # Disallow creation from XML
        xmlt = six.u('<ival><ival>4</ival></ival>')
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.NonElementValidationError, CreateFromDocument, xmlt)
        else:
            with self.assertRaises(pyxb.NonElementValidationError) as cm:
                instance = CreateFromDocument(xmlt)
            e = cm.exception
            self.assertTrue(isinstance(e.element, (ival.typeDefinition(), Node)))

        # Create a bound instance with value 4
        bv4 = ival(4)
        self.assertTrue(isinstance(bv4, ival.typeDefinition()))
        self.assertEqual(bv4._element(), ival)

        # Create an unbound instance with value 4
        uv4 = ival.typeDefinition()(4)
        self.assertTrue(isinstance(uv4, ival.typeDefinition()))
        self.assertTrue(uv4._element() is None)

        # OK to create from an unbound instance
        instance = ival(uv4)
        self.assertEqual(4, instance)

        # OK to create from a bound instance too.  For now.
        instance = ival(bv4)
        self.assertEqual(4, instance)

    def testBasicMixed (self):
        xmlt = six.u('<Mixed><mString>body</mString></Mixed>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        xmlt = six.u('<Mixed>pre<mString>body</mString>post</Mixed>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(3, len(instance.orderedContent()))
        nec = list(pyxb.NonElementContent(instance))
        self.assertEqual(2, len(nec))
        self.assertEqual(nec[0], six.u('pre'))
        self.assertEqual(nec[1], six.u('post'))

        # Yes, I know this is weird.  It's what PyXB does with this:
        # consume what's type-compatible as an element, and append the
        # rest as mixed content.
        instance = Mixed('body', 'post')
        self.assertEqual('body', instance.mString)
        self.assertEqual('post', ''.join(pyxb.NonElementContent(instance)))

        # This is more interesting: what isn't type-compatible gets to
        # be mixed content.
        instance = Mixed(4, 'body', 'post')
        self.assertEqual('body', instance.mString)
        self.assertEqual('4post', ''.join(pyxb.NonElementContent(instance)))

        # Even more interesting: a bound value is implicitly converted
        # to mixed content if the type doesn't match element content.
        bv4 = ival(4)
        instance = Mixed(bv4, 'body', 'post')
        self.assertEqual('body', instance.mString)
        self.assertEqual('4post', ''.join(pyxb.NonElementContent(instance)))
        oc = instance.orderedContent()
        self.assertEqual(3, len(oc))
        oc0 = oc[0].value
        self.assertTrue(isinstance(oc0, six.text_type))
        self.assertEqual(six.u('4'), oc0)

    def testBasicSimples (self):
        xmlt = six.u('<ival>4</ival>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance, 4)
        instance = ival(4)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance, 4)

        xmlt = six.u('<Int units="m">23</Int>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance.value(), 23)
        self.assertEqual(instance.units, six.u('m'))
        instance = Int(23, units="m")
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance.value(), 23)
        self.assertEqual(instance.units, six.u('m'))

        xmlt = six.u('<sval>text</sval>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance, six.u('text'))
        instance = sval(six.u('text'))
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance, six.u('text'))

        xmlt = six.u('<Str version="3">text</Str>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance.value(), six.u('text'))
        self.assertEqual(instance.version, 3)
        instance = Str(six.u('text'), version=3)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance.value(), six.u('text'))
        self.assertEqual(instance.version, 3)

if __name__ == '__main__':
    unittest.main()
