from sympy.core.compatibility import range, PY3
from sympy.sets.fancysets import (ImageSet, Range, normalize_theta_set,
                                  ComplexRegion)
from sympy.sets.sets import (FiniteSet, Interval, imageset, Union,
                             Intersection)
from sympy.simplify.simplify import simplify
from sympy import (S, Symbol, Lambda, symbols, cos, sin, pi, oo, Basic,
                   Rational, sqrt, tan, log, exp, Abs, I, Tuple, eye)
from sympy.utilities.iterables import cartes
from sympy.utilities.pytest import XFAIL, raises
from sympy.abc import x, y, t

import itertools


def test_naturals():
    N = S.Naturals
    assert 5 in N
    assert -5 not in N
    assert 5.5 not in N
    ni = iter(N)
    a, b, c, d = next(ni), next(ni), next(ni), next(ni)
    assert (a, b, c, d) == (1, 2, 3, 4)
    assert isinstance(a, Basic)

    assert N.intersect(Interval(-5, 5)) == Range(1, 6)
    assert N.intersect(Interval(-5, 5, True, True)) == Range(1, 5)

    assert N.boundary == N

    assert N.inf == 1
    assert N.sup == oo

def test_naturals0():
    N = S.Naturals0
    assert 0 in N
    assert -1 not in N
    assert next(iter(N)) == 0

def test_integers():
    Z = S.Integers
    assert 5 in Z
    assert -5 in Z
    assert 5.5 not in Z
    zi = iter(Z)
    a, b, c, d = next(zi), next(zi), next(zi), next(zi)
    assert (a, b, c, d) == (0, 1, -1, 2)
    assert isinstance(a, Basic)

    assert Z.intersect(Interval(-5, 5)) == Range(-5, 6)
    assert Z.intersect(Interval(-5, 5, True, True)) == Range(-4, 5)
    assert Z.intersect(Interval(5, S.Infinity)) == Range(5, S.Infinity)
    assert Z.intersect(Interval.Lopen(5, S.Infinity)) == Range(6, S.Infinity)

    assert Z.inf == -oo
    assert Z.sup == oo

    assert Z.boundary == Z


def test_ImageSet():
    assert ImageSet(Lambda(x, 1), S.Integers) == FiniteSet(1)
    assert ImageSet(Lambda(x, y), S.Integers) == FiniteSet(y)
    squares = ImageSet(Lambda(x, x**2), S.Naturals)
    assert 4 in squares
    assert 5 not in squares
    assert FiniteSet(*range(10)).intersect(squares) == FiniteSet(1, 4, 9)

    assert 16 not in squares.intersect(Interval(0, 10))

    si = iter(squares)
    a, b, c, d = next(si), next(si), next(si), next(si)
    assert (a, b, c, d) == (1, 4, 9, 16)

    harmonics = ImageSet(Lambda(x, 1/x), S.Naturals)
    assert Rational(1, 5) in harmonics
    assert Rational(.25) in harmonics
    assert 0.25 not in harmonics
    assert Rational(.3) not in harmonics

    assert harmonics.is_iterable

    assert imageset(x, -x, Interval(0, 1)) == Interval(-1, 0)

    assert ImageSet(Lambda(x, x**2), Interval(0, 2)).doit() == Interval(0, 4)

    c = ComplexRegion(Interval(1, 3)*Interval(1, 3))
    assert Tuple(2, 6) in ImageSet(Lambda((x, y), (x, 2*y)), c)
    assert Tuple(2, S.Half) in ImageSet(Lambda((x, y), (x, 1/y)), c)
    assert Tuple(2, -2) not in ImageSet(Lambda((x, y), (x, y**2)), c)
    assert Tuple(2, -2) in ImageSet(Lambda((x, y), (x, -2)), c)
    c3 = Interval(3, 7)*Interval(8, 11)*Interval(5, 9)
    assert Tuple(8, 3, 9) in ImageSet(Lambda((t, y, x), (y, t, x)), c3)
    assert Tuple(S(1)/8, 3, 9) in ImageSet(Lambda((t, y, x), (1/y, t, x)), c3)
    assert 2/pi not in ImageSet(Lambda((x, y), 2/x), c)
    assert 2/S(100) not in ImageSet(Lambda((x, y), 2/x), c)
    assert 2/S(3) in ImageSet(Lambda((x, y), 2/x), c)


def test_image_is_ImageSet():
    assert isinstance(imageset(x, sqrt(sin(x)), Range(5)), ImageSet)


