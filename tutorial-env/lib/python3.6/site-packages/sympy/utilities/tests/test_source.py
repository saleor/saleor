import sys

from sympy.utilities.source import get_mod_func, get_class, source
from sympy.utilities.pytest import warns_deprecated_sympy
from sympy import point

def test_source():
    # Dummy stdout
    class StdOut(object):
        def write(self, x):
            pass

    # Test SymPyDeprecationWarning from source()
    with warns_deprecated_sympy():
        # Redirect stdout temporarily so print out is not seen
        stdout = sys.stdout
        try:
            sys.stdout = StdOut()
            source(point)
        finally:
            sys.stdout = stdout

def test_get_mod_func():
    assert get_mod_func(
        'sympy.core.basic.Basic') == ('sympy.core.basic', 'Basic')


def test_get_class():
    _basic = get_class('sympy.core.basic.Basic')
    assert _basic.__name__ == 'Basic'
