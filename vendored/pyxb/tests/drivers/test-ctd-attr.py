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
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-ctd-attr.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)
Namespace.setPrefix('tca')

from pyxb.exceptions_ import *

import unittest

from pyxb.utils import domutils
def ToDOM (instance):
    return instance.toDOM().documentElement

def assign (lhs, rhs):
    lhs = rhs

class TestCTD (unittest.TestCase):


    # Make sure that name collisions are deconflicted in favor of the
    # element declaration.
    def testDeconflict (self):
        self.assertTrue(isinstance(structure, pyxb.binding.basis.element))
        self.assertTrue(issubclass(structure_, pyxb.binding.basis.complexTypeDefinition))
        self.assertTrue(pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY == structure_._ContentTypeTag)

    def testSimple (self):
        self.assertEqual('test', simple_('test').value())

        # Note that when the element is a complex type with simple
        # content, we remove the extra level of indirection so the
        # element content is the same as the ctd content.  Otherwise,
        # you'd have to do foo.content().content() to get to the
        # interesting stuff.  I suppose that ought to be a
        # configuration option.
        self.assertEqual('test', simple('test').value())
        xmlt = six.u('<tca:simple xmlns:tca="URN:testCTD">test</tca:simple>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmlt)
        self.assertEqual('test', instance.value())
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testString (self):
        self.assertEqual('test', pyxb.binding.datatypes.string('test'))
        rv = string('test')
        self.assertTrue(isinstance(rv, pyxb.binding.datatypes.string))
        self.assertEqual('test', rv)
        rv = CreateFromDocument('<string xmlns="URN:testCTD">test</string>')
        self.assertTrue(isinstance(rv, pyxb.binding.datatypes.string))
        # Temporarily fails because string is an element, not an elementBinding
        self.assertEqual(string, rv._element())
        self.assertEqual('test', rv)

    def setImmutable (self, instance, value):
        instance.immutable = value

    def testEmptyWithAttr (self):
        self.assertEqual(5, len(emptyWithAttr.typeDefinition()._AttributeMap))
        self.assertRaises(MissingAttributeError, CreateFromDocument, '<emptyWithAttr xmlns="URN:testCTD"/>')
        instance = CreateFromDocument('<emptyWithAttr capitalized="false" xmlns="URN:testCTD"/>')
        self.assertEqual('irish', instance.language)
        self.assertTrue(not instance.capitalized)
        self.assertEqual(5432, instance.port)
        self.assertEqual('top default', instance.tlAttr)
        self.assertEqual('stone', instance.immutable)

        instance.tlAttr = 'new value'
        self.assertEqual('new value', instance.tlAttr)

        # Can't change immutable attributes
        self.assertRaises(AttributeChangeError, self.setImmutable, instance, 'water')
        self.assertRaises(AttributeChangeError, CreateFromDocument, '<emptyWithAttr capitalized="true" immutable="water"  xmlns="URN:testCTD"/>')

        instance = CreateFromDocument('<emptyWithAttr capitalized="true" language="hebrew"  xmlns="URN:testCTD"/>')
        self.assertEqual('hebrew', instance.language)
        self.assertTrue(instance.capitalized)
        self.assertEqual(5432, instance.port)
        # Raw constructor generates default everything; optional
        # attributes may have value None.
        instance = emptyWithAttr()
        self.assertEqual('irish', instance.language)
        self.assertTrue(instance.capitalized is None)
        self.assertEqual(5432, instance.port)
        self.assertRaises(pyxb.MissingAttributeError, ToDOM, instance)
        instance.capitalized = False
        xmlt = six.u('<tca:emptyWithAttr capitalized="false" xmlns:tca="URN:testCTD"/>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

        # Test reference attribute
        self.assertEqual('top default', instance.tlAttr)

        # Create another instance, to make sure the attributes are different
        instance2 = emptyWithAttr()
        self.assertEqual('irish', instance2.language)
        instance2.language = 'french'
        instance2.capitalized = False
        xmlt = six.u('<tca:emptyWithAttr capitalized="false" language="french" xmlns:tca="URN:testCTD"/>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(ToDOM(instance2).toxml("utf-8"), xmld)
        self.assertNotEqual(instance.language, instance2.language)

        # Verify the use.  Note reference through CTD not element.
        au = emptyWithAttr_._AttributeMap['language']
        self.assertFalse(au.required())
        self.assertFalse(au.prohibited())
        au = emptyWithAttr_._AttributeMap['capitalized']
        self.assertTrue(au.required())
        self.assertFalse(au.prohibited())

    def testRestrictedEWA (self):
        # Verify the use.  Note reference through CTD not element.
        # language is marked prohibited in the restriction
        self.assertNotEqual(restrictedEWA_._AttributeMap['language'], emptyWithAttr_._AttributeMap['language'])
        au = restrictedEWA_._AttributeMap['language']
        self.assertTrue(au.prohibited())
        # capitalized passes through the restriction untouched
        self.assertEqual(restrictedEWA_._AttributeMap['capitalized'], emptyWithAttr_._AttributeMap['capitalized'])

    def testEmptyWithAttrGroups (self):
        xmlt = six.u('<tca:emptyWithAttrGroups bMember1="xxx" xmlns:tca="URN:testCTD"/>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmlt)
        self.assertEqual('gM1', instance.groupMember1)
        self.assertEqual('gM2', instance.groupMember2)
        self.assertEqual('xxx', instance.bMember1)
        self.assertEqual('lA1', instance.localAttr1)
        # Note that defaulted attributes are not generated in the DOM.
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

        # Test reference attribute with changed default
        self.assertEqual('refDefault', instance.tlAttr)

    def testUnrecognizedAttribute (self):
        xmlt = six.u('<emptyWithAttr capitalized="false" garbage="what is this" xmlns="URN:testCTD"/>')
        doc = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedAttributeError, emptyWithAttr.createFromDOM, doc.documentElement)

if __name__ == '__main__':
    unittest.main()