@XFAIL
def test_halfcircle():
    # This test sometimes works and sometimes doesn't.
    # It may be an issue with solve? Maybe with using Lambdas/dummys?
    # I believe the code within fancysets is correct
    r, th = symbols('r, theta', real=True)
    L = Lambda((r, th), (r*cos(th), r*sin(th)))
    halfcircle = ImageSet(L, Interval(0, 1)*Interval(0, pi))

    assert (1, 0) in halfcircle
    assert (0, -1) not in halfcircle
    assert (0, 0) in halfcircle

    assert not halfcircle.is_iterable


def test_ImageSet_iterator_not_injective():
    L = Lambda(x, x - x % 2)  # produces 0, 2, 2, 4, 4, 6, 6, ...
    evens = ImageSet(L, S.Naturals)
    i = iter(evens)
    # No repeats here
    assert (next(i), next(i), next(i), next(i)) == (0, 2, 4, 6)


def test_inf_Range_len():
    raises(ValueError, lambda: len(Range(0, oo, 2)))
    assert Range(0, oo, 2).size is S.Infinity
    assert Range(0, -oo, -2).size is S.Infinity
    assert Range(oo, 0, -2).size is S.Infinity
    assert Range(-oo, 0, 2).size is S.Infinity


def test_Range_set():
    empty = Range(0)

    assert Range(5) == Range(0, 5) == Range(0, 5, 1)

    r = Range(10, 20, 2)
    assert 12 in r
    assert 8 not in r
    assert 11 not in r
    assert 30 not in r

    assert list(Range(0, 5)) == list(range(5))
    assert list(Range(5, 0, -1)) == list(range(5, 0, -1))


    assert Range(5, 15).sup == 14
    assert Range(5, 15).inf == 5
    assert Range(15, 5, -1).sup == 15
    assert Range(15, 5, -1).inf == 6
    assert Range(10, 67, 10).sup == 60
    assert Range(60, 7, -10).inf == 10

    assert len(Range(10, 38, 10)) == 3

    assert Range(0, 0, 5) == empty
    assert Range(oo, oo, 1) == empty
    raises(ValueError, lambda: Range(1, 4, oo))
    raises(ValueError, lambda: Range(-oo, oo))
    raises(ValueError, lambda: Range(oo, -oo, -1))
    raises(ValueError, lambda: Range(-oo, oo, 2))
    raises(ValueError, lambda: Range(0, pi, 1))
    raises(ValueError, lambda: Range(1, 10, 0))

    assert 5 in Range(0, oo, 5)
    assert -5 in Range(-oo, 0, 5)
    assert oo not in Range(0, oo)
    ni = symbols('ni', integer=False)
    assert ni not in Range(oo)
    u = symbols('u', integer=None)
    assert Range(oo).contains(u) is not False
    inf = symbols('inf', infinite=True)
    assert inf not in Range(oo)
    inf = symbols('inf', infinite=True)
    assert inf not in Range(oo)
    assert Range(0, oo, 2)[-1] == oo
    assert Range(-oo, 1, 1)[-1] is S.Zero
    assert Range(oo, 1, -1)[-1] == 2
    assert Range(0, -oo, -2)[-1] == -oo
    assert Range(1, 10, 1)[-1] == 9

    it = iter(Range(-oo, 0, 2))
    raises(ValueError, lambda: next(it))

    assert empty.intersect(S.Integers) == empty
    assert Range(-1, 10, 1).intersect(S.Integers) == Range(-1, 10, 1)
    assert Range(-1, 10, 1).intersect(S.Naturals) == Range(1, 10, 1)

    # test slicing
    assert Range(1, 10, 1)[5] == 6
    assert Range(1, 12, 2)[5] == 11
    assert Range(1, 10, 1)[-1] == 9
    assert Range(1, 10, 3)[-1] == 7
    raises(ValueError, lambda: Range(oo,0,-1)[1:3:0])
    raises(ValueError, lambda: Range(oo,0,-1)[:1])
    raises(ValueError, lambda: Range(1, oo)[-2])
    raises(ValueError, lambda: Range(-oo, 1)[2])
    raises(IndexError, lambda: Range(10)[-20])
    raises(IndexError, lambda: Range(10)[20])
    raises(ValueError, lambda: Range(2, -oo, -2)[2:2:0])
    assert Range(2, -oo, -2)[2:2:2] == empty
    assert Range(2, -oo, -2)[:2:2] == Range(2, -2, -4)
    raises(ValueError, lambda: Range(-oo, 4, 2)[:2:2])
    assert Range(-oo, 4, 2)[::-2] == Range(2, -oo, -4)
    raises(ValueError, lambda: Range(-oo, 4, 2)[::2])
    assert Range(oo, 2, -2)[::] == Range(oo, 2, -2)
    assert Range(-oo, 4, 2)[:-2:-2] == Range(2, 0, -4)
    assert Range(-oo, 4, 2)[:-2:2] == Range(-oo, 0, 4)
    raises(ValueError, lambda: Range(-oo, 4, 2)[:0:-2])
    raises(ValueError, lambda: Range(-oo, 4, 2)[:2:-2])
    assert Range(-oo, 4, 2)[-2::-2] == Range(0, -oo, -4)
    raises(ValueError, lambda: Range(-oo, 4, 2)[-2:0:-2])
    raises(ValueError, lambda: Range(-oo, 4, 2)[0::2])
    assert Range(oo, 2, -2)[0::] == Range(oo, 2, -2)
    raises(ValueError, lambda: Range(-oo, 4, 2)[0:-2:2])
    assert Range(oo, 2, -2)[0:-2:] == Range(oo, 6, -2)
    raises(ValueError, lambda: Range(oo, 2, -2)[0:2:])
    raises(ValueError, lambda: Range(-oo, 4, 2)[2::-1])
    assert Range(-oo, 4, 2)[-2::2] == Range(0, 4, 4)
    assert Range(oo, 0, -2)[-10:0:2] == empty
    raises(ValueError, lambda: Range(oo, 0, -2)[-10:10:2])
    raises(ValueError, lambda: Range(oo, 0, -2)[0::-2])
    assert Range(oo, 0, -2)[0:-4:-2] == empty
    assert Range(oo, 0, -2)[:0:2] == empty
    raises(ValueError, lambda: Range(oo, 0, -2)[:1:-1])

    # test empty Range
    assert empty.reversed == empty
    assert 0 not in empty
    assert list(empty) == []
    assert len(empty) == 0
    assert empty.size is S.Zero
    assert empty.intersect(FiniteSet(0)) is S.EmptySet
    assert bool(empty) is False
    raises(IndexError, lambda: empty[0])
    assert empty[:0] == empty
    raises(NotImplementedError, lambda: empty.inf)
    raises(NotImplementedError, lambda: empty.sup)

    AB = [None] + list(range(12))
    for R in [
            Range(1, 10),
            Range(1, 10, 2),
        ]:
        r = list(R)
        for a, b, c in cartes(AB, AB, [-3, -1, None, 1, 3]):
            for reverse in range(2):
                r = list(reversed(r))
                R = R.reversed
                result = list(R[a:b:c])
                ans = r[a:b:c]
                txt = ('\n%s[%s:%s:%s] = %s -> %s' % (
                R, a, b, c, result, ans))
                check = ans == result
                assert check, txt

    assert Range(1, 10, 1).boundary == Range(1, 10, 1)

    for r in (Range(1, 10, 2), Range(1, oo, 2)):
        rev = r.reversed
        assert r.inf == rev.inf and r.sup == rev.sup
        assert r.step == -rev.step

    # Make sure to use range in Python 3 and xrange in Python 2 (regardless of
    # compatibility imports above)
    if PY3:
        builtin_range = range
    else:
        builtin_range = xrange

    assert Range(builtin_range(10)) == Range(10)
    assert Range(builtin_range(1, 10)) == Range(1, 10)
    assert Range(builtin_range(1, 10, 2)) == Range(1, 10, 2)
    if PY3:
        assert Range(builtin_range(1000000000000)) == \
            Range(1000000000000)


