import json

from six import unichr

from ..error import GraphQLSyntaxError

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Optional, Any, List
    from .source import Source

__all__ = ["Token", "Lexer", "TokenKind", "get_token_desc", "get_token_kind_desc"]


class Token(object):
    __slots__ = "kind", "start", "end", "value"

    def __init__(self, kind, start, end, value=None):
        # type: (int, int, int, Optional[str]) -> None
        self.kind = kind
        self.start = start
        self.end = end
        self.value = value

    def __repr__(self):
        # type: () -> str
        return u"<Token kind={} at {}..{} value={}>".format(
            get_token_kind_desc(self.kind), self.start, self.end, repr(self.value)
        )

    def __eq__(self, other):
        # type: (Any) -> bool
        return (
            isinstance(other, Token)
            and self.kind == other.kind
            and self.start == other.start
            and self.end == other.end
            and self.value == other.value
        )


class Lexer(object):
    __slots__ = "source", "prev_position"

    def __init__(self, source):
        # type: (Source) -> None
        self.source = source
        self.prev_position = 0

    def next_token(self, reset_position=None):
        # type: (Optional[int]) -> Token
        if reset_position is None:
            reset_position = self.prev_position
        token = read_token(self.source, reset_position)
        self.prev_position = token.end
        return token


class TokenKind(object):
    EOF = 1
    BANG = 2
    DOLLAR = 3
    PAREN_L = 4
    PAREN_R = 5
    SPREAD = 6
    COLON = 7
    EQUALS = 8
    AT = 9
    BRACKET_L = 10
    BRACKET_R = 11
    BRACE_L = 12
    PIPE = 13
    BRACE_R = 14
    NAME = 15
    VARIABLE = 16
    INT = 17
    FLOAT = 18
    STRING = 19


def get_token_desc(token):
    # type: (Token) -> str
    if token.value:
        return u'{} "{}"'.format(get_token_kind_desc(token.kind), token.value)
    else:
        return get_token_kind_desc(token.kind)


def get_token_kind_desc(kind):
    # type: (int) -> str
    return TOKEN_DESCRIPTION[kind]


TOKEN_DESCRIPTION = {
    TokenKind.EOF: "EOF",
    TokenKind.BANG: "!",
    TokenKind.DOLLAR: "$",
    TokenKind.PAREN_L: "(",
    TokenKind.PAREN_R: ")",
    TokenKind.SPREAD: "...",
    TokenKind.COLON: ":",
    TokenKind.EQUALS: "=",
    TokenKind.AT: "@",
    TokenKind.BRACKET_L: "[",
    TokenKind.BRACKET_R: "]",
    TokenKind.BRACE_L: "{",
    TokenKind.PIPE: "|",
    TokenKind.BRACE_R: "}",
    TokenKind.NAME: "Name",
    TokenKind.VARIABLE: "Variable",
    TokenKind.INT: "Int",
    TokenKind.FLOAT: "Float",
    TokenKind.STRING: "String",
}


def char_code_at(s, pos):
    # type: (str, int) -> Optional[int]
    if 0 <= pos < len(s):
        return ord(s[pos])

    return None


PUNCT_CODE_TO_KIND = {
    ord("!"): TokenKind.BANG,
    ord("$"): TokenKind.DOLLAR,
    ord("("): TokenKind.PAREN_L,
    ord(")"): TokenKind.PAREN_R,
    ord(":"): TokenKind.COLON,
    ord("="): TokenKind.EQUALS,
    ord("@"): TokenKind.AT,
    ord("["): TokenKind.BRACKET_L,
    ord("]"): TokenKind.BRACKET_R,
    ord("{"): TokenKind.BRACE_L,
    ord("|"): TokenKind.PIPE,
    ord("}"): TokenKind.BRACE_R,
}


def print_char_code(code):
    # type: (Optional[int]) -> str
    if code is None:
        return "<EOF>"

    if code < 0x007F:
        return json.dumps(unichr(code))

    return '"\\u%04X"' % code


