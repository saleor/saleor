# -*- coding: utf-8 -*-
# Copyright 2009-2013, Peter A. Bigot
# Copyright 2012, Jon Foster
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

"""Support for regular expressions conformant to the XML Schema specification.

For the most part, XML regular expressions are similar to the POSIX
ones, and can be handled by the Python C{re} module.  The exceptions
are for multi-character (C{\w}) and category escapes (e.g., C{\p{N}} or
C{\p{IPAExtensions}}) and the character set subtraction capability.
This module supports those by scanning the regular expression,
replacing the category escapes with equivalent charset expressions.
It further detects the subtraction syntax and modifies the charset
expression to remove the unwanted code points.

The basic technique is to step through the characters of the regular
expression, entering a recursive-descent parser when one of the
translated constructs is encountered.

There is a nice set of XML regular expressions at
U{http://www.xmlschemareference.com/examples/Ch14/regexpDemo.xsd},
with a sample document at U{
http://www.xmlschemareference.com/examples/Ch14/regexpDemo.xml}"""

import re
import logging
import pyxb.utils.unicode
from pyxb.utils import six

_log = logging.getLogger(__name__)

# AllEsc maps all the possible escape codes and wildcards in an XML schema
# regular expression into the corresponding CodePointSet.
_AllEsc = { }

def _InitializeAllEsc ():
    """Set the values in _AllEsc without introducing C{k} and C{v} into
    the module."""

    _AllEsc.update({ six.u('.'): pyxb.utils.unicode.WildcardEsc })
    bs = six.unichr(0x5c)
    for k, v in six.iteritems(pyxb.utils.unicode.SingleCharEsc):
        _AllEsc[bs + six.text_type(k)] = v
    for k, v in six.iteritems(pyxb.utils.unicode.MultiCharEsc):
        _AllEsc[bs + six.text_type(k)] = v
    for k, v in six.iteritems(pyxb.utils.unicode.catEsc):
        _AllEsc[bs + six.text_type(k)] = v
    for k, v in six.iteritems(pyxb.utils.unicode.complEsc):
        _AllEsc[bs + six.text_type(k)] = v
    for k, v in six.iteritems(pyxb.utils.unicode.IsBlockEsc):
        _AllEsc[bs + six.text_type(k)] = v
_InitializeAllEsc()

class RegularExpressionError (ValueError):
    """Raised when a regular expression cannot be processed.."""
    def __init__ (self, position, description):
        self.position = position
        ValueError.__init__(self, 'At %d: %s' % (position, description))

_CharClassEsc_re = re.compile(r'\\(?:(?P<cgProp>[pP]{(?P<charProp>[-A-Za-z0-9]+)})|(?P<cgClass>[^pP]))')
def _MatchCharClassEsc(text, position):
    """Parse a U{charClassEsc<http://www.w3.org/TR/xmlschema-2/#nt-charClassEsc>} term.

    This is one of:

      - U{SingleCharEsc<http://www.w3.org/TR/xmlschema-2/#nt-SingleCharEsc>},
      an escaped single character such as C{E{\}n}

      - U{MultiCharEsc<http://www.w3.org/TR/xmlschema-2/#nt-MultiCharEsc>},
      an escape code that can match a range of characters,
      e.g. C{E{\}s} to match certain whitespace characters

      - U{catEsc<http://www.w3.org/TR/xmlschema-2/#nt-catEsc>}, the
      C{E{\}pE{lb}...E{rb}} Unicode property escapes including
      categories and blocks

      - U{complEsc<http://www.w3.org/TR/xmlschema-2/#nt-complEsc>},
      the C{E{\}PE{lb}...E{rb}} inverted Unicode property escapes

    If the parsing fails, throws a RegularExpressionError.

    @return: A pair C{(cps, p)} where C{cps} is a
    L{pyxb.utils.unicode.CodePointSet} containing the code points
    associated with the character class, and C{p} is the text offset
    immediately following the escape sequence.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    """

    mo = _CharClassEsc_re.match(text, position)
    if mo:
        escape_code = mo.group(0)
        cps = _AllEsc.get(escape_code)
        if cps is not None:
            return (cps, mo.end())
        char_prop = mo.group('charProp')
        if char_prop is not None:
            if char_prop.startswith('Is'):
                raise RegularExpressionError(position, 'Unrecognized Unicode block %s in %s' % (char_prop[2:], escape_code))
            raise RegularExpressionError(position, 'Unrecognized character property %s' % (escape_code,))
        raise RegularExpressionError(position, 'Unrecognized character class %s' % (escape_code,))
    raise RegularExpressionError(position, "Unrecognized escape identifier at %s" % (text[position:],))

