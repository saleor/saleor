from sympy import (
    Symbol, Dummy, diff, Derivative, Rational, roots, S, sqrt, hyper,
    cos, gamma, conjugate, factorial, pi, oo, zoo, binomial, RisingFactorial,
    legendre, assoc_legendre, chebyshevu, chebyshevt, chebyshevt_root, chebyshevu_root,
    laguerre, assoc_laguerre, laguerre_poly, hermite, gegenbauer, jacobi, jacobi_normalized)

from sympy.core.compatibility import range
from sympy.utilities.pytest import raises, XFAIL

x = Symbol('x')


def test_jacobi():
    n = Symbol("n")
    a = Symbol("a")
    b = Symbol("b")

    assert jacobi(0, a, b, x) == 1
    assert jacobi(1, a, b, x) == a/2 - b/2 + x*(a/2 + b/2 + 1)

    assert jacobi(n, a, a, x) == RisingFactorial(
        a + 1, n)*gegenbauer(n, a + S(1)/2, x)/RisingFactorial(2*a + 1, n)
    assert jacobi(n, a, -a, x) == ((-1)**a*(-x + 1)**(-a/2)*(x + 1)**(a/2)*assoc_legendre(n, a, x)*
                                   factorial(-a + n)*gamma(a + n + 1)/(factorial(a + n)*gamma(n + 1)))
    assert jacobi(n, -b, b, x) == ((-x + 1)**(b/2)*(x + 1)**(-b/2)*assoc_legendre(n, b, x)*
                                   gamma(-b + n + 1)/gamma(n + 1))
    assert jacobi(n, 0, 0, x) == legendre(n, x)
    assert jacobi(n, S.Half, S.Half, x) == RisingFactorial(
        S(3)/2, n)*chebyshevu(n, x)/factorial(n + 1)
    assert jacobi(n, -S.Half, -S.Half, x) == RisingFactorial(
        S(1)/2, n)*chebyshevt(n, x)/factorial(n)

    X = jacobi(n, a, b, x)
    assert isinstance(X, jacobi)

    assert jacobi(n, a, b, -x) == (-1)**n*jacobi(n, b, a, x)
    assert jacobi(n, a, b, 0) == 2**(-n)*gamma(a + n + 1)*hyper(
        (-b - n, -n), (a + 1,), -1)/(factorial(n)*gamma(a + 1))
    assert jacobi(n, a, b, 1) == RisingFactorial(a + 1, n)/factorial(n)

    m = Symbol("m", positive=True)
    assert jacobi(m, a, b, oo) == oo*RisingFactorial(a + b + m + 1, m)

    assert conjugate(jacobi(m, a, b, x)) == \
        jacobi(m, conjugate(a), conjugate(b), conjugate(x))

    assert diff(jacobi(n, a, b, x), n) == Derivative(jacobi(n, a, b, x), n)
    assert diff(jacobi(n, a, b, x), x) == \
        (a/2 + b/2 + n/2 + S(1)/2)*jacobi(n - 1, a + 1, b + 1, x)

    assert jacobi_normalized(n, a, b, x) == \
           (jacobi(n, a, b, x)/sqrt(2**(a + b + 1)*gamma(a + n + 1)*gamma(b + n + 1)
                                    /((a + b + 2*n + 1)*factorial(n)*gamma(a + b + n + 1))))

    raises(ValueError, lambda: jacobi(-2.1, a, b, x))
    raises(ValueError, lambda: jacobi(Dummy(positive=True, integer=True), 1, 2, oo))


def test_gegenbauer():
    n = Symbol("n")
    a = Symbol("a")

    assert gegenbauer(0, a, x) == 1
    assert gegenbauer(1, a, x) == 2*a*x
    assert gegenbauer(2, a, x) == -a + x**2*(2*a**2 + 2*a)
    assert gegenbauer(3, a, x) == \
        x**3*(4*a**3/3 + 4*a**2 + 8*a/3) + x*(-2*a**2 - 2*a)

    assert gegenbauer(-1, a, x) == 0
    assert gegenbauer(n, S(1)/2, x) == legendre(n, x)
    assert gegenbauer(n, 1, x) == chebyshevu(n, x)
    assert gegenbauer(n, -1, x) == 0

    X = gegenbauer(n, a, x)
    assert isinstance(X, gegenbauer)

    assert gegenbauer(n, a, -x) == (-1)**n*gegenbauer(n, a, x)
    assert gegenbauer(n, a, 0) == 2**n*sqrt(pi) * \
        gamma(a + n/2)/(gamma(a)*gamma(-n/2 + S(1)/2)*gamma(n + 1))
    assert gegenbauer(n, a, 1) == gamma(2*a + n)/(gamma(2*a)*gamma(n + 1))

    assert gegenbauer(n, Rational(3, 4), -1) == zoo

    m = Symbol("m", positive=True)
    assert gegenbauer(m, a, oo) == oo*RisingFactorial(a, m)

    assert conjugate(gegenbauer(n, a, x)) == gegenbauer(n, conjugate(a), conjugate(x))

    assert diff(gegenbauer(n, a, x), n) == Derivative(gegenbauer(n, a, x), n)
    assert diff(gegenbauer(n, a, x), x) == 2*a*gegenbauer(n - 1, a + 1, x)


