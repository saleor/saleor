from sympy import Symbol, exp, log, oo, S, I, sqrt
from sympy.calculus.singularities import (
    singularities,
    is_increasing,
    is_strictly_increasing,
    is_decreasing,
    is_strictly_decreasing,
    is_monotonic
)
from sympy.sets import Interval, FiniteSet
from sympy.utilities.pytest import XFAIL
from sympy.abc import x, y


def test_singularities():
    x = Symbol('x')
    assert singularities(x**2, x) == S.EmptySet
    assert singularities(x/(x**2 + 3*x + 2), x) == FiniteSet(-2, -1)
    assert singularities(1/(x**2 + 1), x) == FiniteSet(I, -I)
    assert singularities(x/(x**3 + 1), x) == \
        FiniteSet(-1, (1 - sqrt(3) * I) / 2, (1 + sqrt(3) * I) / 2)
    assert singularities(1/(y**2 + 2*I*y + 1), y) == \
        FiniteSet(-I + sqrt(2)*I, -I - sqrt(2)*I)

    x = Symbol('x', real=True)
    assert singularities(1/(x**2 + 1), x) == S.EmptySet


@XFAIL
def test_singularities_non_rational():
    x = Symbol('x', real=True)

    assert singularities(exp(1/x), x) == FiniteSet(0)
    assert singularities(log((x - 2)**2), x) == FiniteSet(2)


def test_is_increasing():
    """Test whether is_increasing returns correct value."""
    a = Symbol('a', negative=True)

    assert is_increasing(x**3 - 3*x**2 + 4*x, S.Reals)
    assert is_increasing(-x**2, Interval(-oo, 0))
    assert not is_increasing(-x**2, Interval(0, oo))
    assert not is_increasing(4*x**3 - 6*x**2 - 72*x + 30, Interval(-2, 3))
    assert is_increasing(x**2 + y, Interval(1, oo), x)
    assert is_increasing(-x**2*a, Interval(1, oo), x)
    assert is_increasing(1)


def test_is_strictly_increasing():
    """Test whether is_strictly_increasing returns correct value."""
    assert is_strictly_increasing(
        4*x**3 - 6*x**2 - 72*x + 30, Interval.Ropen(-oo, -2))
    assert is_strictly_increasing(
        4*x**3 - 6*x**2 - 72*x + 30, Interval.Lopen(3, oo))
    assert not is_strictly_increasing(
        4*x**3 - 6*x**2 - 72*x + 30, Interval.open(-2, 3))
    assert not is_strictly_increasing(-x**2, Interval(0, oo))
    assert not is_strictly_decreasing(1)


def test_is_decreasing():
    """Test whether is_decreasing returns correct value."""
    b = Symbol('b', positive=True)

    assert is_decreasing(1/(x**2 - 3*x), Interval.open(1.5, 3))
    assert is_decreasing(1/(x**2 - 3*x), Interval.Lopen(3, oo))
    assert not is_decreasing(1/(x**2 - 3*x), Interval.Ropen(-oo, S(3)/2))
    assert not is_decreasing(-x**2, Interval(-oo, 0))
    assert not is_decreasing(-x**2*b, Interval(-oo, 0), x)


def test_is_strictly_decreasing():
    """Test whether is_strictly_decreasing returns correct value."""
    assert is_strictly_decreasing(1/(x**2 - 3*x), Interval.Lopen(3, oo))
    assert not is_strictly_decreasing(
        1/(x**2 - 3*x), Interval.Ropen(-oo, S(3)/2))
    assert not is_strictly_decreasing(-x**2, Interval(-oo, 0))
    assert not is_strictly_decreasing(1)
    assert is_strictly_decreasing(1/(x**2 - 3*x), Interval.open(1.5, 3))


def test_is_monotonic():
    """Test whether is_monotonic returns correct value."""
    assert is_monotonic(1/(x**2 - 3*x), Interval.open(1.5, 3))
    assert is_monotonic(1/(x**2 - 3*x), Interval.Lopen(3, oo))
    assert is_monotonic(x**3 - 3*x**2 + 4*x, S.Reals)
    assert not is_monotonic(-x**2, S.Reals)
    assert is_monotonic(x**2 + y + 1, Interval(1, 2), x)
