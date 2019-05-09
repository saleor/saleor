from sympy import (S, Symbol, symbols, factorial, factorial2, Float, binomial,
                   rf, ff, gamma, polygamma, EulerGamma, O, pi, nan,
                   oo, zoo, simplify, expand_func, Product, Mul, Piecewise, Mod,
                   Eq, sqrt, Poly)
from sympy.functions.combinatorial.factorials import subfactorial
from sympy.functions.special.gamma_functions import uppergamma
from sympy.utilities.pytest import XFAIL, raises, slow

#Solves and Fixes Issue #10388 - This is the updated test for the same solved issue

def test_rf_eval_apply():
    x, y = symbols('x,y')
    n, k = symbols('n k', integer=True)
    m = Symbol('m', integer=True, nonnegative=True)

    assert rf(nan, y) == nan
    assert rf(x, nan) == nan

    assert rf(x, y) == rf(x, y)

    assert rf(oo, 0) == 1
    assert rf(-oo, 0) == 1

    assert rf(oo, 6) == oo
    assert rf(-oo, 7) == -oo

    assert rf(oo, -6) == oo
    assert rf(-oo, -7) == oo

    assert rf(x, 0) == 1
    assert rf(x, 1) == x
    assert rf(x, 2) == x*(x + 1)
    assert rf(x, 3) == x*(x + 1)*(x + 2)
    assert rf(x, 5) == x*(x + 1)*(x + 2)*(x + 3)*(x + 4)

    assert rf(x, -1) == 1/(x - 1)
    assert rf(x, -2) == 1/((x - 1)*(x - 2))
    assert rf(x, -3) == 1/((x - 1)*(x - 2)*(x - 3))

    assert rf(1, 100) == factorial(100)

    assert rf(x**2 + 3*x, 2) == (x**2 + 3*x)*(x**2 + 3*x + 1)
    assert isinstance(rf(x**2 + 3*x, 2), Mul)
    assert rf(x**3 + x, -2) == 1/((x**3 + x - 1)*(x**3 + x - 2))

    assert rf(Poly(x**2 + 3*x, x), 2) == Poly(x**4 + 8*x**3 + 19*x**2 + 12*x, x)
    assert isinstance(rf(Poly(x**2 + 3*x, x), 2), Poly)
    raises(ValueError, lambda: rf(Poly(x**2 + 3*x, x, y), 2))
    assert rf(Poly(x**3 + x, x), -2) == 1/(x**6 - 9*x**5 + 35*x**4 - 75*x**3 + 94*x**2 - 66*x + 20)
    raises(ValueError, lambda: rf(Poly(x**3 + x, x, y), -2))

    assert rf(x, m).is_integer is None
    assert rf(n, k).is_integer is None
    assert rf(n, m).is_integer is True
    assert rf(n, k + pi).is_integer is False
    assert rf(n, m + pi).is_integer is False
    assert rf(pi, m).is_integer is False

    assert rf(x, k).rewrite(ff) == ff(x + k - 1, k)
    assert rf(x, k).rewrite(binomial) == factorial(k)*binomial(x + k - 1, k)
    assert rf(n, k).rewrite(factorial) == \
        factorial(n + k - 1) / factorial(n - 1)

    import random
    from mpmath import rf as mpmath_rf
    for i in range(100):
        x = -500 + 500 * random.random()
        k = -500 + 500 * random.random()
        assert (abs(mpmath_rf(x, k) - rf(x, k)) < 10**(-15))