def _MatchPosCharGroup(text, position):
    '''Parse a U{posCharGroup<http://www.w3.org/TR/xmlschema-2/#nt-posCharGroup>} term.

    @return: A tuple C{(cps, fs, p)} where:
      - C{cps} is a L{pyxb.utils.unicode.CodePointSet} containing the code points associated with the group;
      - C{fs} is a C{bool} that is C{True} if the next character is the C{-} in a U{charClassSub<http://www.w3.org/TR/xmlschema-2/#nt-charClassSub>} and C{False} if the group is not part of a charClassSub;
      - C{p} is the text offset immediately following the closing brace.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    '''

    start_position = position

    # DASH is just some unique object, used as a marker.
    # It can't be unicode or a CodePointSet.
    class DashClass:
        pass
    DASH = DashClass()

    # We tokenize first, then go back and stick the ranges together.
    tokens = []
    has_following_subtraction = False
    while True:
        if position >= len(text):
            raise RegularExpressionError(position, "Incomplete character class expression, missing closing ']'")
        ch = text[position]
        if ch == six.u('['):
            # Only allowed if this is a subtraction
            if not tokens or tokens[-1] is not DASH:
                raise RegularExpressionError(position, "'[' character not allowed in character class")
            has_following_subtraction = True
            # For a character class subtraction, the "-[" are not part of the
            # posCharGroup, so undo reading the dash
            tokens.pop()
            position = position - 1
            break
        elif ch == six.u(']'):
            # End
            break
        elif ch == six.unichr(0x5c): # backslash
            cps, position = _MatchCharClassEsc(text, position)
            single_char = cps.asSingleCharacter()
            if single_char is not None:
                tokens.append(single_char)
            else:
                tokens.append(cps)
        elif ch == six.u('-'):
            # We need to distinguish between "-" and "\-".  So we use
            # DASH for a plain "-", and u"-" for a "\-".
            tokens.append(DASH)
            position = position + 1
        else:
            tokens.append(ch)
            position = position + 1

    if not tokens:
        raise RegularExpressionError(position, "Empty character class not allowed")

    # At the start or end of the character group, a dash has to be a literal
    if tokens[0] is DASH:
        tokens[0] = six.u('-')
    if tokens[-1] is DASH:
        tokens[-1] = six.u('-')
    result_cps = pyxb.utils.unicode.CodePointSet()
    cur_token = 0
    while cur_token < len(tokens):
        start = tokens[cur_token]
        if cur_token + 2 < len(tokens) and tokens[cur_token + 1] is DASH:
            end = tokens[cur_token + 2]
            if not isinstance(start, six.text_type) or not isinstance(end, six.text_type):
                if start is DASH or end is DASH:
                    raise RegularExpressionError(start_position, 'Two dashes in a row is not allowed in the middle of a character class.')
                raise RegularExpressionError(start_position, 'Dashes must be surrounded by characters, not character class escapes. %r %r' %(start, end))
            if start > end:
                raise RegularExpressionError(start_position, 'Character ranges must have the lowest character first')
            result_cps.add((ord(start), ord(end)))
            cur_token = cur_token + 3
        else:
            if start is DASH:
                raise RegularExpressionError(start_position, 'Dash without an initial character')
            elif isinstance(start, six.text_type):
                result_cps.add(ord(start))
            else:
                result_cps.extend(start)
            cur_token = cur_token + 1

    return result_cps, has_following_subtraction, position

