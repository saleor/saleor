"""
SymPy core decorators.

The purpose of this module is to expose decorators without any other
dependencies, so that they can be easily imported anywhere in sympy/core.
"""

from __future__ import print_function, division

from functools import wraps
from .sympify import SympifyError, sympify
from sympy.core.compatibility import get_function_code


def deprecated(**decorator_kwargs):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    from sympy.utilities.exceptions import SymPyDeprecationWarning

    def _warn_deprecation(wrapped, stacklevel):
        decorator_kwargs.setdefault('feature', wrapped.__name__)
        SymPyDeprecationWarning(**decorator_kwargs).warn(stacklevel=stacklevel)

    def deprecated_decorator(wrapped):
        if hasattr(wrapped, '__mro__'):  # wrapped is actually a class
            class wrapper(wrapped):
                __doc__ = wrapped.__doc__
                __name__ = wrapped.__name__
                __module__ = wrapped.__module__
                _sympy_deprecated_func = wrapped
                def __init__(self, *args, **kwargs):
                    _warn_deprecation(wrapped, 4)
                    super(wrapper, self).__init__(*args, **kwargs)
        else:
            @wraps(wrapped)
            def wrapper(*args, **kwargs):
                _warn_deprecation(wrapped, 3)
                return wrapped(*args, **kwargs)
            wrapper._sympy_deprecated_func = wrapped
        return wrapper
    return deprecated_decorator


def _sympifyit(arg, retval=None):
    """decorator to smartly _sympify function arguments

       @_sympifyit('other', NotImplemented)
       def add(self, other):
           ...

       In add, other can be thought of as already being a SymPy object.

       If it is not, the code is likely to catch an exception, then other will
       be explicitly _sympified, and the whole code restarted.

       if _sympify(arg) fails, NotImplemented will be returned

       see: __sympifyit
    """
    def deco(func):
        return __sympifyit(func, arg, retval)

    return deco


def __sympifyit(func, arg, retval=None):
    """decorator to _sympify `arg` argument for function `func`

       don't use directly -- use _sympifyit instead
    """

    # we support f(a,b) only
    if not get_function_code(func).co_argcount:
        raise LookupError("func not found")
    # only b is _sympified
    assert get_function_code(func).co_varnames[1] == arg
    if retval is None:
        @wraps(func)
        def __sympifyit_wrapper(a, b):
            return func(a, sympify(b, strict=True))

    else:
        @wraps(func)
        def __sympifyit_wrapper(a, b):
            try:
                # If an external class has _op_priority, it knows how to deal
                # with sympy objects. Otherwise, it must be converted.
                if not hasattr(b, '_op_priority'):
                    b = sympify(b, strict=True)
                return func(a, b)
            except SympifyError:
                return retval

    return __sympifyit_wrapper


def call_highest_priority(method_name):
    """A decorator for binary special methods to handle _op_priority.

    Binary special methods in Expr and its subclasses use a special attribute
    '_op_priority' to determine whose special method will be called to
    handle the operation. In general, the object having the highest value of
    '_op_priority' will handle the operation. Expr and subclasses that define
    custom binary special methods (__mul__, etc.) should decorate those
    methods with this decorator to add the priority logic.

    The ``method_name`` argument is the name of the method of the other class
    that will be called.  Use this decorator in the following manner::

        # Call other.__rmul__ if other._op_priority > self._op_priority
        @call_highest_priority('__rmul__')
        def __mul__(self, other):
            ...

        # Call other.__mul__ if other._op_priority > self._op_priority
        @call_highest_priority('__mul__')
        def __rmul__(self, other):
        ...
    """
    def priority_decorator(func):
        @wraps(func)
        def binary_op_wrapper(self, other):
            if hasattr(other, '_op_priority'):
                if other._op_priority > self._op_priority:
                    f = getattr(other, method_name, None)
                    if f is not None:
                        return f(self)
            return func(self, other)
        return binary_op_wrapper
    return priority_decorator
