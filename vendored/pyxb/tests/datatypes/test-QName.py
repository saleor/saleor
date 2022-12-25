# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd
import pyxb.namespace
xsi = pyxb.namespace.XMLSchema_instance

class Test_QName (unittest.TestCase):
    def testValid (self):
        dns = pyxb.namespace.CreateAbsentNamespace()
        nsc = pyxb.namespace.NamespaceContext(target_namespace=dns)
        nsc.declareNamespace(xsi, 'xsi')

        self.assertEqual('schema', xsd.QName('schema', _xmlns_context=nsc))
        self.assertEqual('schema', xsd.QName('schema'))
        self.assertEqual(xsi.createExpandedName('something'), xsd.QName('xsi:something', _xmlns_context=nsc))
        with self.assertRaises(pyxb.QNameResolutionError) as cm:
            xsd.QName('xs:something', _xmlns_context=nsc)
        self.assertEqual('xs:something', cm.exception.qname)
        self.assertEqual(nsc, cm.exception.namespaceContext)
        with self.assertRaises(pyxb.QNameResolutionError) as cm:
            xsd.QName('xsi:something')
        self.assertEqual('xsi:something', cm.exception.qname)
        self.assertEqual(None, cm.exception.namespaceContext)
        self.assertEqual('with.dots', xsd.QName('with.dots', _xmlns_context=nsc))

    def testInvalid (self):
        invalid = [ '-NonName', '-also:-not', 'and:-not', 'too:many:colons', ' whitespace ' ]
        for f in invalid:
            try:
                xsd.QName(f)
                print('Unexpected pass with %s' % (f,))
            except:
                pass
            self.assertRaises(SimpleTypeValueError, xsd.QName, f)

if __name__ == '__main__':
    unittest.main()
