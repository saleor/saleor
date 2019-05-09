"""Symbolic primitives + unicode/ASCII abstraction for pretty.py"""

from __future__ import print_function, division

import sys
import warnings
from string import ascii_lowercase, ascii_uppercase

unicode_warnings = ''

from sympy.core.compatibility import unicode, range

# first, setup unicodedate environment
try:
    import unicodedata

    def U(name):
        """unicode character by name or None if not found"""
        try:
            u = unicodedata.lookup(name)
        except KeyError:
            u = None

            global unicode_warnings
            unicode_warnings += 'No \'%s\' in unicodedata\n' % name

        return u

except ImportError:
    unicode_warnings += 'No unicodedata available\n'
    U = lambda name: None

from sympy.printing.conventions import split_super_sub
from sympy.core.alphabets import greeks

# prefix conventions when constructing tables
# L   - LATIN     i
# G   - GREEK     beta
# D   - DIGIT     0
# S   - SYMBOL    +


__all__ = ['greek_unicode', 'sub', 'sup', 'xsym', 'vobj', 'hobj', 'pretty_symbol',
           'annotated']


_use_unicode = False


def pretty_use_unicode(flag=None):
    """Set whether pretty-printer should use unicode by default"""
    global _use_unicode
    global unicode_warnings
    if flag is None:
        return _use_unicode

    # we know that some letters are not supported in Python 2.X so
    # ignore those warnings. Remove this when 2.X support is dropped.
    if unicode_warnings:
        known = ['LATIN SUBSCRIPT SMALL LETTER %s' % i for i in 'HKLMNPST']
        unicode_warnings = '\n'.join([
            l for l in unicode_warnings.splitlines() if not any(
            i in l for i in known)])
    # ------------ end of 2.X warning filtering

    if flag and unicode_warnings:
        # print warnings (if any) on first unicode usage
        warnings.warn(unicode_warnings)
        unicode_warnings = ''

    use_unicode_prev = _use_unicode
    _use_unicode = flag
    return use_unicode_prev


def pretty_try_use_unicode():
    """See if unicode output is available and leverage it if possible"""

    try:
        symbols = []

        # see, if we can represent greek alphabet
        symbols.extend(greek_unicode.values())

        # and atoms
        symbols += atoms_table.values()

        for s in symbols:
            if s is None:
                return  # common symbols not present!

            encoding = getattr(sys.stdout, 'encoding', None)

            # this happens when e.g. stdout is redirected through a pipe, or is
            # e.g. a cStringIO.StringO
            if encoding is None:
                return  # sys.stdout has no encoding

            # try to encode
            s.encode(encoding)

    except UnicodeEncodeError:
        pass
    else:
        pretty_use_unicode(True)


def xstr(*args):
    """call str or unicode depending on current mode"""
    if _use_unicode:
        return unicode(*args)
    else:
        return str(*args)

# GREEK
g = lambda l: U('GREEK SMALL LETTER %s' % l.upper())
G = lambda l: U('GREEK CAPITAL LETTER %s' % l.upper())

greek_letters = list(greeks) # make a copy
# deal with Unicode's funny spelling of lambda
greek_letters[greek_letters.index('lambda')] = 'lamda'

# {}  greek letter -> (g,G)
greek_unicode = {l: (g(l), G(l)) for l in greek_letters}
greek_unicode = dict((L, g(L)) for L in greek_letters)
greek_unicode.update((L[0].upper() + L[1:], G(L)) for L in greek_letters)

# aliases
greek_unicode['lambda'] = greek_unicode['lamda']
greek_unicode['Lambda'] = greek_unicode['Lamda']
greek_unicode['varsigma'] = u'\N{GREEK SMALL LETTER FINAL SIGMA}'

# BOLD
b = lambda l: U('MATHEMATICAL BOLD SMALL %s' % l.upper())
B = lambda l: U('MATHEMATICAL BOLD CAPITAL %s' % l.upper())

bold_unicode = dict((l, b(l)) for l in ascii_lowercase)
bold_unicode.update((L, B(L)) for L in ascii_uppercase)

