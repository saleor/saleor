from sympy import (FiniteSet, S, Symbol, sqrt,
        symbols, simplify, Eq, cos, And, Tuple, Or, Dict, sympify, binomial,
        cancel, exp, I)
from sympy.core.compatibility import range
from sympy.matrices import Matrix
from sympy.stats import (DiscreteUniform, Die, Bernoulli, Coin, Binomial,
    Hypergeometric, Rademacher, P, E, variance, covariance, skewness, sample,
    density, where, FiniteRV, pspace, cdf,
    correlation, moment, cmoment, smoment, characteristic_function, moment_generating_function)
from sympy.stats.frv_types import DieDistribution
from sympy.utilities.pytest import raises

oo = S.Infinity


def BayesTest(A, B):
    assert P(A, B) == P(And(A, B)) / P(B)
    assert P(A, B) == P(B, A) * P(A) / P(B)


def test_discreteuniform():
    # Symbolic
    a, b, c, t = symbols('a b c t')
    X = DiscreteUniform('X', [a, b, c])

    assert E(X) == (a + b + c)/3
    assert simplify(variance(X)
                    - ((a**2 + b**2 + c**2)/3 - (a/3 + b/3 + c/3)**2)) == 0
    assert P(Eq(X, a)) == P(Eq(X, b)) == P(Eq(X, c)) == S('1/3')

    Y = DiscreteUniform('Y', range(-5, 5))

    # Numeric
    assert E(Y) == S('-1/2')
    assert variance(Y) == S('33/4')

    for x in range(-5, 5):
        assert P(Eq(Y, x)) == S('1/10')
        assert P(Y <= x) == S(x + 6)/10
        assert P(Y >= x) == S(5 - x)/10

    assert dict(density(Die('D', 6)).items()) == \
           dict(density(DiscreteUniform('U', range(1, 7))).items())

    assert characteristic_function(X)(t) == exp(I*a*t)/3 + exp(I*b*t)/3 + exp(I*c*t)/3
    assert moment_generating_function(X)(t) == exp(a*t)/3 + exp(b*t)/3 + exp(c*t)/3

def test_dice():
    # TODO: Make iid method!
    X, Y, Z = Die('X', 6), Die('Y', 6), Die('Z', 6)
    a, b, t = symbols('a b t')

    assert E(X) == 3 + S.Half
    assert variance(X) == S(35)/12
    assert E(X + Y) == 7
    assert E(X + X) == 7
    assert E(a*X + b) == a*E(X) + b
    assert variance(X + Y) == variance(X) + variance(Y) == cmoment(X + Y, 2)
    assert variance(X + X) == 4 * variance(X) == cmoment(X + X, 2)
    assert cmoment(X, 0) == 1
    assert cmoment(4*X, 3) == 64*cmoment(X, 3)
    assert covariance(X, Y) == S.Zero
    assert covariance(X, X + Y) == variance(X)
    assert density(Eq(cos(X*S.Pi), 1))[True] == S.Half
    assert correlation(X, Y) == 0
    assert correlation(X, Y) == correlation(Y, X)
    assert smoment(X + Y, 3) == skewness(X + Y)
    assert smoment(X, 0) == 1
    assert P(X > 3) == S.Half
    assert P(2*X > 6) == S.Half
    assert P(X > Y) == S(5)/12
    assert P(Eq(X, Y)) == P(Eq(X, 1))

    assert E(X, X > 3) == 5 == moment(X, 1, 0, X > 3)
    assert E(X, Y > 3) == E(X) == moment(X, 1, 0, Y > 3)
    assert E(X + Y, Eq(X, Y)) == E(2*X)
    assert moment(X, 0) == 1
    assert moment(5*X, 2) == 25*moment(X, 2)

    assert P(X > 3, X > 3) == S.One
    assert P(X > Y, Eq(Y, 6)) == S.Zero
    assert P(Eq(X + Y, 12)) == S.One/36
    assert P(Eq(X + Y, 12), Eq(X, 6)) == S.One/6

    assert density(X + Y) == density(Y + Z) != density(X + X)
    d = density(2*X + Y**Z)
    assert d[S(22)] == S.One/108 and d[S(4100)] == S.One/216 and S(3130) not in d

    assert pspace(X).domain.as_boolean() == Or(
        *[Eq(X.symbol, i) for i in [1, 2, 3, 4, 5, 6]])

    assert where(X > 3).set == FiniteSet(4, 5, 6)

    assert characteristic_function(X)(t) == exp(6*I*t)/6 + exp(5*I*t)/6 + exp(4*I*t)/6 + exp(3*I*t)/6 + exp(2*I*t)/6 + exp(I*t)/6
    assert moment_generating_function(X)(t) == exp(6*t)/6 + exp(5*t)/6 + exp(4*t)/6 + exp(3*t)/6 + exp(2*t)/6 + exp(t)/6


