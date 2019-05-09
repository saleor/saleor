# -*- coding: utf-8 -*-
"""Python 2/3 compatibility.

Compatibility implementations of features
only available in newer Python versions.
"""
from __future__ import absolute_import, unicode_literals

import errno
import io
import sys

try:
    from collections import Counter
except ImportError:  # pragma: no cover
    from collections import defaultdict

    def Counter():  # noqa
        """Create counter."""
        return defaultdict(int)

try:
    buffer_t = buffer
except NameError:  # pragma: no cover
    # Py3 does not have buffer, only use this for isa checks.

    class buffer_t(object):  # noqa
        """Python 3 does not have a buffer type."""

bytes_t = bytes

__all__ = [
    'Counter', 'reload', 'UserList', 'UserDict',
    'Callable', 'Iterable', 'Mapping',
    'Queue', 'Empty', 'Full', 'LifoQueue', 'builtins', 'array',
    'zip_longest', 'map', 'zip', 'string', 'string_t', 'bytes_t',
    'bytes_if_py2', 'long_t', 'text_t', 'int_types', 'module_name_t',
    'range', 'items', 'keys', 'values', 'nextfun', 'reraise',
    'WhateverIO', 'with_metaclass', 'StringIO', 'getfullargspec',
    'THREAD_TIMEOUT_MAX', 'format_d', 'monotonic', 'buffer_t',
    'python_2_unicode_compatible',
]


#  ############# py3k ########################################################
PY3 = sys.version_info[0] >= 3
PY2 = sys.version_info[0] < 3

try:
    reload = reload                         # noqa
except NameError:                           # pragma: no cover
    try:
        from importlib import reload        # noqa
    except ImportError:                     # pragma: no cover
        from imp import reload              # noqa

try:
    from collections import UserList        # noqa
except ImportError:                         # pragma: no cover
    from UserList import UserList           # noqa

try:
    from collections import UserDict        # noqa
except ImportError:                         # pragma: no cover
    from UserDict import UserDict           # noqa

try:
    from collections.abc import Callable    # noqa
except ImportError:                         # pragma: no cover
    from collections import Callable        # noqa

try:
    from collections.abc import Iterable    # noqa
except ImportError:                         # pragma: no cover
    from collections import Iterable        # noqa

try:
    from collections.abc import Mapping     # noqa
except ImportError:                         # pragma: no cover
    from collections import Mapping         # noqa

#  ############# time.monotonic #############################################

if sys.version_info < (3, 3):

    import platform
    SYSTEM = platform.system()

    try:
        import ctypes
    except ImportError:  # pragma: no cover
        ctypes = None  # noqa

    if SYSTEM == 'Darwin' and ctypes is not None:
        from ctypes.util import find_library
        libSystem = ctypes.CDLL(find_library('libSystem.dylib'))
        CoreServices = ctypes.CDLL(find_library('CoreServices'),
                                   use_errno=True)
        mach_absolute_time = libSystem.mach_absolute_time
        mach_absolute_time.restype = ctypes.c_uint64
        absolute_to_nanoseconds = CoreServices.AbsoluteToNanoseconds
        absolute_to_nanoseconds.restype = ctypes.c_uint64
        absolute_to_nanoseconds.argtypes = [ctypes.c_uint64]

        def _monotonic():
            return absolute_to_nanoseconds(mach_absolute_time()) * 1e-9

    elif SYSTEM == 'Linux' and ctypes is not None:
        # from stackoverflow:
        # questions/1205722/how-do-i-get-monotonic-time-durations-in-python
        import os

        CLOCK_MONOTONIC = 1  # see <linux/time.h>

        class timespec(ctypes.Structure):
            _fields_ = [
                ('tv_sec', ctypes.c_long),
                ('tv_nsec', ctypes.c_long),
            ]

        try:
            librt = ctypes.CDLL('librt.so.1', use_errno=True)
        except Exception:
            try:
                librt = ctypes.CDLL('librt.so.0', use_errno=True)
            except Exception as exc:
                error = OSError(
                    "Could not detect working librt library: {0}".format(
                        exc))
                error.errno = errno.ENOENT
                raise error
        clock_gettime = librt.clock_gettime
        clock_gettime.argtypes = [
            ctypes.c_int, ctypes.POINTER(timespec),
        ]

        def _monotonic():  # noqa
            t = timespec()
            if clock_gettime(CLOCK_MONOTONIC, ctypes.pointer(t)) != 0:
                errno_ = ctypes.get_errno()
                raise OSError(errno_, os.strerror(errno_))
            return t.tv_sec + t.tv_nsec * 1e-9
    else:
        from time import time as _monotonic
try:
    from time import monotonic
except ImportError:
    monotonic = _monotonic  # noqa

# ############# Py3 <-> Py2 #################################################

if PY3:  # pragma: no cover
    import builtins

    from array import array
    from queue import Queue, Empty, Full, LifoQueue
    from itertools import zip_longest

    map = map
    zip = zip
    string = str
    string_t = str
    long_t = int
    text_t = str
    range = range
    int_types = (int,)
    module_name_t = str

    def bytes_if_py2(s):
        """Convert str to bytes if running under Python 2."""
        return s

    def items(d):
        """Get dict items iterator."""
        return d.items()

    def keys(d):
        """Get dict keys iterator."""
        return d.keys()

    def values(d):
        """Get dict values iterator."""
        return d.values()

    def nextfun(it):
        """Get iterator next method."""
        return it.__next__

    exec_ = getattr(builtins, 'exec')

    def reraise(tp, value, tb=None):
        """Reraise exception."""
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