# GREEK BOLD
gb = lambda l: U('MATHEMATICAL BOLD SMALL %s' % l.upper())
GB = lambda l: U('MATHEMATICAL BOLD CAPITAL  %s' % l.upper())

greek_bold_letters = list(greeks) # make a copy, not strictly required here
# deal with Unicode's funny spelling of lambda
greek_bold_letters[greek_bold_letters.index('lambda')] = 'lamda'

# {}  greek letter -> (g,G)
greek_bold_unicode = {l: (g(l), G(l)) for l in greek_bold_letters}
greek_bold_unicode = dict((L, g(L)) for L in greek_bold_letters)
greek_bold_unicode.update((L[0].upper() + L[1:], G(L)) for L in greek_bold_letters)
greek_bold_unicode['lambda'] = greek_unicode['lamda']
greek_bold_unicode['Lambda'] = greek_unicode['Lamda']
greek_bold_unicode['varsigma'] = u'\N{MATHEMATICAL BOLD SMALL FINAL SIGMA}'

digit_2txt = {
    '0':    'ZERO',
    '1':    'ONE',
    '2':    'TWO',
    '3':    'THREE',
    '4':    'FOUR',
    '5':    'FIVE',
    '6':    'SIX',
    '7':    'SEVEN',
    '8':    'EIGHT',
    '9':    'NINE',
}

symb_2txt = {
    '+':    'PLUS SIGN',
    '-':    'MINUS',
    '=':    'EQUALS SIGN',
    '(':    'LEFT PARENTHESIS',
    ')':    'RIGHT PARENTHESIS',
    '[':    'LEFT SQUARE BRACKET',
    ']':    'RIGHT SQUARE BRACKET',
    '{':    'LEFT CURLY BRACKET',
    '}':    'RIGHT CURLY BRACKET',

    # non-std
    '{}':   'CURLY BRACKET',
    'sum':  'SUMMATION',
    'int':  'INTEGRAL',
}

# SUBSCRIPT & SUPERSCRIPT
LSUB = lambda letter: U('LATIN SUBSCRIPT SMALL LETTER %s' % letter.upper())
GSUB = lambda letter: U('GREEK SUBSCRIPT SMALL LETTER %s' % letter.upper())
DSUB = lambda digit:  U('SUBSCRIPT %s' % digit_2txt[digit])
SSUB = lambda symb:   U('SUBSCRIPT %s' % symb_2txt[symb])

LSUP = lambda letter: U('SUPERSCRIPT LATIN SMALL LETTER %s' % letter.upper())
DSUP = lambda digit:  U('SUPERSCRIPT %s' % digit_2txt[digit])
SSUP = lambda symb:   U('SUPERSCRIPT %s' % symb_2txt[symb])

sub = {}    # symb -> subscript symbol
sup = {}    # symb -> superscript symbol

# latin subscripts
for l in 'aeioruvxhklmnpst':
    sub[l] = LSUB(l)

for l in 'in':
    sup[l] = LSUP(l)

for gl in ['beta', 'gamma', 'rho', 'phi', 'chi']:
    sub[gl] = GSUB(gl)

for d in [str(i) for i in range(10)]:
    sub[d] = DSUB(d)
    sup[d] = DSUP(d)

for s in '+-=()':
    sub[s] = SSUB(s)
    sup[s] = SSUP(s)

