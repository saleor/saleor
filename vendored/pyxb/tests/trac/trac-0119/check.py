# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest

import base
import absent

import pyxb.utils.domutils
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(base.Namespace, 'base')

class TestTrac0119 (unittest.TestCase):

    def testRoundTrip (self):
        c = absent.doit('hi')
        m = base.Message(c)
        xmld = m.toxml("utf-8")
        # Cannot resolve absent namespace in base module
        self.assertRaises(pyxb.QNameResolutionError, base.CreateFromDocument, xmld)
        # Can resolve it in absent module
        instance = absent.CreateFromDocument(xmld)
        self.assertEqual(xmld, instance.toxml("utf-8"))

    def testNoDefault (self):
        xmlt='''<?xml version="1.0"?>
<base:Message xmlns:base="urn:trac0119" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <command xsi:type="doit">
    <payload>hi</payload>
  </command>
</base:Message>
'''
        # Cannot resolve absent namespace in base module
        self.assertRaises(pyxb.QNameResolutionError, base.CreateFromDocument, xmlt)
        # Can resolve it in absent module
        instance = absent.CreateFromDocument(xmlt)
        self.assertEqual('hi', instance.command.payload)
        # Can resolve in base module if fallback namespace overridden
        instance = base.CreateFromDocument(xmlt, default_namespace=absent.Namespace)
        self.assertEqual('hi', instance.command.payload)

    def testDefault (self):
        xmlt='''<?xml version="1.0"?>
<Message xmlns="urn:trac0119" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <command xmlns="" xsi:type="doit"> <!-- undefine the default namespace -->
    <payload>hi</payload>
  </command>
</Message>
'''
        # Cannot resolve absent namespace in base module
        self.assertRaises(pyxb.QNameResolutionError, base.CreateFromDocument, xmlt)
        # Can resolve it in absent module
        instance = absent.CreateFromDocument(xmlt)
        self.assertEqual('hi', instance.command.payload)
        # Can resolve in base module if fallback namespace overridden
        instance = base.CreateFromDocument(xmlt, default_namespace=absent.Namespace)
        self.assertEqual('hi', instance.command.payload)

    def testUndefineNondefault (self):
        xmlt='''<?xml version="1.0"?>
<base:Message xmlns:base="urn:trac0119" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <command xsi:type="doit" xmlns:base=""> <!-- undefine the base namespace -->
    <payload>hi</payload>
  </command>
</base:Message>
'''
        # Cannot undefine a prefix in SAX.
        import xml.sax
        self.assertRaises(xml.sax.SAXParseException, base.CreateFromDocument, xmlt)
        self.assertRaises(xml.sax.SAXParseException, absent.CreateFromDocument, xmlt)
        self.assertRaises(xml.sax.SAXParseException, base.CreateFromDocument, xmlt, default_namespace=absent.Namespace)

if __name__ == '__main__':
    unittest.main()
