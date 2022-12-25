# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb
import sample
from pyxb.namespace.builtin import XMLSchema_instance as xsi

class TestTrac0202 (unittest.TestCase):
    def tearDown (self):
        pyxb.utils.domutils.BindingDOMSupport.SetDefaultNamespace(sample.Namespace)

    Expectedt = """<?xml version="1.0" encoding="utf-8"?>
<samplerootelement xmlns="http://sample" xmlns:ns1="http://sample" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="c:\sample.xsd">
\t<sampleelement>
\t\t<ValueAmount ns1:currencyID="abc">100.0</ValueAmount>
\t</sampleelement>
</samplerootelement>
"""
    Expectedd = Expectedt.encode('utf-8')

    def testIssue (self):
        elm = sample.sampleelementType()
        elm.ValueAmount = '100'
        elm.ValueAmount.currencyID = 'abc'
        sam = sample.samplerootelement()
        sam.sampleelement.append(elm)
        bds = pyxb.utils.domutils.BindingDOMSupport()
        bds.setDefaultNamespace(sample.Namespace)
        bds.declareNamespace(xsi)
        samdom = sam.toDOM(bds)
        bds.addAttribute(samdom.documentElement, xsi.createExpandedName('schemaLocation'), "c:\sample.xsd")
        # xsi is probably not referenced elsewhere, so add the XMLNS declaration too
        bds.addXMLNSDeclaration(samdom.documentElement, xsi)
        xmld = samdom.toprettyxml(encoding = "utf-8")
        self.assertEqual(self.Expectedd, xmld)

if __name__ == '__main__':
    unittest.main()
