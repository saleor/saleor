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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="outer">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="inner" type="xs:string"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0163 (unittest.TestCase):

    def testGood (self):
        instance = CreateFromDocument('<outer><inner>one</inner></outer>')
        self.assertEqual(instance.inner, 'one')

    def testBad (self):
        ran_test = True
        try:
            instance = CreateFromDocument('<outer><inner>one</inner><inner>extra</inner></outer>')
            ran_test = False
        except Exception as e:
            self.assertTrue(isinstance(e, pyxb.UnrecognizedContentError))
            self.assertTrue(isinstance(e.value, outer.typeDefinition()._UseForTag('inner').elementBinding().typeDefinition()))
            self.assertEqual(e.value, 'extra')
        self.assertTrue(ran_test)

if __name__ == '__main__':
    unittest.main()
