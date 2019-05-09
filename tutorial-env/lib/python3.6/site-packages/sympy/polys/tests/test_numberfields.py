"""Tests for computational algebraic number field theory. """

from sympy import (S, Rational, Symbol, Poly, sqrt, I, oo, Tuple, expand,
    pi, cos, sin, exp)

from sympy.utilities.pytest import raises, slow
from sympy.core.compatibility import range

from sympy.polys.numberfields import (
    minimal_polynomial,
    primitive_element,
    is_isomorphism_possible,
    field_isomorphism_pslq,
    field_isomorphism,
    to_number_field,
    AlgebraicNumber,
    isolate, IntervalPrinter,
)

from sympy.polys.polyerrors import (
    IsomorphismFailed,
    NotAlgebraic,
    GeneratorsError,
)

from sympy.polys.polyclasses import DMP
from sympy.polys.domains import QQ
from sympy.polys.rootoftools import rootof
from sympy.polys.polytools import degree

from sympy.abc import x, y, z

Q = Rational


def test_minimal_polynomial():
    assert minimal_polynomial(-7, x) == x + 7
    assert minimal_polynomial(-1, x) == x + 1
    assert minimal_polynomial( 0, x) == x
    assert minimal_polynomial( 1, x) == x - 1
    assert minimal_polynomial( 7, x) == x - 7

    assert minimal_polynomial(sqrt(2), x) == x**2 - 2
    assert minimal_polynomial(sqrt(5), x) == x**2 - 5
    assert minimal_polynomial(sqrt(6), x) == x**2 - 6

    assert minimal_polynomial(2*sqrt(2), x) == x**2 - 8
    assert minimal_polynomial(3*sqrt(5), x) == x**2 - 45
    assert minimal_polynomial(4*sqrt(6), x) == x**2 - 96

    assert minimal_polynomial(2*sqrt(2) + 3, x) == x**2 - 6*x + 1
    assert minimal_polynomial(3*sqrt(5) + 6, x) == x**2 - 12*x - 9
    assert minimal_polynomial(4*sqrt(6) + 7, x) == x**2 - 14*x - 47

    assert minimal_polynomial(2*sqrt(2) - 3, x) == x**2 + 6*x + 1
    assert minimal_polynomial(3*sqrt(5) - 6, x) == x**2 + 12*x - 9
    assert minimal_polynomial(4*sqrt(6) - 7, x) == x**2 + 14*x - 47

    assert minimal_polynomial(sqrt(1 + sqrt(6)), x) == x**4 - 2*x**2 - 5
    assert minimal_polynomial(sqrt(I + sqrt(6)), x) == x**8 - 10*x**4 + 49

    assert minimal_polynomial(2*I + sqrt(2 + I), x) == x**4 + 4*x**2 + 8*x + 37

    assert minimal_polynomial(sqrt(2) + sqrt(3), x) == x**4 - 10*x**2 + 1
    assert minimal_polynomial(
        sqrt(2) + sqrt(3) + sqrt(6), x) == x**4 - 22*x**2 - 48*x - 23

    a = 1 - 9*sqrt(2) + 7*sqrt(3)

    assert minimal_polynomial(
        1/a, x) == 392*x**4 - 1232*x**3 + 612*x**2 + 4*x - 1
    assert minimal_polynomial(
        1/sqrt(a), x) == 392*x**8 - 1232*x**6 + 612*x**4 + 4*x**2 - 1

    raises(NotAlgebraic, lambda: minimal_polynomial(oo, x))
    raises(NotAlgebraic, lambda: minimal_polynomial(2**y, x))
    raises(NotAlgebraic, lambda: minimal_polynomial(sin(1), x))

    assert minimal_polynomial(sqrt(2)).dummy_eq(x**2 - 2)
    assert minimal_polynomial(sqrt(2), x) == x**2 - 2

    assert minimal_polynomial(sqrt(2), polys=True) == Poly(x**2 - 2)
    assert minimal_polynomial(sqrt(2), x, polys=True) == Poly(x**2 - 2)
    assert minimal_polynomial(sqrt(2), x, polys=True, compose=False) == Poly(x**2 - 2)

    a = AlgebraicNumber(sqrt(2))
    b = AlgebraicNumber(sqrt(3))

    assert minimal_polynomial(a, x) == x**2 - 2
    assert minimal_polynomial(b, x) == x**2 - 3

    assert minimal_polynomial(a, x, polys=True) == Poly(x**2 - 2)
    assert minimal_polynomial(b, x, polys=True) == Poly(x**2 - 3)

    assert minimal_polynomial(sqrt(a/2 + 17), x) == 2*x**4 - 68*x**2 + 577
    assert minimal_polynomial(sqrt(b/2 + 17), x) == 4*x**4 - 136*x**2 + 1153

    a, b = sqrt(2)/3 + 7, AlgebraicNumber(sqrt(2)/3 + 7)

    f = 81*x**8 - 2268*x**6 - 4536*x**5 + 22644*x**4 + 63216*x**3 - \
        31608*x**2 - 189648*x + 141358

    assert minimal_polynomial(sqrt(a) + sqrt(sqrt(a)), x) == f
    assert minimal_polynomial(sqrt(b) + sqrt(sqrt(b)), x) == f

    assert minimal_polynomial(
        a**Q(3, 2), x) == 729*x**4 - 506898*x**2 + 84604519

    # issue 5994
    eq = S('''
        -1/(800*sqrt(-1/240 + 1/(18000*(-1/17280000 +
        sqrt(15)*I/28800000)**(1/3)) + 2*(-1/17280000 +
        sqrt(15)*I/28800000)**(1/3)))''')
    assert minimal_polynomial(eq, x) == 8000*x**2 - 1

    ex = 1 + sqrt(2) + sqrt(3)
    mp = minimal_polynomial(ex, x)
    assert mp == x**4 - 4*x**3 - 4*x**2 + 16*x - 8

    ex = 1/(1 + sqrt(2) + sqrt(3))
    mp = minimal_polynomial(ex, x)
    assert mp == 8*x**4 - 16*x**3 + 4*x**2 + 4*x - 1

    p = (expand((1 + sqrt(2) - 2*sqrt(3) + sqrt(7))**3))**Rational(1, 3)
    mp = minimal_polynomial(p, x)
    assert mp == x**8 - 8*x**7 - 56*x**6 + 448*x**5 + 480*x**4 - 5056*x**3 + 1984*x**2 + 7424*x - 3008
    p = expand((1 + sqrt(2) - 2*sqrt(3) + sqrt(7))**3)
    mp = minimal_polynomial(p, x)
    assert mp == x**8 - 512*x**7 - 118208*x**6 + 31131136*x**5 + 647362560*x**4 - 56026611712*x**3 + 116994310144*x**2 + 404854931456*x - 27216576512

    assert minimal_polynomial(S("-sqrt(5)/2 - 1/2 + (-sqrt(5)/2 - 1/2)**2"), x) == x - 1
    a = 1 + sqrt(2)
    assert minimal_polynomial((a*sqrt(2) + a)**3, x) == x**2 - 198*x + 1

    p = 1/(1 + sqrt(2) + sqrt(3))
    assert minimal_polynomial(p, x, compose=False) == 8*x**4 - 16*x**3 + 4*x**2 + 4*x - 1

    p = 2/(1 + sqrt(2) + sqrt(3))
    assert minimal_polynomial(p, x, compose=False) == x**4 - 4*x**3 + 2*x**2 + 4*x - 2

    assert minimal_polynomial(1 + sqrt(2)*I, x, compose=False) == x**2 - 2*x + 3
    assert minimal_polynomial(1/(1 + sqrt(2)) + 1, x, compose=False) == x**2 - 2
    assert minimal_polynomial(sqrt(2)*I + I*(1 + sqrt(2)), x,
            compose=False) ==  x**4 + 18*x**2 + 49

    # minimal polynomial of I
    assert minimal_polynomial(I, x, domain=QQ.algebraic_field(I)) == x - I
    K = QQ.algebraic_field(I*(sqrt(2) + 1))
    assert minimal_polynomial(I, x, domain=K) == x - I
    assert minimal_polynomial(I, x, domain=QQ) == x**2 + 1
    assert minimal_polynomial(I, x, domain='QQ(y)') == x**2 + 1


