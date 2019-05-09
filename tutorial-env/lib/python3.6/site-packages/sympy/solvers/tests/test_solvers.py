from sympy import (
    Abs, And, Derivative, Dummy, Eq, Float, Function, Gt, I, Integral,
    LambertW, Lt, Matrix, Or, Poly, Q, Rational, S, Symbol, Ne,
    Wild, acos, asin, atan, atanh, cos, cosh, diff, erf, erfinv, erfc,
    erfcinv, exp, im, log, pi, re, sec, sin,
    sinh, solve, solve_linear, sqrt, sstr, symbols, sympify, tan, tanh,
    root, simplify, atan2, arg, Mul, SparseMatrix, ask, Tuple, nsolve, oo,
    E, cbrt, denom, Add)

from sympy.core.compatibility import range
from sympy.core.function import nfloat
from sympy.solvers import solve_linear_system, solve_linear_system_LU, \
    solve_undetermined_coeffs
from sympy.solvers.solvers import _invert, unrad, checksol, posify, _ispow, \
    det_quick, det_perm, det_minor, _simple_dens, check_assumptions, denoms, \
    failing_assumptions

from sympy.physics.units import cm
from sympy.polys.rootoftools import CRootOf

from sympy.utilities.pytest import slow, XFAIL, SKIP, raises, skip, ON_TRAVIS
from sympy.utilities.randtest import verify_numerically as tn

from sympy.abc import a, b, c, d, k, h, p, x, y, z, t, q, m


def NS(e, n=15, **options):
    return sstr(sympify(e).evalf(n, **options), full_prec=True)


def test_swap_back():
    f, g = map(Function, 'fg')
    fx, gx = f(x), g(x)
    assert solve([fx + y - 2, fx - gx - 5], fx, y, gx) == \
        {fx: gx + 5, y: -gx - 3}
    assert solve(fx + gx*x - 2, [fx, gx], dict=True)[0] == {fx: 2, gx: 0}
    assert solve(fx + gx**2*x - y, [fx, gx], dict=True) == [{fx: y - gx**2*x}]
    assert solve([f(1) - 2, x + 2], dict=True) == [{x: -2, f(1): 2}]


def guess_solve_strategy(eq, symbol):
    try:
        solve(eq, symbol)
        return True
    except (TypeError, NotImplementedError):
        return False


def test_guess_poly():
    # polynomial equations
    assert guess_solve_strategy( S(4), x )  # == GS_POLY
    assert guess_solve_strategy( x, x )  # == GS_POLY
    assert guess_solve_strategy( x + a, x )  # == GS_POLY
    assert guess_solve_strategy( 2*x, x )  # == GS_POLY
    assert guess_solve_strategy( x + sqrt(2), x)  # == GS_POLY
    assert guess_solve_strategy( x + 2**Rational(1, 4), x)  # == GS_POLY
    assert guess_solve_strategy( x**2 + 1, x )  # == GS_POLY
    assert guess_solve_strategy( x**2 - 1, x )  # == GS_POLY
    assert guess_solve_strategy( x*y + y, x )  # == GS_POLY
    assert guess_solve_strategy( x*exp(y) + y, x)  # == GS_POLY
    assert guess_solve_strategy(
        (x - y**3)/(y**2*sqrt(1 - y**2)), x)  # == GS_POLY


def test_guess_poly_cv():
    # polynomial equations via a change of variable
    assert guess_solve_strategy( sqrt(x) + 1, x )  # == GS_POLY_CV_1
    assert guess_solve_strategy(
        x**Rational(1, 3) + sqrt(x) + 1, x )  # == GS_POLY_CV_1
    assert guess_solve_strategy( 4*x*(1 - sqrt(x)), x )  # == GS_POLY_CV_1

    # polynomial equation multiplying both sides by x**n
    assert guess_solve_strategy( x + 1/x + y, x )  # == GS_POLY_CV_2


def test_guess_rational_cv():
    # rational functions
    assert guess_solve_strategy( (x + 1)/(x**2 + 2), x)  # == GS_RATIONAL
    assert guess_solve_strategy(
        (x - y**3)/(y**2*sqrt(1 - y**2)), y)  # == GS_RATIONAL_CV_1

    # rational functions via the change of variable y -> x**n
    assert guess_solve_strategy( (sqrt(x) + 1)/(x**Rational(1, 3) + sqrt(x) + 1), x ) \
        #== GS_RATIONAL_CV_1


def test_guess_transcendental():
    #transcendental functions
    assert guess_solve_strategy( exp(x) + 1, x )  # == GS_TRANSCENDENTAL
    assert guess_solve_strategy( 2*cos(x) - y, x )  # == GS_TRANSCENDENTAL
    assert guess_solve_strategy(
        exp(x) + exp(-x) - y, x )  # == GS_TRANSCENDENTAL
    assert guess_solve_strategy(3**x - 10, x)  # == GS_TRANSCENDENTAL
    assert guess_solve_strategy(-3**x + 10, x)  # == GS_TRANSCENDENTAL

    assert guess_solve_strategy(a*x**b - y, x)  # == GS_TRANSCENDENTAL


def test_solve_args():
    # equation container, issue 5113
    ans = {x: -3, y: 1}
    eqs = (x + 5*y - 2, -3*x + 6*y - 15)
    assert all(solve(container(eqs), x, y) == ans for container in
        (tuple, list, set, frozenset))
    assert solve(Tuple(*eqs), x, y) == ans
    # implicit symbol to solve for
    assert set(solve(x**2 - 4)) == set([S(2), -S(2)])
    assert solve([x + y - 3, x - y - 5]) == {x: 4, y: -1}
    assert solve(x - exp(x), x, implicit=True) == [exp(x)]
    # no symbol to solve for
    assert solve(42) == solve(42, x) == []
    assert solve([1, 2]) == []
    # duplicate symbols removed
    assert solve((x - 3, y + 2), x, y, x) == {x: 3, y: -2}
    # unordered symbols
    # only 1
    assert solve(y - 3, set([y])) == [3]
    # more than 1
    assert solve(y - 3, set([x, y])) == [{y: 3}]
    # multiple symbols: take the first linear solution+
    # - return as tuple with values for all requested symbols
    assert solve(x + y - 3, [x, y]) == [(3 - y, y)]
    # - unless dict is True
    assert solve(x + y - 3, [x, y], dict=True) == [{x: 3 - y}]
    # - or no symbols are given
    assert solve(x + y - 3) == [{x: 3 - y}]
    # multiple symbols might represent an undetermined coefficients system
    assert solve(a + b*x - 2, [a, b]) == {a: 2, b: 0}
    args = (a + b)*x - b**2 + 2, a, b
    assert solve(*args) == \
        [(-sqrt(2), sqrt(2)), (sqrt(2), -sqrt(2))]
    assert solve(*args, set=True) == \
        ([a, b], set([(-sqrt(2), sqrt(2)), (sqrt(2), -sqrt(2))]))
    assert solve(*args, dict=True) == \
        [{b: sqrt(2), a: -sqrt(2)}, {b: -sqrt(2), a: sqrt(2)}]
    eq = a*x**2 + b*x + c - ((x - h)**2 + 4*p*k)/4/p
    flags = dict(dict=True)
    assert solve(eq, [h, p, k], exclude=[a, b, c], **flags) == \
        [{k: c - b**2/(4*a), h: -b/(2*a), p: 1/(4*a)}]
    flags.update(dict(simplify=False))
    assert solve(eq, [h, p, k], exclude=[a, b, c], **flags) == \
        [{k: (4*a*c - b**2)/(4*a), h: -b/(2*a), p: 1/(4*a)}]
    # failing undetermined system
    assert solve(a*x + b**2/(x + 4) - 3*x - 4/x, a, b, dict=True) == \
        [{a: (-b**2*x + 3*x**3 + 12*x**2 + 4*x + 16)/(x**2*(x + 4))}]
    # failed single equation
    assert solve(1/(1/x - y + exp(y))) == []
    raises(
        NotImplementedError, lambda: solve(exp(x) + sin(x) + exp(y) + sin(y)))
    # failed system
    # --  when no symbols given, 1 fails
    assert solve([y, exp(x) + x]) == [{x: -LambertW(1), y: 0}]
    #     both fail
    assert solve(
        (exp(x) - x, exp(y) - y)) == [{x: -LambertW(-1), y: -LambertW(-1)}]
    # --  when symbols given
    solve([y, exp(x) + x], x, y) == [(-LambertW(1), 0)]
    # symbol is a number
    assert solve(x**2 - pi, pi) == [x**2]
    # no equations
    assert solve([], [x]) == []
    # overdetermined system
    # - nonlinear
    assert solve([(x + y)**2 - 4, x + y - 2]) == [{x: -y + 2}]
    # - linear
    assert solve((x + y - 2, 2*x + 2*y - 4)) == {x: -y + 2}
    # When one or more args are Boolean
    assert solve([True, Eq(x, 0)], [x], dict=True) == [{x: 0}]
    assert solve([Eq(x, x), Eq(x, 0), Eq(x, x+1)], [x], dict=True) == []
    assert not solve([Eq(x, x+1), x < 2], x)
    assert solve([Eq(x, 0), x+1<2]) == Eq(x, 0)
    assert solve([Eq(x, x), Eq(x, x+1)], x) == []
    assert solve(True, x) == []
    assert solve([x-1, False], [x], set=True) == ([], set())


def test_solve_polynomial1():
    assert solve(3*x - 2, x) == [Rational(2, 3)]
    assert solve(Eq(3*x, 2), x) == [Rational(2, 3)]

    assert set(solve(x**2 - 1, x)) == set([-S(1), S(1)])
    assert set(solve(Eq(x**2, 1), x)) == set([-S(1), S(1)])

    assert solve(x - y**3, x) == [y**3]
    rx = root(x, 3)
    assert solve(x - y**3, y) == [
        rx, -rx/2 - sqrt(3)*I*rx/2, -rx/2 +  sqrt(3)*I*rx/2]
    a11, a12, a21, a22, b1, b2 = symbols('a11,a12,a21,a22,b1,b2')

    assert solve([a11*x + a12*y - b1, a21*x + a22*y - b2], x, y) == \
        {
            x: (a22*b1 - a12*b2)/(a11*a22 - a12*a21),
            y: (a11*b2 - a21*b1)/(a11*a22 - a12*a21),
        }

    solution = {y: S.Zero, x: S.Zero}

    assert solve((x - y, x + y), x, y ) == solution
    assert solve((x - y, x + y), (x, y)) == solution
    assert solve((x - y, x + y), [x, y]) == solution

    assert set(solve(x**3 - 15*x - 4, x)) == set([
        -2 + 3**Rational(1, 2),
        S(4),
        -2 - 3**Rational(1, 2)
    ])

    assert set(solve((x**2 - 1)**2 - a, x)) == \
        set([sqrt(1 + sqrt(a)), -sqrt(1 + sqrt(a)),
             sqrt(1 - sqrt(a)), -sqrt(1 - sqrt(a))])


def test_solve_polynomial2():
    assert solve(4, x) == []


def test_solve_polynomial_cv_1a():
    """
    Test for solving on equations that can be converted to a polynomial equation
    using the change of variable y -> x**Rational(p, q)
    """
    assert solve( sqrt(x) - 1, x) == [1]
    assert solve( sqrt(x) - 2, x) == [4]
    assert solve( x**Rational(1, 4) - 2, x) == [16]
    assert solve( x**Rational(1, 3) - 3, x) == [27]
    assert solve(sqrt(x) + x**Rational(1, 3) + x**Rational(1, 4), x) == [0]


def test_solve_polynomial_cv_1b():
    assert set(solve(4*x*(1 - a*sqrt(x)), x)) == set([S(0), 1/a**2])
    assert set(solve(x*(root(x, 3) - 3), x)) == set([S(0), S(27)])


def test_solve_polynomial_cv_2():
    """
    Test for solving on equations that can be converted to a polynomial equation
    multiplying both sides of the equation by x**m
    """
    assert solve(x + 1/x - 1, x) in \
        [[ Rational(1, 2) + I*sqrt(3)/2, Rational(1, 2) - I*sqrt(3)/2],
         [ Rational(1, 2) - I*sqrt(3)/2, Rational(1, 2) + I*sqrt(3)/2]]


def test_quintics_1():
    f = x**5 - 110*x**3 - 55*x**2 + 2310*x + 979
    s = solve(f, check=False)
    for root in s:
        res = f.subs(x, root.n()).n()
        assert tn(res, 0)

    f = x**5 - 15*x**3 - 5*x**2 + 10*x + 20
    s = solve(f)
    for root in s:
        assert root.func == CRootOf

    # if one uses solve to get the roots of a polynomial that has a CRootOf
    # solution, make sure that the use of nfloat during the solve process
    # doesn't fail. Note: if you want numerical solutions to a polynomial
    # it is *much* faster to use nroots to get them than to solve the
    # equation only to get RootOf solutions which are then numerically
    # evaluated. So for eq = x**5 + 3*x + 7 do Poly(eq).nroots() rather
    # than [i.n() for i in solve(eq)] to get the numerical roots of eq.
    assert nfloat(solve(x**5 + 3*x**3 + 7)[0], exponent=False) == \
        CRootOf(x**5 + 3*x**3 + 7, 0).n()


def test_highorder_poly():
    # just testing that the uniq generator is unpacked
    sol = solve(x**6 - 2*x + 2)
    assert all(isinstance(i, CRootOf) for i in sol) and len(sol) == 6


def test_quintics_2():
    f = x**5 + 15*x + 12
    s = solve(f, check=False)
    for root in s:
        res = f.subs(x, root.n()).n()
        assert tn(res, 0)

    f = x**5 - 15*x**3 - 5*x**2 + 10*x + 20
    s = solve(f)
    for root in s:
        assert root.func == CRootOf


def test_solve_rational():
    """Test solve for rational functions"""
    assert solve( ( x - y**3 )/( (y**2)*sqrt(1 - y**2) ), x) == [y**3]


