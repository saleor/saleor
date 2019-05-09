from textwrap import dedent
from sympy.core.compatibility import range, unichr
from sympy.utilities.misc import translate, replace, ordinal, rawlines, strlines

def test_translate():
    abc = 'abc'
    translate(abc, None, 'a') == 'bc'
    translate(abc, None, '') == 'abc'
    translate(abc, {'a': 'x'}, 'c') == 'xb'
    assert translate(abc, {'a': 'bc'}, 'c') == 'bcb'
    assert translate(abc, {'ab': 'x'}, 'c') == 'x'
    assert translate(abc, {'ab': ''}, 'c') == ''
    assert translate(abc, {'bc': 'x'}, 'c') == 'ab'
    assert translate(abc, {'abc': 'x', 'a': 'y'}) == 'x'
    u = unichr(4096)
    assert translate(abc, 'a', 'x', u) == 'xbc'
    assert (u in translate(abc, 'a', u, u)) is True


def test_replace():
    assert replace('abc', ('a', 'b')) == 'bbc'
    assert replace('abc', {'a': 'Aa'}) == 'Aabc'
    assert replace('abc', ('a', 'b'), ('c', 'C')) == 'bbC'


def test_ordinal():
    assert ordinal(-1) == '-1st'
    assert ordinal(0) == '0th'
    assert ordinal(1) == '1st'
    assert ordinal(2) == '2nd'
    assert ordinal(3) == '3rd'
    assert all(ordinal(i).endswith('th') for i in range(4, 21))
    assert ordinal(100) == '100th'
    assert ordinal(101) == '101st'
    assert ordinal(102) == '102nd'
    assert ordinal(103) == '103rd'
    assert ordinal(104) == '104th'
    assert ordinal(200) == '200th'
    assert all(ordinal(i) == str(i) + 'th' for i in range(-220, -203))


def test_rawlines():
    assert rawlines('a a\na') == "dedent('''\\\n    a a\n    a''')"
    assert rawlines('a a') == "'a a'"
    assert rawlines(strlines('\\le"ft')) == (
        '(\n'
        "    '(\\n'\n"
        '    \'r\\\'\\\\le"ft\\\'\\n\'\n'
        "    ')'\n"
        ')')


def test_strlines():
    q = 'this quote (") is in the middle'
    # the following assert rhs was prepared with
    # print(rawlines(strlines(q, 10)))
    assert strlines(q, 10) == dedent('''\
        (
        'this quo'
        'te (") i'
        's in the'
        ' middle'
        )''')
    assert q == (
        'this quo'
        'te (") i'
        's in the'
        ' middle'
        )
    q = "this quote (') is in the middle"
    assert strlines(q, 20) == dedent('''\
        (
        "this quote (') is "
        "in the middle"
        )''')
    assert strlines('\\left') == (
        '(\n'
        "r'\\left'\n"
        ')')
    assert strlines('\\left', short=True) == r"r'\left'"
    assert strlines('\\le"ft') == (
        '(\n'
        'r\'\\le"ft\'\n'
        ')')
    q = 'this\nother line'
    assert strlines(q) == rawlines(q)
