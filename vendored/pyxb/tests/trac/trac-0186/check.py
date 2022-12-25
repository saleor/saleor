# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.utils.domutils

import resources

import unittest

class ExternalTrac0186 (unittest.TestCase):
    def testXBIngress (self):
        instance = resources.XBIngress(match='all', action1='none', digits1='', action2='none', digits2='')

    def testXBMatch (self):
        instance = resources.XBMatch('all')

if '__main__' == __name__:
    unittest.main()
