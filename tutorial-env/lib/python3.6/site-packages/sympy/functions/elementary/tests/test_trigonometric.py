from sympy import (symbols, Symbol, nan, oo, zoo, I, sinh, sin, pi, atan,
        acos, Rational, sqrt, asin, acot, coth, E, S, tan, tanh, cos,
        cosh, atan2, exp, log, asinh, acoth, atanh, O, cancel, Matrix, re, im,
        Float, Pow, gcd, sec, csc, cot, diff, simplify, Heaviside, arg,
        conjugate, series, FiniteSet, asec, acsc, Mul, sinc, jn, Product,
        AccumBounds)
from sympy.core.compatibility import range
from sympy.utilities.pytest import XFAIL, slow, raises
from sympy.core.relational import Ne, Eq
from sympy.functions.elementary.piecewise import Piecewise

x, y, z = symbols('x y z')
r = Symbol('r', real=True)
k = Symbol('k', integer=True)
p = Symbol('p', positive=True)
n = Symbol('n', negative=True)
a = Symbol('a', algebraic=True)
na = Symbol('na', nonzero=True, algebraic=True)


def test_sin():
    x, y = symbols('x y')

    assert sin.nargs == FiniteSet(1)
    assert sin(nan) == nan
    assert sin(zoo) == nan

    assert sin(oo) == AccumBounds(-1, 1)
    assert sin(oo) - sin(oo) == AccumBounds(-2, 2)
    assert sin(oo*I) == oo*I
    assert sin(-oo*I) == -oo*I
    assert 0*sin(oo) == S.Zero
    assert 0/sin(oo) == S.Zero
    assert 0 + sin(oo) == AccumBounds(-1, 1)
    assert 5 + sin(oo) == AccumBounds(4, 6)

    assert sin(0) == 0

    assert sin(asin(x)) == x
    assert sin(atan(x)) == x / sqrt(1 + x**2)
    assert sin(acos(x)) == sqrt(1 - x**2)
    assert sin(acot(x)) == 1 / (sqrt(1 + 1 / x**2) * x)
    assert sin(acsc(x)) == 1 / x
    assert sin(asec(x)) == sqrt(1 - 1 / x**2)
    assert sin(atan2(y, x)) == y / sqrt(x**2 + y**2)

    assert sin(pi*I) == sinh(pi)*I
    assert sin(-pi*I) == -sinh(pi)*I
    assert sin(-2*I) == -sinh(2)*I

    assert sin(pi) == 0
    assert sin(-pi) == 0
    assert sin(2*pi) == 0
    assert sin(-2*pi) == 0
    assert sin(-3*10**73*pi) == 0
    assert sin(7*10**103*pi) == 0

    assert sin(pi/2) == 1
    assert sin(-pi/2) == -1
    assert sin(5*pi/2) == 1
    assert sin(7*pi/2) == -1

    ne = symbols('ne', integer=True, even=False)
    e = symbols('e', even=True)
    assert sin(pi*ne/2) == (-1)**(ne/2 - S.Half)
    assert sin(pi*k/2).func == sin
    assert sin(pi*e/2) == 0
    assert sin(pi*k) == 0
    assert sin(pi*k).subs(k, 3) == sin(pi*k/2).subs(k, 6)  # issue 8298

    assert sin(pi/3) == S.Half*sqrt(3)
    assert sin(-2*pi/3) == -S.Half*sqrt(3)

    assert sin(pi/4) == S.Half*sqrt(2)
    assert sin(-pi/4) == -S.Half*sqrt(2)
    assert sin(17*pi/4) == S.Half*sqrt(2)
    assert sin(-3*pi/4) == -S.Half*sqrt(2)

    assert sin(pi/6) == S.Half
    assert sin(-pi/6) == -S.Half
    assert sin(7*pi/6) == -S.Half
    assert sin(-5*pi/6) == -S.Half

    assert sin(1*pi/5) == sqrt((5 - sqrt(5)) / 8)
    assert sin(2*pi/5) == sqrt((5 + sqrt(5)) / 8)
    assert sin(3*pi/5) == sin(2*pi/5)
    assert sin(4*pi/5) == sin(1*pi/5)
    assert sin(6*pi/5) == -sin(1*pi/5)
    assert sin(8*pi/5) == -sin(2*pi/5)

    assert sin(-1273*pi/5) == -sin(2*pi/5)

    assert sin(pi/8) == sqrt((2 - sqrt(2))/4)

    assert sin(pi/10) == -S(1)/4 + sqrt(5)/4

    assert sin(pi/12) == -sqrt(2)/4 + sqrt(6)/4
    assert sin(5*pi/12) == sqrt(2)/4 + sqrt(6)/4
    assert sin(-7*pi/12) == -sqrt(2)/4 - sqrt(6)/4
    assert sin(-11*pi/12) == sqrt(2)/4 - sqrt(6)/4

    assert sin(104*pi/105) == sin(pi/105)
    assert sin(106*pi/105) == -sin(pi/105)

    assert sin(-104*pi/105) == -sin(pi/105)
    assert sin(-106*pi/105) == sin(pi/105)

    assert sin(x*I) == sinh(x)*I

    assert sin(k*pi) == 0
    assert sin(17*k*pi) == 0

    assert sin(k*pi*I) == sinh(k*pi)*I

    assert sin(r).is_real is True

    assert sin(0, evaluate=False).is_algebraic
    assert sin(a).is_algebraic is None
    assert sin(na).is_algebraic is False
    q = Symbol('q', rational=True)
    assert sin(pi*q).is_algebraic
    qn = Symbol('qn', rational=True, nonzero=True)
    assert sin(qn).is_rational is False
    assert sin(q).is_rational is None  # issue 8653

    assert isinstance(sin( re(x) - im(y)), sin) is True
    assert isinstance(sin(-re(x) + im(y)), sin) is False

    for d in list(range(1, 22)) + [60, 85]:
        for n in range(0, d*2 + 1):
            x = n*pi/d
            e = abs( float(sin(x)) - sin(float(x)) )
            assert e < 1e-12


def test_sin_cos():
    for d in [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 24, 30, 40, 60, 120]:  # list is not exhaustive...
        for n in range(-2*d, d*2):
            x = n*pi/d
            assert sin(x + pi/2) == cos(x), "fails for %d*pi/%d" % (n, d)
            assert sin(x - pi/2) == -cos(x), "fails for %d*pi/%d" % (n, d)
            assert sin(x) == cos(x - pi/2), "fails for %d*pi/%d" % (n, d)
            assert -sin(x) == cos(x + pi/2), "fails for %d*pi/%d" % (n, d)


def test_sin_series():
    assert sin(x).series(x, 0, 9) == \
        x - x**3/6 + x**5/120 - x**7/5040 + O(x**9)


def test_sin_rewrite():
    assert sin(x).rewrite(exp) == -I*(exp(I*x) - exp(-I*x))/2
    assert sin(x).rewrite(tan) == 2*tan(x/2)/(1 + tan(x/2)**2)
    assert sin(x).rewrite(cot) == 2*cot(x/2)/(1 + cot(x/2)**2)
    assert sin(sinh(x)).rewrite(
        exp).subs(x, 3).n() == sin(x).rewrite(exp).subs(x, sinh(3)).n()
    assert sin(cosh(x)).rewrite(
        exp).subs(x, 3).n() == sin(x).rewrite(exp).subs(x, cosh(3)).n()
    assert sin(tanh(x)).rewrite(
        exp).subs(x, 3).n() == sin(x).rewrite(exp).subs(x, tanh(3)).n()
    assert sin(coth(x)).rewrite(
        exp).subs(x, 3).n() == sin(x).rewrite(exp).subs(x, coth(3)).n()
    assert sin(sin(x)).rewrite(
        exp).subs(x, 3).n() == sin(x).rewrite(exp).subs(x, sin(3)).n()
    assert sin(cos(x)).rewrite(
        exp).subs(x, 3).n() == sin(x).rewrite(exp).subs(x, cos(3)).n()
    assert sin(tan(x)).rewrite(
        exp).subs(x, 3).n() == sin(x).rewrite(exp).subs(x, tan(3)).n()
    assert sin(cot(x)).rewrite(
        exp).subs(x, 3).n() == sin(x).rewrite(exp).subs(x, cot(3)).n()
    assert sin(log(x)).rewrite(Pow) == I*x**-I / 2 - I*x**I /2
    assert sin(x).rewrite(csc) == 1/csc(x)
    assert sin(x).rewrite(cos) == cos(x - pi / 2, evaluate=False)
    assert sin(x).rewrite(sec) == 1 / sec(x - pi / 2, evaluate=False)


def test_sin_expansion():
    # Note: these formulas are not unique.  The ones here come from the
    # Chebyshev formulas.
    assert sin(x + y).expand(trig=True) == sin(x)*cos(y) + cos(x)*sin(y)
    assert sin(x - y).expand(trig=True) == sin(x)*cos(y) - cos(x)*sin(y)
    assert sin(y - x).expand(trig=True) == cos(x)*sin(y) - sin(x)*cos(y)
    assert sin(2*x).expand(trig=True) == 2*sin(x)*cos(x)
    assert sin(3*x).expand(trig=True) == -4*sin(x)**3 + 3*sin(x)
    assert sin(4*x).expand(trig=True) == -8*sin(x)**3*cos(x) + 4*sin(x)*cos(x)
    assert sin(2).expand(trig=True) == 2*sin(1)*cos(1)
    assert sin(3).expand(trig=True) == -4*sin(1)**3 + 3*sin(1)


def test_sin_AccumBounds():
    assert sin(AccumBounds(-oo, oo)) == AccumBounds(-1, 1)
    assert sin(AccumBounds(0, oo)) == AccumBounds(-1, 1)
    assert sin(AccumBounds(-oo, 0)) == AccumBounds(-1, 1)
    assert sin(AccumBounds(0, 2*S.Pi)) == AccumBounds(-1, 1)
    assert sin(AccumBounds(0, 3*S.Pi/4)) == AccumBounds(0, 1)
    assert sin(AccumBounds(3*S.Pi/4, 7*S.Pi/4)) == AccumBounds(-1, sin(3*S.Pi/4))
    assert sin(AccumBounds(S.Pi/4, S.Pi/3)) == AccumBounds(sin(S.Pi/4), sin(S.Pi/3))
    assert sin(AccumBounds(3*S.Pi/4, 5*S.Pi/6)) == AccumBounds(sin(5*S.Pi/6), sin(3*S.Pi/4))


