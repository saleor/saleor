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
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-mg-choice.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils
def ToDOM (instance):
    return instance.toDOM().documentElement

import unittest

class TestMGChoice (unittest.TestCase):
    def onlyFirst (self, instance):
        self.assertTrue(isinstance(instance.first, choice.typeDefinition()._ElementMap['first'].elementBinding().typeDefinition()))
        self.assertTrue(instance.second is None)
        self.assertTrue(instance.third is None)

    def onlySecond (self, instance):
        self.assertTrue(instance.first is None)
        self.assertTrue(isinstance(instance.second, choice.typeDefinition()._ElementMap['second'].elementBinding().typeDefinition()))
        self.assertTrue(instance.third is None)

    def onlyThird (self, instance):
        self.assertTrue(instance.first is None)
        self.assertTrue(instance.second is None)
        self.assertTrue(isinstance(instance.third, choice.typeDefinition()._ElementMap['third'].elementBinding().typeDefinition()))

    def testSingleChoice (self):
        xmlt = six.u('<ns1:choice xmlns:ns1="URN:test-mg-choice"><first/></ns1:choice>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = choice.createFromDOM(dom.documentElement)
        self.onlyFirst(instance)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

        xmlt = six.u('<ns1:choice xmlns:ns1="URN:test-mg-choice"><second/></ns1:choice>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = choice.createFromDOM(dom.documentElement)
        self.onlySecond(instance)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

        xmlt = six.u('<ns1:choice xmlns:ns1="URN:test-mg-choice"><third/></ns1:choice>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = choice.createFromDOM(dom.documentElement)
        self.onlyThird(instance)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testMissingSingle (self):
        xmlt = six.u('<ns1:choice xmlns:ns1="URN:test-mg-choice"/>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(IncompleteElementContentError, choice.createFromDOM, dom.documentElement)

    def testTooManySingle (self):
        xmlt = six.u('<ns1:choice xmlns:ns1="URN:test-mg-choice"><first/><second/></ns1:choice>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, choice.createFromDOM, dom.documentElement)

        xmlt = six.u('<ns1:choice xmlns:ns1="URN:test-mg-choice"><second/><third/></ns1:choice>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, choice.createFromDOM, dom.documentElement)

    def testMultichoice (self):
        xmlt = six.u('<ns1:multiplechoice xmlns:ns1="URN:test-mg-choice"/>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = multiplechoice.createFromDOM(dom.documentElement)
        self.assertEqual(0, len(instance.first))
        self.assertEqual(0, len(instance.second))
        self.assertEqual(0, len(instance.third))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

        xmlt = six.u('<ns1:multiplechoice xmlns:ns1="URN:test-mg-choice"><first/></ns1:multiplechoice>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = multiplechoice.createFromDOM(dom.documentElement)
        self.assertEqual(1, len(instance.first))
        self.assertEqual(0, len(instance.second))
        self.assertEqual(0, len(instance.third))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

        xmlt = six.u('<ns1:multiplechoice xmlns:ns1="URN:test-mg-choice"><first/><first/><first/><third/></ns1:multiplechoice>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = multiplechoice.createFromDOM(dom.documentElement)
        self.assertEqual(3, len(instance.first))
        self.assertEqual(0, len(instance.second))
        self.assertEqual(1, len(instance.third))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testMultichoiceOrderImportant (self):
        xmlt = six.u('<ns1:multiplechoice xmlns:ns1="URN:test-mg-choice"><first/><third/><first/></ns1:multiplechoice>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = multiplechoice.createFromDOM(dom.documentElement)
        self.assertEqual(2, len(instance.first))
        self.assertEqual(0, len(instance.second))
        self.assertEqual(1, len(instance.third))
        # @todo This test will fail because both firsts will precede the second.
        #self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)


    def testAltMultichoice (self):
        xmlt = six.u('<ns1:altmultiplechoice xmlns:ns1="URN:test-mg-choice"/>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = altmultiplechoice.createFromDOM(dom.documentElement)
        self.assertEqual(0, len(instance.first))
        self.assertEqual(0, len(instance.second))
        self.assertEqual(0, len(instance.third))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

        xmlt = six.u('<ns1:altmultiplechoice xmlns:ns1="URN:test-mg-choice"><first/></ns1:altmultiplechoice>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = altmultiplechoice.createFromDOM(dom.documentElement)
        self.assertEqual(1, len(instance.first))
        self.assertEqual(0, len(instance.second))
        self.assertEqual(0, len(instance.third))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

        xmlt = six.u('<ns1:altmultiplechoice xmlns:ns1="URN:test-mg-choice"><first/><first/><third/></ns1:altmultiplechoice>')
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = altmultiplechoice.createFromDOM(dom.documentElement)
        self.assertEqual(2, len(instance.first))
        self.assertEqual(0, len(instance.second))
        self.assertEqual(1, len(instance.third))
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testTooManyChoices (self):
        xmlt = six.u('<ns1:altmultiplechoice xmlns:ns1="URN:test-mg-choice"><first/><first/><first/><third/></ns1:altmultiplechoice>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, altmultiplechoice.createFromDOM, dom.documentElement)

    def testFixedMultichoice (self):
        xmlt = six.u('<fixedMultichoice xmlns="URN:test-mg-choice"></fixedMultichoice>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = fixedMultichoice.createFromDOM(dom.documentElement)
        xmlt = six.u('<ns1:fixedMultichoice xmlns:ns1="URN:test-mg-choice"><A/><A/></ns1:fixedMultichoice>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = fixedMultichoice.createFromDOM(dom.documentElement)
        xmlt = six.u('<ns1:fixedMultichoice xmlns:ns1="URN:test-mg-choice"><A/><B/></ns1:fixedMultichoice>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, fixedMultichoice.createFromDOM, dom.documentElement)

if __name__ == '__main__':
    unittest.main()