# Variable modifiers
# TODO: Make brackets adjust to height of contents
modifier_dict = {
    # Accents
    'mathring': lambda s: center_accent(s, u'\N{COMBINING RING ABOVE}'),
    'ddddot': lambda s: center_accent(s, u'\N{COMBINING FOUR DOTS ABOVE}'),
    'dddot': lambda s: center_accent(s, u'\N{COMBINING THREE DOTS ABOVE}'),
    'ddot': lambda s: center_accent(s, u'\N{COMBINING DIAERESIS}'),
    'dot': lambda s: center_accent(s, u'\N{COMBINING DOT ABOVE}'),
    'check': lambda s: center_accent(s, u'\N{COMBINING CARON}'),
    'breve': lambda s: center_accent(s, u'\N{COMBINING BREVE}'),
    'acute': lambda s: center_accent(s, u'\N{COMBINING ACUTE ACCENT}'),
    'grave': lambda s: center_accent(s, u'\N{COMBINING GRAVE ACCENT}'),
    'tilde': lambda s: center_accent(s, u'\N{COMBINING TILDE}'),
    'hat': lambda s: center_accent(s, u'\N{COMBINING CIRCUMFLEX ACCENT}'),
    'bar': lambda s: center_accent(s, u'\N{COMBINING OVERLINE}'),
    'vec': lambda s: center_accent(s, u'\N{COMBINING RIGHT ARROW ABOVE}'),
    'prime': lambda s: s+u'\N{PRIME}',
    'prm': lambda s: s+u'\N{PRIME}',
    # # Faces -- these are here for some compatibility with latex printing
    # 'bold': lambda s: s,
    # 'bm': lambda s: s,
    # 'cal': lambda s: s,
    # 'scr': lambda s: s,
    # 'frak': lambda s: s,
    # Brackets
    'norm': lambda s: u'\N{DOUBLE VERTICAL LINE}'+s+u'\N{DOUBLE VERTICAL LINE}',
    'avg': lambda s: u'\N{MATHEMATICAL LEFT ANGLE BRACKET}'+s+u'\N{MATHEMATICAL RIGHT ANGLE BRACKET}',
    'abs': lambda s: u'\N{VERTICAL LINE}'+s+u'\N{VERTICAL LINE}',
    'mag': lambda s: u'\N{VERTICAL LINE}'+s+u'\N{VERTICAL LINE}',
}

# VERTICAL OBJECTS
HUP = lambda symb: U('%s UPPER HOOK' % symb_2txt[symb])
CUP = lambda symb: U('%s UPPER CORNER' % symb_2txt[symb])
MID = lambda symb: U('%s MIDDLE PIECE' % symb_2txt[symb])
EXT = lambda symb: U('%s EXTENSION' % symb_2txt[symb])
HLO = lambda symb: U('%s LOWER HOOK' % symb_2txt[symb])
CLO = lambda symb: U('%s LOWER CORNER' % symb_2txt[symb])
TOP = lambda symb: U('%s TOP' % symb_2txt[symb])
BOT = lambda symb: U('%s BOTTOM' % symb_2txt[symb])

# {} '('  ->  (extension, start, end, middle) 1-character
_xobj_unicode = {

    # vertical symbols
    #       (( ext, top, bot, mid ), c1)
    '(':    (( EXT('('), HUP('('), HLO('(') ), '('),
    ')':    (( EXT(')'), HUP(')'), HLO(')') ), ')'),
    '[':    (( EXT('['), CUP('['), CLO('[') ), '['),
    ']':    (( EXT(']'), CUP(']'), CLO(']') ), ']'),
    '{':    (( EXT('{}'), HUP('{'), HLO('{'), MID('{') ), '{'),
    '}':    (( EXT('{}'), HUP('}'), HLO('}'), MID('}') ), '}'),
    '|':    U('BOX DRAWINGS LIGHT VERTICAL'),

    '<':    ((U('BOX DRAWINGS LIGHT VERTICAL'),
              U('BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT'),
              U('BOX DRAWINGS LIGHT DIAGONAL UPPER LEFT TO LOWER RIGHT')), '<'),

    '>':    ((U('BOX DRAWINGS LIGHT VERTICAL'),
              U('BOX DRAWINGS LIGHT DIAGONAL UPPER LEFT TO LOWER RIGHT'),
              U('BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT')), '>'),

    'lfloor': (( EXT('['), EXT('['), CLO('[') ), U('LEFT FLOOR')),
    'rfloor': (( EXT(']'), EXT(']'), CLO(']') ), U('RIGHT FLOOR')),
    'lceil':  (( EXT('['), CUP('['), EXT('[') ), U('LEFT CEILING')),
    'rceil':  (( EXT(']'), CUP(']'), EXT(']') ), U('RIGHT CEILING')),

    'int':  (( EXT('int'), U('TOP HALF INTEGRAL'), U('BOTTOM HALF INTEGRAL') ), U('INTEGRAL')),
    'sum':  (( U('BOX DRAWINGS LIGHT DIAGONAL UPPER LEFT TO LOWER RIGHT'), '_', U('OVERLINE'), U('BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT')), U('N-ARY SUMMATION')),

    # horizontal objects
    #'-':   '-',
    '-':    U('BOX DRAWINGS LIGHT HORIZONTAL'),
    '_':    U('LOW LINE'),
    # We used to use this, but LOW LINE looks better for roots, as it's a
    # little lower (i.e., it lines up with the / perfectly.  But perhaps this
    # one would still be wanted for some cases?
    # '_':    U('HORIZONTAL SCAN LINE-9'),

    # diagonal objects '\' & '/' ?
    '/':    U('BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT'),
    '\\':   U('BOX DRAWINGS LIGHT DIAGONAL UPPER LEFT TO LOWER RIGHT'),
}

