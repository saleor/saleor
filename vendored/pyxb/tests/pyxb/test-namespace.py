# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb
from pyxb.namespace import ExpandedName
import xml.dom
from pyxb.namespace import XMLSchema as xsd
xsd.validateComponentModel()
import pyxb.binding.datatypes as xsd_module

class TestExpandedName (unittest.TestCase):
    def testEquivalence (self):
        an1 = ExpandedName(None, 'string')
        en1 = ExpandedName(xsd, 'string')
        en2 = ExpandedName(xsd, 'string')
        en3 = ExpandedName(xsd, 'notString')
        self.assertEqual(en1, en2)
        self.assertEqual(en1, ( en1.namespace(), en1.localName() ))
        self.assertTrue(en1 == en2)
        self.assertFalse(en1 == en3)
        self.assertTrue(en1 != en3)
        self.assertTrue(an1 == an1.localName())
        self.assertFalse(an1 == en3.localName())
        self.assertTrue(an1 != en3.localName())
        self.assertFalse(an1 != an1.localName())

    def testRichComparisons (self):
        s1 = 'alpha'
        s2 = 'beta'
        an1 = ExpandedName(None, s1)
        en1 = ExpandedName(xsd, s1)
        an2 = ExpandedName(None, s2)
        en2 = ExpandedName(xsd, s2)
        # an1 ? an2
        self.assertFalse(an1 == an2)
        self.assertTrue(an1 != an2)
        self.assertTrue(an1 <= an2)
        self.assertTrue(an1 < an2)
        self.assertFalse(an1 >= an2)
        self.assertFalse(an1 > an2)
        # an1 ? en1
        self.assertFalse(an1 == en1)
        self.assertTrue(an1 != en1)
        self.assertTrue(an1 <= en1)
        self.assertTrue(an1 < en1)
        self.assertFalse(an1 >= en1)
        self.assertFalse(an1 > en1)
        # s1 ? an1
        self.assertTrue(s1 == an1)
        self.assertFalse(s1 != an1)
        self.assertTrue(s1 <= an1)
        self.assertFalse(s1 < an1)
        self.assertTrue(s1 >= an1)
        self.assertFalse(s1 > an1)
        # an1 ? a1
        self.assertTrue(an1 == s1)
        self.assertFalse(an1 != s1)
        self.assertTrue(an1 <= s1)
        self.assertFalse(an1 < s1)
        self.assertTrue(an1 >= s1)
        self.assertFalse(an1 > s1)

    class FakeDOM:
        namespaceURI = None
        localName = None

    def testConstructor (self):
        ln = 'local'
        ns_uri = 'urn:ns'
        en = ExpandedName(ln)
        self.assertEqual(en.namespace(), None)
        self.assertEqual(en.localName(), ln)
        en2 = ExpandedName(en)
        self.assertEqual(en2, en)
        dom = pyxb.utils.domutils.StringToDOM('<ns1:%s xmlns:ns1="%s" attr="52">content</ns1:%s>' % (ln, ns_uri, ln))
        en = ExpandedName(dom.documentElement)
        ns = pyxb.namespace.NamespaceForURI(ns_uri)
        self.assertTrue(ns is not None)
        self.assertEqual(ns, en.namespace())
        self.assertEqual(ln, en.localName())
        en2 = ExpandedName(ns, ln)
        self.assertEqual(en, en2)
        attr = dom.documentElement.getAttributeNodeNS(None, 'attr')
        self.assertTrue(attr is not None)
        en = ExpandedName(attr)
        self.assertEqual(xml.dom.EMPTY_NAMESPACE, en.namespaceURI())
        self.assertEqual('attr', en.localName())
        child = dom.documentElement.firstChild
        self.assertTrue(child is not None)
        self.assertEqual(xml.dom.Node.TEXT_NODE, child.nodeType)
        self.assertRaises(pyxb.LogicError, ExpandedName, child)

    def testMapping (self):
        an1 = ExpandedName(None, 'string')
        en1 = ExpandedName(xsd, 'string')
        en2 = ExpandedName(xsd, 'string')
        mymap = { }
        mymap[en1] = 'Yes'
        mymap[an1] = 'No'
        mymap['key'] = 'Key'
        self.assertEqual(mymap[en2], 'Yes')
        self.assertEqual(mymap[an1], 'No')
        self.assertEqual(mymap[an1.localName()], 'No')
        self.assertNotEqual(mymap[en2.localName()], 'Yes')
        self.assertEqual(mymap['key'], 'Key')
        self.assertEqual(mymap[ExpandedName(None, 'key')], 'Key')
        self.assertEqual(None, mymap.get('nokey'))
        del mymap[en2]
        self.assertEqual(None, mymap.get(en1))

    def testOrdering (self):
        s1 = "one"
        s2 = "two"
        en1 = ExpandedName(None, s1)
        en2 = ExpandedName(None, s2)
        xn1 = ExpandedName(xsd, s1)
        xn2 = ExpandedName(xsd, s2)
        self.assertTrue(s1 < s2)
        self.assertTrue(s2 > s1)
        self.assertTrue(en1 < s2)
        self.assertTrue(en2 > s1)

    def testAbsent (self):
        an = pyxb.namespace.CreateAbsentNamespace()
        an2 = pyxb.namespace.CreateAbsentNamespace()
        self.assertNotEqual(an, an2)
        self.assertEqual(an.uri(), an2.uri())
        ln = 'local'
        en1 = ExpandedName(None, ln)
        en2 = ExpandedName(an, ln)
        en3 = ExpandedName(an2, ln)
        self.assertEqual(en1, en2)
        self.assertEqual(en1, en3)
        self.assertEqual(en2, en3)
        self.assertEqual(hash(en1), hash(en2))
        self.assertEqual(hash(en1), hash(en3))
        self.assertEqual(hash(en2), hash(en3))

    def testCategoryDeferral (self):
        int_en = pyxb.namespace.ExpandedName(xsd, 'int')
        self.assertEqual(xsd_module.int, int_en.typeBinding())
        self.assertRaises(pyxb.NamespaceError, getattr, int_en, 'notACategory')

class TestCategories (unittest.TestCase):
    def testXSDCategories (self):
        # Need type and element bindings, along with all the component ones
        self.assertTrue('elementBinding' in xsd.categories())
        self.assertTrue('typeBinding' in xsd.categories())

    def testStandard (self):
        def_map = xsd.categoryMap('typeDefinition')
        binding_map = xsd.categoryMap('typeBinding')
        int_en = pyxb.namespace.ExpandedName(xsd, 'int')
        self.assertEqual(xsd_module.int, binding_map['int'])
        self.assertEqual(xsd_module.int.SimpleTypeDefinition(), def_map['int'])
        self.assertEqual(int_en.typeDefinition(), def_map['int'])
        self.assertEqual(xsd_module.int, int_en.typeBinding())

    def testNoCategory (self):
        self.assertRaises(pyxb.NamespaceError, pyxb.namespace.XMLSchema.categoryMap, 'not a category')

if '__main__' == __name__:
    unittest.main()
