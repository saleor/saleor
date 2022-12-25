# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import B
from pyxb import BIND

class Trac43_2 (unittest.TestCase):

    def testCode (self):
        myobj = B.b1(BIND('a2m-value', 'legal'), 'legal')
        self.assertEqual('a2m-value', myobj.a2elt.a2member)
        self.assertEqual(B.bst.legal, myobj.a2elt.a2b)

        myobj.a2elt = BIND('anotherValue', 'legal')
        self.assertEqual('anotherValue', myobj.a2elt.a2member)
        self.assertEqual(B.bst.legal, myobj.a2elt.a2b)

unittest.main()
