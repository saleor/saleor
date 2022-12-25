# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-ctd-extension.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestCTDExtension (unittest.TestCase):
    def setUp (self):
        # Hide the warning about failure to convert DOM node {}third
        # to a binding
        self.__basis_log = logging.getLogger('pyxb.binding.basis')
        self.__basis_loglevel = self.__basis_log.level

    def tearDown (self):
        self.__basis_log.level = self.__basis_loglevel

    def testStructure (self):
        # Extension should be a subclass of parent
        self.assertTrue(issubclass(extendedName, personName))
        # References in subclass to parent class elements/attributes
        # should be the same, unless content model requires they be
        # different.
        self.assertEqual(extendedName.title, personName.title)

    def testPersonName (self):
        xml = '''<oldAddressee pAttr="old">
   <forename>Albert</forename>
   <forename>Arnold</forename>
   <surname>Gore</surname>
  </oldAddressee>'''
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = oldAddressee.createFromDOM(doc.documentElement)
        self.assertEqual(2, len(instance.forename))
        # Note double dereference required because xs:anyType was used
        # as the element type
        self.assertEqual('Albert', instance.forename[0].orderedContent()[0].value)
        self.assertEqual('Arnold', instance.forename[1].orderedContent()[0].value)
        self.assertEqual('Gore', instance.surname.orderedContent()[0].value)
        self.assertEqual('old', instance.pAttr)

    def testExtendedName (self):
        xml = '''<addressee pAttr="new" eAttr="add generation">
   <forename>Albert</forename>
   <forename>Arnold</forename>
   <surname>Gore</surname>
   <generation>Jr</generation>
  </addressee>'''
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = addressee.createFromDOM(doc.documentElement)
        self.assertEqual(2, len(instance.forename))
        self.assertEqual('Albert', instance.forename[0].orderedContent()[0].value)
        self.assertEqual('Arnold', instance.forename[1].orderedContent()[0].value)
        self.assertEqual('Gore', instance.surname.orderedContent()[0].value)
        self.assertEqual('Jr', instance.generation.orderedContent()[0].value)
        self.assertEqual('new', instance.pAttr)
        self.assertEqual('add generation', instance.eAttr)

    def testMidWildcard (self):
        # Hide the warnings that other:something could not be converted
        self.__basis_log.setLevel(logging.ERROR)
        xml = '<defs xmlns:other="other"><documentation/><other:something/><message/><message/><import/><message/></defs>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = defs.createFromDOM(doc.documentElement)
        self.assertFalse(instance.documentation is None)
        self.assertEqual(3, len(instance.message))
        self.assertEqual(1, len(instance.import_))
        self.assertEqual(1, len(instance.wildcardElements()))

        xml = '<defs xmlns:other="other"><other:something/><other:else/><message/><message/><import/><message/></defs>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = defs.createFromDOM(doc.documentElement)
        self.assertTrue(instance.documentation is None)
        self.assertEqual(3, len(instance.message))
        self.assertEqual(1, len(instance.import_))
        self.assertEqual(2, len(instance.wildcardElements()))

    def testEndWildcard (self):
        # Hide the warnings that other:something could not be converted
        self.__basis_log.setLevel(logging.ERROR)
        xml = '<defs xmlns:other="other"><message/><other:something/></defs>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(UnrecognizedContentError, defs.createFromDOM, doc.documentElement)

if __name__ == '__main__':
    unittest.main()
