# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import unittest

class TestTrac0161 (unittest.TestCase):

    def testBasicGenerator (self):
        g = pyxb.binding.generate.Generator()
        args = g.getCommandLineArgs()

    def testPreloadPath (self):
        g = pyxb.binding.generate.Generator(pre_load_archives=['something.wxs'])
        args = g.getCommandLineArgs()

if __name__ == '__main__':
    unittest.main()