def read_token(source, from_position):
    # type: (Source, int) -> Token
    """Gets the next token from the source starting at the given position.

    This skips over whitespace and comments until it finds the next lexable
    token, then lexes punctuators immediately or calls the appropriate
    helper fucntion for more complicated tokens."""
    body = source.body
    body_length = len(body)

    position = position_after_whitespace(body, from_position)

    if position >= body_length:
        return Token(TokenKind.EOF, position, position)

    code = char_code_at(body, position)
    if code:
        if code < 0x0020 and code not in (0x0009, 0x000A, 0x000D):
            raise GraphQLSyntaxError(
                source, position, u"Invalid character {}.".format(print_char_code(code))
            )

        kind = PUNCT_CODE_TO_KIND.get(code)
        if kind is not None:
            return Token(kind, position, position + 1)

        if code == 46:  # .
            if (
                char_code_at(body, position + 1)
                == char_code_at(body, position + 2)
                == 46
            ):
                return Token(TokenKind.SPREAD, position, position + 3)

        elif 65 <= code <= 90 or code == 95 or 97 <= code <= 122:
            # A-Z, _, a-z
            return read_name(source, position)

        elif code == 45 or 48 <= code <= 57:  # -, 0-9
            return read_number(source, position, code)

        elif code == 34:  # "
            return read_string(source, position)

    raise GraphQLSyntaxError(
        source, position, u"Unexpected character {}.".format(print_char_code(code))
    )


ignored_whitespace_characters = frozenset(
    [
        # BOM
        0xFEFF,
        # White Space
        0x0009,  # tab
        0x0020,  # space
        # Line Terminator
        0x000A,  # new line
        0x000D,  # carriage return
        # Comma
        0x002C,
    ]
)


def position_after_whitespace(body, start_position):
    # type: (str, int) -> int
    """Reads from body starting at start_position until it finds a
    non-whitespace or commented character, then returns the position of
    that character for lexing."""
    body_length = len(body)
    position = start_position
    while position < body_length:
        code = char_code_at(body, position)
        if code in ignored_whitespace_characters:
            position += 1

        elif code == 35:  # #, skip comments
            position += 1
            while position < body_length:
                code = char_code_at(body, position)
                if not (
                    code is not None
                    and (code > 0x001F or code == 0x0009)
                    and code not in (0x000A, 0x000D)
                ):
                    break

                position += 1
        else:
            break
    return position


def read_number(source, start, first_code):
    # type: (Source, int, Optional[int]) -> Token
    """Reads a number token from the source file, either a float
    or an int depending on whether a decimal point appears.

    Int:   -?(0|[1-9][0-9]*)
    Float: -?(0|[1-9][0-9]*)(\.[0-9]+)?((E|e)(+|-)?[0-9]+)?"""
    code = first_code
    body = source.body
    position = start
    is_float = False

    if code == 45:  # -
        position += 1
        code = char_code_at(body, position)

    if code == 48:  # 0
        position += 1
        code = char_code_at(body, position)

        if code is not None and 48 <= code <= 57:
            raise GraphQLSyntaxError(
                source,
                position,
                u"Invalid number, unexpected digit after 0: {}.".format(
                    print_char_code(code)
                ),
            )
    else:
        position = read_digits(source, position, code)
        code = char_code_at(body, position)

    if code == 46:  # .
        is_float = True

        position += 1
        code = char_code_at(body, position)
        position = read_digits(source, position, code)
        code = char_code_at(body, position)

    if code in (69, 101):  # E e
        is_float = True
        position += 1
        code = char_code_at(body, position)
        if code in (43, 45):  # + -
            position += 1
            code = char_code_at(body, position)

        position = read_digits(source, position, code)

    return Token(
        TokenKind.FLOAT if is_float else TokenKind.INT,
        start,
        position,
        body[start:position],
    )


def read_digits(source, start, first_code):
    # type: (Source, int, Optional[int]) -> int
    body = source.body
    position = start
    code = first_code

    if code is not None and 48 <= code <= 57:  # 0 - 9
        while True:
            position += 1
            code = char_code_at(body, position)

            if not (code is not None and 48 <= code <= 57):
                break

        return position

    raise GraphQLSyntaxError(
        source,
        position,
        u"Invalid number, expected digit but got: {}.".format(print_char_code(code)),
    )


