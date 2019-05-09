import functools
import json
import os.path
import pprint
from io import open

import pytest
from webencodings import Encoding, lookup

from . import (parse_component_value_list, parse_declaration_list,
               parse_one_component_value, parse_one_declaration,
               parse_one_rule, parse_rule_list, parse_stylesheet,
               parse_stylesheet_bytes, serialize)
from .ast import (AtKeywordToken, AtRule, Comment, CurlyBracketsBlock,
                  Declaration, DimensionToken, FunctionBlock, HashToken,
                  IdentToken, LiteralToken, NumberToken, ParenthesesBlock,
                  ParseError, PercentageToken, QualifiedRule,
                  SquareBracketsBlock, StringToken, UnicodeRangeToken,
                  URLToken, WhitespaceToken)
from .color3 import RGBA, parse_color
from .nth import parse_nth


def generic(func):
    implementations = func()

    @functools.wraps(func)
    def run(value):
        repr(value)  # Test that this does not raise.
        return implementations[type(value)](value)
    return run


@generic
def to_json():
    def numeric(t):
        return [
            t.representation, t.value,
            'integer' if t.int_value is not None else 'number']
    return {
        type(None): lambda _: None,
        str: lambda s: s,
        int: lambda s: s,
        list: lambda l: [to_json(el) for el in l],
        tuple: lambda l: [to_json(el) for el in l],
        Encoding: lambda e: e.name,
        ParseError: lambda e: ['error', e.kind],

        Comment: lambda t: '/* … */',
        WhitespaceToken: lambda t: ' ',
        LiteralToken: lambda t: t.value,
        IdentToken: lambda t: ['ident', t.value],
        AtKeywordToken: lambda t: ['at-keyword', t.value],
        HashToken: lambda t: ['hash', t.value,
                              'id' if t.is_identifier else 'unrestricted'],
        StringToken: lambda t: ['string', t.value],
        URLToken: lambda t: ['url', t.value],
        NumberToken: lambda t: ['number'] + numeric(t),
        PercentageToken: lambda t: ['percentage'] + numeric(t),
        DimensionToken: lambda t: ['dimension'] + numeric(t) + [t.unit],
        UnicodeRangeToken: lambda t: ['unicode-range', t.start, t.end],

        CurlyBracketsBlock: lambda t: ['{}'] + to_json(t.content),
        SquareBracketsBlock: lambda t: ['[]'] + to_json(t.content),
        ParenthesesBlock: lambda t: ['()'] + to_json(t.content),
        FunctionBlock: lambda t: ['function', t.name] + to_json(t.arguments),

        Declaration: lambda d: ['declaration', d.name,
                                to_json(d.value), d.important],
        AtRule: lambda r: ['at-rule', r.at_keyword, to_json(r.prelude),
                           to_json(r.content)],
        QualifiedRule: lambda r: ['qualified rule', to_json(r.prelude),
                                  to_json(r.content)],

        RGBA: lambda v: [round(c, 10) for c in v],
    }


def load_json(filename):
    json_data = json.load(open(os.path.join(
        os.path.dirname(__file__), 'css-parsing-tests', filename),
        encoding='utf-8'))
    return list(zip(json_data[::2], json_data[1::2]))


def json_test(filename=None):
    def decorator(function):
        filename_ = filename or function.__name__.split('_', 1)[-1] + '.json'

        @pytest.mark.parametrize(('css', 'expected'), load_json(filename_))
        def test(css, expected):
            value = to_json(function(css))
            if value != expected:  # pragma: no cover
                pprint.pprint(value)
                assert value == expected
        return test
    return decorator


SKIP = dict(skip_comments=True, skip_whitespace=True)


@json_test()
def test_component_value_list(input):
    return parse_component_value_list(input, skip_comments=True)


@json_test()
def test_one_component_value(input):
    return parse_one_component_value(input, skip_comments=True)


@json_test()
def test_declaration_list(input):
    return parse_declaration_list(input, **SKIP)


@json_test()
def test_one_declaration(input):
    return parse_one_declaration(input, skip_comments=True)


@json_test()
def test_stylesheet(input):
    return parse_stylesheet(input, **SKIP)


@json_test()
def test_rule_list(input):
    return parse_rule_list(input, **SKIP)


@json_test()
def test_one_rule(input):
    return parse_one_rule(input, skip_comments=True)


@json_test()
def test_color3(input):
    return parse_color(input)


@json_test(filename='An+B.json')
def test_nth(input):
    return parse_nth(input)


# Do not use @pytest.mark.parametrize because it is slow with that many values.
def test_color3_hsl():
    for css, expected in load_json('color3_hsl.json'):
        assert to_json(parse_color(css)) == expected


def test_color3_keywords():
    for css, expected in load_json('color3_keywords.json'):
        result = parse_color(css)
        if result is not None:
            r, g, b, a = result
            result = [r * 255, g * 255, b * 255, a]
        assert result == expected


@json_test()
def test_stylesheet_bytes(kwargs):
    kwargs['css_bytes'] = kwargs['css_bytes'].encode('latin1')
    kwargs.pop('comment', None)
    if kwargs.get('environment_encoding'):
        kwargs['environment_encoding'] = lookup(kwargs['environment_encoding'])
    kwargs.update(SKIP)
    return parse_stylesheet_bytes(**kwargs)


@json_test(filename='component_value_list.json')
def test_serialization(css):
    parsed = parse_component_value_list(css, skip_comments=True)
    return parse_component_value_list(serialize(parsed), skip_comments=True)


def test_skip():
    source = '''
    /* foo */
    @media print {
        #foo {
            width: /* bar*/4px;
            color: green;
        }
    }
    '''
    no_ws = parse_stylesheet(source, skip_whitespace=True)
    no_comment = parse_stylesheet(source, skip_comments=True)
    default = parse_component_value_list(source)
    assert serialize(no_ws) != source
    assert serialize(no_comment) != source
    assert serialize(default) == source


def test_comment_eof():
    source = '/* foo '
    parsed = parse_component_value_list(source)
    assert serialize(parsed) == '/* foo */'


def test_parse_declaration_value_color():
    source = 'color:#369'
    declaration = parse_one_declaration(source)
    (value_token,) = declaration.value
    assert parse_color(value_token) == (.2, .4, .6, 1)
    assert declaration.serialize() == source


def test_serialize_rules():
    source = '@import "a.css"; foo#bar.baz { color: red } /**/ @media print{}'
    rules = parse_rule_list(source)
    assert serialize(rules) == source


def test_serialize_declarations():
    source = 'color: #123; /**/ @top-left {} width:7px !important;'
    rules = parse_declaration_list(source)
    assert serialize(rules) == source


def test_backslash_delim():
    source = '\\\nfoo'
    tokens = parse_component_value_list(source)
    assert [t.type for t in tokens] == ['literal', 'whitespace', 'ident']
    assert tokens[0].value == '\\'
    del tokens[1]
    assert [t.type for t in tokens] == ['literal', 'ident']
    assert serialize(tokens) == source
