# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-wildcard.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest


def nc_not (ns_or_absent):
    return ( pyxb.xmlschema.structures.Wildcard.NC_not, ns_or_absent )

class TestIntensionalSet (unittest.TestCase):

    def testTest (self):
        ns = 'URN:namespace'
        not_nc = nc_not(ns)
        self.assertTrue(isinstance(not_nc, tuple))
        self.assertEqual(2, len(not_nc))
        self.assertEqual(pyxb.xmlschema.structures.Wildcard.NC_not, not_nc[0])
        self.assertEqual(ns, not_nc[1])

    def testUnion_1 (self):
        UNION = pyxb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, UNION([ nc_any, nc_any ]))
        self.assertEqual(nc_not(ns1), UNION([ nc_not(ns1), nc_not(ns1) ]))
        self.assertEqual(set([ns1]), UNION([ set([ns1]), set([ns1]) ]))

    def testUnion_2 (self):
        UNION = pyxb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, UNION([ nc_any, set([ns1]) ]))
        self.assertEqual(nc_any, UNION([ nc_any, nc_not(ns1) ]))
        self.assertEqual(nc_any, UNION([ nc_any, nc_not(None) ]))

    def testUnion_3 (self):
        UNION = pyxb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(set([ns1, ns2]), UNION([set([ns1]), set([ns2])]))
        self.assertEqual(set([None, ns1]), UNION([set([None]), set([ns1])]))
        self.assertEqual(set([None]), UNION([set([None]), set([None])]))

    def testUnion_4 (self):
        UNION = pyxb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_not(None), UNION([nc_not(ns1), nc_not(ns2)]))
        self.assertEqual(nc_not(None), UNION([nc_not(ns1), nc_not(None)]))

    def testUnion_5 (self):
        UNION = pyxb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, UNION([nc_not(ns1), set([ns1, None])])) # 5.1
        self.assertEqual(nc_not(None), UNION([nc_not(ns1), set([ns1, ns2])])) # 5.2
        self.assertRaises(SchemaValidationError, UNION, [nc_not(ns1), set([None, ns2])]) # 5.3
        self.assertEqual(nc_not(ns1), UNION([nc_not(ns1), set([ns2])])) # 5.4

    def testUnion_6 (self):
        UNION = pyxb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, UNION([nc_not(None), set([ns1, ns2, None])])) # 6.1
        self.assertEqual(nc_not(None), UNION([nc_not(None), set([ns1, ns2])])) # 6.2

    def testIntersection_1 (self):
        ISECT = pyxb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, ISECT([ nc_any, nc_any ]))
        self.assertEqual(nc_not(ns1), ISECT([ nc_not(ns1), nc_not(ns1) ]))
        self.assertEqual(set([ns1]), ISECT([ set([ns1]), set([ns1]) ]))

    def testIntersection_2 (self):
        ISECT = pyxb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(set([ns1]), ISECT([ nc_any, set([ns1]) ]))
        self.assertEqual(nc_not(ns1), ISECT([ nc_any, nc_not(ns1) ]))
        self.assertEqual(nc_not(None), ISECT([ nc_any, nc_not(None) ]))

    def testIntersection_3 (self):
        ISECT = pyxb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(set([ns2]), ISECT([nc_not(ns1), set([ns1, ns2, None])]))
        self.assertEqual(set([ns2]), ISECT([nc_not(ns1), set([ns1, ns2])]))
        self.assertEqual(set([ns2]), ISECT([nc_not(ns1), set([ns2])]))

    def testIntersection_4 (self):
        ISECT = pyxb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(set([ns2]), ISECT([set([ns1, ns2]), set([ns2, None])]))
        self.assertEqual(set([ns2, None]), ISECT([set([None, ns1, ns2]), set([ns2, None])]))
        self.assertEqual(set([]), ISECT([set([ns1]), set([ns2, None])]))
        self.assertEqual(set([]), ISECT([set([ns1]), set([ns2, ns1]), set([ns2, None])]))
        self.assertEqual(set([ns1]), ISECT([set([ns1, None]), set([None, ns2, ns1]), set([ns1, ns2])]))

    def testIntersection_5 (self):
        ISECT = pyxb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertRaises(SchemaValidationError, ISECT, [nc_not(ns1), nc_not(ns2)])

    def testIntersection_6 (self):
        ISECT = pyxb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pyxb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_not(ns1), ISECT([nc_not(ns1), nc_not(None)]))

