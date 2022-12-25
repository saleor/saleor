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
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/absentns.xsd'))

xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="URN:trac0046" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="URN:trac0046">
  <xs:include schemaLocation="%s"/>
  <xs:element name="anotherGlobalComplex" type="tns:structure"/>
</xs:schema>''' % (schema_path,)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
rv = compile(code, 'test', 'exec')
eval(rv)

import unittest

class TestTrac_0046 (unittest.TestCase):
    def testParsing (self):
        g1 = globalComplex('simple')
        g2 = anotherGlobalComplex('simple2', g1)
        self.assertEqual(g2.globalSimple, 'simple2')
        self.assertEqual(g2.innerComplex.globalSimple, 'simple')

if __name__ == '__main__':
    unittest.main()