def test_minimal_polynomial_hi_prec():
    p = 1/sqrt(1 - 9*sqrt(2) + 7*sqrt(3) + S(1)/10**30)
    mp = minimal_polynomial(p, x)
    # checked with Wolfram Alpha
    assert mp.coeff(x**6) == -1232000000000000000000000000001223999999999999999999999999999987999999999999999999999999999996000000000000000000000000000000


def test_minimal_polynomial_sq():
    from sympy import Add, expand_multinomial
    p = expand_multinomial((1 + 5*sqrt(2) + 2*sqrt(3))**3)
    mp = minimal_polynomial(p**Rational(1, 3), x)
    assert mp == x**4 - 4*x**3 - 118*x**2 + 244*x + 1321
    p = expand_multinomial((1 + sqrt(2) - 2*sqrt(3) + sqrt(7))**3)
    mp = minimal_polynomial(p**Rational(1, 3), x)
    assert mp == x**8 - 8*x**7 - 56*x**6 + 448*x**5 + 480*x**4 - 5056*x**3 + 1984*x**2 + 7424*x - 3008
    p = Add(*[sqrt(i) for i in range(1, 12)])
    mp = minimal_polynomial(p, x)
    assert mp.subs({x: 0}) == -71965773323122507776


def test_minpoly_compose():
    # issue 6868
    eq = S('''
        -1/(800*sqrt(-1/240 + 1/(18000*(-1/17280000 +
        sqrt(15)*I/28800000)**(1/3)) + 2*(-1/17280000 +
        sqrt(15)*I/28800000)**(1/3)))''')
    mp = minimal_polynomial(eq + 3, x)
    assert mp == 8000*x**2 - 48000*x + 71999

    # issue 5888
    assert minimal_polynomial(exp(I*pi/8), x) == x**8 + 1

    mp = minimal_polynomial(sin(pi/7) + sqrt(2), x)
    assert mp == 4096*x**12 - 63488*x**10 + 351488*x**8 - 826496*x**6 + \
        770912*x**4 - 268432*x**2 + 28561
    mp = minimal_polynomial(cos(pi/7) + sqrt(2), x)
    assert mp == 64*x**6 - 64*x**5 - 432*x**4 + 304*x**3 + 712*x**2 - \
            232*x - 239
    mp = minimal_polynomial(exp(I*pi/7) + sqrt(2), x)
    assert mp == x**12 - 2*x**11 - 9*x**10 + 16*x**9 + 43*x**8 - 70*x**7 - 97*x**6 + 126*x**5 + 211*x**4 - 212*x**3 - 37*x**2 + 142*x + 127

    mp = minimal_polynomial(sin(pi/7) + sqrt(2), x)
    assert mp == 4096*x**12 - 63488*x**10 + 351488*x**8 - 826496*x**6 + \
        770912*x**4 - 268432*x**2 + 28561
    mp = minimal_polynomial(cos(pi/7) + sqrt(2), x)
    assert mp == 64*x**6 - 64*x**5 - 432*x**4 + 304*x**3 + 712*x**2 - \
            232*x - 239
    mp = minimal_polynomial(exp(I*pi/7) + sqrt(2), x)
    assert mp == x**12 - 2*x**11 - 9*x**10 + 16*x**9 + 43*x**8 - 70*x**7 - 97*x**6 + 126*x**5 + 211*x**4 - 212*x**3 - 37*x**2 + 142*x + 127

    mp = minimal_polynomial(exp(2*I*pi/7), x)
    assert mp == x**6 + x**5 + x**4 + x**3 + x**2 + x + 1
    mp = minimal_polynomial(exp(2*I*pi/15), x)
    assert mp == x**8 - x**7 + x**5 - x**4 + x**3 - x + 1
    mp = minimal_polynomial(cos(2*pi/7), x)
    assert mp == 8*x**3 + 4*x**2 - 4*x - 1
    mp = minimal_polynomial(sin(2*pi/7), x)
    ex = (5*cos(2*pi/7) - 7)/(9*cos(pi/7) - 5*cos(3*pi/7))
    mp = minimal_polynomial(ex, x)
    assert mp == x**3 + 2*x**2 - x - 1
    assert minimal_polynomial(-1/(2*cos(pi/7)), x) == x**3 + 2*x**2 - x - 1
    assert minimal_polynomial(sin(2*pi/15), x) == \
            256*x**8 - 448*x**6 + 224*x**4 - 32*x**2 + 1
    assert minimal_polynomial(sin(5*pi/14), x) == 8*x**3 - 4*x**2 - 4*x + 1
    assert minimal_polynomial(cos(pi/15), x) == 16*x**4 + 8*x**3 - 16*x**2 - 8*x + 1

    ex = rootof(x**3 +x*4 + 1, 0)
    mp = minimal_polynomial(ex, x)
    assert mp == x**3 + 4*x + 1
    mp = minimal_polynomial(ex + 1, x)
    assert mp == x**3 - 3*x**2 + 7*x - 4
    assert minimal_polynomial(exp(I*pi/3), x) == x**2 - x + 1
    assert minimal_polynomial(exp(I*pi/4), x) == x**4 + 1
    assert minimal_polynomial(exp(I*pi/6), x) == x**4 - x**2 + 1
    assert minimal_polynomial(exp(I*pi/9), x) == x**6 - x**3 + 1
    assert minimal_polynomial(exp(I*pi/10), x) == x**8 - x**6 + x**4 - x**2 + 1
    assert minimal_polynomial(sin(pi/9), x) == 64*x**6 - 96*x**4 + 36*x**2 - 3
    assert minimal_polynomial(sin(pi/11), x) == 1024*x**10 - 2816*x**8 + \
            2816*x**6 - 1232*x**4 + 220*x**2 - 11

    ex = 2**Rational(1, 3)*exp(Rational(2, 3)*I*pi)
    assert minimal_polynomial(ex, x) == x**3 - 2

    raises(NotAlgebraic, lambda: minimal_polynomial(cos(pi*sqrt(2)), x))
    raises(NotAlgebraic, lambda: minimal_polynomial(sin(pi*sqrt(2)), x))
    raises(NotAlgebraic, lambda: minimal_polynomial(exp(I*pi*sqrt(2)), x))

    # issue 5934
    ex = 1/(-36000 - 7200*sqrt(5) + (12*sqrt(10)*sqrt(sqrt(5) + 5) +
        24*sqrt(10)*sqrt(-sqrt(5) + 5))**2) + 1
    raises(ZeroDivisionError, lambda: minimal_polynomial(ex, x))

    ex = sqrt(1 + 2**Rational(1,3)) + sqrt(1 + 2**Rational(1,4)) + sqrt(2)
    mp = minimal_polynomial(ex, x)
    assert degree(mp) == 48 and mp.subs({x:0}) == -16630256576