def test_ff_eval_apply():
    x, y = symbols('x,y')
    n, k = symbols('n k', integer=True)
    m = Symbol('m', integer=True, nonnegative=True)

    assert ff(nan, y) == nan
    assert ff(x, nan) == nan

    assert ff(x, y) == ff(x, y)

    assert ff(oo, 0) == 1
    assert ff(-oo, 0) == 1

    assert ff(oo, 6) == oo
    assert ff(-oo, 7) == -oo

    assert ff(oo, -6) == oo
    assert ff(-oo, -7) == oo

    assert ff(x, 0) == 1
    assert ff(x, 1) == x
    assert ff(x, 2) == x*(x - 1)
    assert ff(x, 3) == x*(x - 1)*(x - 2)
    assert ff(x, 5) == x*(x - 1)*(x - 2)*(x - 3)*(x - 4)

    assert ff(x, -1) == 1/(x + 1)
    assert ff(x, -2) == 1/((x + 1)*(x + 2))
    assert ff(x, -3) == 1/((x + 1)*(x + 2)*(x + 3))

    assert ff(100, 100) == factorial(100)

    assert ff(2*x**2 - 5*x, 2) == (2*x**2  - 5*x)*(2*x**2 - 5*x - 1)
    assert isinstance(ff(2*x**2 - 5*x, 2), Mul)
    assert ff(x**2 + 3*x, -2) == 1/((x**2 + 3*x + 1)*(x**2 + 3*x + 2))

    assert ff(Poly(2*x**2 - 5*x, x), 2) == Poly(4*x**4 - 28*x**3 + 59*x**2 - 35*x, x)
    assert isinstance(ff(Poly(2*x**2 - 5*x, x), 2), Poly)
    raises(ValueError, lambda: ff(Poly(2*x**2 - 5*x, x, y), 2))
    assert ff(Poly(x**2 + 3*x, x), -2) == 1/(x**4 + 12*x**3 + 49*x**2 + 78*x + 40)
    raises(ValueError, lambda: ff(Poly(x**2 + 3*x, x, y), -2))


    assert ff(x, m).is_integer is None
    assert ff(n, k).is_integer is None
    assert ff(n, m).is_integer is True
    assert ff(n, k + pi).is_integer is False
    assert ff(n, m + pi).is_integer is False
    assert ff(pi, m).is_integer is False

    assert isinstance(ff(x, x), ff)
    assert ff(n, n) == factorial(n)

    assert ff(x, k).rewrite(rf) == rf(x - k + 1, k)
    assert ff(x, k).rewrite(gamma) == (-1)**k*gamma(k - x) / gamma(-x)
    assert ff(n, k).rewrite(factorial) == factorial(n) / factorial(n - k)
    assert ff(x, k).rewrite(binomial) == factorial(k) * binomial(x, k)

    import random
    from mpmath import ff as mpmath_ff
    for i in range(100):
        x = -500 + 500 * random.random()
        k = -500 + 500 * random.random()
        assert (abs(mpmath_ff(x, k) - ff(x, k)) < 10**(-15))


def test_rf_ff_eval_hiprec():
    maple = Float('6.9109401292234329956525265438452')
    us = ff(18, S(2)/3).evalf(32)
    assert abs(us - maple)/us < 1e-31

    maple = Float('6.8261540131125511557924466355367')
    us = rf(18, S(2)/3).evalf(32)
    assert abs(us - maple)/us < 1e-31

    maple = Float('34.007346127440197150854651814225')
    us = rf(Float('4.4', 32), Float('2.2', 32));
    assert abs(us - maple)/us < 1e-31


def test_rf_lambdify_mpmath():
    from sympy import lambdify
    x, y = symbols('x,y')
    f = lambdify((x,y), rf(x, y), 'mpmath')
    maple = Float('34.007346127440197')
    us = f(4.4, 2.2)
    assert abs(us - maple)/us < 1e-15


