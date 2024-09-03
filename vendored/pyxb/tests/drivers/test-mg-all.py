# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node
import sys

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-mg-all.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils
def ToDOM (instance):
    return instance.toDOM().documentElement

import unittest

class TestMGAll (unittest.TestCase):
    def testRequired (self):
        xmlt = '<ns1:required xmlns:ns1="URN:test-mg-all"/>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(IncompleteElementContentError, required.createFromDOM, dom.documentElement)

        xmlt = '<ns1:required xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = required.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, required.memberElement('first').typeDefinition()))
        self.assertTrue(isinstance(instance.second, required.memberElement('second').typeDefinition()))
        self.assertTrue(isinstance(instance.third, required.memberElement('third').typeDefinition()))

    def testRequiredMisordered (self):
        xmlt = '<ns1:required xmlns:ns1="URN:test-mg-all"><third/><first/><second/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = required.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, required.memberElement('first').typeDefinition()))
        self.assertTrue(isinstance(instance.second, required.memberElement('second').typeDefinition()))
        self.assertTrue(isinstance(instance.third, required.memberElement('third').typeDefinition()))

    def testRequiredTooMany (self):
        xmlt = '<ns1:required xmlns:ns1="URN:test-mg-all"><third/><first/><second/><third/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, required.createFromDOM, dom.documentElement)

    def testThirdOptional (self):
        xmlt = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = thirdOptional.Factory(_dom_node=dom.documentElement)
        self.assertTrue(isinstance(instance.first, thirdOptional._ElementMap['first'].elementBinding().typeDefinition()))
        self.assertTrue(isinstance(instance.second, thirdOptional._ElementMap['second'].elementBinding().typeDefinition()))
        self.assertTrue(instance.third is None)

        xmlt = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = thirdOptional.Factory(_dom_node=dom.documentElement)
        self.assertTrue(isinstance(instance.first, thirdOptional._ElementMap['first'].elementBinding().typeDefinition()))
        self.assertTrue(isinstance(instance.second, thirdOptional._ElementMap['second'].elementBinding().typeDefinition()))
        self.assertTrue(isinstance(instance.third, thirdOptional._ElementMap['third'].elementBinding().typeDefinition()))

        xmlt = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/><third/><first/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, thirdOptional.Factory, _dom_node=dom.documentElement)

    def testOptional (self):
        xmlt = '<ns1:optional xmlns:ns1="URN:test-mg-all"/>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = optional.createFromDOM(dom.documentElement)
        self.assertTrue(instance.first is None)
        self.assertTrue(instance.second is None)
        self.assertTrue(instance.third is None)

        xmlt = '<ns1:optional xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = optional.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, optional.memberElement('first').typeDefinition()))
        self.assertTrue(isinstance(instance.second, optional.memberElement('second').typeDefinition()))
        self.assertTrue(isinstance(instance.third, optional.memberElement('third').typeDefinition()))

        xmlt = '<ns1:optional xmlns:ns1="URN:test-mg-all"><first/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = optional.createFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance.first, optional.memberElement('first').typeDefinition()))
        self.assertTrue(instance.second is None)
        self.assertTrue(isinstance(instance.third, optional.memberElement('third').typeDefinition()))

        xmlt = '<ns1:optional xmlns:ns1="URN:test-mg-all"><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = optional.createFromDOM(dom.documentElement)
        self.assertTrue(instance.first is None)
        self.assertTrue(instance.second is None)
        self.assertTrue(isinstance(instance.third, optional.memberElement('third').typeDefinition()))

    def testOptionalTooMany (self):
        xmlt = '<ns1:optional xmlns:ns1="URN:test-mg-all"><third/><first/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(UnrecognizedContentError, optional.createFromDOM, dom.documentElement)

    def stripMembers (self, xmlt, body):
        for b in body:
            xmlt = xmlt.replace('<%s/>' % (b,), 'X')
        return xmlt

    def testMany (self):
        for body in [ "abcdefgh", "fghbcd", "bfgcahd" ]:
            xmlt = '<ns1:many xmlns:ns1="URN:test-mg-all">%s</ns1:many>' % (''.join([ '<%s/>' % (_x,) for _x in body ]),)
            dom = pyxb.utils.domutils.StringToDOM(xmlt)
            instance = many.createFromDOM(dom.documentElement)
            instance.validateBinding()
            xml2d = ToDOM(instance).toxml("utf-8")
            xml2t = xml2d.decode('utf-8')
            rev = self.stripMembers(xml2t, body)
            self.assertEqual('<ns1:many xmlns:ns1="URN:test-mg-all">%s</ns1:many>' % (''.join(len(body)*['X']),), rev)
        many_a = many.memberElement('a')
        many_c = many.memberElement('c')
        many_d = many.memberElement('d')
        many_e = many.memberElement('e')
        many_f = many.memberElement('f')
        many_g = many.memberElement('g')
        many_h = many.memberElement('h')
        instance = many(a=many_a(), c=many_c(), d=many_d(), e=many_e(), f=many_f(), g=many_g(), h=many_h())
        self.assertRaises(pyxb.IncompleteElementContentError, instance.validateBinding)
        self.assertRaises(pyxb.IncompleteElementContentError, ToDOM, instance)
        if sys.version_info[:2] >= (2, 7):
            with self.assertRaises(IncompleteElementContentError) as cm:
                instance.validateBinding()
            acceptable = cm.exception.fac_configuration.acceptableSymbols()
            self.assertEqual(1, len(acceptable))
            self.assertEqual(many.memberElement('b'), acceptable[0].elementDeclaration().elementBinding())

if __name__ == '__main__':
    unittest.main()