def test_trig_symmetry():
    assert sin(-x) == -sin(x)
    assert cos(-x) == cos(x)
    assert tan(-x) == -tan(x)
    assert cot(-x) == -cot(x)
    assert sin(x + pi) == -sin(x)
    assert sin(x + 2*pi) == sin(x)
    assert sin(x + 3*pi) == -sin(x)
    assert sin(x + 4*pi) == sin(x)
    assert sin(x - 5*pi) == -sin(x)
    assert cos(x + pi) == -cos(x)
    assert cos(x + 2*pi) == cos(x)
    assert cos(x + 3*pi) == -cos(x)
    assert cos(x + 4*pi) == cos(x)
    assert cos(x - 5*pi) == -cos(x)
    assert tan(x + pi) == tan(x)
    assert tan(x - 3*pi) == tan(x)
    assert cot(x + pi) == cot(x)
    assert cot(x - 3*pi) == cot(x)
    assert sin(pi/2 - x) == cos(x)
    assert sin(3*pi/2 - x) == -cos(x)
    assert sin(5*pi/2 - x) == cos(x)
    assert cos(pi/2 - x) == sin(x)
    assert cos(3*pi/2 - x) == -sin(x)
    assert cos(5*pi/2 - x) == sin(x)
    assert tan(pi/2 - x) == cot(x)
    assert tan(3*pi/2 - x) == cot(x)
    assert tan(5*pi/2 - x) == cot(x)
    assert cot(pi/2 - x) == tan(x)
    assert cot(3*pi/2 - x) == tan(x)
    assert cot(5*pi/2 - x) == tan(x)
    assert sin(pi/2 + x) == cos(x)
    assert cos(pi/2 + x) == -sin(x)
    assert tan(pi/2 + x) == -cot(x)
    assert cot(pi/2 + x) == -tan(x)


def test_cos():
    x, y = symbols('x y')

    assert cos.nargs == FiniteSet(1)
    assert cos(nan) == nan

    assert cos(oo) == AccumBounds(-1, 1)
    assert cos(oo) - cos(oo) == AccumBounds(-2, 2)
    assert cos(oo*I) == oo
    assert cos(-oo*I) == oo
    assert cos(zoo) == nan

    assert cos(0) == 1

    assert cos(acos(x)) == x
    assert cos(atan(x)) == 1 / sqrt(1 + x**2)
    assert cos(asin(x)) == sqrt(1 - x**2)
    assert cos(acot(x)) == 1 / sqrt(1 + 1 / x**2)
    assert cos(acsc(x)) == sqrt(1 - 1 / x**2)
    assert cos(asec(x)) == 1 / x
    assert cos(atan2(y, x)) == x / sqrt(x**2 + y**2)

    assert cos(pi*I) == cosh(pi)
    assert cos(-pi*I) == cosh(pi)
    assert cos(-2*I) == cosh(2)

    assert cos(pi/2) == 0
    assert cos(-pi/2) == 0
    assert cos(pi/2) == 0
    assert cos(-pi/2) == 0
    assert cos((-3*10**73 + 1)*pi/2) == 0
    assert cos((7*10**103 + 1)*pi/2) == 0

    n = symbols('n', integer=True, even=False)
    e = symbols('e', even=True)
    assert cos(pi*n/2) == 0
    assert cos(pi*e/2) == (-1)**(e/2)

    assert cos(pi) == -1
    assert cos(-pi) == -1
    assert cos(2*pi) == 1
    assert cos(5*pi) == -1
    assert cos(8*pi) == 1

    assert cos(pi/3) == S.Half
    assert cos(-2*pi/3) == -S.Half

    assert cos(pi/4) == S.Half*sqrt(2)
    assert cos(-pi/4) == S.Half*sqrt(2)
    assert cos(11*pi/4) == -S.Half*sqrt(2)
    assert cos(-3*pi/4) == -S.Half*sqrt(2)

    assert cos(pi/6) == S.Half*sqrt(3)
    assert cos(-pi/6) == S.Half*sqrt(3)
    assert cos(7*pi/6) == -S.Half*sqrt(3)
    assert cos(-5*pi/6) == -S.Half*sqrt(3)

    assert cos(1*pi/5) == (sqrt(5) + 1)/4
    assert cos(2*pi/5) == (sqrt(5) - 1)/4
    assert cos(3*pi/5) == -cos(2*pi/5)
    assert cos(4*pi/5) == -cos(1*pi/5)
    assert cos(6*pi/5) == -cos(1*pi/5)
    assert cos(8*pi/5) == cos(2*pi/5)

    assert cos(-1273*pi/5) == -cos(2*pi/5)

    assert cos(pi/8) == sqrt((2 + sqrt(2))/4)

    assert cos(pi/12) == sqrt(2)/4 + sqrt(6)/4
    assert cos(5*pi/12) == -sqrt(2)/4 + sqrt(6)/4
    assert cos(7*pi/12) == sqrt(2)/4 - sqrt(6)/4
    assert cos(11*pi/12) == -sqrt(2)/4 - sqrt(6)/4

    assert cos(104*pi/105) == -cos(pi/105)
    assert cos(106*pi/105) == -cos(pi/105)

    assert cos(-104*pi/105) == -cos(pi/105)
    assert cos(-106*pi/105) == -cos(pi/105)

    assert cos(x*I) == cosh(x)
    assert cos(k*pi*I) == cosh(k*pi)

    assert cos(r).is_real is True

    assert cos(0, evaluate=False).is_algebraic
    assert cos(a).is_algebraic is None
    assert cos(na).is_algebraic is False
    q = Symbol('q', rational=True)
    assert cos(pi*q).is_algebraic
    assert cos(2*pi/7).is_algebraic

    assert cos(k*pi) == (-1)**k
    assert cos(2*k*pi) == 1

    for d in list(range(1, 22)) + [60, 85]:
        for n in range(0, 2*d + 1):
            x = n*pi/d
            e = abs( float(cos(x)) - cos(float(x)) )
            assert e < 1e-12


def test_issue_6190():
    c = Float('123456789012345678901234567890.25', '')
    for cls in [sin, cos, tan, cot]:
        assert cls(c*pi) == cls(pi/4)
        assert cls(4.125*pi) == cls(pi/8)
        assert cls(4.7*pi) == cls((4.7 % 2)*pi)


def test_cos_series():
    assert cos(x).series(x, 0, 9) == \
        1 - x**2/2 + x**4/24 - x**6/720 + x**8/40320 + O(x**9)


def test_cos_rewrite():
    assert cos(x).rewrite(exp) == exp(I*x)/2 + exp(-I*x)/2
    assert cos(x).rewrite(tan) == (1 - tan(x/2)**2)/(1 + tan(x/2)**2)
    assert cos(x).rewrite(cot) == -(1 - cot(x/2)**2)/(1 + cot(x/2)**2)
    assert cos(sinh(x)).rewrite(
        exp).subs(x, 3).n() == cos(x).rewrite(exp).subs(x, sinh(3)).n()
    assert cos(cosh(x)).rewrite(
        exp).subs(x, 3).n() == cos(x).rewrite(exp).subs(x, cosh(3)).n()
    assert cos(tanh(x)).rewrite(
        exp).subs(x, 3).n() == cos(x).rewrite(exp).subs(x, tanh(3)).n()
    assert cos(coth(x)).rewrite(
        exp).subs(x, 3).n() == cos(x).rewrite(exp).subs(x, coth(3)).n()
    assert cos(sin(x)).rewrite(
        exp).subs(x, 3).n() == cos(x).rewrite(exp).subs(x, sin(3)).n()
    assert cos(cos(x)).rewrite(
        exp).subs(x, 3).n() == cos(x).rewrite(exp).subs(x, cos(3)).n()
    assert cos(tan(x)).rewrite(
        exp).subs(x, 3).n() == cos(x).rewrite(exp).subs(x, tan(3)).n()
    assert cos(cot(x)).rewrite(
        exp).subs(x, 3).n() == cos(x).rewrite(exp).subs(x, cot(3)).n()
    assert cos(log(x)).rewrite(Pow) == x**I/2 + x**-I/2
    assert cos(x).rewrite(sec) == 1/sec(x)
    assert cos(x).rewrite(sin) == sin(x + pi/2, evaluate=False)
    assert cos(x).rewrite(csc) == 1/csc(-x + pi/2, evaluate=False)


def test_cos_expansion():
    assert cos(x + y).expand(trig=True) == cos(x)*cos(y) - sin(x)*sin(y)
    assert cos(x - y).expand(trig=True) == cos(x)*cos(y) + sin(x)*sin(y)
    assert cos(y - x).expand(trig=True) == cos(x)*cos(y) + sin(x)*sin(y)
    assert cos(2*x).expand(trig=True) == 2*cos(x)**2 - 1
    assert cos(3*x).expand(trig=True) == 4*cos(x)**3 - 3*cos(x)
    assert cos(4*x).expand(trig=True) == 8*cos(x)**4 - 8*cos(x)**2 + 1
    assert cos(2).expand(trig=True) == 2*cos(1)**2 - 1
    assert cos(3).expand(trig=True) == 4*cos(1)**3 - 3*cos(1)


def test_cos_AccumBounds():
    assert cos(AccumBounds(-oo, oo)) == AccumBounds(-1, 1)
    assert cos(AccumBounds(0, oo)) == AccumBounds(-1, 1)
    assert cos(AccumBounds(-oo, 0)) == AccumBounds(-1, 1)
    assert cos(AccumBounds(0, 2*S.Pi)) == AccumBounds(-1, 1)
    assert cos(AccumBounds(-S.Pi/3, S.Pi/4)) == AccumBounds(cos(-S.Pi/3), 1)
    assert cos(AccumBounds(3*S.Pi/4, 5*S.Pi/4)) == AccumBounds(-1, cos(3*S.Pi/4))
    assert cos(AccumBounds(5*S.Pi/4, 4*S.Pi/3)) == AccumBounds(cos(5*S.Pi/4), cos(4*S.Pi/3))
    assert cos(AccumBounds(S.Pi/4, S.Pi/3)) == AccumBounds(cos(S.Pi/3), cos(S.Pi/4))