ESCAPED_CHAR_CODES = {
    34: '"',
    47: "/",
    92: "\\",
    98: "\b",
    102: "\f",
    110: "\n",
    114: "\r",
    116: "\t",
}


def read_string(source, start):
    # type: (Source, int) -> Token
    """Reads a string token from the source file.

    "([^"\\\u000A\u000D\u2028\u2029]|(\\(u[0-9a-fA-F]{4}|["\\/bfnrt])))*"
    """
    body = source.body
    body_length = len(body)

    position = start + 1
    chunk_start = position
    code = 0  # type: Optional[int]
    value = []  # type: List[str]
    append = value.append

    while position < body_length:
        code = char_code_at(body, position)
        if code in (
            None,
            # LineTerminator
            0x000A,
            0x000D,
            # Quote
            34,
        ):
            break

        if code < 0x0020 and code != 0x0009:  # type: ignore
            raise GraphQLSyntaxError(
                source,
                position,
                u"Invalid character within String: {}.".format(print_char_code(code)),
            )

        position += 1
        if code == 92:  # \
            append(body[chunk_start : position - 1])

            code = char_code_at(body, position)
            escaped = ESCAPED_CHAR_CODES.get(code)  # type: ignore
            if escaped is not None:
                append(escaped)

            elif code == 117:  # u
                char_code = uni_char_code(
                    char_code_at(body, position + 1) or 0,
                    char_code_at(body, position + 2) or 0,
                    char_code_at(body, position + 3) or 0,
                    char_code_at(body, position + 4) or 0,
                )

                if char_code < 0:
                    raise GraphQLSyntaxError(
                        source,
                        position,
                        u"Invalid character escape sequence: \\u{}.".format(
                            body[position + 1 : position + 5]
                        ),
                    )

                append(unichr(char_code))
                position += 4
            else:
                raise GraphQLSyntaxError(
                    source,
                    position,
                    u"Invalid character escape sequence: \\{}.".format(
                        unichr(code)  # type: ignore
                    ),
                )

            position += 1
            chunk_start = position

    if code != 34:  # Quote (")
        raise GraphQLSyntaxError(source, position, "Unterminated string")

    append(body[chunk_start:position])
    return Token(TokenKind.STRING, start, position + 1, u"".join(value))


def uni_char_code(a, b, c, d):
    # type: (int, int, int, int) -> int
    """Converts four hexidecimal chars to the integer that the
    string represents. For example, uniCharCode('0','0','0','f')
    will return 15, and uniCharCode('0','0','f','f') returns 255.

    Returns a negative number on error, if a char was invalid.

    This is implemented by noting that char2hex() returns -1 on error,
    which means the result of ORing the char2hex() will also be negative.
    """
    return char2hex(a) << 12 | char2hex(b) << 8 | char2hex(c) << 4 | char2hex(d)


def char2hex(a):
    # type: (int) -> int
    """Converts a hex character to its integer value.
    '0' becomes 0, '9' becomes 9
    'A' becomes 10, 'F' becomes 15
    'a' becomes 10, 'f' becomes 15

    Returns -1 on error."""
    if 48 <= a <= 57:  # 0-9
        return a - 48
    elif 65 <= a <= 70:  # A-F
        return a - 55
    elif 97 <= a <= 102:  # a-f
        return a - 87
    return -1


def read_name(source, position):
    # type: (Source, int) -> Token
    """Reads an alphanumeric + underscore name from the source.

    [_A-Za-z][_0-9A-Za-z]*"""
    body = source.body
    body_length = len(body)
    end = position + 1

    while end != body_length:
        code = char_code_at(body, end)
        if not (
            code is not None
            and (
                code == 95
                or 48 <= code <= 57  # _
                or 65 <= code <= 90  # 0-9
                or 97 <= code <= 122  # A-Z  # a-z
            )
        ):
            break

        end += 1

    return Token(TokenKind.NAME, position, end, body[position:end])
