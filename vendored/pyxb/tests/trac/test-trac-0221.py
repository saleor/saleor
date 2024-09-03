# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node
import pyxb.binding.datatypes as xs

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="english">
    <xs:restriction base="xs:string">
      <xs:enumeration value="one"/>
      <xs:enumeration value="two"/>
      <xs:enumeration value="three"/>
      <xs:enumeration value="b@d"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="conflict">
    <xs:restriction base="xs:string">
      <xs:enumeration value="items"/>
      <xs:enumeration value="two"/>
      <xs:enumeration value="values"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="po2">
    <xs:restriction base="xs:int">
      <xs:enumeration value="1"/>
      <xs:enumeration value="2"/>
      <xs:enumeration value="4"/>
      <xs:enumeration value="8"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="eng" type="english"/>
  <xs:element name="pow" type="po2"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0221 (unittest.TestCase):
    if sys.version_info[:2] < (2, 7):
        def assertIsNone (self, v):
            self.assertEqual(None, v)
        def assertIsNotNone (self, v):
            self.assertNotEqual(None, v)

    def testValueForUnicode (self):
        self.assertEqual(english.one, english._valueForUnicode(six.u('one')))
        self.assertEqual(None, english._valueForUnicode(six.u('no such element')))
        self.assertEqual(english.bd, english._valueForUnicode(six.u('b@d')))

    def testProcessing (self):
        v = CreateFromDocument('<eng>one</eng>')
        self.assertEqual(english.one, v)
        v = CreateFromDocument('<pow>8</pow>')
        self.assertEqual(po2._elementForValue(8).value(), v)
        self.assertEqual(v, po2._valueForUnicode(six.u('8')))

    def testDirect (self):
        v = po2(8)
        self.assertEqual(po2._elementForValue(8).value(), v)
        self.assertTrue(isinstance(v, po2))
        v = po2(six.u('8'))
        self.assertEqual(po2._elementForValue(8).value(), v)
        self.assertTrue(isinstance(v, po2))
        self.assertRaises(SimpleFacetValueError, po2, 9)

        v = english(six.u('b@d'))
        self.assertEqual(english.bd, v)
        self.assertRaises(SimpleFacetValueError, eng, six.u('bd'))

    def testLegacy (self):
        self.assertEqual(english.one, english._CF_enumeration.elementForValue(six.u('one')).value())

    def testElementForValue (self):
        e1 = english._elementForValue(six.u('one'))
        self.assertEqual(english.one, e1.value())
        self.assertEqual('one', e1.tag())
        self.assertRaises(KeyError, english._elementForValue, six.u('no such value'))
        ev = english._elementForValue(six.u('b@d'))
        self.assertEqual(english.bd, ev.value())

        v2 = po2._elementForValue(2)
        self.assertEqual(2, v2.value())
        self.assertIsNone(v2.tag())
        self.assertRaises(KeyError, po2._elementForValue, six.u('2'))

    def testIteratorAspects (self):
        self.assertEqual([1,2,4,8], sorted(po2.values()))
        self.assertEqual(['b@d', 'one', 'three', 'two'], sorted(english.values()))

    def testConflict (self):
        self.assertEqual(['items', 'two', 'values'], sorted(conflict.values()))
        self.assertEqual('items', conflict.items_)
        self.assertEqual('values', conflict.values_)

if __name__ == '__main__':
    unittest.main()