def test_tan():
    assert tan(nan) == nan

    assert tan(zoo) == nan
    assert tan(oo) == AccumBounds(-oo, oo)
    assert tan(oo) - tan(oo) == AccumBounds(-oo, oo)
    assert tan.nargs == FiniteSet(1)
    assert tan(oo*I) == I
    assert tan(-oo*I) == -I

    assert tan(0) == 0

    assert tan(atan(x)) == x
    assert tan(asin(x)) == x / sqrt(1 - x**2)
    assert tan(acos(x)) == sqrt(1 - x**2) / x
    assert tan(acot(x)) == 1 / x
    assert tan(acsc(x)) == 1 / (sqrt(1 - 1 / x**2) * x)
    assert tan(asec(x)) == sqrt(1 - 1 / x**2) * x
    assert tan(atan2(y, x)) == y/x

    assert tan(pi*I) == tanh(pi)*I
    assert tan(-pi*I) == -tanh(pi)*I
    assert tan(-2*I) == -tanh(2)*I

    assert tan(pi) == 0
    assert tan(-pi) == 0
    assert tan(2*pi) == 0
    assert tan(-2*pi) == 0
    assert tan(-3*10**73*pi) == 0

    assert tan(pi/2) == zoo
    assert tan(3*pi/2) == zoo

    assert tan(pi/3) == sqrt(3)
    assert tan(-2*pi/3) == sqrt(3)

    assert tan(pi/4) == S.One
    assert tan(-pi/4) == -S.One
    assert tan(17*pi/4) == S.One
    assert tan(-3*pi/4) == S.One

    assert tan(pi/6) == 1/sqrt(3)
    assert tan(-pi/6) == -1/sqrt(3)
    assert tan(7*pi/6) == 1/sqrt(3)
    assert tan(-5*pi/6) == 1/sqrt(3)

    assert tan(pi/8).expand() == -1 + sqrt(2)
    assert tan(3*pi/8).expand() == 1 + sqrt(2)
    assert tan(5*pi/8).expand() == -1 - sqrt(2)
    assert tan(7*pi/8).expand() == 1 - sqrt(2)

    assert tan(pi/12) == -sqrt(3) + 2
    assert tan(5*pi/12) == sqrt(3) + 2
    assert tan(7*pi/12) == -sqrt(3) - 2
    assert tan(11*pi/12) == sqrt(3) - 2

    assert tan(pi/24).radsimp() == -2 - sqrt(3) + sqrt(2) + sqrt(6)
    assert tan(5*pi/24).radsimp() == -2 + sqrt(3) - sqrt(2) + sqrt(6)
    assert tan(7*pi/24).radsimp() == 2 - sqrt(3) - sqrt(2) + sqrt(6)
    assert tan(11*pi/24).radsimp() == 2 + sqrt(3) + sqrt(2) + sqrt(6)
    assert tan(13*pi/24).radsimp() == -2 - sqrt(3) - sqrt(2) - sqrt(6)
    assert tan(17*pi/24).radsimp() == -2 + sqrt(3) + sqrt(2) - sqrt(6)
    assert tan(19*pi/24).radsimp() == 2 - sqrt(3) + sqrt(2) - sqrt(6)
    assert tan(23*pi/24).radsimp() == 2 + sqrt(3) - sqrt(2) - sqrt(6)

    assert 1 == (tan(8*pi/15)*cos(8*pi/15)/sin(8*pi/15)).ratsimp()

    assert tan(x*I) == tanh(x)*I

    assert tan(k*pi) == 0
    assert tan(17*k*pi) == 0

    assert tan(k*pi*I) == tanh(k*pi)*I

    assert tan(r).is_real is True

    assert tan(0, evaluate=False).is_algebraic
    assert tan(a).is_algebraic is None
    assert tan(na).is_algebraic is False

    assert tan(10*pi/7) == tan(3*pi/7)
    assert tan(11*pi/7) == -tan(3*pi/7)
    assert tan(-11*pi/7) == tan(3*pi/7)

    assert tan(15*pi/14) == tan(pi/14)
    assert tan(-15*pi/14) == -tan(pi/14)


def test_tan_series():
    assert tan(x).series(x, 0, 9) == \
        x + x**3/3 + 2*x**5/15 + 17*x**7/315 + O(x**9)


def test_tan_rewrite():
    neg_exp, pos_exp = exp(-x*I), exp(x*I)
    assert tan(x).rewrite(exp) == I*(neg_exp - pos_exp)/(neg_exp + pos_exp)
    assert tan(x).rewrite(sin) == 2*sin(x)**2/sin(2*x)
    assert tan(x).rewrite(cos) == cos(x - S.Pi/2, evaluate=False)/cos(x)
    assert tan(x).rewrite(cot) == 1/cot(x)
    assert tan(sinh(x)).rewrite(
        exp).subs(x, 3).n() == tan(x).rewrite(exp).subs(x, sinh(3)).n()
    assert tan(cosh(x)).rewrite(
        exp).subs(x, 3).n() == tan(x).rewrite(exp).subs(x, cosh(3)).n()
    assert tan(tanh(x)).rewrite(
        exp).subs(x, 3).n() == tan(x).rewrite(exp).subs(x, tanh(3)).n()
    assert tan(coth(x)).rewrite(
        exp).subs(x, 3).n() == tan(x).rewrite(exp).subs(x, coth(3)).n()
    assert tan(sin(x)).rewrite(
        exp).subs(x, 3).n() == tan(x).rewrite(exp).subs(x, sin(3)).n()
    assert tan(cos(x)).rewrite(
        exp).subs(x, 3).n() == tan(x).rewrite(exp).subs(x, cos(3)).n()
    assert tan(tan(x)).rewrite(
        exp).subs(x, 3).n() == tan(x).rewrite(exp).subs(x, tan(3)).n()
    assert tan(cot(x)).rewrite(
        exp).subs(x, 3).n() == tan(x).rewrite(exp).subs(x, cot(3)).n()
    assert tan(log(x)).rewrite(Pow) == I*(x**-I - x**I)/(x**-I + x**I)
    assert 0 == (cos(pi/34)*tan(pi/34) - sin(pi/34)).rewrite(pow)
    assert 0 == (cos(pi/17)*tan(pi/17) - sin(pi/17)).rewrite(pow)
    assert tan(pi/19).rewrite(pow) == tan(pi/19)
    assert tan(8*pi/19).rewrite(sqrt) == tan(8*pi/19)
    assert tan(x).rewrite(sec) == sec(x)/sec(x - pi/2, evaluate=False)
    assert tan(x).rewrite(csc) == csc(-x + pi/2, evaluate=False)/csc(x)


def test_tan_subs():
    assert tan(x).subs(tan(x), y) == y
    assert tan(x).subs(x, y) == tan(y)
    assert tan(x).subs(x, S.Pi/2) == zoo
    assert tan(x).subs(x, 3*S.Pi/2) == zoo


def test_tan_expansion():
    assert tan(x + y).expand(trig=True) == ((tan(x) + tan(y))/(1 - tan(x)*tan(y))).expand()
    assert tan(x - y).expand(trig=True) == ((tan(x) - tan(y))/(1 + tan(x)*tan(y))).expand()
    assert tan(x + y + z).expand(trig=True) == (
        (tan(x) + tan(y) + tan(z) - tan(x)*tan(y)*tan(z))/
        (1 - tan(x)*tan(y) - tan(x)*tan(z) - tan(y)*tan(z))).expand()
    assert 0 == tan(2*x).expand(trig=True).rewrite(tan).subs([(tan(x), Rational(1, 7))])*24 - 7
    assert 0 == tan(3*x).expand(trig=True).rewrite(tan).subs([(tan(x), Rational(1, 5))])*55 - 37
    assert 0 == tan(4*x - pi/4).expand(trig=True).rewrite(tan).subs([(tan(x), Rational(1, 5))])*239 - 1


def test_tan_AccumBounds():
    assert tan(AccumBounds(-oo, oo)) == AccumBounds(-oo, oo)
    assert tan(AccumBounds(S.Pi/3, 2*S.Pi/3)) == AccumBounds(-oo, oo)
    assert tan(AccumBounds(S.Pi/6, S.Pi/3)) == AccumBounds(tan(S.Pi/6), tan(S.Pi/3))


