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
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-mg-sequence.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils
def ToDOM (instance, tag=None):
    return instance.toDOM().documentElement

import unittest
import collections

class TestMGSeq (unittest.TestCase):
    def setUp (self):
        # Hide the warning about failure to convert DOM node {}third
        # to a binding
        self.__basis_log = logging.getLogger('pyxb.binding.basis')
        self.__basis_loglevel = self.__basis_log.level

    def tearDown (self):
        self.__basis_log.level = self.__basis_loglevel

    def testBad (self):
        # Second is wrong element tag
        # Hide warning about failure to convert
        self.__basis_log.level = logging.ERROR
        xml = '<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><second/><third/><fourth_0_2/></ns1:wrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(UnrecognizedContentError, wrapper.createFromDOM, dom.documentElement)

    def testBasics (self):
        xmlt = six.u('<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><second_opt/><third/><fourth_0_2/></ns1:wrapper>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = wrapper.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, sequence._ElementMap['first'].elementBinding().typeDefinition()))
        self.assertTrue(isinstance(instance.second_opt, sequence._ElementMap['second_opt'].elementBinding().typeDefinition()))
        self.assertTrue(isinstance(instance.third, sequence._ElementMap['third'].elementBinding().typeDefinition()))
        self.assertTrue(isinstance(instance.fourth_0_2, collections.MutableSequence))
        self.assertEqual(1, len(instance.fourth_0_2))
        self.assertTrue(isinstance(instance.fourth_0_2[0], sequence._ElementMap['fourth_0_2'].elementBinding().typeDefinition()))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testMultiplesAtEnd (self):
        xmlt = six.u('<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><third/><fourth_0_2/><fourth_0_2/></ns1:wrapper>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = wrapper.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, sequence._ElementMap['first'].elementBinding().typeDefinition()))
        self.assertTrue(instance.second_opt is None)
        self.assertTrue(isinstance(instance.third, sequence._ElementMap['third'].elementBinding().typeDefinition()))
        self.assertTrue(isinstance(instance.fourth_0_2, collections.MutableSequence))
        self.assertEqual(2, len(instance.fourth_0_2))
        self.assertTrue(isinstance(instance.fourth_0_2[0], sequence._ElementMap['fourth_0_2'].elementBinding().typeDefinition()))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testMultiplesInMiddle (self):
        xmlt = six.u('<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><first/><second_multi/><second_multi/><third/></ns1:altwrapper>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = altwrapper.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, collections.MutableSequence))
        self.assertEqual(1, len(instance.first))
        self.assertEqual(2, len(instance.second_multi))
        self.assertTrue(isinstance(instance.third, altsequence._ElementMap['third'].elementBinding().typeDefinition()))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testMultiplesAtStart (self):
        xmlt = six.u('<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><first/><first/><third/></ns1:altwrapper>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = altwrapper.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, collections.MutableSequence))
        self.assertEqual(2, len(instance.first))
        self.assertEqual(0, len(instance.second_multi))
        self.assertTrue(isinstance(instance.third, altsequence._ElementMap['third'].elementBinding().typeDefinition()))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)
        instance = altwrapper(first=[ altsequence._ElementMap['first'].elementBinding()(), altsequence._ElementMap['first'].elementBinding()() ], third=altsequence._ElementMap['third'].elementBinding()())
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testMissingInMiddle (self):
        xmlt = six.u('<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><third/></ns1:wrapper>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = wrapper.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, sequence._ElementMap['first'].elementBinding().typeDefinition()))
        self.assertTrue(instance.second_opt is None)
        self.assertTrue(isinstance(instance.third, sequence._ElementMap['third'].elementBinding().typeDefinition()))
        self.assertTrue(isinstance(instance.fourth_0_2, collections.MutableSequence))
        self.assertEqual(0, len(instance.fourth_0_2))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testMissingAtStart (self):
        xmlt = six.u('<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><third/></ns1:altwrapper>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, altwrapper.createFromDOM, dom.documentElement)
        instance = altwrapper(third=altsequence._ElementMap['third'].elementBinding()())
        self.assertRaises(pyxb.IncompleteElementContentError, ToDOM, instance)

    def testMissingAtEndLeadingContent (self):
        xmlt = six.u('<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><first/></ns1:altwrapper>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(IncompleteElementContentError, altwrapper.createFromDOM, dom.documentElement)

    def testMissingAtEndNoContent (self):
        xmlt = six.u('<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"></ns1:altwrapper>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(IncompleteElementContentError, altwrapper.createFromDOM, dom.documentElement)

    def testTooManyAtEnd (self):
        xmlt = six.u('<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><third/><fourth_0_2/><fourth_0_2/><fourth_0_2/></ns1:wrapper>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, wrapper.createFromDOM, dom.documentElement)

    def testTooManyAtStart (self):
        xmlt = six.u('<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><first/><first/><first/><third/></ns1:altwrapper>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, altwrapper.createFromDOM, dom.documentElement)
        instance = altwrapper(first=[ altsequence._ElementMap['first'].elementBinding()(), altsequence._ElementMap['first'].elementBinding()(), altsequence._ElementMap['first'].elementBinding()() ], third=altsequence._ElementMap['third'].elementBinding()())
        self.assertRaises(pyxb.UnprocessedElementContentError, ToDOM, instance)
        if sys.version_info[:2] >= (2, 7):
            with self.assertRaises(UnprocessedElementContentError) as cm:
                instance.toxml('utf-8')
            # Verify the exception tells us what was being processed
            self.assertEqual(instance, cm.exception.instance)
            # Verify the exception tells us what was left over
            first_ed = altsequence._ElementMap['first']
            self.assertEqual(instance.first[2], cm.exception.symbol_set[first_ed][0])

    def testTooManyInMiddle (self):
        xml = '<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><second_multi/><second_multi/><second_multi/><third/></ns1:altwrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(UnrecognizedContentError, altwrapper.createFromDOM, dom.documentElement)


if __name__ == '__main__':
    unittest.main()