def test_factorial():
    x = Symbol('x')
    n = Symbol('n', integer=True)
    k = Symbol('k', integer=True, nonnegative=True)
    r = Symbol('r', integer=False)
    s = Symbol('s', integer=False, negative=True)
    t = Symbol('t', nonnegative=True)
    u = Symbol('u', noninteger=True)

    assert factorial(-2) == zoo
    assert factorial(0) == 1
    assert factorial(7) == 5040
    assert factorial(19) == 121645100408832000
    assert factorial(31) == 8222838654177922817725562880000000
    assert factorial(n).func == factorial
    assert factorial(2*n).func == factorial

    assert factorial(x).is_integer is None
    assert factorial(n).is_integer is None
    assert factorial(k).is_integer
    assert factorial(r).is_integer is None

    assert factorial(n).is_positive is None
    assert factorial(k).is_positive

    assert factorial(x).is_real is None
    assert factorial(n).is_real is None
    assert factorial(k).is_real is True
    assert factorial(r).is_real is None
    assert factorial(s).is_real is True
    assert factorial(t).is_real is True
    assert factorial(u).is_real is True

    assert factorial(x).is_composite is None
    assert factorial(n).is_composite is None
    assert factorial(k).is_composite is None
    assert factorial(k + 3).is_composite is True
    assert factorial(r).is_composite is None
    assert factorial(s).is_composite is None
    assert factorial(t).is_composite is None
    assert factorial(u).is_composite is None

    assert factorial(oo) == oo


def test_factorial_Mod():
    pr = Symbol('pr', prime=True)
    p, q = 10**9 + 9, 10**9 + 33 # prime modulo
    r, s = 10**7 + 5, 33333333 # composite modulo
    assert Mod(factorial(pr - 1), pr) == pr - 1
    assert Mod(factorial(pr - 1), -pr) == -1
    assert Mod(factorial(r - 1, evaluate=False), r) == 0
    assert Mod(factorial(s - 1, evaluate=False), s) == 0
    assert Mod(factorial(p - 1, evaluate=False), p) == p - 1
    assert Mod(factorial(q - 1, evaluate=False), q) == q - 1
    assert Mod(factorial(p - 50, evaluate=False), p) == 854928834
    assert Mod(factorial(q - 1800, evaluate=False), q) == 905504050
    assert Mod(factorial(153, evaluate=False), r) == Mod(factorial(153), r)
    assert Mod(factorial(255, evaluate=False), s) == Mod(factorial(255), s)


def test_factorial_diff():
    n = Symbol('n', integer=True)

    assert factorial(n).diff(n) == \
        gamma(1 + n)*polygamma(0, 1 + n)
    assert factorial(n**2).diff(n) == \
        2*n*gamma(1 + n**2)*polygamma(0, 1 + n**2)


def test_factorial_series():
    n = Symbol('n', integer=True)

    assert factorial(n).series(n, 0, 3) == \
        1 - n*EulerGamma + n**2*(EulerGamma**2/2 + pi**2/12) + O(n**3)


def test_factorial_rewrite():
    n = Symbol('n', integer=True)
    k = Symbol('k', integer=True, nonnegative=True)

    assert factorial(n).rewrite(gamma) == gamma(n + 1)
    assert str(factorial(k).rewrite(Product)) == 'Product(_i, (_i, 1, k))'