def test_given():
    X = Die('X', 6)
    assert density(X, X > 5) == {S(6): S(1)}
    assert where(X > 2, X > 5).as_boolean() == Eq(X.symbol, 6)
    assert sample(X, X > 5) == 6


def test_domains():
    X, Y = Die('x', 6), Die('y', 6)
    x, y = X.symbol, Y.symbol
    # Domains
    d = where(X > Y)
    assert d.condition == (x > y)
    d = where(And(X > Y, Y > 3))
    assert d.as_boolean() == Or(And(Eq(x, 5), Eq(y, 4)), And(Eq(x, 6),
        Eq(y, 5)), And(Eq(x, 6), Eq(y, 4)))
    assert len(d.elements) == 3

    assert len(pspace(X + Y).domain.elements) == 36

    Z = Die('x', 4)

    raises(ValueError, lambda: P(X > Z))  # Two domains with same internal symbol

    assert pspace(X + Y).domain.set == FiniteSet(1, 2, 3, 4, 5, 6)**2

    assert where(X > 3).set == FiniteSet(4, 5, 6)
    assert X.pspace.domain.dict == FiniteSet(
        *[Dict({X.symbol: i}) for i in range(1, 7)])

    assert where(X > Y).dict == FiniteSet(*[Dict({X.symbol: i, Y.symbol: j})
            for i in range(1, 7) for j in range(1, 7) if i > j])


def test_dice_bayes():
    X, Y, Z = Die('X', 6), Die('Y', 6), Die('Z', 6)

    BayesTest(X > 3, X + Y < 5)
    BayesTest(Eq(X - Y, Z), Z > Y)
    BayesTest(X > 3, X > 2)


def test_die_args():
    raises(ValueError, lambda: Die('X', -1))  # issue 8105: negative sides.
    raises(ValueError, lambda: Die('X', 0))
    raises(ValueError, lambda: Die('X', 1.5))  # issue 8103: non integer sides.

    k = Symbol('k')
    sym_die = Die('X', k)
    raises(ValueError, lambda: density(sym_die).dict)


def test_bernoulli():
    p, a, b, t = symbols('p a b t')
    X = Bernoulli('B', p, a, b)

    assert E(X) == a*p + b*(-p + 1)
    assert density(X)[a] == p
    assert density(X)[b] == 1 - p
    assert characteristic_function(X)(t) == p * exp(I * a * t) + (-p + 1) * exp(I * b * t)
    assert moment_generating_function(X)(t) == p * exp(a * t) + (-p + 1) * exp(b * t)

    X = Bernoulli('B', p, 1, 0)

    assert E(X) == p
    assert simplify(variance(X)) == p*(1 - p)
    assert E(a*X + b) == a*E(X) + b
    assert simplify(variance(a*X + b)) == simplify(a**2 * variance(X))

    raises(ValueError, lambda: Bernoulli('B', 1.5))
    raises(ValueError, lambda: Bernoulli('B', -0.5))

def test_cdf():
    D = Die('D', 6)
    o = S.One

    assert cdf(
        D) == sympify({1: o/6, 2: o/3, 3: o/2, 4: 2*o/3, 5: 5*o/6, 6: o})


def test_coins():
    C, D = Coin('C'), Coin('D')
    H, T = symbols('H, T')
    assert P(Eq(C, D)) == S.Half
    assert density(Tuple(C, D)) == {(H, H): S.One/4, (H, T): S.One/4,
            (T, H): S.One/4, (T, T): S.One/4}
    assert dict(density(C).items()) == {H: S.Half, T: S.Half}

    F = Coin('F', S.One/10)
    assert P(Eq(F, H)) == S(1)/10

    d = pspace(C).domain

    assert d.as_boolean() == Or(Eq(C.symbol, H), Eq(C.symbol, T))

    raises(ValueError, lambda: P(C > D))  # Can't intelligently compare H to T

def test_binomial_verify_parameters():
    raises(ValueError, lambda: Binomial('b', .2, .5))
    raises(ValueError, lambda: Binomial('b', 3, 1.5))

