import base64
import ipaddress

import collections

from datetime import date, datetime

from dateutil import parser, tz
from six import itervalues, string_types, iteritems
from six.moves import map

from .utils import DslBase, ObjectBase, AttrDict, AttrList
from .exceptions import ValidationException

unicode = type(u'')

def construct_field(name_or_field, **params):
    # {"type": "text", "analyzer": "snowball"}
    if isinstance(name_or_field, collections.Mapping):
        if params:
            raise ValueError('construct_field() cannot accept parameters when passing in a dict.')
        params = name_or_field.copy()
        if 'type' not in params:
            # inner object can be implicitly defined
            if 'properties' in params:
                name = 'object'
            else:
                raise ValueError('construct_field() needs to have a "type" key.')
        else:
            name = params.pop('type')
        return Field.get_dsl_class(name)(**params)

    # Text()
    if isinstance(name_or_field, Field):
        if params:
            raise ValueError('construct_field() cannot accept parameters when passing in a construct_field object.')
        return name_or_field

    # "text", analyzer="snowball"
    return Field.get_dsl_class(name_or_field)(**params)

class Field(DslBase):
    _type_name = 'field'
    _type_shortcut = staticmethod(construct_field)
    # all fields can be multifields
    _param_defs = {'fields': {'type': 'field', 'hash': True}}
    name = None
    _coerce = False

    def __init__(self, *args, **kwargs):
        self._multi = kwargs.pop('multi', False)
        self._required = kwargs.pop('required', False)
        super(Field, self).__init__(*args, **kwargs)

    def __getitem__(self, subfield):
        return self._params.get('fields', {})[subfield]

    def _serialize(self, data):
        return data

    def _deserialize(self, data):
        return data

    def _empty(self):
        return None

    def empty(self):
        if self._multi:
            return AttrList([])
        return self._empty()

    def serialize(self, data):
        if isinstance(data, (list, AttrList)):
            return list(map(self._serialize, data))
        return self._serialize(data)

    def deserialize(self, data):
        if isinstance(data, (list, AttrList)):
            data[:] = [
                None if d is None else self._deserialize(d)
                for d in data
            ]
            return data
        if data is None:
            return None
        return self._deserialize(data)

    def clean(self, data):
        if data is not None:
            data = self.deserialize(data)
        if data in (None, [], {}) and self._required:
            raise ValidationException("Value required for this field.")
        return data

    def to_dict(self):
        d = super(Field, self).to_dict()
        name, value = d.popitem()
        value['type'] = name
        return value

class CustomField(Field):
    name = 'custom'
    _coerce = True

    def to_dict(self):
        if isinstance(self.builtin_type, Field):
            return self.builtin_type.to_dict()

        d = super(CustomField, self).to_dict()
        d['type'] = self.builtin_type
        return d

class Object(Field):
    name = 'object'
    _coerce = True

    def __init__(self, doc_class=None, **kwargs):
        self._doc_class = doc_class
        if doc_class is None:
            # FIXME import
            from .document import InnerDoc
            # no InnerDoc subclass, creating one instead...
            self._doc_class = type('InnerDoc', (InnerDoc, ), {})
            for name, field in iteritems(kwargs.pop('properties', {})):
                self._doc_class._doc_type.mapping.field(name, field)
            if 'dynamic' in kwargs:
                self._doc_class._doc_type.mapping.meta('dynamic', kwargs.pop('dynamic'))

        self._mapping = self._doc_class._doc_type.mapping
        super(Object, self).__init__(**kwargs)

    def __getitem__(self, name):
        return self._mapping[name]

    def __contains__(self, name):
        return name in self._mapping

    def _empty(self):
        return self._wrap({})

    def _wrap(self, data):
        return self._doc_class(**data)

    def empty(self):
        if self._multi:
            return AttrList([], self._wrap)
        return self._empty()

    def to_dict(self):
        d = self._mapping.to_dict()
        _, d = d.popitem()
        d["type"] = self.name
        return d

    def _collect_fields(self):
        return self._mapping.properties._collect_fields()

    def _deserialize(self, data):
        # don't wrap already wrapped data
        if isinstance(data, self._doc_class):
            return data

        if isinstance(data, AttrDict):
            data = data._d_

        return self._wrap(data)

    def _serialize(self, data):
        if data is None:
            return None

        # somebody assigned raw dict to the field, we should tolerate that
        if isinstance(data, collections.Mapping):
            return data

        return data.to_dict()

    def clean(self, data):
        data = super(Object, self).clean(data)
        if data is None:
            return None
        if isinstance(data, (list, AttrList)):
            for d in data:
                d.full_clean()
        else:
            data.full_clean()
        return data

    def update(self, other):
        if not isinstance(other, Object):
            # not an inner/nested object, no merge possible
            return

        self._mapping.update(other._mapping)