def test_cot():
    assert cot(nan) == nan

    assert cot.nargs == FiniteSet(1)
    assert cot(oo*I) == -I
    assert cot(-oo*I) == I
    assert cot(zoo) == nan

    assert cot(0) == zoo
    assert cot(2*pi) == zoo

    assert cot(acot(x)) == x
    assert cot(atan(x)) == 1 / x
    assert cot(asin(x)) == sqrt(1 - x**2) / x
    assert cot(acos(x)) == x / sqrt(1 - x**2)
    assert cot(acsc(x)) == sqrt(1 - 1 / x**2) * x
    assert cot(asec(x)) == 1 / (sqrt(1 - 1 / x**2) * x)
    assert cot(atan2(y, x)) == x/y

    assert cot(pi*I) == -coth(pi)*I
    assert cot(-pi*I) == coth(pi)*I
    assert cot(-2*I) == coth(2)*I

    assert cot(pi) == cot(2*pi) == cot(3*pi)
    assert cot(-pi) == cot(-2*pi) == cot(-3*pi)

    assert cot(pi/2) == 0
    assert cot(-pi/2) == 0
    assert cot(5*pi/2) == 0
    assert cot(7*pi/2) == 0

    assert cot(pi/3) == 1/sqrt(3)
    assert cot(-2*pi/3) == 1/sqrt(3)

    assert cot(pi/4) == S.One
    assert cot(-pi/4) == -S.One
    assert cot(17*pi/4) == S.One
    assert cot(-3*pi/4) == S.One

    assert cot(pi/6) == sqrt(3)
    assert cot(-pi/6) == -sqrt(3)
    assert cot(7*pi/6) == sqrt(3)
    assert cot(-5*pi/6) == sqrt(3)

    assert cot(pi/8).expand() == 1 + sqrt(2)
    assert cot(3*pi/8).expand() == -1 + sqrt(2)
    assert cot(5*pi/8).expand() == 1 - sqrt(2)
    assert cot(7*pi/8).expand() == -1 - sqrt(2)

    assert cot(pi/12) == sqrt(3) + 2
    assert cot(5*pi/12) == -sqrt(3) + 2
    assert cot(7*pi/12) == sqrt(3) - 2
    assert cot(11*pi/12) == -sqrt(3) - 2

    assert cot(pi/24).radsimp() == sqrt(2) + sqrt(3) + 2 + sqrt(6)
    assert cot(5*pi/24).radsimp() == -sqrt(2) - sqrt(3) + 2 + sqrt(6)
    assert cot(7*pi/24).radsimp() == -sqrt(2) + sqrt(3) - 2 + sqrt(6)
    assert cot(11*pi/24).radsimp() == sqrt(2) - sqrt(3) - 2 + sqrt(6)
    assert cot(13*pi/24).radsimp() == -sqrt(2) + sqrt(3) + 2 - sqrt(6)
    assert cot(17*pi/24).radsimp() == sqrt(2) - sqrt(3) + 2 - sqrt(6)
    assert cot(19*pi/24).radsimp() == sqrt(2) + sqrt(3) - 2 - sqrt(6)
    assert cot(23*pi/24).radsimp() == -sqrt(2) - sqrt(3) - 2 - sqrt(6)

    assert 1 == (cot(4*pi/15)*sin(4*pi/15)/cos(4*pi/15)).ratsimp()

    assert cot(x*I) == -coth(x)*I
    assert cot(k*pi*I) == -coth(k*pi)*I

    assert cot(r).is_real is True

    assert cot(a).is_algebraic is None
    assert cot(na).is_algebraic is False

    assert cot(10*pi/7) == cot(3*pi/7)
    assert cot(11*pi/7) == -cot(3*pi/7)
    assert cot(-11*pi/7) == cot(3*pi/7)

    assert cot(39*pi/34) == cot(5*pi/34)
    assert cot(-41*pi/34) == -cot(7*pi/34)

    assert cot(x).is_finite is None
    assert cot(r).is_finite is None
    i = Symbol('i', imaginary=True)
    assert cot(i).is_finite is True

    assert cot(x).subs(x, 3*pi) == zoo


def test_cot_series():
    assert cot(x).series(x, 0, 9) == \
        1/x - x/3 - x**3/45 - 2*x**5/945 - x**7/4725 + O(x**9)
    # issue 6210
    assert cot(x**4 + x**5).series(x, 0, 1) == \
        x**(-4) - 1/x**3 + x**(-2) - 1/x + 1 + O(x)


def test_cot_rewrite():
    neg_exp, pos_exp = exp(-x*I), exp(x*I)
    assert cot(x).rewrite(exp) == I*(pos_exp + neg_exp)/(pos_exp - neg_exp)
    assert cot(x).rewrite(sin) == sin(2*x)/(2*(sin(x)**2))
    assert cot(x).rewrite(cos) == cos(x)/cos(x - pi/2, evaluate=False)
    assert cot(x).rewrite(tan) == 1/tan(x)
    assert cot(sinh(x)).rewrite(
        exp).subs(x, 3).n() == cot(x).rewrite(exp).subs(x, sinh(3)).n()
    assert cot(cosh(x)).rewrite(
        exp).subs(x, 3).n() == cot(x).rewrite(exp).subs(x, cosh(3)).n()
    assert cot(tanh(x)).rewrite(
        exp).subs(x, 3).n() == cot(x).rewrite(exp).subs(x, tanh(3)).n()
    assert cot(coth(x)).rewrite(
        exp).subs(x, 3).n() == cot(x).rewrite(exp).subs(x, coth(3)).n()
    assert cot(sin(x)).rewrite(
        exp).subs(x, 3).n() == cot(x).rewrite(exp).subs(x, sin(3)).n()
    assert cot(tan(x)).rewrite(
        exp).subs(x, 3).n() == cot(x).rewrite(exp).subs(x, tan(3)).n()
    assert cot(log(x)).rewrite(Pow) == -I*(x**-I + x**I)/(x**-I - x**I)
    assert cot(4*pi/34).rewrite(pow).ratsimp() == (cos(4*pi/34)/sin(4*pi/34)).rewrite(pow).ratsimp()
    assert cot(4*pi/17).rewrite(pow) == (cos(4*pi/17)/sin(4*pi/17)).rewrite(pow)
    assert cot(pi/19).rewrite(pow) == cot(pi/19)
    assert cot(pi/19).rewrite(sqrt) == cot(pi/19)
    assert cot(x).rewrite(sec) == sec(x - pi / 2, evaluate=False) / sec(x)
    assert cot(x).rewrite(csc) == csc(x) / csc(- x + pi / 2, evaluate=False)


def test_cot_subs():
    assert cot(x).subs(cot(x), y) == y
    assert cot(x).subs(x, y) == cot(y)
    assert cot(x).subs(x, 0) == zoo
    assert cot(x).subs(x, S.Pi) == zoo


def test_cot_expansion():
    assert cot(x + y).expand(trig=True) == ((cot(x)*cot(y) - 1)/(cot(x) + cot(y))).expand()
    assert cot(x - y).expand(trig=True) == (-(cot(x)*cot(y) + 1)/(cot(x) - cot(y))).expand()
    assert cot(x + y + z).expand(trig=True) == (
        (cot(x)*cot(y)*cot(z) - cot(x) - cot(y) - cot(z))/
        (-1 + cot(x)*cot(y) + cot(x)*cot(z) + cot(y)*cot(z))).expand()
    assert cot(3*x).expand(trig=True) == ((cot(x)**3 - 3*cot(x))/(3*cot(x)**2 - 1)).expand()
    assert 0 == cot(2*x).expand(trig=True).rewrite(cot).subs([(cot(x), Rational(1, 3))])*3 + 4
    assert 0 == cot(3*x).expand(trig=True).rewrite(cot).subs([(cot(x), Rational(1, 5))])*55 - 37
    assert 0 == cot(4*x - pi/4).expand(trig=True).rewrite(cot).subs([(cot(x), Rational(1, 7))])*863 + 191


def test_cot_AccumBounds():
    assert cot(AccumBounds(-oo, oo)) == AccumBounds(-oo, oo)
    assert cot(AccumBounds(-S.Pi/3, S.Pi/3)) == AccumBounds(-oo, oo)
    assert cot(AccumBounds(S.Pi/6, S.Pi/3)) == AccumBounds(cot(S.Pi/3), cot(S.Pi/6))


def test_sinc():
    assert isinstance(sinc(x), sinc)

    s = Symbol('s', zero=True)
    assert sinc(s) == S.One
    assert sinc(S.Infinity) == S.Zero
    assert sinc(-S.Infinity) == S.Zero
    assert sinc(S.NaN) == S.NaN
    assert sinc(S.ComplexInfinity) == S.NaN

    n = Symbol('n', integer=True, nonzero=True)
    assert sinc(n*pi) == S.Zero
    assert sinc(-n*pi) == S.Zero
    assert sinc(pi/2) == 2 / pi
    assert sinc(-pi/2) == 2 / pi
    assert sinc(5*pi/2) == 2 / (5*pi)
    assert sinc(7*pi/2) == -2 / (7*pi)

    assert sinc(-x) == sinc(x)

    assert sinc(x).diff() == (x*cos(x) - sin(x)) / x**2

    assert sinc(x).series() == 1 - x**2/6 + x**4/120 + O(x**6)

    assert sinc(x).rewrite(jn) == jn(0, x)
    assert sinc(x).rewrite(sin) == Piecewise((sin(x)/x, Ne(x, 0)), (1, True))


def test_asin():
    assert asin(nan) == nan

    assert asin.nargs == FiniteSet(1)
    assert asin(oo) == -I*oo
    assert asin(-oo) == I*oo
    assert asin(zoo) == zoo

    # Note: asin(-x) = - asin(x)
    assert asin(0) == 0
    assert asin(1) == pi/2
    assert asin(-1) == -pi/2
    assert asin(sqrt(3)/2) == pi/3
    assert asin(-sqrt(3)/2) == -pi/3
    assert asin(sqrt(2)/2) == pi/4
    assert asin(-sqrt(2)/2) == -pi/4
    assert asin(sqrt((5 - sqrt(5))/8)) == pi/5
    assert asin(-sqrt((5 - sqrt(5))/8)) == -pi/5
    assert asin(Rational(1, 2)) == pi/6
    assert asin(-Rational(1, 2)) == -pi/6
    assert asin((sqrt(2 - sqrt(2)))/2) == pi/8
    assert asin(-(sqrt(2 - sqrt(2)))/2) == -pi/8
    assert asin((sqrt(5) - 1)/4) == pi/10
    assert asin(-(sqrt(5) - 1)/4) == -pi/10
    assert asin((sqrt(3) - 1)/sqrt(2**3)) == pi/12
    assert asin(-(sqrt(3) - 1)/sqrt(2**3)) == -pi/12

    assert asin(x).diff(x) == 1/sqrt(1 - x**2)

    assert asin(0.2).is_real is True
    assert asin(-2).is_real is False
    assert asin(r).is_real is None

    assert asin(-2*I) == -I*asinh(2)

    assert asin(Rational(1, 7), evaluate=False).is_positive is True
    assert asin(Rational(-1, 7), evaluate=False).is_positive is False
    assert asin(p).is_positive is None


def test_asin_series():
    assert asin(x).series(x, 0, 9) == \
        x + x**3/6 + 3*x**5/40 + 5*x**7/112 + O(x**9)
    t5 = asin(x).taylor_term(5, x)
    assert t5 == 3*x**5/40
    assert asin(x).taylor_term(7, x, t5, 0) == 5*x**7/112


