from __future__ import unicode_literals

import collections

from six import iteritems, add_metaclass
from six.moves import map

from .exceptions import UnknownDslObject, ValidationException

SKIP_VALUES = ('', None)
EXPAND__TO_DOT=True

DOC_META_FIELDS = frozenset((
    'id', 'routing', 'version', 'version_type'
))

META_FIELDS = frozenset((
    # Elasticsearch metadata fields, except 'type'
    'index', 'using', 'score',
)).union(DOC_META_FIELDS)

def _wrap(val, obj_wrapper=None):
    if isinstance(val, collections.Mapping):
        return AttrDict(val) if obj_wrapper is None else obj_wrapper(val)
    if isinstance(val, list):
        return AttrList(val)
    return val

class AttrList(object):
    def __init__(self, l, obj_wrapper=None):
        # make iterables into lists
        if not isinstance(l, list):
            l = list(l)
        self._l_ = l
        self._obj_wrapper = obj_wrapper

    def __repr__(self):
        return repr(self._l_)

    def __eq__(self, other):
        if isinstance(other, AttrList):
            return other._l_ == self._l_
        # make sure we still equal to a dict with the same data
        return other == self._l_

    def __ne__(self, other):
        return not self == other

    def __getitem__(self, k):
        l = self._l_[k]
        if isinstance(k, slice):
            return AttrList(l, obj_wrapper=self._obj_wrapper)
        return _wrap(l, self._obj_wrapper)

    def __setitem__(self, k, value):
        self._l_[k] = value

    def __iter__(self):
        return map(lambda i: _wrap(i, self._obj_wrapper), self._l_)

    def __len__(self):
        return len(self._l_)

    def __nonzero__(self):
        return bool(self._l_)
    __bool__ = __nonzero__

    def __getattr__(self, name):
        return getattr(self._l_, name)

    def __getstate__(self):
        return (self._l_, self._obj_wrapper)

    def __setstate__(self, state):
        self._l_, self._obj_wrapper = state


class AttrDict(object):
    """
    Helper class to provide attribute like access (read and write) to
    dictionaries. Used to provide a convenient way to access both results and
    nested dsl dicts.
    """
    def __init__(self, d):
        # assign the inner dict manually to prevent __setattr__ from firing
        super(AttrDict, self).__setattr__('_d_', d)

    def __contains__(self, key):
        return key in self._d_

    def __nonzero__(self):
        return bool(self._d_)
    __bool__ = __nonzero__

    def __dir__(self):
        # introspection for auto-complete in IPython etc
        return list(self._d_.keys())

    def __eq__(self, other):
        if isinstance(other, AttrDict):
            return other._d_ == self._d_
        # make sure we still equal to a dict with the same data
        return other == self._d_

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        r = repr(self._d_)
        if len(r) > 60:
            r = r[:60] + '...}'
        return r

    def __getstate__(self):
        return (self._d_, )

    def __setstate__(self, state):
        super(AttrDict, self).__setattr__('_d_', state[0])

    def __getattr__(self, attr_name):
        try:
            return self.__getitem__(attr_name)
        except KeyError:
            raise AttributeError(
                '%r object has no attribute %r' % (self.__class__.__name__, attr_name))

    def __delattr__(self, attr_name):
        try:
            del self._d_[attr_name]
        except KeyError:
            raise AttributeError(
                '%r object has no attribute %r' % (self.__class__.__name__, attr_name))

    def __getitem__(self, key):
        return _wrap(self._d_[key])

    def __setitem__(self, key, value):
        self._d_[key] = value

    def __delitem__(self, key):
        del self._d_[key]

    def __setattr__(self, name, value):
        if name in self._d_ or not hasattr(self.__class__, name):
            self._d_[name] = value
        else:
            # there is an attribute on the class (could be property, ..) - don't add it as field
            super(AttrDict, self).__setattr__(name, value)

    def __iter__(self):
        return iter(self._d_)

    def to_dict(self):
        return self._d_


