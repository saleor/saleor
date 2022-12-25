# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" targetNamespace="URN:test-trac-0047" xmlns:gml="URN:test-trac-0047">
        <simpleType name="NilReasonEnumeration">
                <union>
                        <simpleType>
                                <restriction base="string">
                                        <enumeration value="inapplicable"/>
                                        <enumeration value="missing"/>
                                        <enumeration value="template"/>
                                        <enumeration value="unknown"/>
                                        <enumeration value="withheld"/>
                                </restriction>
                        </simpleType>
                        <simpleType>
                                <restriction base="string">
                                        <pattern value="other:\w{2,}"/>
                                </restriction>
                        </simpleType>
                </union>
        </simpleType>
        <simpleType name="SignType">
                <annotation>
                        <documentation>gml:SignType is a convenience type with values "+" (plus) and "-" (minus).</documentation>
                </annotation>
                <restriction base="string">
                        <enumeration value="-"/>
                        <enumeration value="+"/>
                </restriction>
        </simpleType>
        <simpleType name="booleanOrNilReason">
                <annotation>
                        <documentation>Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value.</documentation>
                </annotation>
                <union memberTypes="gml:NilReasonEnumeration boolean anyURI"/>
        </simpleType>
        <simpleType name="doubleOrNilReason">
                <annotation>
                        <documentation>Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value.</documentation>
                </annotation>
                <union memberTypes="gml:NilReasonEnumeration double anyURI"/>
        </simpleType>
        <simpleType name="integerOrNilReason">
                <annotation>
                        <documentation>Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value.</documentation>
                </annotation>
                <union memberTypes="gml:NilReasonEnumeration integer anyURI"/>
        </simpleType>
  <element name="dblNil" type="gml:doubleOrNilReason"/>
</schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0047 (unittest.TestCase):
    def testEnum (self):
        self.assertEqual('missing', NilReasonEnumeration.Factory('missing'))
        self.assertRaises(pyxb.SimpleTypeValueError, NilReasonEnumeration.Factory, 'notValid')
        self.assertEqual('other:myReason', NilReasonEnumeration.Factory('other:myReason'))

    def testDblNil (self):
        v = dblNil(2.45)
        self.assertTrue(isinstance(v, float))
        v = dblNil('2.534')
        self.assertTrue(isinstance(v, float))
        v = dblNil('withheld')
        self.assertTrue(isinstance(v, NilReasonEnumeration._MemberTypes[0]))
        v = dblNil('other:myReason')
        self.assertTrue(isinstance(v, NilReasonEnumeration._MemberTypes[1]))
        v = dblNil('somethingElse')
        self.assertTrue(isinstance(v, xs.anyURI))

if __name__ == '__main__':
    unittest.main()
