# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
import pyxb.binding.saxer
import io

from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/substgroup.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestSubstGroup (unittest.TestCase):
    def testISO8601 (self):
        xmlt = six.u('<when><ISO8601>2009-06-15T17:50:00Z</ISO8601></when>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = CreateFromDOM(dom.documentElement)
        self.assertEqual(instance.sgTime._element(), ISO8601)
        self.assertEqual(instance.toDOM().documentElement.toxml("utf-8"), xmld)

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        saxer.parse(io.StringIO(xmlt))
        instance = handler.rootObject()
        self.assertEqual(instance.sgTime._element(), ISO8601)
        self.assertEqual(instance.toDOM().documentElement.toxml("utf-8"), xmld)

    def testPairTime (self):
        xmlt = six.u('<when><pairTime><seconds>34.0</seconds><fractionalSeconds>0.21</fractionalSeconds></pairTime></when>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = CreateFromDOM(dom.documentElement)
        self.assertEqual(instance.sgTime._element(), pairTime)
        self.assertEqual(instance.sgTime.seconds, 34)
        self.assertEqual(instance.toDOM().documentElement.toxml("utf-8"), xmld)

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        saxer.parse(io.StringIO(xmlt))
        instance = handler.rootObject()
        self.assertEqual(instance.sgTime._element(), pairTime)
        self.assertEqual(instance.sgTime.seconds, 34)
        self.assertEqual(instance.toDOM().documentElement.toxml("utf-8"), xmld)


    def testSGTime (self):
        xmlt = six.u('<when><sgTime>2009-06-15T17:50:00Z</sgTime></when>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(pyxb.AbstractElementError, CreateFromDOM, dom.documentElement)

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        self.assertRaises(pyxb.AbstractElementError, saxer.parse, io.StringIO(xmlt))

        xmlt = six.u('<sgTime>2009-06-15T17:50:00Z</sgTime>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(pyxb.AbstractElementError, CreateFromDOM, dom.documentElement)
        self.assertRaises(pyxb.AbstractElementError, saxer.parse, io.StringIO(xmlt))

        xmlt = six.u('<ISO8601>2009-06-15T17:50:00Z</ISO8601>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = CreateFromDOM(dom.documentElement)
        self.assertEqual(instance._element(), ISO8601)
        saxer.parse(io.StringIO(xmlt))
        instance = handler.rootObject()
        self.assertEqual(instance._element(), ISO8601)

    def testGenAbstract (self):
        xmlt = six.u('<when><pairTime><seconds>34.0</seconds><fractionalSeconds>0.21</fractionalSeconds></pairTime></when>')
        xmld = xmlt.encode('utf-8')
        instance = when(pairTime(34.0, 0.21))
        self.assertEqual(instance.sgTime._element(), pairTime)
        self.assertEqual(instance.sgTime.seconds, 34)
        self.assertEqual(instance.toDOM().documentElement.toxml("utf-8"), xmld)
        # Loss of element association kills DOM generation
        instance.sgTime._setElement(None)
        self.assertRaises(pyxb.AbstractElementError, instance.toDOM)
        self.assertRaises(pyxb.AbstractElementError, sgTime)

if __name__ == '__main__':
    unittest.main()
