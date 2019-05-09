from pytest import raises

from graphql.error import GraphQLSyntaxError
from graphql.language.lexer import Lexer, Token, TokenKind
from graphql.language.source import Source


def lex_one(s):
    # type: (str) -> Token
    return Lexer(Source(s)).next_token()


def test_repr_token():
    # type: () -> None
    token = lex_one("500")
    assert repr(token) == "<Token kind=Int at 0..3 value='500'>"


def test_disallows_uncommon_control_characters():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"\u0007")

    assert (
        u'Syntax Error GraphQL (1:1) Invalid character "\\u0007"'
        in excinfo.value.message
    )


def test_accepts_bom_header():
    # type: () -> None
    assert lex_one(u"\uFEFF foo") == Token(TokenKind.NAME, 2, 5, u"foo")


def test_skips_whitespace():
    # type: () -> None
    assert (
        lex_one(
            u"""

    foo


"""
        )
        == Token(TokenKind.NAME, 6, 9, "foo")
    )

    assert (
        lex_one(
            u"""
    #comment
    foo#comment
"""
        )
        == Token(TokenKind.NAME, 18, 21, "foo")
    )

    assert lex_one(u""",,,foo,,,""") == Token(TokenKind.NAME, 3, 6, "foo")


def test_errors_respect_whitespace():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(
            u"""

    ?


"""
        )
    assert excinfo.value.message == (
        u'Syntax Error GraphQL (3:5) Unexpected character "?".\n'
        u"\n"
        u"2: \n"
        u"3:     ?\n"
        u"       ^\n"
        u"4: \n"
    )


def test_lexes_strings():
    # type: () -> None
    assert lex_one(u'"simple"') == Token(TokenKind.STRING, 0, 8, "simple")
    assert lex_one(u'" white space "') == Token(
        TokenKind.STRING, 0, 15, " white space "
    )
    assert lex_one(u'"quote \\""') == Token(TokenKind.STRING, 0, 10, 'quote "')
    assert lex_one(u'"escaped \\n\\r\\b\\t\\f"') == Token(
        TokenKind.STRING, 0, 20, "escaped \n\r\b\t\f"
    )
    assert lex_one(u'"slashes \\\\ \\/"') == Token(
        TokenKind.STRING, 0, 15, "slashes \\ /"
    )
    assert lex_one(u'"unicode \\u1234\\u5678\\u90AB\\uCDEF"') == Token(
        TokenKind.STRING, 0, 34, u"unicode \u1234\u5678\u90AB\uCDEF"
    )