def test_legendre():
    assert legendre(0, x) == 1
    assert legendre(1, x) == x
    assert legendre(2, x) == ((3*x**2 - 1)/2).expand()
    assert legendre(3, x) == ((5*x**3 - 3*x)/2).expand()
    assert legendre(4, x) == ((35*x**4 - 30*x**2 + 3)/8).expand()
    assert legendre(5, x) == ((63*x**5 - 70*x**3 + 15*x)/8).expand()
    assert legendre(6, x) == ((231*x**6 - 315*x**4 + 105*x**2 - 5)/16).expand()

    assert legendre(10, -1) == 1
    assert legendre(11, -1) == -1
    assert legendre(10, 1) == 1
    assert legendre(11, 1) == 1
    assert legendre(10, 0) != 0
    assert legendre(11, 0) == 0

    assert legendre(-1, x) == 1
    k = Symbol('k')
    assert legendre(5 - k, x).subs(k, 2) == ((5*x**3 - 3*x)/2).expand()

    assert roots(legendre(4, x), x) == {
        sqrt(Rational(3, 7) - Rational(2, 35)*sqrt(30)): 1,
        -sqrt(Rational(3, 7) - Rational(2, 35)*sqrt(30)): 1,
        sqrt(Rational(3, 7) + Rational(2, 35)*sqrt(30)): 1,
        -sqrt(Rational(3, 7) + Rational(2, 35)*sqrt(30)): 1,
    }

    n = Symbol("n")

    X = legendre(n, x)
    assert isinstance(X, legendre)

    assert legendre(-n, x) == legendre(n - 1, x)
    assert legendre(n, -x) == (-1)**n*legendre(n, x)

    assert conjugate(legendre(n, x)) == legendre(n, conjugate(x))

    assert diff(legendre(n, x), x) == \
        n*(x*legendre(n, x) - legendre(n - 1, x))/(x**2 - 1)
    assert diff(legendre(n, x), n) == Derivative(legendre(n, x), n)


def test_assoc_legendre():
    Plm = assoc_legendre
    Q = sqrt(1 - x**2)

    assert Plm(0, 0, x) == 1
    assert Plm(1, 0, x) == x
    assert Plm(1, 1, x) == -Q
    assert Plm(2, 0, x) == (3*x**2 - 1)/2
    assert Plm(2, 1, x) == -3*x*Q
    assert Plm(2, 2, x) == 3*Q**2
    assert Plm(3, 0, x) == (5*x**3 - 3*x)/2
    assert Plm(3, 1, x).expand() == (( 3*(1 - 5*x**2)/2 ).expand() * Q).expand()
    assert Plm(3, 2, x) == 15*x * Q**2
    assert Plm(3, 3, x) == -15 * Q**3

    # negative m
    assert Plm(1, -1, x) == -Plm(1, 1, x)/2
    assert Plm(2, -2, x) == Plm(2, 2, x)/24
    assert Plm(2, -1, x) == -Plm(2, 1, x)/6
    assert Plm(3, -3, x) == -Plm(3, 3, x)/720
    assert Plm(3, -2, x) == Plm(3, 2, x)/120
    assert Plm(3, -1, x) == -Plm(3, 1, x)/12

    n = Symbol("n")
    m = Symbol("m")

    X = Plm(n, m, x)
    assert isinstance(X, assoc_legendre)

    assert Plm(n, 0, x) == legendre(n, x)

    assert conjugate(assoc_legendre(n, m, x)) == \
        assoc_legendre(n, conjugate(m), conjugate(x))
    raises(ValueError, lambda: Plm(0, 1, x))