class Nested(Object):
    name = 'nested'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('multi', True)
        super(Nested, self).__init__(*args, **kwargs)

class Date(Field):
    name = 'date'
    _coerce = True

    def __init__(self, *args, **kwargs):
        self._default_timezone = kwargs.pop('default_timezone', None)
        if isinstance(self._default_timezone, string_types):
            self._default_timezone = tz.gettz(self._default_timezone)
        super(Date, self).__init__(*args, **kwargs)

    def _deserialize(self, data):
        if isinstance(data, string_types):
            try:
                data = parser.parse(data)
            except Exception as e:
                raise ValidationException('Could not parse date from the value (%r)' % data, e)

        if isinstance(data, datetime):
            if self._default_timezone and data.tzinfo is None:
                data = data.replace(tzinfo=self._default_timezone)
            return data
        if isinstance(data, date):
            return data
        if isinstance(data, int):
            # Divide by a float to preserve milliseconds on the datetime.
            return datetime.utcfromtimestamp(data / 1000.0)

        raise ValidationException('Could not parse date from the value (%r)' % data)

class String(Field):
    _param_defs = {
        'fields': {'type': 'field', 'hash': True},
        'analyzer': {'type': 'analyzer'},
        'search_analyzer': {'type': 'analyzer'},
    }
    name = 'string'

class Text(Field):
    _param_defs = {
        'fields': {'type': 'field', 'hash': True},
        'analyzer': {'type': 'analyzer'},
        'search_analyzer': {'type': 'analyzer'},
        'search_quote_analyzer': {'type': 'analyzer'},
    }
    name = 'text'

class Keyword(Field):
    _param_defs = {
        'fields': {'type': 'field', 'hash': True},
        'search_analyzer': {'type': 'analyzer'},
        'normalizer': {'type': 'normalizer'}
    }
    name = 'keyword'

class Boolean(Field):
    name = 'boolean'
    _coerce = True

    def _deserialize(self, data):
        if data == "false":
            return False
        return bool(data)

    def clean(self, data):
        if data is not None:
            data = self.deserialize(data)
        if data is None and self._required:
            raise ValidationException("Value required for this field.")
        return data

class Float(Field):
    name = 'float'
    _coerce = True

    def _deserialize(self, data):
        return float(data)

class HalfFloat(Float):
    name = 'half_float'

class ScaledFloat(Float):
    name = 'scaled_float'

    def __init__(self, scaling_factor, *args, **kwargs):
        super(ScaledFloat, self).__init__(scaling_factor=scaling_factor, *args, **kwargs)

class Double(Float):
    name = 'double'

class Integer(Field):
    name = 'integer'
    _coerce = True

    def _deserialize(self, data):
        return int(data)

class Byte(Integer):
    name = 'byte'

class Short(Integer):
    name = 'short'

class Long(Integer):
    name = 'long'

class Ip(Field):
    name = 'ip'
    _coerce = True

    def _deserialize(self, data):
        # the ipaddress library for pypy, python2.5 and 2.6 only accepts unicode.
        return ipaddress.ip_address(unicode(data))

    def _serialize(self, data):
        if data is None:
            return None
        return str(data)

class Binary(Field):
    name = 'binary'
    _coerce = True

    def _deserialize(self, data):
        return base64.b64decode(data)

    def _serialize(self, data):
        if data is None:
            return None
        return base64.b64encode(data)

class GeoPoint(Field):
    name = 'geo_point'

class GeoShape(Field):
    name = 'geo_shape'

class Completion(Field):
    name = 'completion'

class Percolator(Field):
    name = 'percolator'

class IntegerRange(Field):
    name = 'integer_range'

class FloatRange(Field):
    name = 'float_range'

class LongRange(Field):
    name = 'long_range'

class DoubleRange(Field):
    name = 'double_ranged'

class DateRange(Field):
    name = 'date_range'

class Join(Field):
    name = 'join'

class TokenCount(Field):
    name = 'token_count'

class Murmur3(Field):
    name = 'murmur3'
