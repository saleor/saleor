# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-include-dau.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
#open('code.py', 'w').write(code)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIncludeDD (unittest.TestCase):
    def setUp (self):
        self.__basis_log = logging.getLogger('pyxb.binding.basis')
        self.__basis_loglevel = self.__basis_log.level

    def tearDown (self):
        self.__basis_log.level = self.__basis_loglevel

    def testDefault (self):
        xmls = '<entry xmlns="%s"><from>one</from><to>single</to></entry>' % (Namespace.uri(),)
        # Default namespace applies to from which should be in no namespace
        # Hide the warning from pyxb.binding.basis.complexTypeDefinition.append
        # that it couldn't convert the DOM node to a binding.
        self.__basis_log.setLevel(logging.ERROR)
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDocument, xmls.encode('utf-8'))

    def testExplicit (self):
        xmls = '<ns:entry xmlns:ns="%s"><from>one</from><ns:to>single</ns:to></ns:entry>' % (Namespace.uri(),)
        instance = CreateFromDocument(xmls.encode('utf-8'))
        self.assertEqual(english.one, instance.from_)

if __name__ == '__main__':
    unittest.main()
