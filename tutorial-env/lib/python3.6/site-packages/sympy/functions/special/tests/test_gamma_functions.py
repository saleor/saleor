from sympy import (
    Symbol, gamma, I, oo, nan, zoo, factorial, sqrt, Rational, log,
    polygamma, EulerGamma, pi, uppergamma, S, expand_func, loggamma, sin,
    cos, O, lowergamma, exp, erf, erfc, exp_polar, harmonic, zeta,conjugate)
from sympy.core.function import ArgumentIndexError
from sympy.utilities.randtest import (test_derivative_numerically as td,
                                      random_complex_number as randcplx,
                                      verify_numerically as tn)
from sympy.utilities.pytest import raises

x = Symbol('x')
y = Symbol('y')
n = Symbol('n', integer=True)
w = Symbol('w', real=True)

def test_gamma():
    assert gamma(nan) == nan
    assert gamma(oo) == oo

    assert gamma(-100) == zoo
    assert gamma(0) == zoo

    assert gamma(1) == 1
    assert gamma(2) == 1
    assert gamma(3) == 2

    assert gamma(102) == factorial(101)

    assert gamma(Rational(1, 2)) == sqrt(pi)

    assert gamma(Rational(3, 2)) == Rational(1, 2)*sqrt(pi)
    assert gamma(Rational(5, 2)) == Rational(3, 4)*sqrt(pi)
    assert gamma(Rational(7, 2)) == Rational(15, 8)*sqrt(pi)

    assert gamma(Rational(-1, 2)) == -2*sqrt(pi)
    assert gamma(Rational(-3, 2)) == Rational(4, 3)*sqrt(pi)
    assert gamma(Rational(-5, 2)) == -Rational(8, 15)*sqrt(pi)

    assert gamma(Rational(-15, 2)) == Rational(256, 2027025)*sqrt(pi)

    assert gamma(Rational(
        -11, 8)).expand(func=True) == Rational(64, 33)*gamma(Rational(5, 8))
    assert gamma(Rational(
        -10, 3)).expand(func=True) == Rational(81, 280)*gamma(Rational(2, 3))
    assert gamma(Rational(
        14, 3)).expand(func=True) == Rational(880, 81)*gamma(Rational(2, 3))
    assert gamma(Rational(
        17, 7)).expand(func=True) == Rational(30, 49)*gamma(Rational(3, 7))
    assert gamma(Rational(
        19, 8)).expand(func=True) == Rational(33, 64)*gamma(Rational(3, 8))

    assert gamma(x).diff(x) == gamma(x)*polygamma(0, x)

    assert gamma(x - 1).expand(func=True) == gamma(x)/(x - 1)
    assert gamma(x + 2).expand(func=True, mul=False) == x*(x + 1)*gamma(x)

    assert conjugate(gamma(x)) == gamma(conjugate(x))

    assert expand_func(gamma(x + Rational(3, 2))) == \
        (x + Rational(1, 2))*gamma(x + Rational(1, 2))

    assert expand_func(gamma(x - Rational(1, 2))) == \
        gamma(Rational(1, 2) + x)/(x - Rational(1, 2))

    # Test a bug:
    assert expand_func(gamma(x + Rational(3, 4))) == gamma(x + Rational(3, 4))

    assert gamma(3*exp_polar(I*pi)/4).is_nonnegative is False
    assert gamma(3*exp_polar(I*pi)/4).is_nonpositive is True


def test_gamma_rewrite():
    assert gamma(n).rewrite(factorial) == factorial(n - 1)


def test_gamma_series():
    assert gamma(x + 1).series(x, 0, 3) == \
        1 - EulerGamma*x + x**2*(EulerGamma**2/2 + pi**2/12) + O(x**3)
    assert gamma(x).series(x, -1, 3) == \
        -1/(x + 1) + EulerGamma - 1 + (x + 1)*(-1 - pi**2/12 - EulerGamma**2/2 + \
       EulerGamma) + (x + 1)**2*(-1 - pi**2/12 - EulerGamma**2/2 + EulerGamma**3/6 - \
       polygamma(2, 1)/6 + EulerGamma*pi**2/12 + EulerGamma) + O((x + 1)**3, (x, -1))


def tn_branch(s, func):
    from sympy import I, pi, exp_polar
    from random import uniform
    c = uniform(1, 5)
    expr = func(s, c*exp_polar(I*pi)) - func(s, c*exp_polar(-I*pi))
    eps = 1e-15
    expr2 = func(s + eps, -c + eps*I) - func(s + eps, -c - eps*I)
    return abs(expr.n() - expr2.n()).n() < 1e-10


