from itertools import product as cartes

from sympy import (
    limit, exp, oo, log, sqrt, Limit, sin, floor, cos, ceiling,
    atan, gamma, Symbol, S, pi, Integral, Rational, I, EulerGamma,
    tan, cot, integrate, Sum, sign, Function, subfactorial, symbols,
    binomial, simplify, frac, Float, sec, zoo, fresnelc, fresnels)

from sympy.calculus.util import AccumBounds
from sympy.core.add import Add
from sympy.core.mul import Mul
from sympy.series.limits import heuristics
from sympy.series.order import Order
from sympy.utilities.pytest import XFAIL, raises
from sympy.core.numbers import GoldenRatio
from sympy.functions.combinatorial.numbers import fibonacci

from sympy.abc import x, y, z, k
n = Symbol('n', integer=True, positive=True)


def test_basic1():
    assert limit(x, x, oo) == oo
    assert limit(x, x, -oo) == -oo
    assert limit(-x, x, oo) == -oo
    assert limit(x**2, x, -oo) == oo
    assert limit(-x**2, x, oo) == -oo
    assert limit(x*log(x), x, 0, dir="+") == 0
    assert limit(1/x, x, oo) == 0
    assert limit(exp(x), x, oo) == oo
    assert limit(-exp(x), x, oo) == -oo
    assert limit(exp(x)/x, x, oo) == oo
    assert limit(1/x - exp(-x), x, oo) == 0
    assert limit(x + 1/x, x, oo) == oo
    assert limit(x - x**2, x, oo) == -oo
    assert limit((1 + x)**(1 + sqrt(2)), x, 0) == 1
    assert limit((1 + x)**oo, x, 0) == oo
    assert limit((1 + x)**oo, x, 0, dir='-') == 0
    assert limit((1 + x + y)**oo, x, 0, dir='-') == (1 + y)**(oo)
    assert limit(y/x/log(x), x, 0) == -oo*sign(y)
    assert limit(cos(x + y)/x, x, 0) == sign(cos(y))*oo
    assert limit(gamma(1/x + 3), x, oo) == 2
    assert limit(S.NaN, x, -oo) == S.NaN
    assert limit(Order(2)*x, x, S.NaN) == S.NaN
    assert limit(1/(x - 1), x, 1, dir="+") == oo
    assert limit(1/(x - 1), x, 1, dir="-") == -oo
    assert limit(1/(5 - x)**3, x, 5, dir="+") == -oo
    assert limit(1/(5 - x)**3, x, 5, dir="-") == oo
    assert limit(1/sin(x), x, pi, dir="+") == -oo
    assert limit(1/sin(x), x, pi, dir="-") == oo
    assert limit(1/cos(x), x, pi/2, dir="+") == -oo
    assert limit(1/cos(x), x, pi/2, dir="-") == oo
    assert limit(1/tan(x**3), x, (2*pi)**(S(1)/3), dir="+") == oo
    assert limit(1/tan(x**3), x, (2*pi)**(S(1)/3), dir="-") == -oo
    assert limit(1/cot(x)**3, x, (3*pi/2), dir="+") == -oo
    assert limit(1/cot(x)**3, x, (3*pi/2), dir="-") == oo

    # test bi-directional limits
    assert limit(sin(x)/x, x, 0, dir="+-") == 1
    assert limit(x**2, x, 0, dir="+-") == 0
    assert limit(1/x**2, x, 0, dir="+-") == oo

    # test failing bi-directional limits
    raises(ValueError, lambda: limit(1/x, x, 0, dir="+-"))
    # approaching 0
    # from dir="+"
    assert limit(1 + 1/x, x, 0) == oo
    # from dir='-'
    # Add
    assert limit(1 + 1/x, x, 0, dir='-') == -oo
    # Pow
    assert limit(x**(-2), x, 0, dir='-') == oo
    assert limit(x**(-3), x, 0, dir='-') == -oo
    assert limit(1/sqrt(x), x, 0, dir='-') == (-oo)*I
    assert limit(x**2, x, 0, dir='-') == 0
    assert limit(sqrt(x), x, 0, dir='-') == 0
    assert limit(x**-pi, x, 0, dir='-') == oo*sign((-1)**(-pi))
    assert limit((1 + cos(x))**oo, x, 0) == oo


