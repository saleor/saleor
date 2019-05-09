from sympy.multipledispatch import dispatch, Dispatcher
from sympy.core import Basic, Expr, Function, Add, Mul, Pow, Dummy, Integer
from sympy import Min, Max, Set, sympify, Lambda, symbols, exp, log, S, oo
from sympy.core.numbers import Infinity, NegativeInfinity, Zero
from sympy.sets import (imageset, Interval, FiniteSet, Union, ImageSet,
    ProductSet, EmptySet, Intersection)
from sympy.core.function import FunctionClass
from sympy.logic.boolalg import And, Or, Not, true, false


_x, _y = symbols("x y")


@dispatch(Basic, Basic)
def _set_pow(x, y):
    return None

@dispatch(Set, Set)
def _set_pow(x, y):
    return ImageSet(Lambda((_x, _y), (_x ** _y)), x, y)

@dispatch(Expr, Expr)
def _set_pow(x, y):
    return x**y

@dispatch(Interval, Zero)
def _set_pow(x, z):
    return FiniteSet(S.One)

@dispatch(Interval, Integer)
def _set_pow(x, exponent):
    """
    Powers in interval arithmetic
    https://en.wikipedia.org/wiki/Interval_arithmetic
    """
    s1 = x.start**exponent
    s2 = x.end**exponent
    if ((s2 > s1) if exponent > 0 else (x.end > -x.start)) == True:
        left_open = x.left_open
        right_open = x.right_open
        # TODO: handle unevaluated condition.
        sleft = s2
    else:
        # TODO: `s2 > s1` could be unevaluated.
        left_open = x.right_open
        right_open = x.left_open
        sleft = s1

    if x.start.is_positive:
        return Interval(
            Min(s1, s2),
            Max(s1, s2), left_open, right_open)
    elif x.end.is_negative:
        return Interval(
            Min(s1, s2),
            Max(s1, s2), left_open, right_open)

    # Case where x.start < 0 and x.end > 0:
    if exponent.is_odd:
        if exponent.is_negative:
            if x.start.is_zero:
                return Interval(s2, oo, x.right_open)
            if x.end.is_zero:
                return Interval(-oo, s1, True, x.left_open)
            return Union(Interval(-oo, s1, True, x.left_open), Interval(s2, oo, x.right_open))
        else:
            return Interval(s1, s2, x.left_open, x.right_open)
    elif exponent.is_even:
        if exponent.is_negative:
            if x.start.is_zero:
                return Interval(s2, oo, x.right_open)
            if x.end.is_zero:
                return Interval(s1, oo, x.left_open)
            return Interval(0, oo)
        else:
            return Interval(S.Zero, sleft, S.Zero not in x, left_open)

@dispatch(Interval, Infinity)
def _set_pow(b, e):
    # TODO: add logic for open intervals?
    if b.start.is_nonnegative:
        if b.end < 1:
            return FiniteSet(S.Zero)
        if b.start > 1:
            return FiniteSet(S.Infinity)
        return Interval(0, oo)
    elif b.end.is_negative:
        if b.start > -1:
            return FiniteSet(S.Zero)
        if b.end < -1:
            return FiniteSet(-oo, oo)
        return Interval(-oo, oo)
    else:
        if b.start > -1:
            if b.end < 1:
                return FiniteSet(S.Zero)
            return Interval(0, oo)
        return Interval(-oo, oo)

@dispatch(Interval, NegativeInfinity)
def _set_pow(b, e):
    from sympy.sets.setexpr import set_div
    return _set_pow(set_div(S.One, b), oo)