else:
    import __builtin__ as builtins  # noqa
    from array import array as _array
    from Queue import Queue, Empty, Full, LifoQueue  # noqa
    from itertools import (               # noqa
        imap as map,
        izip as zip,
        izip_longest as zip_longest,
    )

    string = unicode                # noqa
    string_t = basestring           # noqa
    text_t = unicode
    long_t = long                   # noqa
    range = xrange
    module_name_t = str
    int_types = (int, long)

    def array(typecode, *args, **kwargs):
        """Create array."""
        if isinstance(typecode, unicode):
            typecode = typecode.encode()
        return _array(typecode, *args, **kwargs)

    def bytes_if_py2(s):
        """Convert str to bytes if running under Python 2."""
        if isinstance(s, unicode):
            return s.encode()
        return s

    def items(d):                   # noqa
        """Return dict items iterator."""
        return d.iteritems()

    def keys(d):                    # noqa
        """Return dict key iterator."""
        return d.iterkeys()

    def values(d):                  # noqa
        """Return dict values iterator."""
        return d.itervalues()

    def nextfun(it):                # noqa
        """Return iterator next method."""
        return it.next

    def exec_(code, globs=None, locs=None):  # pragma: no cover
        """Execute code in a namespace."""
        if globs is None:
            frame = sys._getframe(1)
            globs = frame.f_globals
            if locs is None:
                locs = frame.f_locals
            del frame
        elif locs is None:
            locs = globs
        exec("""exec code in globs, locs""")

    exec_("""def reraise(tp, value, tb=None): raise tp, value, tb""")


def with_metaclass(Type, skip_attrs=None):
    """Class decorator to set metaclass.

    Works with both Python 2 and Python 3 and it does not add
    an extra class in the lookup order like ``six.with_metaclass`` does
    (that is -- it copies the original class instead of using inheritance).

    """
    if skip_attrs is None:
        skip_attrs = {'__dict__', '__weakref__'}

    def _clone_with_metaclass(Class):
        attrs = {key: value for key, value in items(vars(Class))
                 if key not in skip_attrs}
        return Type(Class.__name__, Class.__bases__, attrs)

    return _clone_with_metaclass


# ############# threading.TIMEOUT_MAX ########################################
try:
    from threading import TIMEOUT_MAX as THREAD_TIMEOUT_MAX
except ImportError:
    THREAD_TIMEOUT_MAX = 1e10  # noqa

# ############# format(int, ',d') ############################################

if sys.version_info >= (2, 7):  # pragma: no cover
    def format_d(i):
        """Format number."""
        return format(i, ',d')
else:  # pragma: no cover
    def format_d(i):  # noqa
        """Format number."""
        s = '%d' % i
        groups = []
        while s and s[-1].isdigit():
            groups.append(s[-3:])
            s = s[:-3]
        return s + ','.join(reversed(groups))

StringIO = io.StringIO
_SIO_write = StringIO.write
_SIO_init = StringIO.__init__


class WhateverIO(StringIO):
    """StringIO that takes bytes or str."""

    def __init__(self, v=None, *a, **kw):
        _SIO_init(self, v.decode() if isinstance(v, bytes) else v, *a, **kw)

    def write(self, data):
        _SIO_write(self, data.decode() if isinstance(data, bytes) else data)


def python_2_unicode_compatible(cls):
    """Class decorator to ensure class is compatible with Python 2."""
    return python_2_non_unicode_str(python_2_non_unicode_repr(cls))


def python_2_non_unicode_repr(cls):
    """Ensure cls.__repr__ returns unicode.

    A class decorator that ensures ``__repr__`` returns non-unicode
    when running under Python 2.
    """
    if PY2:
        try:
            cls.__dict__['__repr__']
        except KeyError:
            pass
        else:
            def __repr__(self, *args, **kwargs):
                return self.__unicode_repr__(*args, **kwargs).encode(
                    'utf-8', 'replace')
            cls.__unicode_repr__, cls.__repr__ = cls.__repr__, __repr__
    return cls


def python_2_non_unicode_str(cls):
    """Python 2 class string compatibility.

    A class decorator that defines ``__unicode__`` and ``__str__`` methods
    under Python 2.  Under Python 3 it does nothing.

    To support Python 2 and 3 with a single code base, define a ``__str__``
    method returning text and apply this decorator to the class.
    """
    if PY2:
        try:
            cls.__dict__['__str__']
        except KeyError:
            pass
        else:
            def __str__(self, *args, **kwargs):
                return self.__unicode__(*args, **kwargs).encode(
                    'utf-8', 'replace')
            cls.__unicode__, cls.__str__ = cls.__str__, __str__
    return cls


try:  # pragma: no cover
    from inspect import formatargspec, getfullargspec
except ImportError:  # Py2
    from collections import namedtuple
    from inspect import formatargspec, getargspec as _getargspec  # noqa

    FullArgSpec = namedtuple('FullArgSpec', (
        'args', 'varargs', 'varkw', 'defaults',
        'kwonlyargs', 'kwonlydefaults', 'annotations',
    ))

    def getfullargspec(fun, _fill=(None, ) * 3):  # noqa
        """For compatibility with Python 3."""
        s = _getargspec(fun)
        return FullArgSpec(*s + _fill)