def test_lowergamma():
    from sympy import meijerg, exp_polar, I, expint
    assert lowergamma(x, 0) == 0
    assert lowergamma(x, y).diff(y) == y**(x - 1)*exp(-y)
    assert td(lowergamma(randcplx(), y), y)
    assert td(lowergamma(x, randcplx()), x)
    assert lowergamma(x, y).diff(x) == \
        gamma(x)*polygamma(0, x) - uppergamma(x, y)*log(y) \
        - meijerg([], [1, 1], [0, 0, x], [], y)

    assert lowergamma(S.Half, x) == sqrt(pi)*erf(sqrt(x))
    assert not lowergamma(S.Half - 3, x).has(lowergamma)
    assert not lowergamma(S.Half + 3, x).has(lowergamma)
    assert lowergamma(S.Half, x, evaluate=False).has(lowergamma)
    assert tn(lowergamma(S.Half + 3, x, evaluate=False),
              lowergamma(S.Half + 3, x), x)
    assert tn(lowergamma(S.Half - 3, x, evaluate=False),
              lowergamma(S.Half - 3, x), x)

    assert tn_branch(-3, lowergamma)
    assert tn_branch(-4, lowergamma)
    assert tn_branch(S(1)/3, lowergamma)
    assert tn_branch(pi, lowergamma)
    assert lowergamma(3, exp_polar(4*pi*I)*x) == lowergamma(3, x)
    assert lowergamma(y, exp_polar(5*pi*I)*x) == \
        exp(4*I*pi*y)*lowergamma(y, x*exp_polar(pi*I))
    assert lowergamma(-2, exp_polar(5*pi*I)*x) == \
        lowergamma(-2, x*exp_polar(I*pi)) + 2*pi*I

    assert conjugate(lowergamma(x, y)) == lowergamma(conjugate(x), conjugate(y))
    assert conjugate(lowergamma(x, 0)) == conjugate(lowergamma(x, 0))
    assert conjugate(lowergamma(x, -oo)) == conjugate(lowergamma(x, -oo))

    assert lowergamma(
        x, y).rewrite(expint) == -y**x*expint(-x + 1, y) + gamma(x)
    k = Symbol('k', integer=True)
    assert lowergamma(
        k, y).rewrite(expint) == -y**k*expint(-k + 1, y) + gamma(k)
    k = Symbol('k', integer=True, positive=False)
    assert lowergamma(k, y).rewrite(expint) == lowergamma(k, y)
    assert lowergamma(x, y).rewrite(uppergamma) == gamma(x) - uppergamma(x, y)

    assert lowergamma(70, 6) == factorial(69) - 69035724522603011058660187038367026272747334489677105069435923032634389419656200387949342530805432320 * exp(-6)
    assert (lowergamma(S(77) / 2, 6) - lowergamma(S(77) / 2, 6, evaluate=False)).evalf() < 1e-16
    assert (lowergamma(-S(77) / 2, 6) - lowergamma(-S(77) / 2, 6, evaluate=False)).evalf() < 1e-16


def test_uppergamma():
    from sympy import meijerg, exp_polar, I, expint
    assert uppergamma(4, 0) == 6
    assert uppergamma(x, y).diff(y) == -y**(x - 1)*exp(-y)
    assert td(uppergamma(randcplx(), y), y)
    assert uppergamma(x, y).diff(x) == \
        uppergamma(x, y)*log(y) + meijerg([], [1, 1], [0, 0, x], [], y)
    assert td(uppergamma(x, randcplx()), x)

    assert uppergamma(S.Half, x) == sqrt(pi)*erfc(sqrt(x))
    assert not uppergamma(S.Half - 3, x).has(uppergamma)
    assert not uppergamma(S.Half + 3, x).has(uppergamma)
    assert uppergamma(S.Half, x, evaluate=False).has(uppergamma)
    assert tn(uppergamma(S.Half + 3, x, evaluate=False),
              uppergamma(S.Half + 3, x), x)
    assert tn(uppergamma(S.Half - 3, x, evaluate=False),
              uppergamma(S.Half - 3, x), x)

    assert tn_branch(-3, uppergamma)
    assert tn_branch(-4, uppergamma)
    assert tn_branch(S(1)/3, uppergamma)
    assert tn_branch(pi, uppergamma)
    assert uppergamma(3, exp_polar(4*pi*I)*x) == uppergamma(3, x)
    assert uppergamma(y, exp_polar(5*pi*I)*x) == \
        exp(4*I*pi*y)*uppergamma(y, x*exp_polar(pi*I)) + \
        gamma(y)*(1 - exp(4*pi*I*y))
    assert uppergamma(-2, exp_polar(5*pi*I)*x) == \
        uppergamma(-2, x*exp_polar(I*pi)) - 2*pi*I

    assert uppergamma(-2, x) == expint(3, x)/x**2

    assert conjugate(uppergamma(x, y)) == uppergamma(conjugate(x), conjugate(y))
    assert conjugate(uppergamma(x, 0)) == gamma(conjugate(x))
    assert conjugate(uppergamma(x, -oo)) == conjugate(uppergamma(x, -oo))

    assert uppergamma(x, y).rewrite(expint) == y**x*expint(-x + 1, y)
    assert uppergamma(x, y).rewrite(lowergamma) == gamma(x) - lowergamma(x, y)

    assert uppergamma(70, 6) == 69035724522603011058660187038367026272747334489677105069435923032634389419656200387949342530805432320*exp(-6)
    assert (uppergamma(S(77) / 2, 6) - uppergamma(S(77) / 2, 6, evaluate=False)).evalf() < 1e-16
    assert (uppergamma(-S(77) / 2, 6) - uppergamma(-S(77) / 2, 6, evaluate=False)).evalf() < 1e-16

