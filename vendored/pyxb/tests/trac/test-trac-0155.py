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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns="http://schema.omg.org/spec/CTS2/1.0/Core"
           targetNamespace="http://schema.omg.org/spec/CTS2/1.0/Core"
           elementFormDefault="qualified">
    <xs:complexType mixed="true" name="tsAnyType">
        <xs:sequence>
            <xs:any maxOccurs="unbounded" minOccurs="0" namespace="##any" processContents="lax"/>
        </xs:sequence>
    </xs:complexType>

    <xs:element name="OpaqueData">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="v" type="tsAnyType" minOccurs="1"/>
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
# Note: Without this, there's an exception thrown below because the
# binding for the namespace isn't available; PyXB falls back to a raw
# DOM model there.  With this, though, you run afoul of trac/153 which
# may not be fixed in the PyXB 1.1.x series.
#import pyxb.bundles.common.xhtml1

class TestTrac0155 (unittest.TestCase):
    testxml = """<?xml version="1.0" encoding="UTF-8"?>
<OpaqueData xmlns="http://schema.omg.org/spec/CTS2/1.0/Core"
    xmlns:core="http://schema.omg.org/spec/CTS2/1.0/Core"
    xmlns:html="http://www.w3.org/1999/xhtml"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <core:v xmlns="http://www.w3.org/1999/xhtml"><ul><li>entry1</li><li>entry2</li></ul></core:v>
</OpaqueData> """

    def setUp (self):
        pyxb.utils.domutils.BindingDOMSupport.SetDefaultNamespace(Namespace.uri())

    def tearDown (self):
        pyxb.utils.domutils.BindingDOMSupport.SetDefaultNamespace(None)

    Expectedd = """<?xml version="1.0" encoding="utf-8"?><OpaqueData xmlns="http://schema.omg.org/spec/CTS2/1.0/Core" xmlns:ns1="http://www.w3.org/1999/xhtml"><v><ns1:ul><ns1:li>entry1</ns1:li><ns1:li>entry2</ns1:li></ns1:ul></v></OpaqueData>""".encode('utf-8')

    def test (self):
        txml = CreateFromDocument(self.testxml)
        #dom = txml.toDOM()
        #print dom.toprettyxml()
        #print txml.toxml()
        #print self.Expected
        self.assertEqual(txml.toxml('utf-8'), self.Expectedd)


if __name__ == '__main__':
    unittest.main()