def test_range_range_intersection():
    for a, b, r in [
            (Range(0), Range(1), S.EmptySet),
            (Range(3), Range(4, oo), S.EmptySet),
            (Range(3), Range(-3, -1), S.EmptySet),
            (Range(1, 3), Range(0, 3), Range(1, 3)),
            (Range(1, 3), Range(1, 4), Range(1, 3)),
            (Range(1, oo, 2), Range(2, oo, 2), S.EmptySet),
            (Range(0, oo, 2), Range(oo), Range(0, oo, 2)),
            (Range(0, oo, 2), Range(100), Range(0, 100, 2)),
            (Range(2, oo, 2), Range(oo), Range(2, oo, 2)),
            (Range(0, oo, 2), Range(5, 6), S.EmptySet),
            (Range(2, 80, 1), Range(55, 71, 4), Range(55, 71, 4)),
            (Range(0, 6, 3), Range(-oo, 5, 3), S.EmptySet),
            (Range(0, oo, 2), Range(5, oo, 3), Range(8, oo, 6)),
            (Range(4, 6, 2), Range(2, 16, 7), S.EmptySet),]:
        assert a.intersect(b) == r
        assert a.intersect(b.reversed) == r
        assert a.reversed.intersect(b) == r
        assert a.reversed.intersect(b.reversed) == r
        a, b = b, a
        assert a.intersect(b) == r
        assert a.intersect(b.reversed) == r
        assert a.reversed.intersect(b) == r
        assert a.reversed.intersect(b.reversed) == r