def test_basic2():
    assert limit(x**x, x, 0, dir="+") == 1
    assert limit((exp(x) - 1)/x, x, 0) == 1
    assert limit(1 + 1/x, x, oo) == 1
    assert limit(-exp(1/x), x, oo) == -1
    assert limit(x + exp(-x), x, oo) == oo
    assert limit(x + exp(-x**2), x, oo) == oo
    assert limit(x + exp(-exp(x)), x, oo) == oo
    assert limit(13 + 1/x - exp(-x), x, oo) == 13


def test_basic3():
    assert limit(1/x, x, 0, dir="+") == oo
    assert limit(1/x, x, 0, dir="-") == -oo


def test_basic4():
    assert limit(2*x + y*x, x, 0) == 0
    assert limit(2*x + y*x, x, 1) == 2 + y
    assert limit(2*x**8 + y*x**(-3), x, -2) == 512 - y/8
    assert limit(sqrt(x + 1) - sqrt(x), x, oo) == 0
    assert integrate(1/(x**3 + 1), (x, 0, oo)) == 2*pi*sqrt(3)/9


def test_basic5():
    class my(Function):
        @classmethod
        def eval(cls, arg):
            if arg is S.Infinity:
                return S.NaN
    assert limit(my(x), x, oo) == Limit(my(x), x, oo)


def test_issue_3885():
    assert limit(x*y + x*z, z, 2) == x*y + 2*x


def test_Limit():
    assert Limit(sin(x)/x, x, 0) != 1
    assert Limit(sin(x)/x, x, 0).doit() == 1
    assert Limit(x, x, 0, dir='+-').args == (x, x, 0, Symbol('+-'))


def test_floor():
    assert limit(floor(x), x, -2, "+") == -2
    assert limit(floor(x), x, -2, "-") == -3
    assert limit(floor(x), x, -1, "+") == -1
    assert limit(floor(x), x, -1, "-") == -2
    assert limit(floor(x), x, 0, "+") == 0
    assert limit(floor(x), x, 0, "-") == -1
    assert limit(floor(x), x, 1, "+") == 1
    assert limit(floor(x), x, 1, "-") == 0
    assert limit(floor(x), x, 2, "+") == 2
    assert limit(floor(x), x, 2, "-") == 1
    assert limit(floor(x), x, 248, "+") == 248
    assert limit(floor(x), x, 248, "-") == 247


def test_floor_requires_robust_assumptions():
    assert limit(floor(sin(x)), x, 0, "+") == 0
    assert limit(floor(sin(x)), x, 0, "-") == -1
    assert limit(floor(cos(x)), x, 0, "+") == 0
    assert limit(floor(cos(x)), x, 0, "-") == 0
    assert limit(floor(5 + sin(x)), x, 0, "+") == 5
    assert limit(floor(5 + sin(x)), x, 0, "-") == 4
    assert limit(floor(5 + cos(x)), x, 0, "+") == 5
    assert limit(floor(5 + cos(x)), x, 0, "-") == 5


def test_ceiling():
    assert limit(ceiling(x), x, -2, "+") == -1
    assert limit(ceiling(x), x, -2, "-") == -2
    assert limit(ceiling(x), x, -1, "+") == 0
    assert limit(ceiling(x), x, -1, "-") == -1
    assert limit(ceiling(x), x, 0, "+") == 1
    assert limit(ceiling(x), x, 0, "-") == 0
    assert limit(ceiling(x), x, 1, "+") == 2
    assert limit(ceiling(x), x, 1, "-") == 1
    assert limit(ceiling(x), x, 2, "+") == 3
    assert limit(ceiling(x), x, 2, "-") == 2
    assert limit(ceiling(x), x, 248, "+") == 249
    assert limit(ceiling(x), x, 248, "-") == 248


