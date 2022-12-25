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
  <xs:element name="structure">
    <xs:complexType><xs:anyAttribute processContents="lax"/></xs:complexType>
  </xs:element>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

AttributeNamespace = pyxb.namespace.NamespaceInstance('URN:attr:200908231005')

class TestTrac_200908231005 (unittest.TestCase):
    def testParsing (self):
        xmls = '<structure xmlns:attr="%s" attr:field="value"/>' % (AttributeNamespace.uri(),)
        instance = CreateFromDocument(xmls)
        wam = instance.wildcardAttributeMap()
        self.assertEqual(1, len(wam))
        self.assertEqual('value', wam.get(AttributeNamespace.createExpandedName('field')))


if __name__ == '__main__':
    unittest.main()