def test_range_interval_intersection():
    p = symbols('p', positive=True)
    assert isinstance(Range(3).intersect(Interval(p, p + 2)), Intersection)
    assert Range(4).intersect(Interval(0, 3)) == Range(4)
    assert Range(4).intersect(Interval(-oo, oo)) == Range(4)
    assert Range(4).intersect(Interval(1, oo)) == Range(1, 4)
    assert Range(4).intersect(Interval(1.1, oo)) == Range(2, 4)
    assert Range(4).intersect(Interval(0.1, 3)) == Range(1, 4)
    assert Range(4).intersect(Interval(0.1, 3.1)) == Range(1, 4)
    assert Range(4).intersect(Interval.open(0, 3)) == Range(1, 3)
    assert Range(4).intersect(Interval.open(0.1, 0.5)) is S.EmptySet

    # Null Range intersections
    assert Range(0).intersect(Interval(0.2, 0.8)) is S.EmptySet
    assert Range(0).intersect(Interval(-oo, oo)) is S.EmptySet


def test_Integers_eval_imageset():
    ans = ImageSet(Lambda(x, 2*x + S(3)/7), S.Integers)
    im = imageset(Lambda(x, -2*x + S(3)/7), S.Integers)
    assert im == ans
    im = imageset(Lambda(x, -2*x - S(11)/7), S.Integers)
    assert im == ans
    y = Symbol('y')
    assert imageset(x, 2*x + y, S.Integers) == \
        imageset(x, 2*x + y % 2, S.Integers)

    _x = symbols('x', negative=True)
    eq = _x**2 - _x + 1
    assert imageset(_x, eq, S.Integers).lamda.expr == _x**2 + _x + 1
    eq = 3*_x - 1
    assert imageset(_x, eq, S.Integers).lamda.expr == 3*_x + 2

    assert imageset(x, (x, 1/x), S.Integers) == \
        ImageSet(Lambda(x, (x, 1/x)), S.Integers)


def test_Range_eval_imageset():
    a, b, c = symbols('a b c')
    assert imageset(x, a*(x + b) + c, Range(3)) == \
        imageset(x, a*x + a*b + c, Range(3))
    eq = (x + 1)**2
    assert imageset(x, eq, Range(3)).lamda.expr == eq
    eq = a*(x + b) + c
    r = Range(3, -3, -2)
    imset = imageset(x, eq, r)
    assert imset.lamda.expr != eq
    assert list(imset) == [eq.subs(x, i).expand() for i in list(r)]


def test_fun():
    assert (FiniteSet(*ImageSet(Lambda(x, sin(pi*x/4)),
        Range(-10, 11))) == FiniteSet(-1, -sqrt(2)/2, 0, sqrt(2)/2, 1))


def test_Reals():
    assert 5 in S.Reals
    assert S.Pi in S.Reals
    assert -sqrt(2) in S.Reals
    assert (2, 5) not in S.Reals
    assert sqrt(-1) not in S.Reals
    assert S.Reals == Interval(-oo, oo)
    assert S.Reals != Interval(0, oo)


def test_Complex():
    assert 5 in S.Complexes
    assert 5 + 4*I in S.Complexes
    assert S.Pi in S.Complexes
    assert -sqrt(2) in S.Complexes
    assert -I in S.Complexes
    assert sqrt(-1) in S.Complexes
    assert S.Complexes.intersect(S.Reals) == S.Reals
    assert S.Complexes.union(S.Reals) == S.Complexes
    assert S.Complexes == ComplexRegion(S.Reals*S.Reals)
    assert (S.Complexes == ComplexRegion(Interval(1, 2)*Interval(3, 4))) == False
    assert str(S.Complexes) == "S.Complexes"


def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(itertools.islice(iterable, n))


def test_intersections():
    assert S.Integers.intersect(S.Reals) == S.Integers
    assert 5 in S.Integers.intersect(S.Reals)
    assert 5 in S.Integers.intersect(S.Reals)
    assert -5 not in S.Naturals.intersect(S.Reals)
    assert 5.5 not in S.Integers.intersect(S.Reals)
    assert 5 in S.Integers.intersect(Interval(3, oo))
    assert -5 in S.Integers.intersect(Interval(-oo, 3))
    assert all(x.is_Integer
            for x in take(10, S.Integers.intersect(Interval(3, oo)) ))


