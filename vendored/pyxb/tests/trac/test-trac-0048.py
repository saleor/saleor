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
<xs:element name="nilURI" nillable="true" type="xs:anyURI"/>
<xs:complexType name="uriAttr">
  <xs:simpleContent>
    <xs:extension base="xs:anyURI">
      <xs:attribute name="reason" type="xs:string"/>
    </xs:extension>
  </xs:simpleContent>
</xs:complexType>
<xs:element name="nilURIAttr" nillable="true" type="uriAttr"/>
<xs:element name="uriAttr" type="uriAttr"/>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0048 (unittest.TestCase):
    def testSimple (self):
        self.assertEqual('foo', nilURI('foo'))
        x = nilURI(_nil=True)
        self.assertTrue(x._isNil())

    def testComplex (self):
        x = nilURIAttr('foo', reason="bogus")
        self.assertEqual('foo', x.value())
        x = nilURIAttr(_nil=True, reason="bogus")
        #self.assertTrue(x._isNil())

if __name__ == '__main__':
    unittest.main()
