from sympy.core.basic import Basic
from sympy.core.numbers import Rational
from sympy.core.singleton import S, Singleton, SingletonRegistry

from sympy.core.compatibility import with_metaclass, exec_

def test_Singleton():
    global instantiated
    instantiated = 0

    class MySingleton(with_metaclass(Singleton, Basic)):
        def __new__(cls):
            global instantiated
            instantiated += 1
            return Basic.__new__(cls)

    assert instantiated == 0
    MySingleton() # force instantiation
    assert instantiated == 1
    assert MySingleton() is not Basic()
    assert MySingleton() is MySingleton()
    assert S.MySingleton is MySingleton()
    assert instantiated == 1

    class MySingleton_sub(MySingleton):
        pass
    assert instantiated == 1
    MySingleton_sub()
    assert instantiated == 2
    assert MySingleton_sub() is not MySingleton()
    assert MySingleton_sub() is MySingleton_sub()

def test_singleton_redefinition():
    class TestSingleton(with_metaclass(Singleton, Basic)):
        pass

    assert TestSingleton() is S.TestSingleton

    class TestSingleton(with_metaclass(Singleton, Basic)):
        pass

    assert TestSingleton() is S.TestSingleton

def test_names_in_namespace():
    # Every singleton name should be accessible from the 'from sympy import *'
    # namespace in addition to the S object. However, it does not need to be
    # by the same name (e.g., oo instead of S.Infinity).

    # As a general rule, things should only be added to the singleton registry
    # if they are used often enough that code can benefit either from the
    # performance benefit of being able to use 'is' (this only matters in very
    # tight loops), or from the memory savings of having exactly one instance
    # (this matters for the numbers singletons, but very little else). The
    # singleton registry is already a bit overpopulated, and things cannot be
    # removed from it without breaking backwards compatibility. So if you got
    # here by adding something new to the singletons, ask yourself if it
    # really needs to be singletonized. Note that SymPy classes compare to one
    # another just fine, so Class() == Class() will give True even if each
    # Class() returns a new instance. Having unique instances is only
    # necessary for the above noted performance gains. It should not be needed
    # for any behavioral purposes.

    # If you determine that something really should be a singleton, it must be
    # accessible to sympify() without using 'S' (hence this test). Also, its
    # str printer should print a form that does not use S. This is because
    # sympify() disables attribute lookups by default for safety purposes.
    d = {}
    exec_('from sympy import *', d)

    for name in dir(S) + list(S._classes_to_install):
        if name.startswith('_'):
            continue
        if name == 'register':
            continue
        if isinstance(getattr(S, name), Rational):
            continue
        if getattr(S, name).__module__.startswith('sympy.physics'):
            continue
        if name in ['MySingleton', 'MySingleton_sub', 'TestSingleton']:
            # From the tests above
            continue
        if name == 'NegativeInfinity':
            # Accessible by -oo
            continue

        # Use is here because of complications with ==
        assert any(getattr(S, name) is i or type(getattr(S, name)) is i for i in d.values()), name
