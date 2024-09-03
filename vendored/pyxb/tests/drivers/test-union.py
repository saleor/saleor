# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-union.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
#open('code.py', 'w').write(code)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestUnion (unittest.TestCase):
    def test (self):
        self.assertRaises(LogicError, myUnion, 5)
        self.assertEqual(5, myUnion.Factory(5))
        self.assertEqual(5, myUnion.Factory('5'))
        self.assertRaises(SimpleTypeValueError, myUnion.Factory, 10)
        self.assertTrue(isinstance(myUnion.Factory('5'), singleDigit))
        self.assertTrue(isinstance(myUnion.Factory('one'), english))
        self.assertEqual(welsh.un, myUnion.Factory('un'))
        self.assertTrue(isinstance(myUnion.Factory('un'), welsh))
        self.assertEqual(english.one, myUnion.Factory('one'))
        self.assertRaises(LogicError, myUnion, 'five')

    def testList (self):
        my_list = unionList([ myUnion.Factory(4), myUnion.Factory('one')])
        self.assertEqual(2, len(my_list))

    def testRestrictedUnion (self):
        self.assertEqual(ones.one, ones.Factory('one'))
        self.assertRaises(SimpleTypeValueError, ones.Factory, 'two')
        self.assertEqual(ones.un, ones.Factory('un'))

    def testAnonymousUnion (self):
        self.assertEqual('four', words2.Factory('four'))
        self.assertEqual('pump', words2.Factory('pump'))
        self.assertRaises(SimpleTypeValueError,  words2.Factory, 'one')

    def testFiveWords (self):
        self.assertEqual('one', fiveWords.Factory('one'))
        self.assertEqual('dau', fiveWords.Factory('dau'))
        self.assertEqual('four', fiveWords.Factory('four'))
        self.assertEqual('pump', fiveWords.Factory('pump'))

    def testMyElement (self):
        self.assertEqual(0, myElement('0'))
        self.assertEqual(english.two, myElement('two'))
        self.assertEqual(welsh.tri, myElement('tri'))
        self.assertRaises(SimpleTypeValueError, myElement, 'five')

    def testValidation (self):
        # Test automated conversion
        uv = myUnion._ValidatedMember('one')
        self.assertTrue(isinstance(uv, english))
        uv = myUnion._ValidatedMember('tri')
        self.assertTrue(isinstance(uv, welsh))

    def testXsdLiteral (self):
        ul = unionList([0, 'un', 'one'])
        self.assertEqual('0 un one', ul.xsdLiteral())

    def testXMLErrors (self):
        self.assertEqual(welsh.un, CreateFromDocument('<myElement xmlns="URN:unionTest">un</myElement>'))
        self.assertRaises(UnrecognizedDOMRootNodeError, CreateFromDocument, '<welsh>un</welsh>')
        self.assertRaises(UnrecognizedDOMRootNodeError, CreateFromDocument, '<myelement>un</myelement>')

    def testMyElementDOM (self):
        self.assertEqual(0, myElement.createFromDOM(pyxb.utils.domutils.StringToDOM('<myElement xmlns="URN:unionTest">0</myElement>').documentElement))
        self.assertEqual(0, CreateFromDocument('<myElement xmlns="URN:unionTest">0</myElement>'))

        self.assertEqual(english.one, myElement.createFromDOM(pyxb.utils.domutils.StringToDOM('<myElement xmlns="URN:unionTest">one</myElement>').documentElement))
        self.assertEqual(welsh.un, myElement.createFromDOM(pyxb.utils.domutils.StringToDOM('<myElement xmlns="URN:unionTest">un</myElement>').documentElement))

        self.assertEqual(english.one, myElement.createFromDOM(pyxb.utils.domutils.StringToDOM('<myElement xmlns="URN:unionTest">one<!-- with comment --></myElement>').documentElement))
        self.assertEqual(welsh.un, myElement.createFromDOM(pyxb.utils.domutils.StringToDOM('<myElement xmlns="URN:unionTest"><!-- with comment -->un</myElement>').documentElement))

        self.assertEqual(english.one, myElement.createFromDOM(pyxb.utils.domutils.StringToDOM('<myElement xmlns="URN:unionTest"> one <!-- with comment and whitespace --></myElement>').documentElement))
        self.assertRaises(SimpleTypeValueError, myElement.createFromDOM, pyxb.utils.domutils.StringToDOM('<myElement xmlns="URN:unionTest"><!-- whitespace is error for welsh --> un</myElement>').documentElement)

        self.assertEqual(english.one, myElement.createFromDOM(pyxb.utils.domutils.StringToDOM('''<myElement xmlns="URN:unionTest"><!-- whitespace is collapsed for english -->
one
</myElement>''').documentElement))
        self.assertRaises(SimpleTypeValueError, myElement.createFromDOM, pyxb.utils.domutils.StringToDOM('''<myElement xmlns="URN:unionTest"><!--whitespace is only reduced for welsh -->
un
</myElement>''').documentElement)

if __name__ == '__main__':
    unittest.main()
