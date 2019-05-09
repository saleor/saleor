from sympy import sin, cos, exp, E, series, oo, S, Derivative, O, Integral, \
    Function, log, sqrt, Symbol, Subs, pi, symbols, IndexedBase, atan
from sympy.abc import x, y, n, k
from sympy.utilities.pytest import raises
from sympy.core.compatibility import range
from sympy.series.gruntz import calculate_series


def test_sin():
    e1 = sin(x).series(x, 0)
    e2 = series(sin(x), x, 0)
    assert e1 == e2


def test_cos():
    e1 = cos(x).series(x, 0)
    e2 = series(cos(x), x, 0)
    assert e1 == e2


def test_exp():
    e1 = exp(x).series(x, 0)
    e2 = series(exp(x), x, 0)
    assert e1 == e2


def test_exp2():
    e1 = exp(cos(x)).series(x, 0)
    e2 = series(exp(cos(x)), x, 0)
    assert e1 == e2


def test_issue_5223():
    assert series(1, x) == 1
    assert next(S(0).lseries(x)) == 0
    assert cos(x).series() == cos(x).series(x)
    raises(ValueError, lambda: cos(x + y).series())
    raises(ValueError, lambda: x.series(dir=""))

    assert (cos(x).series(x, 1) -
            cos(x + 1).series(x).subs(x, x - 1)).removeO() == 0
    e = cos(x).series(x, 1, n=None)
    assert [next(e) for i in range(2)] == [cos(1), -((x - 1)*sin(1))]
    e = cos(x).series(x, 1, n=None, dir='-')
    assert [next(e) for i in range(2)] == [cos(1), (1 - x)*sin(1)]
    # the following test is exact so no need for x -> x - 1 replacement
    assert abs(x).series(x, 1, dir='-') == x
    assert exp(x).series(x, 1, dir='-', n=3).removeO() == \
        E - E*(-x + 1) + E*(-x + 1)**2/2

    D = Derivative
    assert D(x**2 + x**3*y**2, x, 2, y, 1).series(x).doit() == 12*x*y
    assert next(D(cos(x), x).lseries()) == D(1, x)
    assert D(
        exp(x), x).series(n=3) == D(1, x) + D(x, x) + D(x**2/2, x) + D(x**3/6, x) + O(x**3)

    assert Integral(x, (x, 1, 3), (y, 1, x)).series(x) == -4 + 4*x

    assert (1 + x + O(x**2)).getn() == 2
    assert (1 + x).getn() is None

    assert ((1/sin(x))**oo).series() == oo
    logx = Symbol('logx')
    assert ((sin(x))**y).nseries(x, n=1, logx=logx) == \
        exp(y*logx) + O(x*exp(y*logx), x)

    assert sin(1/x).series(x, oo, n=5) == 1/x - 1/(6*x**3) + O(x**(-5), (x, oo))
    assert abs(x).series(x, oo, n=5, dir='+') == x
    assert abs(x).series(x, -oo, n=5, dir='-') == -x
    assert abs(-x).series(x, oo, n=5, dir='+') == x
    assert abs(-x).series(x, -oo, n=5, dir='-') == -x

    assert exp(x*log(x)).series(n=3) == \
        1 + x*log(x) + x**2*log(x)**2/2 + O(x**3*log(x)**3)
    # XXX is this right? If not, fix "ngot > n" handling in expr.
    p = Symbol('p', positive=True)
    assert exp(sqrt(p)**3*log(p)).series(n=3) == \
        1 + p**S('3/2')*log(p) + O(p**3*log(p)**3)

    assert exp(sin(x)*log(x)).series(n=2) == 1 + x*log(x) + O(x**2*log(x)**2)


def test_issue_11313():
    assert Integral(cos(x), x).series(x) == sin(x).series(x)
    assert Derivative(sin(x), x).series(x, n=3).doit() == cos(x).series(x, n=3)

    assert Derivative(x**3, x).as_leading_term(x) == 3*x**2
    assert Derivative(x**3, y).as_leading_term(x) == 0
    assert Derivative(sin(x), x).as_leading_term(x) == 1
    assert Derivative(cos(x), x).as_leading_term(x) == -x

    # This result is equivalent to zero, zero is not return because
    # `Expr.series` doesn't currently detect an `x` in its `free_symbol`s.
    assert Derivative(1, x).as_leading_term(x) == Derivative(1, x)

    assert Derivative(exp(x), x).series(x).doit() == exp(x).series(x)
    assert 1 + Integral(exp(x), x).series(x) == exp(x).series(x)

    assert Derivative(log(x), x).series(x).doit() == (1/x).series(x)
    assert Integral(log(x), x).series(x) == Integral(log(x), x).doit().series(x)


