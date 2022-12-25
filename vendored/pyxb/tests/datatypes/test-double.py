# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb.binding.datatypes as xsd

class Test_double (unittest.TestCase):
    def testRange (self):
        # Not going to do anything for this
        pass

if __name__ == '__main__':
    unittest.main()