def test_binomial_numeric():
    nvals = range(5)
    pvals = [0, S(1)/4, S.Half, S(3)/4, 1]

    for n in nvals:
        for p in pvals:
            X = Binomial('X', n, p)
            assert E(X) == n*p
            assert variance(X) == n*p*(1 - p)
            if n > 0 and 0 < p < 1:
                assert skewness(X) == (1 - 2*p)/sqrt(n*p*(1 - p))
            for k in range(n + 1):
                assert P(Eq(X, k)) == binomial(n, k)*p**k*(1 - p)**(n - k)


def test_binomial_symbolic():
    n = 2  # Because we're using for loops, can't do symbolic n
    p = symbols('p', positive=True)
    X = Binomial('X', n, p)
    t = Symbol('t')

    assert simplify(E(X)) == n*p == simplify(moment(X, 1))
    assert simplify(variance(X)) == n*p*(1 - p) == simplify(cmoment(X, 2))
    assert cancel((skewness(X) - (1 - 2*p)/sqrt(n*p*(1 - p)))) == 0
    assert characteristic_function(X)(t) == p ** 2 * exp(2 * I * t) + 2 * p * (-p + 1) * exp(I * t) + (-p + 1) ** 2
    assert moment_generating_function(X)(t) == p ** 2 * exp(2 * t) + 2 * p * (-p + 1) * exp(t) + (-p + 1) ** 2

    # Test ability to change success/failure winnings
    H, T = symbols('H T')
    Y = Binomial('Y', n, p, succ=H, fail=T)
    assert simplify(E(Y) - (n*(H*p + T*(1 - p)))) == 0


def test_hypergeometric_numeric():
    for N in range(1, 5):
        for m in range(0, N + 1):
            for n in range(1, N + 1):
                X = Hypergeometric('X', N, m, n)
                N, m, n = map(sympify, (N, m, n))
                assert sum(density(X).values()) == 1
                assert E(X) == n * m / N
                if N > 1:
                    assert variance(X) == n*(m/N)*(N - m)/N*(N - n)/(N - 1)
                # Only test for skewness when defined
                if N > 2 and 0 < m < N and n < N:
                    assert skewness(X) == simplify((N - 2*m)*sqrt(N - 1)*(N - 2*n)
                        / (sqrt(n*m*(N - m)*(N - n))*(N - 2)))


def test_rademacher():
    X = Rademacher('X')
    t = Symbol('t')

    assert E(X) == 0
    assert variance(X) == 1
    assert density(X)[-1] == S.Half
    assert density(X)[1] == S.Half
    assert characteristic_function(X)(t) == exp(I*t)/2 + exp(-I*t)/2
    assert moment_generating_function(X)(t) == exp(t) / 2 + exp(-t) / 2


def test_FiniteRV():
    F = FiniteRV('F', {1: S.Half, 2: S.One/4, 3: S.One/4})

    assert dict(density(F).items()) == {S(1): S.Half, S(2): S.One/4, S(3): S.One/4}
    assert P(F >= 2) == S.Half

    assert pspace(F).domain.as_boolean() == Or(
        *[Eq(F.symbol, i) for i in [1, 2, 3]])

    raises(ValueError, lambda: FiniteRV('F', {1: S.Half, 2: S.Half, 3: S.Half}))
    raises(ValueError, lambda: FiniteRV('F', {1: S.Half, 2: S(-1)/2, 3: S.One}))
    raises(ValueError, lambda: FiniteRV('F', {1: S.One, 2: S(3)/2, 3: S.Zero, 4: S(-1)/2, 5: S(-3)/4, 6: S(-1)/4}))

def test_density_call():
    from sympy.abc import p
    x = Bernoulli('x', p)
    d = density(x)
    assert d(0) == 1 - p
    assert d(S.Zero) == 1 - p
    assert d(5) == 0

    assert 0 in d
    assert 5 not in d
    assert d(S(0)) == d[S(0)]


def test_DieDistribution():
    from sympy.abc import x
    X = DieDistribution(6)
    assert X.pdf(S(1)/2) == S.Zero
    assert X.pdf(x).subs({x: 1}).doit() == S(1)/6
    assert X.pdf(x).subs({x: 7}).doit() == 0
    assert X.pdf(x).subs({x: -1}).doit() == 0
    assert X.pdf(x).subs({x: S(1)/3}).doit() == 0
    raises(TypeError, lambda: X.pdf(x).subs({x: Matrix([0, 0])}))
    raises(ValueError, lambda: X.pdf(x**2 - 1))

def test_FinitePSpace():
    X = Die('X', 6)
    space = pspace(X)
    assert space.density == DieDistribution(6)
