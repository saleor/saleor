# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.utils import unicode, xmlre
import re

import unittest

class TestXMLRE (unittest.TestCase):
    def assertMatches(self, xml_pattern, value):
        '''Helper function to assert a value matches an XSD regexp pattern.'''
        py_pattern = xmlre.XMLToPython(xml_pattern)
        compiled = re.compile(py_pattern)
        mo = compiled.match(value)
        self.assertTrue(mo is not None, 'XML re %r Python %r should match %r' % (xml_pattern, py_pattern, value))

    def assertNoMatch(self, xml_pattern, value):
        '''Helper function to assert a value does not matche an XSD regexp
        pattern.'''
        py_pattern = xmlre.XMLToPython(xml_pattern)
        compiled = re.compile(py_pattern)
        mo = compiled.match(value)
        self.assertTrue(mo is None, 'XML re %r Python %r should not match %r' % (xml_pattern, py_pattern, value))

    def testRangeErrors (self):
        self.assertTrue(xmlre.MaybeMatchCharacterClass('', 1) is None)

    def testWildcardEscape (self):
        (charset, position) = xmlre.MaybeMatchCharacterClass('.', 0)
        self.assertEqual(charset, unicode.WildcardEsc)
        self.assertEqual(position, 1)

    def testSingleCharEscapes (self):
        # 17 chars recognized as escapes
        self.assertEqual(len(unicode.SingleCharEsc), 17)

        (charset, position) = xmlre.MaybeMatchCharacterClass(r'\t', 0)
        self.assertEqual(charset.asTuples(), [ (9, 9) ])
        self.assertEqual(2, position)

        (charset, position) = xmlre.MaybeMatchCharacterClass(r'\?', 0)
        self.assertEqual(charset.asTuples(), [ (ord('?'), ord('?')) ])
        self.assertEqual(2, position)

        (charset, position) = xmlre.MaybeMatchCharacterClass(r'\\', 0)
        self.assertEqual(charset.asTuples(), [ (ord('\\'), ord('\\')) ])
        self.assertEqual(2, position)

    def testMultiCharEscapes (self):
        # 5*2 chars recognized as escapes
        self.assertEqual(len(unicode.MultiCharEsc), 10)
        (charset, position) = xmlre.MaybeMatchCharacterClass(r'\s', 0)
        self.assertEqual(charset.asTuples(), [ (9, 10), (13, 13), (32, 32) ])
        self.assertEqual(2, position)

    def testMatchCharProperty (self):
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, "\pL", 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, "\p{L", 0)
        text = "\p{L}"
        (charset, position) = xmlre._MatchCharClassEsc(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['L'])
        text = "\p{IsCyrillic}"
        (charset, position) = xmlre._MatchCharClassEsc(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.BlockMap['Cyrillic'])

    def testCharProperty (self):
        text = r'\p{D}'
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, text, 0)
        text = r'\P{D}'
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, text, 0)
        text = r'\p{N}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['N'])
        text = r'\P{N}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), unicode.PropertyMap['N'])
        text = r'\p{Sm}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['Sm'])

    def testCharBlock (self):
        text = r'\p{IsArrows}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.BlockMap['Arrows'])
        text = r'\P{IsArrows}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), unicode.BlockMap['Arrows'])

        text = r'\p{IsWelsh}'
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, text, 0)
        text = r'\P{IsWelsh}'
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, text, 0)

    def testCharGroup (self):
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, '[]', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, '[A--]', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, '[A--]', 0)
        text = r'[A-Z]'
        #(charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        #self.assertEqual(position, len(text))
        #self.assertEqual(charset, unicode.CodePointSet((ord('A'), ord('Z'))))

    def testCharOrSCE (self):
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, '[', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, ']', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, '-', 0)
        (charset, position) = xmlre._MatchCharClassEsc(r'\t', 0)
        self.assertEqual(2, position)
        self.assertEqual(unicode.CodePointSet("\t"), charset)

    def testMatchPosCharGroup (self):
        text = 'A]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 1)
        self.assertEqual(charset, unicode.CodePointSet(ord('A')))
        text = r'\n]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 2)
        self.assertEqual(charset, unicode.CodePointSet(10))
        text = r'-]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 1)
        self.assertEqual(charset, unicode.CodePointSet(ord('-')))
        text = 'A-Z]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 3)
        self.assertEqual(charset, unicode.CodePointSet((ord('A'), ord('Z'))))
        text = r'\t-\r]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 5)
        self.assertEqual(charset, unicode.CodePointSet((9, 13)))
        text = r'\t-A]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 4)
        self.assertEqual(charset, unicode.CodePointSet((9, ord('A'))))
        text = r'Z-\]]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 4)
        self.assertEqual(charset, unicode.CodePointSet((ord('Z'), ord(']'))))
        text = 'Z-A]'
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchPosCharGroup, text, 0)

    def testMatchCharClassExpr (self):
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassExpr, 'missing open', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassExpr, '[missing close', 0)
        first_five = unicode.CodePointSet( (ord('A'), ord('E')) )
        text = r'[ABCDE]'
        (charset, position) = xmlre._MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, first_five)
        text = r'[^ABCDE]'
        (charset, position) = xmlre._MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), first_five)
        text = r'[A-Z-[GHI]]'
        expected = unicode.CodePointSet( (ord('A'), ord('Z')) )
        expected.subtract( (ord('G'), ord('I') ))
        (charset, position) = xmlre._MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, expected)
        text = r'[\p{L}-\p{Lo}]'
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassExpr, text, 0)
        text = r'[\p{L}-[\p{Lo}]]'
        (charset, position) = xmlre._MatchCharClassExpr(text, 0)
        expected = unicode.CodePointSet(unicode.PropertyMap['L'])
        expected.subtract(unicode.PropertyMap['Lo'])
        self.assertEqual(position, len(text))
        self.assertEqual(charset, expected)

    def testXMLToPython (self):
        self.assertEqual(r'^123$', xmlre.XMLToPython('123'))
        # Note that single-char escapes in the expression are
        # converted to character classes.
        self.assertEqual(r'^Why[ ]not[?]$', xmlre.XMLToPython(r'Why[ ]not\?'))

    def testRegularExpressions (self):
        text = '[\i-[:]][\c-[:]]*'
        compiled_re = re.compile(xmlre.XMLToPython(text))
        self.assertTrue(compiled_re.match('identifier'))
        self.assertFalse(compiled_re.match('0bad'))
        self.assertFalse(compiled_re.match(' spaceBad'))
        self.assertFalse(compiled_re.match('qname:bad'))
        text = '\\i\\c*'
        text_py = xmlre.XMLToPython(text)
        compiled_re = re.compile(text_py)
        self.assertTrue(compiled_re.match('identifier'))
        self.assertTrue(compiled_re.match('_underscore'))

    def testTrivialLiteral(self):
        # Simplest sanity check for assertMatches / assertNoMatch
        self.assertMatches("hello", "hello")
        self.assertNoMatch("hello", "hhello")
        self.assertNoMatch("hello", "helloo")
        self.assertNoMatch("hello", "goodbye")

    def testConvertingRangesToPythonWithDash(self):
        # It's really easy to convert this RE into "foo[&-X]bar", if
        # sorting characters in ASCII order without special-casing "-"
        self.assertNoMatch("foo[-&X]bar", "fooWbar")
        self.assertMatches("foo[-&X]bar", "foo-bar")
        self.assertMatches("foo[-&X]bar", "foo&bar")
        self.assertMatches("foo[-&X]bar", "fooXbar")

    def testConvertingRangesToPythonWithCaret(self):
        # It's really easy to convert this RE into "foo[^z]bar", if
        # sorting characters in ASCII order without special-casing "^"
        self.assertNoMatch("foo[z^]bar", "fooWbar")
        self.assertMatches("foo[z^]bar", "foozbar")
        self.assertMatches("foo[z^]bar", "foo^bar")

    def testConvertingRangesToPythonWithBackslash(self):
        # It's really easy to convert this RE into "foo[A\n]bar", if
        # you forget to special-case r"\"
        self.assertNoMatch("foo[A\\\\n]bar", "fooWbar")
        self.assertNoMatch("foo[A\\\\n]bar", "foo\nbar")
        self.assertMatches("foo[A\\\\n]bar", "fooAbar")
        self.assertMatches("foo[A\\\\n]bar", "foo\\bar")
        self.assertMatches("foo[A\\\\n]bar", "foonbar")

    def testCnUnicodeClass(self):
        # The Cn class is basically "everything that is not included in the
        # Unicode character database".  So it requires special handling when
        # you parse the Unicode character database.  It is really easy to
        # miss this and leave the Cn class empty.
        self.assertNoMatch("foo\\p{Cn}bar", "fooWbar")
        self.assertMatches("foo\\p{Cn}bar", "foo\ufffebar")
        self.assertMatches("foo\\P{Cn}bar", "fooWbar")
        self.assertNoMatch("foo\\P{Cn}bar", "foo\ufffebar")

    def testCnUnicodeClassInC(self):
        # If the Cn class is wrong (see above), then C will probably be wrong
        # too.
        self.assertNoMatch("foo\\p{C}bar", "fooWbar")
        self.assertMatches("foo\\p{C}bar", "foo\ufffebar")
        self.assertMatches("foo\\P{C}bar", "fooWbar")
        self.assertNoMatch("foo\\P{C}bar", "foo\ufffebar")

    def testMultiCharEscape_s(self):
        self.assertNoMatch("foo\\sbar", "fooWbar")
        self.assertMatches("foo\\sbar", "foo bar")

    def testMultiCharEscape_S(self):
        self.assertMatches("foo\\Sbar", "fooWbar")
        self.assertNoMatch("foo\\Sbar", "foo bar")

    def testMultiCharEscape_i(self):
        self.assertNoMatch("foo\\ibar", "foo bar")
        self.assertMatches("foo\\ibar", "fooWbar")
        self.assertMatches("foo\\ibar", "foo:bar")
        self.assertMatches("foo\\ibar", "foo_bar")
        self.assertMatches("foo\\ibar", "foo\u0D0Cbar")
        self.assertNoMatch("foo\\ibar", "foo-bar")
        self.assertNoMatch("foo\\ibar", "foo.bar")
        self.assertNoMatch("foo\\ibar", "foo\u203Fbar")
        self.assertNoMatch("foo\\ibar", "foo\u3005bar")

    def testMultiCharEscape_I(self):
        self.assertMatches("foo\\Ibar", "foo bar")
        self.assertNoMatch("foo\\Ibar", "fooWbar")
        self.assertNoMatch("foo\\Ibar", "foo:bar")
        self.assertNoMatch("foo\\Ibar", "foo_bar")
        self.assertNoMatch("foo\\Ibar", "foo\u0D0Cbar")
        self.assertMatches("foo\\Ibar", "foo-bar")
        self.assertMatches("foo\\Ibar", "foo.bar")
        self.assertMatches("foo\\Ibar", "foo\u203Fbar")
        self.assertMatches("foo\\Ibar", "foo\u3005bar")

    def testMultiCharEscape_c(self):
        self.assertNoMatch("foo\\cbar", "foo bar")
        self.assertMatches("foo\\cbar", "fooWbar")
        self.assertMatches("foo\\cbar", "foo:bar")
        self.assertMatches("foo\\cbar", "foo_bar")
        self.assertMatches("foo\\cbar", "foo\u0D0Cbar")
        self.assertMatches("foo\\cbar", "foo-bar")
        self.assertMatches("foo\\cbar", "foo.bar")
        self.assertNoMatch("foo\\cbar", "foo\u203Fbar")
        self.assertMatches("foo\\cbar", "foo\u3005bar")

    def testMultiCharEscape_C(self):
        self.assertMatches("foo\\Cbar", "foo bar")
        self.assertNoMatch("foo\\Cbar", "fooWbar")
        self.assertNoMatch("foo\\Cbar", "foo:bar")
        self.assertNoMatch("foo\\Cbar", "foo_bar")
        self.assertNoMatch("foo\\Cbar", "foo\u0D0Cbar")
        self.assertNoMatch("foo\\Cbar", "foo-bar")
        self.assertNoMatch("foo\\Cbar", "foo.bar")
        self.assertMatches("foo\\Cbar", "foo\u203Fbar")
        self.assertNoMatch("foo\\Cbar", "foo\u3005bar")

    def testMultiCharEscape_d(self):
        self.assertNoMatch("foo\\dbar", "foo bar")
        self.assertNoMatch("foo\\dbar", "foozbar")
        self.assertMatches("foo\\dbar", "foo5bar")
        self.assertMatches("foo\\dbar", "foo\u0669bar")

    def testMultiCharEscape_D(self):
        self.assertMatches("foo\\Dbar", "foo bar")
        self.assertMatches("foo\\Dbar", "foozbar")
        self.assertNoMatch("foo\\Dbar", "foo5bar")
        self.assertNoMatch("foo\\Dbar", "foo\u0669bar")

    def testMultiCharEscape_w(self):
        self.assertNoMatch("foo\\wbar", "foo bar")
        self.assertNoMatch("foo\\wbar", "foo&bar")
        self.assertMatches("foo\\wbar", "fooWbar")
        self.assertMatches("[\\w]*", "fooWboar")

    def testMultiCharEscape_W(self):
        self.assertMatches("foo\\Wbar", "foo bar")
        self.assertMatches("foo\\Wbar", "foo&bar")
        self.assertNoMatch("foo\\Wbar", "fooWbar")

    def testUnicodeClass(self):
        self.assertMatches("\\p{L}*", "hello")
        self.assertNoMatch("\\p{L}*", "hell7")

    def testQuotedOpenBrace(self):
        self.assertMatches("foo\\[bar", "foo[bar")
        self.assertNoMatch("foo\\[bar", "foo\\[bar")
        self.assertNoMatch("foo\\[bar", "foob")

    def testQuotedCloseBrace(self):
        self.assertMatches("foo\\]bar", "foo]bar")
        self.assertNoMatch("foo\\]bar", "foo\\]bar")
        self.assertNoMatch("foo\\]bar", "foob")

    def testQuotedAndUnquotedCloseBrace(self):
        self.assertMatches("foo[b\\]c]ar", "foobar")
        self.assertMatches("foo[b\\]c]ar", "foo]ar")
        self.assertMatches("foo[b\\]c]ar", "foocar")
        self.assertNoMatch("foo[b\\]c]ar", "fooar")

    def testUnquotedAndQuotedCloseBrace(self):
        self.assertMatches("foo[zb]c\\]ar", "foobc]ar")
        self.assertMatches("foo[zb]c\\]ar", "foozc]ar")
        self.assertNoMatch("foo[zb]c\\]ar", "foozar")

    def testQuotedOpenCloseBraces(self):
        self.assertMatches("foo\\[bar\\]", "foo[bar]")
        self.assertNoMatch("foo\\[bar\\]", "foo\\[bar]")
        self.assertNoMatch("foo\\[bar\\]", "foobar")

    def testQuotedAndUnquotedOpenBrace(self):
        self.assertMatches("foo\\[b[az]r", "foo[bar")
        self.assertMatches("foo\\[b[az]r", "foo[bzr")
        self.assertNoMatch("foo\\[b[az]r", "foobr")

    def testUnquotedAndQuotedOpenBrace(self):
        self.assertMatches("foo[b\\[az]r", "foobr")
        self.assertMatches("foo[b\\[az]r", "foo[r")
        self.assertNoMatch("foo[b\\[az]r", "foobar")

    def testFoo(self):
        self.assertMatches("foo\\\\[bc\\]a]r", "foo\\br")
        self.assertNoMatch("foo\\\\[bc\\]a]r", "foo\\bar")
        self.assertNoMatch("foo\\\\[bc\\]a]r", "foobar")

    def testDashStartRangeWithRange(self):
        # Spec says: The - character is a valid character range only at the
        # beginning or end of a positive character group.
        self.assertMatches("foo[-a-z]bar", "fooabar")
        self.assertMatches("foo[-a-z]bar", "foo-bar")
        self.assertMatches("foo[-a-z]bar", "foonbar")
        self.assertMatches("foo[-a-z]bar", "foozbar")
        self.assertNoMatch("foo[-a-z]bar", "fooWbar")

    def testDashStartRangeOneLetter(self):
        self.assertMatches("foo[-a]bar", "fooabar")
        self.assertMatches("foo[-a]bar", "foo-bar")
        self.assertNoMatch("foo[-a]bar", "fooWbar")

    def testDashStartRangeSeveralLetters(self):
        self.assertMatches("foo[-abc]bar", "fooabar")
        self.assertMatches("foo[-abc]bar", "foobbar")
        self.assertMatches("foo[-abc]bar", "foocbar")
        self.assertMatches("foo[-abc]bar", "foo-bar")
        self.assertNoMatch("foo[-abc]bar", "fooWbar")

    def testDashOnlyRange(self):
        self.assertMatches("foo[-]bar", "foo-bar")
        self.assertNoMatch("foo[-a-z]bar", "fooWbar")

    def testDashEndRange(self):
        self.assertMatches("foo[a-z-]bar", "fooabar")
        self.assertMatches("foo[a-z-]bar", "foo-bar")
        self.assertMatches("foo[a-z-]bar", "foonbar")
        self.assertMatches("foo[a-z-]bar", "foozbar")
        self.assertNoMatch("foo[a-z-]bar", "fooWbar")

    def testDashEndRangeOneLetter(self):
        self.assertMatches("foo[a-]bar", "fooabar")
        self.assertMatches("foo[a-]bar", "foo-bar")
        self.assertNoMatch("foo[a-]bar", "fooWbar")

    def testDashEndRangeSeveralLetters(self):
        self.assertMatches("foo[abc-]bar", "fooabar")
        self.assertMatches("foo[abc-]bar", "foobbar")
        self.assertMatches("foo[abc-]bar", "foocbar")
        self.assertMatches("foo[abc-]bar", "foo-bar")
        self.assertNoMatch("foo[abc-]bar", "fooWbar")

    def testDashEndRangeWithSub(self):
        self.assertMatches("foo[a-z--[q]]bar", "fooabar")
        self.assertMatches("foo[a-z--[q]]bar", "foo-bar")
        self.assertMatches("foo[a-z--[q]]bar", "foonbar")
        self.assertMatches("foo[a-z--[q]]bar", "foozbar")
        self.assertNoMatch("foo[a-z--[q]]bar", "fooWbar")
        self.assertNoMatch("foo[a-z--[q]]bar", "fooqbar")

    def testDashEndRangeOneLetterWithSub(self):
        self.assertMatches("foo[a--[q]]bar", "fooabar")
        self.assertMatches("foo[a--[q]]bar", "foo-bar")
        self.assertNoMatch("foo[a--[q]]bar", "fooWbar")

        self.assertMatches("foo[a--[a]]bar", "foo-bar")
        self.assertNoMatch("foo[a--[a]]bar", "fooabar")
        self.assertNoMatch("foo[a--[a]]bar", "fooWbar")

    def testDashEndRangeSeveralLettersWithSub(self):
        self.assertMatches("foo[abc--[b]]bar", "fooabar")
        self.assertMatches("foo[abc--[b]]bar", "foocbar")
        self.assertMatches("foo[abc--[b]]bar", "foo-bar")
        self.assertNoMatch("foo[abc--[b]]bar", "foobbar")
        self.assertNoMatch("foo[abc--[b]]bar", "fooWbar")

    def testCaret(self):
        self.assertMatches("foo^bar", "foo^bar")
        self.assertNoMatch("foo^bar", "foobar")
        self.assertNoMatch("foo^bar", "barfoo")

    def testCaretStart(self):
        self.assertMatches("^foobar", "^foobar")
        self.assertNoMatch("^foobar", "foobar")

    def testDollar(self):
        self.assertMatches("foo$bar", "foo$bar")
        self.assertNoMatch("foo$bar", "foobar")
        self.assertNoMatch("foo$bar", "barfoo")

    def testDollarEnd(self):
        self.assertMatches("foobar$", "foobar$")
        self.assertNoMatch("foobar$", "foobar")

    def testCaretInRangeSub(self):
        self.assertMatches("foo[a^-[a]]bar", "foo^bar")
        self.assertNoMatch("foo[a^-[a]]bar", "fooabar")
        self.assertNoMatch("foo[a^-[a]]bar", "foobar")

    def testCaretInRange(self):
        self.assertMatches("foo[a^]bar", "foo^bar")
        self.assertMatches("foo[a^]bar", "fooabar")
        self.assertNoMatch("foo[a^]bar", "foobar")

    def testSingleCharRange(self):
        self.assertMatches("foo[b]ar", "foobar")

    def testQuotedSingleChar(self):
        self.assertMatches("foo\\\\bar", "foo\\bar")

if __name__ == '__main__':
    unittest.main()