def test_ceiling_requires_robust_assumptions():
    assert limit(ceiling(sin(x)), x, 0, "+") == 1
    assert limit(ceiling(sin(x)), x, 0, "-") == 0
    assert limit(ceiling(cos(x)), x, 0, "+") == 1
    assert limit(ceiling(cos(x)), x, 0, "-") == 1
    assert limit(ceiling(5 + sin(x)), x, 0, "+") == 6
    assert limit(ceiling(5 + sin(x)), x, 0, "-") == 5
    assert limit(ceiling(5 + cos(x)), x, 0, "+") == 6
    assert limit(ceiling(5 + cos(x)), x, 0, "-") == 6


def test_atan():
    x = Symbol("x", real=True)
    assert limit(atan(x)*sin(1/x), x, 0) == 0
    assert limit(atan(x) + sqrt(x + 1) - sqrt(x), x, oo) == pi/2


def test_abs():
    assert limit(abs(x), x, 0) == 0
    assert limit(abs(sin(x)), x, 0) == 0
    assert limit(abs(cos(x)), x, 0) == 1
    assert limit(abs(sin(x + 1)), x, 0) == sin(1)


def test_heuristic():
    x = Symbol("x", real=True)
    assert heuristics(sin(1/x) + atan(x), x, 0, '+') == AccumBounds(-1, 1)
    assert limit(log(2 + sqrt(atan(x))*sqrt(sin(1/x))), x, 0) == log(2)


def test_issue_3871():
    z = Symbol("z", positive=True)
    f = -1/z*exp(-z*x)
    assert limit(f, x, oo) == 0
    assert f.limit(x, oo) == 0


def test_exponential():
    n = Symbol('n')
    x = Symbol('x', real=True)
    assert limit((1 + x/n)**n, n, oo) == exp(x)
    assert limit((1 + x/(2*n))**n, n, oo) == exp(x/2)
    assert limit((1 + x/(2*n + 1))**n, n, oo) == exp(x/2)
    assert limit(((x - 1)/(x + 1))**x, x, oo) == exp(-2)
    assert limit(1 + (1 + 1/x)**x, x, oo) == 1 + S.Exp1


@XFAIL
def test_exponential2():
    n = Symbol('n')
    assert limit((1 + x/(n + sin(n)))**n, n, oo) == exp(x)


def test_doit():
    f = Integral(2 * x, x)
    l = Limit(f, x, oo)
    assert l.doit() == oo


def test_AccumBounds():
    assert limit(sin(k) - sin(k + 1), k, oo) == AccumBounds(-2, 2)
    assert limit(cos(k) - cos(k + 1) + 1, k, oo) == AccumBounds(-1, 3)

    # not the exact bound
    assert limit(sin(k) - sin(k)*cos(k), k, oo) == AccumBounds(-2, 2)

    # test for issue #9934
    t1 = Mul(S(1)/2, 1/(-1 + cos(1)), Add(AccumBounds(-3, 1), cos(1)))
    assert limit(simplify(Sum(cos(n).rewrite(exp), (n, 0, k)).doit().rewrite(sin)), k, oo) == t1

    t2 = Mul(S(1)/2, Add(AccumBounds(-2, 2), sin(1)), 1/(-cos(1) + 1))
    assert limit(simplify(Sum(sin(n).rewrite(exp), (n, 0, k)).doit().rewrite(sin)), k, oo) == t2

    assert limit(frac(x)**x, x, oo) == AccumBounds(0, oo)
    assert limit(((sin(x) + 1)/2)**x, x, oo) == AccumBounds(0, oo)
    # Possible improvement: AccumBounds(0, 1)


@XFAIL
def test_doit2():
    f = Integral(2 * x, x)
    l = Limit(f, x, oo)
    # limit() breaks on the contained Integral.
    assert l.doit(deep=False) == l