def test_minpoly_issue_7113():
    # see discussion in https://github.com/sympy/sympy/pull/2234
    from sympy.simplify.simplify import nsimplify
    r = nsimplify(pi, tolerance=0.000000001)
    mp = minimal_polynomial(r, x)
    assert mp == 1768292677839237920489538677417507171630859375*x**109 - \
    2734577732179183863586489182929671773182898498218854181690460140337930774573792597743853652058046464


def test_minpoly_issue_7574():
    ex = -(-1)**Rational(1, 3) + (-1)**Rational(2,3)
    assert minimal_polynomial(ex, x) == x + 1


def test_primitive_element():
    assert primitive_element([sqrt(2)], x) == (x**2 - 2, [1])
    assert primitive_element(
        [sqrt(2), sqrt(3)], x) == (x**4 - 10*x**2 + 1, [1, 1])

    assert primitive_element([sqrt(2)], x, polys=True) == (Poly(x**2 - 2), [1])
    assert primitive_element([sqrt(
        2), sqrt(3)], x, polys=True) == (Poly(x**4 - 10*x**2 + 1), [1, 1])

    assert primitive_element(
        [sqrt(2)], x, ex=True) == (x**2 - 2, [1], [[1, 0]])
    assert primitive_element([sqrt(2), sqrt(3)], x, ex=True) == \
        (x**4 - 10*x**2 + 1, [1, 1], [[Q(1, 2), 0, -Q(9, 2), 0], [-
         Q(1, 2), 0, Q(11, 2), 0]])

    assert primitive_element(
        [sqrt(2)], x, ex=True, polys=True) == (Poly(x**2 - 2), [1], [[1, 0]])
    assert primitive_element([sqrt(2), sqrt(3)], x, ex=True, polys=True) == \
        (Poly(x**4 - 10*x**2 + 1), [1, 1], [[Q(1, 2), 0, -Q(9, 2),
         0], [-Q(1, 2), 0, Q(11, 2), 0]])

    assert primitive_element([sqrt(2)], polys=True) == (Poly(x**2 - 2), [1])

    raises(ValueError, lambda: primitive_element([], x, ex=False))
    raises(ValueError, lambda: primitive_element([], x, ex=True))

    # Issue 14117
    a, b = I*sqrt(2*sqrt(2) + 3), I*sqrt(-2*sqrt(2) + 3)
    assert primitive_element([a, b, I], x) == (x**4 + 6*x**2 + 1, [1, 0, 0])

