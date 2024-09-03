# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb.binding.basis
from pyxb.utils import six

class TestReserved (unittest.TestCase):
    def testSTD (self):
        tSTD = pyxb.binding.basis.simpleTypeDefinition
        for k in six.iterkeys(tSTD.__dict__):
            if not k.startswith('_'):
                self.assertTrue(k in tSTD._ReservedSymbols, k)

    def testCTD (self):
        tCTD = pyxb.binding.basis.complexTypeDefinition
        for k in six.iterkeys(tCTD.__dict__):
            if not k.startswith('_'):
                self.assertTrue(k in tCTD._ReservedSymbols, k)

if '__main__' == __name__:
    unittest.main()
