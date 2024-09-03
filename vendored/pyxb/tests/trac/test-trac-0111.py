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
  <xs:simpleType name="cards">
    <xs:restriction base="xs:string">
        <xs:enumeration value="clubs"/>
        <xs:enumeration value="hearts"/>
        <xs:enumeration value="diamonds"/>
        <xs:enumeration value="spades"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="card" type="cards"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0111 (unittest.TestCase):
    Expected = set( ('clubs', 'hearts', 'diamonds', 'spades') )
    def testItems (self):
        vals = set()
        for ee in six.iteritems(cards):
            self.assertTrue(isinstance(ee, cards._CF_enumeration._CollectionFacet_itemType))
            vals.add(ee.value())
        self.assertEqual(self.Expected, vals)

    def testIterItems (self):
        vals = set()
        for ee in six.iteritems(cards):
            self.assertTrue(isinstance(ee, cards._CF_enumeration._CollectionFacet_itemType))
            vals.add(ee.value())
        self.assertEqual(self.Expected, vals)

    def testValues (self):
        vals = set()
        for e in six.itervalues(cards):
            vals.add(e)
        self.assertEqual(self.Expected, vals)

    def testIterValues (self):
        vals = set()
        for e in six.itervalues(cards):
            vals.add(e)
        self.assertEqual(self.Expected, vals)

if __name__ == '__main__':
    unittest.main()
