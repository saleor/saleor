# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import A
import B

class Trac43_1 (unittest.TestCase):

    def testCode (self):

        x = A.a2('a2m-value', 'legal')
        self.assertEqual('a2m-value', x.a2member)
        self.assertEqual(B.bst.legal, x.a2b)

        myobj = B.b1(x, 'legal')
        self.assertEqual(myobj.a2elt, x)

        x2 = A.a2('anotherValue', 'legal')
        myobj.a2elt = x2
        self.assertEqual('anotherValue', myobj.a2elt.a2member)
        self.assertEqual(B.bst.legal, myobj.a2elt.a2b)

unittest.main()