def test_field_isomorphism_pslq():
    a = AlgebraicNumber(I)
    b = AlgebraicNumber(I*sqrt(3))

    raises(NotImplementedError, lambda: field_isomorphism_pslq(a, b))

    a = AlgebraicNumber(sqrt(2))
    b = AlgebraicNumber(sqrt(3))
    c = AlgebraicNumber(sqrt(7))
    d = AlgebraicNumber(sqrt(2) + sqrt(3))
    e = AlgebraicNumber(sqrt(2) + sqrt(3) + sqrt(7))

    assert field_isomorphism_pslq(a, a) == [1, 0]
    assert field_isomorphism_pslq(a, b) is None
    assert field_isomorphism_pslq(a, c) is None
    assert field_isomorphism_pslq(a, d) == [Q(1, 2), 0, -Q(9, 2), 0]
    assert field_isomorphism_pslq(
        a, e) == [Q(1, 80), 0, -Q(1, 2), 0, Q(59, 20), 0]

    assert field_isomorphism_pslq(b, a) is None
    assert field_isomorphism_pslq(b, b) == [1, 0]
    assert field_isomorphism_pslq(b, c) is None
    assert field_isomorphism_pslq(b, d) == [-Q(1, 2), 0, Q(11, 2), 0]
    assert field_isomorphism_pslq(b, e) == [-Q(
        3, 640), 0, Q(67, 320), 0, -Q(297, 160), 0, Q(313, 80), 0]

    assert field_isomorphism_pslq(c, a) is None
    assert field_isomorphism_pslq(c, b) is None
    assert field_isomorphism_pslq(c, c) == [1, 0]
    assert field_isomorphism_pslq(c, d) is None
    assert field_isomorphism_pslq(c, e) == [Q(
        3, 640), 0, -Q(71, 320), 0, Q(377, 160), 0, -Q(469, 80), 0]

    assert field_isomorphism_pslq(d, a) is None
    assert field_isomorphism_pslq(d, b) is None
    assert field_isomorphism_pslq(d, c) is None
    assert field_isomorphism_pslq(d, d) == [1, 0]
    assert field_isomorphism_pslq(d, e) == [-Q(
        3, 640), 0, Q(71, 320), 0, -Q(377, 160), 0, Q(549, 80), 0]

    assert field_isomorphism_pslq(e, a) is None
    assert field_isomorphism_pslq(e, b) is None
    assert field_isomorphism_pslq(e, c) is None
    assert field_isomorphism_pslq(e, d) is None
    assert field_isomorphism_pslq(e, e) == [1, 0]

    f = AlgebraicNumber(3*sqrt(2) + 8*sqrt(7) - 5)

    assert field_isomorphism_pslq(
        f, e) == [Q(3, 80), 0, -Q(139, 80), 0, Q(347, 20), 0, -Q(761, 20), -5]


