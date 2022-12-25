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
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:group name="gText">
    <xs:choice>
      <xs:element ref="text"/>
      <xs:element ref="bold"/>
      <xs:element ref="ital"/>
    </xs:choice>
  </xs:group>
  <xs:complexType name="tText" mixed="true">
    <xs:group ref="gText" minOccurs="0" maxOccurs="unbounded"/>
  </xs:complexType>
  <xs:complexType name="tBold" mixed="true">
    <xs:group ref="gText" minOccurs="0" maxOccurs="unbounded"/>
  </xs:complexType>
  <xs:complexType name="tItal" mixed="true">
    <xs:group ref="gText" minOccurs="0" maxOccurs="unbounded"/>
  </xs:complexType>
  <xs:element name="text" type="tText"/>
  <xs:element name="bold" type="tBold"/>
  <xs:element name="ital" type="tItal"/>
  <xs:complexType name="tOrdered">
    <xs:sequence>
      <xs:element ref="bold" minOccurs="0" maxOccurs="unbounded"/>
      <xs:element ref="ital" minOccurs="0" maxOccurs="unbounded"/>
      <xs:element ref="text" minOccurs="0" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="ordered" type="tOrdered"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

# Assign a shared validation configuration to these types
gvc = pyxb.GlobalValidationConfig
vc = gvc.copy()
for cls in [ tText, tBold, tItal, tOrdered ]:
    cls._SetValidationConfig(vc)

from pyxb.exceptions_ import *

import unittest
import sys

class TestTrac0153 (unittest.TestCase):
    def tearDown (self):
        vc._setContentInfluencesGeneration(gvc.contentInfluencesGeneration)
        vc._setOrphanElementInContent(gvc.orphanElementInContent)
        vc._setInvalidElementInContent(gvc.invalidElementInContent)

    ExpectedText = '''<text>Intro with <bold>bold text</bold> and <ital>italicized text with <bold>bold</bold> inside</ital> ending with a little <bold>more bold</bold> text.</text>'''
    ExpectedData = ExpectedText.encode('utf-8')

    def makeText (self):
        return text('Intro with ',
                    bold('bold text'),
                    ' and ',
                    ital('italicized text with ', bold('bold'), ' inside'),
                    ' ending with a little ',
                    bold('more bold'),
                    ' text.')

    ExpectedMultit = '''<text>t1<bold>b2</bold>t3<bold>b4</bold><ital>i5</ital><bold>b6</bold></text>'''
    ExpectedMultid = ExpectedMultit.encode('utf-8')
    def makeMulti (self):
        return text('t1', bold('b2'), 't3', bold('b4'), ital('i5'), bold('b6'))

    def testDefaults (self):
        self.assertEqual(vc.contentInfluencesGeneration, vc.MIXED_ONLY)
        self.assertEqual(vc.orphanElementInContent, vc.IGNORE_ONCE)
        self.assertEqual(vc.invalidElementInContent, vc.IGNORE_ONCE)

    def testMakeText (self):
        i = self.makeText()
        self.assertEqual(2, len(i.bold))
        self.assertEqual(1, len(i.ital))
        self.assertEqual(1, len(i.ital[0].bold))
        self.assertEqual(self.ExpectedData, i.toxml('utf-8', root_only=True))
        i2 = CreateFromDocument(self.ExpectedText)
        self.assertEqual(self.ExpectedData, i2.toxml('utf-8', root_only=True))

    def testNeverCIT (self):
        i = self.makeText()
        vc._setContentInfluencesGeneration(vc.NEVER)
        # All non-element content is lost, and element content is
        # emitted in declaration order.
        xmlt = six.u('<text><bold/><bold/><ital><bold/></ital></text>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(i.toxml('utf-8', root_only=True), xmld)

    def testOrphan (self):
        i = self.makeText()
        # Drop the second bold
        dropped = i.bold.pop()
        self.assertEqual(vc.orphanElementInContent, vc.IGNORE_ONCE)
        xmlt = six.u('<text>Intro with <bold>bold text</bold> and <ital>italicized text with <bold>bold</bold> inside</ital> ending with a little  text.</text>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(i.toxml('utf-8', root_only=True), xmld)
        vc._setOrphanElementInContent(vc.GIVE_UP)
        self.assertEqual(vc.orphanElementInContent, vc.GIVE_UP)
        self.assertEqual(gvc.orphanElementInContent, gvc.IGNORE_ONCE)
        xmlt = six.u('<text>Intro with <bold>bold text</bold> and <ital>italicized text with <bold>bold</bold> inside</ital> ending with a little  text.</text>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(i.toxml('utf-8', root_only=True), xmld)
        vc._setOrphanElementInContent(vc.RAISE_EXCEPTION)
        self.assertEqual(vc.orphanElementInContent, vc.RAISE_EXCEPTION)
        self.assertEqual(gvc.orphanElementInContent, gvc.IGNORE_ONCE)
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.OrphanElementContentError, i.toxml, 'utf-8', root_only=True)
            return
        with self.assertRaises(pyxb.OrphanElementContentError) as cm:
            xmld = i.toxml('utf-8', root_only=True)
        e = cm.exception
        self.assertEqual(e.instance, i)
        self.assertEqual(e.preferred.value, dropped)

    def testOrphan2 (self):
        i = self.makeMulti()
        xmld = i.toxml('utf-8', root_only=True)
        self.assertEqual(self.ExpectedMultid, xmld)
        self.assertEqual(3, len(i.bold))
        dropped = i.bold.pop(0)
        self.assertEqual(vc.orphanElementInContent, vc.IGNORE_ONCE)
        xmlt = six.u('<text>t1t3<bold>b4</bold><ital>i5</ital><bold>b6</bold></text>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(i.toxml('utf-8', root_only=True), xmld)
        vc._setOrphanElementInContent(vc.GIVE_UP)
        # Elements in declaration order, non-element content at end
        xmlt = six.u('<text><bold>b4</bold><bold>b6</bold><ital>i5</ital>t1t3</text>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(i.toxml('utf-8', root_only=True), xmld)

    ExpectedOrderedt = '''<ordered><bold>b1</bold><bold>b2</bold><ital>i1</ital><text>t1</text></ordered>'''
    ExpectedOrderedd = ExpectedOrderedt.encode('utf-8')

    def makeOrdered (self):
        return ordered(bold('b1'), bold('b2'), ital('i1'), text('t1'))

    def testOrdered (self):
        i = self.makeOrdered()
        xmld = i.toxml('utf-8', root_only=True)
        self.assertEqual(self.ExpectedOrderedd, xmld)

if __name__ == '__main__':
    unittest.main()
