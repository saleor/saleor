# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.xmlschema.structures
import pyxb.utils.domutils

from pyxb.exceptions_ import *

import unittest

def CreateDocumentationNode (content):
    xmls = '<xs:annotation xmlns:xs="%s"><xs:documentation>%s</xs:documentation></xs:annotation>' % (pyxb.namespace.XMLSchema.uri(), content)
    dom = pyxb.utils.domutils.StringToDOM(xmls)
    node = dom.documentElement
    nsc = pyxb.namespace.NamespaceContext.GetNodeContext(node)
    if nsc.targetNamespace() is None:
        nsc.finalizeTargetNamespace()
    return pyxb.xmlschema.structures.Annotation.CreateFromDOM(node)


class TestTrac_0045 (unittest.TestCase):
    def testSimple (self):
        self.assertEqual('hi there!', CreateDocumentationNode("hi there!").asDocString())
        self.assertEqual(' "hi there!" ', CreateDocumentationNode('"hi there!"').asDocString())
        self.assertEqual("''' docstring! '''", CreateDocumentationNode('""" docstring! """').asDocString())
        self.assertEqual("inner ''' docstring!", CreateDocumentationNode('inner """ docstring!').asDocString())

if __name__ == '__main__':
    unittest.main()
