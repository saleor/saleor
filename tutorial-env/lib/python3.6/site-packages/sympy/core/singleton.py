"""Singleton mechanism"""

from __future__ import print_function, division

from .core import Registry
from .assumptions import ManagedProperties
from .sympify import sympify


class SingletonRegistry(Registry):
    """
    The registry for the singleton classes (accessible as ``S``).

    This class serves as two separate things.

    The first thing it is is the ``SingletonRegistry``. Several classes in
    SymPy appear so often that they are singletonized, that is, using some
    metaprogramming they are made so that they can only be instantiated once
    (see the :class:`sympy.core.singleton.Singleton` class for details). For
    instance, every time you create ``Integer(0)``, this will return the same
    instance, :class:`sympy.core.numbers.Zero`. All singleton instances are
    attributes of the ``S`` object, so ``Integer(0)`` can also be accessed as
    ``S.Zero``.

    Singletonization offers two advantages: it saves memory, and it allows
    fast comparison. It saves memory because no matter how many times the
    singletonized objects appear in expressions in memory, they all point to
    the same single instance in memory. The fast comparison comes from the
    fact that you can use ``is`` to compare exact instances in Python
    (usually, you need to use ``==`` to compare things). ``is`` compares
    objects by memory address, and is very fast. For instance

    >>> from sympy import S, Integer
    >>> a = Integer(0)
    >>> a is S.Zero
    True

    For the most part, the fact that certain objects are singletonized is an
    implementation detail that users shouldn't need to worry about. In SymPy
    library code, ``is`` comparison is often used for performance purposes
    The primary advantage of ``S`` for end users is the convenient access to
    certain instances that are otherwise difficult to type, like ``S.Half``
    (instead of ``Rational(1, 2)``).

    When using ``is`` comparison, make sure the argument is sympified. For
    instance,

    >>> 0 is S.Zero
    False

    This problem is not an issue when using ``==``, which is recommended for
    most use-cases:

    >>> 0 == S.Zero
    True

    The second thing ``S`` is is a shortcut for
    :func:`sympy.core.sympify.sympify`. :func:`sympy.core.sympify.sympify` is
    the function that converts Python objects such as ``int(1)`` into SymPy
    objects such as ``Integer(1)``. It also converts the string form of an
    expression into a SymPy expression, like ``sympify("x**2")`` ->
    ``Symbol("x")**2``. ``S(1)`` is the same thing as ``sympify(1)``
    (basically, ``S.__call__`` has been defined to call ``sympify``).

    This is for convenience, since ``S`` is a single letter. It's mostly
    useful for defining rational numbers. Consider an expression like ``x +
    1/2``. If you enter this directly in Python, it will evaluate the ``1/2``
    and give ``0.5`` (or just ``0`` in Python 2, because of integer division),
    because both arguments are ints (see also
    :ref:`tutorial-gotchas-final-notes`). However, in SymPy, you usually want
    the quotient of two integers to give an exact rational number. The way
    Python's evaluation works, at least one side of an operator needs to be a
    SymPy object for the SymPy evaluation to take over. You could write this
    as ``x + Rational(1, 2)``, but this is a lot more typing. A shorter
    version is ``x + S(1)/2``. Since ``S(1)`` returns ``Integer(1)``, the
    division will return a ``Rational`` type, since it will call
    ``Integer.__div__``, which knows how to return a ``Rational``.

    """
    __slots__ = []

    # Also allow things like S(5)
    __call__ = staticmethod(sympify)

    def __init__(self):
        self._classes_to_install = {}
        # Dict of classes that have been registered, but that have not have been
        # installed as an attribute of this SingletonRegistry.
        # Installation automatically happens at the first attempt to access the
        # attribute.
        # The purpose of this is to allow registration during class
        # initialization during import, but not trigger object creation until
        # actual use (which should not happen until after all imports are
        # finished).

    def register(self, cls):
        # Make sure a duplicate class overwrites the old one
        if hasattr(self, cls.__name__):
            delattr(self, cls.__name__)
        self._classes_to_install[cls.__name__] = cls

    def __getattr__(self, name):
        """Python calls __getattr__ if no attribute of that name was installed
        yet.

        This __getattr__ checks whether a class with the requested name was
        already registered but not installed; if no, raises an AttributeError.
        Otherwise, retrieves the class, calculates its singleton value, installs
        it as an attribute of the given name, and unregisters the class."""
        if name not in self._classes_to_install:
            raise AttributeError(
                "Attribute '%s' was not installed on SymPy registry %s" % (
                name, self))
        class_to_install = self._classes_to_install[name]
        value_to_install = class_to_install()
        self.__setattr__(name, value_to_install)
        del self._classes_to_install[name]
        return value_to_install

    def __repr__(self):
        return "S"

S = SingletonRegistry()


class Singleton(ManagedProperties):
    """
    Metaclass for singleton classes.

    A singleton class has only one instance which is returned every time the
    class is instantiated. Additionally, this instance can be accessed through
    the global registry object S as S.<class_name>.

    Examples
    ========

        >>> from sympy import S, Basic
        >>> from sympy.core.singleton import Singleton
        >>> from sympy.core.compatibility import with_metaclass
        >>> class MySingleton(with_metaclass(Singleton, Basic)):
        ...     pass
        >>> Basic() is Basic()
        False
        >>> MySingleton() is MySingleton()
        True
        >>> S.MySingleton is MySingleton()
        True

    Notes
    =====

    Instance creation is delayed until the first time the value is accessed.
    (SymPy versions before 1.0 would create the instance during class
    creation time, which would be prone to import cycles.)

    This metaclass is a subclass of ManagedProperties because that is the
    metaclass of many classes that need to be Singletons (Python does not allow
    subclasses to have a different metaclass than the superclass, except the
    subclass may use a subclassed metaclass).
    """

    _instances = {}
    "Maps singleton classes to their instances."

    def __new__(cls, *args, **kwargs):
        result = super(Singleton, cls).__new__(cls, *args, **kwargs)
        S.register(result)
        return result

    def __call__(self, *args, **kwargs):
        # Called when application code says SomeClass(), where SomeClass is a
        # class of which Singleton is the metaclas.
        # __call__ is invoked first, before __new__() and __init__().
        if self not in Singleton._instances:
            Singleton._instances[self] = \
                super(Singleton, self).__call__(*args, **kwargs)
                # Invokes the standard constructor of SomeClass.
        return Singleton._instances[self]

        # Inject pickling support.
        def __getnewargs__(self):
            return ()
        self.__getnewargs__ = __getnewargs__
