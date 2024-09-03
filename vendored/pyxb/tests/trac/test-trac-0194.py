# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
import gc

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:complexType name="color"/>
    <xs:complexType name="ecolor">
        <xs:complexContent>
            <xs:extension base="color">
               <xs:sequence>
                  <xs:element name="color" type="xs:string"/>
               </xs:sequence>
            </xs:extension>
        </xs:complexContent>
    </xs:complexType>
    <xs:complexType name="acolor">
        <xs:complexContent>
            <xs:extension base="color">
               <xs:attribute name="color" type="xs:string"/>
            </xs:extension>
        </xs:complexContent>
    </xs:complexType>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0194 (unittest.TestCase):
    def testAll (self):
        pass

if __name__ == '__main__':
    unittest.main()