def test_solve_nonlinear():
    assert solve(x**2 - y**2, x, y, dict=True) == [{x: -y}, {x: y}]
    assert solve(x**2 - y**2/exp(x), x, y, dict=True) == [{x: 2*LambertW(y/2)}]
    assert solve(x**2 - y**2/exp(x), y, x, dict=True) == [{y: -x*sqrt(exp(x))},
                                                          {y: x*sqrt(exp(x))}]


def test_issue_8666():
    x = symbols('x')
    assert solve(Eq(x**2 - 1/(x**2 - 4), 4 - 1/(x**2 - 4)), x) == []
    assert solve(Eq(x + 1/x, 1/x), x) == []


def test_issue_7228():
    assert solve(4**(2*(x**2) + 2*x) - 8, x) == [-Rational(3, 2), S.Half]


def test_issue_7190():
    assert solve(log(x-3) + log(x+3), x) == [sqrt(10)]


def test_linear_system():
    x, y, z, t, n = symbols('x, y, z, t, n')

    assert solve([x - 1, x - y, x - 2*y, y - 1], [x, y]) == []

    assert solve([x - 1, x - y, x - 2*y, x - 1], [x, y]) == []
    assert solve([x - 1, x - 1, x - y, x - 2*y], [x, y]) == []

    assert solve([x + 5*y - 2, -3*x + 6*y - 15], x, y) == {x: -3, y: 1}

    M = Matrix([[0, 0, n*(n + 1), (n + 1)**2, 0],
                [n + 1, n + 1, -2*n - 1, -(n + 1), 0],
                [-1, 0, 1, 0, 0]])

    assert solve_linear_system(M, x, y, z, t) == \
        {x: -t - t/n, z: -t - t/n, y: 0}

    assert solve([x + y + z + t, -z - t], x, y, z, t) == {x: -y, z: -t}


def test_linear_system_function():
    a = Function('a')
    assert solve([a(0, 0) + a(0, 1) + a(1, 0) + a(1, 1), -a(1, 0) - a(1, 1)],
        a(0, 0), a(0, 1), a(1, 0), a(1, 1)) == {a(1, 0): -a(1, 1), a(0, 0): -a(0, 1)}


def test_linear_systemLU():
    n = Symbol('n')

    M = Matrix([[1, 2, 0, 1], [1, 3, 2*n, 1], [4, -1, n**2, 1]])

    assert solve_linear_system_LU(M, [x, y, z]) == {z: -3/(n**2 + 18*n),
                                                  x: 1 - 12*n/(n**2 + 18*n),
                                                  y: 6*n/(n**2 + 18*n)}

# Note: multiple solutions exist for some of these equations, so the tests
# should be expected to break if the implementation of the solver changes
# in such a way that a different branch is chosen

@slow
def test_solve_transcendental():
    from sympy.abc import a, b

    assert solve(exp(x) - 3, x) == [log(3)]
    assert set(solve((a*x + b)*(exp(x) - 3), x)) == set([-b/a, log(3)])
    assert solve(cos(x) - y, x) == [-acos(y) + 2*pi, acos(y)]
    assert solve(2*cos(x) - y, x) == [-acos(y/2) + 2*pi, acos(y/2)]
    assert solve(Eq(cos(x), sin(x)), x) == [-3*pi/4, pi/4]

    assert set(solve(exp(x) + exp(-x) - y, x)) in [set([
        log(y/2 - sqrt(y**2 - 4)/2),
        log(y/2 + sqrt(y**2 - 4)/2),
    ]), set([
        log(y - sqrt(y**2 - 4)) - log(2),
        log(y + sqrt(y**2 - 4)) - log(2)]),
    set([
        log(y/2 - sqrt((y - 2)*(y + 2))/2),
        log(y/2 + sqrt((y - 2)*(y + 2))/2)])]
    assert solve(exp(x) - 3, x) == [log(3)]
    assert solve(Eq(exp(x), 3), x) == [log(3)]
    assert solve(log(x) - 3, x) == [exp(3)]
    assert solve(sqrt(3*x) - 4, x) == [Rational(16, 3)]
    assert solve(3**(x + 2), x) == []
    assert solve(3**(2 - x), x) == []
    assert solve(x + 2**x, x) == [-LambertW(log(2))/log(2)]
    ans = solve(3*x + 5 + 2**(-5*x + 3), x)
    assert len(ans) == 1 and ans[0].expand() == \
        -Rational(5, 3) + LambertW(-10240*root(2, 3)*log(2)/3)/(5*log(2))
    assert solve(5*x - 1 + 3*exp(2 - 7*x), x) == \
        [Rational(1, 5) + LambertW(-21*exp(Rational(3, 5))/5)/7]
    assert solve(2*x + 5 + log(3*x - 2), x) == \
        [Rational(2, 3) + LambertW(2*exp(-Rational(19, 3))/3)/2]
    assert solve(3*x + log(4*x), x) == [LambertW(Rational(3, 4))/3]
    assert set(solve((2*x + 8)*(8 + exp(x)), x)) == set([S(-4), log(8) + pi*I])
    eq = 2*exp(3*x + 4) - 3
    ans = solve(eq, x)  # this generated a failure in flatten
    assert len(ans) == 3 and all(eq.subs(x, a).n(chop=True) == 0 for a in ans)
    assert solve(2*log(3*x + 4) - 3, x) == [(exp(Rational(3, 2)) - 4)/3]
    assert solve(exp(x) + 1, x) == [pi*I]

    eq = 2*(3*x + 4)**5 - 6*7**(3*x + 9)
    result = solve(eq, x)
    ans = [(log(2401) + 5*LambertW(-log(7**(7*3**Rational(1, 5)/5))))/(3*log(7))/-1]
    assert result == ans
    # it works if expanded, too
    assert solve(eq.expand(), x) == result

    assert solve(z*cos(x) - y, x) == [-acos(y/z) + 2*pi, acos(y/z)]
    assert solve(z*cos(2*x) - y, x) == [-acos(y/z)/2 + pi, acos(y/z)/2]
    assert solve(z*cos(sin(x)) - y, x) == [
        pi - asin(acos(y/z)), asin(acos(y/z) - 2*pi) + pi,
        -asin(acos(y/z) - 2*pi), asin(acos(y/z))]

    assert solve(z*cos(x), x) == [pi/2, 3*pi/2]

    # issue 4508
    assert solve(y - b*x/(a + x), x) in [[-a*y/(y - b)], [a*y/(b - y)]]
    assert solve(y - b*exp(a/x), x) == [a/log(y/b)]
    # issue 4507
    assert solve(y - b/(1 + a*x), x) in [[(b - y)/(a*y)], [-((y - b)/(a*y))]]
    # issue 4506
    assert solve(y - a*x**b, x) == [(y/a)**(1/b)]
    # issue 4505
    assert solve(z**x - y, x) == [log(y)/log(z)]
    # issue 4504
    assert solve(2**x - 10, x) == [log(10)/log(2)]
    # issue 6744
    assert solve(x*y) == [{x: 0}, {y: 0}]
    assert solve([x*y]) == [{x: 0}, {y: 0}]
    assert solve(x**y - 1) == [{x: 1}, {y: 0}]
    assert solve([x**y - 1]) == [{x: 1}, {y: 0}]
    assert solve(x*y*(x**2 - y**2)) == [{x: 0}, {x: -y}, {x: y}, {y: 0}]
    assert solve([x*y*(x**2 - y**2)]) == [{x: 0}, {x: -y}, {x: y}, {y: 0}]
    # issue 4739
    assert solve(exp(log(5)*x) - 2**x, x) == [0]
    # issue 14791
    assert solve(exp(log(5)*x) - exp(log(2)*x), x) == [0]
    f = Function('f')
    assert solve(y*f(log(5)*x) - y*f(log(2)*x), x) == [0]
    assert solve(f(x) - f(0), x) == [0]
    assert solve(f(x) - f(2 - x), x) == [1]
    raises(NotImplementedError, lambda: solve(f(x, y) - f(1, 2), x))
    raises(NotImplementedError, lambda: solve(f(x, y) - f(2 - x, 2), x))
    raises(ValueError, lambda: solve(f(x, y) - f(1 - x), x))
    raises(ValueError, lambda: solve(f(x, y) - f(1), x))

    # misc
    # make sure that the right variables is picked up in tsolve
    # shouldn't generate a GeneratorsNeeded error in _tsolve when the NaN is generated
    # for eq_down. Actual answers, as determined numerically are approx. +/- 0.83
    raises(NotImplementedError, lambda:
        solve(sinh(x)*sinh(sinh(x)) + cosh(x)*cosh(sinh(x)) - 3))

    # watch out for recursive loop in tsolve
    raises(NotImplementedError, lambda: solve((x + 2)**y*x - 3, x))

    # issue 7245
    assert solve(sin(sqrt(x))) == [0, pi**2]

    # issue 7602
    a, b = symbols('a, b', real=True, negative=False)
    assert str(solve(Eq(a, 0.5 - cos(pi*b)/2), b)) == \
        '[2.0 - 0.318309886183791*acos(1.0 - 2.0*a), 0.318309886183791*acos(1.0 - 2.0*a)]'

    # issue 15325
    assert solve(y**(1/x) - z, x) == [log(y)/log(z)]


def test_solve_for_functions_derivatives():
    t = Symbol('t')
    x = Function('x')(t)
    y = Function('y')(t)
    a11, a12, a21, a22, b1, b2 = symbols('a11,a12,a21,a22,b1,b2')

    soln = solve([a11*x + a12*y - b1, a21*x + a22*y - b2], x, y)
    assert soln == {
        x: (a22*b1 - a12*b2)/(a11*a22 - a12*a21),
        y: (a11*b2 - a21*b1)/(a11*a22 - a12*a21),
    }

    assert solve(x - 1, x) == [1]
    assert solve(3*x - 2, x) == [Rational(2, 3)]

    soln = solve([a11*x.diff(t) + a12*y.diff(t) - b1, a21*x.diff(t) +
            a22*y.diff(t) - b2], x.diff(t), y.diff(t))
    assert soln == { y.diff(t): (a11*b2 - a21*b1)/(a11*a22 - a12*a21),
            x.diff(t): (a22*b1 - a12*b2)/(a11*a22 - a12*a21) }

    assert solve(x.diff(t) - 1, x.diff(t)) == [1]
    assert solve(3*x.diff(t) - 2, x.diff(t)) == [Rational(2, 3)]

    eqns = set((3*x - 1, 2*y - 4))
    assert solve(eqns, set((x, y))) == { x: Rational(1, 3), y: 2 }
    x = Symbol('x')
    f = Function('f')
    F = x**2 + f(x)**2 - 4*x - 1
    assert solve(F.diff(x), diff(f(x), x)) == [(-x + 2)/f(x)]

    # Mixed cased with a Symbol and a Function
    x = Symbol('x')
    y = Function('y')(t)

    soln = solve([a11*x + a12*y.diff(t) - b1, a21*x +
            a22*y.diff(t) - b2], x, y.diff(t))
    assert soln == { y.diff(t): (a11*b2 - a21*b1)/(a11*a22 - a12*a21),
            x: (a22*b1 - a12*b2)/(a11*a22 - a12*a21) }


def test_issue_3725():
    f = Function('f')
    F = x**2 + f(x)**2 - 4*x - 1
    e = F.diff(x)
    assert solve(e, f(x).diff(x)) in [[(2 - x)/f(x)], [-((x - 2)/f(x))]]


def test_issue_3870():
    a, b, c, d = symbols('a b c d')
    A = Matrix(2, 2, [a, b, c, d])
    B = Matrix(2, 2, [0, 2, -3, 0])
    C = Matrix(2, 2, [1, 2, 3, 4])

    assert solve(A*B - C, [a, b, c, d]) == {a: 1, b: -S(1)/3, c: 2, d: -1}
    assert solve([A*B - C], [a, b, c, d]) == {a: 1, b: -S(1)/3, c: 2, d: -1}
    assert solve(Eq(A*B, C), [a, b, c, d]) == {a: 1, b: -S(1)/3, c: 2, d: -1}

    assert solve([A*B - B*A], [a, b, c, d]) == {a: d, b: -S(2)/3*c}
    assert solve([A*C - C*A], [a, b, c, d]) == {a: d - c, b: S(2)/3*c}
    assert solve([A*B - B*A, A*C - C*A], [a, b, c, d]) == {a: d, b: 0, c: 0}

    assert solve([Eq(A*B, B*A)], [a, b, c, d]) == {a: d, b: -S(2)/3*c}
    assert solve([Eq(A*C, C*A)], [a, b, c, d]) == {a: d - c, b: S(2)/3*c}
    assert solve([Eq(A*B, B*A), Eq(A*C, C*A)], [a, b, c, d]) == {a: d, b: 0, c: 0}


def test_solve_linear():
    w = Wild('w')
    assert solve_linear(x, x) == (0, 1)
    assert solve_linear(x, exclude=[x]) == (0, 1)
    assert solve_linear(x, symbols=[w]) == (0, 1)
    assert solve_linear(x, y - 2*x) in [(x, y/3), (y, 3*x)]
    assert solve_linear(x, y - 2*x, exclude=[x]) == (y, 3*x)
    assert solve_linear(3*x - y, 0) in [(x, y/3), (y, 3*x)]
    assert solve_linear(3*x - y, 0, [x]) == (x, y/3)
    assert solve_linear(3*x - y, 0, [y]) == (y, 3*x)
    assert solve_linear(x**2/y, 1) == (y, x**2)
    assert solve_linear(w, x) in [(w, x), (x, w)]
    assert solve_linear(cos(x)**2 + sin(x)**2 + 2 + y) == \
        (y, -2 - cos(x)**2 - sin(x)**2)
    assert solve_linear(cos(x)**2 + sin(x)**2 + 2 + y, symbols=[x]) == (0, 1)
    assert solve_linear(Eq(x, 3)) == (x, 3)
    assert solve_linear(1/(1/x - 2)) == (0, 0)
    assert solve_linear((x + 1)*exp(-x), symbols=[x]) == (x, -1)
    assert solve_linear((x + 1)*exp(x), symbols=[x]) == ((x + 1)*exp(x), 1)
    assert solve_linear(x*exp(-x**2), symbols=[x]) == (x, 0)
    assert solve_linear(0**x - 1) == (0**x - 1, 1)
    assert solve_linear(1 + 1/(x - 1)) == (x, 0)
    eq = y*cos(x)**2 + y*sin(x)**2 - y  # = y*(1 - 1) = 0
    assert solve_linear(eq) == (0, 1)
    eq = cos(x)**2 + sin(x)**2  # = 1
    assert solve_linear(eq) == (0, 1)
    raises(ValueError, lambda: solve_linear(Eq(x, 3), 3))