def test_infinitely_indexed_set_1():
    from sympy.abc import n, m, t
    assert imageset(Lambda(n, n), S.Integers) == imageset(Lambda(m, m), S.Integers)

    assert imageset(Lambda(n, 2*n), S.Integers).intersect(
            imageset(Lambda(m, 2*m + 1), S.Integers)) is S.EmptySet

    assert imageset(Lambda(n, 2*n), S.Integers).intersect(
            imageset(Lambda(n, 2*n + 1), S.Integers)) is S.EmptySet

    assert imageset(Lambda(m, 2*m), S.Integers).intersect(
                imageset(Lambda(n, 3*n), S.Integers)) == \
            ImageSet(Lambda(t, 6*t), S.Integers)

    assert imageset(x, x/2 + S(1)/3, S.Integers).intersect(S.Integers) is S.EmptySet
    assert imageset(x, x/2 + S.Half, S.Integers).intersect(S.Integers) is S.Integers


def test_infinitely_indexed_set_2():
    from sympy.abc import n
    a = Symbol('a', integer=True)
    assert imageset(Lambda(n, n), S.Integers) == \
        imageset(Lambda(n, n + a), S.Integers)
    assert imageset(Lambda(n, n + pi), S.Integers) == \
        imageset(Lambda(n, n + a + pi), S.Integers)
    assert imageset(Lambda(n, n), S.Integers) == \
        imageset(Lambda(n, -n + a), S.Integers)
    assert imageset(Lambda(n, -6*n), S.Integers) == \
        ImageSet(Lambda(n, 6*n), S.Integers)
    assert imageset(Lambda(n, 2*n + pi), S.Integers) == \
        ImageSet(Lambda(n, 2*n + pi - 2), S.Integers)


def test_imageset_intersect_real():
    from sympy import I
    from sympy.abc import n
    assert imageset(Lambda(n, n + (n - 1)*(n + 1)*I), S.Integers).intersect(S.Reals) == \
            FiniteSet(-1, 1)

    s = ImageSet(Lambda(n, -I*(I*(2*pi*n - pi/4) + log(Abs(sqrt(-I))))), S.Integers)
    assert s.intersect(S.Reals) == imageset(Lambda(n, 2*n*pi - pi/4), S.Integers)


def test_imageset_intersect_interval():
    from sympy.abc import n
    f1 = ImageSet(Lambda(n, n*pi), S.Integers)
    f2 = ImageSet(Lambda(n, 2*n), Interval(0, pi))
    f3 = ImageSet(Lambda(n, 2*n*pi + pi/2), S.Integers)
    # complex expressions
    f4 = ImageSet(Lambda(n, n*I*pi), S.Integers)
    f5 = ImageSet(Lambda(n, 2*I*n*pi + pi/2), S.Integers)
    # non-linear expressions
    f6 = ImageSet(Lambda(n, log(n)), S.Integers)
    f7 = ImageSet(Lambda(n, n**2), S.Integers)
    f8 = ImageSet(Lambda(n, Abs(n)), S.Integers)
    f9 = ImageSet(Lambda(n, exp(n)), S.Naturals0)

    assert f1.intersect(Interval(-1, 1)) == FiniteSet(0)
    assert f1.intersect(Interval(0, 2*pi, False, True)) == FiniteSet(0, pi)
    assert f2.intersect(Interval(1, 2)) == Interval(1, 2)
    assert f3.intersect(Interval(-1, 1)) == S.EmptySet
    assert f3.intersect(Interval(-5, 5)) == FiniteSet(-3*pi/2, pi/2)
    assert f4.intersect(Interval(-1, 1)) == FiniteSet(0)
    assert f4.intersect(Interval(1, 2)) == S.EmptySet
    assert f5.intersect(Interval(0, 1)) == S.EmptySet
    assert f6.intersect(Interval(0, 1)) == FiniteSet(S.Zero, log(2))
    assert f7.intersect(Interval(0, 10)) == Intersection(f7, Interval(0, 10))
    assert f8.intersect(Interval(0, 2)) == Intersection(f8, Interval(0, 2))
    assert f9.intersect(Interval(1, 2)) == Intersection(f9, Interval(1, 2))


def test_infinitely_indexed_set_3():
    from sympy.abc import n, m, t
    assert imageset(Lambda(m, 2*pi*m), S.Integers).intersect(
            imageset(Lambda(n, 3*pi*n), S.Integers)) == \
        ImageSet(Lambda(t, 6*pi*t), S.Integers)
    assert imageset(Lambda(n, 2*n + 1), S.Integers) == \
        imageset(Lambda(n, 2*n - 1), S.Integers)
    assert imageset(Lambda(n, 3*n + 2), S.Integers) == \
        imageset(Lambda(n, 3*n - 1), S.Integers)


