from sympy import symbols, Mul, sin, Integral, oo, Eq, Sum
from sympy.stats import Normal, Poisson, variance
from sympy.stats.rv import probability, expectation
from sympy.stats import Covariance, Variance, Probability, Expectation


def test_literal_probability():
    X = Normal('X', 2, 3)
    Y = Normal('Y', 3, 4)
    Z = Poisson('Z', 4)
    W = Poisson('W', 3)
    x = symbols('x', real=True)
    y, w, z = symbols('y, w, z')

    assert Probability(X > 0).evaluate_integral() == probability(X > 0)
    assert Probability(X > x).evaluate_integral() == probability(X > x)
    assert Probability(X > 0).rewrite(Integral).doit() == probability(X > 0)
    assert Probability(X > x).rewrite(Integral).doit() == probability(X > x)

    assert Expectation(X).evaluate_integral() == expectation(X)
    assert Expectation(X).rewrite(Integral).doit() == expectation(X)
    assert Expectation(X**2).evaluate_integral() == expectation(X**2)
    assert Expectation(x*X).args == (x*X,)
    assert Expectation(x*X).doit() == x*Expectation(X)
    assert Expectation(2*X + 3*Y + z*X*Y).doit() == 2*Expectation(X) + 3*Expectation(Y) + z*Expectation(X*Y)
    assert Expectation(2*X + 3*Y + z*X*Y).args == (2*X + 3*Y + z*X*Y,)
    assert Expectation(sin(X)) == Expectation(sin(X)).doit()
    assert Expectation(2*x*sin(X)*Y + y*X**2 + z*X*Y).doit() == 2*x*Expectation(sin(X)*Y) + y*Expectation(X**2) + z*Expectation(X*Y)

    assert Variance(w).args == (w,)
    assert Variance(w).doit() == 0
    assert Variance(X).evaluate_integral() == Variance(X).rewrite(Integral).doit() == variance(X)
    assert Variance(X + z).args == (X + z,)
    assert Variance(X + z).doit() == Variance(X)
    assert Variance(X*Y).args == (Mul(X, Y),)
    assert type(Variance(X*Y)) == Variance
    assert Variance(z*X).doit() == z**2*Variance(X)
    assert Variance(X + Y).doit() == Variance(X) + Variance(Y) + 2*Covariance(X, Y)
    assert Variance(X + Y + Z + W).doit() == (Variance(X) + Variance(Y) + Variance(Z) + Variance(W) +
                                       2 * Covariance(X, Y) + 2 * Covariance(X, Z) + 2 * Covariance(X, W) +
                                       2 * Covariance(Y, Z) + 2 * Covariance(Y, W) + 2 * Covariance(W, Z))
    assert Variance(X**2).evaluate_integral() == variance(X**2)
    assert Variance(X**2) == Variance(X**2)
    assert Variance(x*X**2).doit() == x**2*Variance(X**2)
    assert Variance(sin(X)).args == (sin(X),)
    assert Variance(sin(X)).doit() == Variance(sin(X))
    assert Variance(x*sin(X)).doit() == x**2*Variance(sin(X))

    assert Covariance(w, z).args == (w, z)
    assert Covariance(w, z).doit() == 0
    assert Covariance(X, w).doit() == 0
    assert Covariance(w, X).doit() == 0
    assert Covariance(X, Y).args == (X, Y)
    assert type(Covariance(X, Y)) == Covariance
    assert Covariance(z*X + 3, Y).doit() == z*Covariance(X, Y)
    assert Covariance(X, X).args == (X, X)
    assert Covariance(X, X).doit() == Variance(X)
    assert Covariance(z*X + 3, w*Y + 4).doit() == w*z*Covariance(X,Y)
    assert Covariance(X, Y) == Covariance(Y, X)
    assert Covariance(X + Y, Z + W).doit() == Covariance(W, X) + Covariance(W, Y) + Covariance(X, Z) + Covariance(Y, Z)
    assert Covariance(x*X + y*Y, z*Z + w*W).doit() == (x*w*Covariance(W, X) + w*y*Covariance(W, Y) +
                                                x*z*Covariance(X, Z) + y*z*Covariance(Y, Z))
    assert Covariance(x*X**2 + y*sin(Y), z*Y*Z**2 + w*W).doit() == (w*x*Covariance(W, X**2) + w*y*Covariance(sin(Y), W) +
                                                        x*z*Covariance(Y*Z**2, X**2) + y*z*Covariance(Y*Z**2, sin(Y)))
    assert Covariance(X, X**2).doit() == Covariance(X, X**2)
    assert Covariance(X, sin(X)).doit() == Covariance(sin(X), X)
    assert Covariance(X**2, sin(X)*Y).doit() == Covariance(sin(X)*Y, X**2)


def test_probability_rewrite():
    X = Normal('X', 2, 3)
    Y = Normal('Y', 3, 4)
    Z = Poisson('Z', 4)
    W = Poisson('W', 3)
    x, y, w, z = symbols('x, y, w, z')

    assert Variance(w).rewrite(Expectation) == 0
    assert Variance(X).rewrite(Expectation) == Expectation(X ** 2) - Expectation(X) ** 2
    assert Variance(X, condition=Y).rewrite(Expectation) == Expectation(X ** 2, Y) - Expectation(X, Y) ** 2
    assert Variance(X, Y) != Expectation(X**2) - Expectation(X)**2
    assert Variance(X + z).rewrite(Expectation) == Expectation((X + z) ** 2) - Expectation(X + z) ** 2
    assert Variance(X * Y).rewrite(Expectation) == Expectation(X ** 2 * Y ** 2) - Expectation(X * Y) ** 2

    assert Covariance(w, X).rewrite(Expectation) == -w*Expectation(X) + Expectation(w*X)
    assert Covariance(X, Y).rewrite(Expectation) == Expectation(X*Y) - Expectation(X)*Expectation(Y)
    assert Covariance(X, Y, condition=W).rewrite(Expectation) == Expectation(X * Y, W) - Expectation(X, W) * Expectation(Y, W)

    w, x, z = symbols("W, x, z")
    px = Probability(Eq(X, x))
    pz = Probability(Eq(Z, z))

    assert Expectation(X).rewrite(Probability) == Integral(x*px, (x, -oo, oo))
    assert Expectation(Z).rewrite(Probability) == Sum(z*pz, (z, 0, oo))
    assert Variance(X).rewrite(Probability) == Integral(x**2*px, (x, -oo, oo)) - Integral(x*px, (x, -oo, oo))**2
    assert Variance(Z).rewrite(Probability) == Sum(z**2*pz, (z, 0, oo)) - Sum(z*pz, (z, 0, oo))**2

    assert Variance(X, condition=Y).rewrite(Probability) == Integral(x**2*Probability(Eq(X, x), Y), (x, -oo, oo)) - \
                                                            Integral(x*Probability(Eq(X, x), Y), (x, -oo, oo))**2
