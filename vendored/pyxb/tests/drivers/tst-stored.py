# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb

print("\n".join([ str(_ns) for _ns in pyxb.namespace.AvailableNamespaces() ]))
ns = pyxb.namespace.NamespaceForURI('URN:shared-types', True)
ns.validateComponentModel()
ns = pyxb.namespace.NamespaceForURI('URN:test-external', True)
ns.validateComponentModel()

import bindings.st as st
import bindings.te as te

import unittest

class ExternalTest (unittest.TestCase):
    def testUnionExtension (self):
        e = te.morewords('one')
        self.assertTrue(isinstance(e, st.english))
        self.assertTrue(te.uMorewords._IsValidValue(e))
        self.assertEqual(e, st.english.one)
        self.assertEqual(e, te.uMorewords.one)
        w = te.morewords('un')
        self.assertTrue(isinstance(w, st.welsh))
        self.assertTrue(te.uMorewords._IsValidValue(w))
        self.assertEqual(w, st.welsh.un)
        self.assertEqual(w, te.uMorewords.un)
        n = te.morewords('ichi')
        self.assertTrue(te.uMorewords._IsValidValue(n))
        self.assertEqual(n, te.uMorewords.ichi)

    def testValidation (self):
        self.assertEqual(st.Namespace.uri(), 'URN:shared-types')
        self.assertTrue(st.Namespace.validateComponentModel())
        self.assertEqual(te.Namespace.uri(), 'URN:test-external')
        self.assertTrue(te.Namespace.validateComponentModel())

if '__main__' == __name__:
    unittest.main()