def test_solve_undetermined_coeffs():
    assert solve_undetermined_coeffs(a*x**2 + b*x**2 + b*x + 2*c*x + c + 1, [a, b, c], x) == \
        {a: -2, b: 2, c: -1}
    # Test that rational functions work
    assert solve_undetermined_coeffs(a/x + b/(x + 1) - (2*x + 1)/(x**2 + x), [a, b], x) == \
        {a: 1, b: 1}
    # Test cancellation in rational functions
    assert solve_undetermined_coeffs(((c + 1)*a*x**2 + (c + 1)*b*x**2 +
    (c + 1)*b*x + (c + 1)*2*c*x + (c + 1)**2)/(c + 1), [a, b, c], x) == \
        {a: -2, b: 2, c: -1}


def test_solve_inequalities():
    x = Symbol('x')
    sol = And(S(0) < x, x < oo)
    assert solve(x + 1 > 1) == sol
    assert solve([x + 1 > 1]) == sol
    assert solve([x + 1 > 1], x) == sol
    assert solve([x + 1 > 1], [x]) == sol

    system = [Lt(x**2 - 2, 0), Gt(x**2 - 1, 0)]
    assert solve(system) == \
        And(Or(And(Lt(-sqrt(2), x), Lt(x, -1)),
               And(Lt(1, x), Lt(x, sqrt(2)))), Eq(0, 0))

    x = Symbol('x', real=True)
    system = [Lt(x**2 - 2, 0), Gt(x**2 - 1, 0)]
    assert solve(system) == \
        Or(And(Lt(-sqrt(2), x), Lt(x, -1)), And(Lt(1, x), Lt(x, sqrt(2))))

    # issues 6627, 3448
    assert solve((x - 3)/(x - 2) < 0, x) == And(Lt(2, x), Lt(x, 3))
    assert solve(x/(x + 1) > 1, x) == And(Lt(-oo, x), Lt(x, -1))

    assert solve(sin(x) > S.Half) == And(pi/6 < x, x < 5*pi/6)

    assert solve(Eq(False, x < 1)) == (S(1) <= x) & (x < oo)
    assert solve(Eq(True, x < 1)) == (-oo < x) & (x < 1)
    assert solve(Eq(x < 1, False)) == (S(1) <= x) & (x < oo)
    assert solve(Eq(x < 1, True)) == (-oo < x) & (x < 1)

    assert solve(Eq(False, x)) == False
    assert solve(Eq(True, x)) == True
    assert solve(Eq(False, ~x)) == True
    assert solve(Eq(True, ~x)) == False
    assert solve(Ne(True, x)) == False


def test_issue_4793():
    assert solve(1/x) == []
    assert solve(x*(1 - 5/x)) == [5]
    assert solve(x + sqrt(x) - 2) == [1]
    assert solve(-(1 + x)/(2 + x)**2 + 1/(2 + x)) == []
    assert solve(-x**2 - 2*x + (x + 1)**2 - 1) == []
    assert solve((x/(x + 1) + 3)**(-2)) == []
    assert solve(x/sqrt(x**2 + 1), x) == [0]
    assert solve(exp(x) - y, x) == [log(y)]
    assert solve(exp(x)) == []
    assert solve(x**2 + x + sin(y)**2 + cos(y)**2 - 1, x) in [[0, -1], [-1, 0]]
    eq = 4*3**(5*x + 2) - 7
    ans = solve(eq, x)
    assert len(ans) == 5 and all(eq.subs(x, a).n(chop=True) == 0 for a in ans)
    assert solve(log(x**2) - y**2/exp(x), x, y, set=True) == (
        [x, y],
        {(x, sqrt(exp(x) * log(x ** 2))), (x, -sqrt(exp(x) * log(x ** 2)))})
    assert solve(x**2*z**2 - z**2*y**2) == [{x: -y}, {x: y}, {z: 0}]
    assert solve((x - 1)/(1 + 1/(x - 1))) == []
    assert solve(x**(y*z) - x, x) == [1]
    raises(NotImplementedError, lambda: solve(log(x) - exp(x), x))
    raises(NotImplementedError, lambda: solve(2**x - exp(x) - 3))


def test_PR1964():
    # issue 5171
    assert solve(sqrt(x)) == solve(sqrt(x**3)) == [0]
    assert solve(sqrt(x - 1)) == [1]
    # issue 4462
    a = Symbol('a')
    assert solve(-3*a/sqrt(x), x) == []
    # issue 4486
    assert solve(2*x/(x + 2) - 1, x) == [2]
    # issue 4496
    assert set(solve((x**2/(7 - x)).diff(x))) == set([S(0), S(14)])
    # issue 4695
    f = Function('f')
    assert solve((3 - 5*x/f(x))*f(x), f(x)) == [5*x/3]
    # issue 4497
    assert solve(1/root(5 + x, 5) - 9, x) == [-295244/S(59049)]

    assert solve(sqrt(x) + sqrt(sqrt(x)) - 4) == [(-S.Half + sqrt(17)/2)**4]
    assert set(solve(Poly(sqrt(exp(x)) + sqrt(exp(-x)) - 4))) in \
        [
            set([log((-sqrt(3) + 2)**2), log((sqrt(3) + 2)**2)]),
            set([2*log(-sqrt(3) + 2), 2*log(sqrt(3) + 2)]),
            set([log(-4*sqrt(3) + 7), log(4*sqrt(3) + 7)]),
        ]
    assert set(solve(Poly(exp(x) + exp(-x) - 4))) == \
        set([log(-sqrt(3) + 2), log(sqrt(3) + 2)])
    assert set(solve(x**y + x**(2*y) - 1, x)) == \
        set([(-S.Half + sqrt(5)/2)**(1/y), (-S.Half - sqrt(5)/2)**(1/y)])

    assert solve(exp(x/y)*exp(-z/y) - 2, y) == [(x - z)/log(2)]
    assert solve(
        x**z*y**z - 2, z) in [[log(2)/(log(x) + log(y))], [log(2)/(log(x*y))]]
    # if you do inversion too soon then multiple roots (as for the following)
    # will be missed, e.g. if exp(3*x) = exp(3) -> 3*x = 3
    E = S.Exp1
    assert solve(exp(3*x) - exp(3), x) in [
        [1, log(E*(-S.Half - sqrt(3)*I/2)), log(E*(-S.Half + sqrt(3)*I/2))],
        [1, log(-E/2 - sqrt(3)*E*I/2), log(-E/2 + sqrt(3)*E*I/2)],
        ]

    # coverage test
    p = Symbol('p', positive=True)
    assert solve((1/p + 1)**(p + 1)) == []


def test_issue_5197():
    x = Symbol('x', real=True)
    assert solve(x**2 + 1, x) == []
    n = Symbol('n', integer=True, positive=True)
    assert solve((n - 1)*(n + 2)*(2*n - 1), n) == [1]
    x = Symbol('x', positive=True)
    y = Symbol('y')
    assert solve([x + 5*y - 2, -3*x + 6*y - 15], x, y) == []
                 # not {x: -3, y: 1} b/c x is positive
    # The solution following should not contain (-sqrt(2), sqrt(2))
    assert solve((x + y)*n - y**2 + 2, x, y) == [(sqrt(2), -sqrt(2))]
    y = Symbol('y', positive=True)
    # The solution following should not contain {y: -x*exp(x/2)}
    assert solve(x**2 - y**2/exp(x), y, x, dict=True) == [{y: x*exp(x/2)}]
    assert solve(x**2 - y**2/exp(x), x, y, dict=True) == [{x: 2*LambertW(y/2)}]
    x, y, z = symbols('x y z', positive=True)
    assert solve(z**2*x**2 - z**2*y**2/exp(x), y, x, z, dict=True) == [{y: x*exp(x/2)}]


def test_checking():
    assert set(
        solve(x*(x - y/x), x, check=False)) == set([sqrt(y), S(0), -sqrt(y)])
    assert set(solve(x*(x - y/x), x, check=True)) == set([sqrt(y), -sqrt(y)])
    # {x: 0, y: 4} sets denominator to 0 in the following so system should return None
    assert solve((1/(1/x + 2), 1/(y - 3) - 1)) == []
    # 0 sets denominator of 1/x to zero so None is returned
    assert solve(1/(1/x + 2)) == []


def test_issue_4671_4463_4467():
    assert solve((sqrt(x**2 - 1) - 2)) in ([sqrt(5), -sqrt(5)],
                                           [-sqrt(5), sqrt(5)])
    # This is probably better than the form below but equivalent:
    #assert solve((2**exp(y**2/x) + 2)/(x**2 + 15), y) == [-sqrt(x*log(1 + I*pi/log(2)))
    #                                                    , sqrt(x*log(1 + I*pi/log(2)))]
    assert solve((2**exp(y**2/x) + 2)/(x**2 + 15), y) == [
         sqrt(x*(-log(log(2)) + log(log(2) + I*pi))),
        -sqrt(-x*(log(log(2)) - log(log(2) + I*pi)))]

    C1, C2 = symbols('C1 C2')
    f = Function('f')
    assert solve(C1 + C2/x**2 - exp(-f(x)), f(x)) == [log(x**2/(C1*x**2 + C2))]
    a = Symbol('a')
    E = S.Exp1
    assert solve(1 - log(a + 4*x**2), x) in (
        [-sqrt(-a + E)/2, sqrt(-a + E)/2],
        [sqrt(-a + E)/2, -sqrt(-a + E)/2]
    )
    assert solve(log(a**(-3) - x**2)/a, x) in (
        [-sqrt(-1 + a**(-3)), sqrt(-1 + a**(-3))],
        [sqrt(-1 + a**(-3)), -sqrt(-1 + a**(-3))],)
    assert solve(1 - log(a + 4*x**2), x) in (
        [-sqrt(-a + E)/2, sqrt(-a + E)/2],
        [sqrt(-a + E)/2, -sqrt(-a + E)/2],)
    assert set(solve((
        a**2 + 1) * (sin(a*x) + cos(a*x)), x)) == set([-pi/(4*a), 3*pi/(4*a)])
    assert solve(3 - (sinh(a*x) + cosh(a*x)), x) == [log(3)/a]
    assert set(solve(3 - (sinh(a*x) + cosh(a*x)**2), x)) == \
        set([log(-2 + sqrt(5))/a, log(-sqrt(2) + 1)/a,
        log(-sqrt(5) - 2)/a, log(1 + sqrt(2))/a])
    assert solve(atan(x) - 1) == [tan(1)]


def test_issue_5132():
    r, t = symbols('r,t')
    assert set(solve([r - x**2 - y**2, tan(t) - y/x], [x, y])) == \
        set([(
            -sqrt(r*cos(t)**2), -1*sqrt(r*cos(t)**2)*tan(t)),
            (sqrt(r*cos(t)**2), sqrt(r*cos(t)**2)*tan(t))])
    assert solve([exp(x) - sin(y), 1/y - 3], [x, y]) == \
        [(log(sin(S(1)/3)), S(1)/3)]
    assert solve([exp(x) - sin(y), 1/exp(y) - 3], [x, y]) == \
        [(log(-sin(log(3))), -log(3))]
    assert set(solve([exp(x) - sin(y), y**2 - 4], [x, y])) == \
        set([(log(-sin(2)), -S(2)), (log(sin(2)), S(2))])
    eqs = [exp(x)**2 - sin(y) + z**2, 1/exp(y) - 3]
    assert solve(eqs, set=True) == \
        ([x, y], set([
        (log(-sqrt(-z**2 - sin(log(3)))), -log(3)),
        (log(-z**2 - sin(log(3)))/2, -log(3))]))
    assert solve(eqs, x, z, set=True) == (
        [x, z],
        {(log(-z**2 + sin(y))/2, z), (log(-sqrt(-z**2 + sin(y))), z)})
    assert set(solve(eqs, x, y)) == \
        set([
            (log(-sqrt(-z**2 - sin(log(3)))), -log(3)),
        (log(-z**2 - sin(log(3)))/2, -log(3))])
    assert set(solve(eqs, y, z)) == \
        set([
            (-log(3), -sqrt(-exp(2*x) - sin(log(3)))),
        (-log(3), sqrt(-exp(2*x) - sin(log(3))))])
    eqs = [exp(x)**2 - sin(y) + z, 1/exp(y) - 3]
    assert solve(eqs, set=True) == ([x, y], set(
        [
        (log(-sqrt(-z - sin(log(3)))), -log(3)),
            (log(-z - sin(log(3)))/2, -log(3))]))
    assert solve(eqs, x, z, set=True) == (
        [x, z],
        {(log(-sqrt(-z + sin(y))), z), (log(-z + sin(y))/2, z)})
    assert set(solve(eqs, x, y)) == set(
        [
            (log(-sqrt(-z - sin(log(3)))), -log(3)),
            (log(-z - sin(log(3)))/2, -log(3))])
    assert solve(eqs, z, y) == \
        [(-exp(2*x) - sin(log(3)), -log(3))]
    assert solve((sqrt(x**2 + y**2) - sqrt(10), x + y - 4), set=True) == (
        [x, y], set([(S(1), S(3)), (S(3), S(1))]))
    assert set(solve((sqrt(x**2 + y**2) - sqrt(10), x + y - 4), x, y)) == \
        set([(S(1), S(3)), (S(3), S(1))])


