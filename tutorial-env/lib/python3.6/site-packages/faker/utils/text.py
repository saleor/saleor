# coding=utf-8

import re

import six
import unicodedata


_re_pattern = re.compile(r'[^\w\s-]', flags=re.U)
_re_pattern_allow_dots = re.compile(r'[^\.\w\s-]', flags=re.U)
_re_spaces = re.compile(r'[-\s]+', flags=re.U)


def slugify(value, allow_dots=False, allow_unicode=False):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace. Modified to optionally allow dots.

    Adapted from Django 1.9
    """
    if allow_dots:
        pattern = _re_pattern_allow_dots
    else:
        pattern = _re_pattern

    value = six.text_type(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
        value = pattern.sub('', value).strip().lower()
        return _re_spaces.sub('-', value)
    value = unicodedata.normalize('NFKD', value).encode(
        'ascii', 'ignore').decode('ascii')
    value = pattern.sub('', value).strip().lower()
    return _re_spaces.sub('-', value)