def test_issue_3792():
    assert limit((1 - cos(x))/x**2, x, S(1)/2) == 4 - 4*cos(S(1)/2)
    assert limit(sin(sin(x + 1) + 1), x, 0) == sin(1 + sin(1))
    assert limit(abs(sin(x + 1) + 1), x, 0) == 1 + sin(1)


def test_issue_4090():
    assert limit(1/(x + 3), x, 2) == S(1)/5
    assert limit(1/(x + pi), x, 2) == S(1)/(2 + pi)
    assert limit(log(x)/(x**2 + 3), x, 2) == log(2)/7
    assert limit(log(x)/(x**2 + pi), x, 2) == log(2)/(4 + pi)


def test_issue_4547():
    assert limit(cot(x), x, 0, dir='+') == oo
    assert limit(cot(x), x, pi/2, dir='+') == 0


def test_issue_5164():
    assert limit(x**0.5, x, oo) == oo**0.5 == oo
    assert limit(x**0.5, x, 16) == S(16)**0.5
    assert limit(x**0.5, x, 0) == 0
    assert limit(x**(-0.5), x, oo) == 0
    assert limit(x**(-0.5), x, 4) == S(4)**(-0.5)


def test_issue_5183():
    # using list(...) so py.test can recalculate values
    tests = list(cartes([x, -x],
                        [-1, 1],
                        [2, 3, Rational(1, 2), Rational(2, 3)],
                        ['-', '+']))
    results = (oo, oo, -oo, oo, -oo*I, oo, -oo*(-1)**Rational(1, 3), oo,
               0, 0, 0, 0, 0, 0, 0, 0,
               oo, oo, oo, -oo, oo, -oo*I, oo, -oo*(-1)**Rational(1, 3),
               0, 0, 0, 0, 0, 0, 0, 0)
    assert len(tests) == len(results)
    for i, (args, res) in enumerate(zip(tests, results)):
        y, s, e, d = args
        eq = y**(s*e)
        try:
            assert limit(eq, x, 0, dir=d) == res
        except AssertionError:
            if 0:  # change to 1 if you want to see the failing tests
                print()
                print(i, res, eq, d, limit(eq, x, 0, dir=d))
            else:
                assert None


def test_issue_5184():
    assert limit(sin(x)/x, x, oo) == 0
    assert limit(atan(x), x, oo) == pi/2
    assert limit(gamma(x), x, oo) == oo
    assert limit(cos(x)/x, x, oo) == 0
    assert limit(gamma(x), x, Rational(1, 2)) == sqrt(pi)

    r = Symbol('r', real=True, finite=True)
    assert limit(r*sin(1/r), r, 0) == 0


def test_issue_5229():
    assert limit((1 + y)**(1/y) - S.Exp1, y, 0) == 0


def test_issue_4546():
    # using list(...) so py.test can recalculate values
    tests = list(cartes([cot, tan],
                        [-pi/2, 0, pi/2, pi, 3*pi/2],
                        ['-', '+']))
    results = (0, 0, -oo, oo, 0, 0, -oo, oo, 0, 0,
               oo, -oo, 0, 0, oo, -oo, 0, 0, oo, -oo)
    assert len(tests) == len(results)
    for i, (args, res) in enumerate(zip(tests, results)):
        f, l, d = args
        eq = f(x)
        try:
            assert limit(eq, x, l, dir=d) == res
        except AssertionError:
            if 0:  # change to 1 if you want to see the failing tests
                print()
                print(i, res, eq, l, d, limit(eq, x, l, dir=d))
            else:
                assert None


def test_issue_3934():
    assert limit((1 + x**log(3))**(1/x), x, 0) == 1
    assert limit((5**(1/x) + 3**(1/x))**x, x, 0) == 5


def test_calculate_series():
    # needs gruntz calculate_series to go to n = 32
    assert limit(x**(S(77)/3)/(1 + x**(S(77)/3)), x, oo) == 1
    # needs gruntz calculate_series to go to n = 128
    assert limit(x**101.1/(1 + x**101.1), x, oo) == 1


