from sympy import (
    Rational, gammasimp, factorial, gamma, binomial, Symbol, pi, S,
    sin, exp, powsimp, sqrt, simplify, symbols, cos, rf)

from sympy.abc import x, y, n, k


def test_gammasimp():
    R = Rational

    # was part of test_combsimp_gamma() in test_combsimp.py
    assert gammasimp(gamma(x)) == gamma(x)
    assert gammasimp(gamma(x + 1)/x) == gamma(x)
    assert gammasimp(gamma(x)/(x - 1)) == gamma(x - 1)
    assert gammasimp(x*gamma(x)) == gamma(x + 1)
    assert gammasimp((x + 1)*gamma(x + 1)) == gamma(x + 2)
    assert gammasimp(gamma(x + y)*(x + y)) == gamma(x + y + 1)
    assert gammasimp(x/gamma(x + 1)) == 1/gamma(x)
    assert gammasimp((x + 1)**2/gamma(x + 2)) == (x + 1)/gamma(x + 1)
    assert gammasimp(x*gamma(x) + gamma(x + 3)/(x + 2)) == \
        (x + 2)*gamma(x + 1)

    assert gammasimp(gamma(2*x)*x) == gamma(2*x + 1)/2
    assert gammasimp(gamma(2*x)/(x - S(1)/2)) == 2*gamma(2*x - 1)

    assert gammasimp(gamma(x)*gamma(1 - x)) == pi/sin(pi*x)
    assert gammasimp(gamma(x)*gamma(-x)) == -pi/(x*sin(pi*x))
    assert gammasimp(1/gamma(x + 3)/gamma(1 - x)) == \
        sin(pi*x)/(pi*x*(x + 1)*(x + 2))

    assert gammasimp(factorial(n + 2)) == gamma(n + 3)
    assert gammasimp(binomial(n, k)) == \
        gamma(n + 1)/(gamma(k + 1)*gamma(-k + n + 1))

    assert powsimp(gammasimp(
        gamma(x)*gamma(x + S(1)/2)*gamma(y)/gamma(x + y))) == \
        2**(-2*x + 1)*sqrt(pi)*gamma(2*x)*gamma(y)/gamma(x + y)
    assert gammasimp(1/gamma(x)/gamma(x - S(1)/3)/gamma(x + S(1)/3)) == \
        3**(3*x - S(3)/2)/(2*pi*gamma(3*x - 1))
    assert simplify(
        gamma(S(1)/2 + x/2)*gamma(1 + x/2)/gamma(1 + x)/sqrt(pi)*2**x) == 1
    assert gammasimp(gamma(S(-1)/4)*gamma(S(-3)/4)) == 16*sqrt(2)*pi/3

    assert powsimp(gammasimp(gamma(2*x)/gamma(x))) == \
        2**(2*x - 1)*gamma(x + S(1)/2)/sqrt(pi)

    # issue 6792
    e = (-gamma(k)*gamma(k + 2) + gamma(k + 1)**2)/gamma(k)**2
    assert gammasimp(e) == -k
    assert gammasimp(1/e) == -1/k
    e = (gamma(x) + gamma(x + 1))/gamma(x)
    assert gammasimp(e) == x + 1
    assert gammasimp(1/e) == 1/(x + 1)
    e = (gamma(x) + gamma(x + 2))*(gamma(x - 1) + gamma(x))/gamma(x)
    assert gammasimp(e) == (x**2 + x + 1)*gamma(x + 1)/(x - 1)
    e = (-gamma(k)*gamma(k + 2) + gamma(k + 1)**2)/gamma(k)**2
    assert gammasimp(e**2) == k**2
    assert gammasimp(e**2/gamma(k + 1)) == k/gamma(k)
    a = R(1, 2) + R(1, 3)
    b = a + R(1, 3)
    assert gammasimp(gamma(2*k)/gamma(k)*gamma(k + a)*gamma(k + b))
    3*2**(2*k + 1)*3**(-3*k - 2)*sqrt(pi)*gamma(3*k + R(3, 2))/2

    # issue 9699
    assert gammasimp((x + 1)*factorial(x)/gamma(y)) == gamma(x + 2)/gamma(y)
    assert gammasimp(rf(x + n, k)*binomial(n, k)) == gamma(n + 1)*gamma(k + n
        + x)/(gamma(k + 1)*gamma(n + x)*gamma(-k + n + 1))

    A, B = symbols('A B', commutative=False)
    assert gammasimp(e*B*A) == gammasimp(e)*B*A

    # check iteration
    assert gammasimp(gamma(2*k)/gamma(k)*gamma(-k - R(1, 2))) == (
        -2**(2*k + 1)*sqrt(pi)/(2*((2*k + 1)*cos(pi*k))))
    assert gammasimp(
        gamma(k)*gamma(k + R(1, 3))*gamma(k + R(2, 3))/gamma(3*k/2)) == (
        3*2**(3*k + 1)*3**(-3*k - S.Half)*sqrt(pi)*gamma(3*k/2 + S.Half)/2)

    # issue 6153
    assert gammasimp(gamma(S(1)/4)/gamma(S(5)/4)) == 4

    # was part of test_combsimp() in test_combsimp.py
    assert gammasimp(binomial(n + 2, k + S(1)/2)) == gamma(n + 3)/ \
        (gamma(k + S(3)/2)*gamma(-k + n + S(5)/2))
    assert gammasimp(binomial(n + 2, k + 2.0)) == \
        gamma(n + 3)/(gamma(k + 3.0)*gamma(-k + n + 1))

    # issue 11548
    assert gammasimp(binomial(0, x)) == sin(pi*x)/(pi*x)

    e = gamma(n + S(1)/3)*gamma(n + S(2)/3)
    assert gammasimp(e) == e
    assert gammasimp(gamma(4*n + S(1)/2)/gamma(2*n - S(3)/4)) == \
        2**(4*n - S(5)/2)*(8*n - 3)*gamma(2*n + S(3)/4)/sqrt(pi)

    i, m = symbols('i m', integer = True)
    e = gamma(exp(i))
    assert gammasimp(e) == e
    e = gamma(m + 3)
    assert gammasimp(e) == e
    e = gamma(m + 1)/(gamma(i + 1)*gamma(-i + m + 1))
    assert gammasimp(e) == e

    p = symbols("p", integer=True, positive=True)
    assert gammasimp(gamma(-p+4)) == gamma(-p+4)