_xobj_ascii = {
    # vertical symbols
    #       (( ext, top, bot, mid ), c1)
    '(':    (( '|', '/', '\\' ), '('),
    ')':    (( '|', '\\', '/' ), ')'),

# XXX this looks ugly
#   '[':    (( '|', '-', '-' ), '['),
#   ']':    (( '|', '-', '-' ), ']'),
# XXX not so ugly :(
    '[':    (( '[', '[', '[' ), '['),
    ']':    (( ']', ']', ']' ), ']'),

    '{':    (( '|', '/', '\\', '<' ), '{'),
    '}':    (( '|', '\\', '/', '>' ), '}'),
    '|':    '|',

    '<':    (( '|', '/', '\\' ), '<'),
    '>':    (( '|', '\\', '/' ), '>'),

    'int':  ( ' | ', '  /', '/  ' ),

    # horizontal objects
    '-':    '-',
    '_':    '_',

    # diagonal objects '\' & '/' ?
    '/':    '/',
    '\\':   '\\',
}


def xobj(symb, length):
    """Construct spatial object of given length.

    return: [] of equal-length strings
    """

    if length <= 0:
        raise ValueError("Length should be greater than 0")

    # TODO robustify when no unicodedat available
    if _use_unicode:
        _xobj = _xobj_unicode
    else:
        _xobj = _xobj_ascii

    vinfo = _xobj[symb]

    c1 = top = bot = mid = None

    if not isinstance(vinfo, tuple):        # 1 entry
        ext = vinfo
    else:
        if isinstance(vinfo[0], tuple):     # (vlong), c1
            vlong = vinfo[0]
            c1 = vinfo[1]
        else:                               # (vlong), c1
            vlong = vinfo

        ext = vlong[0]

        try:
            top = vlong[1]
            bot = vlong[2]
            mid = vlong[3]
        except IndexError:
            pass

    if c1 is None:
        c1 = ext
    if top is None:
        top = ext
    if bot is None:
        bot = ext
    if mid is not None:
        if (length % 2) == 0:
            # even height, but we have to print it somehow anyway...
            # XXX is it ok?
            length += 1

    else:
        mid = ext

    if length == 1:
        return c1

    res = []
    next = (length - 2)//2
    nmid = (length - 2) - next*2

    res += [top]
    res += [ext]*next
    res += [mid]*nmid
    res += [ext]*next
    res += [bot]

    return res


def vobj(symb, height):
    """Construct vertical object of a given height

       see: xobj
    """
    return '\n'.join( xobj(symb, height) )


def hobj(symb, width):
    """Construct horizontal object of a given width

       see: xobj
    """
    return ''.join( xobj(symb, width) )

# RADICAL
# n -> symbol
root = {
    2: U('SQUARE ROOT'),   # U('RADICAL SYMBOL BOTTOM')
    3: U('CUBE ROOT'),
    4: U('FOURTH ROOT'),
}


# RATIONAL
VF = lambda txt: U('VULGAR FRACTION %s' % txt)

