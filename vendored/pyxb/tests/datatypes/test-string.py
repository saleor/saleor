# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb.binding.datatypes as xsd

class Test_string (unittest.TestCase):
    def testRange (self):
        # Not really anything to test here.
        pass

if __name__ == '__main__':
    unittest.main()
