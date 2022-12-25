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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:complexType name="Number">
    <xs:simpleContent>
      <xs:extension base="xs:integer">
        <xs:attribute name="bounded" type="xs:boolean" default="true" />
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:element name="number" type="Number" nillable="true"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue0007 (unittest.TestCase):
    def testConstruction (self):
        # Absence of attribute uses implicit default
        i = number(53)
        self.assertEqual(six.u('<number>53</number>').encode('utf-8'), i.toxml('utf-8', root_only=True))
        self.assertTrue(i.bounded)
        # Explicit assignment of attribute makes it explicit even if same as default
        i.bounded = True
        self.assertEqual(six.u('<number bounded="true">53</number>').encode('utf-8'), i.toxml('utf-8', root_only=True))
        i.bounded = False
        self.assertEqual(six.u('<number bounded="false">53</number>').encode('utf-8'), i.toxml('utf-8', root_only=True))

    def testNilConstruction (self):
        i = number(_nil=True)
        self.assertEqual(six.u('<number xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>').encode('utf-8'), i.toxml('utf-8', root_only=True))
        self.assertRaises(pyxb.ContentInNilInstanceError, i._setValue, 25)

    def testReplacement (self):
        i = number(53, bounded=True)
        self.assertEqual(six.u('<number bounded="true">53</number>').encode('utf-8'), i.toxml('utf-8', root_only=True))
        self.assertEqual(53, i.value())
        i._setValue(27)
        self.assertEqual(six.u('<number bounded="true">27</number>').encode('utf-8'), i.toxml('utf-8', root_only=True))
        self.assertRaises(pyxb.SimpleTypeValueError, i._setValue, 'text')

if __name__ == '__main__':
    unittest.main()
