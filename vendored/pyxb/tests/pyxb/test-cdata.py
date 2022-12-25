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
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="var" type="xs:string"/>
</xs:schema>'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestPyXBCDATA (unittest.TestCase):
    def testParse(self):
        instance = CreateFromDocument("<var>text</var>")
        self.assertEqual(instance, 'text')
        instance = CreateFromDocument("<var><![CDATA[text]]></var>")
        self.assertEqual(instance, 'text')
        instance = CreateFromDocument("<var>&gt; text &lt;</var>")
        self.assertEqual(instance, '> text <')
        instance = CreateFromDocument("<var><![CDATA[> text <]]></var>")
        self.assertEqual(instance, '> text <')

    def testGenerate(self):
        instance = var('text')
        self.assertEqual(instance, 'text')
        instance = var('>text<')
        self.assertEqual(instance, '>text<')
        xmlt = six.u('<var>&gt;text&lt;</var>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)

if __name__ == '__main__':
    unittest.main()
