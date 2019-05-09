from sympy import Eq, factorial, Function, Lambda, rf, S, sqrt, symbols, I, expand_func, binomial, gamma
from sympy.solvers.recurr import rsolve, rsolve_hyper, rsolve_poly, rsolve_ratio
from sympy.utilities.pytest import raises, slow
from sympy.core.compatibility import range
from sympy.abc import a, b

y = Function('y')
n, k = symbols('n,k', integer=True)
C0, C1, C2 = symbols('C0,C1,C2')


def test_rsolve_poly():
    assert rsolve_poly([-1, -1, 1], 0, n) == 0
    assert rsolve_poly([-1, -1, 1], 1, n) == -1

    assert rsolve_poly([-1, n + 1], n, n) == 1
    assert rsolve_poly([-1, 1], n, n) == C0 + (n**2 - n)/2
    assert rsolve_poly([-n - 1, n], 1, n) == C1*n - 1
    assert rsolve_poly([-4*n - 2, 1], 4*n + 1, n) == -1

    assert rsolve_poly([-1, 1], n**5 + n**3, n) == \
        C0 - n**3 / 2 - n**5 / 2 + n**2 / 6 + n**6 / 6 + 2*n**4 / 3


def test_rsolve_ratio():
    solution = rsolve_ratio([-2*n**3 + n**2 + 2*n - 1, 2*n**3 + n**2 - 6*n,
        -2*n**3 - 11*n**2 - 18*n - 9, 2*n**3 + 13*n**2 + 22*n + 8], 0, n)

    assert solution in [
        C1*((-2*n + 3)/(n**2 - 1))/3,
        (S(1)/2)*(C1*(-3 + 2*n)/(-1 + n**2)),
        (S(1)/2)*(C1*( 3 - 2*n)/( 1 - n**2)),
        (S(1)/2)*(C2*(-3 + 2*n)/(-1 + n**2)),
        (S(1)/2)*(C2*( 3 - 2*n)/( 1 - n**2)),
    ]


def test_rsolve_hyper():
    assert rsolve_hyper([-1, -1, 1], 0, n) in [
        C0*(S.Half - S.Half*sqrt(5))**n + C1*(S.Half + S.Half*sqrt(5))**n,
        C1*(S.Half - S.Half*sqrt(5))**n + C0*(S.Half + S.Half*sqrt(5))**n,
    ]

    assert rsolve_hyper([n**2 - 2, -2*n - 1, 1], 0, n) in [
        C0*rf(sqrt(2), n) + C1*rf(-sqrt(2), n),
        C1*rf(sqrt(2), n) + C0*rf(-sqrt(2), n),
    ]

    assert rsolve_hyper([n**2 - k, -2*n - 1, 1], 0, n) in [
        C0*rf(sqrt(k), n) + C1*rf(-sqrt(k), n),
        C1*rf(sqrt(k), n) + C0*rf(-sqrt(k), n),
    ]

    assert rsolve_hyper(
        [2*n*(n + 1), -n**2 - 3*n + 2, n - 1], 0, n) == C1*factorial(n) + C0*2**n

    assert rsolve_hyper(
        [n + 2, -(2*n + 3)*(17*n**2 + 51*n + 39), n + 1], 0, n) == None

    assert rsolve_hyper([-n - 1, -1, 1], 0, n) == None

    assert rsolve_hyper([-1, 1], n, n).expand() == C0 + n**2/2 - n/2

    assert rsolve_hyper([-1, 1], 1 + n, n).expand() == C0 + n**2/2 + n/2

    assert rsolve_hyper([-1, 1], 3*(n + n**2), n).expand() == C0 + n**3 - n

    assert rsolve_hyper([-a, 1],0,n).expand() == C0*a**n

    assert rsolve_hyper([-a, 0, 1], 0, n).expand() == (-1)**n*C1*a**(n/2) + C0*a**(n/2)

    assert rsolve_hyper([1, 1, 1], 0, n).expand() == \
        C0*(-S(1)/2 - sqrt(3)*I/2)**n + C1*(-S(1)/2 + sqrt(3)*I/2)**n

    assert rsolve_hyper([1, -2*n/a - 2/a, 1], 0, n) is None


def recurrence_term(c, f):
    """Compute RHS of recurrence in f(n) with coefficients in c."""
    return sum(c[i]*f.subs(n, n + i) for i in range(len(c)))


def test_rsolve_bulk():
    """Some bulk-generated tests."""
    funcs = [ n, n + 1, n**2, n**3, n**4, n + n**2, 27*n + 52*n**2 - 3*
        n**3 + 12*n**4 - 52*n**5 ]
    coeffs = [ [-2, 1], [-2, -1, 1], [-1, 1, 1, -1, 1], [-n, 1], [n**2 -
        n + 12, 1] ]
    for p in funcs:
        # compute difference
        for c in coeffs:
            q = recurrence_term(c, p)
            if p.is_polynomial(n):
                assert rsolve_poly(c, q, n) == p
            # See issue 3956:
            #if p.is_hypergeometric(n):
            #    assert rsolve_hyper(c, q, n) == p