def test_lex_reports_useful_string_errors():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"')
    assert u"Syntax Error GraphQL (1:2) Unterminated string" in excinfo.value.message

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"no end quote')
    assert u"Syntax Error GraphQL (1:14) Unterminated string" in excinfo.value.message

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"contains unescaped \u0007 control char"')
    assert (
        u'Syntax Error GraphQL (1:21) Invalid character within String: "\\u0007".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"null-byte is not \u0000 end of file"')
    assert (
        u'Syntax Error GraphQL (1:19) Invalid character within String: "\\u0000".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"multi\nline"')
    assert u"Syntax Error GraphQL (1:7) Unterminated string" in excinfo.value.message

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"multi\rline"')
    assert u"Syntax Error GraphQL (1:7) Unterminated string" in excinfo.value.message

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"bad \\z esc"')
    assert (
        u"Syntax Error GraphQL (1:7) Invalid character escape sequence: \\z."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"bad \\x esc"')
    assert (
        u"Syntax Error GraphQL (1:7) Invalid character escape sequence: \\x."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"bad \\u1 esc"')
    assert (
        u"Syntax Error GraphQL (1:7) Invalid character escape sequence: \\u1 es."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"bad \\u0XX1 esc"')
    assert (
        u"Syntax Error GraphQL (1:7) Invalid character escape sequence: \\u0XX1."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"bad \\uXXXX esc"')
    assert (
        u"Syntax Error GraphQL (1:7) Invalid character escape sequence: \\uXXXX"
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"bad \\uFXXX esc"')
    assert (
        u"Syntax Error GraphQL (1:7) Invalid character escape sequence: \\uFXXX."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u'"bad \\uXXXF esc"')
    assert (
        u"Syntax Error GraphQL (1:7) Invalid character escape sequence: \\uXXXF."
        in excinfo.value.message
    )


def test_lexes_numbers():
    # type: () -> None
    assert lex_one(u"4") == Token(TokenKind.INT, 0, 1, "4")
    assert lex_one(u"4.123") == Token(TokenKind.FLOAT, 0, 5, "4.123")
    assert lex_one(u"-4") == Token(TokenKind.INT, 0, 2, "-4")
    assert lex_one(u"9") == Token(TokenKind.INT, 0, 1, "9")
    assert lex_one(u"0") == Token(TokenKind.INT, 0, 1, "0")
    assert lex_one(u"-4.123") == Token(TokenKind.FLOAT, 0, 6, "-4.123")
    assert lex_one(u"0.123") == Token(TokenKind.FLOAT, 0, 5, "0.123")
    assert lex_one(u"123e4") == Token(TokenKind.FLOAT, 0, 5, "123e4")
    assert lex_one(u"123E4") == Token(TokenKind.FLOAT, 0, 5, "123E4")
    assert lex_one(u"123e-4") == Token(TokenKind.FLOAT, 0, 6, "123e-4")
    assert lex_one(u"123e+4") == Token(TokenKind.FLOAT, 0, 6, "123e+4")
    assert lex_one(u"-1.123e4") == Token(TokenKind.FLOAT, 0, 8, "-1.123e4")
    assert lex_one(u"-1.123E4") == Token(TokenKind.FLOAT, 0, 8, "-1.123E4")
    assert lex_one(u"-1.123e-4") == Token(TokenKind.FLOAT, 0, 9, "-1.123e-4")
    assert lex_one(u"-1.123e+4") == Token(TokenKind.FLOAT, 0, 9, "-1.123e+4")
    assert lex_one(u"-1.123e4567") == Token(TokenKind.FLOAT, 0, 11, "-1.123e4567")


def test_lex_reports_useful_number_errors():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"00")
    assert (
        u'Syntax Error GraphQL (1:2) Invalid number, unexpected digit after 0: "0".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"+1")
    assert (
        u'Syntax Error GraphQL (1:1) Unexpected character "+"' in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"1.")
    assert (
        u"Syntax Error GraphQL (1:3) Invalid number, expected digit but got: <EOF>."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u".123")
    assert (
        u'Syntax Error GraphQL (1:1) Unexpected character ".".' in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"1.A")
    assert (
        u'Syntax Error GraphQL (1:3) Invalid number, expected digit but got: "A".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"-A")
    assert (
        u'Syntax Error GraphQL (1:2) Invalid number, expected digit but got: "A".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"1.0e")
    assert (
        u"Syntax Error GraphQL (1:5) Invalid number, expected digit but got: <EOF>."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"1.0eA")
    assert (
        u'Syntax Error GraphQL (1:5) Invalid number, expected digit but got: "A".'
        in excinfo.value.message
    )


def test_lexes_punctuation():
    # type: () -> None
    assert lex_one(u"!") == Token(TokenKind.BANG, 0, 1)
    assert lex_one(u"$") == Token(TokenKind.DOLLAR, 0, 1)
    assert lex_one(u"(") == Token(TokenKind.PAREN_L, 0, 1)
    assert lex_one(u")") == Token(TokenKind.PAREN_R, 0, 1)
    assert lex_one(u"...") == Token(TokenKind.SPREAD, 0, 3)
    assert lex_one(u":") == Token(TokenKind.COLON, 0, 1)
    assert lex_one(u"=") == Token(TokenKind.EQUALS, 0, 1)
    assert lex_one(u"@") == Token(TokenKind.AT, 0, 1)
    assert lex_one(u"[") == Token(TokenKind.BRACKET_L, 0, 1)
    assert lex_one(u"]") == Token(TokenKind.BRACKET_R, 0, 1)
    assert lex_one(u"{") == Token(TokenKind.BRACE_L, 0, 1)
    assert lex_one(u"|") == Token(TokenKind.PIPE, 0, 1)
    assert lex_one(u"}") == Token(TokenKind.BRACE_R, 0, 1)


def test_lex_reports_useful_unknown_character_error():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"..")
    assert (
        u'Syntax Error GraphQL (1:1) Unexpected character "."' in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"?")
    assert (
        u'Syntax Error GraphQL (1:1) Unexpected character "?"' in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"\u203B")
    assert (
        u'Syntax Error GraphQL (1:1) Unexpected character "\\u203B"'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(u"\u200b")
    assert (
        u'Syntax Error GraphQL (1:1) Unexpected character "\\u200B"'
        in excinfo.value.message
    )


def test_lex_reports_useful_information_for_dashes_in_names():
    # type: () -> None
    q = u"a-b"
    lexer = Lexer(Source(q))
    first_token = lexer.next_token()
    assert first_token == Token(TokenKind.NAME, 0, 1, "a")
    with raises(GraphQLSyntaxError) as excinfo:
        lexer.next_token()

    assert (
        u'Syntax Error GraphQL (1:3) Invalid number, expected digit but got: "b".'
        in excinfo.value.message
    )
