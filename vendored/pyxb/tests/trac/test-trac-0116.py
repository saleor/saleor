# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="utf-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<xsd:element name="root" type="xsd:string"/>
</xsd:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('binding0116.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

import unittest

class TestTrac0116 (unittest.TestCase):
    xmls = '''<?xml version="1.0" encoding="utf-8"?><root foo='boo'/>'''

    def testBasic (self):
        self.assertRaises(pyxb.AttributeOnSimpleTypeError, CreateFromDocument, self.xmls)

if __name__ == '__main__':
    unittest.main()