def test_asin_rewrite():
    assert asin(x).rewrite(log) == -I*log(I*x + sqrt(1 - x**2))
    assert asin(x).rewrite(atan) == 2*atan(x/(1 + sqrt(1 - x**2)))
    assert asin(x).rewrite(acos) == S.Pi/2 - acos(x)
    assert asin(x).rewrite(acot) == 2*acot((sqrt(-x**2 + 1) + 1)/x)
    assert asin(x).rewrite(asec) == -asec(1/x) + pi/2
    assert asin(x).rewrite(acsc) == acsc(1/x)


def test_acos():
    assert acos(nan) == nan
    assert acos(zoo) == zoo

    assert acos.nargs == FiniteSet(1)
    assert acos(oo) == I*oo
    assert acos(-oo) == -I*oo

    # Note: acos(-x) = pi - acos(x)
    assert acos(0) == pi/2
    assert acos(Rational(1, 2)) == pi/3
    assert acos(-Rational(1, 2)) == (2*pi)/3
    assert acos(1) == 0
    assert acos(-1) == pi
    assert acos(sqrt(2)/2) == pi/4
    assert acos(-sqrt(2)/2) == (3*pi)/4

    assert acos(x).diff(x) == -1/sqrt(1 - x**2)

    assert acos(0.2).is_real is True
    assert acos(-2).is_real is False
    assert acos(r).is_real is None

    assert acos(Rational(1, 7), evaluate=False).is_positive is True
    assert acos(Rational(-1, 7), evaluate=False).is_positive is True
    assert acos(Rational(3, 2), evaluate=False).is_positive is False
    assert acos(p).is_positive is None

    assert acos(2 + p).conjugate() != acos(10 + p)
    assert acos(-3 + n).conjugate() != acos(-3 + n)
    assert acos(S.One/3).conjugate() == acos(S.One/3)
    assert acos(-S.One/3).conjugate() == acos(-S.One/3)
    assert acos(p + n*I).conjugate() == acos(p - n*I)
    assert acos(z).conjugate() != acos(conjugate(z))


def test_acos_series():
    assert acos(x).series(x, 0, 8) == \
        pi/2 - x - x**3/6 - 3*x**5/40 - 5*x**7/112 + O(x**8)
    assert acos(x).series(x, 0, 8) == pi/2 - asin(x).series(x, 0, 8)
    t5 = acos(x).taylor_term(5, x)
    assert t5 == -3*x**5/40
    assert acos(x).taylor_term(7, x, t5, 0) == -5*x**7/112


def test_acos_rewrite():
    assert acos(x).rewrite(log) == pi/2 + I*log(I*x + sqrt(1 - x**2))
    assert acos(x).rewrite(atan) == \
           atan(sqrt(1 - x**2)/x) + (pi/2)*(1 - x*sqrt(1/x**2))
    assert acos(0).rewrite(atan) == S.Pi/2
    assert acos(0.5).rewrite(atan) == acos(0.5).rewrite(log)
    assert acos(x).rewrite(asin) == S.Pi/2 - asin(x)
    assert acos(x).rewrite(acot) == -2*acot((sqrt(-x**2 + 1) + 1)/x) + pi/2
    assert acos(x).rewrite(asec) == asec(1/x)
    assert acos(x).rewrite(acsc) == -acsc(1/x) + pi/2


def test_atan():
    assert atan(nan) == nan

    assert atan.nargs == FiniteSet(1)
    assert atan(oo) == pi/2
    assert atan(-oo) == -pi/2
    assert atan(zoo) == AccumBounds(-pi/2, pi/2)

    assert atan(0) == 0
    assert atan(1) == pi/4
    assert atan(sqrt(3)) == pi/3
    assert atan(oo) == pi/2
    assert atan(x).diff(x) == 1/(1 + x**2)

    assert atan(r).is_real is True

    assert atan(-2*I) == -I*atanh(2)
    assert atan(p).is_positive is True
    assert atan(n).is_positive is False
    assert atan(x).is_positive is None


def test_atan_rewrite():
    assert atan(x).rewrite(log) == I*(log(1 - I*x)-log(1 + I*x))/2
    assert atan(x).rewrite(asin) == (-asin(1/sqrt(x**2 + 1)) + pi/2)*sqrt(x**2)/x
    assert atan(x).rewrite(acos) == sqrt(x**2)*acos(1/sqrt(x**2 + 1))/x
    assert atan(x).rewrite(acot) == acot(1/x)
    assert atan(x).rewrite(asec) == sqrt(x**2)*asec(sqrt(x**2 + 1))/x
    assert atan(x).rewrite(acsc) == (-acsc(sqrt(x**2 + 1)) + pi/2)*sqrt(x**2)/x

    assert atan(-5*I).evalf() == atan(x).rewrite(log).evalf(subs={x:-5*I})
    assert atan(5*I).evalf() == atan(x).rewrite(log).evalf(subs={x:5*I})


def test_atan2():
    assert atan2.nargs == FiniteSet(2)
    assert atan2(0, 0) == S.NaN
    assert atan2(0, 1) == 0
    assert atan2(1, 1) == pi/4
    assert atan2(1, 0) == pi/2
    assert atan2(1, -1) == 3*pi/4
    assert atan2(0, -1) == pi
    assert atan2(-1, -1) == -3*pi/4
    assert atan2(-1, 0) == -pi/2
    assert atan2(-1, 1) == -pi/4
    i = symbols('i', imaginary=True)
    r = symbols('r', real=True)
    eq = atan2(r, i)
    ans = -I*log((i + I*r)/sqrt(i**2 + r**2))
    reps = ((r, 2), (i, I))
    assert eq.subs(reps) == ans.subs(reps)

    x = Symbol('x', negative=True)
    y = Symbol('y', negative=True)
    assert atan2(y, x) == atan(y/x) - pi
    y = Symbol('y', nonnegative=True)
    assert atan2(y, x) == atan(y/x) + pi
    y = Symbol('y')
    assert atan2(y, x) == atan2(y, x, evaluate=False)

    u = Symbol("u", positive=True)
    assert atan2(0, u) == 0
    u = Symbol("u", negative=True)
    assert atan2(0, u) == pi

    assert atan2(y, oo) ==  0
    assert atan2(y, -oo)==  2*pi*Heaviside(re(y)) - pi

    assert atan2(y, x).rewrite(log) == -I*log((x + I*y)/sqrt(x**2 + y**2))
    assert atan2(y, x).rewrite(atan) == 2*atan(y/(x + sqrt(x**2 + y**2)))

    ex = atan2(y, x) - arg(x + I*y)
    assert ex.subs({x:2, y:3}).rewrite(arg) == 0
    assert ex.subs({x:2, y:3*I}).rewrite(arg) == -pi - I*log(sqrt(5)*I/5)
    assert ex.subs({x:2*I, y:3}).rewrite(arg) == -pi/2 - I*log(sqrt(5)*I)
    assert ex.subs({x:2*I, y:3*I}).rewrite(arg) == -pi + atan(2/S(3)) + atan(3/S(2))
    i = symbols('i', imaginary=True)
    r = symbols('r', real=True)
    e = atan2(i, r)
    rewrite = e.rewrite(arg)
    reps = {i: I, r: -2}
    assert rewrite == -I*log(abs(I*i + r)/sqrt(abs(i**2 + r**2))) + arg((I*i + r)/sqrt(i**2 + r**2))
    assert (e - rewrite).subs(reps).equals(0)

    assert conjugate(atan2(x, y)) == atan2(conjugate(x), conjugate(y))

    assert diff(atan2(y, x), x) == -y/(x**2 + y**2)
    assert diff(atan2(y, x), y) == x/(x**2 + y**2)

    assert simplify(diff(atan2(y, x).rewrite(log), x)) == -y/(x**2 + y**2)
    assert simplify(diff(atan2(y, x).rewrite(log), y)) ==  x/(x**2 + y**2)


def test_acot():
    assert acot(nan) == nan

    assert acot.nargs == FiniteSet(1)
    assert acot(-oo) == 0
    assert acot(oo) == 0
    assert acot(zoo) == 0
    assert acot(1) == pi/4
    assert acot(0) == pi/2
    assert acot(sqrt(3)/3) == pi/3
    assert acot(1/sqrt(3)) == pi/3
    assert acot(-1/sqrt(3)) == -pi/3
    assert acot(x).diff(x) == -1/(1 + x**2)

    assert acot(r).is_real is True

    assert acot(I*pi) == -I*acoth(pi)
    assert acot(-2*I) == I*acoth(2)
    assert acot(x).is_positive is None
    assert acot(n).is_positive is False
    assert acot(p).is_positive is True
    assert acot(I).is_positive is False


def test_acot_rewrite():
    assert acot(x).rewrite(log) == I*(log(1 - I/x)-log(1 + I/x))/2
    assert acot(x).rewrite(asin) == x*(-asin(sqrt(-x**2)/sqrt(-x**2 - 1)) + pi/2)*sqrt(x**(-2))
    assert acot(x).rewrite(acos) == x*sqrt(x**(-2))*acos(sqrt(-x**2)/sqrt(-x**2 - 1))
    assert acot(x).rewrite(atan) == atan(1/x)
    assert acot(x).rewrite(asec) == x*sqrt(x**(-2))*asec(sqrt((x**2 + 1)/x**2))
    assert acot(x).rewrite(acsc) == x*(-acsc(sqrt((x**2 + 1)/x**2)) + pi/2)*sqrt(x**(-2))

    assert acot(-I/5).evalf() == acot(x).rewrite(log).evalf(subs={x:-I/5})
    assert acot(I/5).evalf() == acot(x).rewrite(log).evalf(subs={x:I/5})


def test_attributes():
    assert sin(x).args == (x,)


def test_sincos_rewrite():
    assert sin(pi/2 - x) == cos(x)
    assert sin(pi - x) == sin(x)
    assert cos(pi/2 - x) == sin(x)
    assert cos(pi - x) == -cos(x)


def _check_even_rewrite(func, arg):
    """Checks that the expr has been rewritten using f(-x) -> f(x)
    arg : -x
    """
    return func(arg).args[0] == -arg


def _check_odd_rewrite(func, arg):
    """Checks that the expr has been rewritten using f(-x) -> -f(x)
    arg : -x
    """
    return func(arg).func.is_Mul


