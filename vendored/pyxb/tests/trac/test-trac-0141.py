# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
import pyxb.utils.utility
from pyxb.utils.utility import MakeIdentifier

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
   <xs:complexType name="simple_type">
      <xs:simpleContent>
         <xs:extension base="xs:string">
           <xs:attribute name="is_clean" type="xs:boolean"/>
         </xs:extension>
      </xs:simpleContent>
   </xs:complexType>
   <xs:element name="simple_element" type="simple_type"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
rv = compile(code, 'test', 'exec')
eval(rv)

import unittest
import re

_CamelCase_re = re.compile(r'_\w')

def MakeCamelCase (identifier):
    return _CamelCase_re.sub(lambda _m: _m.group(0)[1].upper(), six.text_type(identifier))

class TestTrac0141 (unittest.TestCase):
    def tearDown (cls):
        pyxb.utils.utility._SetXMLIdentifierToPython(None)

    def testDefaultMakeIdentifier (self):
        self.assertEqual(MakeIdentifier('is_string'), 'is_string')

    def testReplacedMakeIdentifier (self):
        pyxb.utils.utility._SetXMLIdentifierToPython(MakeCamelCase)
        self.assertEqual(MakeIdentifier('is_string'), 'isString')

    def testReplacedBuild (self):
        pyxb.utils.utility._SetXMLIdentifierToPython(MakeCamelCase)
        code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
        rv = compile(code, 'test', 'exec')
        xglobals = globals().copy()
        xlocals = locals().copy()
        self.assertFalse('simpleElement' in xlocals)
        eval(rv, xglobals, xlocals)
        self.assertTrue('simpleElement' in xlocals)
        instance = xlocals['simpleElement'](isClean=True)
        self.assertTrue(instance.isClean)

    def testNormalBuild (self):
        instance = simple_element(is_clean=True)
        self.assertTrue(instance.is_clean)

if __name__ == '__main__':
    unittest.main()