def test_field_isomorphism():
    assert field_isomorphism(3, sqrt(2)) == [3]

    assert field_isomorphism( I*sqrt(3), I*sqrt(3)/2) == [ 2, 0]
    assert field_isomorphism(-I*sqrt(3), I*sqrt(3)/2) == [-2, 0]

    assert field_isomorphism( I*sqrt(3), -I*sqrt(3)/2) == [-2, 0]
    assert field_isomorphism(-I*sqrt(3), -I*sqrt(3)/2) == [ 2, 0]

    assert field_isomorphism( 2*I*sqrt(3)/7, 5*I*sqrt(3)/3) == [ S(6)/35, 0]
    assert field_isomorphism(-2*I*sqrt(3)/7, 5*I*sqrt(3)/3) == [-S(6)/35, 0]

    assert field_isomorphism( 2*I*sqrt(3)/7, -5*I*sqrt(3)/3) == [-S(6)/35, 0]
    assert field_isomorphism(-2*I*sqrt(3)/7, -5*I*sqrt(3)/3) == [ S(6)/35, 0]

    assert field_isomorphism(
        2*I*sqrt(3)/7 + 27, 5*I*sqrt(3)/3) == [ S(6)/35, 27]
    assert field_isomorphism(
        -2*I*sqrt(3)/7 + 27, 5*I*sqrt(3)/3) == [-S(6)/35, 27]

    assert field_isomorphism(
        2*I*sqrt(3)/7 + 27, -5*I*sqrt(3)/3) == [-S(6)/35, 27]
    assert field_isomorphism(
        -2*I*sqrt(3)/7 + 27, -5*I*sqrt(3)/3) == [ S(6)/35, 27]

    p = AlgebraicNumber( sqrt(2) + sqrt(3))
    q = AlgebraicNumber(-sqrt(2) + sqrt(3))
    r = AlgebraicNumber( sqrt(2) - sqrt(3))
    s = AlgebraicNumber(-sqrt(2) - sqrt(3))

    pos_coeffs = [ S(1)/2, S(0), -S(9)/2, S(0)]
    neg_coeffs = [-S(1)/2, S(0), S(9)/2, S(0)]

    a = AlgebraicNumber(sqrt(2))

    assert is_isomorphism_possible(a, p) is True
    assert is_isomorphism_possible(a, q) is True
    assert is_isomorphism_possible(a, r) is True
    assert is_isomorphism_possible(a, s) is True

    assert field_isomorphism(a, p, fast=True) == pos_coeffs
    assert field_isomorphism(a, q, fast=True) == neg_coeffs
    assert field_isomorphism(a, r, fast=True) == pos_coeffs
    assert field_isomorphism(a, s, fast=True) == neg_coeffs

    assert field_isomorphism(a, p, fast=False) == pos_coeffs
    assert field_isomorphism(a, q, fast=False) == neg_coeffs
    assert field_isomorphism(a, r, fast=False) == pos_coeffs
    assert field_isomorphism(a, s, fast=False) == neg_coeffs

    a = AlgebraicNumber(-sqrt(2))

    assert is_isomorphism_possible(a, p) is True
    assert is_isomorphism_possible(a, q) is True
    assert is_isomorphism_possible(a, r) is True
    assert is_isomorphism_possible(a, s) is True

    assert field_isomorphism(a, p, fast=True) == neg_coeffs
    assert field_isomorphism(a, q, fast=True) == pos_coeffs
    assert field_isomorphism(a, r, fast=True) == neg_coeffs
    assert field_isomorphism(a, s, fast=True) == pos_coeffs

    assert field_isomorphism(a, p, fast=False) == neg_coeffs
    assert field_isomorphism(a, q, fast=False) == pos_coeffs
    assert field_isomorphism(a, r, fast=False) == neg_coeffs
    assert field_isomorphism(a, s, fast=False) == pos_coeffs

    pos_coeffs = [ S(1)/2, S(0), -S(11)/2, S(0)]
    neg_coeffs = [-S(1)/2, S(0), S(11)/2, S(0)]

    a = AlgebraicNumber(sqrt(3))

    assert is_isomorphism_possible(a, p) is True
    assert is_isomorphism_possible(a, q) is True
    assert is_isomorphism_possible(a, r) is True
    assert is_isomorphism_possible(a, s) is True

    assert field_isomorphism(a, p, fast=True) == neg_coeffs
    assert field_isomorphism(a, q, fast=True) == neg_coeffs
    assert field_isomorphism(a, r, fast=True) == pos_coeffs
    assert field_isomorphism(a, s, fast=True) == pos_coeffs

    assert field_isomorphism(a, p, fast=False) == neg_coeffs
    assert field_isomorphism(a, q, fast=False) == neg_coeffs
    assert field_isomorphism(a, r, fast=False) == pos_coeffs
    assert field_isomorphism(a, s, fast=False) == pos_coeffs

    a = AlgebraicNumber(-sqrt(3))

    assert is_isomorphism_possible(a, p) is True
    assert is_isomorphism_possible(a, q) is True
    assert is_isomorphism_possible(a, r) is True
    assert is_isomorphism_possible(a, s) is True

    assert field_isomorphism(a, p, fast=True) == pos_coeffs
    assert field_isomorphism(a, q, fast=True) == pos_coeffs
    assert field_isomorphism(a, r, fast=True) == neg_coeffs
    assert field_isomorphism(a, s, fast=True) == neg_coeffs

    assert field_isomorphism(a, p, fast=False) == pos_coeffs
    assert field_isomorphism(a, q, fast=False) == pos_coeffs
    assert field_isomorphism(a, r, fast=False) == neg_coeffs
    assert field_isomorphism(a, s, fast=False) == neg_coeffs

    pos_coeffs = [ S(3)/2, S(0), -S(33)/2, -S(8)]
    neg_coeffs = [-S(3)/2, S(0), S(33)/2, -S(8)]

    a = AlgebraicNumber(3*sqrt(3) - 8)

    assert is_isomorphism_possible(a, p) is True
    assert is_isomorphism_possible(a, q) is True
    assert is_isomorphism_possible(a, r) is True
    assert is_isomorphism_possible(a, s) is True

    assert field_isomorphism(a, p, fast=True) == neg_coeffs
    assert field_isomorphism(a, q, fast=True) == neg_coeffs
    assert field_isomorphism(a, r, fast=True) == pos_coeffs
    assert field_isomorphism(a, s, fast=True) == pos_coeffs

    assert field_isomorphism(a, p, fast=False) == neg_coeffs
    assert field_isomorphism(a, q, fast=False) == neg_coeffs
    assert field_isomorphism(a, r, fast=False) == pos_coeffs
    assert field_isomorphism(a, s, fast=False) == pos_coeffs

    a = AlgebraicNumber(3*sqrt(2) + 2*sqrt(3) + 1)

    pos_1_coeffs = [ S(1)/2, S(0), -S(5)/2, S(1)]
    neg_5_coeffs = [-S(5)/2, S(0), S(49)/2, S(1)]
    pos_5_coeffs = [ S(5)/2, S(0), -S(49)/2, S(1)]
    neg_1_coeffs = [-S(1)/2, S(0), S(5)/2, S(1)]

    assert is_isomorphism_possible(a, p) is True
    assert is_isomorphism_possible(a, q) is True
    assert is_isomorphism_possible(a, r) is True
    assert is_isomorphism_possible(a, s) is True

    assert field_isomorphism(a, p, fast=True) == pos_1_coeffs
    assert field_isomorphism(a, q, fast=True) == neg_5_coeffs
    assert field_isomorphism(a, r, fast=True) == pos_5_coeffs
    assert field_isomorphism(a, s, fast=True) == neg_1_coeffs

    assert field_isomorphism(a, p, fast=False) == pos_1_coeffs
    assert field_isomorphism(a, q, fast=False) == neg_5_coeffs
    assert field_isomorphism(a, r, fast=False) == pos_5_coeffs
    assert field_isomorphism(a, s, fast=False) == neg_1_coeffs

    a = AlgebraicNumber(sqrt(2))
    b = AlgebraicNumber(sqrt(3))
    c = AlgebraicNumber(sqrt(7))

    assert is_isomorphism_possible(a, b) is True
    assert is_isomorphism_possible(b, a) is True

    assert is_isomorphism_possible(c, p) is False

    assert field_isomorphism(sqrt(2), sqrt(3), fast=True) is None
    assert field_isomorphism(sqrt(3), sqrt(2), fast=True) is None

    assert field_isomorphism(sqrt(2), sqrt(3), fast=False) is None
    assert field_isomorphism(sqrt(3), sqrt(2), fast=False) is None