class TestWildcard (unittest.TestCase):
    def setUp (self):
        # Hide the warning about failure to convert DOM node {}third
        # to a binding
        self.__basis_log = logging.getLogger('pyxb.binding.basis')
        self.__basis_loglevel = self.__basis_log.level
        self.__basis_log.setLevel(logging.ERROR)

    def tearDown (self):
        pyxb.RequireValidWhenParsing(True)
        self.__basis_log.level = self.__basis_loglevel

    def testElement (self):
        # NB: Test on CTD, not element
        self.assertTrue(wrapper_._HasWildcardElement)
        xmls = '<wrapper><first/><second/><third/></wrapper>'
        doc = pyxb.utils.domutils.StringToDOM(xmls)
        instance = wrapper.createFromDOM(doc.documentElement)
        self.assertTrue(isinstance(instance.wildcardElements(), list))
        self.assertEqual(1, len(instance.wildcardElements()))
        # Alternative parser path
        instance = CreateFromDocument(xmls)
        self.assertTrue(isinstance(instance.wildcardElements(), list))
        self.assertEqual(1, len(instance.wildcardElements()))

    def _validateWildcardWrappingRecognized (self, instance):
        self.assertTrue(isinstance(instance.wildcardElements(), list))
        self.assertEqual(1, len(instance.wildcardElements()))
        dom = instance.wildcardElements()[0]
        self.assertTrue(isinstance(dom, Node))
        self.assertEqual(Node.ELEMENT_NODE, dom.nodeType)
        self.assertEqual('third', dom.nodeName)
        self.assertEqual(1, len(dom.childNodes))
        cdom = dom.firstChild
        self.assertTrue(isinstance(cdom, Node))
        self.assertEqual(Node.ELEMENT_NODE, cdom.nodeType)
        self.assertEqual('selt', cdom.nodeName)
        ccdom = cdom.firstChild
        self.assertTrue(isinstance(ccdom, Node))
        self.assertEqual(Node.TEXT_NODE, ccdom.nodeType)
        self.assertEqual('text', ccdom.data)

    def testWildcardWrappingRecognized (self):
        # NB: Test on CTD, not element
        self.assertTrue(wrapper_._HasWildcardElement)
        xmls = '<wrapper><first/><second/><third><selt>text</selt></third></wrapper>'
        doc = pyxb.utils.domutils.StringToDOM(xmls)
        instance = wrapper.createFromDOM(doc.documentElement)
        self._validateWildcardWrappingRecognized(instance)
        # Alternative parser path
        instance = CreateFromDocument(xmls)
        self._validateWildcardWrappingRecognized(instance)

    def testMultiElement (self):
        tested_overmax = False
        for rep in range(0, 6):
            xmls = '<wrapper><first/><second/>%s</wrapper>' % (''.join(rep * ['<third/>']),)
            doc = pyxb.utils.domutils.StringToDOM(xmls)
            if 3 >= rep:
                instance = wrapper.createFromDOM(doc.documentElement)
                self.assertTrue(isinstance(instance.wildcardElements(), list))
                self.assertEqual(rep, len(instance.wildcardElements()))
                for i in range(0, rep):
                    self.assertEqual('third', instance.wildcardElements()[i].nodeName)
            else:
                tested_overmax = True
                self.assertRaises(UnrecognizedContentError, wrapper.createFromDOM, doc.documentElement)
        self.assertTrue(tested_overmax)

    def testAttribute (self):
        # NB: Test on CTD, not element
        self.assertTrue(isinstance(wrapper_._AttributeWildcard, pyxb.binding.content.Wildcard))
        xmls = '<wrapper myattr="true" auxattr="somevalue"/>'
        doc = pyxb.utils.domutils.StringToDOM(xmls)
        instance = wrapper.createFromDOM(doc.documentElement)
        self.assertTrue(isinstance(instance.wildcardAttributeMap(), dict))
        self.assertEqual(1, len(instance.wildcardAttributeMap()))
        self.assertEqual('somevalue', instance.wildcardAttributeMap()['auxattr'])

if __name__ == '__main__':
    unittest.main()
