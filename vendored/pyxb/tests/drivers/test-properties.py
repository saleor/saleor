# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node

import pyxb.binding.basis

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/alt-po1.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils

def ToDOM (instance, dom_support=None):
    return instance.toDOM(dom_support).documentElement

import unittest

class TestProperties (unittest.TestCase):

    street_content = '''95 Main St.
Anytown, AS  12345-6789'''
    street_xmlt = six.u('<street>%s</street>') % (street_content,)
    street_xmld = street_xmlt.encode('utf-8')
    street_dom = pyxb.utils.domutils.StringToDOM(street_xmlt).documentElement

    address1_xmlt = six.u('<name>Customer</name><street>95 Main St</street>')
    address2_xmlt = six.u('<name>Sugar Mama</name><street>24 E. Dearling Ave.</street>')

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
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        addr2 = USAddress.Factory(_dom_node=dom.documentElement)

    def testPurchaseOrder (self):
        po = purchaseOrder(shipTo=USAddress(name='Customer', street='95 Main St'),
                           billTo=USAddress(name='Sugar Mama', street='24 E. Dearling Ave'),
                           comment='Thanks!')
        xmld = ToDOM(po).toxml("utf-8")
        xml1t = '<ns1:purchaseOrder xmlns:ns1="http://www.example.com/altPO1"><shipTo><name>Customer</name><street>95 Main St</street></shipTo><billTo><name>Sugar Mama</name><street>24 E. Dearling Ave</street></billTo><ns1:comment>Thanks!</ns1:comment></ns1:purchaseOrder>'
        xml1d = xml1t.encode('utf-8')
        self.assertEqual(xmld, xml1d)

        dom = pyxb.utils.domutils.StringToDOM(xml1t)
        po2 = purchaseOrder.createFromDOM(dom.documentElement)
        self.assertEqual(ToDOM(po2).toxml("utf-8"), xml1d)

        xml2t = '<purchaseOrder xmlns="http://www.example.com/altPO1"><shipTo><name>Customer</name><street>95 Main St</street></shipTo><billTo><name>Sugar Mama</name><street>24 E. Dearling Ave</street></billTo><comment>Thanks!</comment></purchaseOrder>'
        xml2d = xml2t.encode('utf-8')
        bds = pyxb.utils.domutils.BindingDOMSupport()
        bds.setDefaultNamespace(Namespace)
        self.assertEqual(ToDOM(po2, dom_support=bds).toxml("utf-8"), xml2d)

if __name__ == '__main__':
    unittest.main()
