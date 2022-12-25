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
xsd='''
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:complexType name="empty"/>
    <xs:element name="elt" type="empty"/>
</xs:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue0031 (unittest.TestCase):
    def testAttribute (self):
        with self.assertRaises(pyxb.UnrecognizedAttributeError) as cm:
            CreateFromDocument('<elt atr="foo"/>')
        self.assertEqual(str(cm.exception), 'Attempt to reference unrecognized attribute atr in type {}'.format(empty))

if __name__ == '__main__':
    unittest.main()
