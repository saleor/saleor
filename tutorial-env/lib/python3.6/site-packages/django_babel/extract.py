# -*- coding: utf-8 -*-
from django.template.base import Lexer, TOKEN_TEXT, TOKEN_VAR, TOKEN_BLOCK
from django.utils.translation import trim_whitespace
from django.utils.encoding import smart_text

try:
    from django.utils.translation.trans_real import (
        inline_re, block_re, endblock_re, plural_re, constant_re)
except ImportError:
    # Django 1.11+
    from django.utils.translation.template import (
        inline_re, block_re, endblock_re, plural_re, constant_re)


def join_tokens(tokens, trim=False):
    message = ''.join(tokens)
    if trim:
        message = trim_whitespace(message)
    return message


def strip_quotes(s):
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s


def extract_django(fileobj, keywords, comment_tags, options):
    """Extract messages from Django template files.

    :param fileobj: the file-like object the messages should be extracted from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """
    intrans = False
    inplural = False
    trimmed = False
    message_context = None
    singular = []
    plural = []
    lineno = 1

    encoding = options.get('encoding', 'utf8')
    text = fileobj.read().decode(encoding)

    try:
        text_lexer = Lexer(text)
    except TypeError:
        # Django 1.9 changed the way we invoke Lexer; older versions
        # require two parameters.
        text_lexer = Lexer(text, None)

    for t in text_lexer.tokenize():
        lineno += t.contents.count('\n')
        if intrans:
            if t.token_type == TOKEN_BLOCK:
                endbmatch = endblock_re.match(t.contents)
                pluralmatch = plural_re.match(t.contents)
                if endbmatch:
                    if inplural:
                        if message_context:
                            yield (
                                lineno,
                                'npgettext',
                                [smart_text(message_context),
                                 smart_text(join_tokens(singular, trimmed)),
                                 smart_text(join_tokens(plural, trimmed))],
                                [],
                            )
                        else:
                            yield (
                                lineno,
                                'ngettext',
                                (smart_text(join_tokens(singular, trimmed)),
                                 smart_text(join_tokens(plural, trimmed))),
                                [])
                    else:
                        if message_context:
                            yield (
                                lineno,
                                'pgettext',
                                [smart_text(message_context),
                                 smart_text(join_tokens(singular, trimmed))],
                                [],
                            )
                        else:
                            yield (
                                lineno,
                                None,
                                smart_text(join_tokens(singular, trimmed)),
                                [])

                    intrans = False
                    inplural = False
                    message_context = None
                    singular = []
                    plural = []
                elif pluralmatch:
                    inplural = True
                else:
                    raise SyntaxError('Translation blocks must not include '
                                      'other block tags: %s' % t.contents)
            elif t.token_type == TOKEN_VAR:
                if inplural:
                    plural.append('%%(%s)s' % t.contents)
                else:
                    singular.append('%%(%s)s' % t.contents)
            elif t.token_type == TOKEN_TEXT:
                if inplural:
                    plural.append(t.contents)
                else:
                    singular.append(t.contents)
        else:
            if t.token_type == TOKEN_BLOCK:
                imatch = inline_re.match(t.contents)
                bmatch = block_re.match(t.contents)
                cmatches = constant_re.findall(t.contents)
                if imatch:
                    g = imatch.group(1)
                    g = strip_quotes(g)
                    message_context = imatch.group(3)
                    if message_context:
                        # strip quotes
                        message_context = message_context[1:-1]
                        yield (
                            lineno,
                            'pgettext',
                            [smart_text(message_context), smart_text(g)],
                            [],
                        )
                        message_context = None
                    else:
                        yield lineno, None, smart_text(g), []
                elif bmatch:
                    if bmatch.group(2):
                        message_context = bmatch.group(2)[1:-1]
                    for fmatch in constant_re.findall(t.contents):
                        stripped_fmatch = strip_quotes(fmatch)
                        yield lineno, None, smart_text(stripped_fmatch), []
                    intrans = True
                    inplural = False
                    trimmed = 'trimmed' in t.split_contents()
                    singular = []
                    plural = []
                elif cmatches:
                    for cmatch in cmatches:
                        stripped_cmatch = strip_quotes(cmatch)
                        yield lineno, None, smart_text(stripped_cmatch), []
            elif t.token_type == TOKEN_VAR:
                parts = t.contents.split('|')
                cmatch = constant_re.match(parts[0])
                if cmatch:
                    stripped_cmatch = strip_quotes(cmatch.group(1))
                    yield lineno, None, smart_text(stripped_cmatch), []
                for p in parts[1:]:
                    if p.find(':_(') >= 0:
                        p1 = p.split(':', 1)[1]
                        if p1[0] == '_':
                            p1 = p1[1:]
                        if p1[0] == '(':
                            p1 = p1.strip('()')
                        p1 = strip_quotes(p1)
                        yield lineno, None, smart_text(p1), []