def test_issue_5955():
    assert limit((x**16)/(1 + x**16), x, oo) == 1
    assert limit((x**100)/(1 + x**100), x, oo) == 1
    assert limit((x**1885)/(1 + x**1885), x, oo) == 1
    assert limit((x**1000/((x + 1)**1000 + exp(-x))), x, oo) == 1


def test_newissue():
    assert limit(exp(1/sin(x))/exp(cot(x)), x, 0) == 1


def test_extended_real_line():
    assert limit(x - oo, x, oo) == -oo
    assert limit(oo - x, x, -oo) == oo
    assert limit(x**2/(x - 5) - oo, x, oo) == -oo
    assert limit(1/(x + sin(x)) - oo, x, 0) == -oo
    assert limit(oo/x, x, oo) == oo
    assert limit(x - oo + 1/x, x, oo) == -oo
    assert limit(x - oo + 1/x, x, 0) == -oo


@XFAIL
def test_order_oo():
    x = Symbol('x', positive=True, finite=True)
    assert Order(x)*oo != Order(1, x)
    assert limit(oo/(x**2 - 4), x, oo) == oo


def test_issue_5436():
    raises(NotImplementedError, lambda: limit(exp(x*y), x, oo))
    raises(NotImplementedError, lambda: limit(exp(-x*y), x, oo))


def test_Limit_dir():
    raises(TypeError, lambda: Limit(x, x, 0, dir=0))
    raises(ValueError, lambda: Limit(x, x, 0, dir='0'))


def test_polynomial():
    assert limit((x + 1)**1000/((x + 1)**1000 + 1), x, oo) == 1
    assert limit((x + 1)**1000/((x + 1)**1000 + 1), x, -oo) == 1


def test_rational():
    assert limit(1/y - (1/(y + x) + x/(y + x)/y)/z, x, oo) == (z - 1)/(y*z)
    assert limit(1/y - (1/(y + x) + x/(y + x)/y)/z, x, -oo) == (z - 1)/(y*z)


def test_issue_5740():
    assert limit(log(x)*z - log(2*x)*y, x, 0) == oo*sign(y - z)


def test_issue_6366():
    n = Symbol('n', integer=True, positive=True)
    r = (n + 1)*x**(n + 1)/(x**(n + 1) - 1) - x/(x - 1)
    assert limit(r, x, 1).simplify() == n/2


def test_factorial():
    from sympy import factorial, E
    f = factorial(x)
    assert limit(f, x, oo) == oo
    assert limit(x/f, x, oo) == 0
    # see Stirling's approximation:
    # https://en.wikipedia.org/wiki/Stirling's_approximation
    assert limit(f/(sqrt(2*pi*x)*(x/E)**x), x, oo) == 1
    assert limit(f, x, -oo) == factorial(-oo)
    assert limit(f, x, x**2) == factorial(x**2)
    assert limit(f, x, -x**2) == factorial(-x**2)


def test_issue_6560():
    e = (5*x**3/4 - 3*x/4 + (y*(3*x**2/2 - S(1)/2) +
                             35*x**4/8 - 15*x**2/4 + S(3)/8)/(2*(y + 1)))
    assert limit(e, y, oo) == (5*x**3 + 3*x**2 - 3*x - 1)/4


def test_issue_5172():
    n = Symbol('n')
    r = Symbol('r', positive=True)
    c = Symbol('c')
    p = Symbol('p', positive=True)
    m = Symbol('m', negative=True)
    expr = ((2*n*(n - r + 1)/(n + r*(n - r + 1)))**c +
            (r - 1)*(n*(n - r + 2)/(n + r*(n - r + 1)))**c - n)/(n**c - n)
    expr = expr.subs(c, c + 1)
    raises(NotImplementedError, lambda: limit(expr, n, oo))
    assert limit(expr.subs(c, m), n, oo) == 1
    assert limit(expr.subs(c, p), n, oo).simplify() == \
        (2**(p + 1) + r - 1)/(r + 1)**(p + 1)


