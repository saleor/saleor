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
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/particle.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

from pyxb.utils import domutils
def ToDOM (instance, tag=None):
    return instance.toDOM().documentElement

class TestParticle (unittest.TestCase):
    def test_bad_creation (self):
        xmlt = six.u('<h01 xmlns="URN:test"/>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        # Creating with wrong element
        self.assertRaises(pyxb.StructuralBadDocumentError, h01b.createFromDOM, dom.documentElement)

    def test_h01_empty (self):
        xmlt = six.u('<ns1:h01 xmlns:ns1="URN:test"/>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = h01.createFromDOM(dom.documentElement)
        self.assertTrue(instance.elt is None)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def test_h01_elt (self):
        xmlt = six.u('<ns1:h01 xmlns:ns1="URN:test"><elt/></ns1:h01>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = h01.createFromDOM(dom.documentElement)
        self.assertTrue(instance.elt is not None)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def test_h01_elt2 (self):
        xmlt = six.u('<h01 xmlns="URN:test"><elt/><elt/></h01>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, h01.createFromDOM, dom.documentElement)

    def test_h01b_empty (self):
        xmlt = six.u('<ns1:h01b xmlns:ns1="URN:test"/>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = h01b.createFromDOM(dom.documentElement)
        self.assertTrue(instance.elt is None)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def test_h01b_elt (self):
        xmlt = six.u('<ns1:h01b xmlns:ns1="URN:test"><elt/></ns1:h01b>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = h01b.createFromDOM(dom.documentElement)
        self.assertTrue(instance.elt is not None)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def test_h01b_elt2 (self):
        xmlt = six.u('<ns1:h01b xmlns:ns1="URN:test"><elt/><elt/></ns1:h01b>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, h01b.createFromDOM, dom.documentElement)

    def test_h11_empty (self):
        xmlt = six.u('<ns1:h11 xmlns:ns1="URN:test"/>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(IncompleteElementContentError, h11.createFromDOM, dom.documentElement)

    def test_h11_elt (self):
        xmlt = six.u('<ns1:h11 xmlns:ns1="URN:test"><elt/></ns1:h11>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = h11.createFromDOM(dom.documentElement)
        self.assertTrue(instance.elt is not None)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def test_h24 (self):
        xmlt = six.u('<h24 xmlns="URN:test"></h24>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(IncompleteElementContentError, h24.createFromDOM, dom.documentElement)

        for num_elt in range(0, 5):
            xmlt = six.u('<ns1:h24 xmlns:ns1="URN:test">%s</ns1:h24>') % (''.join(num_elt * ['<elt/>']),)
            dom = pyxb.utils.domutils.StringToDOM(xmlt)
            if 2 > num_elt:
                self.assertRaises(IncompleteElementContentError, h24.createFromDOM, dom.documentElement)
            elif 4 >= num_elt:
                instance = h24.createFromDOM(dom.documentElement)
                xmld = xmlt.encode('utf-8')
                self.assertEqual(num_elt, len(instance.elt))
                self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)
            else:
                self.assertRaises(UnrecognizedContentError, h24.createFromDOM, dom.documentElement)

    def test_h24b (self):
        xmlt = six.u('<ns1:h24b xmlns:ns1="URN:test"></ns1:h24b>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(IncompleteElementContentError, h24b.createFromDOM, dom.documentElement)

        for num_elt in range(0, 5):
            xmlt = six.u('<ns1:h24b xmlns:ns1="URN:test">%s</ns1:h24b>') % (''.join(num_elt * ['<elt/>']),)
            dom = pyxb.utils.domutils.StringToDOM(xmlt)
            if 2 > num_elt:
                self.assertRaises(IncompleteElementContentError, h24b.createFromDOM, dom.documentElement)
            elif 4 >= num_elt:
                xmld = xmlt.encode('utf-8')
                instance = h24b.createFromDOM(dom.documentElement)
                self.assertEqual(num_elt, len(instance.elt))
                self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)
            else:
                self.assertRaises(UnrecognizedContentError, h24b.createFromDOM, dom.documentElement)

if __name__ == '__main__':
    unittest.main()
