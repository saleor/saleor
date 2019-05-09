# A collection of failing integrals from the issues.

from sympy import (
    integrate, Integral, exp, oo, pi, sign, sqrt, sin, cos,
    tan, S, log, gamma, sinh,
)

from sympy.utilities.pytest import XFAIL, SKIP, slow, skip, ON_TRAVIS

from sympy.abc import x, k, c, y, R, b, h, a, m


@SKIP("Too slow for @slow")
@XFAIL
def test_issue_3880():
    # integrate_hyperexponential(Poly(t*2*(1 - t0**2)*t0*(x**3 + x**2), t), Poly((1 + t0**2)**2*2*(x**2 + x + 1), t), [Poly(1, x), Poly(1 + t0**2, t0), Poly(t, t)], [x, t0, t], [exp, tan])
    assert not integrate(exp(x)*cos(2*x)*sin(2*x) * (x**3 + x**2)/(2*(x**2 + x + 1)), x).has(Integral)


@XFAIL
def test_issue_4212():
    assert not integrate(sign(x), x).has(Integral)


@XFAIL
def test_issue_4326():
    assert integrate(((h*(x - R + b))/b)*sqrt(R**2 - x**2), (x, R - b, R)).has(Integral)


@XFAIL
def test_issue_4491():
    assert not integrate(x*sqrt(x**2 + 2*x + 4), x).has(Integral)


@XFAIL
def test_issue_4511():
    # This works, but gives a complicated answer.  The correct answer is x - cos(x).
    # The last one is what Maple gives.  It is also quite slow.
    assert integrate(cos(x)**2 / (1 - sin(x))) in [x - cos(x), 1 - cos(x) + x,
            -2/(tan((S(1)/2)*x)**2 + 1) + x]


@XFAIL
def test_issue_4525():
    # Warning: takes a long time
    assert not integrate((x**m * (1 - x)**n * (a + b*x + c*x**2))/(1 + x**2), (x, 0, 1)).has(Integral)



@XFAIL
@slow
def test_issue_4540():
    if ON_TRAVIS:
        skip("Too slow for travis.")
    # Note, this integral is probably nonelementary
    assert not integrate(
        (sin(1/x) - x*exp(x)) /
        ((-sin(1/x) + x*exp(x))*x + x*sin(1/x)), x).has(Integral)


@XFAIL
def test_issue_4551():
    assert integrate(1/(x*sqrt(1 - x**2)), x).has(Integral)


@XFAIL
def test_issue_4737a():
    # Implementation of Si()
    assert integrate(sin(x)/x, x).has(Integral)


@XFAIL
def test_issue_1638b():
    assert integrate(sin(x)/x, (x, -oo, oo)) == pi/2


@XFAIL
@slow
def test_issue_4891():
    # Requires the hypergeometric function.
    assert not integrate(cos(x)**y, x).has(Integral)


@XFAIL
@slow
def test_issue_1796a():
    assert not integrate(exp(2*b*x)*exp(-a*x**2), x).has(Integral)


@XFAIL
def test_issue_4895b():
    assert not integrate(exp(2*b*x)*exp(-a*x**2), (x, -oo, 0)).has(Integral)


@XFAIL
def test_issue_4895c():
    assert not integrate(exp(2*b*x)*exp(-a*x**2), (x, -oo, oo)).has(Integral)


@XFAIL
def test_issue_4895d():
    assert not integrate(exp(2*b*x)*exp(-a*x**2), (x, 0, oo)).has(Integral)


@XFAIL
@slow
def test_issue_4941():
    if ON_TRAVIS:
        skip("Too slow for travis.")
    assert not integrate(sqrt(1 + sinh(x/20)**2), (x, -25, 25)).has(Integral)


@XFAIL
def test_issue_4992():
    # Nonelementary integral.  Requires hypergeometric/Meijer-G handling.
    assert not integrate(log(x) * x**(k - 1) * exp(-x) / gamma(k), (x, 0, oo)).has(Integral)
