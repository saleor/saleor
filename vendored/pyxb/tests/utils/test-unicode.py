# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
from pyxb.utils.unicode import *

class TestCodePointSet (unittest.TestCase):
    def testConstructor (self):
        c = CodePointSet()
        self.assertEqual(c.asTuples(), [])
        c = CodePointSet(10, 15)
        self.assertEqual(c.asTuples(), [ (10, 10), (15, 15) ])
        c = CodePointSet([10, 15])
        self.assertEqual(c.asTuples(), [ (10, 10), (15, 15) ])

    def testCopyConstructor (self):
        c = CodePointSet()
        c.add(10)
        c.add(15)
        self.assertEqual(c.asTuples(), [ (10, 10), (15, 15) ])
        c2 = CodePointSet(c)
        self.assertEqual(c2.asTuples(), [ (10, 10), (15, 15) ])
        c.add(20)
        self.assertEqual(c.asTuples(), [ (10, 10), (15, 15), (20, 20) ])
        self.assertEqual(c2.asTuples(), [ (10, 10), (15, 15) ])

    def testNegate (self):
        c = CodePointSet().negate()
        self.assertEqual(c.asTuples(), [ (0, CodePointSet.MaxCodePoint) ])
        c2 = c.negate()
        self.assertEqual(c2.asTuples(), [])

    def testAddSingle (self):
        c = CodePointSet()
        c.add(15)
        self.assertEqual(c.asTuples(), [ (15, 15) ])
        c.add(15)
        self.assertEqual(c.asTuples(), [ (15, 15) ])

        c.add(0)
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15) ])
        n = c.negate()
        self.assertEqual(n.asTuples(), [ (1, 14), (16, CodePointSet.MaxCodePoint) ])

        n.add(0)
        self.assertEqual(n.asTuples(), [ (0, 14), (16, CodePointSet.MaxCodePoint) ])
        n.add(15)
        self.assertEqual(n.asTuples(), [ (0, CodePointSet.MaxCodePoint) ])

        c = CodePointSet()
        c.add(':')
        self.assertEqual(c.asTuples(), [ (58, 58) ])

    def testRemoveRange (self):
        base = CodePointSet(0, 15, (20, 30), (40, 60))
        self.assertEqual(base.asTuples(), [ (0, 0), (15, 15), (20, 30), (40, 60) ])
        # 0 1 15 16 20 31 40 61
        c = CodePointSet(base).subtract( (22, 25) )
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 21), (26, 30), (40, 60) ])
        c = CodePointSet(base).subtract( (22, 35) )
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 21), (40, 60) ])
        c = CodePointSet(base).subtract( (35, 55) )
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (56, 60) ])
        c = CodePointSet(base).subtract( (35, 38) )
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (40, 60) ])

    def testAddRange (self):
        base = CodePointSet(0, 15)
        self.assertEqual(base.asTuples(), [ (0, 0), (15, 15) ])
        base.add((20, 30))
        self.assertEqual(base.asTuples(), [ (0, 0), (15, 15), (20, 30) ])
        base.add((40, 60))
        self.assertEqual(base.asTuples(), [ (0, 0), (15, 15), (20, 30), (40, 60) ])
        # 0 1 15 16 20 31 40 61
        # Bridge missing range
        c = CodePointSet(base).add((1, 15))
        self.assertEqual(c.asTuples(), [ (0, 15), (20, 30), (40, 60) ])

        # Insert in middle of missing range
        c = CodePointSet(base).add((35, 38))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (35, 38), (40, 60) ])
        # Join following range
        c = CodePointSet(base).add((35, 39))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (35, 60) ])
        c = CodePointSet(base).add((35, 40))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (35, 60) ])

        # 0 1 15 16 20 31 40 61
        # Insert into middle of existing range
        c = CodePointSet(base).add((22, 25))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (40, 60) ])
        # Extend existing range
        c = CodePointSet(base).add((22, 35))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 35), (40, 60) ])
        c = CodePointSet(base).add((22, 38))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 38), (40, 60) ])
        # Span missing range
        c = CodePointSet(base).add((22, 39))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 60) ])
        c = CodePointSet(base).add((22, 40))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 60) ])
        c = CodePointSet(base).add((22, 41))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 60) ])

        # 0 1 15 16 20 31 40 61
        c = CodePointSet(base).add((15, 18))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 18), (20, 30), (40, 60) ])
        c = CodePointSet(base).add((35, 65))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (35, 65) ])
        c = CodePointSet(base).add((12, 16))
        self.assertEqual(c.asTuples(), [ (0, 0), (12, 16), (20, 30), (40, 60) ])

    def testAsPattern (self):
        c = CodePointSet()
        self.assertEqual('[]', c.asPattern())
        c.add(':')
        self.assertEqual('[\u003A]', c.asPattern())

        n = c.negate()
        if SupportsWideUnicode:
            self.assertEqual('[\\x00-\u0039\u003B-\U0010FFFF]', n.asPattern())
        else:
            self.assertEqual('[\\x00-\u0039\u003B-\uFFFF]', n.asPattern())

        c = CodePointSet()
        c.add(']')
        self.assertEqual('[\]]', c.asPattern())
        c = CodePointSet()
        c.add('-')
        c.add('+')
        self.assertEqual('[+\-]', c.asPattern())


    def testAsSingleCharacter (self):
        c = CodePointSet()
        self.assertTrue(c.asSingleCharacter() is None)
        c.add('A')
        self.assertEqual('A', c.asSingleCharacter())
        c.add('B')
        self.assertTrue(c.asSingleCharacter() is None)
        self.assertEqual('G', CodePointSet('G').asSingleCharacter())
        self.assertEqual('\u0041', CodePointSet(65).asSingleCharacter())
        self.assertEqual('\uFFFF', CodePointSet(0xFFFF).asSingleCharacter())

class TestXML1p0e2 (unittest.TestCase):
    def testChar (self):
        if SupportsWideUnicode:
            self.assertTrue(( 1+CodePointSet.MaxShortCodePoint, CodePointSet.MaxCodePoint ) in XML1p0e2.Char.asTuples())

if '__main__' == __name__:
    unittest.main()
