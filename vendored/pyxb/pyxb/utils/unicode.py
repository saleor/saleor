# -*- coding: utf-8 -*-
# Copyright 2009-2013, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""This module contains support for Unicode characters as required to
support the regular expression syntax defined in U{annex F
<http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#regexs>}
of the XML Schema definition.

In particular, we need to be able to identify character properties and
block escapes, as defined in F.1.1, by name.

 - Block data: U{http://www.unicode.org/Public/3.1-Update/Blocks-4.txt}
 - Property list data: U{http://www.unicode.org/Public/3.1-Update/PropList-3.1.0.txt}
 - Full dataset: U{http://www.unicode.org/Public/3.1-Update/UnicodeData-3.1.0.txt}

The Unicode database active at the time XML Schema 1.0 was defined is
archived at
U{http://www.unicode.org/Public/3.1-Update/UnicodeCharacterDatabase-3.1.0.html},
and refers to U{Unicode Standard Annex #27: Unicode 3.1
<http://www.unicode.org/unicode/reports/tr27/>}.
"""

import re
import logging
import pyxb.utils.utility
from pyxb.utils import six
from pyxb.utils.six.moves import xrange

_log = logging.getLogger(__name__)

SupportsWideUnicode = False
try:
    re.compile(six.u('[\U0001d7ce-\U0001d7ff]'))
    SupportsWideUnicode = True
except:
    pass

import bisect

class CodePointSetError (LookupError):
    """Raised when some abuse of a L{CodePointSet} is detected."""
    pass

@pyxb.utils.utility.BackfillComparisons
class CodePointSet (object):
    """Represent a set of Unicode code points.

    Each code point is an integral value between 0 and 0x10FFFF.  This
    class is used to represent a set of code points in a manner
    suitable for use as regular expression character sets."""

    MaxCodePoint = 0x10FFFF
    """The maximum value for a code point in the Unicode code point
    space.  This is normally 0xFFFF, because wide unicode characters
    are generally not enabled in Python builds.  If, however, they are
    enabled, this will be the full value of 0x10FFFF."""

    MaxShortCodePoint = 0xFFFF
    if not SupportsWideUnicode:
        MaxCodePoint = MaxShortCodePoint

    # The internal representation of the codepoints is as a sorted
    # list where values at an even index denote the first codepoint in
    # a range that is in the set, and the immediately following value
    # indicates the next following codepoint that is not in the set.
    # A missing value at the end is interpreted as MaxCodePoint.  For
    # example, the sequence [ 12, 15, 200 ] denotes the set containing
    # codepoints 12, 13, 14, and everything above 199.
    __codepoints = None

    def _codepoints (self):
        """For testing purrposes only, access to the codepoints
        internal representation."""
        return self.__codepoints

    def __hash__ (self):
        return hash(self.__codepoints)

    def __eq__ (self, other):
        """Equality is delegated to the codepoints list."""
        return self.__codepoints == other.__codepoints

    def __lt__ (self, other):
        return self.__codepoints < other.__codepoints

    def __init__ (self, *args):
        self.__codepoints = []
        if 1 == len(args):
            if isinstance(args[0], CodePointSet):
                self.__codepoints.extend(args[0].__codepoints)
                return
            if isinstance(args[0], list):
                args = args[0]
        for a in args:
            self.add(a)

    def __mutate (self, value, do_add):
        # Identify the start (inclusive) and end (exclusive) code
        # points of the value's range.
        if isinstance(value, tuple):
            (s, e) = value
            e += 1
        elif isinstance(value, six.string_types):
            if 1 < len(value):
                raise TypeError()
            s = ord(value)
            e = s+1
        else:
            s = int(value)
            e = s+1
        if s >= e:
            raise ValueError('codepoint range value order')

        # Validate the range for the code points supported by this
        # Python interpreter.  Recall that e is exclusive.
        if s > self.MaxCodePoint:
            return self
        if e > self.MaxCodePoint:
            e = self.MaxCodePoint+1

        # Index of first code point equal to or greater than s
        li = bisect.bisect_left(self.__codepoints, s)
        # Index of last code point less than or equal to e
        ri = bisect.bisect_right(self.__codepoints, e)
        # There are four cases; if we're subtracting, they reflect.
        case = ((li & 1) << 1) | (ri & 1)
        if not do_add:
            case = 3 - case
        if 0x03 == case:
            # Add: Incoming value begins and ends within existing ranges
            del self.__codepoints[li:ri]
        elif 0x02 == case:
            # Add: Incoming value extends into an excluded range
            del self.__codepoints[li+1:ri]
            self.__codepoints[li] = e
        elif 0x01 == case:
            # Add: Incoming value begins in an excluded range
            del self.__codepoints[li+1:ri]
            self.__codepoints[li] = s
        else:
            # Add: Incoming value begins and ends within excluded ranges
            self.__codepoints[li:ri] = [s, e]
        return self

    def add (self, value):
        """Add the given value to the code point set.

        @param value: An integral value denoting a code point, or a
        tuple C{(s,e)} denoting the start and end (inclusive) code
        points in a range.
        @return: C{self}"""
        return self.__mutate(value, True)

    def extend (self, values):
        """Add multiple values to a code point set.

        @param values: Either a L{CodePointSet} instance, or an iterable
        whose members are valid parameters to L{add}.

        @return: C{self}"""
        if isinstance(values, CodePointSet):
            self.extend(values.asTuples())
        else:
            for v in values:
                self.__mutate(v, True)
        return self

    def subtract (self, value):
        """Remove the given value from the code point set.

        @param value: An integral value denoting a code point, or a tuple
        C{(s,e)} denoting the start and end (inclusive) code points in a
        range, or a L{CodePointSet}.

        @return: C{self}"""
        if isinstance(value, CodePointSet):
            for v in value.asTuples():
                self.subtract(v)
            return self
        return self.__mutate(value, False)

    # Escape sequences for characters that must not appear unescaped in
    # Python regular expression patterns.  Maps each bad character to a safe
    # escape sequence.
    __XMLtoPythonREEscapedCodepoints = (
        # From docs for Python's "re" module: Regular expression
        # pattern strings may not contain null bytes
        0,
        # Indicates negation if it happens to occur at the start of a
        # character group
        ord('^'),
        # Escape character (backslash)
        ord('\\'),
        # Actually doesn't need to be escaped inside a Python
        # character group, but escaping it is less confusing.
        ord('['),
        # End of character group
        ord(']'),
        # Indicates a range of characters
        ord('-')
    )

    # Return the given code point as a unicode character suitable for
    # use in a regular expression
    def __unichr (self, code_point):
        rv = six.unichr(code_point)
        if 0 == code_point:
            rv = six.u('x00')
        if code_point in self.__XMLtoPythonREEscapedCodepoints:
            rv = six.unichr(0x5c) + rv
        return rv

    def asPattern (self, with_brackets=True):
        """Return the code point set as Unicode regular expression
        character group consisting of a sequence of characters or
        character ranges.

        This returns a regular expression fragment using Python's
        regular expression syntax.  Note that different regular expression
        syntaxes are not compatible, often in subtle ways.

        @param with_brackets: If C{True} (default), square brackets
        are added to enclose the returned character group."""
        rva = []
        if with_brackets:
            rva.append(six.u('['))
        for (s, e) in self.asTuples():
            if s == e:
                rva.append(self.__unichr(s))
            else:
                rva.extend([self.__unichr(s), '-', self.__unichr(e)])
        if with_brackets:
            rva.append(six.u(']'))
        return six.u('').join(rva)

    def asTuples (self):
        """Return the codepoints as tuples denoting the ranges that are in
        the set.

        Each tuple C{(s, e)} indicates that the code points from C{s}
        (inclusive) to C{e}) (inclusive) are in the set."""

        rv = []
        start = None
        for ri in xrange(len(self.__codepoints)):
            if start is not None:
                rv.append( (start, self.__codepoints[ri]-1) )
                start = None
            else:
                start = self.__codepoints[ri]
        if (start is not None) and (start <= self.MaxCodePoint):
            rv.append( (start, self.MaxCodePoint) )
        return rv

    def negate (self):
        """Return an instance that represents the inverse of this set."""
        rv = type(self)()
        if (0 < len(self.__codepoints)) and (0 == self.__codepoints[0]):
            rv.__codepoints.extend(self.__codepoints[1:])
        else:
            rv.__codepoints.append(0)
            rv.__codepoints.extend(self.__codepoints)
        return rv

    def asSingleCharacter (self):
        """If this set represents a single character, return it as its
        unicode string value.  Otherwise return C{None}."""
        if (2 != len(self.__codepoints)) or (1 < (self.__codepoints[1] - self.__codepoints[0])):
            return None
        return six.unichr(self.__codepoints[0])

from pyxb.utils.unicode_data import PropertyMap
from pyxb.utils.unicode_data import BlockMap

class XML1p0e2 (object):
    """Regular expression support for XML Schema Data Types.

    This class holds character classes and regular expressions used to
    constrain the lexical space of XML Schema datatypes derived from
    U{string<http://www.w3.org/TR/xmlschema-2/#string>}.  They are
    from U{XML 1.0 (Second
    Edition)<http://www.w3.org/TR/2000/WD-xml-2e-20000814>} and
    U{Namespaces in XML
    <http://www.w3.org/TR/1999/REC-xml-names-19990114/>}.

    Unlike the regular expressions used for pattern constraints in XML
    Schema, which are derived from the Unicode 3.1 specification,
    these are derived from the Unicode 2.0 specification.

    The XML Schema definition refers explicitly to the second edition
    of XML, so we have to use these code point sets and patterns.  Be
    aware that U{subsequent updates to the XML specification
    <http://www.w3.org/XML/xml-V10-4e-errata#E09>} have changed the
    corresponding patterns for other uses of XML.  One significant
    change is that the original specification, used here, does not
    allow wide unicode characters."""

    Char = CodePointSet(
        0x0009,
        0x000A,
        0x000D,
        ( 0x0020, 0xD7FF ),
        ( 0xE000, 0xFFFD )
        )
    if SupportsWideUnicode:
        Char.add( ( 1+CodePointSet.MaxShortCodePoint, CodePointSet.MaxCodePoint ) )

    BaseChar = CodePointSet(
        ( 0x0041, 0x005A ),
        ( 0x0061, 0x007A ),
        ( 0x00C0, 0x00D6 ),
        ( 0x00D8, 0x00F6 ),
        ( 0x00F8, 0x00FF ),
        ( 0x0100, 0x0131 ),
        ( 0x0134, 0x013E ),
        ( 0x0141, 0x0148 ),
        ( 0x014A, 0x017E ),
        ( 0x0180, 0x01C3 ),
        ( 0x01CD, 0x01F0 ),
        ( 0x01F4, 0x01F5 ),
        ( 0x01FA, 0x0217 ),
        ( 0x0250, 0x02A8 ),
        ( 0x02BB, 0x02C1 ),
        0x0386,
        ( 0x0388, 0x038A ),
        0x038C,
        ( 0x038E, 0x03A1 ),
        ( 0x03A3, 0x03CE ),
        ( 0x03D0, 0x03D6 ),
        0x03DA,
        0x03DC,
        0x03DE,
        0x03E0,
        ( 0x03E2, 0x03F3 ),
        ( 0x0401, 0x040C ),
        ( 0x040E, 0x044F ),
        ( 0x0451, 0x045C ),
        ( 0x045E, 0x0481 ),
        ( 0x0490, 0x04C4 ),
        ( 0x04C7, 0x04C8 ),
        ( 0x04CB, 0x04CC ),
        ( 0x04D0, 0x04EB ),
        ( 0x04EE, 0x04F5 ),
        ( 0x04F8, 0x04F9 ),
        ( 0x0531, 0x0556 ),
        0x0559,
        ( 0x0561, 0x0586 ),
        ( 0x05D0, 0x05EA ),
        ( 0x05F0, 0x05F2 ),
        ( 0x0621, 0x063A ),
        ( 0x0641, 0x064A ),
        ( 0x0671, 0x06B7 ),
        ( 0x06BA, 0x06BE ),
        ( 0x06C0, 0x06CE ),
        ( 0x06D0, 0x06D3 ),
        0x06D5,
        ( 0x06E5, 0x06E6 ),
        ( 0x0905, 0x0939 ),
        0x093D,
        ( 0x0958, 0x0961 ),
        ( 0x0985, 0x098C ),
        ( 0x098F, 0x0990 ),
        ( 0x0993, 0x09A8 ),
        ( 0x09AA, 0x09B0 ),
        0x09B2,
        ( 0x09B6, 0x09B9 ),
        ( 0x09DC, 0x09DD ),
        ( 0x09DF, 0x09E1 ),
        ( 0x09F0, 0x09F1 ),
        ( 0x0A05, 0x0A0A ),
        ( 0x0A0F, 0x0A10 ),
        ( 0x0A13, 0x0A28 ),
        ( 0x0A2A, 0x0A30 ),
        ( 0x0A32, 0x0A33 ),
        ( 0x0A35, 0x0A36 ),
        ( 0x0A38, 0x0A39 ),
        ( 0x0A59, 0x0A5C ),
        0x0A5E,
        ( 0x0A72, 0x0A74 ),
        ( 0x0A85, 0x0A8B ),
        0x0A8D,
        ( 0x0A8F, 0x0A91 ),
        ( 0x0A93, 0x0AA8 ),
        ( 0x0AAA, 0x0AB0 ),
        ( 0x0AB2, 0x0AB3 ),
        ( 0x0AB5, 0x0AB9 ),
        0x0ABD,
        0x0AE0,
        ( 0x0B05, 0x0B0C ),
        ( 0x0B0F, 0x0B10 ),
        ( 0x0B13, 0x0B28 ),
        ( 0x0B2A, 0x0B30 ),
        ( 0x0B32, 0x0B33 ),
        ( 0x0B36, 0x0B39 ),
        0x0B3D,
        ( 0x0B5C, 0x0B5D ),
        ( 0x0B5F, 0x0B61 ),
        ( 0x0B85, 0x0B8A ),
        ( 0x0B8E, 0x0B90 ),
        ( 0x0B92, 0x0B95 ),
        ( 0x0B99, 0x0B9A ),
        0x0B9C,
        ( 0x0B9E, 0x0B9F ),
        ( 0x0BA3, 0x0BA4 ),
        ( 0x0BA8, 0x0BAA ),
        ( 0x0BAE, 0x0BB5 ),
        ( 0x0BB7, 0x0BB9 ),
        ( 0x0C05, 0x0C0C ),
        ( 0x0C0E, 0x0C10 ),
        ( 0x0C12, 0x0C28 ),
        ( 0x0C2A, 0x0C33 ),
        ( 0x0C35, 0x0C39 ),
        ( 0x0C60, 0x0C61 ),
        ( 0x0C85, 0x0C8C ),
        ( 0x0C8E, 0x0C90 ),
        ( 0x0C92, 0x0CA8 ),
        ( 0x0CAA, 0x0CB3 ),
        ( 0x0CB5, 0x0CB9 ),
        0x0CDE,
        ( 0x0CE0, 0x0CE1 ),
        ( 0x0D05, 0x0D0C ),
        ( 0x0D0E, 0x0D10 ),
        ( 0x0D12, 0x0D28 ),
        ( 0x0D2A, 0x0D39 ),
        ( 0x0D60, 0x0D61 ),
        ( 0x0E01, 0x0E2E ),
        0x0E30,
        ( 0x0E32, 0x0E33 ),
        ( 0x0E40, 0x0E45 ),
        ( 0x0E81, 0x0E82 ),
        0x0E84,
        ( 0x0E87, 0x0E88 ),
        0x0E8A,
        0x0E8D,
        ( 0x0E94, 0x0E97 ),
        ( 0x0E99, 0x0E9F ),
        ( 0x0EA1, 0x0EA3 ),
        0x0EA5,
        0x0EA7,
        ( 0x0EAA, 0x0EAB ),
        ( 0x0EAD, 0x0EAE ),
        0x0EB0,
        ( 0x0EB2, 0x0EB3 ),
        0x0EBD,
        ( 0x0EC0, 0x0EC4 ),
        ( 0x0F40, 0x0F47 ),
        ( 0x0F49, 0x0F69 ),
        ( 0x10A0, 0x10C5 ),
        ( 0x10D0, 0x10F6 ),
        0x1100,
        ( 0x1102, 0x1103 ),
        ( 0x1105, 0x1107 ),
        0x1109,
        ( 0x110B, 0x110C ),
        ( 0x110E, 0x1112 ),
        0x113C,
        0x113E,
        0x1140,
        0x114C,
        0x114E,
        0x1150,
        ( 0x1154, 0x1155 ),
        0x1159,
        ( 0x115F, 0x1161 ),
        0x1163,
        0x1165,
        0x1167,
        0x1169,
        ( 0x116D, 0x116E ),
        ( 0x1172, 0x1173 ),
        0x1175,
        0x119E,
        0x11A8,
        0x11AB,
        ( 0x11AE, 0x11AF ),
        ( 0x11B7, 0x11B8 ),
        0x11BA,
        ( 0x11BC, 0x11C2 ),
        0x11EB,
        0x11F0,
        0x11F9,
        ( 0x1E00, 0x1E9B ),
        ( 0x1EA0, 0x1EF9 ),
        ( 0x1F00, 0x1F15 ),
        ( 0x1F18, 0x1F1D ),
        ( 0x1F20, 0x1F45 ),
        ( 0x1F48, 0x1F4D ),
        ( 0x1F50, 0x1F57 ),
        0x1F59,
        0x1F5B,
        0x1F5D,
        ( 0x1F5F, 0x1F7D ),
        ( 0x1F80, 0x1FB4 ),
        ( 0x1FB6, 0x1FBC ),
        0x1FBE,
        ( 0x1FC2, 0x1FC4 ),
        ( 0x1FC6, 0x1FCC ),
        ( 0x1FD0, 0x1FD3 ),
        ( 0x1FD6, 0x1FDB ),
        ( 0x1FE0, 0x1FEC ),
        ( 0x1FF2, 0x1FF4 ),
        ( 0x1FF6, 0x1FFC ),
        0x2126,
        ( 0x212A, 0x212B ),
        0x212E,
        ( 0x2180, 0x2182 ),
        ( 0x3041, 0x3094 ),
        ( 0x30A1, 0x30FA ),
        ( 0x3105, 0x312C ),
        ( 0xAC00, 0xD7A3 )
        )

    Ideographic = CodePointSet(
        ( 0x4E00, 0x9FA5 ),
        0x3007,
        ( 0x3021, 0x3029 )
        )

    Letter = CodePointSet(BaseChar).extend(Ideographic)

    CombiningChar = CodePointSet(
        ( 0x0300, 0x0345 ),
        ( 0x0360, 0x0361 ),
        ( 0x0483, 0x0486 ),
        ( 0x0591, 0x05A1 ),
        ( 0x05A3, 0x05B9 ),
        ( 0x05BB, 0x05BD ),
        0x05BF,
        ( 0x05C1, 0x05C2 ),
        0x05C4,
        ( 0x064B, 0x0652 ),
        0x0670,
        ( 0x06D6, 0x06DC ),
        ( 0x06DD, 0x06DF ),
        ( 0x06E0, 0x06E4 ),
        ( 0x06E7, 0x06E8 ),
        ( 0x06EA, 0x06ED ),
        ( 0x0901, 0x0903 ),
        0x093C,
        ( 0x093E, 0x094C ),
        0x094D,
        ( 0x0951, 0x0954 ),
        ( 0x0962, 0x0963 ),
        ( 0x0981, 0x0983 ),
        0x09BC,
        0x09BE,
        0x09BF,
        ( 0x09C0, 0x09C4 ),
        ( 0x09C7, 0x09C8 ),
        ( 0x09CB, 0x09CD ),
        0x09D7,
        ( 0x09E2, 0x09E3 ),
        0x0A02,
        0x0A3C,
        0x0A3E,
        0x0A3F,
        ( 0x0A40, 0x0A42 ),
        ( 0x0A47, 0x0A48 ),
        ( 0x0A4B, 0x0A4D ),
        ( 0x0A70, 0x0A71 ),
        ( 0x0A81, 0x0A83 ),
        0x0ABC,
        ( 0x0ABE, 0x0AC5 ),
        ( 0x0AC7, 0x0AC9 ),
        ( 0x0ACB, 0x0ACD ),
        ( 0x0B01, 0x0B03 ),
        0x0B3C,
        ( 0x0B3E, 0x0B43 ),
        ( 0x0B47, 0x0B48 ),
        ( 0x0B4B, 0x0B4D ),
        ( 0x0B56, 0x0B57 ),
        ( 0x0B82, 0x0B83 ),
        ( 0x0BBE, 0x0BC2 ),
        ( 0x0BC6, 0x0BC8 ),
        ( 0x0BCA, 0x0BCD ),
        0x0BD7,
        ( 0x0C01, 0x0C03 ),
        ( 0x0C3E, 0x0C44 ),
        ( 0x0C46, 0x0C48 ),
        ( 0x0C4A, 0x0C4D ),
        ( 0x0C55, 0x0C56 ),
        ( 0x0C82, 0x0C83 ),
        ( 0x0CBE, 0x0CC4 ),
        ( 0x0CC6, 0x0CC8 ),
        ( 0x0CCA, 0x0CCD ),
        ( 0x0CD5, 0x0CD6 ),
        ( 0x0D02, 0x0D03 ),
        ( 0x0D3E, 0x0D43 ),
        ( 0x0D46, 0x0D48 ),
        ( 0x0D4A, 0x0D4D ),
        0x0D57,
        0x0E31,
        ( 0x0E34, 0x0E3A ),
        ( 0x0E47, 0x0E4E ),
        0x0EB1,
        ( 0x0EB4, 0x0EB9 ),
        ( 0x0EBB, 0x0EBC ),
        ( 0x0EC8, 0x0ECD ),
        ( 0x0F18, 0x0F19 ),
        0x0F35,
        0x0F37,
        0x0F39,
        0x0F3E,
        0x0F3F,
        ( 0x0F71, 0x0F84 ),
        ( 0x0F86, 0x0F8B ),
        ( 0x0F90, 0x0F95 ),
        0x0F97,
        ( 0x0F99, 0x0FAD ),
        ( 0x0FB1, 0x0FB7 ),
        0x0FB9,
        ( 0x20D0, 0x20DC ),
        0x20E1,
        ( 0x302A, 0x302F ),
        0x3099,
        0x309A
        )

    Digit = CodePointSet(
        ( 0x0030, 0x0039 ),
        ( 0x0660, 0x0669 ),
        ( 0x06F0, 0x06F9 ),
        ( 0x0966, 0x096F ),
        ( 0x09E6, 0x09EF ),
        ( 0x0A66, 0x0A6F ),
        ( 0x0AE6, 0x0AEF ),
        ( 0x0B66, 0x0B6F ),
        ( 0x0BE7, 0x0BEF ),
        ( 0x0C66, 0x0C6F ),
        ( 0x0CE6, 0x0CEF ),
        ( 0x0D66, 0x0D6F ),
        ( 0x0E50, 0x0E59 ),
        ( 0x0ED0, 0x0ED9 ),
        ( 0x0F20, 0x0F29 )
        )

    Extender = CodePointSet(
        0x00B7,
        0x02D0,
        0x02D1,
        0x0387,
        0x0640,
        0x0E46,
        0x0EC6,
        0x3005,
        ( 0x3031, 0x3035 ),
        ( 0x309D, 0x309E ),
        ( 0x30FC, 0x30FE )
        )

    # Not an explicit production, but used in Name production
    NameStartChar = CodePointSet(Letter)
    NameStartChar.add(ord('_'))
    NameStartChar.add(ord(':'))

    NCNameStartChar = CodePointSet(Letter)
    NCNameStartChar.add(ord('_'))

    NameChar = CodePointSet(Letter)
    NameChar.extend(Digit)
    NameChar.add(ord('.'))
    NameChar.add(ord('-'))
    NameChar.add(ord('_'))
    NameChar.add(ord(':'))
    NameChar.extend(CombiningChar)
    NameChar.extend(Extender)

    NCNameChar = CodePointSet(Letter)
    NCNameChar.extend(Digit)
    NCNameChar.add(ord('.'))
    NCNameChar.add(ord('-'))
    NCNameChar.add(ord('_'))
    NCNameChar.extend(CombiningChar)
    NCNameChar.extend(Extender)

    Name_pat = '%s%s*' % (NameStartChar.asPattern(), NameChar.asPattern())
    Name_re = re.compile('^%s$' % (Name_pat,))
    NmToken_pat = '%s+' % (NameChar.asPattern(),)
    NmToken_re = re.compile('^%s$' % (NmToken_pat,))
    NCName_pat = '%s%s*' % (NCNameStartChar.asPattern(), NCNameChar.asPattern())
    NCName_re = re.compile('^%s$' % (NCName_pat,))
    QName_pat = '(%s:)?%s' % (NCName_pat, NCName_pat)
    QName_re = re.compile('^%s$' % (QName_pat,))

# Production 24 : Single Character Escapes
SingleCharEsc = { 'n' : CodePointSet(0x0A),
                  'r' : CodePointSet(0x0D),
                  't' : CodePointSet(0x09) }
for c in r'\|.-^?*+{}()[]':
    SingleCharEsc[c] = CodePointSet(ord(c))

# Production 25 : Category Escapes
# Production 26: Complemented Category Escapes
catEsc = { }
complEsc = { }
for k, v in six.iteritems(PropertyMap):
    catEsc[six.u('p{%s}') % (k,)] = v
    catEsc[six.u('P{%s}') % (k,)] = v.negate()

# Production 36 : IsBlock escapes
IsBlockEsc = { }
for k, v in six.iteritems(BlockMap):
    IsBlockEsc[six.u('p{Is%s}') % (k,)] = v
    IsBlockEsc[six.u('P{Is%s}') % (k,)] = v.negate()

# Production 37 : Multi-Character Escapes
WildcardEsc = CodePointSet(ord('\n'), ord('\r')).negate()
MultiCharEsc = { }
MultiCharEsc['s'] = CodePointSet(0x20, ord('\t'), ord('\n'), ord('\r'))
MultiCharEsc['S'] = MultiCharEsc['s'].negate()
MultiCharEsc['i'] = CodePointSet(XML1p0e2.Letter).add(ord('_')).add(ord(':'))
MultiCharEsc['I'] = MultiCharEsc['i'].negate()
MultiCharEsc['c'] = CodePointSet(XML1p0e2.NameChar)
MultiCharEsc['C'] = MultiCharEsc['c'].negate()
MultiCharEsc['d'] = PropertyMap['Nd']
MultiCharEsc['D'] = MultiCharEsc['d'].negate()
MultiCharEsc['W'] = CodePointSet(PropertyMap['P']).extend(PropertyMap['Z']).extend(PropertyMap['C'])
MultiCharEsc['w'] = MultiCharEsc['W'].negate()