def test_chebyshev():
    assert chebyshevt(0, x) == 1
    assert chebyshevt(1, x) == x
    assert chebyshevt(2, x) == 2*x**2 - 1
    assert chebyshevt(3, x) == 4*x**3 - 3*x

    for n in range(1, 4):
        for k in range(n):
            z = chebyshevt_root(n, k)
            assert chebyshevt(n, z) == 0
        raises(ValueError, lambda: chebyshevt_root(n, n))

    for n in range(1, 4):
        for k in range(n):
            z = chebyshevu_root(n, k)
            assert chebyshevu(n, z) == 0
        raises(ValueError, lambda: chebyshevu_root(n, n))

    n = Symbol("n")
    X = chebyshevt(n, x)
    assert isinstance(X, chebyshevt)
    assert chebyshevt(n, -x) == (-1)**n*chebyshevt(n, x)
    assert chebyshevt(-n, x) == chebyshevt(n, x)

    assert chebyshevt(n, 0) == cos(pi*n/2)
    assert chebyshevt(n, 1) == 1

    assert conjugate(chebyshevt(n, x)) == chebyshevt(n, conjugate(x))

    assert diff(chebyshevt(n, x), x) == n*chebyshevu(n - 1, x)

    X = chebyshevu(n, x)
    assert isinstance(X, chebyshevu)

    assert chebyshevu(n, -x) == (-1)**n*chebyshevu(n, x)
    assert chebyshevu(-n, x) == -chebyshevu(n - 2, x)

    assert chebyshevu(n, 0) == cos(pi*n/2)
    assert chebyshevu(n, 1) == n + 1

    assert conjugate(chebyshevu(n, x)) == chebyshevu(n, conjugate(x))

    assert diff(chebyshevu(n, x), x) == \
        (-x*chebyshevu(n, x) + (n + 1)*chebyshevt(n + 1, x))/(x**2 - 1)


def test_hermite():
    assert hermite(0, x) == 1
    assert hermite(1, x) == 2*x
    assert hermite(2, x) == 4*x**2 - 2
    assert hermite(3, x) == 8*x**3 - 12*x
    assert hermite(4, x) == 16*x**4 - 48*x**2 + 12
    assert hermite(6, x) == 64*x**6 - 480*x**4 + 720*x**2 - 120

    n = Symbol("n")
    assert hermite(n, x) == hermite(n, x)
    assert hermite(n, -x) == (-1)**n*hermite(n, x)
    assert hermite(-n, x) == hermite(-n, x)

    assert conjugate(hermite(n, x)) == hermite(n, conjugate(x))

    assert diff(hermite(n, x), x) == 2*n*hermite(n - 1, x)
    assert diff(hermite(n, x), n) == Derivative(hermite(n, x), n)


def test_laguerre():
    n = Symbol("n")

    # Laguerre polynomials:
    assert laguerre(0, x) == 1
    assert laguerre(1, x) == -x + 1
    assert laguerre(2, x) == x**2/2 - 2*x + 1
    assert laguerre(3, x) == -x**3/6 + 3*x**2/2 - 3*x + 1

    X = laguerre(Rational(5,2), x)
    assert isinstance(X, laguerre)

    X = laguerre(n, x)
    assert isinstance(X, laguerre)

    assert laguerre(n, 0) == 1

    assert conjugate(laguerre(n, x)) == laguerre(n, conjugate(x))

    assert diff(laguerre(n, x), x) == -assoc_laguerre(n - 1, 1, x)

    raises(ValueError, lambda: laguerre(-2.1, x))


def test_assoc_laguerre():
    n = Symbol("n")
    m = Symbol("m")
    alpha = Symbol("alpha")

    # generalized Laguerre polynomials:
    assert assoc_laguerre(0, alpha, x) == 1
    assert assoc_laguerre(1, alpha, x) == -x + alpha + 1
    assert assoc_laguerre(2, alpha, x).expand() == \
        (x**2/2 - (alpha + 2)*x + (alpha + 2)*(alpha + 1)/2).expand()
    assert assoc_laguerre(3, alpha, x).expand() == \
        (-x**3/6 + (alpha + 3)*x**2/2 - (alpha + 2)*(alpha + 3)*x/2 +
        (alpha + 1)*(alpha + 2)*(alpha + 3)/6).expand()

    # Test the lowest 10 polynomials with laguerre_poly, to make sure it works:
    for i in range(10):
        assert assoc_laguerre(i, 0, x).expand() == laguerre_poly(i, x)

    X = assoc_laguerre(n, m, x)
    assert isinstance(X, assoc_laguerre)

    assert assoc_laguerre(n, 0, x) == laguerre(n, x)
    assert assoc_laguerre(n, alpha, 0) == binomial(alpha + n, alpha)

    assert diff(assoc_laguerre(n, alpha, x), x) == \
        -assoc_laguerre(n - 1, alpha + 1, x)

    assert conjugate(assoc_laguerre(n, alpha, x)) == \
        assoc_laguerre(n, conjugate(alpha), conjugate(x))

    raises(ValueError, lambda: assoc_laguerre(-2.1, alpha, x))


@XFAIL
def test_laguerre_2():
    # This fails due to issue for Sum, like issue 2440
    alpha, k = Symbol("alpha"), Dummy("k")
    assert diff(assoc_laguerre(n, alpha, x), alpha) == Sum(assoc_laguerre(k, alpha, x)/(-alpha + n), (k, 0, n - 1))
