"""Tests for tools and arithmetics for monomials of distributed polynomials. """

from sympy.polys.monomials import (
    itermonomials, monomial_count,
    monomial_mul, monomial_div,
    monomial_gcd, monomial_lcm,
    monomial_max, monomial_min,
    monomial_divides,
    Monomial,
)

from sympy.polys.polyerrors import ExactQuotientFailed

from sympy.abc import a, b, c, x, y, z
from sympy.core import S, symbols
from sympy.utilities.pytest import raises


def test_monomials():
    assert itermonomials([], -1) == set()
    assert itermonomials([], 0) == {S(1)}
    assert itermonomials([], 1) == {S(1)}
    assert itermonomials([], 2) == {S(1)}
    assert itermonomials([], 3) == {S(1)}

    assert itermonomials([x], -1) == set()
    assert itermonomials([x], 0) == {S(1)}
    assert itermonomials([x], 1) == {S(1), x}
    assert itermonomials([x], 2) == {S(1), x, x**2}
    assert itermonomials([x], 3) == {S(1), x, x**2, x**3}

    assert itermonomials([x, y], 0) == {S(1)}
    assert itermonomials([x, y], 1) == {S(1), x, y}
    assert itermonomials([x, y], 2) == {S(1), x, y, x**2, y**2, x*y}
    assert itermonomials([x, y], 3) == \
        {S(1), x, y, x**2, x**3, y**2, y**3, x*y, x*y**2, y*x**2}


    i, j, k = symbols('i j k', commutative=False)
    assert itermonomials([i, j, k], 0) == {S(1)}
    assert itermonomials([i, j, k], 1) == {S(1), i, j, k}
    assert itermonomials([i, j, k], 2) == \
            {S(1), i, j, k, i**2, j**2, k**2, i*j, i*k, j*i, j*k, k*i, k*j}

    assert itermonomials([i, j, k], 3) == \
            {S(1), i, j, k, i**2, j**2, k**2, i*j, i*k, j*i, j*k, k*i, k*j,
                        i**3, j**3, k**3,
                        i**2 * j, i**2 * k, j * i**2, k * i**2,
                        j**2 * i, j**2 * k, i * j**2, k * j**2,
                        k**2 * i, k**2 * j, i * k**2, j * k**2,
                        i*j*i, i*k*i, j*i*j, j*k*j, k*i*k, k*j*k,
                        i*j*k, i*k*j, j*i*k, j*k*i, k*i*j, k*j*i,
                    }

    assert itermonomials([x, i, j], 0) == {S(1)}
    assert itermonomials([x, i, j], 1) == {S(1), x, i, j}
    assert itermonomials([x, i, j], 2) == {S(1), x, i, j, x*i, x*j, i*j, j*i, x**2, i**2, j**2}
    assert itermonomials([x, i, j], 3) == \
            {S(1), x, i, j, x*i, x*j, i*j, j*i, x**2, i**2, j**2,
                        x**3, i**3, j**3,
                        x**2 * i, x**2 * j,
                        x * i**2, j * i**2, i**2 * j, i*j*i,
                        x * j**2, i * j**2, j**2 * i, j*i*j,
                        x * i * j, x * j * i,
                    }

def test_monomial_count():
    assert monomial_count(2, 2) == 6
    assert monomial_count(2, 3) == 10

def test_monomial_mul():
    assert monomial_mul((3, 4, 1), (1, 2, 0)) == (4, 6, 1)

def test_monomial_div():
    assert monomial_div((3, 4, 1), (1, 2, 0)) == (2, 2, 1)

def test_monomial_gcd():
    assert monomial_gcd((3, 4, 1), (1, 2, 0)) == (1, 2, 0)

def test_monomial_lcm():
    assert monomial_lcm((3, 4, 1), (1, 2, 0)) == (3, 4, 1)

def test_monomial_max():
    assert monomial_max((3, 4, 5), (0, 5, 1), (6, 3, 9)) == (6, 5, 9)

def test_monomial_min():
    assert monomial_min((3, 4, 5), (0, 5, 1), (6, 3, 9)) == (0, 3, 1)

def test_monomial_divides():
    assert monomial_divides((1, 2, 3), (4, 5, 6)) is True
    assert monomial_divides((1, 2, 3), (0, 5, 6)) is False

def test_Monomial():
    m = Monomial((3, 4, 1), (x, y, z))
    n = Monomial((1, 2, 0), (x, y, z))

    assert m.as_expr() == x**3*y**4*z
    assert n.as_expr() == x**1*y**2

    assert m.as_expr(a, b, c) == a**3*b**4*c
    assert n.as_expr(a, b, c) == a**1*b**2

    assert m.exponents == (3, 4, 1)
    assert m.gens == (x, y, z)

    assert n.exponents == (1, 2, 0)
    assert n.gens == (x, y, z)

    assert m == (3, 4, 1)
    assert n != (3, 4, 1)
    assert m != (1, 2, 0)
    assert n == (1, 2, 0)

    assert m[0] == m[-3] == 3
    assert m[1] == m[-2] == 4
    assert m[2] == m[-1] == 1

    assert n[0] == n[-3] == 1
    assert n[1] == n[-2] == 2
    assert n[2] == n[-1] == 0

    assert m[:2] == (3, 4)
    assert n[:2] == (1, 2)

    assert m*n == Monomial((4, 6, 1))
    assert m/n == Monomial((2, 2, 1))

    assert m*(1, 2, 0) == Monomial((4, 6, 1))
    assert m/(1, 2, 0) == Monomial((2, 2, 1))

    assert m.gcd(n) == Monomial((1, 2, 0))
    assert m.lcm(n) == Monomial((3, 4, 1))

    assert m.gcd((1, 2, 0)) == Monomial((1, 2, 0))
    assert m.lcm((1, 2, 0)) == Monomial((3, 4, 1))

    assert m**0 == Monomial((0, 0, 0))
    assert m**1 == m
    assert m**2 == Monomial((6, 8, 2))
    assert m**3 == Monomial((9, 12, 3))

    raises(ExactQuotientFailed, lambda: m/Monomial((5, 2, 0)))
