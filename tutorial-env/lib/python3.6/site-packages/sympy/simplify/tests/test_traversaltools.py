"""Tools for applying functions to specified parts of expressions. """

from sympy.simplify.traversaltools import use

from sympy import expand, factor, I
from sympy.abc import x, y


def test_use():
    assert use(0, expand) == 0

    f = (x + y)**2*x + 1

    assert use(f, expand, level=0) == x**3 + 2*x**2*y + x*y**2 + + 1
    assert use(f, expand, level=1) == x**3 + 2*x**2*y + x*y**2 + + 1
    assert use(f, expand, level=2) == 1 + x*(2*x*y + x**2 + y**2)
    assert use(f, expand, level=3) == (x + y)**2*x + 1

    f = (x**2 + 1)**2 - 1
    kwargs = {'gaussian': True}

    assert use(f, factor, level=0, kwargs=kwargs) == x**2*(x**2 + 2)
    assert use(f, factor, level=1, kwargs=kwargs) == (x + I)**2*(x - I)**2 - 1
    assert use(f, factor, level=2, kwargs=kwargs) == (x + I)**2*(x - I)**2 - 1
    assert use(f, factor, level=3, kwargs=kwargs) == (x**2 + 1)**2 - 1
