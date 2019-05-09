import functools
import inspect
import types
import warnings
import sys


def warn(msg):
    # type: (str) -> None
    warnings.simplefilter("always", DeprecationWarning)  # turn off filter
    warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
    warnings.simplefilter("default", DeprecationWarning)  # reset filter


class deprecated(object):
    def __init__(self, reason, name=None):
        if inspect.isclass(reason) or inspect.isfunction(reason):
            raise TypeError("Reason for deprecation must be supplied")
        self.reason = reason
        self.name = name

    def __call__(self, cls_or_func):
        if inspect.isfunction(cls_or_func):
            fmt = "Call to deprecated function or method {name} ({reason})."

        elif inspect.isclass(cls_or_func):
            fmt = "Call to deprecated class {name} ({reason})."

        else:
            raise TypeError(type(cls_or_func))

        msg = fmt.format(name=self.name or cls_or_func.__name__, reason=self.reason)

        @functools.wraps(cls_or_func)
        def new_func(*args, **kwargs):
            warn(msg)
            return cls_or_func(*args, **kwargs)

        return new_func


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = (str,)  # type: tuple
    integer_types = (int,)  # type: tuple
    class_types = (type,)  # type: tuple
    text_type = str
    binary_type = bytes
else:
    string_types = (basestring,)  # type: tuple
    integer_types = (int, long)  # type: tuple
    class_types = (type, types.ClassType)  # type: tuple
    text_type = unicode
    binary_type = str
