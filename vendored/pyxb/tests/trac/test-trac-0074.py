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
import xml.dom.minidom
import io

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:trac-0074">
<xs:element name="top" type="xs:string"/>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0074 (unittest.TestCase):
    def test (self):
        t0p = Namespace.createExpandedName('t0p')
        xmlt = six.u('<ns:t0p xmlns:ns="urn:trac-0074">content</ns:t0p>')
        dom = xml.dom.minidom.parseString(xmlt)
        try:
            dom_instance = CreateFromDOM(dom.documentElement)
            self.fail('DOM creation succeeded')
        except pyxb.UnrecognizedDOMRootNodeError as e:
            self.assertEqual(dom.documentElement, e.node)
            self.assertEqual(t0p, e.node_name)

        saxdom = pyxb.utils.saxdom.parseString(xmlt)
        try:
            saxdom_instance = CreateFromDOM(saxdom)
            self.fail('SAXDOM creation succeeded')
        except pyxb.UnrecognizedDOMRootNodeError as e:
            self.assertEqual(saxdom.documentElement, e.node)
            self.assertEqual(t0p, e.node_name)

        saxer = pyxb.binding.saxer.make_parser()
        handler = saxer.getContentHandler()
        saxer.parse(io.StringIO(xmlt))
        try:
            sax_instance = handler.rootObject()
            self.fail('SAXER creation succeeded')
        except pyxb.UnrecognizedDOMRootNodeError as e:
            self.assertEqual(t0p, e.node_name)

if __name__ == '__main__':
    unittest.main()
