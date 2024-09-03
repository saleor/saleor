# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import common

class Test (unittest.TestCase):
    def testBase (self):
        b = common.base('hi')
        self.assertEqual(b.bstr, 'hi')

    def testNamespaceInfo (self):
        ns = common.Namespace
        ns.validateComponentModel()
        self.assertEqual(0, len(ns.moduleRecords()))

if '__main__' == __name__:
    unittest.main()