def test_ImageSet_simplification():
    from sympy.abc import n, m
    assert imageset(Lambda(n, n), S.Integers) == S.Integers
    assert imageset(Lambda(n, sin(n)),
                    imageset(Lambda(m, tan(m)), S.Integers)) == \
            imageset(Lambda(m, sin(tan(m))), S.Integers)


def test_ImageSet_contains():
    from sympy.abc import x
    assert (2, S.Half) in imageset(x, (x, 1/x), S.Integers)


def test_ComplexRegion_contains():

    # contains in ComplexRegion
    a = Interval(2, 3)
    b = Interval(4, 6)
    c = Interval(7, 9)
    c1 = ComplexRegion(a*b)
    c2 = ComplexRegion(Union(a*b, c*a))
    assert 2.5 + 4.5*I in c1
    assert 2 + 4*I in c1
    assert 3 + 4*I in c1
    assert 8 + 2.5*I in c2
    assert 2.5 + 6.1*I not in c1
    assert 4.5 + 3.2*I not in c1

    r1 = Interval(0, 1)
    theta1 = Interval(0, 2*S.Pi)
    c3 = ComplexRegion(r1*theta1, polar=True)
    assert 0.5 + 0.6*I in c3
    assert I in c3
    assert 1 in c3
    assert 0 in c3
    assert 1 + I not in c3
    assert 1 - I not in c3


def test_ComplexRegion_intersect():

    # Polar form
    X_axis = ComplexRegion(Interval(0, oo)*FiniteSet(0, S.Pi), polar=True)

    unit_disk = ComplexRegion(Interval(0, 1)*Interval(0, 2*S.Pi), polar=True)
    upper_half_unit_disk = ComplexRegion(Interval(0, 1)*Interval(0, S.Pi), polar=True)
    upper_half_disk = ComplexRegion(Interval(0, oo)*Interval(0, S.Pi), polar=True)
    lower_half_disk = ComplexRegion(Interval(0, oo)*Interval(S.Pi, 2*S.Pi), polar=True)
    right_half_disk = ComplexRegion(Interval(0, oo)*Interval(-S.Pi/2, S.Pi/2), polar=True)
    first_quad_disk = ComplexRegion(Interval(0, oo)*Interval(0, S.Pi/2), polar=True)

    assert upper_half_disk.intersect(unit_disk) == upper_half_unit_disk
    assert right_half_disk.intersect(first_quad_disk) == first_quad_disk
    assert upper_half_disk.intersect(right_half_disk) == first_quad_disk
    assert upper_half_disk.intersect(lower_half_disk) == X_axis

    c1 = ComplexRegion(Interval(0, 4)*Interval(0, 2*S.Pi), polar=True)
    assert c1.intersect(Interval(1, 5)) == Interval(1, 4)
    assert c1.intersect(Interval(4, 9)) == FiniteSet(4)
    assert c1.intersect(Interval(5, 12)) is S.EmptySet

    # Rectangular form
    X_axis = ComplexRegion(Interval(-oo, oo)*FiniteSet(0))

    unit_square = ComplexRegion(Interval(-1, 1)*Interval(-1, 1))
    upper_half_unit_square = ComplexRegion(Interval(-1, 1)*Interval(0, 1))
    upper_half_plane = ComplexRegion(Interval(-oo, oo)*Interval(0, oo))
    lower_half_plane = ComplexRegion(Interval(-oo, oo)*Interval(-oo, 0))
    right_half_plane = ComplexRegion(Interval(0, oo)*Interval(-oo, oo))
    first_quad_plane = ComplexRegion(Interval(0, oo)*Interval(0, oo))

    assert upper_half_plane.intersect(unit_square) == upper_half_unit_square
    assert right_half_plane.intersect(first_quad_plane) == first_quad_plane
    assert upper_half_plane.intersect(right_half_plane) == first_quad_plane
    assert upper_half_plane.intersect(lower_half_plane) == X_axis

    c1 = ComplexRegion(Interval(-5, 5)*Interval(-10, 10))
    assert c1.intersect(Interval(2, 7)) == Interval(2, 5)
    assert c1.intersect(Interval(5, 7)) == FiniteSet(5)
    assert c1.intersect(Interval(6, 9)) is S.EmptySet

    # unevaluated object
    C1 = ComplexRegion(Interval(0, 1)*Interval(0, 2*S.Pi), polar=True)
    C2 = ComplexRegion(Interval(-1, 1)*Interval(-1, 1))
    assert C1.intersect(C2) == Intersection(C1, C2, evaluate=False)