def _check_no_rewrite(func, arg):
    """Checks that the expr is not rewritten"""
    return func(arg).args[0] == arg


def test_evenodd_rewrite():
    a = cos(2)  # negative
    b = sin(1)  # positive
    even = [cos]
    odd = [sin, tan, cot, asin, atan, acot]
    with_minus = [-1, -2**1024 * E, -pi/105, -x*y, -x - y]
    for func in even:
        for expr in with_minus:
            assert _check_even_rewrite(func, expr)
        assert _check_no_rewrite(func, a*b)
        assert func(
            x - y) == func(y - x)  # it doesn't matter which form is canonical
    for func in odd:
        for expr in with_minus:
            assert _check_odd_rewrite(func, expr)
        assert _check_no_rewrite(func, a*b)
        assert func(
            x - y) == -func(y - x)  # it doesn't matter which form is canonical


def test_issue_4547():
    assert sin(x).rewrite(cot) == 2*cot(x/2)/(1 + cot(x/2)**2)
    assert cos(x).rewrite(cot) == -(1 - cot(x/2)**2)/(1 + cot(x/2)**2)
    assert tan(x).rewrite(cot) == 1/cot(x)
    assert cot(x).fdiff() == -1 - cot(x)**2


def test_as_leading_term_issue_5272():
    assert sin(x).as_leading_term(x) == x
    assert cos(x).as_leading_term(x) == 1
    assert tan(x).as_leading_term(x) == x
    assert cot(x).as_leading_term(x) == 1/x
    assert asin(x).as_leading_term(x) == x
    assert acos(x).as_leading_term(x) == x
    assert atan(x).as_leading_term(x) == x
    assert acot(x).as_leading_term(x) == x


def test_leading_terms():
    for func in [sin, cos, tan, cot, asin, acos, atan, acot]:
        for arg in (1/x, S.Half):
            eq = func(arg)
            assert eq.as_leading_term(x) == eq


def test_atan2_expansion():
    assert cancel(atan2(x**2, x + 1).diff(x) - atan(x**2/(x + 1)).diff(x)) == 0
    assert cancel(atan(y/x).series(y, 0, 5) - atan2(y, x).series(y, 0, 5)
                  + atan2(0, x) - atan(0)) == O(y**5)
    assert cancel(atan(y/x).series(x, 1, 4) - atan2(y, x).series(x, 1, 4)
                  + atan2(y, 1) - atan(y)) == O((x - 1)**4, (x, 1))
    assert cancel(atan((y + x)/x).series(x, 1, 3) - atan2(y + x, x).series(x, 1, 3)
                  + atan2(1 + y, 1) - atan(1 + y)) == O((x - 1)**3, (x, 1))
    assert Matrix([atan2(y, x)]).jacobian([y, x]) == \
        Matrix([[x/(y**2 + x**2), -y/(y**2 + x**2)]])


def test_aseries():
    def t(n, v, d, e):
        assert abs(
            n(1/v).evalf() - n(1/x).series(x, dir=d).removeO().subs(x, v)) < e
    t(atan, 0.1, '+', 1e-5)
    t(atan, -0.1, '-', 1e-5)
    t(acot, 0.1, '+', 1e-5)
    t(acot, -0.1, '-', 1e-5)


def test_issue_4420():
    i = Symbol('i', integer=True)
    e = Symbol('e', even=True)
    o = Symbol('o', odd=True)

    # unknown parity for variable
    assert cos(4*i*pi) == 1
    assert sin(4*i*pi) == 0
    assert tan(4*i*pi) == 0
    assert cot(4*i*pi) == zoo

    assert cos(3*i*pi) == cos(pi*i)  # +/-1
    assert sin(3*i*pi) == 0
    assert tan(3*i*pi) == 0
    assert cot(3*i*pi) == zoo

    assert cos(4.0*i*pi) == 1
    assert sin(4.0*i*pi) == 0
    assert tan(4.0*i*pi) == 0
    assert cot(4.0*i*pi) == zoo

    assert cos(3.0*i*pi) == cos(pi*i)  # +/-1
    assert sin(3.0*i*pi) == 0
    assert tan(3.0*i*pi) == 0
    assert cot(3.0*i*pi) == zoo

    assert cos(4.5*i*pi) == cos(0.5*pi*i)
    assert sin(4.5*i*pi) == sin(0.5*pi*i)
    assert tan(4.5*i*pi) == tan(0.5*pi*i)
    assert cot(4.5*i*pi) == cot(0.5*pi*i)

    # parity of variable is known
    assert cos(4*e*pi) == 1
    assert sin(4*e*pi) == 0
    assert tan(4*e*pi) == 0
    assert cot(4*e*pi) == zoo

    assert cos(3*e*pi) == 1
    assert sin(3*e*pi) == 0
    assert tan(3*e*pi) == 0
    assert cot(3*e*pi) == zoo

    assert cos(4.0*e*pi) == 1
    assert sin(4.0*e*pi) == 0
    assert tan(4.0*e*pi) == 0
    assert cot(4.0*e*pi) == zoo

    assert cos(3.0*e*pi) == 1
    assert sin(3.0*e*pi) == 0
    assert tan(3.0*e*pi) == 0
    assert cot(3.0*e*pi) == zoo

    assert cos(4.5*e*pi) == cos(0.5*pi*e)
    assert sin(4.5*e*pi) == sin(0.5*pi*e)
    assert tan(4.5*e*pi) == tan(0.5*pi*e)
    assert cot(4.5*e*pi) == cot(0.5*pi*e)

    assert cos(4*o*pi) == 1
    assert sin(4*o*pi) == 0
    assert tan(4*o*pi) == 0
    assert cot(4*o*pi) == zoo

    assert cos(3*o*pi) == -1
    assert sin(3*o*pi) == 0
    assert tan(3*o*pi) == 0
    assert cot(3*o*pi) == zoo

    assert cos(4.0*o*pi) == 1
    assert sin(4.0*o*pi) == 0
    assert tan(4.0*o*pi) == 0
    assert cot(4.0*o*pi) == zoo

    assert cos(3.0*o*pi) == -1
    assert sin(3.0*o*pi) == 0
    assert tan(3.0*o*pi) == 0
    assert cot(3.0*o*pi) == zoo

    assert cos(4.5*o*pi) == cos(0.5*pi*o)
    assert sin(4.5*o*pi) == sin(0.5*pi*o)
    assert tan(4.5*o*pi) == tan(0.5*pi*o)
    assert cot(4.5*o*pi) == cot(0.5*pi*o)

    # x could be imaginary
    assert cos(4*x*pi) == cos(4*pi*x)
    assert sin(4*x*pi) == sin(4*pi*x)
    assert tan(4*x*pi) == tan(4*pi*x)
    assert cot(4*x*pi) == cot(4*pi*x)

    assert cos(3*x*pi) == cos(3*pi*x)
    assert sin(3*x*pi) == sin(3*pi*x)
    assert tan(3*x*pi) == tan(3*pi*x)
    assert cot(3*x*pi) == cot(3*pi*x)

    assert cos(4.0*x*pi) == cos(4.0*pi*x)
    assert sin(4.0*x*pi) == sin(4.0*pi*x)
    assert tan(4.0*x*pi) == tan(4.0*pi*x)
    assert cot(4.0*x*pi) == cot(4.0*pi*x)

    assert cos(3.0*x*pi) == cos(3.0*pi*x)
    assert sin(3.0*x*pi) == sin(3.0*pi*x)
    assert tan(3.0*x*pi) == tan(3.0*pi*x)
    assert cot(3.0*x*pi) == cot(3.0*pi*x)

    assert cos(4.5*x*pi) == cos(4.5*pi*x)
    assert sin(4.5*x*pi) == sin(4.5*pi*x)
    assert tan(4.5*x*pi) == tan(4.5*pi*x)
    assert cot(4.5*x*pi) == cot(4.5*pi*x)


def test_inverses():
    raises(AttributeError, lambda: sin(x).inverse())
    raises(AttributeError, lambda: cos(x).inverse())
    assert tan(x).inverse() == atan
    assert cot(x).inverse() == acot
    raises(AttributeError, lambda: csc(x).inverse())
    raises(AttributeError, lambda: sec(x).inverse())
    assert asin(x).inverse() == sin
    assert acos(x).inverse() == cos
    assert atan(x).inverse() == tan
    assert acot(x).inverse() == cot



def test_real_imag():
    a, b = symbols('a b', real=True)
    z = a + b*I
    for deep in [True, False]:
        assert sin(
            z).as_real_imag(deep=deep) == (sin(a)*cosh(b), cos(a)*sinh(b))
        assert cos(
            z).as_real_imag(deep=deep) == (cos(a)*cosh(b), -sin(a)*sinh(b))
        assert tan(z).as_real_imag(deep=deep) == (sin(2*a)/(cos(2*a) +
            cosh(2*b)), sinh(2*b)/(cos(2*a) + cosh(2*b)))
        assert cot(z).as_real_imag(deep=deep) == (-sin(2*a)/(cos(2*a) -
            cosh(2*b)), -sinh(2*b)/(cos(2*a) - cosh(2*b)))
        assert sin(a).as_real_imag(deep=deep) == (sin(a), 0)
        assert cos(a).as_real_imag(deep=deep) == (cos(a), 0)
        assert tan(a).as_real_imag(deep=deep) == (tan(a), 0)
        assert cot(a).as_real_imag(deep=deep) == (cot(a), 0)


@XFAIL
def test_sin_cos_with_infinity():
    # Test for issue 5196
    # https://github.com/sympy/sympy/issues/5196
    assert sin(oo) == S.NaN
    assert cos(oo) == S.NaN