def test_factorial2():
    n = Symbol('n', integer=True)

    assert factorial2(-1) == 1
    assert factorial2(0) == 1
    assert factorial2(7) == 105
    assert factorial2(8) == 384

    # The following is exhaustive
    tt = Symbol('tt', integer=True, nonnegative=True)
    tte = Symbol('tte', even=True, nonnegative=True)
    tpe = Symbol('tpe', even=True, positive=True)
    tto = Symbol('tto', odd=True, nonnegative=True)
    tf = Symbol('tf', integer=True, nonnegative=False)
    tfe = Symbol('tfe', even=True, nonnegative=False)
    tfo = Symbol('tfo', odd=True, nonnegative=False)
    ft = Symbol('ft', integer=False, nonnegative=True)
    ff = Symbol('ff', integer=False, nonnegative=False)
    fn = Symbol('fn', integer=False)
    nt = Symbol('nt', nonnegative=True)
    nf = Symbol('nf', nonnegative=False)
    nn = Symbol('nn')
    #Solves and Fixes Issue #10388 - This is the updated test for the same solved issue
    raises (ValueError, lambda: factorial2(oo))
    raises (ValueError, lambda: factorial2(S(5)/2))
    assert factorial2(n).is_integer is None
    assert factorial2(tt - 1).is_integer
    assert factorial2(tte - 1).is_integer
    assert factorial2(tpe - 3).is_integer
    assert factorial2(tto - 4).is_integer
    assert factorial2(tto - 2).is_integer
    assert factorial2(tf).is_integer is None
    assert factorial2(tfe).is_integer is None
    assert factorial2(tfo).is_integer is None
    assert factorial2(ft).is_integer is None
    assert factorial2(ff).is_integer is None
    assert factorial2(fn).is_integer is None
    assert factorial2(nt).is_integer is None
    assert factorial2(nf).is_integer is None
    assert factorial2(nn).is_integer is None

    assert factorial2(n).is_positive is None
    assert factorial2(tt - 1).is_positive is True
    assert factorial2(tte - 1).is_positive is True
    assert factorial2(tpe - 3).is_positive is True
    assert factorial2(tpe - 1).is_positive is True
    assert factorial2(tto - 2).is_positive is True
    assert factorial2(tto - 1).is_positive is True
    assert factorial2(tf).is_positive is None
    assert factorial2(tfe).is_positive is None
    assert factorial2(tfo).is_positive is None
    assert factorial2(ft).is_positive is None
    assert factorial2(ff).is_positive is None
    assert factorial2(fn).is_positive is None
    assert factorial2(nt).is_positive is None
    assert factorial2(nf).is_positive is None
    assert factorial2(nn).is_positive is None

    assert factorial2(tt).is_even is None
    assert factorial2(tt).is_odd is None
    assert factorial2(tte).is_even is None
    assert factorial2(tte).is_odd is None
    assert factorial2(tte + 2).is_even is True
    assert factorial2(tpe).is_even is True
    assert factorial2(tto).is_odd is True
    assert factorial2(tf).is_even is None
    assert factorial2(tf).is_odd is None
    assert factorial2(tfe).is_even is None
    assert factorial2(tfe).is_odd is None
    assert factorial2(tfo).is_even is False
    assert factorial2(tfo).is_odd is None


def test_factorial2_rewrite():
    n = Symbol('n', integer=True)
    assert factorial2(n).rewrite(gamma) == \
        2**(n/2)*Piecewise((1, Eq(Mod(n, 2), 0)), (sqrt(2)/sqrt(pi), Eq(Mod(n, 2), 1)))*gamma(n/2 + 1)
    assert factorial2(2*n).rewrite(gamma) == 2**n*gamma(n + 1)
    assert factorial2(2*n + 1).rewrite(gamma) == \
        sqrt(2)*2**(n + S(1)/2)*gamma(n + S(3)/2)/sqrt(pi)