def _MatchCharClassExpr(text, position):
    '''Parse a U{charClassExpr<http://www.w3.org/TR/xmlschema-2/#nt-charClassExpr>}.

    These are XML regular expression classes such as C{[abc]}, C{[a-c]}, C{[^abc]}, or C{[a-z-[q]]}.

    @param text: The complete text of the regular expression being
    translated.  The first character must be the C{[} starting a
    character class.

    @param position: The offset of the start of the character group.

    @return: A pair C{(cps, p)} where C{cps} is a
    L{pyxb.utils.unicode.CodePointSet} containing the code points
    associated with the property, and C{p} is the text offset
    immediately following the closing brace.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    '''
    if position >= len(text):
        raise RegularExpressionError(position, 'Missing character class expression')
    if six.u('[') != text[position]:
        raise RegularExpressionError(position, "Expected start of character class expression, got '%s'" % (text[position],))
    position = position + 1
    if position >= len(text):
        raise RegularExpressionError(position, 'Missing character class expression')
    negated = (text[position] == '^')
    if negated:
        position = position + 1

    result_cps, has_following_subtraction, position = _MatchPosCharGroup(text, position)

    if negated:
        result_cps = result_cps.negate()

    if has_following_subtraction:
        assert text[position] == six.u('-')
        assert text[position + 1] == six.u('[')
        position = position + 1
        sub_cps, position = _MatchCharClassExpr(text, position)
        result_cps.subtract(sub_cps)

    if position >= len(text) or text[position] != six.u(']'):
        raise RegularExpressionError(position, "Expected ']' to end character class")
    return result_cps, position + 1

def MaybeMatchCharacterClass (text, position):
    """Attempt to match a U{character class expression
    <http://www.w3.org/TR/xmlschema-2/#nt-charClassExpr>}.

    @param text: The complete text of the regular expression being
    translated

    @param position: The offset of the start of the potential
    expression.

    @return: C{None} if C{position} does not begin a character class
    expression; otherwise a pair C{(cps, p)} where C{cps} is a
    L{pyxb.utils.unicode.CodePointSet} containing the code points associated with
    the property, and C{p} is the text offset immediately following
    the closing brace."""
    if position >= len(text):
        return None
    c = text[position]
    np = position + 1
    if '.' == c:
        return (pyxb.utils.unicode.WildcardEsc, np)
    if '[' == c:
        return _MatchCharClassExpr(text, position)
    if '\\' == c:
        return _MatchCharClassEsc(text, position)
    return None

def XMLToPython (pattern):
    """Convert the given pattern to the format required for Python
    regular expressions.

    @param pattern: A Unicode string defining a pattern consistent
    with U{XML regular
    expressions<http://www.w3.org/TR/xmlschema-2/index.html#regexs>}.

    @return: A Unicode string specifying a Python regular expression
    that matches the same language as C{pattern}."""
    assert isinstance(pattern, six.text_type)
    new_pattern_elts = []
    new_pattern_elts.append('^')
    position = 0
    while position < len(pattern):
        cg = MaybeMatchCharacterClass(pattern, position)
        if cg is None:
            ch = pattern[position]
            if ch == six.u('^') or ch == six.u('$'):
                # These characters have no special meaning in XSD.  But they
                # match start and end of string in Python, so they have to
                # be escaped.
                new_pattern_elts.append(six.unichr(0x5c) + ch)
            else:
                new_pattern_elts.append(ch)
            position += 1
        else:
            (cps, position) = cg
            new_pattern_elts.append(cps.asPattern())
    new_pattern_elts.append('$')
    return ''.join(new_pattern_elts)