def test_to_number_field():
    assert to_number_field(sqrt(2)) == AlgebraicNumber(sqrt(2))
    assert to_number_field(
        [sqrt(2), sqrt(3)]) == AlgebraicNumber(sqrt(2) + sqrt(3))

    a = AlgebraicNumber(sqrt(2) + sqrt(3), [S(1)/2, S(0), -S(9)/2, S(0)])

    assert to_number_field(sqrt(2), sqrt(2) + sqrt(3)) == a
    assert to_number_field(sqrt(2), AlgebraicNumber(sqrt(2) + sqrt(3))) == a

    raises(IsomorphismFailed, lambda: to_number_field(sqrt(2), sqrt(3)))


def test_AlgebraicNumber():
    minpoly, root = x**2 - 2, sqrt(2)

    a = AlgebraicNumber(root, gen=x)

    assert a.rep == DMP([QQ(1), QQ(0)], QQ)
    assert a.root == root
    assert a.alias is None
    assert a.minpoly == minpoly
    assert a.is_number

    assert a.is_aliased is False

    assert a.coeffs() == [S(1), S(0)]
    assert a.native_coeffs() == [QQ(1), QQ(0)]

    a = AlgebraicNumber(root, gen=x, alias='y')

    assert a.rep == DMP([QQ(1), QQ(0)], QQ)
    assert a.root == root
    assert a.alias == Symbol('y')
    assert a.minpoly == minpoly
    assert a.is_number

    assert a.is_aliased is True

    a = AlgebraicNumber(root, gen=x, alias=Symbol('y'))

    assert a.rep == DMP([QQ(1), QQ(0)], QQ)
    assert a.root == root
    assert a.alias == Symbol('y')
    assert a.minpoly == minpoly
    assert a.is_number

    assert a.is_aliased is True

    assert AlgebraicNumber(sqrt(2), []).rep == DMP([], QQ)
    assert AlgebraicNumber(sqrt(2), ()).rep == DMP([], QQ)
    assert AlgebraicNumber(sqrt(2), (0, 0)).rep == DMP([], QQ)

    assert AlgebraicNumber(sqrt(2), [8]).rep == DMP([QQ(8)], QQ)
    assert AlgebraicNumber(sqrt(2), [S(8)/3]).rep == DMP([QQ(8, 3)], QQ)

    assert AlgebraicNumber(sqrt(2), [7, 3]).rep == DMP([QQ(7), QQ(3)], QQ)
    assert AlgebraicNumber(
        sqrt(2), [S(7)/9, S(3)/2]).rep == DMP([QQ(7, 9), QQ(3, 2)], QQ)

    assert AlgebraicNumber(sqrt(2), [1, 2, 3]).rep == DMP([QQ(2), QQ(5)], QQ)

    a = AlgebraicNumber(AlgebraicNumber(root, gen=x), [1, 2])

    assert a.rep == DMP([QQ(1), QQ(2)], QQ)
    assert a.root == root
    assert a.alias is None
    assert a.minpoly == minpoly
    assert a.is_number

    assert a.is_aliased is False

    assert a.coeffs() == [S(1), S(2)]
    assert a.native_coeffs() == [QQ(1), QQ(2)]

    a = AlgebraicNumber((minpoly, root), [1, 2])

    assert a.rep == DMP([QQ(1), QQ(2)], QQ)
    assert a.root == root
    assert a.alias is None
    assert a.minpoly == minpoly
    assert a.is_number

    assert a.is_aliased is False

    a = AlgebraicNumber((Poly(minpoly), root), [1, 2])

    assert a.rep == DMP([QQ(1), QQ(2)], QQ)
    assert a.root == root
    assert a.alias is None
    assert a.minpoly == minpoly
    assert a.is_number

    assert a.is_aliased is False

    assert AlgebraicNumber( sqrt(3)).rep == DMP([ QQ(1), QQ(0)], QQ)
    assert AlgebraicNumber(-sqrt(3)).rep == DMP([ QQ(1), QQ(0)], QQ)

    a = AlgebraicNumber(sqrt(2))
    b = AlgebraicNumber(sqrt(2))

    assert a == b

    c = AlgebraicNumber(sqrt(2), gen=x)
    d = AlgebraicNumber(sqrt(2), gen=x)

    assert a == b
    assert a == c

    a = AlgebraicNumber(sqrt(2), [1, 2])
    b = AlgebraicNumber(sqrt(2), [1, 3])

    assert a != b and a != sqrt(2) + 3

    assert (a == x) is False and (a != x) is True

    a = AlgebraicNumber(sqrt(2), [1, 0])
    b = AlgebraicNumber(sqrt(2), [1, 0], alias=y)

    assert a.as_poly(x) == Poly(x)
    assert b.as_poly() == Poly(y)

    assert a.as_expr() == sqrt(2)
    assert a.as_expr(x) == x
    assert b.as_expr() == sqrt(2)
    assert b.as_expr(x) == x

    a = AlgebraicNumber(sqrt(2), [2, 3])
    b = AlgebraicNumber(sqrt(2), [2, 3], alias=y)

    p = a.as_poly()

    assert p == Poly(2*p.gen + 3)

    assert a.as_poly(x) == Poly(2*x + 3)
    assert b.as_poly() == Poly(2*y + 3)

    assert a.as_expr() == 2*sqrt(2) + 3
    assert a.as_expr(x) == 2*x + 3
    assert b.as_expr() == 2*sqrt(2) + 3
    assert b.as_expr(x) == 2*x + 3

    a = AlgebraicNumber(sqrt(2))
    b = to_number_field(sqrt(2))
    assert a.args == b.args == (sqrt(2), Tuple(1, 0))
    b = AlgebraicNumber(sqrt(2), alias='alpha')
    assert b.args == (sqrt(2), Tuple(1, 0), Symbol('alpha'))

    a = AlgebraicNumber(sqrt(2), [1, 2, 3])
    assert a.args == (sqrt(2), Tuple(1, 2, 3))


