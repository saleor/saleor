# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.utils import six
import noi
import unittest
import pyxb
import io
import xml.dom.minidom

def first_element_child (n):
    for c in n.childNodes:
        if c.ELEMENT_NODE == c.nodeType:
            return c
    return None

class TestTrac0114 (unittest.TestCase):

    xmlData = open('namespace_other_issue.xml', 'rb').read()

    def validateDOM (self, instance):
        self.assertEqual
        print('a NS: %s / %s' % (a.namespaceURI, a.tagName))
        print('aext NS: %s / %s' % (aext.namespaceURI, aext.tagName))
        print('xyz NS: %s / %s' % (xyz.namespaceURI, xyz.tagName))

    def testMiniDOM (self):
        dom = xml.dom.minidom.parse(io.BytesIO(self.xmlData))
        a = dom.documentElement
        self.assertEqual(a.namespaceURI, noi.Namespace.uri())
        aext = first_element_child(a)
        self.assertEqual(aext.namespaceURI, noi.Namespace.uri())
        xyz = first_element_child(aext)
        self.assertEqual(xyz.namespaceURI, 'urn:schema:b')

    def testPyXB (self):
        instance = noi.CreateFromDocument(self.xmlData)
        dom = instance.toDOM()
        a = dom.documentElement
        self.assertEqual(a.namespaceURI, noi.Namespace.uri())
        aext = a.firstChild
        self.assertEqual(aext.namespaceURI, noi.Namespace.uri())
        xyz = aext.firstChild
        self.assertEqual(xyz.namespaceURI, 'urn:schema:b')
        xmlt = six.u('<ns1:a xmlns:ns1="urn:schema:a" xmlns:ns2="urn:schema:b" xmlns:ns3="urn:schema:c"><ns1:Extensions><ns2:xyz ns3:tag="value">abc</ns2:xyz></ns1:Extensions></ns1:a>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(a.toxml("utf-8"), xmld)

if __name__ == '__main__':
    unittest.main()
