from sympy import S, Sum, I, lambdify, re, im, log, simplify, zeta, pi
from sympy.abc import x
from sympy.core.relational import Eq, Ne
from sympy.functions.elementary.exponential import exp
from sympy.logic.boolalg import Or
from sympy.sets.fancysets import Range
from sympy.stats import (P, E, variance, density, characteristic_function,
        where, moment_generating_function)
from sympy.stats.drv_types import (PoissonDistribution, GeometricDistribution,
        Poisson, Geometric, Logarithmic, NegativeBinomial, YuleSimon, Zeta)
from sympy.stats.rv import sample
from sympy.utilities.pytest import slow

def test_PoissonDistribution():
    l = 3
    p = PoissonDistribution(l)
    assert abs(p.cdf(10).evalf() - 1) < .001
    assert p.expectation(x, x) == l
    assert p.expectation(x**2, x) - p.expectation(x, x)**2 == l

def test_Poisson():
    l = 3
    x = Poisson('x', l)
    assert E(x) == l
    assert variance(x) == l
    assert density(x) == PoissonDistribution(l)
    assert isinstance(E(x, evaluate=False), Sum)
    assert isinstance(E(2*x, evaluate=False), Sum)

def test_GeometricDistribution():
    p = S.One / 5
    d = GeometricDistribution(p)
    assert d.expectation(x, x) == 1/p
    assert d.expectation(x**2, x) - d.expectation(x, x)**2 == (1-p)/p**2
    assert abs(d.cdf(20000).evalf() - 1) < .001

def test_Logarithmic():
    p = S.One / 2
    x = Logarithmic('x', p)
    assert E(x) == -p / ((1 - p) * log(1 - p))
    assert variance(x) == -1/log(2)**2 + 2/log(2)
    assert E(2*x**2 + 3*x + 4) == 4 + 7 / log(2)
    assert isinstance(E(x, evaluate=False), Sum)

def test_negative_binomial():
    r = 5
    p = S(1) / 3
    x = NegativeBinomial('x', r, p)
    assert E(x) == p*r / (1-p)
    assert variance(x) == p*r / (1-p)**2
    assert E(x**5 + 2*x + 3) == S(9207)/4
    assert isinstance(E(x, evaluate=False), Sum)

def test_yule_simon():
    rho = S(3)
    x = YuleSimon('x', rho)
    assert simplify(E(x)) == rho / (rho - 1)
    assert simplify(variance(x)) == rho**2 / ((rho - 1)**2 * (rho - 2))
    assert isinstance(E(x, evaluate=False), Sum)

def test_zeta():
    s = S(5)
    x = Zeta('x', s)
    assert E(x) == zeta(s-1) / zeta(s)
    assert simplify(variance(x)) == (zeta(s) * zeta(s-2) - zeta(s-1)**2) / zeta(s)**2


@slow
def test_sample_discrete():
    X, Y, Z = Geometric('X', S(1)/2), Poisson('Y', 4), Poisson('Z', 1000)
    W = Poisson('W', S(1)/100)
    assert sample(X) in X.pspace.domain.set
    assert sample(Y) in Y.pspace.domain.set
    assert sample(Z) in Z.pspace.domain.set
    assert sample(W) in W.pspace.domain.set

def test_discrete_probability():
    X = Geometric('X', S(1)/5)
    Y = Poisson('Y', 4)
    G = Geometric('e', x)
    assert P(Eq(X, 3)) == S(16)/125
    assert P(X < 3) == S(9)/25
    assert P(X > 3) == S(64)/125
    assert P(X >= 3) == S(16)/25
    assert P(X <= 3) == S(61)/125
    assert P(Ne(X, 3)) == S(109)/125
    assert P(Eq(Y, 3)) == 32*exp(-4)/3
    assert P(Y < 3) == 13*exp(-4)
    assert P(Y > 3).equals(32*(-S(71)/32 + 3*exp(4)/32)*exp(-4)/3)
    assert P(Y >= 3).equals(32*(-S(39)/32 + 3*exp(4)/32)*exp(-4)/3)
    assert P(Y <= 3) == 71*exp(-4)/3
    assert P(Ne(Y, 3)).equals(
        13*exp(-4) + 32*(-S(71)/32 + 3*exp(4)/32)*exp(-4)/3)
    assert P(X < S.Infinity) is S.One
    assert P(X > S.Infinity) is S.Zero
    assert P(G < 3) == x*(-x + 1) + x
    assert P(Eq(G, 3)) == x*(-x + 1)**2

