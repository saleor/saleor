# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
from pyxb.utils import six

import os.path
xsd=six.u('''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="anything" type="xs:anyType" nillable="true"/>
        <xs:element name="container">
                <xs:complexType>
                        <xs:sequence>
                                <xs:element ref="anything"/>
                        </xs:sequence>
                </xs:complexType>
        </xs:element>
</xs:schema>
''')

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

import pyxb.utils.domutils
import pyxb.namespace
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(pyxb.namespace.XMLSchema, 'xs')

class TestTrac_0094 (unittest.TestCase):
    body = 'something'
    xmlt = six.u('''<anything xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:string">%s</anything>''') % (body,)
    xmld = xmlt.encode('utf-8')

    def testFromXML (self):
        instance = CreateFromDocument(self.xmlt)
        self.assertTrue(isinstance(instance, xs.string))
        self.assertEqual(instance, self.body)
        self.assertEqual(instance._element(), anything)

    def testToXML (self):
        instance = xs.string(self.body, _element=anything)
        self.assertEqual(instance.toxml("utf-8", root_only=True), self.xmld)

    def testContainerCtor (self):
        i = xs.string(self.body, _element=anything)
        instance = container(anything=i)
        explicit_xml = instance.toxml("utf-8")
        instance = container(anything=xs.string(self.body))
        implicit_xml = instance.toxml("utf-8")
        self.assertEqual(explicit_xml, implicit_xml)

    def testContainerAssignment (self):
        i = xs.string(self.body, _element=anything)
        instance = container()
        instance.anything = i
        explicit_xml = instance.toxml("utf-8")
        instance.anything = xs.string(self.body)
        implicit_xml = instance.toxml("utf-8")
        self.assertEqual(explicit_xml, implicit_xml)
        instance.anything = xs.int(43)
        self.assertTrue(isinstance(instance.anything, xs.int))
        int_xml = instance.toxml("utf-8")
        instance.anything = self.body
        self.assertTrue(isinstance(instance.anything, xs.anyType))
        oc = instance.anything.orderedContent()
        self.assertEqual(1, len(oc))
        self.assertTrue(isinstance(oc[0], pyxb.binding.basis.NonElementContent))
        xmlt = six.u('<container><anything>something</anything></container>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(xmld, instance.toxml('utf-8', root_only=True))
        instance.anything = 43
        self.assertTrue(isinstance(instance.anything, xs.anyType))
        oc = instance.anything.orderedContent()
        self.assertEqual(1, len(oc))
        self.assertTrue(isinstance(oc[0], pyxb.binding.basis.NonElementContent))
        xmlt = six.u('<container><anything>43</anything></container>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(xmld, instance.toxml('utf-8', root_only=True))

if __name__ == '__main__':
    unittest.main()