def test_polygamma():
    from sympy import I

    assert polygamma(n, nan) == nan

    assert polygamma(0, oo) == oo
    assert polygamma(0, -oo) == oo
    assert polygamma(0, I*oo) == oo
    assert polygamma(0, -I*oo) == oo
    assert polygamma(1, oo) == 0
    assert polygamma(5, oo) == 0

    assert polygamma(0, -9) == zoo

    assert polygamma(0, -9) == zoo
    assert polygamma(0, -1) == zoo

    assert polygamma(0, 0) == zoo

    assert polygamma(0, 1) == -EulerGamma
    assert polygamma(0, 7) == Rational(49, 20) - EulerGamma

    assert polygamma(1, 1) == pi**2/6
    assert polygamma(1, 2) == pi**2/6 - 1
    assert polygamma(1, 3) == pi**2/6 - Rational(5, 4)
    assert polygamma(3, 1) == pi**4 / 15
    assert polygamma(3, 5) == 6*(Rational(-22369, 20736) + pi**4/90)
    assert polygamma(5, 1) == 8 * pi**6 / 63

    def t(m, n):
        x = S(m)/n
        r = polygamma(0, x)
        if r.has(polygamma):
            return False
        return abs(polygamma(0, x.n()).n() - r.n()).n() < 1e-10
    assert t(1, 2)
    assert t(3, 2)
    assert t(-1, 2)
    assert t(1, 4)
    assert t(-3, 4)
    assert t(1, 3)
    assert t(4, 3)
    assert t(3, 4)
    assert t(2, 3)
    assert t(123, 5)

    assert polygamma(0, x).rewrite(zeta) == polygamma(0, x)
    assert polygamma(1, x).rewrite(zeta) == zeta(2, x)
    assert polygamma(2, x).rewrite(zeta) == -2*zeta(3, x)

    assert polygamma(3, 7*x).diff(x) == 7*polygamma(4, 7*x)

    assert polygamma(0, x).rewrite(harmonic) == harmonic(x - 1) - EulerGamma
    assert polygamma(2, x).rewrite(harmonic) == 2*harmonic(x - 1, 3) - 2*zeta(3)
    ni = Symbol("n", integer=True)
    assert polygamma(ni, x).rewrite(harmonic) == (-1)**(ni + 1)*(-harmonic(x - 1, ni + 1)
                                                                 + zeta(ni + 1))*factorial(ni)

    # Polygamma of non-negative integer order is unbranched:
    from sympy import exp_polar
    k = Symbol('n', integer=True, nonnegative=True)
    assert polygamma(k, exp_polar(2*I*pi)*x) == polygamma(k, x)

    # but negative integers are branched!
    k = Symbol('n', integer=True)
    assert polygamma(k, exp_polar(2*I*pi)*x).args == (k, exp_polar(2*I*pi)*x)

    # Polygamma of order -1 is loggamma:
    assert polygamma(-1, x) == loggamma(x)

    # But smaller orders are iterated integrals and don't have a special name
    assert polygamma(-2, x).func is polygamma

    # Test a bug
    assert polygamma(0, -x).expand(func=True) == polygamma(0, -x)