def test_ComplexRegion_union():

    # Polar form
    c1 = ComplexRegion(Interval(0, 1)*Interval(0, 2*S.Pi), polar=True)
    c2 = ComplexRegion(Interval(0, 1)*Interval(0, S.Pi), polar=True)
    c3 = ComplexRegion(Interval(0, oo)*Interval(0, S.Pi), polar=True)
    c4 = ComplexRegion(Interval(0, oo)*Interval(S.Pi, 2*S.Pi), polar=True)

    p1 = Union(Interval(0, 1)*Interval(0, 2*S.Pi), Interval(0, 1)*Interval(0, S.Pi))
    p2 = Union(Interval(0, oo)*Interval(0, S.Pi), Interval(0, oo)*Interval(S.Pi, 2*S.Pi))

    assert c1.union(c2) == ComplexRegion(p1, polar=True)
    assert c3.union(c4) == ComplexRegion(p2, polar=True)

    # Rectangular form
    c5 = ComplexRegion(Interval(2, 5)*Interval(6, 9))
    c6 = ComplexRegion(Interval(4, 6)*Interval(10, 12))
    c7 = ComplexRegion(Interval(0, 10)*Interval(-10, 0))
    c8 = ComplexRegion(Interval(12, 16)*Interval(14, 20))

    p3 = Union(Interval(2, 5)*Interval(6, 9), Interval(4, 6)*Interval(10, 12))
    p4 = Union(Interval(0, 10)*Interval(-10, 0), Interval(12, 16)*Interval(14, 20))

    assert c5.union(c6) == ComplexRegion(p3)
    assert c7.union(c8) == ComplexRegion(p4)

    assert c1.union(Interval(2, 4)) == Union(c1, Interval(2, 4), evaluate=False)
    assert c5.union(Interval(2, 4)) == Union(c5, ComplexRegion.from_real(Interval(2, 4)))


def test_ComplexRegion_measure():
    a, b = Interval(2, 5), Interval(4, 8)
    theta1, theta2 = Interval(0, 2*S.Pi), Interval(0, S.Pi)
    c1 = ComplexRegion(a*b)
    c2 = ComplexRegion(Union(a*theta1, b*theta2), polar=True)

    assert c1.measure == 12
    assert c2.measure == 9*pi


def test_normalize_theta_set():

    # Interval
    assert normalize_theta_set(Interval(pi, 2*pi)) == \
        Union(FiniteSet(0), Interval.Ropen(pi, 2*pi))
    assert normalize_theta_set(Interval(9*pi/2, 5*pi)) == Interval(pi/2, pi)
    assert normalize_theta_set(Interval(-3*pi/2, pi/2)) == Interval.Ropen(0, 2*pi)
    assert normalize_theta_set(Interval.open(-3*pi/2, pi/2)) == \
        Union(Interval.Ropen(0, pi/2), Interval.open(pi/2, 2*pi))
    assert normalize_theta_set(Interval.open(-7*pi/2, -3*pi/2)) == \
        Union(Interval.Ropen(0, pi/2), Interval.open(pi/2, 2*pi))
    assert normalize_theta_set(Interval(-pi/2, pi/2)) == \
        Union(Interval(0, pi/2), Interval.Ropen(3*pi/2, 2*pi))
    assert normalize_theta_set(Interval.open(-pi/2, pi/2)) == \
        Union(Interval.Ropen(0, pi/2), Interval.open(3*pi/2, 2*pi))
    assert normalize_theta_set(Interval(-4*pi, 3*pi)) == Interval.Ropen(0, 2*pi)
    assert normalize_theta_set(Interval(-3*pi/2, -pi/2)) == Interval(pi/2, 3*pi/2)
    assert normalize_theta_set(Interval.open(0, 2*pi)) == Interval.open(0, 2*pi)
    assert normalize_theta_set(Interval.Ropen(-pi/2, pi/2)) == \
        Union(Interval.Ropen(0, pi/2), Interval.Ropen(3*pi/2, 2*pi))
    assert normalize_theta_set(Interval.Lopen(-pi/2, pi/2)) == \
        Union(Interval(0, pi/2), Interval.open(3*pi/2, 2*pi))
    assert normalize_theta_set(Interval(-pi/2, pi/2)) == \
        Union(Interval(0, pi/2), Interval.Ropen(3*pi/2, 2*pi))
    assert normalize_theta_set(Interval.open(4*pi, 9*pi/2)) == Interval.open(0, pi/2)
    assert normalize_theta_set(Interval.Lopen(4*pi, 9*pi/2)) == Interval.Lopen(0, pi/2)
    assert normalize_theta_set(Interval.Ropen(4*pi, 9*pi/2)) == Interval.Ropen(0, pi/2)
    assert normalize_theta_set(Interval.open(3*pi, 5*pi)) == \
        Union(Interval.Ropen(0, pi), Interval.open(pi, 2*pi))

    # FiniteSet
    assert normalize_theta_set(FiniteSet(0, pi, 3*pi)) == FiniteSet(0, pi)
    assert normalize_theta_set(FiniteSet(0, pi/2, pi, 2*pi)) == FiniteSet(0, pi/2, pi)
    assert normalize_theta_set(FiniteSet(0, -pi/2, -pi, -2*pi)) == FiniteSet(0, pi, 3*pi/2)
    assert normalize_theta_set(FiniteSet(-3*pi/2, pi/2)) == \
        FiniteSet(pi/2)
    assert normalize_theta_set(FiniteSet(2*pi)) == FiniteSet(0)

    # Unions
    assert normalize_theta_set(Union(Interval(0, pi/3), Interval(pi/2, pi))) == \
        Union(Interval(0, pi/3), Interval(pi/2, pi))
    assert normalize_theta_set(Union(Interval(0, pi), Interval(2*pi, 7*pi/3))) == \
        Interval(0, pi)

    # ValueError for non-real sets
    raises(ValueError, lambda: normalize_theta_set(S.Complexes))


