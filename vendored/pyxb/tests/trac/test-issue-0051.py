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
xsd='''
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="wbin">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="bin" type="xs:hexBinary"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
    <xs:element name="bin" type="xs:hexBinary"/>
    <xs:element name="u64" type="xs:base64Binary"/>
</xs:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue0051 (unittest.TestCase):
    def testWrapped (self):
        i = CreateFromDocument('<wbin><bin>aa</bin></wbin>')
        self.assertEqual(1, len(i.bin))
        i = CreateFromDocument('<wbin><bin> </bin></wbin>')
        self.assertEqual(0, len(i.bin))
        i = CreateFromDocument('<wbin><bin/></wbin>')
        self.assertEqual(0, len(i.bin))

    def testBare (self):
        i = CreateFromDocument('<bin>aa</bin>')
        self.assertEqual(1, len(i))
        i = CreateFromDocument('<bin> </bin>')
        self.assertEqual(0, len(i))
        i = CreateFromDocument('<bin/>')
        self.assertEqual(0, len(i))
        i = CreateFromDocument('<u64>Zg==</u64>')
        self.assertEqual(1, len(i))
        i = CreateFromDocument('<u64> </u64>')
        self.assertEqual(0, len(i))
        i = CreateFromDocument('<u64/>')
        self.assertEqual(0, len(i))

if __name__ == '__main__':
    unittest.main()
