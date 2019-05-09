import re
import functools

try:
    from urllib.parse import quote
except ImportError:
    # Python 2
    from urllib import quote

from . import url


__all__ = ['Template', 'expand']


patterns = re.compile("{([^\}]+)}")


class Template(object):

    def __init__(self, url_str):
        self._base = url_str

    def __str__(self):
        return 'Template: %s' % self._base

    def expand(self, variables=None):
        return url.URL(expand(self._base, variables))


def expand(template, variables=None):
    """
    Expand a URL template string using the passed variables
    """
    if variables is None:
        variables = {}
    return patterns.sub(functools.partial(_replace, variables), template)


# Utils

def _flatten(container):
    """
    _flatten a sequence of sequences into a single list
    """
    _flattened = []
    for sequence in container:
        _flattened.extend(sequence)
    return _flattened

# Format functions
# ----------------
# These are responsible for formatting the (key, value) pair into a string


def _format_pair_no_equals(explode, separator, escape, key, value):
    """
    Format a key, value pair but don't include the equals sign
    when there is no value
    """
    if not value:
        return key
    return _format_pair(explode, separator, escape, key, value)


def _format_pair_with_equals(explode, separator, escape, key, value):
    """
    Format a key, value pair including the equals sign
    when there is no value
    """
    if not value:
        return key + '='
    return _format_pair(explode, separator, escape, key, value)


def _format_pair(explode, separator, escape, key, value):
    if isinstance(value, (list, tuple)):
        join_char = ","
        if explode:
            join_char = separator
        try:
            dict(value)
        except:
            # Scalar container
            if explode:
                items = ["%s=%s" % (key, escape(v)) for v in value]
                return join_char.join(items)
            else:
                escaped_value = join_char.join(map(escape, value))
        else:
            # Tuple container
            if explode:
                items = ["%s=%s" % (k, escape(v)) for (k, v) in value]
                return join_char.join(items)
            else:
                items = _flatten(value)
                escaped_value = join_char.join(map(escape, items))
    else:
        escaped_value = escape(value)
    return '%s=%s' % (key, escaped_value)


def _format_default(explode, separator, escape, key, value):
    if isinstance(value, (list, tuple)):
        join_char = ","
        if explode:
            join_char = separator
        try:
            dict(value)
        except:
            # Scalar container
            escaped_value = join_char.join(map(escape, value))
        else:
            # Tuple container
            if explode:
                items = ["%s=%s" % (k, escape(v)) for (k, v) in value]
                escaped_value = join_char.join(items)
            else:
                items = _flatten(value)
                escaped_value = join_char.join(map(escape, items))
    else:
        escaped_value = escape(value)
    return escaped_value


# Modifer functions
# -----------------
# These are responsible for modifying the variable before formatting

_identity = lambda x: x


def _truncate(string, num_chars):
    return string[:num_chars]


# Splitting functions
# -------------------
# These are responsible for splitting a string into a sequence of (key,
# modifier) tuples


def _split_basic(string):
    """
    Split a string into a list of tuples of the form (key, modifier_fn,
    explode) where modifier_fn is a function that applies the appropriate
    modification to the variable.
    """
    tuples = []
    for word in string.split(','):
        # Attempt to split on colon
        parts = word.split(':', 2)
        key, modifier_fn, explode = parts[0], _identity, False
        if len(parts) > 1:
            modifier_fn = functools.partial(
                _truncate, num_chars=int(parts[1]))
        if word[len(word) - 1] == '*':
            key = word[:len(word) - 1]
            explode = True
        tuples.append((key, modifier_fn, explode))
    return tuples


def _split_operator(string):
    return _split_basic(string[1:])


# Escaping functions
# ------------------


def _escape_all(value):
    return url.unicode_quote(value, safe="")


def _escape_reserved(value):
    return url.unicode_quote(value, safe="/!,.;")

# Operator map
# ------------
# A mapping of:
#     operator -> (prefix, separator, split_fn, escape_fn, format_fn)
operator_map = {
    '+': ('', ',', _split_operator, _escape_reserved, _format_default),
    '#': ('#', ',', _split_operator, _escape_reserved, _format_default),
    '.': ('.', '.', _split_operator, _escape_all, _format_default),
    '/': ('/', '/', _split_operator, _escape_all, _format_default),
    ';': (';', ';', _split_operator, _escape_all, _format_pair_no_equals),
    '?': ('?', '&', _split_operator, _escape_all, _format_pair_with_equals),
    '&': ('&', '&', _split_operator, _escape_all, _format_pair_with_equals),
}
defaults = ('', ',', _split_basic, _escape_all, _format_default)


def _replace(variables, match):
    """
    Return the appropriate replacement for `match` using the passed variables
    """
    expression = match.group(1)

    # Look-up chars and functions for the specified operator
    (prefix_char, separator_char, split_fn, escape_fn,
     format_fn) = operator_map.get(expression[0], defaults)

    replacements = []
    for key, modify_fn, explode in split_fn(expression):
        if key in variables:
            variable = modify_fn(variables[key])
            replacement = format_fn(
                explode, separator_char, escape_fn, key, variable)
            replacements.append(replacement)
    if not replacements:
        return ''
    return prefix_char + separator_char.join(replacements)
