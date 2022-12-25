# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
import pyxb.binding.facets

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
<xs:simpleType name="tUC">
  <xs:annotation><xs:documentation>Simple type to represent an ASCII upper-case letter</xs:documentation></xs:annotation>
  <xs:restriction base="xs:string">
    <xs:pattern value="[A-Z]"/>
  </xs:restriction>
</xs:simpleType>
<xs:element name="UC" type="tUC"/>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0190 (unittest.TestCase):
    def testBasic (self):
        i = UC('A')
        self.assertEqual(i, 'A')
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.SimpleFacetValueError, UC, 'a')
        else:
            with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
                i = UC('a')
            e = cm.exception
            self.assertEqual(e.type, tUC)
            self.assertEqual(e.value, 'a')
            self.assertTrue(isinstance(e.facet, pyxb.binding.facets.CF_pattern))
            self.assertEqual(e.details(), 'Type tUC pattern constraint violated by value a')

    def testUnicode (self):
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.SimpleFacetValueError, UC, six.unichr(0xf6))
        else:
            with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
                i = UC(six.unichr(0xf6))
            e = cm.exception
            self.assertEqual(e.type, tUC)
            self.assertEqual(e.value, six.unichr(0xf6))
            self.assertTrue(isinstance(e.facet, pyxb.binding.facets.CF_pattern))
            if six.PY2:
                self.assertRaises(UnicodeEncodeError, str, e.details())
            self.assertEqual(e.details(), six.u('Type tUC pattern constraint violated by value \xf6'))

if __name__ == '__main__':
    unittest.main()
