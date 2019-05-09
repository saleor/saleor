"""Tests for efficient functions for generating orthogonal polynomials. """

from sympy import Poly, S, Rational as Q
from sympy.utilities.pytest import raises

from sympy.polys.orthopolys import (
    jacobi_poly,
    gegenbauer_poly,
    chebyshevt_poly,
    chebyshevu_poly,
    hermite_poly,
    legendre_poly,
    laguerre_poly,
)

from sympy.abc import x, a, b


def test_jacobi_poly():
    raises(ValueError, lambda: jacobi_poly(-1, a, b, x))

    assert jacobi_poly(1, a, b, x, polys=True) == Poly(
        (a/2 + b/2 + 1)*x + a/2 - b/2, x, domain='ZZ(a,b)')

    assert jacobi_poly(0, a, b, x) == 1
    assert jacobi_poly(1, a, b, x) == a/2 - b/2 + x*(a/2 + b/2 + 1)
    assert jacobi_poly(2, a, b, x) == (a**2/8 - a*b/4 - a/8 + b**2/8 - b/8 + x**2*(a**2/8 + a*b/4 + 7*a/8 +
                                       b**2/8 + 7*b/8 + S(3)/2) + x*(a**2/4 + 3*a/4 - b**2/4 - 3*b/4) - S(1)/2)

    assert jacobi_poly(1, a, b, polys=True) == Poly(
        (a/2 + b/2 + 1)*x + a/2 - b/2, x, domain='ZZ(a,b)')


def test_gegenbauer_poly():
    raises(ValueError, lambda: gegenbauer_poly(-1, a, x))

    assert gegenbauer_poly(
        1, a, x, polys=True) == Poly(2*a*x, x, domain='ZZ(a)')

    assert gegenbauer_poly(0, a, x) == 1
    assert gegenbauer_poly(1, a, x) == 2*a*x
    assert gegenbauer_poly(2, a, x) == -a + x**2*(2*a**2 + 2*a)
    assert gegenbauer_poly(
        3, a, x) == x**3*(4*a**3/3 + 4*a**2 + 8*a/3) + x*(-2*a**2 - 2*a)

    assert gegenbauer_poly(1, S.Half).dummy_eq(x)
    assert gegenbauer_poly(1, a, polys=True) == Poly(2*a*x, x, domain='ZZ(a)')


def test_chebyshevt_poly():
    raises(ValueError, lambda: chebyshevt_poly(-1, x))

    assert chebyshevt_poly(1, x, polys=True) == Poly(x)

    assert chebyshevt_poly(0, x) == 1
    assert chebyshevt_poly(1, x) == x
    assert chebyshevt_poly(2, x) == 2*x**2 - 1
    assert chebyshevt_poly(3, x) == 4*x**3 - 3*x
    assert chebyshevt_poly(4, x) == 8*x**4 - 8*x**2 + 1
    assert chebyshevt_poly(5, x) == 16*x**5 - 20*x**3 + 5*x
    assert chebyshevt_poly(6, x) == 32*x**6 - 48*x**4 + 18*x**2 - 1

    assert chebyshevt_poly(1).dummy_eq(x)
    assert chebyshevt_poly(1, polys=True) == Poly(x)


def test_chebyshevu_poly():
    raises(ValueError, lambda: chebyshevu_poly(-1, x))

    assert chebyshevu_poly(1, x, polys=True) == Poly(2*x)

    assert chebyshevu_poly(0, x) == 1
    assert chebyshevu_poly(1, x) == 2*x
    assert chebyshevu_poly(2, x) == 4*x**2 - 1
    assert chebyshevu_poly(3, x) == 8*x**3 - 4*x
    assert chebyshevu_poly(4, x) == 16*x**4 - 12*x**2 + 1
    assert chebyshevu_poly(5, x) == 32*x**5 - 32*x**3 + 6*x
    assert chebyshevu_poly(6, x) == 64*x**6 - 80*x**4 + 24*x**2 - 1

    assert chebyshevu_poly(1).dummy_eq(2*x)
    assert chebyshevu_poly(1, polys=True) == Poly(2*x)