# (p,q) -> symbol
frac = {
    (1, 2): VF('ONE HALF'),
    (1, 3): VF('ONE THIRD'),
    (2, 3): VF('TWO THIRDS'),
    (1, 4): VF('ONE QUARTER'),
    (3, 4): VF('THREE QUARTERS'),
    (1, 5): VF('ONE FIFTH'),
    (2, 5): VF('TWO FIFTHS'),
    (3, 5): VF('THREE FIFTHS'),
    (4, 5): VF('FOUR FIFTHS'),
    (1, 6): VF('ONE SIXTH'),
    (5, 6): VF('FIVE SIXTHS'),
    (1, 8): VF('ONE EIGHTH'),
    (3, 8): VF('THREE EIGHTHS'),
    (5, 8): VF('FIVE EIGHTHS'),
    (7, 8): VF('SEVEN EIGHTHS'),
}


# atom symbols
_xsym = {
    '==':  ('=', '='),
    '<':   ('<', '<'),
    '>':   ('>', '>'),
    '<=':  ('<=', U('LESS-THAN OR EQUAL TO')),
    '>=':  ('>=', U('GREATER-THAN OR EQUAL TO')),
    '!=':  ('!=', U('NOT EQUAL TO')),
    ':=':  (':=', ':='),
    '+=':  ('+=', '+='),
    '-=':  ('-=', '-='),
    '*=':  ('*=', '*='),
    '/=':  ('/=', '/='),
    '%=':  ('%=', '%='),
    '*':   ('*', U('DOT OPERATOR')),
    '-->': ('-->', U('EM DASH') + U('EM DASH') +
            U('BLACK RIGHT-POINTING TRIANGLE') if U('EM DASH')
            and U('BLACK RIGHT-POINTING TRIANGLE') else None),
    '==>': ('==>', U('BOX DRAWINGS DOUBLE HORIZONTAL') +
            U('BOX DRAWINGS DOUBLE HORIZONTAL') +
            U('BLACK RIGHT-POINTING TRIANGLE') if
            U('BOX DRAWINGS DOUBLE HORIZONTAL') and
            U('BOX DRAWINGS DOUBLE HORIZONTAL') and
            U('BLACK RIGHT-POINTING TRIANGLE') else None),
    '.':   ('*', U('RING OPERATOR')),
}


def xsym(sym):
    """get symbology for a 'character'"""
    op = _xsym[sym]

    if _use_unicode:
        return op[1]
    else:
        return op[0]


# SYMBOLS

atoms_table = {
    # class                    how-to-display
    'Exp1':                    U('SCRIPT SMALL E'),
    'Pi':                      U('GREEK SMALL LETTER PI'),
    'Infinity':                U('INFINITY'),
    'NegativeInfinity':        U('INFINITY') and ('-' + U('INFINITY')),  # XXX what to do here
    #'ImaginaryUnit':          U('GREEK SMALL LETTER IOTA'),
    #'ImaginaryUnit':          U('MATHEMATICAL ITALIC SMALL I'),
    'ImaginaryUnit':           U('DOUBLE-STRUCK ITALIC SMALL I'),
    'EmptySet':                U('EMPTY SET'),
    'Naturals':                U('DOUBLE-STRUCK CAPITAL N'),
    'Naturals0':               (U('DOUBLE-STRUCK CAPITAL N') and
                                (U('DOUBLE-STRUCK CAPITAL N') +
                                 U('SUBSCRIPT ZERO'))),
    'Integers':                U('DOUBLE-STRUCK CAPITAL Z'),
    'Reals':                   U('DOUBLE-STRUCK CAPITAL R'),
    'Complexes':               U('DOUBLE-STRUCK CAPITAL C'),
    'Union':                   U('UNION'),
    'SymmetricDifference':     U('INCREMENT'),
    'Intersection':            U('INTERSECTION'),
    'Ring':                    U('RING OPERATOR')
}


def pretty_atom(atom_name, default=None, printer=None):
    """return pretty representation of an atom"""
    if _use_unicode:
        if printer is not None and atom_name == 'ImaginaryUnit' and printer._settings['imaginary_unit'] == 'j':
            return U('DOUBLE-STRUCK ITALIC SMALL J')
        else:
            return atoms_table[atom_name]
    else:
        if default is not None:
            return default

        raise KeyError('only unicode')  # send it default printer