def test_binomial():
    x = Symbol('x')
    n = Symbol('n', integer=True)
    nz = Symbol('nz', integer=True, nonzero=True)
    k = Symbol('k', integer=True)
    kp = Symbol('kp', integer=True, positive=True)
    kn = Symbol('kn', integer=True, negative=True)
    u = Symbol('u', negative=True)
    v = Symbol('v', nonnegative=True)
    p = Symbol('p', positive=True)
    z = Symbol('z', zero=True)
    nt = Symbol('nt', integer=False)
    kt = Symbol('kt', integer=False)
    a = Symbol('a', integer=True, nonnegative=True)
    b = Symbol('b', integer=True, nonnegative=True)

    assert binomial(0, 0) == 1
    assert binomial(1, 1) == 1
    assert binomial(10, 10) == 1
    assert binomial(n, z) == 1
    assert binomial(1, 2) == 0
    assert binomial(-1, 2) == 1
    assert binomial(1, -1) == 0
    assert binomial(-1, 1) == -1
    assert binomial(-1, -1) == 0
    assert binomial(S.Half, S.Half) == 1
    assert binomial(-10, 1) == -10
    assert binomial(-10, 7) == -11440
    assert binomial(n, -1) == 0 # holds for all integers (negative, zero, positive)
    assert binomial(kp, -1) == 0
    assert binomial(nz, 0) == 1
    assert expand_func(binomial(n, 1)) == n
    assert expand_func(binomial(n, 2)) == n*(n - 1)/2
    assert expand_func(binomial(n, n - 2)) == n*(n - 1)/2
    assert expand_func(binomial(n, n - 1)) == n
    assert binomial(n, 3).func == binomial
    assert binomial(n, 3).expand(func=True) ==  n**3/6 - n**2/2 + n/3
    assert expand_func(binomial(n, 3)) ==  n*(n - 2)*(n - 1)/6
    assert binomial(n, n).func == binomial # e.g. (-1, -1) == 0, (2, 2) == 1
    assert binomial(n, n + 1).func == binomial  # e.g. (-1, 0) == 1
    assert binomial(kp, kp + 1) == 0
    assert binomial(kn, kn) == 0 # issue #14529
    assert binomial(n, u).func == binomial
    assert binomial(kp, u).func == binomial
    assert binomial(n, p).func == binomial
    assert binomial(n, k).func == binomial
    assert binomial(n, n + p).func == binomial
    assert binomial(kp, kp + p).func == binomial

    assert expand_func(binomial(n, n - 3)) == n*(n - 2)*(n - 1)/6

    assert binomial(n, k).is_integer
    assert binomial(nt, k).is_integer is None
    assert binomial(x, nt).is_integer is False

    assert binomial(gamma(25), 6) == 79232165267303928292058750056084441948572511312165380965440075720159859792344339983120618959044048198214221915637090855535036339620413440000
    assert binomial(1324, 47) == 906266255662694632984994480774946083064699457235920708992926525848438478406790323869952
    assert binomial(1735, 43) == 190910140420204130794758005450919715396159959034348676124678207874195064798202216379800
    assert binomial(2512, 53) == 213894469313832631145798303740098720367984955243020898718979538096223399813295457822575338958939834177325304000
    assert binomial(3383, 52) == 27922807788818096863529701501764372757272890613101645521813434902890007725667814813832027795881839396839287659777235
    assert binomial(4321, 51) == 124595639629264868916081001263541480185227731958274383287107643816863897851139048158022599533438936036467601690983780576

    assert binomial(a, b).is_nonnegative is True
    assert binomial(-1, 2, evaluate=False).is_nonnegative is True
    assert binomial(10, 5, evaluate=False).is_nonnegative is True
    assert binomial(10, -3, evaluate=False).is_nonnegative is True
    assert binomial(-10, -3, evaluate=False).is_nonnegative is True
    assert binomial(-10, 2, evaluate=False).is_nonnegative is True
    assert binomial(-10, 1, evaluate=False).is_nonnegative is False
    assert binomial(-10, 7, evaluate=False).is_nonnegative is False

    # issue #14625
    for _ in (pi, -pi, nt, v, a):
        assert binomial(_, _) == 1
        assert binomial(_, _ - 1) == _
    assert isinstance(binomial(u, u), binomial)
    assert isinstance(binomial(u, u - 1), binomial)
    assert isinstance(binomial(x, x), binomial)
    assert isinstance(binomial(x, x - 1), binomial)

    # issue #13980 and #13981
    assert binomial(-7, -5) == 0
    assert binomial(-23, -12) == 0
    assert binomial(S(13)/2, -10) == 0
    assert binomial(-49, -51) == 0

    assert binomial(19, S(-7)/2) == S(-68719476736)/(911337863661225*pi)
    assert binomial(0, S(3)/2) == S(-2)/(3*pi)
    assert binomial(-3, S(-7)/2) == zoo
    assert binomial(kn, kt) == zoo

    assert binomial(nt, kt).func == binomial
    assert binomial(nt, S(15)/6) == 8*gamma(nt + 1)/(15*sqrt(pi)*gamma(nt - S(3)/2))
    assert binomial(S(20)/3, S(-10)/8) == gamma(S(23)/3)/(gamma(S(-1)/4)*gamma(S(107)/12))
    assert binomial(S(19)/2, S(-7)/2) == S(-1615)/8388608
    assert binomial(S(-13)/5, S(-7)/8) == gamma(S(-8)/5)/(gamma(S(-29)/40)*gamma(S(1)/8))
    assert binomial(S(-19)/8, S(-13)/5) == gamma(S(-11)/8)/(gamma(S(-8)/5)*gamma(S(49)/40))

    # binomial for complexes
    from sympy import I
    assert binomial(I, S(-89)/8) == gamma(1 + I)/(gamma(S(-81)/8)*gamma(S(97)/8 + I))
    assert binomial(I, 2*I) == gamma(1 + I)/(gamma(1 - I)*gamma(1 + 2*I))
    assert binomial(-7, I) == zoo
    assert binomial(-7/S(6), I) == gamma(-1/S(6))/(gamma(-1/S(6) - I)*gamma(1 + I))
    assert binomial((1+2*I), (1+3*I)) == gamma(2 + 2*I)/(gamma(1 - I)*gamma(2 + 3*I))
    assert binomial(I, 5) == S(1)/3 - I/S(12)
    assert binomial((2*I + 3), 7) == -13*I/S(63)
    assert isinstance(binomial(I, n), binomial)


