# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
from pyxb.utils.templates import *

_dictionary = { 'one' : 'un'
              , 'two' : 'dau'
              , 'three' : 'tri'
              , 'un' : 1
              , 'dau': 2
              , 'tri': 3
              , 'empty': ''
              , 'defined': 'value'
              }

class IfDefinedPatternTestCase (unittest.TestCase):
    dictionary = _dictionary

    def testNoSubst (self):
        self.assertEqual('un', replaceInText('%{?one?}', **self.dictionary))
        self.assertEqual('', replaceInText('%{?four?}', **self.dictionary))

    def testPlainSubst (self):
        self.assertEqual('one is defined', replaceInText('%{?one?+one is defined?}', **self.dictionary))
        self.assertEqual('', replaceInText('%{?four?+four is defined?}', **self.dictionary))
        self.assertEqual('four is not defined', replaceInText('%{?four?+@? is defined?-?@ is not defined?}', **self.dictionary))
        self.assertEqual('name', replaceInText('%{?context?+%{?@}.?}name'))
        self.assertEqual('name', replaceInText('%{?context?+%{?@}.?}name', context=None))
        self.assertEqual('owner.name', replaceInText('%{?context?+%{?@}.?}name', context='owner'))

    def testWithSubst (self):
        self.assertEqual('un and un are two', replaceInText('%{?one?+%{?@} and %{?@} are two?-what is ?@??}', **self.dictionary))
        self.assertEqual('what is "four"?', replaceInText('%{?four?+%{?@} and %{?@} are two?-what is "?@"??}', **self.dictionary))


class ConditionalPatternTestCase (unittest.TestCase):
    dictionary = _dictionary

    def testBasic (self):
        self.assertEqual('three is defined', replaceInText('%{?three??three is defined?:three is not defined?}', **self.dictionary))
        self.assertEqual("%{EXCEPTION: name 'four' is not defined}", replaceInText('%{?four??four is defined?:four is not defined?}', **self.dictionary))
        self.assertEqual('value', replaceInText('%{?defined??%{defined}?:pass?}', **self.dictionary))
        self.assertEqual('pass', replaceInText('%{?empty??%{empty}?:pass?}', **self.dictionary))

    def testHalfExpressions (self):
        self.assertEqual('value is three', replaceInText('%{?3 == un+dau??value is three?}', **self.dictionary))
        self.assertEqual('', replaceInText('%{?3 == un-dau??value is three?}', **self.dictionary))
        self.assertEqual('good 1 == un', replaceInText('%{?1 == un??good ?@?:bad ?@?}', **self.dictionary))
        self.assertEqual('bad 2 == un', replaceInText('%{?2 == un??good ?@?:bad ?@?}', **self.dictionary))
        self.assertEqual('''
        if runtime_test:
            print 'Good on 1 == un'
''', replaceInText('''
        %{?1 == un??if runtime_test:
            print 'Good on ?@'
?}''', **self.dictionary))

    def testExpressions (self):
        self.assertEqual('value is three', replaceInText('%{?3 == un+dau??value is three?:value is not three?}', **self.dictionary))
        self.assertEqual('value is not three', replaceInText('%{?3 == un-dau??value is three?:value is not three?}', **self.dictionary))

    def testNesting (self):
        self.assertEqual('tri', replaceInText('%{?3 == un+dau??%{three}?:not %{three}?}', **self.dictionary))

class IdPatternTestCase (unittest.TestCase):
    dictionary = _dictionary

    def testNoChange (self):
        cases = [ 'plain text'
                , '   leading whitespace'
                , 'trailing whitespace '
                , '''Multiline
text''' ] # '''
        for c in cases:
            self.assertEqual(c, replaceInText(c, **{}))

    def testSimpleSubstitution (self):
        self.assertEqual('un', replaceInText('%{one}', **self.dictionary))
        self.assertEqual('un and dau', replaceInText('%{one} and %{two}', **self.dictionary))
        self.assertEqual('''Line un
Line dau
Line tri
''', replaceInText('''Line %{one}
Line %{two}
Line %{three}
''', **self.dictionary))

    def testMissing (self):
        self.assertEqual('%{MISSING:four}', replaceInText('%{four}', **self.dictionary))

if __name__ == '__main__':
    #print replaceInText('%{?three%?three is defined%:three is not defined?}', ConditionalPatternTestCase.dictionary)
    #print "\n".join(_substConditionalPattern.match('%{?three%?three is defined%:three is not defined?}').groups())
    unittest.main()