class DslMeta(type):
    """
    Base Metaclass for DslBase subclasses that builds a registry of all classes
    for given DslBase subclass (== all the query types for the Query subclass
    of DslBase).

    It then uses the information from that registry (as well as `name` and
    `shortcut` attributes from the base class) to construct any subclass based
    on it's name.

    For typical use see `QueryMeta` and `Query` in `elasticsearch_dsl.query`.
    """
    _types = {}
    def __init__(cls, name, bases, attrs):
        super(DslMeta, cls).__init__(name, bases, attrs)
        # skip for DslBase
        if not hasattr(cls, '_type_shortcut'):
            return
        if cls.name is None:
            # abstract base class, register it's shortcut
            cls._types[cls._type_name] = cls._type_shortcut
            # and create a registry for subclasses
            if not hasattr(cls, '_classes'):
                cls._classes = {}
        elif cls.name not in cls._classes:
            # normal class, register it
            cls._classes[cls.name] = cls

    @classmethod
    def get_dsl_type(cls, name):
        try:
            return cls._types[name]
        except KeyError:
            raise UnknownDslObject('DSL type %s does not exist.' % name)


@add_metaclass(DslMeta)
class DslBase(object):
    """
    Base class for all DSL objects - queries, filters, aggregations etc. Wraps
    a dictionary representing the object's json.

    Provides several feature:
        - attribute access to the wrapped dictionary (.field instead of ['field'])
        - _clone method returning a deep copy of self
        - to_dict method to serialize into dict (to be sent via elasticsearch-py)
        - basic logical operators (&, | and ~) using a Bool(Filter|Query) TODO:
          move into a class specific for Query/Filter
        - respects the definition of the class and (de)serializes it's
          attributes based on the `_param_defs` definition (for example turning
          all values in the `must` attribute into Query objects)
    """
    _param_defs = {}

    @classmethod
    def get_dsl_class(cls, name):
        try:
            return cls._classes[name]
        except KeyError:
            raise UnknownDslObject('DSL class `%s` does not exist in %s.' % (name, cls._type_name))

    def __init__(self, _expand__to_dot=EXPAND__TO_DOT, **params):
        self._params = {}
        for pname, pvalue in iteritems(params):
            if '__' in pname and _expand__to_dot:
                pname = pname.replace('__', '.')
            self._setattr(pname, pvalue)

    def _repr_params(self):
        """ Produce a repr of all our parameters to be used in __repr__. """
        return ', '.join(
            '%s=%r' % (n.replace('.', '__'), v)
            for (n, v) in sorted(iteritems(self._params))
            # make sure we don't include empty typed params
            if 'type' not in self._param_defs.get(n, {}) or v
        )

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            self._repr_params()
        )

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.to_dict() == self.to_dict()

    def __ne__(self, other):
        return not self == other

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super(DslBase, self).__setattr__(name, value)
        return self._setattr(name, value)

    def _setattr(self, name, value):
        # if this attribute has special type assigned to it...
        if name in self._param_defs:
            pinfo = self._param_defs[name]

            if 'type' in pinfo:
                # get the shortcut used to construct this type (query.Q, aggs.A, etc)
                shortcut = self.__class__.get_dsl_type(pinfo['type'])
                if pinfo.get('multi'):
                    if not isinstance(value, (tuple, list)):
                        value = (value, )
                    value = list(map(shortcut, value))

                # dict(name -> DslBase), make sure we pickup all the objs
                elif pinfo.get('hash'):
                    value = dict((k, shortcut(v)) for (k, v) in iteritems(value))

                # single value object, just convert
                else:
                    value = shortcut(value)
        self._params[name] = value

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(
                '%r object has no attribute %r' % (self.__class__.__name__, name))

        value = None
        try:
            value = self._params[name]
        except KeyError:
            # compound types should never throw AttributeError and return empty
            # container instead
            if name in self._param_defs:
                pinfo = self._param_defs[name]
                if pinfo.get('multi'):
                    value = self._params.setdefault(name, [])
                elif pinfo.get('hash'):
                    value = self._params.setdefault(name, {})
        if value is None:
            raise AttributeError(
                '%r object has no attribute %r' % (self.__class__.__name__, name))

        # wrap nested dicts in AttrDict for convenient access
        if isinstance(value, collections.Mapping):
            return AttrDict(value)
        return value

    def to_dict(self):
        """
        Serialize the DSL object to plain dict
        """
        d = {}
        for pname, value in iteritems(self._params):
            pinfo = self._param_defs.get(pname)

            # typed param
            if pinfo and 'type' in pinfo:
                # don't serialize empty lists and dicts for typed fields
                if value in ({}, []):
                    continue

                # multi-values are serialized as list of dicts
                if pinfo.get('multi'):
                    value = list(map(lambda x: x.to_dict(), value))

                # squash all the hash values into one dict
                elif pinfo.get('hash'):
                    value = dict((k, v.to_dict()) for k, v in iteritems(value))

                # serialize single values
                else:
                    value = value.to_dict()

            # serialize anything with to_dict method
            elif hasattr(value, 'to_dict'):
                value = value.to_dict()

            d[pname] = value
        return {self.name: d}

    def _clone(self):
        return self._type_shortcut(self.to_dict())


