from __future__ import unicode_literals


def serialize(nodes):
    """Serialize nodes to CSS syntax.

    This should be used for :term:`component values`
    instead of just :meth:`~tinycss2.ast.Node.serialize` on each node
    as it takes care of corner cases such as ``;`` between declarations,
    and consecutive identifiers
    that would otherwise parse back as the same token.

    :param nodes: an iterable of :class:`~tinycss2.ast.Node` objects
    :returns: an Unicode string

    """
    chunks = []
    _serialize_to(nodes, chunks.append)
    return ''.join(chunks)


def serialize_identifier(value):
    """Serialize any string as a CSS identifier

    :param value: a :term:`string`
    :returns:
        an Unicode string
        that would parse as an :class:`~tinycss2.ast.IdentToken`
        whose :attr:`~tinycss2.ast.IdentToken.value` attribute
        equals the passed :obj:`value` argument.

    """
    if value == '-':
        return r'\-'

    if value[:2] == '--':
        return '--' + serialize_name(value[2:])

    if value[0] == '-':
        result = '-'
        value = value[1:]
    else:
        result = ''
    c = value[0]
    result += (
        c if c in ('abcdefghijklmnopqrstuvwxyz_'
                   'ABCDEFGHIJKLMNOPQRSTUVWXYZ') or ord(c) > 0x7F else
        r'\A ' if c == '\n' else
        r'\D ' if c == '\r' else
        r'\C ' if c == '\f' else
        '\\%X ' % ord(c) if c in '0123456789' else
        '\\' + c
    )
    result += serialize_name(value[1:])
    return result


def serialize_name(value):
    return ''.join(
        c if c in ('abcdefghijklmnopqrstuvwxyz-_0123456789'
                   'ABCDEFGHIJKLMNOPQRSTUVWXYZ') or ord(c) > 0x7F else
        r'\A ' if c == '\n' else
        r'\D ' if c == '\r' else
        r'\C ' if c == '\f' else
        '\\' + c
        for c in value
    )


def serialize_string_value(value):
    return ''.join(
        r'\"' if c == '"' else
        r'\\' if c == '\\' else
        r'\A ' if c == '\n' else
        r'\D ' if c == '\r' else
        r'\C ' if c == '\f' else
        c
        for c in value
    )


# http://dev.w3.org/csswg/css-syntax/#serialization-tables
def _serialize_to(nodes, write):
    """Serialize an iterable of nodes to CSS syntax,
    writing chunks as Unicode string
    by calling the provided :obj:`write` callback.

    """
    bad_pairs = BAD_PAIRS
    previous_type = None
    for node in nodes:
        serialization_type = (node.type if node.type != 'literal'
                              else node.value)
        if (previous_type, serialization_type) in bad_pairs:
            write('/**/')
        elif previous_type == '\\' and not (
                serialization_type == 'whitespace' and
                node.value.startswith('\n')):
            write('\n')
        node._serialize_to(write)
        if serialization_type == 'declaration':
            write(';')
        previous_type = serialization_type


BAD_PAIRS = set(
    [(a, b)
        for a in ('ident', 'at-keyword', 'hash', 'dimension', '#', '-',
                  'number')
        for b in ('ident', 'function', 'url', 'number', 'percentage',
                  'dimension', 'unicode-range')] +
    [(a, b)
        for a in ('ident', 'at-keyword', 'hash', 'dimension')
        for b in ('-', '-->')] +
    [(a, b)
        for a in ('#', '-', 'number', '@')
        for b in ('ident', 'function', 'url')] +
    [(a, b)
        for a in ('unicode-range', '.', '+')
        for b in ('number', 'percentage', 'dimension')] +
    [('@', b) for b in ('ident', 'function', 'url', 'unicode-range', '-')] +
    [('unicode-range', b) for b in ('ident', 'function', '?')] +
    [(a, '=') for a in '$*^~|'] +
    [('ident', '() block'), ('|', '|'), ('/', '*')]
)
