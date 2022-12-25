# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

from pyxb.exceptions_ import *

import unittest

class TestIssue0043 (unittest.TestCase):
    def testFloat (self):
        self.assertEqual('INF', xs.float('Infinity').xsdLiteral())
        self.assertEqual('-INF', xs.float('-Infinity').xsdLiteral())
        self.assertEqual('NaN', xs.float('nan').xsdLiteral())

    def testDouble (self):
        self.assertEqual('INF', xs.double('Infinity').xsdLiteral())
        self.assertEqual('-INF', xs.double('-Infinity').xsdLiteral())
        self.assertEqual('NaN', xs.double('nan').xsdLiteral())

if __name__ == '__main__':
    unittest.main()
