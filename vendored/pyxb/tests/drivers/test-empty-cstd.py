# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-empty-cstd.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestEmptyCSTD (unittest.TestCase):
    def testPresent (self):
        xmls = '<time xmlns="urn:test">http://test/something</time>'
        instance = CreateFromDocument(xmls)
        self.assertEqual("http://test/something", instance.value())
    def testMissing (self):
        xmls = '<time xmlns="urn:test"></time>'
        instance = CreateFromDocument(xmls)
        self.assertEqual("", instance.value())
    def testWhitespace (self):
        xmls = '<time xmlns="urn:test">   </time>'
        instance = CreateFromDocument(xmls)
        self.assertEqual(six.u(''), instance.value())
    def testEmpty (self):
        xmls = '<time xmlns="urn:test"/>'
        instance = CreateFromDocument(xmls)
        self.assertEqual("", instance.value())

if __name__ == '__main__':
    unittest.main()