def test_issue_5335():
    lam, a0, conc = symbols('lam a0 conc')
    a = 0.005
    b = 0.743436700916726
    eqs = [lam + 2*y - a0*(1 - x/2)*x - a*x/2*x,
           a0*(1 - x/2)*x - 1*y - b*y,
           x + y - conc]
    sym = [x, y, a0]
    # there are 4 solutions obtained manually but only two are valid
    assert len(solve(eqs, sym, manual=True, minimal=True)) == 2
    assert len(solve(eqs, sym)) == 2  # cf below with rational=False


@SKIP("Hangs")
def _test_issue_5335_float():
    # gives ZeroDivisionError: polynomial division
    lam, a0, conc = symbols('lam a0 conc')
    a = 0.005
    b = 0.743436700916726
    eqs = [lam + 2*y - a0*(1 - x/2)*x - a*x/2*x,
           a0*(1 - x/2)*x - 1*y - b*y,
           x + y - conc]
    sym = [x, y, a0]
    assert len(solve(eqs, sym, rational=False)) == 2


def test_issue_5767():
    assert set(solve([x**2 + y + 4], [x])) == \
        set([(-sqrt(-y - 4),), (sqrt(-y - 4),)])


def test_polysys():
    assert set(solve([x**2 + 2/y - 2, x + y - 3], [x, y])) == \
        set([(S(1), S(2)), (1 + sqrt(5), 2 - sqrt(5)),
        (1 - sqrt(5), 2 + sqrt(5))])
    assert solve([x**2 + y - 2, x**2 + y]) == []
    # the ordering should be whatever the user requested
    assert solve([x**2 + y - 3, x - y - 4], (x, y)) != solve([x**2 +
                 y - 3, x - y - 4], (y, x))


@slow
def test_unrad1():
    raises(NotImplementedError, lambda:
        unrad(sqrt(x) + sqrt(x + 1) + sqrt(1 - sqrt(x)) + 3))
    raises(NotImplementedError, lambda:
        unrad(sqrt(x) + (x + 1)**Rational(1, 3) + 2*sqrt(y)))

    s = symbols('s', cls=Dummy)

    # checkers to deal with possibility of answer coming
    # back with a sign change (cf issue 5203)
    def check(rv, ans):
        assert bool(rv[1]) == bool(ans[1])
        if ans[1]:
            return s_check(rv, ans)
        e = rv[0].expand()
        a = ans[0].expand()
        return e in [a, -a] and rv[1] == ans[1]

    def s_check(rv, ans):
        # get the dummy
        rv = list(rv)
        d = rv[0].atoms(Dummy)
        reps = list(zip(d, [s]*len(d)))
        # replace s with this dummy
        rv = (rv[0].subs(reps).expand(), [rv[1][0].subs(reps), rv[1][1].subs(reps)])
        ans = (ans[0].subs(reps).expand(), [ans[1][0].subs(reps), ans[1][1].subs(reps)])
        return str(rv[0]) in [str(ans[0]), str(-ans[0])] and \
            str(rv[1]) == str(ans[1])

    assert check(unrad(sqrt(x)),
        (x, []))
    assert check(unrad(sqrt(x) + 1),
        (x - 1, []))
    assert check(unrad(sqrt(x) + root(x, 3) + 2),
        (s**3 + s**2 + 2, [s, s**6 - x]))
    assert check(unrad(sqrt(x)*root(x, 3) + 2),
        (x**5 - 64, []))
    assert check(unrad(sqrt(x) + (x + 1)**Rational(1, 3)),
        (x**3 - (x + 1)**2, []))
    assert check(unrad(sqrt(x) + sqrt(x + 1) + sqrt(2*x)),
        (-2*sqrt(2)*x - 2*x + 1, []))
    assert check(unrad(sqrt(x) + sqrt(x + 1) + 2),
        (16*x - 9, []))
    assert check(unrad(sqrt(x) + sqrt(x + 1) + sqrt(1 - x)),
        (5*x**2 - 4*x, []))
    assert check(unrad(a*sqrt(x) + b*sqrt(x) + c*sqrt(y) + d*sqrt(y)),
        ((a*sqrt(x) + b*sqrt(x))**2 - (c*sqrt(y) + d*sqrt(y))**2, []))
    assert check(unrad(sqrt(x) + sqrt(1 - x)),
        (2*x - 1, []))
    assert check(unrad(sqrt(x) + sqrt(1 - x) - 3),
        (x**2 - x + 16, []))
    assert check(unrad(sqrt(x) + sqrt(1 - x) + sqrt(2 + x)),
        (5*x**2 - 2*x + 1, []))
    assert unrad(sqrt(x) + sqrt(1 - x) + sqrt(2 + x) - 3) in [
        (25*x**4 + 376*x**3 + 1256*x**2 - 2272*x + 784, []),
        (25*x**8 - 476*x**6 + 2534*x**4 - 1468*x**2 + 169, [])]
    assert unrad(sqrt(x) + sqrt(1 - x) + sqrt(2 + x) - sqrt(1 - 2*x)) == \
        (41*x**4 + 40*x**3 + 232*x**2 - 160*x + 16, [])  # orig root at 0.487
    assert check(unrad(sqrt(x) + sqrt(x + 1)), (S(1), []))

    eq = sqrt(x) + sqrt(x + 1) + sqrt(1 - sqrt(x))
    assert check(unrad(eq),
        (16*x**2 - 9*x, []))
    assert set(solve(eq, check=False)) == set([S(0), S(9)/16])
    assert solve(eq) == []
    # but this one really does have those solutions
    assert set(solve(sqrt(x) - sqrt(x + 1) + sqrt(1 - sqrt(x)))) == \
        set([S.Zero, S(9)/16])

    assert check(unrad(sqrt(x) + root(x + 1, 3) + 2*sqrt(y), y),
        (S('2*sqrt(x)*(x + 1)**(1/3) + x - 4*y + (x + 1)**(2/3)'), []))
    assert check(unrad(sqrt(x/(1 - x)) + (x + 1)**Rational(1, 3)),
        (x**5 - x**4 - x**3 + 2*x**2 + x - 1, []))
    assert check(unrad(sqrt(x/(1 - x)) + 2*sqrt(y), y),
        (4*x*y + x - 4*y, []))
    assert check(unrad(sqrt(x)*sqrt(1 - x) + 2, x),
        (x**2 - x + 4, []))

    # http://tutorial.math.lamar.edu/
    #        Classes/Alg/SolveRadicalEqns.aspx#Solve_Rad_Ex2_a
    assert solve(Eq(x, sqrt(x + 6))) == [3]
    assert solve(Eq(x + sqrt(x - 4), 4)) == [4]
    assert solve(Eq(1, x + sqrt(2*x - 3))) == []
    assert set(solve(Eq(sqrt(5*x + 6) - 2, x))) == set([-S(1), S(2)])
    assert set(solve(Eq(sqrt(2*x - 1) - sqrt(x - 4), 2))) == set([S(5), S(13)])
    assert solve(Eq(sqrt(x + 7) + 2, sqrt(3 - x))) == [-6]
    # http://www.purplemath.com/modules/solverad.htm
    assert solve((2*x - 5)**Rational(1, 3) - 3) == [16]
    assert set(solve(x + 1 - root(x**4 + 4*x**3 - x, 4))) == \
        set([-S(1)/2, -S(1)/3])
    assert set(solve(sqrt(2*x**2 - 7) - (3 - x))) == set([-S(8), S(2)])
    assert solve(sqrt(2*x + 9) - sqrt(x + 1) - sqrt(x + 4)) == [0]
    assert solve(sqrt(x + 4) + sqrt(2*x - 1) - 3*sqrt(x - 1)) == [5]
    assert solve(sqrt(x)*sqrt(x - 7) - 12) == [16]
    assert solve(sqrt(x - 3) + sqrt(x) - 3) == [4]
    assert solve(sqrt(9*x**2 + 4) - (3*x + 2)) == [0]
    assert solve(sqrt(x) - 2 - 5) == [49]
    assert solve(sqrt(x - 3) - sqrt(x) - 3) == []
    assert solve(sqrt(x - 1) - x + 7) == [10]
    assert solve(sqrt(x - 2) - 5) == [27]
    assert solve(sqrt(17*x - sqrt(x**2 - 5)) - 7) == [3]
    assert solve(sqrt(x) - sqrt(x - 1) + sqrt(sqrt(x))) == []

    # don't posify the expression in unrad and do use _mexpand
    z = sqrt(2*x + 1)/sqrt(x) - sqrt(2 + 1/x)
    p = posify(z)[0]
    assert solve(p) == []
    assert solve(z) == []
    assert solve(z + 6*I) == [-S(1)/11]
    assert solve(p + 6*I) == []
    # issue 8622
    assert unrad((root(x + 1, 5) - root(x, 3))) == (
        x**5 - x**3 - 3*x**2 - 3*x - 1, [])
    # issue #8679
    assert check(unrad(x + root(x, 3) + root(x, 3)**2 + sqrt(y), x),
        (s**3 + s**2 + s + sqrt(y), [s, s**3 - x]))

    # for coverage
    assert check(unrad(sqrt(x) + root(x, 3) + y),
        (s**3 + s**2 + y, [s, s**6 - x]))
    assert solve(sqrt(x) + root(x, 3) - 2) == [1]
    raises(NotImplementedError, lambda:
        solve(sqrt(x) + root(x, 3) + root(x + 1, 5) - 2))
    # fails through a different code path
    raises(NotImplementedError, lambda: solve(-sqrt(2) + cosh(x)/x))
    # unrad some
    assert solve(sqrt(x + root(x, 3))+root(x - y, 5), y) == [
        x + (x**(S(1)/3) + x)**(S(5)/2)]
    assert check(unrad(sqrt(x) - root(x + 1, 3)*sqrt(x + 2) + 2),
        (s**10 + 8*s**8 + 24*s**6 - 12*s**5 - 22*s**4 - 160*s**3 - 212*s**2 -
        192*s - 56, [s, s**2 - x]))
    e = root(x + 1, 3) + root(x, 3)
    assert unrad(e) == (2*x + 1, [])
    eq = (sqrt(x) + sqrt(x + 1) + sqrt(1 - x) - 6*sqrt(5)/5)
    assert check(unrad(eq),
        (15625*x**4 + 173000*x**3 + 355600*x**2 - 817920*x + 331776, []))
    assert check(unrad(root(x, 4) + root(x, 4)**3 - 1),
        (s**3 + s - 1, [s, s**4 - x]))
    assert check(unrad(root(x, 2) + root(x, 2)**3 - 1),
        (x**3 + 2*x**2 + x - 1, []))
    assert unrad(x**0.5) is None
    assert check(unrad(t + root(x + y, 5) + root(x + y, 5)**3),
        (s**3 + s + t, [s, s**5 - x - y]))
    assert check(unrad(x + root(x + y, 5) + root(x + y, 5)**3, y),
        (s**3 + s + x, [s, s**5 - x - y]))
    assert check(unrad(x + root(x + y, 5) + root(x + y, 5)**3, x),
        (s**5 + s**3 + s - y, [s, s**5 - x - y]))
    assert check(unrad(root(x - 1, 3) + root(x + 1, 5) + root(2, 5)),
        (s**5 + 5*2**(S(1)/5)*s**4 + s**3 + 10*2**(S(2)/5)*s**3 +
        10*2**(S(3)/5)*s**2 + 5*2**(S(4)/5)*s + 4, [s, s**3 - x + 1]))
    raises(NotImplementedError, lambda:
        unrad((root(x, 2) + root(x, 3) + root(x, 4)).subs(x, x**5 - x + 1)))

    # the simplify flag should be reset to False for unrad results;
    # if it's not then this next test will take a long time
    assert solve(root(x, 3) + root(x, 5) - 2) == [1]
    eq = (sqrt(x) + sqrt(x + 1) + sqrt(1 - x) - 6*sqrt(5)/5)
    assert check(unrad(eq),
        ((5*x - 4)*(3125*x**3 + 37100*x**2 + 100800*x - 82944), []))
    ans = S('''
        [4/5, -1484/375 + 172564/(140625*(114*sqrt(12657)/78125 +
        12459439/52734375)**(1/3)) +
        4*(114*sqrt(12657)/78125 + 12459439/52734375)**(1/3)]''')
    assert solve(eq) == ans
    # duplicate radical handling
    assert check(unrad(sqrt(x + root(x + 1, 3)) - root(x + 1, 3) - 2),
        (s**3 - s**2 - 3*s - 5, [s, s**3 - x - 1]))
    # cov post-processing
    e = root(x**2 + 1, 3) - root(x**2 - 1, 5) - 2
    assert check(unrad(e),
        (s**5 - 10*s**4 + 39*s**3 - 80*s**2 + 80*s - 30,
        [s, s**3 - x**2 - 1]))

    e = sqrt(x + root(x + 1, 2)) - root(x + 1, 3) - 2
    assert check(unrad(e),
        (s**6 - 2*s**5 - 7*s**4 - 3*s**3 + 26*s**2 + 40*s + 25,
        [s, s**3 - x - 1]))
    assert check(unrad(e, _reverse=True),
        (s**6 - 14*s**5 + 73*s**4 - 187*s**3 + 276*s**2 - 228*s + 89,
        [s, s**2 - x - sqrt(x + 1)]))
    # this one needs r0, r1 reversal to work
    assert check(unrad(sqrt(x + sqrt(root(x, 3) - 1)) - root(x, 6) - 2),
        (s**12 - 2*s**8 - 8*s**7 - 8*s**6 + s**4 + 8*s**3 + 23*s**2 +
        32*s + 17, [s, s**6 - x]))

    # is this needed?
    #assert unrad(root(cosh(x), 3)/x*root(x + 1, 5) - 1) == (
    #    x**15 - x**3*cosh(x)**5 - 3*x**2*cosh(x)**5 - 3*x*cosh(x)**5 - cosh(x)**5, [])
    raises(NotImplementedError, lambda:
        unrad(sqrt(cosh(x)/x) + root(x + 1,3)*sqrt(x) - 1))
    assert unrad(S('(x+y)**(2*y/3) + (x+y)**(1/3) + 1')) is None
    assert check(unrad(S('(x+y)**(2*y/3) + (x+y)**(1/3) + 1'), x),
        (s**(2*y) + s + 1, [s, s**3 - x - y]))

    # This tests two things: that if full unrad is attempted and fails
    # the solution should still be found; also it tests that the use of
    # composite
    assert len(solve(sqrt(y)*x + x**3 - 1, x)) == 3
    assert len(solve(-512*y**3 + 1344*(x + 2)**(S(1)/3)*y**2 -
        1176*(x + 2)**(S(2)/3)*y - 169*x + 686, y, _unrad=False)) == 3

    # watch out for when the cov doesn't involve the symbol of interest
    eq = S('-x + (7*y/8 - (27*x/2 + 27*sqrt(x**2)/2)**(1/3)/3)**3 - 1')
    assert solve(eq, y) == [
        4*2**(S(2)/3)*(27*x + 27*sqrt(x**2))**(S(1)/3)/21 - (-S(1)/2 -
        sqrt(3)*I/2)*(-6912*x/343 + sqrt((-13824*x/343 - S(13824)/343)**2)/2 -
        S(6912)/343)**(S(1)/3)/3, 4*2**(S(2)/3)*(27*x + 27*sqrt(x**2))**(S(1)/3)/21 -
        (-S(1)/2 + sqrt(3)*I/2)*(-6912*x/343 + sqrt((-13824*x/343 -
        S(13824)/343)**2)/2 - S(6912)/343)**(S(1)/3)/3, 4*2**(S(2)/3)*(27*x +
        27*sqrt(x**2))**(S(1)/3)/21 - (-6912*x/343 + sqrt((-13824*x/343 -
        S(13824)/343)**2)/2 - S(6912)/343)**(S(1)/3)/3]

    eq = root(x + 1, 3) - (root(x, 3) + root(x, 5))
    assert check(unrad(eq),
        (3*s**13 + 3*s**11 + s**9 - 1, [s, s**15 - x]))
    assert check(unrad(eq - 2),
        (3*s**13 + 3*s**11 + 6*s**10 + s**9 + 12*s**8 + 6*s**6 + 12*s**5 +
        12*s**3 + 7, [s, s**15 - x]))
    assert check(unrad(root(x, 3) - root(x + 1, 4)/2 + root(x + 2, 3)),
        (4096*s**13 + 960*s**12 + 48*s**11 - s**10 - 1728*s**4,
        [s, s**4 - x - 1]))  # orig expr has two real roots: -1, -.389
    assert check(unrad(root(x, 3) + root(x + 1, 4) - root(x + 2, 3)/2),
        (343*s**13 + 2904*s**12 + 1344*s**11 + 512*s**10 - 1323*s**9 -
        3024*s**8 - 1728*s**7 + 1701*s**5 + 216*s**4 - 729*s, [s, s**4 - x -
        1]))  # orig expr has one real root: -0.048
    assert check(unrad(root(x, 3)/2 - root(x + 1, 4) + root(x + 2, 3)),
        (729*s**13 - 216*s**12 + 1728*s**11 - 512*s**10 + 1701*s**9 -
        3024*s**8 + 1344*s**7 + 1323*s**5 - 2904*s**4 + 343*s, [s, s**4 - x -
        1]))  # orig expr has 2 real roots: -0.91, -0.15
    assert check(unrad(root(x, 3)/2 - root(x + 1, 4) + root(x + 2, 3) - 2),
        (729*s**13 + 1242*s**12 + 18496*s**10 + 129701*s**9 + 388602*s**8 +
        453312*s**7 - 612864*s**6 - 3337173*s**5 - 6332418*s**4 - 7134912*s**3
        - 5064768*s**2 - 2111913*s - 398034, [s, s**4 - x - 1]))
        # orig expr has 1 real root: 19.53

    ans = solve(sqrt(x) + sqrt(x + 1) -
                sqrt(1 - x) - sqrt(2 + x))
    assert len(ans) == 1 and NS(ans[0])[:4] == '0.73'
    # the fence optimization problem
    # https://github.com/sympy/sympy/issues/4793#issuecomment-36994519
    F = Symbol('F')
    eq = F - (2*x + 2*y + sqrt(x**2 + y**2))
    ans = 2*F/7 - sqrt(2)*F/14
    X = solve(eq, x, check=False)
    for xi in reversed(X):  # reverse since currently, ans is the 2nd one
        Y = solve((x*y).subs(x, xi).diff(y), y, simplify=False, check=False)
        if any((a - ans).expand().is_zero for a in Y):
            break
    else:
        assert None  # no answer was found
    assert solve(sqrt(x + 1) + root(x, 3) - 2) == S('''
        [(-11/(9*(47/54 + sqrt(93)/6)**(1/3)) + 1/3 + (47/54 +
        sqrt(93)/6)**(1/3))**3]''')
    assert solve(sqrt(sqrt(x + 1)) + x**Rational(1, 3) - 2) == S('''
        [(-sqrt(-2*(-1/16 + sqrt(6913)/16)**(1/3) + 6/(-1/16 +
        sqrt(6913)/16)**(1/3) + 17/2 + 121/(4*sqrt(-6/(-1/16 +
        sqrt(6913)/16)**(1/3) + 2*(-1/16 + sqrt(6913)/16)**(1/3) + 17/4)))/2 +
        sqrt(-6/(-1/16 + sqrt(6913)/16)**(1/3) + 2*(-1/16 +
        sqrt(6913)/16)**(1/3) + 17/4)/2 + 9/4)**3]''')
    assert solve(sqrt(x) + root(sqrt(x) + 1, 3) - 2) == S('''
        [(-(81/2 + 3*sqrt(741)/2)**(1/3)/3 + (81/2 + 3*sqrt(741)/2)**(-1/3) +
        2)**2]''')
    eq = S('''
        -x + (1/2 - sqrt(3)*I/2)*(3*x**3/2 - x*(3*x**2 - 34)/2 + sqrt((-3*x**3
        + x*(3*x**2 - 34) + 90)**2/4 - 39304/27) - 45)**(1/3) + 34/(3*(1/2 -
        sqrt(3)*I/2)*(3*x**3/2 - x*(3*x**2 - 34)/2 + sqrt((-3*x**3 + x*(3*x**2
        - 34) + 90)**2/4 - 39304/27) - 45)**(1/3))''')
    assert check(unrad(eq),
        (-s*(-s**6 + sqrt(3)*s**6*I - 153*2**(S(2)/3)*3**(S(1)/3)*s**4 +
        51*12**(S(1)/3)*s**4 - 102*2**(S(2)/3)*3**(S(5)/6)*s**4*I - 1620*s**3 +
        1620*sqrt(3)*s**3*I + 13872*18**(S(1)/3)*s**2 - 471648 +
        471648*sqrt(3)*I), [s, s**3 - 306*x - sqrt(3)*sqrt(31212*x**2 -
        165240*x + 61484) + 810]))

    assert solve(eq) == [] # not other code errors


