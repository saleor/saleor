# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

# Derived from test-trac-0182 which uses wildcards
import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element type="xs:int" name="eOne"/>
  <xs:element type="xs:int" name="eTwo"/>
  <xs:complexType name="tElt">
    <xs:sequence>
      <xs:element ref="eOne" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="elt" type="tElt"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0189 (unittest.TestCase):
    def tearDown (self):
        pyxb.RequireValidWhenGenerating(True)
        pyxb.RequireValidWhenParsing(True)

    def testGenerate (self):
        ia = eOne(1)
        ib = eTwo(2)
        content = [ ia, ib ]
        i = elt(ia)
        self.assertRaises(UnrecognizedContentError, elt, ia, ib)

    def testParse (self):
        xmls = '<elt><eOne>1</eOne></elt>'
        i = CreateFromDocument(xmls)
        self.assertEqual(i.eOne, 1)
        xmls = '<elt><eOne>1</eOne><eTwo>2</eTwo></elt>'
        self.assertRaises(UnrecognizedContentError, CreateFromDocument, xmls)
        pyxb.RequireValidWhenParsing(False)
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.StructuralBadDocumentError, CreateFromDocument, xmls)
        else:
            with self.assertRaises(pyxb.StructuralBadDocumentError) as cm:
                i = CreateFromDocument(xmls)
            e = cm.exception

    def testAppend (self):
        i = elt(1)
        self.assertEqual(i.eOne, 1)
        ed = i._ElementMap.get('eOne')
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.NonPluralAppendError, ed.append, i, 2)
        else:
            with self.assertRaises(pyxb.NonPluralAppendError) as cm:
                ed.append(i, 2)
            e = cm.exception
            self.assertEqual(e.instance, i)
            self.assertEqual(e.element_declaration, ed)
            self.assertEqual(e.value, 2)
            self.assertEqual(e.details(), 'Instance of tElt cannot append to element eOne')

if __name__ == '__main__':
    unittest.main()
