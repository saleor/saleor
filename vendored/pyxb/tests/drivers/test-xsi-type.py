# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six

from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/xsi-type.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

originalOneFloor = oneFloor
def oneFloorCtor (*args, **kw):
    return restaurant(*args, **kw)
originalOneFloor._SetAlternativeConstructor(oneFloorCtor)

from pyxb.exceptions_ import *

import unittest

class TestXSIType (unittest.TestCase):
    def testFailsNoType (self):
        xmlt = six.u('<elt/>')
        doc = pyxb.utils.domutils.StringToDOM(xmlt)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, doc.documentElement)

    def testDirect (self):
        xmlt = six.u('<notAlt attrOne="low"><first>content</first></notAlt>')
        doc = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual('content', instance.first)
        self.assertEqual('low', instance.attrOne)

    def testSubstitutions (self):
        xmlt = six.u('<elt attrOne="low" xsi:type="alt1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><first>content</first></elt>')
        doc = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual('content', instance.first)
        self.assertEqual('low', instance.attrOne)
        xmlt = six.u('<elt attrTwo="hi" xsi:type="alt2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><second/></elt>')
        doc = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = CreateFromDOM(doc.documentElement)
        self.assertTrue(instance.second is not None)
        self.assertEqual('hi', instance.attrTwo)

    def testMultilevel (self):
        xmlt = six.u('<concreteBase><basement>dirt floor</basement></concreteBase>')
        doc = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual('dirt floor', instance.basement)
        xmlt = six.u('<oneFloor xsi:type="restaurant" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><basement>concrete</basement><lobby>tiled</lobby><room>eats</room></oneFloor>')
        doc = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(concreteBase_.basement, instance.__class__.basement)
        self.assertEqual(oneFloor_.lobby, instance.__class__.lobby)
        self.assertEqual(restaurant_.room, instance.__class__.room)
        self.assertEqual('tiled', instance.lobby)
        self.assertEqual('eats', instance.room)

    def testConstructor (self):
        kw = { 'basement' : 'concrete',
               'lobby' : 'tiled',
               'room' : 'eats' }
        ctd = restaurant_(**kw)
        dom = ctd.toDOM(element_name='restaurant').documentElement
        xmlt = six.u('<restaurant><basement>concrete</basement><lobby>tiled</lobby><room>eats</room></restaurant>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(dom.toxml("utf-8"), xmld)

        rest = restaurant(**kw)
        dom = rest.toDOM().documentElement
        self.assertEqual(dom.toxml("utf-8"), xmld)

        self.assertRaises(pyxb.AbstractInstantiationError, originalOneFloor, **kw)

    def testNesting (self):
        instance = block(oneFloor=[ restaurant(basement="dirt", lobby="tile", room="messy"),
                                    restaurant(basement="concrete", lobby="carpet", room="tidy")])
        self.assertEqual('dirt', instance.oneFloor[0].basement)
        self.assertEqual('messy', instance.oneFloor[0].room)
        self.assertEqual('concrete', instance.oneFloor[1].basement)
        self.assertEqual('tidy', instance.oneFloor[1].room)
        xmld = instance.toxml("utf-8")
        dom = pyxb.utils.domutils.StringToDOM(xmld)
        instance2 = CreateFromDOM(dom.documentElement)
        r2d = instance2.toxml("utf-8")
        r3d = instance2.toxml("utf-8")
        self.assertEqual(r2d, r3d)
        self.assertEqual(xmld, r2d)

if __name__ == '__main__':
    unittest.main()