@slow
def test_unrad_slow():
    # this has roots with multiplicity > 1; there should be no
    # repeats in roots obtained, however
    eq = (sqrt(1 + sqrt(1 - 4*x**2)) - x*((1 + sqrt(1 + 2*sqrt(1 - 4*x**2)))))
    assert solve(eq) == [S.Half]


@XFAIL
def test_unrad_fail():
    # this only works if we check real_root(eq.subs(x, S(1)/3))
    # but checksol doesn't work like that
    assert solve(root(x**3 - 3*x**2, 3) + 1 - x) == [S(1)/3]
    assert solve(root(x + 1, 3) + root(x**2 - 2, 5) + 1) == [
        -1, -1 + CRootOf(x**5 + x**4 + 5*x**3 + 8*x**2 + 10*x + 5, 0)**3]


def test_checksol():
    x, y, r, t = symbols('x, y, r, t')
    eq = r - x**2 - y**2
    dict_var_soln = {y: - sqrt(r) / sqrt(tan(t)**2 + 1),
        x: -sqrt(r)*tan(t)/sqrt(tan(t)**2 + 1)}
    assert checksol(eq, dict_var_soln) == True
    assert checksol(Eq(x, False), {x: False}) is True
    assert checksol(Ne(x, False), {x: False}) is False
    assert checksol(Eq(x < 1, True), {x: 0}) is True
    assert checksol(Eq(x < 1, True), {x: 1}) is False
    assert checksol(Eq(x < 1, False), {x: 1}) is True
    assert checksol(Eq(x < 1, False), {x: 0}) is False
    assert checksol(Eq(x + 1, x**2 + 1), {x: 1}) is True
    assert checksol([x - 1, x**2 - 1], x, 1) is True
    assert checksol([x - 1, x**2 - 2], x, 1) is False
    assert checksol(Poly(x**2 - 1), x, 1) is True
    raises(ValueError, lambda: checksol(x, 1))
    raises(ValueError, lambda: checksol([], x, 1))

def test__invert():
    assert _invert(x - 2) == (2, x)
    assert _invert(2) == (2, 0)
    assert _invert(exp(1/x) - 3, x) == (1/log(3), x)
    assert _invert(exp(1/x + a/x) - 3, x) == ((a + 1)/log(3), x)
    assert _invert(a, x) == (a, 0)


def test_issue_4463():
    assert solve(-a*x + 2*x*log(x), x) == [exp(a/2)]
    assert solve(a/x + exp(x/2), x) == [2*LambertW(-a/2)]
    assert solve(x**x) == []
    assert solve(x**x - 2) == [exp(LambertW(log(2)))]
    assert solve(((x - 3)*(x - 2))**((x - 3)*(x - 4))) == [2]
    assert solve(
        (a/x + exp(x/2)).diff(x), x) == [4*LambertW(sqrt(2)*sqrt(a)/4)]

@slow
def test_issue_5114_solvers():
    a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r = symbols('a:r')

    # there is no 'a' in the equation set but this is how the
    # problem was originally posed
    syms = a, b, c, f, h, k, n
    eqs = [b + r/d - c/d,
    c*(1/d + 1/e + 1/g) - f/g - r/d,
        f*(1/g + 1/i + 1/j) - c/g - h/i,
        h*(1/i + 1/l + 1/m) - f/i - k/m,
        k*(1/m + 1/o + 1/p) - h/m - n/p,
        n*(1/p + 1/q) - k/p]
    assert len(solve(eqs, syms, manual=True, check=False, simplify=False)) == 1


def test_issue_5849():
    I1, I2, I3, I4, I5, I6 = symbols('I1:7')
    dI1, dI4, dQ2, dQ4, Q2, Q4 = symbols('dI1,dI4,dQ2,dQ4,Q2,Q4')

    e = (
        I1 - I2 - I3,
        I3 - I4 - I5,
        I4 + I5 - I6,
        -I1 + I2 + I6,
        -2*I1 - 2*I3 - 2*I5 - 3*I6 - dI1/2 + 12,
        -I4 + dQ4,
        -I2 + dQ2,
        2*I3 + 2*I5 + 3*I6 - Q2,
        I4 - 2*I5 + 2*Q4 + dI4
    )

    ans = [{
           dQ4: I3 - I5,
    dI1: -4*I2 - 8*I3 - 4*I5 - 6*I6 + 24,
    I4: I3 - I5,
    dQ2: I2,
    Q2: 2*I3 + 2*I5 + 3*I6,
    I1: I2 + I3,
    Q4: -I3/2 + 3*I5/2 - dI4/2}]
    v = I1, I4, Q2, Q4, dI1, dI4, dQ2, dQ4
    assert solve(e, *v, manual=True, check=False, dict=True) == ans
    assert solve(e, *v, manual=True) == []
    # the matrix solver (tested below) doesn't like this because it produces
    # a zero row in the matrix. Is this related to issue 4551?
    assert [ei.subs(
        ans[0]) for ei in e] == [0, 0, I3 - I6, -I3 + I6, 0, 0, 0, 0, 0]


def test_issue_5849_matrix():
    '''Same as test_2750 but solved with the matrix solver.'''
    I1, I2, I3, I4, I5, I6 = symbols('I1:7')
    dI1, dI4, dQ2, dQ4, Q2, Q4 = symbols('dI1,dI4,dQ2,dQ4,Q2,Q4')

    e = (
        I1 - I2 - I3,
        I3 - I4 - I5,
        I4 + I5 - I6,
        -I1 + I2 + I6,
        -2*I1 - 2*I3 - 2*I5 - 3*I6 - dI1/2 + 12,
        -I4 + dQ4,
        -I2 + dQ2,
        2*I3 + 2*I5 + 3*I6 - Q2,
        I4 - 2*I5 + 2*Q4 + dI4
    )
    assert solve(e, I1, I4, Q2, Q4, dI1, dI4, dQ2, dQ4) == {
        dI4: -I3 + 3*I5 - 2*Q4,
        dI1: -4*I2 - 8*I3 - 4*I5 - 6*I6 + 24,
        dQ2: I2,
        I1: I2 + I3,
        Q2: 2*I3 + 2*I5 + 3*I6,
        dQ4: I3 - I5,
        I4: I3 - I5}