def test_precomputed_characteristic_functions():
    import mpmath

    def test_cf(dist, support_lower_limit, support_upper_limit):
        pdf = density(dist)
        t = S('t')
        x = S('x')

        # first function is the hardcoded CF of the distribution
        cf1 = lambdify([t], characteristic_function(dist)(t), 'mpmath')

        # second function is the Fourier transform of the density function
        f = lambdify([x, t], pdf(x)*exp(I*x*t), 'mpmath')
        cf2 = lambda t: mpmath.nsum(lambda x: f(x, t), [support_lower_limit, support_upper_limit], maxdegree=10)

        # compare the two functions at various points
        for test_point in [2, 5, 8, 11]:
            n1 = cf1(test_point)
            n2 = cf2(test_point)

            assert abs(re(n1) - re(n2)) < 1e-12
            assert abs(im(n1) - im(n2)) < 1e-12

    test_cf(Geometric('g', S(1)/3), 1, mpmath.inf)
    test_cf(Logarithmic('l', S(1)/5), 1, mpmath.inf)
    test_cf(NegativeBinomial('n', 5, S(1)/7), 0, mpmath.inf)
    test_cf(Poisson('p', 5), 0, mpmath.inf)
    test_cf(YuleSimon('y', 5), 1, mpmath.inf)
    test_cf(Zeta('z', 5), 1, mpmath.inf)

def test_moment_generating_functions():
    t = S('t')

    geometric_mgf = moment_generating_function(Geometric('g', S(1)/2))(t)
    assert geometric_mgf.diff(t).subs(t, 0) == 2

    logarithmic_mgf = moment_generating_function(Logarithmic('l', S(1)/2))(t)
    assert logarithmic_mgf.diff(t).subs(t, 0) == 1/log(2)

    negative_binomial_mgf = moment_generating_function(NegativeBinomial('n', 5, S(1)/3))(t)
    assert negative_binomial_mgf.diff(t).subs(t, 0) == S(5)/2

    poisson_mgf = moment_generating_function(Poisson('p', 5))(t)
    assert poisson_mgf.diff(t).subs(t, 0) == 5

    yule_simon_mgf = moment_generating_function(YuleSimon('y', 3))(t)
    assert simplify(yule_simon_mgf.diff(t).subs(t, 0)) == S(3)/2

    zeta_mgf = moment_generating_function(Zeta('z', 5))(t)
    assert zeta_mgf.diff(t).subs(t, 0) == pi**4/(90*zeta(5))

def test_Or():
    X = Geometric('X', S(1)/2)
    P(Or(X < 3, X > 4)) == S(13)/16
    P(Or(X > 2, X > 1)) == P(X > 1)
    P(Or(X >= 3, X < 3)) == 1

def test_where():
    X = Geometric('X', S(1)/5)
    Y = Poisson('Y', 4)
    assert where(X**2 > 4).set == Range(3, S.Infinity, 1)
    assert where(X**2 >= 4).set == Range(2, S.Infinity, 1)
    assert where(Y**2 < 9).set == Range(0, 3, 1)
    assert where(Y**2 <= 9).set == Range(0, 4, 1)

def test_conditional():
    X = Geometric('X', S(2)/3)
    Y = Poisson('Y', 3)
    assert P(X > 2, X > 3) == 1
    assert P(X > 3, X > 2) == S(1)/3
    assert P(Y > 2, Y < 2) == 0
    assert P(Eq(Y, 3), Y >= 0) == 9*exp(-3)/2
    assert P(Eq(Y, 3), Eq(Y, 2)) == 0
    assert P(X < 2, Eq(X, 2)) == 0
    assert P(X > 2, Eq(X, 3)) == 1

def test_product_spaces():
    X1 = Geometric('X1', S(1)/2)
    X2 = Geometric('X2', S(1)/3)
    assert str(P(X1 + X2 < 3, evaluate=False)) == """Sum(Piecewise((2**(X2 - n - 2)*(2/3)**(X2 - 1)/6, """\
    + """(-X2 + n + 3 >= 1) & (-X2 + n + 3 < oo)), (0, True)), (X2, 1, oo), (n, -oo, -1))"""
    assert str(P(X1 + X2 > 3)) == """Sum(Piecewise((2**(X2 - n - 2)*(2/3)**(X2 - 1)/6, """ +\
        """(-X2 + n + 3 >= 1) & (-X2 + n + 3 < oo)), (0, True)), (X2, 1, oo), (n, 1, oo))"""
    assert str(P(Eq(X1 + X2, 3))) == """Sum(Piecewise((2**(X2 - 2)*(2/3)**(X2 - 1)/6, """ +\
    """X2 <= 2), (0, True)), (X2, 1, oo))"""
