# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
import pyxb.binding.datatypes as xs

from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/enumerations.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestEnumerations (unittest.TestCase):
    def testString (self):
        self.assertRaises(pyxb.SimpleTypeValueError, eString, 'fourteen')
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDocument, '<eString>fourteen</eString>')
        self.assertEqual('one', eString('one'))
        self.assertEqual('one', CreateFromDocument('<eString>one</eString>'))
        self.assertEqual(eString.typeDefinition().one, 'one')

    def testInteger (self):
        self.assertTrue(issubclass(tInteger, xs.int))
        self.assertRaises(pyxb.SimpleTypeValueError, eInteger, 4)
        self.assertRaises(pyxb.SimpleTypeValueError, eInteger, '4')
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDocument, '<eInteger>4</eInteger>')
        self.assertRaises(pyxb.SimpleTypeValueError, eInteger) # Value defaults to zero, not in enumeration
        self.assertEqual(3, eInteger(3))
        self.assertEqual(3, CreateFromDocument('<eInteger>3</eInteger>'))
        self.assertEqual(21, eInteger(21))
        self.assertEqual(21, CreateFromDocument('<eInteger>21</eInteger>'))

    def testDouble (self):
        self.assertTrue(issubclass(tDouble, xs.double))
        self.assertRaises(pyxb.SimpleTypeValueError, eDouble, 2)
        self.assertRaises(pyxb.SimpleTypeValueError, eDouble, 2.0)
        self.assertRaises(pyxb.SimpleTypeValueError, eDouble, '2')
        self.assertRaises(pyxb.SimpleTypeValueError, eDouble, '2.0')
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDocument, '<eDouble>2</eDouble>')
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDocument, '<eDouble>2.0</eDouble>')
        self.assertRaises(pyxb.SimpleTypeValueError, eDouble) # Value defaults to zero, not in enumeration
        self.assertEqual(1.0, eDouble(1.0))
        self.assertEqual(1.0, CreateFromDocument('<eDouble>1</eDouble>'))
        self.assertEqual(1.0, CreateFromDocument('<eDouble>1.0</eDouble>'))
        self.assertEqual(1.5, eDouble(1.5))
        self.assertEqual(1.5, CreateFromDocument('<eDouble>1.5</eDouble>'))
        self.assertEqual(1.7, eDouble(1.7))
        self.assertEqual(1.7, CreateFromDocument('<eDouble>1.7</eDouble>'))

    def testAny (self):
        self.assertTrue(issubclass(tAny, xs.string))
        self.assertRaises(pyxb.SimpleTypeValueError, eAny, 2)
        self.assertRaises(pyxb.SimpleTypeValueError, eAny, '2')
        self.assertRaises(pyxb.SimpleTypeValueError, CreateFromDocument, '<eAny>2</eAny>')
        self.assertEqual('one', eAny('one'))
        self.assertEqual('one', CreateFromDocument('<eAny>one</eAny>'))
        self.assertEqual(eAny.typeDefinition().one, eAny('one'))
        self.assertEqual('1', eAny('1'))
        self.assertEqual(eAny.typeDefinition().n1, eAny('1'))
        self.assertEqual('1.0', eAny('1.0'))
        self.assertEqual(eAny.typeDefinition().n1_0, eAny('1.0'))

    def testList (self):
        self.assertEqual([1, 1, 2, 3], justList('1 1 2 3'))
        self.assertEqual([1, 1, 2, 3], eListInt('1 1 2 3'))
        self.assertEqual([1, 1, 2, 3], eListInt((1,1,2,3)))
        self.assertEqual([1, 1, 2, 3], CreateFromDocument('<eListInt>1 1 2 3</eListInt>'))
        # NB Constraining value space, not lexical space, so whiteSpace facets apply
        self.assertEqual([1, 1, 2, 3], eListInt('1   1      2 3'))
        self.assertEqual([1, 1, 2, 3], CreateFromDocument('<eListInt>1    1       2 3</eListInt>'))
        self.assertRaises(pyxb.SimpleTypeValueError, eListInt, '1 2 3')
        self.assertRaises(pyxb.SimpleTypeValueError, eListInt, (1,2,3))

    def testListRestriction (self):
        self.assertTrue(9, len(justList([2] * 9)))
        self.assertTrue(10, len(justList([2] * 10)))
        self.assertRaises(pyxb.SimpleTypeValueError, justList, [2] * 11)

    def testJustUnion (self):
        self.assertEqual(uVarious.one, eJustVarious('one'))
        self.assertEqual(uVarious.two, eJustVarious('two'))
        v = eJustVarious(1.0)
        self.assertTrue(isinstance(v, float)) # make sure no implicit cast
        self.assertEqual(1.0, v)
        self.assertEqual([1,1,2,3,5,8], eJustVarious((1,1,2,3,5,8)))
        self.assertEqual([1,1,2,3,5,8], CreateFromDocument('<eJustVarious>1 1 2 3 5 8</eJustVarious>'))
        self.assertRaises(pyxb.SimpleTypeValueError, eJustVarious, (1,2,3,5,8))

    def testUnion (self):
        self.assertEqual(tVarious.one, eVarious('one'))
        self.assertRaises(pyxb.SimpleTypeValueError, eVarious, 'two')
        self.assertEqual(1.0, eVarious(1.0))
        self.assertEqual(1.0, eVarious('1.0'))
        v = eVarious('1')
        self.assertTrue(isinstance(v, float))
        v = eVarious(1.0)
        self.assertTrue(isinstance(v, float))
        v = eVarious(1)
        self.assertTrue(isinstance(v, float))
        self.assertEqual(1.0, eVarious('1')) # this is a valid float as well as int
        self.assertRaises(pyxb.SimpleTypeValueError, eVarious, '1.6')
        self.assertEqual([1,1,2,3], eVarious((1,1,2,3)))
        self.assertRaises(pyxb.SimpleTypeValueError, eVarious, (1,1,2,3,5,8))


if __name__ == '__main__':
    unittest.main()