def test_issue_5901():
    f, g, h = map(Function, 'fgh')
    a = Symbol('a')
    D = Derivative(f(x), x)
    G = Derivative(g(a), a)
    assert solve(f(x) + f(x).diff(x), f(x)) == \
        [-D]
    assert solve(f(x) - 3, f(x)) == \
        [3]
    assert solve(f(x) - 3*f(x).diff(x), f(x)) == \
        [3*D]
    assert solve([f(x) - 3*f(x).diff(x)], f(x)) == \
        {f(x): 3*D}
    assert solve([f(x) - 3*f(x).diff(x), f(x)**2 - y + 4], f(x), y) == \
        [{f(x): 3*D, y: 9*D**2 + 4}]
    assert solve(-f(a)**2*g(a)**2 + f(a)**2*h(a)**2 + g(a).diff(a),
                h(a), g(a), set=True) == \
        ([g(a)], set([
        (-sqrt(h(a)**2*f(a)**2 + G)/f(a),),
        (sqrt(h(a)**2*f(a)**2+ G)/f(a),)]))
    args = [f(x).diff(x, 2)*(f(x) + g(x)) - g(x)**2 + 2, f(x), g(x)]
    assert set(solve(*args)) == \
        set([(-sqrt(2), sqrt(2)), (sqrt(2), -sqrt(2))])
    eqs = [f(x)**2 + g(x) - 2*f(x).diff(x), g(x)**2 - 4]
    assert solve(eqs, f(x), g(x), set=True) == \
        ([f(x), g(x)], set([
        (-sqrt(2*D - 2), S(2)),
        (sqrt(2*D - 2), S(2)),
        (-sqrt(2*D + 2), -S(2)),
        (sqrt(2*D + 2), -S(2))]))

    # the underlying problem was in solve_linear that was not masking off
    # anything but a Mul or Add; it now raises an error if it gets anything
    # but a symbol and solve handles the substitutions necessary so solve_linear
    # won't make this error
    raises(
        ValueError, lambda: solve_linear(f(x) + f(x).diff(x), symbols=[f(x)]))
    assert solve_linear(f(x) + f(x).diff(x), symbols=[x]) == \
        (f(x) + Derivative(f(x), x), 1)
    assert solve_linear(f(x) + Integral(x, (x, y)), symbols=[x]) == \
        (f(x) + Integral(x, (x, y)), 1)
    assert solve_linear(f(x) + Integral(x, (x, y)) + x, symbols=[x]) == \
        (x + f(x) + Integral(x, (x, y)), 1)
    assert solve_linear(f(y) + Integral(x, (x, y)) + x, symbols=[x]) == \
        (x, -f(y) - Integral(x, (x, y)))
    assert solve_linear(x - f(x)/a + (f(x) - 1)/a, symbols=[x]) == \
        (x, 1/a)
    assert solve_linear(x + Derivative(2*x, x)) == \
        (x, -2)
    assert solve_linear(x + Integral(x, y), symbols=[x]) == \
        (x, 0)
    assert solve_linear(x + Integral(x, y) - 2, symbols=[x]) == \
        (x, 2/(y + 1))

    assert set(solve(x + exp(x)**2, exp(x))) == \
        set([-sqrt(-x), sqrt(-x)])
    assert solve(x + exp(x), x, implicit=True) == \
        [-exp(x)]
    assert solve(cos(x) - sin(x), x, implicit=True) == []
    assert solve(x - sin(x), x, implicit=True) == \
        [sin(x)]
    assert solve(x**2 + x - 3, x, implicit=True) == \
        [-x**2 + 3]
    assert solve(x**2 + x - 3, x**2, implicit=True) == \
        [-x + 3]


def test_issue_5912():
    assert set(solve(x**2 - x - 0.1, rational=True)) == \
        set([S(1)/2 + sqrt(35)/10, -sqrt(35)/10 + S(1)/2])
    ans = solve(x**2 - x - 0.1, rational=False)
    assert len(ans) == 2 and all(a.is_Number for a in ans)
    ans = solve(x**2 - x - 0.1)
    assert len(ans) == 2 and all(a.is_Number for a in ans)


def test_float_handling():
    def test(e1, e2):
        return len(e1.atoms(Float)) == len(e2.atoms(Float))
    assert solve(x - 0.5, rational=True)[0].is_Rational
    assert solve(x - 0.5, rational=False)[0].is_Float
    assert solve(x - S.Half, rational=False)[0].is_Rational
    assert solve(x - 0.5, rational=None)[0].is_Float
    assert solve(x - S.Half, rational=None)[0].is_Rational
    assert test(nfloat(1 + 2*x), 1.0 + 2.0*x)
    for contain in [list, tuple, set]:
        ans = nfloat(contain([1 + 2*x]))
        assert type(ans) is contain and test(list(ans)[0], 1.0 + 2.0*x)
    k, v = list(nfloat({2*x: [1 + 2*x]}).items())[0]
    assert test(k, 2*x) and test(v[0], 1.0 + 2.0*x)
    assert test(nfloat(cos(2*x)), cos(2.0*x))
    assert test(nfloat(3*x**2), 3.0*x**2)
    assert test(nfloat(3*x**2, exponent=True), 3.0*x**2.0)
    assert test(nfloat(exp(2*x)), exp(2.0*x))
    assert test(nfloat(x/3), x/3.0)
    assert test(nfloat(x**4 + 2*x + cos(S(1)/3) + 1),
            x**4 + 2.0*x + 1.94495694631474)
    # don't call nfloat if there is no solution
    tot = 100 + c + z + t
    assert solve(((.7 + c)/tot - .6, (.2 + z)/tot - .3, t/tot - .1)) == []


def test_check_assumptions():
    x = symbols('x', positive=True)
    assert solve(x**2 - 1) == [1]
    assert check_assumptions(1, x) == True
    raises(AssertionError, lambda: check_assumptions(2*x, x, positive=True))
    raises(TypeError, lambda: check_assumptions(1, 1))


def test_failing_assumptions():
    x = Symbol('x', real=True, positive=True)
    y = Symbol('y')
    assert failing_assumptions(6*x + y, **x.assumptions0) == \
    {'real': None, 'imaginary': None, 'complex': None, 'hermitian': None,
    'positive': None, 'nonpositive': None, 'nonnegative': None, 'nonzero': None,
    'negative': None, 'zero': None}

def test_issue_6056():
    assert solve(tanh(x + 3)*tanh(x - 3) - 1) == []
    assert set([simplify(w) for w in solve(tanh(x - 1)*tanh(x + 1) + 1)]) == set([
        -log(2)/2 + log(1 - I),
        -log(2)/2 + log(-1 - I),
        -log(2)/2 + log(1 + I),
        -log(2)/2 + log(-1 + I),])
    assert set([simplify(w) for w in solve((tanh(x + 3)*tanh(x - 3) + 1)**2)]) == set([
        -log(2)/2 + log(1 - I),
        -log(2)/2 + log(-1 - I),
        -log(2)/2 + log(1 + I),
        -log(2)/2 + log(-1 + I),])


def test_issue_5673():
    eq = -x + exp(exp(LambertW(log(x)))*LambertW(log(x)))
    assert checksol(eq, x, 2) is True
    assert checksol(eq, x, 2, numerical=False) is None


def test_exclude():
    R, C, Ri, Vout, V1, Vminus, Vplus, s = \
        symbols('R, C, Ri, Vout, V1, Vminus, Vplus, s')
    Rf = symbols('Rf', positive=True)  # to eliminate Rf = 0 soln
    eqs = [C*V1*s + Vplus*(-2*C*s - 1/R),
           Vminus*(-1/Ri - 1/Rf) + Vout/Rf,
           C*Vplus*s + V1*(-C*s - 1/R) + Vout/R,
           -Vminus + Vplus]
    assert solve(eqs, exclude=s*C*R) == [
        {
            Rf: Ri*(C*R*s + 1)**2/(C*R*s),
            Vminus: Vplus,
            V1: 2*Vplus + Vplus/(C*R*s),
            Vout: C*R*Vplus*s + 3*Vplus + Vplus/(C*R*s)},
        {
            Vplus: 0,
            Vminus: 0,
            V1: 0,
            Vout: 0},
    ]

    # TODO: Investigate why currently solution [0] is preferred over [1].
    assert solve(eqs, exclude=[Vplus, s, C]) in [[{
        Vminus: Vplus,
        V1: Vout/2 + Vplus/2 + sqrt((Vout - 5*Vplus)*(Vout - Vplus))/2,
        R: (Vout - 3*Vplus - sqrt(Vout**2 - 6*Vout*Vplus + 5*Vplus**2))/(2*C*Vplus*s),
        Rf: Ri*(Vout - Vplus)/Vplus,
    }, {
        Vminus: Vplus,
        V1: Vout/2 + Vplus/2 - sqrt((Vout - 5*Vplus)*(Vout - Vplus))/2,
        R: (Vout - 3*Vplus + sqrt(Vout**2 - 6*Vout*Vplus + 5*Vplus**2))/(2*C*Vplus*s),
        Rf: Ri*(Vout - Vplus)/Vplus,
    }], [{
        Vminus: Vplus,
        Vout: (V1**2 - V1*Vplus - Vplus**2)/(V1 - 2*Vplus),
        Rf: Ri*(V1 - Vplus)**2/(Vplus*(V1 - 2*Vplus)),
        R: Vplus/(C*s*(V1 - 2*Vplus)),
    }]]


def test_high_order_roots():
    s = x**5 + 4*x**3 + 3*x**2 + S(7)/4
    assert set(solve(s)) == set(Poly(s*4, domain='ZZ').all_roots())


def test_minsolve_linear_system():
    def count(dic):
        return len([x for x in dic.values() if x == 0])
    assert count(solve([x + y + z, y + z + a + t], particular=True, quick=True)) \
        == 3
    assert count(solve([x + y + z, y + z + a + t], particular=True, quick=False)) \
        == 3
    assert count(solve([x + y + z, y + z + a], particular=True, quick=True)) == 1
    assert count(solve([x + y + z, y + z + a], particular=True, quick=False)) == 2


def test_real_roots():
    # cf. issue 6650
    x = Symbol('x', real=True)
    assert len(solve(x**5 + x**3 + 1)) == 1


def test_issue_6528():
    eqs = [
        327600995*x**2 - 37869137*x + 1809975124*y**2 - 9998905626,
        895613949*x**2 - 273830224*x*y + 530506983*y**2 - 10000000000]
    # two expressions encountered are > 1400 ops long so if this hangs
    # it is likely because simplification is being done
    assert len(solve(eqs, y, x, check=False)) == 4


def test_overdetermined():
    x = symbols('x', real=True)
    eqs = [Abs(4*x - 7) - 5, Abs(3 - 8*x) - 1]
    assert solve(eqs, x) == [(S.Half,)]
    assert solve(eqs, x, manual=True) == [(S.Half,)]
    assert solve(eqs, x, manual=True, check=False) == [(S.Half,), (S(3),)]


def test_issue_6605():
    x = symbols('x')
    assert solve(4**(x/2) - 2**(x/3)) == [0, 3*I*pi/log(2)]
    # while the first one passed, this one failed
    x = symbols('x', real=True)
    assert solve(5**(x/2) - 2**(x/3)) == [0]
    b = sqrt(6)*sqrt(log(2))/sqrt(log(5))
    assert solve(5**(x/2) - 2**(3/x)) == [-b, b]


def test__ispow():
    assert _ispow(x**2)
    assert not _ispow(x)
    assert not _ispow(True)


def test_issue_6644():
    eq = -sqrt((m - q)**2 + (-m/(2*q) + S(1)/2)**2) + sqrt((-m**2/2 - sqrt(
    4*m**4 - 4*m**2 + 8*m + 1)/4 - S(1)/4)**2 + (m**2/2 - m - sqrt(
    4*m**4 - 4*m**2 + 8*m + 1)/4 - S(1)/4)**2)
    sol = solve(eq, q, simplify=False, check=False)
    assert len(sol) == 5


def test_issue_6752():
    assert solve([a**2 + a, a - b], [a, b]) == [(-1, -1), (0, 0)]
    assert solve([a**2 + a*c, a - b], [a, b]) == [(0, 0), (-c, -c)]


def test_issue_6792():
    assert solve(x*(x - 1)**2*(x + 1)*(x**6 - x + 1)) == [
        -1, 0, 1, CRootOf(x**6 - x + 1, 0), CRootOf(x**6 - x + 1, 1),
         CRootOf(x**6 - x + 1, 2), CRootOf(x**6 - x + 1, 3),
         CRootOf(x**6 - x + 1, 4), CRootOf(x**6 - x + 1, 5)]


def test_issues_6819_6820_6821_6248_8692():
    # issue 6821
    x, y = symbols('x y', real=True)
    assert solve(abs(x + 3) - 2*abs(x - 3)) == [1, 9]
    assert solve([abs(x) - 2, arg(x) - pi], x) == [(-2,), (2,)]
    assert set(solve(abs(x - 7) - 8)) == set([-S(1), S(15)])

    # issue 8692
    assert solve(Eq(Abs(x + 1) + Abs(x**2 - 7), 9), x) == [
        -S(1)/2 + sqrt(61)/2, -sqrt(69)/2 + S(1)/2]

    # issue 7145
    assert solve(2*abs(x) - abs(x - 1)) == [-1, Rational(1, 3)]

    x = symbols('x')
    assert solve([re(x) - 1, im(x) - 2], x) == [
        {re(x): 1, x: 1 + 2*I, im(x): 2}]

    # check for 'dict' handling of solution
    eq = sqrt(re(x)**2 + im(x)**2) - 3
    assert solve(eq) == solve(eq, x)

    i = symbols('i', imaginary=True)
    assert solve(abs(i) - 3) == [-3*I, 3*I]
    raises(NotImplementedError, lambda: solve(abs(x) - 3))

    w = symbols('w', integer=True)
    assert solve(2*x**w - 4*y**w, w) == solve((x/y)**w - 2, w)

    x, y = symbols('x y', real=True)
    assert solve(x + y*I + 3) == {y: 0, x: -3}
    # issue 2642
    assert solve(x*(1 + I)) == [0]

    x, y = symbols('x y', imaginary=True)
    assert solve(x + y*I + 3 + 2*I) == {x: -2*I, y: 3*I}

    x = symbols('x', real=True)
    assert solve(x + y + 3 + 2*I) == {x: -3, y: -2*I}

    # issue 6248
    f = Function('f')
    assert solve(f(x + 1) - f(2*x - 1)) == [2]
    assert solve(log(x + 1) - log(2*x - 1)) == [2]

    x = symbols('x')
    assert solve(2**x + 4**x) == [I*pi/log(2)]


