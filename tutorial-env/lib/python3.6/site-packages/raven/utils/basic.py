from __future__ import absolute_import

try:
    from collections.abc import Mapping
except ImportError:
    # Python < 3.3
    from collections import Mapping

from functools import update_wrapper
import threading

from raven.utils.compat import iteritems


def merge_dicts(*dicts):
    out = {}
    for d in dicts:
        if not d:
            continue

        for k, v in iteritems(d):
            out[k] = v
    return out


def varmap(func, var, context=None, name=None):
    """
    Executes ``func(key_name, value)`` on all values
    recurisively discovering dict and list scoped
    values.
    """
    if context is None:
        context = {}
    objid = id(var)
    if objid in context:
        return func(name, '<...>')
    context[objid] = 1

    if isinstance(var, (list, tuple)) and not is_namedtuple(var):
        ret = [varmap(func, f, context, name) for f in var]
    else:
        ret = func(name, var)
        if isinstance(ret, Mapping):
            ret = dict((k, varmap(func, v, context, k))
                       for k, v in iteritems(var))
    del context[objid]
    return ret


class memoize(object):
    """
    Memoize the result of a property call.

    >>> class A(object):
    >>>     @memoize
    >>>     def func(self):
    >>>         return 'foo'
    """

    def __init__(self, func):
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        d, n = vars(obj), self.__name__
        if n not in d:
            d[n] = self.func(obj)
        return d[n]


def once(func):
    """Runs a thing once and once only."""
    lock = threading.Lock()

    def new_func(*args, **kwargs):
        if new_func.called:
            return
        with lock:
            if new_func.called:
                return
            rv = func(*args, **kwargs)
            new_func.called = True
            return rv

    new_func = update_wrapper(new_func, func)
    new_func.called = False
    return new_func


def is_namedtuple(value):
    # https://stackoverflow.com/a/2166841/1843746
    # But modified to handle subclasses of namedtuples.
    if not isinstance(value, tuple):
        return False
    f = getattr(type(value), '_fields', None)
    if not isinstance(f, tuple):
        return False
    return all(type(n) == str for n in f)