@slow
def test_sincos_rewrite_sqrt():
    # equivalent to testing rewrite(pow)
    for p in [1, 3, 5, 17]:
        for t in [1, 8]:
            n = t*p
            # The vertices `exp(i*pi/n)` of a regular `n`-gon can
            # be expressed by means of nested square roots if and
            # only if `n` is a product of Fermat primes, `p`, and
            # powers of 2, `t'. The code aims to check all vertices
            # not belonging to an `m`-gon for `m < n`(`gcd(i, n) == 1`).
            # For large `n` this makes the test too slow, therefore
            # the vertices are limited to those of index `i < 10`.
            for i in range(1, min((n + 1)//2 + 1, 10)):
                if 1 == gcd(i, n):
                    x = i*pi/n
                    s1 = sin(x).rewrite(sqrt)
                    c1 = cos(x).rewrite(sqrt)
                    assert not s1.has(cos, sin), "fails for %d*pi/%d" % (i, n)
                    assert not c1.has(cos, sin), "fails for %d*pi/%d" % (i, n)
                    assert 1e-3 > abs(sin(x.evalf(5)) - s1.evalf(2)), "fails for %d*pi/%d" % (i, n)
                    assert 1e-3 > abs(cos(x.evalf(5)) - c1.evalf(2)), "fails for %d*pi/%d" % (i, n)
    assert cos(pi/14).rewrite(sqrt) == sqrt(cos(pi/7)/2 + S.Half)
    assert cos(pi/257).rewrite(sqrt).evalf(64) == cos(pi/257).evalf(64)
    assert cos(-15*pi/2/11, evaluate=False).rewrite(
        sqrt) == -sqrt(-cos(4*pi/11)/2 + S.Half)
    assert cos(Mul(2, pi, S.Half, evaluate=False), evaluate=False).rewrite(
        sqrt) == -1
    e = cos(pi/3/17)  # don't use pi/15 since that is caught at instantiation
    a = (
        -3*sqrt(-sqrt(17) + 17)*sqrt(sqrt(17) + 17)/64 -
        3*sqrt(34)*sqrt(sqrt(17) + 17)/128 - sqrt(sqrt(17) +
        17)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) + 17)
        + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/64 - sqrt(-sqrt(17)
        + 17)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/128 - S(1)/32 +
        sqrt(2)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/64 +
        3*sqrt(2)*sqrt(sqrt(17) + 17)/128 + sqrt(34)*sqrt(-sqrt(17) + 17)/128
        + 13*sqrt(2)*sqrt(-sqrt(17) + 17)/128 + sqrt(17)*sqrt(-sqrt(17) +
        17)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) + 17)
        + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/128 + 5*sqrt(17)/32
        + sqrt(3)*sqrt(-sqrt(2)*sqrt(sqrt(17) + 17)*sqrt(sqrt(17)/32 +
        sqrt(2)*sqrt(-sqrt(17) + 17)/32 +
        sqrt(2)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/32 + S(15)/32)/8 -
        5*sqrt(2)*sqrt(sqrt(17)/32 + sqrt(2)*sqrt(-sqrt(17) + 17)/32 +
        sqrt(2)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/32 +
        S(15)/32)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/64 -
        3*sqrt(2)*sqrt(-sqrt(17) + 17)*sqrt(sqrt(17)/32 +
        sqrt(2)*sqrt(-sqrt(17) + 17)/32 +
        sqrt(2)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/32 + S(15)/32)/32
        + sqrt(34)*sqrt(sqrt(17)/32 + sqrt(2)*sqrt(-sqrt(17) + 17)/32 +
        sqrt(2)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/32 +
        S(15)/32)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/64 +
        sqrt(sqrt(17)/32 + sqrt(2)*sqrt(-sqrt(17) + 17)/32 +
        sqrt(2)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/32 + S(15)/32)/2 +
        S.Half + sqrt(-sqrt(17) + 17)*sqrt(sqrt(17)/32 + sqrt(2)*sqrt(-sqrt(17) +
        17)/32 + sqrt(2)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) -
        sqrt(2)*sqrt(-sqrt(17) + 17) + sqrt(34)*sqrt(-sqrt(17) + 17) +
        6*sqrt(17) + 34)/32 + S(15)/32)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) -
        sqrt(2)*sqrt(-sqrt(17) + 17) + sqrt(34)*sqrt(-sqrt(17) + 17) +
        6*sqrt(17) + 34)/32 + sqrt(34)*sqrt(-sqrt(17) + 17)*sqrt(sqrt(17)/32 +
        sqrt(2)*sqrt(-sqrt(17) + 17)/32 +
        sqrt(2)*sqrt(-8*sqrt(2)*sqrt(sqrt(17) + 17) - sqrt(2)*sqrt(-sqrt(17) +
        17) + sqrt(34)*sqrt(-sqrt(17) + 17) + 6*sqrt(17) + 34)/32 +
        S(15)/32)/32)/2)
    assert e.rewrite(sqrt) == a
    assert e.n() == a.n()
    # coverage of fermatCoords: multiplicity > 1; the following could be
    # different but that portion of the code should be tested in some way
    assert cos(pi/9/17).rewrite(sqrt) == \
        sin(pi/9)*sin(2*pi/17) + cos(pi/9)*cos(2*pi/17)


