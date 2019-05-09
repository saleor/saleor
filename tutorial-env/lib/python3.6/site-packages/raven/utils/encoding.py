"""
raven.utils.encoding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, unicode_literals

import warnings

from raven.utils.compat import integer_types, text_type, binary_type, \
    string_types, PY2


def is_protected_type(obj):
    """Determine if the object instance is of a protected type.

    Objects of protected types are preserved as-is when passed to
    force_text(strings_only=True).
    """
    import Decimal
    import datetime
    return isinstance(obj, integer_types + (type(None), float, Decimal,
        datetime.datetime, datetime.date, datetime.time))


def force_text(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_text, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first, saves 30-40% when s is an instance of
    # text_type. This function gets called often in that setting.
    if isinstance(s, text_type):
        return s
    if strings_only and is_protected_type(s):
        return s
    try:
        if not isinstance(s, string_types):
            if hasattr(s, '__unicode__'):
                s = s.__unicode__()
            else:
                if not PY2:
                    if isinstance(s, bytes):
                        s = text_type(s, encoding, errors)
                    else:
                        s = text_type(s)
                else:
                    s = text_type(bytes(s), encoding, errors)
        else:
            # Note: We use .decode() here, instead of text_type(s, encoding,
            # errors), so that if s is a SafeBytes, it ends up being a
            # SafeText at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError as e:
        if not isinstance(s, Exception):
            raise UnicodeDecodeError(*e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join([force_text(arg, encoding, strings_only,
                    errors) for arg in s])
    return s


def transform(value):
    from raven.utils.serializer import transform
    warnings.warn('You should switch to raven.utils.serializer.'
                  'transform', DeprecationWarning)

    return transform(value)


def to_unicode(value):
    try:
        value = text_type(force_text(value))
    except (UnicodeEncodeError, UnicodeDecodeError):
        value = '(Error decoding value)'
    except Exception:  # in some cases we get a different exception
        try:
            value = text_type(force_text(repr(type(value))))
        except Exception:
            value = '(Error decoding value)'
    return value


def to_string(value):
    try:
        return binary_type(value.decode('utf-8').encode('utf-8'))
    except Exception:
        return to_unicode(value).encode('utf-8')