def test_to_algebraic_integer():
    a = AlgebraicNumber(sqrt(3), gen=x).to_algebraic_integer()

    assert a.minpoly == x**2 - 3
    assert a.root == sqrt(3)
    assert a.rep == DMP([QQ(1), QQ(0)], QQ)

    a = AlgebraicNumber(2*sqrt(3), gen=x).to_algebraic_integer()
    assert a.minpoly == x**2 - 12
    assert a.root == 2*sqrt(3)
    assert a.rep == DMP([QQ(1), QQ(0)], QQ)

    a = AlgebraicNumber(sqrt(3)/2, gen=x).to_algebraic_integer()

    assert a.minpoly == x**2 - 12
    assert a.root == 2*sqrt(3)
    assert a.rep == DMP([QQ(1), QQ(0)], QQ)

    a = AlgebraicNumber(sqrt(3)/2, [S(7)/19, 3], gen=x).to_algebraic_integer()

    assert a.minpoly == x**2 - 12
    assert a.root == 2*sqrt(3)
    assert a.rep == DMP([QQ(7, 19), QQ(3)], QQ)


def test_IntervalPrinter():
    ip = IntervalPrinter()
    assert ip.doprint(x**Q(1, 3)) == "x**(mpi('1/3'))"
    assert ip.doprint(sqrt(x)) == "x**(mpi('1/2'))"