def test_polygamma_expand_func():
    assert polygamma(0, x).expand(func=True) == polygamma(0, x)
    assert polygamma(0, 2*x).expand(func=True) == \
        polygamma(0, x)/2 + polygamma(0, Rational(1, 2) + x)/2 + log(2)
    assert polygamma(1, 2*x).expand(func=True) == \
        polygamma(1, x)/4 + polygamma(1, Rational(1, 2) + x)/4
    assert polygamma(2, x).expand(func=True) == \
        polygamma(2, x)
    assert polygamma(0, -1 + x).expand(func=True) == \
        polygamma(0, x) - 1/(x - 1)
    assert polygamma(0, 1 + x).expand(func=True) == \
        1/x + polygamma(0, x )
    assert polygamma(0, 2 + x).expand(func=True) == \
        1/x + 1/(1 + x) + polygamma(0, x)
    assert polygamma(0, 3 + x).expand(func=True) == \
        polygamma(0, x) + 1/x + 1/(1 + x) + 1/(2 + x)
    assert polygamma(0, 4 + x).expand(func=True) == \
        polygamma(0, x) + 1/x + 1/(1 + x) + 1/(2 + x) + 1/(3 + x)
    assert polygamma(1, 1 + x).expand(func=True) == \
        polygamma(1, x) - 1/x**2
    assert polygamma(1, 2 + x).expand(func=True, multinomial=False) == \
        polygamma(1, x) - 1/x**2 - 1/(1 + x)**2
    assert polygamma(1, 3 + x).expand(func=True, multinomial=False) == \
        polygamma(1, x) - 1/x**2 - 1/(1 + x)**2 - 1/(2 + x)**2
    assert polygamma(1, 4 + x).expand(func=True, multinomial=False) == \
        polygamma(1, x) - 1/x**2 - 1/(1 + x)**2 - \
        1/(2 + x)**2 - 1/(3 + x)**2
    assert polygamma(0, x + y).expand(func=True) == \
        polygamma(0, x + y)
    assert polygamma(1, x + y).expand(func=True) == \
        polygamma(1, x + y)
    assert polygamma(1, 3 + 4*x + y).expand(func=True, multinomial=False) == \
        polygamma(1, y + 4*x) - 1/(y + 4*x)**2 - \
        1/(1 + y + 4*x)**2 - 1/(2 + y + 4*x)**2
    assert polygamma(3, 3 + 4*x + y).expand(func=True, multinomial=False) == \
        polygamma(3, y + 4*x) - 6/(y + 4*x)**4 - \
        6/(1 + y + 4*x)**4 - 6/(2 + y + 4*x)**4
    assert polygamma(3, 4*x + y + 1).expand(func=True, multinomial=False) == \
        polygamma(3, y + 4*x) - 6/(y + 4*x)**4
    e = polygamma(3, 4*x + y + S(3)/2)
    assert e.expand(func=True) == e
    e = polygamma(3, x + y + S(3)/4)
    assert e.expand(func=True, basic=False) == e


