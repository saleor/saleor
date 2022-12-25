__author__ = 'Harold Solbrig'

# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="http://foo.org/test" targetNamespace="http://foo.org/test" elementFormDefault="qualified">
    <xs:complexType name="Outer">
        <xs:complexContent>
            <xs:extension base="Inner">
                <xs:sequence>
                    <xs:element name="c" type="xs:string" minOccurs="0" maxOccurs="1"/>
                </xs:sequence>
            </xs:extension>
        </xs:complexContent>
    </xs:complexType>
    <xs:element name="Test" type="Outer"/>
    <xs:complexType name="Inner">
        <xs:sequence>
            <xs:element name="a" type="xs:string" minOccurs="0"/>
            <xs:element name="b" type="xs:string" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

#pyxb.GlobalValidationConfig._setContentInfluencesGeneration(pyxb.GlobalValidationConfig.NEVER)

class TestTrac0184(unittest.TestCase):
   def testNesting(self):
       xml = """<?xml version="1.0" encoding="UTF-8"?>
<Test xmlns="http://foo.org/test">
<a>A</a>
<b>B</b>
<c>C</c>
</Test>"""
       instance = CreateFromDocument(xml)
       dom = instance.toDOM()
       xmlt = six.u('<?xml version="1.0" encoding="utf-8"?><ns1:Test xmlns:ns1="http://foo.org/test"><ns1:a>A</ns1:a><ns1:b>B</ns1:b><ns1:c>C</ns1:c></ns1:Test>')
       xmld = xmlt.encode('utf-8')
       self.assertEqual(instance.toxml('utf-8'), xmld)

if __name__ == '__main__':
    unittest.main()
