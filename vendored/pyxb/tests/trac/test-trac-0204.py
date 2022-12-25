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
    <xs:complexType name="YesNoChoice">
        <xs:annotation>
            <xs:documentation>Yes No Choice</xs:documentation>
        </xs:annotation>
        <xs:choice>
            <xs:element name="Yes" type="xs:boolean" fixed="true"/>
            <xs:element name="No" type="xs:boolean" fixed="true"/>
        </xs:choice>
    </xs:complexType>
  <xs:element name="yesNoChoice" type="YesNoChoice"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest
import sys

class TestTrac0204 (unittest.TestCase):
    if sys.version_info[:2] < (2, 7):
        def assertIsNone (self, v):
            self.assertEqual(None, v)
        def assertIsNotNone (self, v):
            self.assertNotEqual(None, v)

    def testCtor (self):
        instance = yesNoChoice()
        self.assertIsNone(instance.Yes)
        self.assertIsNone(instance.No)
        instance = yesNoChoice(Yes=True)
        self.assertIsNotNone(instance.Yes)
        self.assertIsNone(instance.No)
        instance = yesNoChoice(Yes=True, No=True)
        self.assertRaises(pyxb.UnprocessedElementContentError, instance.validateBinding)

if __name__ == '__main__':
    unittest.main()
