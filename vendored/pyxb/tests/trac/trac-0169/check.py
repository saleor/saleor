# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest

import trac169

import pyxb.utils.domutils

class TestTrac0169 (unittest.TestCase):

    def testBasic (self):
        v = trac169.c(23)
        self.assertEqual(23, v)

if __name__ == '__main__':
    unittest.main()
