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
<schema
    xmlns="http://www.w3.org/2001/XMLSchema"
    targetNamespace="urn:issue0032"
    xmlns:tns="urn:issue0032"
    elementFormDefault="qualified">

    <element name="customer">
        <complexType>
            <sequence>
                <element name="address" type="tns:address"/>
            </sequence>
        </complexType>
    </element>

    <complexType name="address">
        <sequence>
            <element name="street" type="string"/>
        </sequence>
    </complexType>

    <complexType name="canadianAddress">
        <complexContent>
            <extension base="tns:address">
                <sequence>
                    <element name="postalCode" type="string"/>
                </sequence>
            </extension>
        </complexContent>
    </complexType>

</schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue0032 (unittest.TestCase):
    xmlt = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<customer xmlns="urn:issue0032">
    <address xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="canadianAddress">
        <street>1 A Street</street>
        <postalCode>Ontario</postalCode>
    </address>
</customer>'''

    def testRoundTrip (self):
        i = CreateFromDocument(self.xmlt)
        self.assertTrue(isinstance(i.address, canadianAddress))
        xmlt = i.toxml('utf-8')
        i2 = CreateFromDocument(xmlt)
        self.assertTrue(isinstance(i2.address, canadianAddress))

if __name__ == '__main__':
    unittest.main()
