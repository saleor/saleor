# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-include-aaq.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
#open('code.py', 'w').write(code)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIncludeDD (unittest.TestCase):
    def testDefault (self):
        xmls = '<entry><from>one</from><to>single</to></entry>'
        instance = CreateFromDocument(xmls)
        self.assertEqual(english.one, instance.from_)

if __name__ == '__main__':
    unittest.main()