def test_issue_7088():
    a = Symbol('a')
    assert limit(sqrt(x/(x + a)), x, oo) == 1


def test_issue_6364():
    a = Symbol('a')
    e = z/(1 - sqrt(1 + z)*sin(a)**2 - sqrt(1 - z)*cos(a)**2)
    assert limit(e, z, 0).simplify() == 2/cos(2*a)


def test_issue_4099():
    a = Symbol('a')
    assert limit(a/x, x, 0) == oo*sign(a)
    assert limit(-a/x, x, 0) == -oo*sign(a)
    assert limit(-a*x, x, oo) == -oo*sign(a)
    assert limit(a*x, x, oo) == oo*sign(a)


def test_issue_4503():
    dx = Symbol('dx')
    assert limit((sqrt(1 + exp(x + dx)) - sqrt(1 + exp(x)))/dx, dx, 0) == \
        exp(x)/(2*sqrt(exp(x) + 1))


def test_issue_8730():
    assert limit(subfactorial(x), x, oo) == oo


def test_issue_10801():
    # make sure limits work with binomial
    assert limit(16**k / (k * binomial(2*k, k)**2), k, oo) == pi


def test_issue_9205():
    x, y, a = symbols('x, y, a')
    assert Limit(x, x, a).free_symbols == {a}
    assert Limit(x, x, a, '-').free_symbols == {a}
    assert Limit(x + y, x + y, a).free_symbols == {a}
    assert Limit(-x**2 + y, x**2, a).free_symbols == {y, a}


def test_issue_11879():
    assert simplify(limit(((x+y)**n-x**n)/y, y, 0)) == n*x**(n-1)


def test_limit_with_Float():
    k = symbols("k")
    assert limit(1.0 ** k, k, oo) == 1
    assert limit(0.3*1.0**k, k, oo) == Float(0.3)


def test_issue_10610():
    assert limit(3**x*3**(-x - 1)*(x + 1)**2/x**2, x, oo) == S(1)/3


def test_issue_6599():
    assert limit((n + cos(n))/n, n, oo) == 1


def test_issue_12555():
    assert limit((3**x + 2* x**10) / (x**10 + exp(x)), x, -oo) == 2
    assert limit((3**x + 2* x**10) / (x**10 + exp(x)), x, oo) == oo


def test_issue_12564():
    assert limit(x**2 + x*sin(x) + cos(x), x, -oo) == oo
    assert limit(x**2 + x*sin(x) + cos(x), x, oo) == oo
    assert limit(((x + cos(x))**2).expand(), x, oo) == oo
    assert limit(((x + sin(x))**2).expand(), x, oo) == oo
    assert limit(((x + cos(x))**2).expand(), x, -oo) == oo
    assert limit(((x + sin(x))**2).expand(), x, -oo) == oo


def test_issue_14456():
    raises(NotImplementedError, lambda: Limit(exp(x), x, zoo).doit())
    raises(NotImplementedError, lambda: Limit(x**2/(x+1), x, zoo).doit())


def test_issue_14411():
    assert limit(3*sec(4*pi*x - x/3), x, 3*pi/(24*pi - 2)) == -oo


def test_issue_14574():
    assert limit(sqrt(x)*cos(x - x**2) / (x + 1), x, oo) == 0


def test_issue_10102():
    assert limit(fresnels(x), x, oo) == S.Half
    assert limit(3 + fresnels(x), x, oo) == 3 + S.Half
    assert limit(5*fresnels(x), x, oo) == 5*S.Half
    assert limit(fresnelc(x), x, oo) == S.Half
    assert limit(fresnels(x), x, -oo) == -S.Half
    assert limit(4*fresnelc(x), x, -oo) == -2


def test_issue_14377():
    raises(NotImplementedError, lambda: limit(exp(I*x)*sin(pi*x), x, oo))


def test_issue_15984():
    assert limit((-x + log(exp(x) + 1))/x, x, oo, dir='-').doit() == 0