@slow
def test_binomial_Mod():
    p, q = 10**5 + 3, 10**9 + 33 # prime modulo
    r, s = 10**7 + 5, 33333333 # composite modulo

    n, k, m = symbols('n k m')
    assert (binomial(n, k) % q).subs({n: s, k: p}) == Mod(binomial(s, p), q)
    assert (binomial(n, k) % m).subs({n: 8, k: 5, m: 13}) == 4
    assert (binomial(9, k) % 7).subs(k, 2) == 1

    # Lucas Theorem
    assert Mod(binomial(156675, 4433, evaluate=False), p) == Mod(binomial(156675, 4433), p)
    assert Mod(binomial(123456, 43253, evaluate=False), p) == Mod(binomial(123456, 43253), p)
    assert Mod(binomial(-178911, 237, evaluate=False), p) == Mod(-binomial(178911 + 237 - 1, 237), p)
    assert Mod(binomial(-178911, 238, evaluate=False), p) == Mod(binomial(178911 + 238 - 1, 238), p)

    # factorial Mod
    assert Mod(binomial(1234, 432, evaluate=False), q) == Mod(binomial(1234, 432), q)
    assert Mod(binomial(9734, 451, evaluate=False), q) == Mod(binomial(9734, 451), q)
    assert Mod(binomial(-10733, 4459, evaluate=False), q) == Mod(binomial(-10733, 4459), q)
    assert Mod(binomial(-15733, 4458, evaluate=False), q) == Mod(binomial(-15733, 4458), q)

    # binomial factorize
    assert Mod(binomial(253, 113, evaluate=False), r) == Mod(binomial(253, 113), r)
    assert Mod(binomial(753, 119, evaluate=False), r) == Mod(binomial(753, 119), r)
    assert Mod(binomial(3781, 948, evaluate=False), s) == Mod(binomial(3781, 948), s)
    assert Mod(binomial(25773, 1793, evaluate=False), s) == Mod(binomial(25773, 1793), s)
    assert Mod(binomial(-753, 118, evaluate=False), r) == Mod(binomial(-753, 118), r)
    assert Mod(binomial(-25773, 1793, evaluate=False), s) == Mod(binomial(-25773, 1793), s)