def pretty_symbol(symb_name, bold_name=False):
    """return pretty representation of a symbol"""
    # let's split symb_name into symbol + index
    # UC: beta1
    # UC: f_beta

    if not _use_unicode:
        return symb_name

    name, sups, subs = split_super_sub(symb_name)

    def translate(s, bold_name) :
        if bold_name:
            gG = greek_bold_unicode.get(s)
        else:
            gG = greek_unicode.get(s)
        if gG is not None:
            return gG
        for key in sorted(modifier_dict.keys(), key=lambda k:len(k), reverse=True) :
            if s.lower().endswith(key) and len(s)>len(key):
                return modifier_dict[key](translate(s[:-len(key)], bold_name))
        if bold_name:
            return ''.join([bold_unicode[c] for c in s])
        return s

    name = translate(name, bold_name)

    # Let's prettify sups/subs. If it fails at one of them, pretty sups/subs are
    # not used at all.
    def pretty_list(l, mapping):
        result = []
        for s in l:
            pretty = mapping.get(s)
            if pretty is None:
                try:  # match by separate characters
                    pretty = ''.join([mapping[c] for c in s])
                except (TypeError, KeyError):
                    return None
            result.append(pretty)
        return result

    pretty_sups = pretty_list(sups, sup)
    if pretty_sups is not None:
        pretty_subs = pretty_list(subs, sub)
    else:
        pretty_subs = None

    # glue the results into one string
    if pretty_subs is None:  # nice formatting of sups/subs did not work
        if subs:
            name += '_'+'_'.join([translate(s, bold_name) for s in subs])
        if sups:
            name += '__'+'__'.join([translate(s, bold_name) for s in sups])
        return name
    else:
        sups_result = ' '.join(pretty_sups)
        subs_result = ' '.join(pretty_subs)

    return ''.join([name, sups_result, subs_result])


def annotated(letter):
    """
    Return a stylised drawing of the letter ``letter``, together with
    information on how to put annotations (super- and subscripts to the
    left and to the right) on it.

    See pretty.py functions _print_meijerg, _print_hyper on how to use this
    information.
    """
    ucode_pics = {
        'F': (2, 0, 2, 0, u'\N{BOX DRAWINGS LIGHT DOWN AND RIGHT}\N{BOX DRAWINGS LIGHT HORIZONTAL}\n'
                          u'\N{BOX DRAWINGS LIGHT VERTICAL AND RIGHT}\N{BOX DRAWINGS LIGHT HORIZONTAL}\n'
                          u'\N{BOX DRAWINGS LIGHT UP}'),
        'G': (3, 0, 3, 1, u'\N{BOX DRAWINGS LIGHT ARC DOWN AND RIGHT}\N{BOX DRAWINGS LIGHT HORIZONTAL}\N{BOX DRAWINGS LIGHT ARC DOWN AND LEFT}\n'
                          u'\N{BOX DRAWINGS LIGHT VERTICAL}\N{BOX DRAWINGS LIGHT RIGHT}\N{BOX DRAWINGS LIGHT DOWN AND LEFT}\n'
                          u'\N{BOX DRAWINGS LIGHT ARC UP AND RIGHT}\N{BOX DRAWINGS LIGHT HORIZONTAL}\N{BOX DRAWINGS LIGHT ARC UP AND LEFT}')
    }
    ascii_pics = {
        'F': (3, 0, 3, 0, ' _\n|_\n|\n'),
        'G': (3, 0, 3, 1, ' __\n/__\n\\_|')
    }

    if _use_unicode:
        return ucode_pics[letter]
    else:
        return ascii_pics[letter]


def center_accent(string, accent):
    """
    Returns a string with accent inserted on the middle character. Useful to
    put combining accents on symbol names, including multi-character names.

    Parameters
    ==========

    string : string
        The string to place the accent in.
    accent : string
        The combining accent to insert

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Combining_character
    .. [2] https://en.wikipedia.org/wiki/Combining_Diacritical_Marks

    """

    # Accent is placed on the previous character, although it may not always look
    # like that depending on console
    midpoint = len(string) // 2 + 1
    firstpart = string[:midpoint]
    secondpart = string[midpoint:]
    return firstpart + accent + secondpart