def test_hermite_poly():
    raises(ValueError, lambda: hermite_poly(-1, x))

    assert hermite_poly(1, x, polys=True) == Poly(2*x)

    assert hermite_poly(0, x) == 1
    assert hermite_poly(1, x) == 2*x
    assert hermite_poly(2, x) == 4*x**2 - 2
    assert hermite_poly(3, x) == 8*x**3 - 12*x
    assert hermite_poly(4, x) == 16*x**4 - 48*x**2 + 12
    assert hermite_poly(5, x) == 32*x**5 - 160*x**3 + 120*x
    assert hermite_poly(6, x) == 64*x**6 - 480*x**4 + 720*x**2 - 120

    assert hermite_poly(1).dummy_eq(2*x)
    assert hermite_poly(1, polys=True) == Poly(2*x)


def test_legendre_poly():
    raises(ValueError, lambda: legendre_poly(-1, x))

    assert legendre_poly(1, x, polys=True) == Poly(x)

    assert legendre_poly(0, x) == 1
    assert legendre_poly(1, x) == x
    assert legendre_poly(2, x) == Q(3, 2)*x**2 - Q(1, 2)
    assert legendre_poly(3, x) == Q(5, 2)*x**3 - Q(3, 2)*x
    assert legendre_poly(4, x) == Q(35, 8)*x**4 - Q(30, 8)*x**2 + Q(3, 8)
    assert legendre_poly(5, x) == Q(63, 8)*x**5 - Q(70, 8)*x**3 + Q(15, 8)*x
    assert legendre_poly(6, x) == Q(
        231, 16)*x**6 - Q(315, 16)*x**4 + Q(105, 16)*x**2 - Q(5, 16)

    assert legendre_poly(1).dummy_eq(x)
    assert legendre_poly(1, polys=True) == Poly(x)


def test_laguerre_poly():
    raises(ValueError, lambda: laguerre_poly(-1, x))

    assert laguerre_poly(1, x, polys=True) == Poly(-x + 1)

    assert laguerre_poly(0, x) == 1
    assert laguerre_poly(1, x) == -x + 1
    assert laguerre_poly(2, x) == Q(1, 2)*x**2 - Q(4, 2)*x + 1
    assert laguerre_poly(3, x) == -Q(1, 6)*x**3 + Q(9, 6)*x**2 - Q(18, 6)*x + 1
    assert laguerre_poly(4, x) == Q(
        1, 24)*x**4 - Q(16, 24)*x**3 + Q(72, 24)*x**2 - Q(96, 24)*x + 1
    assert laguerre_poly(5, x) == -Q(1, 120)*x**5 + Q(25, 120)*x**4 - Q(
        200, 120)*x**3 + Q(600, 120)*x**2 - Q(600, 120)*x + 1
    assert laguerre_poly(6, x) == Q(1, 720)*x**6 - Q(36, 720)*x**5 + Q(450, 720)*x**4 - Q(2400, 720)*x**3 + Q(5400, 720)*x**2 - Q(4320, 720)*x + 1

    assert laguerre_poly(0, x, a) == 1
    assert laguerre_poly(1, x, a) == -x + a + 1
    assert laguerre_poly(2, x, a) == x**2/2 + (-a - 2)*x + a**2/2 + 3*a/2 + 1
    assert laguerre_poly(3, x, a) == -x**3/6 + (a/2 + Q(
        3)/2)*x**2 + (-a**2/2 - 5*a/2 - 3)*x + a**3/6 + a**2 + 11*a/6 + 1

    assert laguerre_poly(1).dummy_eq(-x + 1)
    assert laguerre_poly(1, polys=True) == Poly(-x + 1)