def test_series_of_Subs():
    from sympy.abc import x, y, z

    subs1 = Subs(sin(x), x, y)
    subs2 = Subs(sin(x) * cos(z), x, y)
    subs3 = Subs(sin(x * z), (x, z), (y, x))

    assert subs1.series(x) == subs1
    subs1_series = (Subs(x, x, y) + Subs(-x**3/6, x, y) +
        Subs(x**5/120, x, y) + O(y**6))
    assert subs1.series() == subs1_series
    assert subs1.series(y) == subs1_series
    assert subs1.series(z) == subs1
    assert subs2.series(z) == (Subs(z**4*sin(x)/24, x, y) +
        Subs(-z**2*sin(x)/2, x, y) + Subs(sin(x), x, y) + O(z**6))
    assert subs3.series(x).doit() == subs3.doit().series(x)
    assert subs3.series(z).doit() == sin(x*y)

    raises(ValueError, lambda: Subs(x + 2*y, y, z).series())
    assert Subs(x + y, y, z).series(x).doit() == x + z


def test_issue_3978():
    f = Function('f')
    assert f(x).series(x, 0, 3, dir='-') == \
            f(0) + x*Subs(Derivative(f(x), x), x, 0) + \
            x**2*Subs(Derivative(f(x), x, x), x, 0)/2 + O(x**3)
    assert f(x).series(x, 0, 3) == \
            f(0) + x*Subs(Derivative(f(x), x), x, 0) + \
            x**2*Subs(Derivative(f(x), x, x), x, 0)/2 + O(x**3)
    assert f(x**2).series(x, 0, 3) == \
            f(0) + x**2*Subs(Derivative(f(x), x), x, 0) + O(x**3)
    assert f(x**2+1).series(x, 0, 3) == \
            f(1) + x**2*Subs(Derivative(f(x), x), x, 1) + O(x**3)

    class TestF(Function):
        pass

    assert TestF(x).series(x, 0, 3) ==  TestF(0) + \
            x*Subs(Derivative(TestF(x), x), x, 0) + \
            x**2*Subs(Derivative(TestF(x), x, x), x, 0)/2 + O(x**3)

from sympy.series.acceleration import richardson, shanks
from sympy import Sum, Integer


def test_acceleration():
    e = (1 + 1/n)**n
    assert round(richardson(e, n, 10, 20).evalf(), 10) == round(E.evalf(), 10)

    A = Sum(Integer(-1)**(k + 1) / k, (k, 1, n))
    assert round(shanks(A, n, 25).evalf(), 4) == round(log(2).evalf(), 4)
    assert round(shanks(A, n, 25, 5).evalf(), 10) == round(log(2).evalf(), 10)


def test_issue_5852():
    assert series(1/cos(x/log(x)), x, 0) == 1 + x**2/(2*log(x)**2) + \
        5*x**4/(24*log(x)**4) + O(x**6)


def test_issue_4583():
    assert cos(1 + x + x**2).series(x, 0, 5) == cos(1) - x*sin(1) + \
        x**2*(-sin(1) - cos(1)/2) + x**3*(-cos(1) + sin(1)/6) + \
        x**4*(-11*cos(1)/24 + sin(1)/2) + O(x**5)


def test_issue_6318():
    eq = (1/x)**(S(2)/3)
    assert (eq + 1).as_leading_term(x) == eq


def test_x_is_base_detection():
    eq = (x**2)**(S(2)/3)
    assert eq.series() == x**(S(4)/3)


def test_sin_power():
    e = sin(x)**1.2
    assert calculate_series(e, x) == x**1.2


def test_issue_7203():
    assert series(cos(x), x, pi, 3) == \
        -1 + (x - pi)**2/2 + O((x - pi)**3, (x, pi))


def test_exp_product_positive_factors():
    a, b = symbols('a, b', positive=True)
    x = a * b
    assert series(exp(x), x, n=8) == 1 + a*b + a**2*b**2/2 + \
        a**3*b**3/6 + a**4*b**4/24 + a**5*b**5/120 + a**6*b**6/720 + \
        a**7*b**7/5040 + O(a**8*b**8, a, b)


def test_issue_8805():
    assert series(1, n=8) == 1


def test_issue_10761():
    assert series(1/(x**-2 + x**-3), x, 0) == x**3 - x**4 + x**5 + O(x**6)


def test_issue_14885():
    assert series(x**(-S(3)/2)*exp(x), x, 0) == (x**(-S(3)/2) + 1/sqrt(x) +
        sqrt(x)/2 + x**(S(3)/2)/6 + x**(S(5)/2)/24 + x**(S(7)/2)/120 +
        x**(S(9)/2)/720 + x**(S(11)/2)/5040 + O(x**6))


def test_issue_15539():
    assert series(atan(x), x, -oo) == (-1/(5*x**5) + 1/(3*x**3) - 1/x - pi/2
        + O(x**(-6), (x, -oo)))
    assert series(atan(x), x, oo) == (-1/(5*x**5) + 1/(3*x**3) - 1/x + pi/2
        + O(x**(-6), (x, oo)))