def test_ComplexRegion_FiniteSet():
    x, y, z, a, b, c = symbols('x y z a b c')

    # Issue #9669
    assert ComplexRegion(FiniteSet(a, b, c)*FiniteSet(x, y, z)) == \
        FiniteSet(a + I*x, a + I*y, a + I*z, b + I*x, b + I*y,
                  b + I*z, c + I*x, c + I*y, c + I*z)
    assert ComplexRegion(FiniteSet(2)*FiniteSet(3)) == FiniteSet(2 + 3*I)


def test_union_RealSubSet():
    assert (S.Complexes).union(Interval(1, 2)) == S.Complexes
    assert (S.Complexes).union(S.Integers) == S.Complexes


def test_issue_9980():
    c1 = ComplexRegion(Interval(1, 2)*Interval(2, 3))
    c2 = ComplexRegion(Interval(1, 5)*Interval(1, 3))
    R = Union(c1, c2)
    assert simplify(R) == ComplexRegion(Union(Interval(1, 2)*Interval(2, 3), \
                                    Interval(1, 5)*Interval(1, 3)), False)
    assert c1.func(*c1.args) == c1
    assert R.func(*R.args) == R

def test_issue_11732():
    interval12 = Interval(1, 2)
    finiteset1234 = FiniteSet(1, 2, 3, 4)
    pointComplex = Tuple(1, 5)

    assert (interval12 in S.Naturals) == False
    assert (interval12 in S.Naturals0) == False
    assert (interval12 in S.Integers) == False
    assert (interval12 in S.Complexes) == False

    assert (finiteset1234 in S.Naturals) == False
    assert (finiteset1234 in S.Naturals0) == False
    assert (finiteset1234 in S.Integers) == False
    assert (finiteset1234 in S.Complexes) == False

    assert (pointComplex in S.Naturals) == False
    assert (pointComplex in S.Naturals0) == False
    assert (pointComplex in S.Integers) == False
    assert (pointComplex in S.Complexes) == True


def test_issue_11730():
    unit = Interval(0, 1)
    square = ComplexRegion(unit ** 2)

    assert Union(S.Complexes, FiniteSet(oo)) != S.Complexes
    assert Union(S.Complexes, FiniteSet(eye(4))) != S.Complexes
    assert Union(unit, square) == square
    assert Intersection(S.Reals, square) == unit


def test_issue_11938():
    unit = Interval(0, 1)
    ival = Interval(1, 2)
    cr1 = ComplexRegion(ival * unit)

    assert Intersection(cr1, S.Reals) == ival
    assert Intersection(cr1, unit) == FiniteSet(1)

    arg1 = Interval(0, S.Pi)
    arg2 = FiniteSet(S.Pi)
    arg3 = Interval(S.Pi / 4, 3 * S.Pi / 4)
    cp1 = ComplexRegion(unit * arg1, polar=True)
    cp2 = ComplexRegion(unit * arg2, polar=True)
    cp3 = ComplexRegion(unit * arg3, polar=True)

    assert Intersection(cp1, S.Reals) == Interval(-1, 1)
    assert Intersection(cp2, S.Reals) == Interval(-1, 0)
    assert Intersection(cp3, S.Reals) == FiniteSet(0)

def test_issue_11914():
    a, b = Interval(0, 1), Interval(0, pi)
    c, d = Interval(2, 3), Interval(pi, 3 * pi / 2)
    cp1 = ComplexRegion(a * b, polar=True)
    cp2 = ComplexRegion(c * d, polar=True)

    assert -3 in cp1.union(cp2)
    assert -3 in cp2.union(cp1)
    assert -5 not in cp1.union(cp2)