class ObjectBase(AttrDict):
    def __init__(self, **kwargs):
        super(ObjectBase, self).__init__(kwargs)

    @classmethod
    def from_es(cls, hit):
        meta = hit.copy()
        doc = meta.pop('_source', {})
        if 'fields' in meta:
            for k, v in iteritems(meta.pop('fields')):
                if k.startswith('_') and k[1:] in META_FIELDS:
                    meta[k] = v
                else:
                    doc[k] = v

        m = cls._doc_type.mapping
        for k in m:
            if k in doc and m[k]._coerce:
                doc[k] = m[k].deserialize(doc[k])
        return cls(meta=meta, **doc)

    def __getattr__(self, name):
        try:
            return super(ObjectBase, self).__getattr__(name)
        except AttributeError:
            if name in self._doc_type.mapping:
                f = self._doc_type.mapping[name]
                if hasattr(f, 'empty'):
                    value = f.empty()
                    if value not in SKIP_VALUES:
                        setattr(self, name, value)
                        value = getattr(self, name)
                    return value
            raise

    def to_dict(self):
        out = {}
        for k, v in iteritems(self._d_):
            try:
                f = self._doc_type.mapping[k]
            except KeyError:
                pass
            else:
                if f._coerce:
                    v = f.serialize(v)

            # if someone assigned AttrList, unwrap it
            if isinstance(v, AttrList):
                v = v._l_

            # don't serialize empty values
            # careful not to include numeric zeros
            if v in ([], {}, None):
                continue

            out[k] = v
        return out

    def clean_fields(self):
        errors = {}
        for name in self._doc_type.mapping:
            field = self._doc_type.mapping[name]
            data = self._d_.get(name, None)
            try:
                # save the cleaned value
                data = field.clean(data)
            except ValidationException as e:
                errors.setdefault(name, []).append(e)

            if name in self._d_ or data not in ([], {}, None):
                self._d_[name] = data

        if errors:
            raise ValidationException(errors)

    def clean(self):
        pass

    def full_clean(self):
        self.clean_fields()
        self.clean()

def merge(data, new_data):
    if not (isinstance(data, (AttrDict, collections.Mapping))
            and isinstance(new_data, (AttrDict, collections.Mapping))):
        raise ValueError('You can only merge two dicts! Got %r and %r instead.' % (data, new_data))

    for key, value in iteritems(new_data):
        if key in data and isinstance(getattr(data, key), (AttrDict, collections.Mapping)) and \
                isinstance(value, (AttrDict, collections.Mapping)):
            merge(getattr(data, key), value)
        else:
            setattr(data, key, value)
