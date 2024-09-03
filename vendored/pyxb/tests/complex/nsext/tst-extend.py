# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import common4app
import common

class Test (unittest.TestCase):
    def testExtended (self):
        x = common4app.extended('hi', 'there')
        self.assertEqual(x.elt, 'hi')
        self.assertEqual(x.extElt, 'there')
        self.assertTrue(issubclass(common4app.extended.typeDefinition(), common.base.typeDefinition()))

    def testNamespaceInfo (self):
        ns = common.Namespace
        ns.validateComponentModel()
        self.assertEqual(0, len(ns.moduleRecords()))

if '__main__' == __name__:
    unittest.main()
