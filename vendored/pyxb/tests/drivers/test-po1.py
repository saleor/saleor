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
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/po1.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

#open('code.py', 'w').write(code)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils

def ToDOM (instance, dom_support=None):
    return instance.toDOM(dom_support).documentElement

import unittest

class TestPO1 (unittest.TestCase):
    street_content = '''95 Main St.
Anytown, AS  12345-6789'''
    street_xmlt = six.u('<street>%s</street>') % (street_content,)
    street_xmld = street_xmlt.encode('utf-8')
    street_dom = pyxb.utils.domutils.StringToDOM(street_xmlt).documentElement

    address1_xmlt = six.u('<name>Customer</name><street>95 Main St</street>')
    address2_xmlt = six.u('<name>Sugar Mama</name><street>24 E. Dearling Ave.</street>')

    def tearDown (self):
        pyxb.RequireValidWhenGenerating(True)
        pyxb.RequireValidWhenParsing(True)

    def testPythonElementSimpleContent (self):
        elt = USAddress._ElementMap['street'].elementBinding()(self.street_content)
        self.assertEqual(self.street_content, elt)
        self.assertEqual(ToDOM(elt).toxml("utf-8"), self.street_xmld)

    def testDOMElementSimpleContent (self):
        elt = USAddress._ElementMap['street'].elementBinding().createFromDOM(self.street_dom)
        self.assertEqual(ToDOM(elt).toxml("utf-8"), self.street_xmld)

    def testPythonElementComplexContent_Element (self):
        addr = USAddress(name='Customer', street='95 Main St')
        self.assertEqual('95 Main St', addr.street)
        addr = USAddress('Customer', '95 Main St')
        self.assertEqual('95 Main St', addr.street)
        addr.street = '43 West Oak'
        self.assertEqual('43 West Oak', addr.street)

    def testDOM_CTD_element (self):
        # NB: USAddress is a CTD, not an element.
        xmlt = six.u('<shipTo>%s</shipTo>') % (self.address1_xmlt,)
        xmld = xmlt.encode('utf-8')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        addr2 = USAddress.Factory(_dom_node=dom.documentElement)

    def testPurchaseOrder (self):
        po = purchaseOrder(shipTo=USAddress(name='Customer', street='95 Main St'),
                           billTo=USAddress(name='Sugar Mama', street='24 E. Dearling Ave'),
                           comment='Thanks!')
        xmld = ToDOM(po).toxml("utf-8")
        xml1t = '<ns1:purchaseOrder xmlns:ns1="http://www.example.com/PO1"><shipTo><name>Customer</name><street>95 Main St</street></shipTo><billTo><name>Sugar Mama</name><street>24 E. Dearling Ave</street></billTo><ns1:comment>Thanks!</ns1:comment></ns1:purchaseOrder>'
        xml1d = xml1t.encode('utf-8')
        self.assertEqual(xmld, xml1d)

        dom = pyxb.utils.domutils.StringToDOM(xmld)
        po2 = purchaseOrder.createFromDOM(dom.documentElement)
        self.assertEqual(xml1d, ToDOM(po2).toxml("utf-8"))
        loc = po2.shipTo._location()
        self.assertTrue((not isinstance(loc, pyxb.utils.utility.Locatable_mixin)) or (58 == loc.columnNumber))
        loc = po2.billTo.name._location()
        self.assertTrue((not isinstance(loc, pyxb.utils.utility.Locatable_mixin)) or (131 == loc.columnNumber))

        po2 = CreateFromDocument(xmld)
        self.assertEqual(xml1d, ToDOM(po2).toxml("utf-8"))
        loc = po2.shipTo._location()
        self.assertTrue((not isinstance(loc, pyxb.utils.utility.Locatable_mixin)) or (58 == loc.columnNumber))
        loc = po2.billTo.name._location()
        self.assertTrue((not isinstance(loc, pyxb.utils.utility.Locatable_mixin)) or (131 == loc.columnNumber))

        xml2t = '<purchaseOrder xmlns="http://www.example.com/PO1"><shipTo><name>Customer</name><street>95 Main St</street></shipTo><billTo><name>Sugar Mama</name><street>24 E. Dearling Ave</street></billTo><comment>Thanks!</comment></purchaseOrder>'
        xml2d = xml2t.encode('utf-8')
        bds = pyxb.utils.domutils.BindingDOMSupport()
        bds.setDefaultNamespace(Namespace)
        self.assertEqual(xml2d, ToDOM(po2, dom_support=bds).toxml("utf-8"))

    def testGenerationValidation (self):
        ship_to = USAddress('Robert Smith', 'General Delivery')
        po = purchaseOrder(ship_to)
        self.assertEqual('General Delivery', po.shipTo.street)
        self.assertTrue(po.billTo is None)

        self.assertTrue(pyxb.RequireValidWhenGenerating())
        self.assertRaises(pyxb.IncompleteElementContentError, po.toxml)
        try:
            pyxb.RequireValidWhenGenerating(False)
            self.assertFalse(pyxb.RequireValidWhenGenerating())
            xmlt = six.u('<ns1:purchaseOrder xmlns:ns1="http://www.example.com/PO1"><shipTo><street>General Delivery</street><name>Robert Smith</name></shipTo></ns1:purchaseOrder>')
            xmlta = six.u('<ns1:purchaseOrder xmlns:ns1="http://www.example.com/PO1"><shipTo><name>Robert Smith</name><street>General Delivery</street></shipTo></ns1:purchaseOrder>')
            xmlds = [ _xmlt.encode('utf-8') for _xmlt in (xmlt, xmlta) ]
            self.assertTrue(po.toxml("utf-8", root_only=True) in xmlds)
        finally:
            pyxb.RequireValidWhenGenerating(True)
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDocument, xmlt)
        self.assertTrue(pyxb.RequireValidWhenParsing())
        try:
            pyxb.RequireValidWhenParsing(False)
            self.assertFalse(pyxb.RequireValidWhenParsing())
            po2 = CreateFromDocument(xmlt)
        finally:
            pyxb.RequireValidWhenParsing(True)
        self.assertEqual('General Delivery', po2.shipTo.street)
        self.assertTrue(po2.billTo is None)

if __name__ == '__main__':
    unittest.main()
