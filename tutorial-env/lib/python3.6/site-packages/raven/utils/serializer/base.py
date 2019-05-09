# -*- coding: utf-8 -*-
"""
raven.utils.serializer.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import collections
import itertools
import types

from raven.utils.compat import text_type, binary_type, string_types, iteritems, \
    class_types, PY2, PY3
from raven.utils.encoding import to_unicode
from .manager import manager as serialization_manager
from raven.utils import is_namedtuple


__all__ = ('Serializer',)


def has_sentry_metadata(value):
    try:
        return callable(value.__getattribute__('__sentry__'))
    except Exception:
        return False


class Serializer(object):
    types = ()

    def __init__(self, manager):
        self.manager = manager

    def can(self, value):
        """
        Given ``value``, return a boolean describing whether this
        serializer can operate on the given type
        """
        return isinstance(value, self.types)

    def serialize(self, value, **kwargs):
        """
        Given ``value``, coerce into a JSON-safe type.
        """
        return value

    def recurse(self, value, max_depth=6, _depth=0, **kwargs):
        """
        Given ``value``, recurse (using the parent serializer) to handle
        coercing of newly defined values.
        """
        string_max_length = kwargs.get('string_max_length', None)

        _depth += 1
        if _depth >= max_depth:
            try:
                value = text_type(repr(value))[:string_max_length]
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.manager.logger.exception(e)
                return text_type(type(value))
        return self.manager.transform(value, max_depth=max_depth,
                                      _depth=_depth, **kwargs)


class NamedtupleSerializer(Serializer):
    types = (collections.namedtuple,)

    def can(self, value):
        """
        Given ``value``, return a boolean describing whether this
        serializer can operate on the given type
        """
        return is_namedtuple(value)

    def serialize(self, value, **kwargs):
        list_max_length = kwargs.get('list_max_length') or float('inf')
        less_than = lambda x: x[0] < list_max_length
        items = value._asdict().items()
        takewhile = itertools.takewhile
        x = dict([
            (k, self.recurse(v, **kwargs))
            for n, (k, v) in takewhile(less_than, enumerate(items))
        ])
        return x


class IterableSerializer(Serializer):
    types = (tuple, list, set, frozenset)

    def serialize(self, value, **kwargs):
        list_max_length = kwargs.get('list_max_length') or float('inf')
        return tuple(
            self.recurse(o, **kwargs)
            for n, o
            in itertools.takewhile(lambda x: x[0] < list_max_length,
                                   enumerate(value))
        )


class DictSerializer(Serializer):
    types = (dict,)

    def make_key(self, key):
        if not isinstance(key, string_types):
            return to_unicode(key)
        return key

    def serialize(self, value, **kwargs):
        list_max_length = kwargs.get('list_max_length') or float('inf')
        return dict(
            (self.make_key(self.recurse(k, **kwargs)), self.recurse(v, **kwargs))
            for n, (k, v)
            in itertools.takewhile(lambda x: x[0] < list_max_length, enumerate(
                iteritems(value)))
        )


class UnicodeSerializer(Serializer):
    types = (text_type,)

    def serialize(self, value, **kwargs):
        # try to return a reasonable string that can be decoded
        # correctly by the server so it doesn't show up as \uXXX for each
        # unicode character
        # e.g. we want the output to be like: "u'רונית מגן'"
        string_max_length = kwargs.get('string_max_length', None)
        return repr(text_type('%s')) % (value[:string_max_length],)


class StringSerializer(Serializer):
    types = (binary_type,)

    def serialize(self, value, **kwargs):
        string_max_length = kwargs.get('string_max_length', None)
        if PY3:
            return repr(value[:string_max_length])

        try:
            # Python2 madness: let's try to recover from developer's issues
            # Try to process the string as if it was a unicode.
            return "'" + value.decode('utf8')[:string_max_length] \
                .encode('utf8') + "'"
        except UnicodeDecodeError:
            pass

        return repr(value[:string_max_length])


class TypeSerializer(Serializer):
    types = class_types

    def can(self, value):
        return not super(TypeSerializer, self).can(value) \
            and has_sentry_metadata(value)

    def serialize(self, value, **kwargs):
        return self.recurse(value.__sentry__(), **kwargs)


class BooleanSerializer(Serializer):
    types = (bool,)

    def serialize(self, value, **kwargs):
        return bool(value)


class FloatSerializer(Serializer):
    types = (float,)

    def serialize(self, value, **kwargs):
        return float(value)


class IntegerSerializer(Serializer):
    types = (int,)

    def serialize(self, value, **kwargs):
        return int(value)


class FunctionSerializer(Serializer):
    types = (types.FunctionType,)

    def serialize(self, value, **kwargs):
        return '<function %s from %s at 0x%x>' % (
            value.__name__, value.__module__, id(value))


if PY2:
    class LongSerializer(Serializer):
        types = (long,)  # noqa

        def serialize(self, value, **kwargs):
            return long(value)  # noqa


# register all serializers, order matters
serialization_manager.register(NamedtupleSerializer)
serialization_manager.register(IterableSerializer)
serialization_manager.register(DictSerializer)
serialization_manager.register(UnicodeSerializer)
serialization_manager.register(StringSerializer)
serialization_manager.register(TypeSerializer)
serialization_manager.register(BooleanSerializer)
serialization_manager.register(FloatSerializer)
serialization_manager.register(IntegerSerializer)
serialization_manager.register(FunctionSerializer)
if PY2:
    serialization_manager.register(LongSerializer)