def test_loggamma():
    raises(TypeError, lambda: loggamma(2, 3))
    raises(ArgumentIndexError, lambda: loggamma(x).fdiff(2))

    assert loggamma(-1) == oo
    assert loggamma(-2) == oo
    assert loggamma(0) == oo
    assert loggamma(1) == 0
    assert loggamma(2) == 0
    assert loggamma(3) == log(2)
    assert loggamma(4) == log(6)

    n = Symbol("n", integer=True, positive=True)
    assert loggamma(n) == log(gamma(n))
    assert loggamma(-n) == oo
    assert loggamma(n/2) == log(2**(-n + 1)*sqrt(pi)*gamma(n)/gamma(n/2 + S.Half))

    from sympy import I

    assert loggamma(oo) == oo
    assert loggamma(-oo) == zoo
    assert loggamma(I*oo) == zoo
    assert loggamma(-I*oo) == zoo
    assert loggamma(zoo) == zoo
    assert loggamma(nan) == nan

    L = loggamma(S(16)/3)
    E = -5*log(3) + loggamma(S(1)/3) + log(4) + log(7) + log(10) + log(13)
    assert expand_func(L).doit() == E
    assert L.n() == E.n()

    L = loggamma(19/S(4))
    E = -4*log(4) + loggamma(S(3)/4) + log(3) + log(7) + log(11) + log(15)
    assert expand_func(L).doit() == E
    assert L.n() == E.n()

    L = loggamma(S(23)/7)
    E = -3*log(7) + log(2) + loggamma(S(2)/7) + log(9) + log(16)
    assert expand_func(L).doit() == E
    assert L.n() == E.n()

    L = loggamma(19/S(4)-7)
    E = -log(9) - log(5) + loggamma(S(3)/4) + 3*log(4) - 3*I*pi
    assert expand_func(L).doit() == E
    assert L.n() == E.n()

    L = loggamma(23/S(7)-6)
    E = -log(19) - log(12) - log(5) + loggamma(S(2)/7) + 3*log(7) - 3*I*pi
    assert expand_func(L).doit() == E
    assert L.n() == E.n()

    assert loggamma(x).diff(x) == polygamma(0, x)
    s1 = loggamma(1/(x + sin(x)) + cos(x)).nseries(x, n=4)
    s2 = (-log(2*x) - 1)/(2*x) - log(x/pi)/2 + (4 - log(2*x))*x/24 + O(x**2) + \
        log(x)*x**2/2
    assert (s1 - s2).expand(force=True).removeO() == 0
    s1 = loggamma(1/x).series(x)
    s2 = (1/x - S(1)/2)*log(1/x) - 1/x + log(2*pi)/2 + \
        x/12 - x**3/360 + x**5/1260 + O(x**7)
    assert ((s1 - s2).expand(force=True)).removeO() == 0

    assert loggamma(x).rewrite('intractable') == log(gamma(x))

    s1 = loggamma(x).series(x)
    assert s1 == -log(x) - EulerGamma*x + pi**2*x**2/12 + x**3*polygamma(2, 1)/6 + \
        pi**4*x**4/360 + x**5*polygamma(4, 1)/120 + O(x**6)
    assert s1 == loggamma(x).rewrite('intractable').series(x)

    assert conjugate(loggamma(x)) == loggamma(conjugate(x))
    assert conjugate(loggamma(0)) == conjugate(loggamma(0))
    assert conjugate(loggamma(1)) == loggamma(conjugate(1))
    assert conjugate(loggamma(-oo)) == conjugate(loggamma(-oo))
    assert loggamma(x).is_real is None
    y, z = Symbol('y', real=True), Symbol('z', imaginary=True)
    assert loggamma(y).is_real
    assert loggamma(z).is_real is False

    def tN(N, M):
        assert loggamma(1/x)._eval_nseries(x, n=N).getn() == M
    tN(0, 0)
    tN(1, 1)
    tN(2, 3)
    tN(3, 3)
    tN(4, 5)
    tN(5, 5)


def test_polygamma_expansion():
    # A. & S., pa. 259 and 260
    assert polygamma(0, 1/x).nseries(x, n=3) == \
        -log(x) - x/2 - x**2/12 + O(x**4)
    assert polygamma(1, 1/x).series(x, n=5) == \
        x + x**2/2 + x**3/6 + O(x**5)
    assert polygamma(3, 1/x).nseries(x, n=11) == \
        2*x**3 + 3*x**4 + 2*x**5 - x**7 + 4*x**9/3 + O(x**11)


def test_issue_8657():
    n = Symbol('n', negative=True, integer=True)
    m = Symbol('m', integer=True)
    o = Symbol('o', positive=True)
    p = Symbol('p', negative=True, integer=False)
    assert gamma(n).is_real is None
    assert gamma(m).is_real is None
    assert gamma(o).is_real is True
    assert gamma(p).is_real is True
    assert gamma(w).is_real is None


def test_issue_8524():
    x = Symbol('x', positive=True)
    y = Symbol('y', negative=True)
    z = Symbol('z', positive=False)
    p = Symbol('p', negative=False)
    q = Symbol('q', integer=True)
    r = Symbol('r', integer=False)
    e = Symbol('e', even=True, negative=True)
    assert gamma(x).is_positive is True
    assert gamma(y).is_positive is None
    assert gamma(z).is_positive is None
    assert gamma(p).is_positive is None
    assert gamma(q).is_positive is None
    assert gamma(r).is_positive is None
    assert gamma(e + S.Half).is_positive is True
    assert gamma(e - S.Half).is_positive is False

def test_issue_14450():
    assert uppergamma(S(3)/8, x).evalf() == uppergamma(0.375, x)
    assert lowergamma(x, S(3)/8).evalf() == lowergamma(x, 0.375)
    # some values from Wolfram Alpha for comparison
    assert abs(uppergamma(S(3)/8, 2).evalf() - 0.07105675881) < 1e-9
    assert abs(lowergamma(S(3)/8, 2).evalf() - 2.2993794256) < 1e-9

def test_issue_14528():
    k = Symbol('k', integer=True, nonpositive=True)
    assert isinstance(gamma(k), gamma)
