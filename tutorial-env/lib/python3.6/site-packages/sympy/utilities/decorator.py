"""Useful utility decorators. """

from __future__ import print_function, division

import sys
import types
import inspect

from functools import update_wrapper

from sympy.core.decorators import wraps
from sympy.core.compatibility import class_types, get_function_globals, get_function_name, iterable
from sympy.utilities.runtests import DependencyError, SymPyDocTests, PyTestReporter

def threaded_factory(func, use_add):
    """A factory for ``threaded`` decorators. """
    from sympy.core import sympify
    from sympy.matrices import MatrixBase

    @wraps(func)
    def threaded_func(expr, *args, **kwargs):
        if isinstance(expr, MatrixBase):
            return expr.applyfunc(lambda f: func(f, *args, **kwargs))
        elif iterable(expr):
            try:
                return expr.__class__([func(f, *args, **kwargs) for f in expr])
            except TypeError:
                return expr
        else:
            expr = sympify(expr)

            if use_add and expr.is_Add:
                return expr.__class__(*[ func(f, *args, **kwargs) for f in expr.args ])
            elif expr.is_Relational:
                return expr.__class__(func(expr.lhs, *args, **kwargs),
                                      func(expr.rhs, *args, **kwargs))
            else:
                return func(expr, *args, **kwargs)

    return threaded_func


def threaded(func):
    """Apply ``func`` to sub--elements of an object, including :class:`Add`.

    This decorator is intended to make it uniformly possible to apply a
    function to all elements of composite objects, e.g. matrices, lists, tuples
    and other iterable containers, or just expressions.

    This version of :func:`threaded` decorator allows threading over
    elements of :class:`Add` class. If this behavior is not desirable
    use :func:`xthreaded` decorator.

    Functions using this decorator must have the following signature::

      @threaded
      def function(expr, *args, **kwargs):

    """
    return threaded_factory(func, True)


def xthreaded(func):
    """Apply ``func`` to sub--elements of an object, excluding :class:`Add`.

    This decorator is intended to make it uniformly possible to apply a
    function to all elements of composite objects, e.g. matrices, lists, tuples
    and other iterable containers, or just expressions.

    This version of :func:`threaded` decorator disallows threading over
    elements of :class:`Add` class. If this behavior is not desirable
    use :func:`threaded` decorator.

    Functions using this decorator must have the following signature::

      @xthreaded
      def function(expr, *args, **kwargs):

    """
    return threaded_factory(func, False)


def conserve_mpmath_dps(func):
    """After the function finishes, resets the value of mpmath.mp.dps to
    the value it had before the function was run."""
    import functools
    import mpmath

    def func_wrapper(*args, **kwargs):
        dps = mpmath.mp.dps
        try:
            return func(*args, **kwargs)
        finally:
            mpmath.mp.dps = dps

    func_wrapper = functools.update_wrapper(func_wrapper, func)
    return func_wrapper


class no_attrs_in_subclass(object):
    """Don't 'inherit' certain attributes from a base class

    >>> from sympy.utilities.decorator import no_attrs_in_subclass

    >>> class A(object):
    ...     x = 'test'

    >>> A.x = no_attrs_in_subclass(A, A.x)

    >>> class B(A):
    ...     pass

    >>> hasattr(A, 'x')
    True
    >>> hasattr(B, 'x')
    False

    """
    def __init__(self, cls, f):
        self.cls = cls
        self.f = f

    def __get__(self, instance, owner=None):
        if owner == self.cls:
            if hasattr(self.f, '__get__'):
                return self.f.__get__(instance, owner)
            return self.f
        raise AttributeError


def doctest_depends_on(exe=None, modules=None, disable_viewers=None, python_version=None):
    """
    Adds metadata about the dependencies which need to be met for doctesting
    the docstrings of the decorated objects.

    exe should be a list of executables

    modules should be a list of modules

    disable_viewers should be a list of viewers for preview() to disable

    python_version should be the minimum Python version required, as a tuple
    (like (3, 0))
    """

    dependencies = {}
    if exe is not None:
        dependencies['executables'] = exe
    if modules is not None:
        dependencies['modules'] = modules
    if disable_viewers is not None:
        dependencies['disable_viewers'] = disable_viewers
    if python_version is not None:
        dependencies['python_version'] = python_version

    def skiptests():
        r = PyTestReporter()
        t = SymPyDocTests(r, None)
        try:
            t._check_dependencies(**dependencies)
        except DependencyError:
            return True  # Skip doctests
        else:
            return False # Run doctests

    def depends_on_deco(fn):
        fn._doctest_depends_on = dependencies
        fn.__doctest_skip__ = skiptests

        if inspect.isclass(fn):
            fn._doctest_depdends_on = no_attrs_in_subclass(
                fn, fn._doctest_depends_on)
            fn.__doctest_skip__ = no_attrs_in_subclass(
                fn, fn.__doctest_skip__)
        return fn

    return depends_on_deco


def public(obj):
    """
    Append ``obj``'s name to global ``__all__`` variable (call site).

    By using this decorator on functions or classes you achieve the same goal
    as by filling ``__all__`` variables manually, you just don't have to repeat
    yourself (object's name). You also know if object is public at definition
    site, not at some random location (where ``__all__`` was set).

    Note that in multiple decorator setup (in almost all cases) ``@public``
    decorator must be applied before any other decorators, because it relies
    on the pointer to object's global namespace. If you apply other decorators
    first, ``@public`` may end up modifying the wrong namespace.

    Examples
    ========

    >>> from sympy.utilities.decorator import public

    >>> __all__
    Traceback (most recent call last):
    ...
    NameError: name '__all__' is not defined

    >>> @public
    ... def some_function():
    ...     pass

    >>> __all__
    ['some_function']

    """
    if isinstance(obj, types.FunctionType):
        ns = get_function_globals(obj)
        name = get_function_name(obj)
    elif isinstance(obj, (type(type), class_types)):
        ns = sys.modules[obj.__module__].__dict__
        name = obj.__name__
    else:
        raise TypeError("expected a function or a class, got %s" % obj)

    if "__all__" not in ns:
        ns["__all__"] = [name]
    else:
        ns["__all__"].append(name)

    return obj


def memoize_property(storage):
    """Create a property, where the lookup is stored in ``storage``"""
    def decorator(method):
        name = method.__name__
        def wrapper(self):
            if name not in storage:
                storage[name] = method(self)
            return storage[name]
        return property(update_wrapper(wrapper, method))
    return decorator