def test_isolate():
    assert isolate(1) == (1, 1)
    assert isolate(S(1)/2) == (S(1)/2, S(1)/2)

    assert isolate(sqrt(2)) == (1, 2)
    assert isolate(-sqrt(2)) == (-2, -1)

    assert isolate(sqrt(2), eps=S(1)/100) == (S(24)/17, S(17)/12)
    assert isolate(-sqrt(2), eps=S(1)/100) == (-S(17)/12, -S(24)/17)

    raises(NotImplementedError, lambda: isolate(I))

def test_minpoly_fraction_field():
    assert minimal_polynomial(1/x, y) == -x*y + 1
    assert minimal_polynomial(1 / (x + 1), y) == (x + 1)*y - 1

    assert minimal_polynomial(sqrt(x), y) == y**2 - x
    assert minimal_polynomial(sqrt(x + 1), y) == y**2 - x - 1
    assert minimal_polynomial(sqrt(x) / x, y) == x*y**2 - 1
    assert minimal_polynomial(sqrt(2) * sqrt(x), y) == y**2 - 2 * x
    assert minimal_polynomial(sqrt(2) + sqrt(x), y) == \
        y**4 + (-2*x - 4)*y**2 + x**2 - 4*x + 4

    assert minimal_polynomial(x**Rational(1,3), y) == y**3 - x
    assert minimal_polynomial(x**Rational(1,3) + sqrt(x), y) == \
        y**6 - 3*x*y**4 - 2*x*y**3 + 3*x**2*y**2 - 6*x**2*y - x**3 + x**2

    assert minimal_polynomial(sqrt(x) / z, y) == z**2*y**2 - x
    assert minimal_polynomial(sqrt(x) / (z + 1), y) == (z**2 + 2*z + 1)*y**2 - x

    assert minimal_polynomial(1/x, y, polys=True) == Poly(-x*y + 1, y)
    assert minimal_polynomial(1 / (x + 1), y, polys=True) == \
        Poly((x + 1)*y - 1, y)
    assert minimal_polynomial(sqrt(x), y, polys=True) == Poly(y**2 - x, y)
    assert minimal_polynomial(sqrt(x) / z, y, polys=True) == \
        Poly(z**2*y**2 - x, y)

    # this is (sqrt(1 + x**3)/x).integrate(x).diff(x) - sqrt(1 + x**3)/x
    a = sqrt(x)/sqrt(1 + x**(-3)) - sqrt(x**3 + 1)/x + 1/(x**(S(5)/2)* \
        (1 + x**(-3))**(S(3)/2)) + 1/(x**(S(11)/2)*(1 + x**(-3))**(S(3)/2))

    assert minimal_polynomial(a, y) == y

    raises(NotAlgebraic, lambda: minimal_polynomial(exp(x), y))
    raises(GeneratorsError, lambda: minimal_polynomial(sqrt(x), x))
    raises(GeneratorsError, lambda: minimal_polynomial(sqrt(x) - y, x))
    raises(NotImplementedError, lambda: minimal_polynomial(sqrt(x), y, compose=False))

@slow
def test_minpoly_fraction_field_slow():
    assert minimal_polynomial(minimal_polynomial(sqrt(x**Rational(1,5) - 1),
        y).subs(y, sqrt(x**Rational(1,5) - 1)), z) == z

def test_minpoly_domain():
    assert minimal_polynomial(sqrt(2), x, domain=QQ.algebraic_field(sqrt(2))) == \
        x - sqrt(2)
    assert minimal_polynomial(sqrt(8), x, domain=QQ.algebraic_field(sqrt(2))) == \
        x - 2*sqrt(2)
    assert minimal_polynomial(sqrt(Rational(3,2)), x,
        domain=QQ.algebraic_field(sqrt(2))) == 2*x**2 - 3

    raises(NotAlgebraic, lambda: minimal_polynomial(y, x, domain=QQ))


def test_issue_14831():
    a = -2*sqrt(2)*sqrt(12*sqrt(2) + 17)
    assert minimal_polynomial(a, x) == x**2 + 16*x - 8
    e = (-3*sqrt(12*sqrt(2) + 17) + 12*sqrt(2) +
         17 - 2*sqrt(2)*sqrt(12*sqrt(2) + 17))
    assert minimal_polynomial(e, x) == x
