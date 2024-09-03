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
<xs:element name="testElt">
  <xs:complexType>
  <xs:sequence>
    <xs:element name="content" type="xs:string"/>
  </xs:sequence>
  </xs:complexType>
</xs:element>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0051 (unittest.TestCase):
    def __setContent (self, e, v):
        e.content = v

    def __setToXML (self, e, v):
        e.toxml = v

    def testElement (self):
        e = testElt('hello')
        self.assertEqual('hello', e.content_)
        e.content_ = 'goodbye'
        self.assertEqual('goodbye', e.content_)
        if pyxb._CorruptionDetectionEnabled:
            self.assertRaises(pyxb.BindingError, self.__setContent, e, 'invalid')
            self.assertRaises(pyxb.BindingError, self.__setToXML, e, 32)

if __name__ == '__main__':
    unittest.main()
