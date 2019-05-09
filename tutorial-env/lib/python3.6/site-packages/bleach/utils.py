from collections import OrderedDict

import six


def _attr_key(attr):
    """Returns appropriate key for sorting attribute names

    Attribute names are a tuple of ``(namespace, name)`` where namespace can be
    ``None`` or a string. These can't be compared in Python 3, so we conver the
    ``None`` to an empty string.

    """
    key = (attr[0][0] or ''), attr[0][1]
    return key


def alphabetize_attributes(attrs):
    """Takes a dict of attributes (or None) and returns them alphabetized"""
    if not attrs:
        return attrs

    return OrderedDict(
        [(k, v) for k, v in sorted(attrs.items(), key=_attr_key)]
    )


def force_unicode(text):
    """Takes a text (Python 2: str/unicode; Python 3: unicode) and converts to unicode

    :arg str/unicode text: the text in question

    :returns: text as unicode

    :raises UnicodeDecodeError: if the text was a Python 2 str and isn't in
        utf-8

    """
    # If it's already unicode, then return it
    if isinstance(text, six.text_type):
        return text

    # If not, convert it
    return six.text_type(text, 'utf-8', 'strict')