@slow
def test_tancot_rewrite_sqrt():
    # equivalent to testing rewrite(pow)
    for p in [1, 3, 5, 17]:
        for t in [1, 8]:
            n = t*p
            for i in range(1, min((n + 1)//2 + 1, 10)):
                if 1 == gcd(i, n):
                    x = i*pi/n
                    if  2*i != n and 3*i != 2*n:
                        t1 = tan(x).rewrite(sqrt)
                        assert not t1.has(cot, tan), "fails for %d*pi/%d" % (i, n)
                        assert 1e-3 > abs( tan(x.evalf(7)) - t1.evalf(4) ), "fails for %d*pi/%d" % (i, n)
                    if  i != 0 and i != n:
                        c1 = cot(x).rewrite(sqrt)
                        assert not c1.has(cot, tan), "fails for %d*pi/%d" % (i, n)
                        assert 1e-3 > abs( cot(x.evalf(7)) - c1.evalf(4) ), "fails for %d*pi/%d" % (i, n)

def test_sec():
    x = symbols('x', real=True)
    z = symbols('z')

    assert sec.nargs == FiniteSet(1)

    assert sec(zoo) == nan
    assert sec(0) == 1
    assert sec(pi) == -1
    assert sec(pi/2) == zoo
    assert sec(-pi/2) == zoo
    assert sec(pi/6) == 2*sqrt(3)/3
    assert sec(pi/3) == 2
    assert sec(5*pi/2) == zoo
    assert sec(9*pi/7) == -sec(2*pi/7)
    assert sec(3*pi/4) == -sqrt(2)  # issue 8421
    assert sec(I) == 1/cosh(1)
    assert sec(x*I) == 1/cosh(x)
    assert sec(-x) == sec(x)

    assert sec(asec(x)) == x

    assert sec(z).conjugate() == sec(conjugate(z))

    assert (sec(z).as_real_imag() ==
    (cos(re(z))*cosh(im(z))/(sin(re(z))**2*sinh(im(z))**2 +
                             cos(re(z))**2*cosh(im(z))**2),
     sin(re(z))*sinh(im(z))/(sin(re(z))**2*sinh(im(z))**2 +
                             cos(re(z))**2*cosh(im(z))**2)))

    assert sec(x).expand(trig=True) == 1/cos(x)
    assert sec(2*x).expand(trig=True) == 1/(2*cos(x)**2 - 1)

    assert sec(x).is_real == True
    assert sec(z).is_real == None

    assert sec(a).is_algebraic is None
    assert sec(na).is_algebraic is False

    assert sec(x).as_leading_term() == sec(x)

    assert sec(0).is_finite == True
    assert sec(x).is_finite == None
    assert sec(pi/2).is_finite == False

    assert series(sec(x), x, x0=0, n=6) == 1 + x**2/2 + 5*x**4/24 + O(x**6)

    # https://github.com/sympy/sympy/issues/7166
    assert series(sqrt(sec(x))) == 1 + x**2/4 + 7*x**4/96 + O(x**6)

    # https://github.com/sympy/sympy/issues/7167
    assert (series(sqrt(sec(x)), x, x0=pi*3/2, n=4) ==
            1/sqrt(x - 3*pi/2) + (x - 3*pi/2)**(S(3)/2)/12 +
            (x - 3*pi/2)**(S(7)/2)/160 + O((x - 3*pi/2)**4, (x, 3*pi/2)))

    assert sec(x).diff(x) == tan(x)*sec(x)

    # Taylor Term checks
    assert sec(z).taylor_term(4, z) == 5*z**4/24
    assert sec(z).taylor_term(6, z) == 61*z**6/720
    assert sec(z).taylor_term(5, z) == 0


def test_sec_rewrite():
    assert sec(x).rewrite(exp) == 1/(exp(I*x)/2 + exp(-I*x)/2)
    assert sec(x).rewrite(cos) == 1/cos(x)
    assert sec(x).rewrite(tan) == (tan(x/2)**2 + 1)/(-tan(x/2)**2 + 1)
    assert sec(x).rewrite(pow) == sec(x)
    assert sec(x).rewrite(sqrt) == sec(x)
    assert sec(z).rewrite(cot) == (cot(z/2)**2 + 1)/(cot(z/2)**2 - 1)
    assert sec(x).rewrite(sin) == 1 / sin(x + pi / 2, evaluate=False)
    assert sec(x).rewrite(tan) == (tan(x / 2)**2 + 1) / (-tan(x / 2)**2 + 1)
    assert sec(x).rewrite(csc) == csc(-x + pi/2, evaluate=False)


def test_csc():
    x = symbols('x', real=True)
    z = symbols('z')

    # https://github.com/sympy/sympy/issues/6707
    cosecant = csc('x')
    alternate = 1/sin('x')
    assert cosecant.equals(alternate) == True
    assert alternate.equals(cosecant) == True

    assert csc.nargs == FiniteSet(1)

    assert csc(0) == zoo
    assert csc(pi) == zoo
    assert csc(zoo) == nan

    assert csc(pi/2) == 1
    assert csc(-pi/2) == -1
    assert csc(pi/6) == 2
    assert csc(pi/3) == 2*sqrt(3)/3
    assert csc(5*pi/2) == 1
    assert csc(9*pi/7) == -csc(2*pi/7)
    assert csc(3*pi/4) == sqrt(2)  # issue 8421
    assert csc(I) == -I/sinh(1)
    assert csc(x*I) == -I/sinh(x)
    assert csc(-x) == -csc(x)

    assert csc(acsc(x)) == x

    assert csc(z).conjugate() == csc(conjugate(z))

    assert (csc(z).as_real_imag() ==
            (sin(re(z))*cosh(im(z))/(sin(re(z))**2*cosh(im(z))**2 +
                                     cos(re(z))**2*sinh(im(z))**2),
             -cos(re(z))*sinh(im(z))/(sin(re(z))**2*cosh(im(z))**2 +
                          cos(re(z))**2*sinh(im(z))**2)))

    assert csc(x).expand(trig=True) == 1/sin(x)
    assert csc(2*x).expand(trig=True) == 1/(2*sin(x)*cos(x))

    assert csc(x).is_real == True
    assert csc(z).is_real == None

    assert csc(a).is_algebraic is None
    assert csc(na).is_algebraic is False

    assert csc(x).as_leading_term() == csc(x)

    assert csc(0).is_finite == False
    assert csc(x).is_finite == None
    assert csc(pi/2).is_finite == True

    assert series(csc(x), x, x0=pi/2, n=6) == \
        1 + (x - pi/2)**2/2 + 5*(x - pi/2)**4/24 + O((x - pi/2)**6, (x, pi/2))
    assert series(csc(x), x, x0=0, n=6) == \
            1/x + x/6 + 7*x**3/360 + 31*x**5/15120 + O(x**6)

    assert csc(x).diff(x) == -cot(x)*csc(x)

    assert csc(x).taylor_term(2, x) == 0
    assert csc(x).taylor_term(3, x) == 7*x**3/360
    assert csc(x).taylor_term(5, x) == 31*x**5/15120


def test_asec():
    z = Symbol('z', zero=True)
    assert asec(z) == zoo
    assert asec(nan) == nan
    assert asec(1) == 0
    assert asec(-1) == pi
    assert asec(oo) == pi/2
    assert asec(-oo) == pi/2
    assert asec(zoo) == pi/2

    assert asec(x).diff(x) == 1/(x**2*sqrt(1 - 1/x**2))
    assert asec(x).as_leading_term(x) == log(x)

    assert asec(x).rewrite(log) == I*log(sqrt(1 - 1/x**2) + I/x) + pi/2
    assert asec(x).rewrite(asin) == -asin(1/x) + pi/2
    assert asec(x).rewrite(acos) == acos(1/x)
    assert asec(x).rewrite(atan) == (2*atan(x + sqrt(x**2 - 1)) - pi/2)*sqrt(x**2)/x
    assert asec(x).rewrite(acot) == (2*acot(x - sqrt(x**2 - 1)) - pi/2)*sqrt(x**2)/x
    assert asec(x).rewrite(acsc) == -acsc(x) + pi/2


def test_asec_is_real():
    assert asec(S(1)/2).is_real is False
    n = Symbol('n', positive=True, integer=True)
    assert asec(n).is_real is True
    assert asec(x).is_real is None
    assert asec(r).is_real is None
    t = Symbol('t', real=False)
    assert asec(t).is_real is False


def test_acsc():
    assert acsc(nan) == nan
    assert acsc(1) == pi/2
    assert acsc(-1) == -pi/2
    assert acsc(oo) == 0
    assert acsc(-oo) == 0
    assert acsc(zoo) == 0

    assert acsc(x).diff(x) == -1/(x**2*sqrt(1 - 1/x**2))
    assert acsc(x).as_leading_term(x) == log(x)

    assert acsc(x).rewrite(log) == -I*log(sqrt(1 - 1/x**2) + I/x)
    assert acsc(x).rewrite(asin) == asin(1/x)
    assert acsc(x).rewrite(acos) == -acos(1/x) + pi/2
    assert acsc(x).rewrite(atan) == (-atan(sqrt(x**2 - 1)) + pi/2)*sqrt(x**2)/x
    assert acsc(x).rewrite(acot) == (-acot(1/sqrt(x**2 - 1)) + pi/2)*sqrt(x**2)/x
    assert acsc(x).rewrite(asec) == -asec(x) + pi/2


def test_csc_rewrite():
    assert csc(x).rewrite(pow) == csc(x)
    assert csc(x).rewrite(sqrt) == csc(x)

    assert csc(x).rewrite(exp) == 2*I/(exp(I*x) - exp(-I*x))
    assert csc(x).rewrite(sin) == 1/sin(x)
    assert csc(x).rewrite(tan) == (tan(x/2)**2 + 1)/(2*tan(x/2))
    assert csc(x).rewrite(cot) == (cot(x/2)**2 + 1)/(2*cot(x/2))
    assert csc(x).rewrite(cos) == 1/cos(x - pi/2, evaluate=False)
    assert csc(x).rewrite(sec) == sec(-x + pi/2, evaluate=False)


def test_issue_8653():
    n = Symbol('n', integer=True)
    assert sin(n).is_irrational is None
    assert cos(n).is_irrational is None
    assert tan(n).is_irrational is None


def test_issue_9157():
    n = Symbol('n', integer=True, positive=True)
    atan(n - 1).is_nonnegative is True


def test_trig_period():
    x, y = symbols('x, y')

    assert sin(x).period() == 2*pi
    assert cos(x).period() == 2*pi
    assert tan(x).period() == pi
    assert cot(x).period() == pi
    assert sec(x).period() == 2*pi
    assert csc(x).period() == 2*pi
    assert sin(2*x).period() == pi
    assert cot(4*x - 6).period() == pi/4
    assert cos((-3)*x).period() == 2*pi/3
    assert cos(x*y).period(x) == 2*pi/abs(y)
    assert sin(3*x*y + 2*pi).period(y) == 2*pi/abs(3*x)
    assert tan(3*x).period(y) == S.Zero
    raises(NotImplementedError, lambda: sin(x**2).period(x))


def test_issue_7171():
    assert sin(x).rewrite(sqrt) == sin(x)
    assert sin(x).rewrite(pow) == sin(x)


def test_issue_11864():
    w, k = symbols('w, k', real=True)
    F = Piecewise((1, Eq(2*pi*k, 0)), (sin(pi*k)/(pi*k), True))
    soln = Piecewise((1, Eq(2*pi*k, 0)), (sinc(pi*k), True))
    assert F.rewrite(sinc) == soln

def test_real_assumptions():
    z = Symbol('z', real=False)
    assert sin(z).is_real is None
    assert cos(z).is_real is None
    assert tan(z).is_real is False
    assert sec(z).is_real is None
    assert csc(z).is_real is None
    assert cot(z).is_real is False
    assert asin(p).is_real is None
    assert asin(n).is_real is None
    assert asec(p).is_real is None
    assert asec(n).is_real is None
    assert acos(p).is_real is None
    assert acos(n).is_real is None
    assert acsc(p).is_real is None
    assert acsc(n).is_real is None
    assert atan(p).is_positive is True
    assert atan(n).is_negative is True
    assert acot(p).is_positive is True
    assert acot(n).is_negative is True

def test_issue_14320():
    assert asin(sin(2)) == -2 + pi and (-pi/2 <= -2 + pi <= pi/2) and sin(2) == sin(-2 + pi)
    assert asin(cos(2)) == -2 + pi/2 and (-pi/2 <= -2 + pi/2 <= pi/2) and cos(2) == sin(-2 + pi/2)
    assert acos(sin(2)) == -pi/2 + 2 and (0 <= -pi/2 + 2 <= pi) and sin(2) == cos(-pi/2 + 2)
    assert acos(cos(20)) == -6*pi + 20 and (0 <= -6*pi + 20 <= pi) and cos(20) == cos(-6*pi + 20)
    assert acos(cos(30)) == -30 + 10*pi and (0 <= -30 + 10*pi <= pi) and cos(30) == cos(-30 + 10*pi)

    assert atan(tan(17)) == -5*pi + 17 and (-pi/2 < -5*pi + 17 < pi/2) and tan(17) == tan(-5*pi + 17)
    assert atan(tan(15)) == -5*pi + 15 and (-pi/2 < -5*pi + 15 < pi/2) and tan(15) == tan(-5*pi + 15)
    assert atan(cot(12)) == -12 + 7*pi/2 and (-pi/2 < -12 + 7*pi/2 < pi/2) and cot(12) == tan(-12 + 7*pi/2)
    assert acot(cot(15)) == -5*pi + 15 and (-pi/2 < -5*pi + 15 <= pi/2) and cot(15) == cot(-5*pi + 15)
    assert acot(tan(19)) == -19 + 13*pi/2 and (-pi/2 < -19 + 13*pi/2 <= pi/2) and tan(19) == cot(-19 + 13*pi/2)

    assert asec(sec(11)) == -11 + 4*pi and (0 <= -11 + 4*pi <= pi) and cos(11) == cos(-11 + 4*pi)
    assert asec(csc(13)) == -13 + 9*pi/2 and (0 <= -13 + 9*pi/2 <= pi) and sin(13) == cos(-13 + 9*pi/2)
    assert acsc(csc(14)) == -4*pi + 14 and (-pi/2 <= -4*pi + 14 <= pi/2) and sin(14) == sin(-4*pi + 14)
    assert acsc(sec(10)) == -7*pi/2 + 10 and (-pi/2 <= -7*pi/2 + 10 <= pi/2) and cos(10) == sin(-7*pi/2 + 10)

def test_issue_14543():
    assert sec(2*pi + 11) == sec(11)
    assert sec(2*pi - 11) == sec(11)
    assert sec(pi + 11) == -sec(11)
    assert sec(pi - 11) == -sec(11)

    assert csc(2*pi + 17) == csc(17)
    assert csc(2*pi - 17) == -csc(17)
    assert csc(pi + 17) == -csc(17)
    assert csc(pi - 17) == csc(17)

    x = Symbol('x')
    assert csc(pi/2 + x) == sec(x)
    assert csc(pi/2 - x) == sec(x)
    assert csc(3*pi/2 + x) == -sec(x)
    assert csc(3*pi/2 - x) == -sec(x)

    assert sec(pi/2 - x) == csc(x)
    assert sec(pi/2 + x) == -csc(x)
    assert sec(3*pi/2 + x) == csc(x)
    assert sec(3*pi/2 - x) == -csc(x)

def test_issue_15959():
    assert tan(3*pi/8) == 1 + sqrt(2)