def test_issue_14607():
    # issue 14607
    s, tau_c, tau_1, tau_2, phi, K = symbols(
        's, tau_c, tau_1, tau_2, phi, K')

    target = (s**2*tau_1*tau_2 + s*tau_1 + s*tau_2 + 1)/(K*s*(-phi + tau_c))

    K_C, tau_I, tau_D = symbols('K_C, tau_I, tau_D',
                                positive=True, nonzero=True)
    PID = K_C*(1 + 1/(tau_I*s) + tau_D*s)

    eq = (target - PID).together()
    eq *= denom(eq).simplify()
    eq = Poly(eq, s)
    c = eq.coeffs()

    vars = [K_C, tau_I, tau_D]
    s = solve(c, vars, dict=True)

    assert len(s) == 1

    knownsolution = {K_C: -(tau_1 + tau_2)/(K*(phi - tau_c)),
                     tau_I: tau_1 + tau_2,
                     tau_D: tau_1*tau_2/(tau_1 + tau_2)}

    for var in vars:
        assert s[0][var].simplify() == knownsolution[var].simplify()


@slow
def test_lambert_multivariate():
    from sympy.abc import a, x, y
    from sympy.solvers.bivariate import _filtered_gens, _lambert, _solve_lambert

    assert _filtered_gens(Poly(x + 1/x + exp(x) + y), x) == set([x, exp(x)])
    assert _lambert(x, x) == []
    assert solve((x**2 - 2*x + 1).subs(x, log(x) + 3*x)) == [LambertW(3*S.Exp1)/3]
    assert solve((x**2 - 2*x + 1).subs(x, (log(x) + 3*x)**2 - 1)) == \
          [LambertW(3*exp(-sqrt(2)))/3, LambertW(3*exp(sqrt(2)))/3]
    assert solve((x**2 - 2*x - 2).subs(x, log(x) + 3*x)) == \
          [LambertW(3*exp(1 - sqrt(3)))/3, LambertW(3*exp(1 + sqrt(3)))/3]
    assert solve(x*log(x) + 3*x + 1, x) == [exp(-3 + LambertW(-exp(3)))]
    eq = (x*exp(x) - 3).subs(x, x*exp(x))
    assert solve(eq) == [LambertW(3*exp(-LambertW(3)))]
    # coverage test
    raises(NotImplementedError, lambda: solve(x - sin(x)*log(y - x), x))

    _13 = S(1)/3
    _56 = S(5)/6
    _53 = S(5)/3
    K = (a**(-5))**(_13)*LambertW(_13)**(_13)/-2
    assert solve(3*log(a**(3*x + 5)) + a**(3*x + 5), x) == [
        (log(a**(-5)) + log(3*LambertW(_13)))/(3*log(a)),
        log((3**(_13) - 3**(_56)*I)*K)/log(a),
        log((3**(_13) + 3**(_56)*I)*K)/log(a)]

    # check collection
    K = ((b + 3)*LambertW(1/(b + 3))/a**5)**(_13)
    assert solve(
            3*log(a**(3*x + 5)) + b*log(a**(3*x + 5)) + a**(3*x + 5),
            x) == [
        log(K*(1 - sqrt(3)*I)/-2)/log(a),
        log(K*(1 + sqrt(3)*I)/-2)/log(a),
        log((b + 3)*LambertW(1/(b + 3))/a**5)/(3*log(a))]

    p = symbols('p', positive=True)
    eq = 4*2**(2*p + 3) - 2*p - 3
    assert _solve_lambert(eq, p, _filtered_gens(Poly(eq), p)) == [
        -S(3)/2 - LambertW(-4*log(2))/(2*log(2))]

    # issue 4271
    assert solve((a/x + exp(x/2)).diff(x, 2), x) == [
        6*LambertW(root(-1, 3)*root(a, 3)/3)]

    assert solve((log(x) + x).subs(x, x**2 + 1)) == [
        -I*sqrt(-LambertW(1) + 1), sqrt(-1 + LambertW(1))]

    assert solve(x**3 - 3**x, x) == [3, -3*LambertW(-log(3)/3)/log(3)]
    assert solve(x**2 - 2**x, x) == [2, 4]
    assert solve(-x**2 + 2**x, x) == [2, 4]
    assert solve(3**cos(x) - cos(x)**3) == [acos(3), acos(-3*LambertW(-log(3)/3)/log(3))]
    assert set(solve(3*log(x) - x*log(3))) == set(  # 2.478... and 3
        [3, -3*LambertW(-log(3)/3)/log(3)])
    assert solve(LambertW(2*x) - y, x) == [y*exp(y)/2]


@XFAIL
def test_other_lambert():
    from sympy.abc import x
    assert solve(3*sin(x) - x*sin(3), x) == [3]
    a = S(6)/5
    assert set(solve(x**a - a**x)) == set(
        [a, -a*LambertW(-log(a)/a)/log(a)])
    assert set(solve(3**cos(x) - cos(x)**3)) == set(
        [acos(3), acos(-3*LambertW(-log(3)/3)/log(3))])


def test_rewrite_trig():
    assert solve(sin(x) + tan(x)) == [0, -pi, pi, 2*pi]
    assert solve(sin(x) + sec(x)) == [
        -2*atan(-S.Half + sqrt(2)*sqrt(1 - sqrt(3)*I)/2 + sqrt(3)*I/2),
        2*atan(S.Half - sqrt(2)*sqrt(1 + sqrt(3)*I)/2 + sqrt(3)*I/2), 2*atan(S.Half
        + sqrt(2)*sqrt(1 + sqrt(3)*I)/2 + sqrt(3)*I/2), 2*atan(S.Half -
        sqrt(3)*I/2 + sqrt(2)*sqrt(1 - sqrt(3)*I)/2)]
    assert solve(sinh(x) + tanh(x)) == [0, I*pi]

    # issue 6157
    assert solve(2*sin(x) - cos(x), x) == [-2*atan(2 - sqrt(5)),
                                           -2*atan(2 + sqrt(5))]


@XFAIL
def test_rewrite_trigh():
    # if this import passes then the test below should also pass
    from sympy import sech
    assert solve(sinh(x) + sech(x)) == [
        2*atanh(-S.Half + sqrt(5)/2 - sqrt(-2*sqrt(5) + 2)/2),
        2*atanh(-S.Half + sqrt(5)/2 + sqrt(-2*sqrt(5) + 2)/2),
        2*atanh(-sqrt(5)/2 - S.Half + sqrt(2 + 2*sqrt(5))/2),
        2*atanh(-sqrt(2 + 2*sqrt(5))/2 - sqrt(5)/2 - S.Half)]


def test_uselogcombine():
    eq = z - log(x) + log(y/(x*(-1 + y**2/x**2)))
    assert solve(eq, x, force=True) == [-sqrt(y*(y - exp(z))), sqrt(y*(y - exp(z)))]
    assert solve(log(x + 3) + log(1 + 3/x) - 3) in [
        [-3 + sqrt(-12 + exp(3))*exp(S(3)/2)/2 + exp(3)/2,
        -sqrt(-12 + exp(3))*exp(S(3)/2)/2 - 3 + exp(3)/2],
        [-3 + sqrt(-36 + (-exp(3) + 6)**2)/2 + exp(3)/2,
        -3 - sqrt(-36 + (-exp(3) + 6)**2)/2 + exp(3)/2],
        ]
    assert solve(log(exp(2*x) + 1) + log(-tanh(x) + 1) - log(2)) == []


def test_atan2():
    assert solve(atan2(x, 2) - pi/3, x) == [2*sqrt(3)]


def test_errorinverses():
    assert solve(erf(x) - y, x) == [erfinv(y)]
    assert solve(erfinv(x) - y, x) == [erf(y)]
    assert solve(erfc(x) - y, x) == [erfcinv(y)]
    assert solve(erfcinv(x) - y, x) == [erfc(y)]


def test_issue_2725():
    R = Symbol('R')
    eq = sqrt(2)*R*sqrt(1/(R + 1)) + (R + 1)*(sqrt(2)*sqrt(1/(R + 1)) - 1)
    sol = solve(eq, R, set=True)[1]
    assert sol == set([(S(5)/3 + (-S(1)/2 - sqrt(3)*I/2)*(S(251)/27 +
        sqrt(111)*I/9)**(S(1)/3) + 40/(9*((-S(1)/2 - sqrt(3)*I/2)*(S(251)/27 +
        sqrt(111)*I/9)**(S(1)/3))),), (S(5)/3 + 40/(9*(S(251)/27 +
        sqrt(111)*I/9)**(S(1)/3)) + (S(251)/27 + sqrt(111)*I/9)**(S(1)/3),)])


def test_issue_5114_6611():
    # See that it doesn't hang; this solves in about 2 seconds.
    # Also check that the solution is relatively small.
    # Note: the system in issue 6611 solves in about 5 seconds and has
    # an op-count of 138336 (with simplify=False).
    b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r = symbols('b:r')
    eqs = Matrix([
        [b - c/d + r/d], [c*(1/g + 1/e + 1/d) - f/g - r/d],
        [-c/g + f*(1/j + 1/i + 1/g) - h/i], [-f/i + h*(1/m + 1/l + 1/i) - k/m],
        [-h/m + k*(1/p + 1/o + 1/m) - n/p], [-k/p + n*(1/q + 1/p)]])
    v = Matrix([f, h, k, n, b, c])
    ans = solve(list(eqs), list(v), simplify=False)
    # If time is taken to simplify then then 2617 below becomes
    # 1168 and the time is about 50 seconds instead of 2.
    assert sum([s.count_ops() for s in ans.values()]) <= 2617


def test_det_quick():
    m = Matrix(3, 3, symbols('a:9'))
    assert m.det() == det_quick(m)  # calls det_perm
    m[0, 0] = 1
    assert m.det() == det_quick(m)  # calls det_minor
    m = Matrix(3, 3, list(range(9)))
    assert m.det() == det_quick(m)  # defaults to .det()
    # make sure they work with Sparse
    s = SparseMatrix(2, 2, (1, 2, 1, 4))
    assert det_perm(s) == det_minor(s) == s.det()


def test_real_imag_splitting():
    a, b = symbols('a b', real=True)
    assert solve(sqrt(a**2 + b**2) - 3, a) == \
        [-sqrt(-b**2 + 9), sqrt(-b**2 + 9)]
    a, b = symbols('a b', imaginary=True)
    assert solve(sqrt(a**2 + b**2) - 3, a) == []


def test_issue_7110():
    y = -2*x**3 + 4*x**2 - 2*x + 5
    assert any(ask(Q.real(i)) for i in solve(y))


def test_units():
    assert solve(1/x - 1/(2*cm)) == [2*cm]


def test_issue_7547():
    A, B, V = symbols('A,B,V')
    eq1 = Eq(630.26*(V - 39.0)*V*(V + 39) - A + B, 0)
    eq2 = Eq(B, 1.36*10**8*(V - 39))
    eq3 = Eq(A, 5.75*10**5*V*(V + 39.0))
    sol = Matrix(nsolve(Tuple(eq1, eq2, eq3), [A, B, V], (0, 0, 0)))
    assert str(sol) == str(Matrix(
        [['4442890172.68209'],
         ['4289299466.1432'],
         ['70.5389666628177']]))


def test_issue_7895():
    r = symbols('r', real=True)
    assert solve(sqrt(r) - 2) == [4]


def test_issue_2777():
    # the equations represent two circles
    x, y = symbols('x y', real=True)
    e1, e2 = sqrt(x**2 + y**2) - 10, sqrt(y**2 + (-x + 10)**2) - 3
    a, b = 191/S(20), 3*sqrt(391)/20
    ans = [(a, -b), (a, b)]
    assert solve((e1, e2), (x, y)) == ans
    assert solve((e1, e2/(x - a)), (x, y)) == []
    # make the 2nd circle's radius be -3
    e2 += 6
    assert solve((e1, e2), (x, y)) == []
    assert solve((e1, e2), (x, y), check=False) == ans


def test_issue_7322():
    number = 5.62527e-35
    assert solve(x - number, x)[0] == number


def test_nsolve():
    raises(ValueError, lambda: nsolve(x, (-1, 1), method='bisect'))
    raises(TypeError, lambda: nsolve((x - y + 3,x + y,z - y),(x,y,z),(-50,50)))
    raises(TypeError, lambda: nsolve((x + y, x - y), (0, 1)))


@slow
def test_high_order_multivariate():
    assert len(solve(a*x**3 - x + 1, x)) == 3
    assert len(solve(a*x**4 - x + 1, x)) == 4
    assert solve(a*x**5 - x + 1, x) == []  # incomplete solution allowed
    raises(NotImplementedError, lambda:
        solve(a*x**5 - x + 1, x, incomplete=False))

    # result checking must always consider the denominator and CRootOf
    # must be checked, too
    d = x**5 - x + 1
    assert solve(d*(1 + 1/d)) == [CRootOf(d + 1, i) for i in range(5)]
    d = x - 1
    assert solve(d*(2 + 1/d)) == [S.Half]


def test_base_0_exp_0():
    assert solve(0**x - 1) == [0]
    assert solve(0**(x - 2) - 1) == [2]
    assert solve(S('x*(1/x**0 - x)', evaluate=False)) == \
        [0, 1]


def test__simple_dens():
    assert _simple_dens(1/x**0, [x]) == set()
    assert _simple_dens(1/x**y, [x]) == set([x**y])
    assert _simple_dens(1/root(x, 3), [x]) == set([x])


def test_issue_8755():
    # This tests two things: that if full unrad is attempted and fails
    # the solution should still be found; also it tests the use of
    # keyword `composite`.
    assert len(solve(sqrt(y)*x + x**3 - 1, x)) == 3
    assert len(solve(-512*y**3 + 1344*(x + 2)**(S(1)/3)*y**2 -
        1176*(x + 2)**(S(2)/3)*y - 169*x + 686, y, _unrad=False)) == 3