def test_binomial_diff():
    n = Symbol('n', integer=True)
    k = Symbol('k', integer=True)

    assert binomial(n, k).diff(n) == \
        (-polygamma(0, 1 + n - k) + polygamma(0, 1 + n))*binomial(n, k)
    assert binomial(n**2, k**3).diff(n) == \
        2*n*(-polygamma(
            0, 1 + n**2 - k**3) + polygamma(0, 1 + n**2))*binomial(n**2, k**3)

    assert binomial(n, k).diff(k) == \
        (-polygamma(0, 1 + k) + polygamma(0, 1 + n - k))*binomial(n, k)
    assert binomial(n**2, k**3).diff(k) == \
        3*k**2*(-polygamma(
            0, 1 + k**3) + polygamma(0, 1 + n**2 - k**3))*binomial(n**2, k**3)


def test_binomial_rewrite():
    n = Symbol('n', integer=True)
    k = Symbol('k', integer=True)

    assert binomial(n, k).rewrite(
        factorial) == factorial(n)/(factorial(k)*factorial(n - k))
    assert binomial(
        n, k).rewrite(gamma) == gamma(n + 1)/(gamma(k + 1)*gamma(n - k + 1))
    assert binomial(n, k).rewrite(ff) == ff(n, k) / factorial(k)


@XFAIL
def test_factorial_simplify_fail():
    # simplify(factorial(x + 1).diff(x) - ((x + 1)*factorial(x)).diff(x))) == 0
    from sympy.abc import x
    assert simplify(x*polygamma(0, x + 1) - x*polygamma(0, x + 2) +
    polygamma(0, x + 1) - polygamma(0, x + 2) + 1) == 0


def test_subfactorial():
    assert all(subfactorial(i) == ans for i, ans in enumerate(
        [1, 0, 1, 2, 9, 44, 265, 1854, 14833, 133496]))
    assert subfactorial(oo) == oo
    assert subfactorial(nan) == nan

    x = Symbol('x')
    assert subfactorial(x).rewrite(uppergamma) == uppergamma(x + 1, -1)/S.Exp1

    tt = Symbol('tt', integer=True, nonnegative=True)
    tf = Symbol('tf', integer=True, nonnegative=False)
    tn = Symbol('tf', integer=True)
    ft = Symbol('ft', integer=False, nonnegative=True)
    ff = Symbol('ff', integer=False, nonnegative=False)
    fn = Symbol('ff', integer=False)
    nt = Symbol('nt', nonnegative=True)
    nf = Symbol('nf', nonnegative=False)
    nn = Symbol('nf')
    te = Symbol('te', even=True, nonnegative=True)
    to = Symbol('to', odd=True, nonnegative=True)
    assert subfactorial(tt).is_integer
    assert subfactorial(tf).is_integer is None
    assert subfactorial(tn).is_integer is None
    assert subfactorial(ft).is_integer is None
    assert subfactorial(ff).is_integer is None
    assert subfactorial(fn).is_integer is None
    assert subfactorial(nt).is_integer is None
    assert subfactorial(nf).is_integer is None
    assert subfactorial(nn).is_integer is None
    assert subfactorial(tt).is_nonnegative
    assert subfactorial(tf).is_nonnegative is None
    assert subfactorial(tn).is_nonnegative is None
    assert subfactorial(ft).is_nonnegative is None
    assert subfactorial(ff).is_nonnegative is None
    assert subfactorial(fn).is_nonnegative is None
    assert subfactorial(nt).is_nonnegative is None
    assert subfactorial(nf).is_nonnegative is None
    assert subfactorial(nn).is_nonnegative is None
    assert subfactorial(tt).is_even is None
    assert subfactorial(tt).is_odd is None
    assert subfactorial(te).is_odd is True
    assert subfactorial(to).is_even is True