def test_rsolve():
    f = y(n + 2) - y(n + 1) - y(n)
    h = sqrt(5)*(S.Half + S.Half*sqrt(5))**n \
        - sqrt(5)*(S.Half - S.Half*sqrt(5))**n

    assert rsolve(f, y(n)) in [
        C0*(S.Half - S.Half*sqrt(5))**n + C1*(S.Half + S.Half*sqrt(5))**n,
        C1*(S.Half - S.Half*sqrt(5))**n + C0*(S.Half + S.Half*sqrt(5))**n,
    ]

    assert rsolve(f, y(n), [0, 5]) == h
    assert rsolve(f, y(n), {0: 0, 1: 5}) == h
    assert rsolve(f, y(n), {y(0): 0, y(1): 5}) == h
    assert rsolve(y(n) - y(n - 1) - y(n - 2), y(n), [0, 5]) == h
    assert rsolve(Eq(y(n), y(n - 1) + y(n - 2)), y(n), [0, 5]) == h

    assert f.subs(y, Lambda(k, rsolve(f, y(n)).subs(n, k))).simplify() == 0

    f = (n - 1)*y(n + 2) - (n**2 + 3*n - 2)*y(n + 1) + 2*n*(n + 1)*y(n)
    g = C1*factorial(n) + C0*2**n
    h = -3*factorial(n) + 3*2**n

    assert rsolve(f, y(n)) == g
    assert rsolve(f, y(n), []) == g
    assert rsolve(f, y(n), {}) == g

    assert rsolve(f, y(n), [0, 3]) == h
    assert rsolve(f, y(n), {0: 0, 1: 3}) == h
    assert rsolve(f, y(n), {y(0): 0, y(1): 3}) == h

    assert f.subs(y, Lambda(k, rsolve(f, y(n)).subs(n, k))).simplify() == 0

    f = y(n) - y(n - 1) - 2

    assert rsolve(f, y(n), {y(0): 0}) == 2*n
    assert rsolve(f, y(n), {y(0): 1}) == 2*n + 1
    assert rsolve(f, y(n), {y(0): 0, y(1): 1}) is None

    assert f.subs(y, Lambda(k, rsolve(f, y(n)).subs(n, k))).simplify() == 0

    f = 3*y(n - 1) - y(n) - 1

    assert rsolve(f, y(n), {y(0): 0}) == -3**n/2 + S.Half
    assert rsolve(f, y(n), {y(0): 1}) == 3**n/2 + S.Half
    assert rsolve(f, y(n), {y(0): 2}) == 3*3**n/2 + S.Half

    assert f.subs(y, Lambda(k, rsolve(f, y(n)).subs(n, k))).simplify() == 0

    f = y(n) - 1/n*y(n - 1)
    assert rsolve(f, y(n)) == C0/factorial(n)
    assert f.subs(y, Lambda(k, rsolve(f, y(n)).subs(n, k))).simplify() == 0

    f = y(n) - 1/n*y(n - 1) - 1
    assert rsolve(f, y(n)) is None

    f = 2*y(n - 1) + (1 - n)*y(n)/n

    assert rsolve(f, y(n), {y(1): 1}) == 2**(n - 1)*n
    assert rsolve(f, y(n), {y(1): 2}) == 2**(n - 1)*n*2
    assert rsolve(f, y(n), {y(1): 3}) == 2**(n - 1)*n*3

    assert f.subs(y, Lambda(k, rsolve(f, y(n)).subs(n, k))).simplify() == 0

    f = (n - 1)*(n - 2)*y(n + 2) - (n + 1)*(n + 2)*y(n)

    assert rsolve(f, y(n), {y(3): 6, y(4): 24}) == n*(n - 1)*(n - 2)
    assert rsolve(
        f, y(n), {y(3): 6, y(4): -24}) == -n*(n - 1)*(n - 2)*(-1)**(n)

    assert f.subs(y, Lambda(k, rsolve(f, y(n)).subs(n, k))).simplify() == 0

    assert rsolve(Eq(y(n + 1), a*y(n)), y(n), {y(1): a}).simplify() == a**n

    assert rsolve(y(n) - a*y(n-2),y(n), \
            {y(1): sqrt(a)*(a + b), y(2): a*(a - b)}).simplify() == \
            a**(n/2)*(-(-1)**n*b + a)

    f = (-16*n**2 + 32*n - 12)*y(n - 1) + (4*n**2 - 12*n + 9)*y(n)

    assert expand_func(rsolve(f, y(n), \
            {y(1): binomial(2*n + 1, 3)}).rewrite(gamma)).simplify() == \
        2**(2*n)*n*(2*n - 1)*(4*n**2 - 1)/12

    assert (rsolve(y(n) + a*(y(n + 1) + y(n - 1))/2, y(n)) -
            (C0*((sqrt(-a**2 + 1) - 1)/a)**n +
             C1*((-sqrt(-a**2 + 1) - 1)/a)**n)).simplify() == 0

    assert rsolve((k + 1)*y(k), y(k)) is None
    assert (rsolve((k + 1)*y(k) + (k + 3)*y(k + 1) + (k + 5)*y(k + 2), y(k))
            is None)


def test_rsolve_raises():
    x = Function('x')
    raises(ValueError, lambda: rsolve(y(n) - y(k + 1), y(n)))
    raises(ValueError, lambda: rsolve(y(n) - y(n + 1), x(n)))
    raises(ValueError, lambda: rsolve(y(n) - x(n + 1), y(n)))
    raises(ValueError, lambda: rsolve(y(n) - sqrt(n)*y(n + 1), y(n)))
    raises(ValueError, lambda: rsolve(y(n) - y(n + 1), y(n), {x(0): 0}))


def test_issue_6844():
    f = y(n + 2) - y(n + 1) + y(n)/4
    assert rsolve(f, y(n)) == 2**(-n)*(C0 + C1*n)
    assert rsolve(f, y(n), {y(0): 0, y(1): 1}) == 2*2**(-n)*n


@slow
def test_issue_15751():
    f = y(n) + 21*y(n + 1) - 273*y(n + 2) - 1092*y(n + 3) + 1820*y(n + 4) + 1092*y(n + 5) - 273*y(n + 6) - 21*y(n + 7) + y(n + 8)
    assert rsolve(f, y(n)) is not None