@slow
def test_issue_8828():
    x1 = 0
    y1 = -620
    r1 = 920
    x2 = 126
    y2 = 276
    x3 = 51
    y3 = 205
    r3 = 104
    v = x, y, z

    f1 = (x - x1)**2 + (y - y1)**2 - (r1 - z)**2
    f2 = (x2 - x)**2 + (y2 - y)**2 - z**2
    f3 = (x - x3)**2 + (y - y3)**2 - (r3 - z)**2
    F = f1,f2,f3

    g1 = sqrt((x - x1)**2 + (y - y1)**2) + z - r1
    g2 = f2
    g3 = sqrt((x - x3)**2 + (y - y3)**2) + z - r3
    G = g1,g2,g3

    A = solve(F, v)
    B = solve(G, v)
    C = solve(G, v, manual=True)

    p, q, r = [set([tuple(i.evalf(2) for i in j) for j in R]) for R in [A, B, C]]
    assert p == q == r


@slow
def test_issue_2840_8155():
    assert solve(sin(3*x) + sin(6*x)) == [
        0, -pi, pi, 14*pi/9, 16*pi/9, 2*pi, 2*I*(log(2) - log(-1 - sqrt(3)*I)),
        2*I*(log(2) - log(-1 + sqrt(3)*I)), 2*I*(log(2) - log(1 - sqrt(3)*I)),
        2*I*(log(2) - log(1 + sqrt(3)*I)), 2*I*(log(2) - log(-sqrt(3) - I)),
        2*I*(log(2) - log(-sqrt(3) + I)), 2*I*(log(2) - log(sqrt(3) - I)),
        2*I*(log(2) - log(sqrt(3) + I)), -2*I*log(-(-1)**(S(1)/9)), -2*I*log(
        -(-1)**(S(2)/9)), -2*I*log(-sin(pi/18) - I*cos(pi/18)), -2*I*log(-sin(
        pi/18) + I*cos(pi/18)), -2*I*log(sin(pi/18) - I*cos(pi/18)), -2*I*log(
        sin(pi/18) + I*cos(pi/18)), -2*I*log(exp(-2*I*pi/9)), -2*I*log(exp(
        -I*pi/9)), -2*I*log(exp(I*pi/9)), -2*I*log(exp(2*I*pi/9))]
    assert solve(2*sin(x) - 2*sin(2*x)) == [
        0, -pi, pi, 2*I*(log(2) - log(-sqrt(3) - I)), 2*I*(log(2) -
        log(-sqrt(3) + I)), 2*I*(log(2) - log(sqrt(3) - I)), 2*I*(log(2) -
        log(sqrt(3) + I))]


def test_issue_9567():
    assert solve(1 + 1/(x - 1)) == [0]


def test_issue_11538():
    assert solve(x + E) == [-E]
    assert solve(x**2 + E) == [-I*sqrt(E), I*sqrt(E)]
    assert solve(x**3 + 2*E) == [
        -cbrt(2 * E),
        cbrt(2)*cbrt(E)/2 - cbrt(2)*sqrt(3)*I*cbrt(E)/2,
        cbrt(2)*cbrt(E)/2 + cbrt(2)*sqrt(3)*I*cbrt(E)/2]
    assert solve([x + 4, y + E], x, y) == {x: -4, y: -E}
    assert solve([x**2 + 4, y + E], x, y) == [
        (-2*I, -E), (2*I, -E)]

    e1 = x - y**3 + 4
    e2 = x + y + 4 + 4 * E
    assert len(solve([e1, e2], x, y)) == 3


@slow
def test_issue_12114():
    a, b, c, d, e, f, g = symbols('a,b,c,d,e,f,g')
    terms = [1 + a*b + d*e, 1 + a*c + d*f, 1 + b*c + e*f,
             g - a**2 - d**2, g - b**2 - e**2, g - c**2 - f**2]
    s = solve(terms, [a, b, c, d, e, f, g], dict=True)
    assert s == [{a: -sqrt(-f**2 - 1), b: -sqrt(-f**2 - 1),
                  c: -sqrt(-f**2 - 1), d: f, e: f, g: -1},
                 {a: sqrt(-f**2 - 1), b: sqrt(-f**2 - 1),
                  c: sqrt(-f**2 - 1), d: f, e: f, g: -1},
                 {a: -sqrt(3)*f/2 - sqrt(-f**2 + 2)/2,
                  b: sqrt(3)*f/2 - sqrt(-f**2 + 2)/2, c: sqrt(-f**2 + 2),
                  d: -f/2 + sqrt(-3*f**2 + 6)/2,
                  e: -f/2 - sqrt(3)*sqrt(-f**2 + 2)/2, g: 2},
                 {a: -sqrt(3)*f/2 + sqrt(-f**2 + 2)/2,
                  b: sqrt(3)*f/2 + sqrt(-f**2 + 2)/2, c: -sqrt(-f**2 + 2),
                  d: -f/2 - sqrt(-3*f**2 + 6)/2,
                  e: -f/2 + sqrt(3)*sqrt(-f**2 + 2)/2, g: 2},
                 {a: sqrt(3)*f/2 - sqrt(-f**2 + 2)/2,
                  b: -sqrt(3)*f/2 - sqrt(-f**2 + 2)/2, c: sqrt(-f**2 + 2),
                  d: -f/2 - sqrt(-3*f**2 + 6)/2,
                  e: -f/2 + sqrt(3)*sqrt(-f**2 + 2)/2, g: 2},
                 {a: sqrt(3)*f/2 + sqrt(-f**2 + 2)/2,
                  b: -sqrt(3)*f/2 + sqrt(-f**2 + 2)/2, c: -sqrt(-f**2 + 2),
                  d: -f/2 + sqrt(-3*f**2 + 6)/2,
                  e: -f/2 - sqrt(3)*sqrt(-f**2 + 2)/2, g: 2}]


def test_inf():
    assert solve(1 - oo*x) == []
    assert solve(oo*x, x) == []
    assert solve(oo*x - oo, x) == []


def test_issue_12448():
    f = Function('f')
    fun = [f(i) for i in range(15)]
    sym = symbols('x:15')
    reps = dict(zip(fun, sym))

    (x, y, z), c = sym[:3], sym[3:]
    ssym = solve([c[4*i]*x + c[4*i + 1]*y + c[4*i + 2]*z + c[4*i + 3]
        for i in range(3)], (x, y, z))

    (x, y, z), c = fun[:3], fun[3:]
    sfun = solve([c[4*i]*x + c[4*i + 1]*y + c[4*i + 2]*z + c[4*i + 3]
        for i in range(3)], (x, y, z))

    assert sfun[fun[0]].xreplace(reps).count_ops() == \
        ssym[sym[0]].count_ops()


def test_denoms():
    assert denoms(x/2 + 1/y) == set([2, y])
    assert denoms(x/2 + 1/y, y) == set([y])
    assert denoms(x/2 + 1/y, [y]) == set([y])
    assert denoms(1/x + 1/y + 1/z, [x, y]) == set([x, y])
    assert denoms(1/x + 1/y + 1/z, x, y) == set([x, y])
    assert denoms(1/x + 1/y + 1/z, set([x, y])) == set([x, y])


def test_issue_12476():
    x0, x1, x2, x3, x4, x5 = symbols('x0 x1 x2 x3 x4 x5')
    eqns = [x0**2 - x0, x0*x1 - x1, x0*x2 - x2, x0*x3 - x3, x0*x4 - x4, x0*x5 - x5,
            x0*x1 - x1, -x0/3 + x1**2 - 2*x2/3, x1*x2 - x1/3 - x2/3 - x3/3,
            x1*x3 - x2/3 - x3/3 - x4/3, x1*x4 - 2*x3/3 - x5/3, x1*x5 - x4, x0*x2 - x2,
            x1*x2 - x1/3 - x2/3 - x3/3, -x0/6 - x1/6 + x2**2 - x2/6 - x3/3 - x4/6,
            -x1/6 + x2*x3 - x2/3 - x3/6 - x4/6 - x5/6, x2*x4 - x2/3 - x3/3 - x4/3,
            x2*x5 - x3, x0*x3 - x3, x1*x3 - x2/3 - x3/3 - x4/3,
            -x1/6 + x2*x3 - x2/3 - x3/6 - x4/6 - x5/6,
            -x0/6 - x1/6 - x2/6 + x3**2 - x3/3 - x4/6, -x1/3 - x2/3 + x3*x4 - x3/3,
            -x2 + x3*x5, x0*x4 - x4, x1*x4 - 2*x3/3 - x5/3, x2*x4 - x2/3 - x3/3 - x4/3,
            -x1/3 - x2/3 + x3*x4 - x3/3, -x0/3 - 2*x2/3 + x4**2, -x1 + x4*x5, x0*x5 - x5,
            x1*x5 - x4, x2*x5 - x3, -x2 + x3*x5, -x1 + x4*x5, -x0 + x5**2, x0 - 1]
    sols = [{x0: 1, x3: S(1)/6, x2: S(1)/6, x4: -S(2)/3, x1: -S(2)/3, x5: 1},
            {x0: 1, x3: S(1)/2, x2: -S(1)/2, x4: 0, x1: 0, x5: -1},
            {x0: 1, x3: -S(1)/3, x2: -S(1)/3, x4: S(1)/3, x1: S(1)/3, x5: 1},
            {x0: 1, x3: 1, x2: 1, x4: 1, x1: 1, x5: 1},
            {x0: 1, x3: -S(1)/3, x2: S(1)/3, x4: sqrt(5)/3, x1: -sqrt(5)/3, x5: -1},
            {x0: 1, x3: -S(1)/3, x2: S(1)/3, x4: -sqrt(5)/3, x1: sqrt(5)/3, x5: -1}]

    assert solve(eqns) == sols


def test_issue_13849():
    t = symbols('t')
    assert solve((t*(sqrt(5) + sqrt(2)) - sqrt(2), t), t) == []


def test_issue_14860():
    from sympy.physics.units import newton, kilo
    assert solve(8*kilo*newton + x + y, x) == [-8000*newton - y]


def test_issue_14721():
    k, h, a, b = symbols(':4')
    assert solve([
        -1 + (-k + 1)**2/b**2 + (-h - 1)**2/a**2,
        -1 + (-k + 1)**2/b**2 + (-h + 1)**2/a**2,
        h, k + 2], h, k, a, b) == [
        (0, -2, -b*sqrt(1/(b**2 - 9)), b),
        (0, -2, b*sqrt(1/(b**2 - 9)), b)]
    assert solve([
        h, h/a + 1/b**2 - 2, -h/2 + 1/b**2 - 2], a, h, b) == [
        (a, 0, -sqrt(2)/2), (a, 0, sqrt(2)/2)]
    assert solve((a + b**2 - 1, a + b**2 - 2)) == []


def test_issue_14779():
    x = symbols('x', real=True)
    assert solve(sqrt(x**4 - 130*x**2 + 1089) + sqrt(x**4 - 130*x**2
                 + 3969) - 96*Abs(x)/x,x) == [sqrt(130)]


def test_issue_15307():
    assert solve((y - 2, Mul(x + 3,x - 2, evaluate=False))) == \
        [{x: -3, y: 2}, {x: 2, y: 2}]
    assert solve((y - 2, Mul(3, x - 2, evaluate=False))) == \
        {x: 2, y: 2}
    assert solve((y - 2, Add(x + 4, x - 2, evaluate=False))) == \
        {x: -1, y: 2}
    eq1 = Eq(12513*x + 2*y - 219093, -5726*x - y)
    eq2 = Eq(-2*x + 8, 2*x - 40)
    assert solve([eq1, eq2]) == {x:12, y:75}

def test_issue_15415():
    assert solve(x - 3, x) == [3]
    assert solve([x - 3], x) == {x:3}
    assert solve(Eq(y + 3*x**2/2, y + 3*x), y) == []
    assert solve([Eq(y + 3*x**2/2, y + 3*x)], y) == []
    assert solve([Eq(y + 3*x**2/2, y + 3*x), Eq(x, 1)], y) == []


@slow
def test_issue_15731():
    # f(x)**g(x)=c
    assert solve(Eq((x**2 - 7*x + 11)**(x**2 - 13*x + 42), 1)) == [2, 3, 4, 5, 6, 7]
    assert solve((x)**(x + 4) - 4) == [-2]
    assert solve((-x)**(-x + 4) - 4) == [2]
    assert solve((x**2 - 6)**(x**2 - 2) - 4) == [-2, 2]
    assert solve((x**2 - 2*x - 1)**(x**2 - 3) - 1/(1 - 2*sqrt(2))) == [sqrt(2)]
    assert solve(x**(x + S.Half) - 4*sqrt(2)) == [S(2)]
    assert solve((x**2 + 1)**x - 25) == [2]
    assert solve(x**(2/x) - 2) == [2, 4]
    assert solve((x/2)**(2/x) - sqrt(2)) == [4, 8]
    assert solve(x**(x + S.Half) - S(9)/4) == [S(3)/2]
    # a**g(x)=c
    assert solve((-sqrt(sqrt(2)))**x - 2) == [4, log(2)/(log(2**(S(1)/4)) + I*pi)]
    assert solve((sqrt(2))**x - sqrt(sqrt(2))) == [S(1)/2]
    assert solve((-sqrt(2))**x + 2*(sqrt(2))) == [3,
            (3*log(2)**2 + 4*pi**2 - 4*I*pi*log(2))/(log(2)**2 + 4*pi**2)]
    assert solve((sqrt(2))**x - 2*(sqrt(2))) == [3]
    assert solve(I**x + 1) == [2]
    assert solve((1 + I)**x - 2*I) == [2]
    assert solve((sqrt(2) + sqrt(3))**x - (2*sqrt(6) + 5)**(S(1)/3)) == [S(2)/3]
    # bases of both sides are equal
    b = Symbol('b')
    assert solve(b**x - b**2, x) == [2]
    assert solve(b**x - 1/b, x) == [-1]
    assert solve(b**x - b, x) == [1]
    b = Symbol('b', positive=True)
    assert solve(b**x - b**2, x) == [2]
    assert solve(b**x - 1/b, x) == [-1]
