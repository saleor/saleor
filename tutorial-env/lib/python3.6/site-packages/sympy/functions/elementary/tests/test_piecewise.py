from sympy import (
    adjoint, And, Basic, conjugate, diff, expand, Eq, Function, I, ITE,
    Integral, integrate, Interval, lambdify, log, Max, Min, oo, Or, pi,
    Piecewise, piecewise_fold, Rational, solve, symbols, transpose,
    cos, sin, exp, Abs, Ne, Not, Symbol, S, sqrt, Tuple, zoo,
    factor_terms, DiracDelta, Heaviside, Add, Mul, factorial, Ge)
from sympy.printing import srepr
from sympy.utilities.pytest import raises, slow

from sympy.functions.elementary.piecewise import Undefined


a, b, c, d, x, y = symbols('a:d, x, y')
z = symbols('z', nonzero=True)


def test_piecewise():

    # Test canonicalization
    assert Piecewise((x, x < 1), (0, True)) == Piecewise((x, x < 1), (0, True))
    assert Piecewise((x, x < 1), (0, True), (1, True)) == \
        Piecewise((x, x < 1), (0, True))
    assert Piecewise((x, x < 1), (0, False), (-1, 1 > 2)) == \
        Piecewise((x, x < 1))
    assert Piecewise((x, x < 1), (0, x < 1), (0, True)) == \
        Piecewise((x, x < 1), (0, True))
    assert Piecewise((x, x < 1), (0, x < 2), (0, True)) == \
        Piecewise((x, x < 1), (0, True))
    assert Piecewise((x, x < 1), (x, x < 2), (0, True)) == \
        Piecewise((x, Or(x < 1, x < 2)), (0, True))
    assert Piecewise((x, x < 1), (x, x < 2), (x, True)) == x
    assert Piecewise((x, True)) == x
    # Explicitly constructed empty Piecewise not accepted
    raises(TypeError, lambda: Piecewise())
    # False condition is never retained
    assert Piecewise((2*x, x < 0), (x, False)) == \
        Piecewise((2*x, x < 0), (x, False), evaluate=False) == \
        Piecewise((2*x, x < 0))
    assert Piecewise((x, False)) == Undefined
    raises(TypeError, lambda: Piecewise(x))
    assert Piecewise((x, 1)) == x  # 1 and 0 are accepted as True/False
    raises(TypeError, lambda: Piecewise((x, 2)))
    raises(TypeError, lambda: Piecewise((x, x**2)))
    raises(TypeError, lambda: Piecewise(([1], True)))
    assert Piecewise(((1, 2), True)) == Tuple(1, 2)
    cond = (Piecewise((1, x < 0), (2, True)) < y)
    assert Piecewise((1, cond)
        ) == Piecewise((1, ITE(x < 0, y > 1, y > 2)))

    assert Piecewise((1, x > 0), (2, And(x <= 0, x > -1))
        ) == Piecewise((1, x > 0), (2, x > -1))

    # Test subs
    p = Piecewise((-1, x < -1), (x**2, x < 0), (log(x), x >= 0))
    p_x2 = Piecewise((-1, x**2 < -1), (x**4, x**2 < 0), (log(x**2), x**2 >= 0))
    assert p.subs(x, x**2) == p_x2
    assert p.subs(x, -5) == -1
    assert p.subs(x, -1) == 1
    assert p.subs(x, 1) == log(1)

    # More subs tests
    p2 = Piecewise((1, x < pi), (-1, x < 2*pi), (0, x > 2*pi))
    p3 = Piecewise((1, Eq(x, 0)), (1/x, True))
    p4 = Piecewise((1, Eq(x, 0)), (2, 1/x>2))
    assert p2.subs(x, 2) == 1
    assert p2.subs(x, 4) == -1
    assert p2.subs(x, 10) == 0
    assert p3.subs(x, 0.0) == 1
    assert p4.subs(x, 0.0) == 1


    f, g, h = symbols('f,g,h', cls=Function)
    pf = Piecewise((f(x), x < -1), (f(x) + h(x) + 2, x <= 1))
    pg = Piecewise((g(x), x < -1), (g(x) + h(x) + 2, x <= 1))
    assert pg.subs(g, f) == pf

    assert Piecewise((1, Eq(x, 0)), (0, True)).subs(x, 0) == 1
    assert Piecewise((1, Eq(x, 0)), (0, True)).subs(x, 1) == 0
    assert Piecewise((1, Eq(x, y)), (0, True)).subs(x, y) == 1
    assert Piecewise((1, Eq(x, z)), (0, True)).subs(x, z) == 1
    assert Piecewise((1, Eq(exp(x), cos(z))), (0, True)).subs(x, z) == \
        Piecewise((1, Eq(exp(z), cos(z))), (0, True))

    p5 = Piecewise( (0, Eq(cos(x) + y, 0)), (1, True))
    assert p5.subs(y, 0) == Piecewise( (0, Eq(cos(x), 0)), (1, True))

    assert Piecewise((-1, y < 1), (0, x < 0), (1, Eq(x, 0)), (2, True)
        ).subs(x, 1) == Piecewise((-1, y < 1), (2, True))
    assert Piecewise((1, Eq(x**2, -1)), (2, x < 0)).subs(x, I) == 1

    p6 = Piecewise((x, x > 0))
    n = symbols('n', negative=True)
    assert p6.subs(x, n) == Undefined

    # Test evalf
    assert p.evalf() == p
    assert p.evalf(subs={x: -2}) == -1
    assert p.evalf(subs={x: -1}) == 1
    assert p.evalf(subs={x: 1}) == log(1)
    assert p6.evalf(subs={x: -5}) == Undefined

    # Test doit
    f_int = Piecewise((Integral(x, (x, 0, 1)), x < 1))
    assert f_int.doit() == Piecewise( (S(1)/2, x < 1) )

    # Test differentiation
    f = x
    fp = x*p
    dp = Piecewise((0, x < -1), (2*x, x < 0), (1/x, x >= 0))
    fp_dx = x*dp + p
    assert diff(p, x) == dp
    assert diff(f*p, x) == fp_dx

    # Test simple arithmetic
    assert x*p == fp
    assert x*p + p == p + x*p
    assert p + f == f + p
    assert p + dp == dp + p
    assert p - dp == -(dp - p)

    # Test power
    dp2 = Piecewise((0, x < -1), (4*x**2, x < 0), (1/x**2, x >= 0))
    assert dp**2 == dp2

    # Test _eval_interval
    f1 = x*y + 2
    f2 = x*y**2 + 3
    peval = Piecewise((f1, x < 0), (f2, x > 0))
    peval_interval = f1.subs(
        x, 0) - f1.subs(x, -1) + f2.subs(x, 1) - f2.subs(x, 0)
    assert peval._eval_interval(x, 0, 0) == 0
    assert peval._eval_interval(x, -1, 1) == peval_interval
    peval2 = Piecewise((f1, x < 0), (f2, True))
    assert peval2._eval_interval(x, 0, 0) == 0
    assert peval2._eval_interval(x, 1, -1) == -peval_interval
    assert peval2._eval_interval(x, -1, -2) == f1.subs(x, -2) - f1.subs(x, -1)
    assert peval2._eval_interval(x, -1, 1) == peval_interval
    assert peval2._eval_interval(x, None, 0) == peval2.subs(x, 0)
    assert peval2._eval_interval(x, -1, None) == -peval2.subs(x, -1)

    # Test integration
    assert p.integrate() == Piecewise(
        (-x, x < -1),
        (x**3/3 + S(4)/3, x < 0),
        (x*log(x) - x + S(4)/3, True))
    p = Piecewise((x, x < 1), (x**2, -1 <= x), (x, 3 < x))
    assert integrate(p, (x, -2, 2)) == 5/6.0
    assert integrate(p, (x, 2, -2)) == -5/6.0
    p = Piecewise((0, x < 0), (1, x < 1), (0, x < 2), (1, x < 3), (0, True))
    assert integrate(p, (x, -oo, oo)) == 2
    p = Piecewise((x, x < -10), (x**2, x <= -1), (x, 1 < x))
    assert integrate(p, (x, -2, 2)) == Undefined

    # Test commutativity
    assert isinstance(p, Piecewise) and p.is_commutative is True


def test_piecewise_free_symbols():
    f = Piecewise((x, a < 0), (y, True))
    assert f.free_symbols == {x, y, a}


def test_piecewise_integrate1():
    x, y = symbols('x y', real=True, finite=True)

    f = Piecewise(((x - 2)**2, x >= 0), (1, True))
    assert integrate(f, (x, -2, 2)) == Rational(14, 3)

    g = Piecewise(((x - 5)**5, x >= 4), (f, True))
    assert integrate(g, (x, -2, 2)) == Rational(14, 3)
    assert integrate(g, (x, -2, 5)) == Rational(43, 6)

    assert g == Piecewise(((x - 5)**5, x >= 4), (f, x < 4))

    g = Piecewise(((x - 5)**5, 2 <= x), (f, x < 2))
    assert integrate(g, (x, -2, 2)) == Rational(14, 3)
    assert integrate(g, (x, -2, 5)) == -Rational(701, 6)

    assert g == Piecewise(((x - 5)**5, 2 <= x), (f, True))

    g = Piecewise(((x - 5)**5, 2 <= x), (2*f, True))
    assert integrate(g, (x, -2, 2)) == 2 * Rational(14, 3)
    assert integrate(g, (x, -2, 5)) == -Rational(673, 6)


def test_piecewise_integrate1b():
    g = Piecewise((1, x > 0), (0, Eq(x, 0)), (-1, x < 0))
    assert integrate(g, (x, -1, 1)) == 0

    g = Piecewise((1, x - y < 0), (0, True))
    assert integrate(g, (y, -oo, 0)) == -Min(0, x)
    assert g.subs(x, -3).integrate((y, -oo, 0)) == 3
    assert integrate(g, (y, 0, -oo)) == Min(0, x)
    assert integrate(g, (y, 0, oo)) == -Max(0, x) + oo
    assert integrate(g, (y, -oo, 42)) == -Min(42, x) + 42
    assert integrate(g, (y, -oo, oo)) == -x + oo

    g = Piecewise((0, x < 0), (x, x <= 1), (1, True))
    gy1 = g.integrate((x, y, 1))
    g1y = g.integrate((x, 1, y))
    for yy in (-1, S.Half, 2):
        assert g.integrate((x, yy, 1)) == gy1.subs(y, yy)
        assert g.integrate((x, 1, yy)) == g1y.subs(y, yy)
    assert gy1 == Piecewise(
        (-Min(1, Max(0, y))**2/2 + S(1)/2, y < 1),
        (-y + 1, True))
    assert g1y == Piecewise(
        (Min(1, Max(0, y))**2/2 - S(1)/2, y < 1),
        (y - 1, True))

@slow
def test_piecewise_integrate1ca():
    y = symbols('y', real=True)
    g = Piecewise(
        (1 - x, Interval(0, 1).contains(x)),
        (1 + x, Interval(-1, 0).contains(x)),
        (0, True)
        )
    gy1 = g.integrate((x, y, 1))
    g1y = g.integrate((x, 1, y))

    assert g.integrate((x, -2, 1)) == gy1.subs(y, -2)
    assert g.integrate((x, 1, -2)) == g1y.subs(y, -2)
    assert g.integrate((x, 0, 1)) == gy1.subs(y, 0)
    assert g.integrate((x, 1, 0)) == g1y.subs(y, 0)
    # XXX Make test pass without simplify
    assert g.integrate((x, 2, 1)) == gy1.subs(y, 2).simplify()
    assert g.integrate((x, 1, 2)) == g1y.subs(y, 2).simplify()

    assert piecewise_fold(gy1.rewrite(Piecewise)) == \
        Piecewise(
            (1, y <= -1),
            (-y**2/2 - y + S(1)/2, y <= 0),
            (y**2/2 - y + S(1)/2, y < 1),
            (0, True))
    assert piecewise_fold(g1y.rewrite(Piecewise)) == \
        Piecewise(
            (-1, y <= -1),
            (y**2/2 + y - S(1)/2, y <= 0),
            (-y**2/2 + y - S(1)/2, y < 1),
            (0, True))

    # g1y and gy1 should simplify if the condition that y < 1
    # is applied, e.g. Min(1, Max(-1, y)) --> Max(-1, y)
    # XXX Make test pass without simplify
    assert gy1.simplify() == Piecewise(
        (
            -Min(1, Max(-1, y))**2/2 - Min(1, Max(-1, y)) +
            Min(1, Max(0, y))**2 + S(1)/2, y < 1),
        (0, True)
        )
    assert g1y.simplify() == Piecewise(
        (
            Min(1, Max(-1, y))**2/2 + Min(1, Max(-1, y)) -
            Min(1, Max(0, y))**2 - S(1)/2, y < 1),
        (0, True))

@slow
def test_piecewise_integrate1cb():
    y = symbols('y', real=True)
    g = Piecewise(
        (0, Or(x <= -1, x >= 1)),
        (1 - x, x > 0),
        (1 + x, True)
        )
    gy1 = g.integrate((x, y, 1))
    g1y = g.integrate((x, 1, y))

    assert g.integrate((x, -2, 1)) == gy1.subs(y, -2)
    assert g.integrate((x, 1, -2)) == g1y.subs(y, -2)
    assert g.integrate((x, 0, 1)) == gy1.subs(y, 0)
    assert g.integrate((x, 1, 0)) == g1y.subs(y, 0)
    assert g.integrate((x, 2, 1)) == gy1.subs(y, 2)
    assert g.integrate((x, 1, 2)) == g1y.subs(y, 2)

    assert piecewise_fold(gy1.rewrite(Piecewise)) == \
        Piecewise(
            (1, y <= -1),
            (-y**2/2 - y + S(1)/2, y <= 0),
            (y**2/2 - y + S(1)/2, y < 1),
            (0, True))
    assert piecewise_fold(g1y.rewrite(Piecewise)) == \
        Piecewise(
            (-1, y <= -1),
            (y**2/2 + y - S(1)/2, y <= 0),
            (-y**2/2 + y - S(1)/2, y < 1),
            (0, True))

    # g1y and gy1 should simplify if the condition that y < 1
    # is applied, e.g. Min(1, Max(-1, y)) --> Max(-1, y)
    assert gy1 == Piecewise(
        (
            -Min(1, Max(-1, y))**2/2 - Min(1, Max(-1, y)) +
            Min(1, Max(0, y))**2 + S(1)/2, y < 1),
        (0, True)
        )
    assert g1y == Piecewise(
        (
            Min(1, Max(-1, y))**2/2 + Min(1, Max(-1, y)) -
            Min(1, Max(0, y))**2 - S(1)/2, y < 1),
        (0, True))


def test_piecewise_integrate2():
    from itertools import permutations
    lim = Tuple(x, c, d)
    p = Piecewise((1, x < a), (2, x > b), (3, True))
    q = p.integrate(lim)
    assert q == Piecewise(
        (-c + 2*d - 2*Min(d, Max(a, c)) + Min(d, Max(a, b, c)), c < d),
        (-2*c + d + 2*Min(c, Max(a, d)) - Min(c, Max(a, b, d)), True))
    for v in permutations((1, 2, 3, 4)):
        r = dict(zip((a, b, c, d), v))
        assert p.subs(r).integrate(lim.subs(r)) == q.subs(r)


def test_meijer_bypass():
    # totally bypass meijerg machinery when dealing
    # with Piecewise in integrate
    assert Piecewise((1, x < 4), (0, True)).integrate((x, oo, 1)) == -3


def test_piecewise_integrate3_inequality_conditions():
    from sympy.utilities.iterables import cartes
    lim = (x, 0, 5)
    # set below includes two pts below range, 2 pts in range,
    # 2 pts above range, and the boundaries
    N = (-2, -1, 0, 1, 2, 5, 6, 7)

    p = Piecewise((1, x > a), (2, x > b), (0, True))
    ans = p.integrate(lim)
    for i, j in cartes(N, repeat=2):
        reps = dict(zip((a, b), (i, j)))
        assert ans.subs(reps) == p.subs(reps).integrate(lim)
    assert ans.subs(a, 4).subs(b, 1) == 0 + 2*3 + 1

    p = Piecewise((1, x > a), (2, x < b), (0, True))
    ans = p.integrate(lim)
    for i, j in cartes(N, repeat=2):
        reps = dict(zip((a, b), (i, j)))
        assert ans.subs(reps) == p.subs(reps).integrate(lim)

    # delete old tests that involved c1 and c2 since those
    # reduce to the above except that a value of 0 was used
    # for two expressions whereas the above uses 3 different
    # values


@slow
def test_piecewise_integrate4_symbolic_conditions():
    a = Symbol('a', real=True, finite=True)
    b = Symbol('b', real=True, finite=True)
    x = Symbol('x', real=True, finite=True)
    y = Symbol('y', real=True, finite=True)
    p0 = Piecewise((0, Or(x < a, x > b)), (1, True))
    p1 = Piecewise((0, x < a), (0, x > b), (1, True))
    p2 = Piecewise((0, x > b), (0, x < a), (1, True))
    p3 = Piecewise((0, x < a), (1, x < b), (0, True))
    p4 = Piecewise((0, x > b), (1, x > a), (0, True))
    p5 = Piecewise((1, And(a < x, x < b)), (0, True))

    # check values of a=1, b=3 (and reversed) with values
    # of y of 0, 1, 2, 3, 4
    lim = Tuple(x, -oo, y)
    for p in (p0, p1, p2, p3, p4, p5):
        ans = p.integrate(lim)
        for i in range(5):
            reps = {a:1, b:3, y:i}
            assert ans.subs(reps) == p.subs(reps).integrate(lim.subs(reps))
            reps = {a: 3, b:1, y:i}
            assert ans.subs(reps) == p.subs(reps).integrate(lim.subs(reps))
    lim = Tuple(x, y, oo)
    for p in (p0, p1, p2, p3, p4, p5):
        ans = p.integrate(lim)
        for i in range(5):
            reps = {a:1, b:3, y:i}
            assert ans.subs(reps) == p.subs(reps).integrate(lim.subs(reps))
            reps = {a:3, b:1, y:i}
            assert ans.subs(reps) == p.subs(reps).integrate(lim.subs(reps))

    ans = Piecewise(
        (0, x <= Min(a, b)),
        (x - Min(a, b), x <= b),
        (b - Min(a, b), True))
    for i in (p0, p1, p2, p4):
        assert i.integrate(x) == ans
    assert p3.integrate(x) == Piecewise(
        (0, x < a),
        (-a + x, x <= Max(a, b)),
        (-a + Max(a, b), True))
    assert p5.integrate(x) == Piecewise(
        (0, x <= a),
        (-a + x, x <= Max(a, b)),
        (-a + Max(a, b), True))

    p1 = Piecewise((0, x < a), (0.5, x > b), (1, True))
    p2 = Piecewise((0.5, x > b), (0, x < a), (1, True))
    p3 = Piecewise((0, x < a), (1, x < b), (0.5, True))
    p4 = Piecewise((0.5, x > b), (1, x > a), (0, True))
    p5 = Piecewise((1, And(a < x, x < b)), (0.5, x > b), (0, True))

    # check values of a=1, b=3 (and reversed) with values
    # of y of 0, 1, 2, 3, 4
    lim = Tuple(x, -oo, y)
    for p in (p1, p2, p3, p4, p5):
        ans = p.integrate(lim)
        for i in range(5):
            reps = {a:1, b:3, y:i}
            assert ans.subs(reps) == p.subs(reps).integrate(lim.subs(reps))
            reps = {a: 3, b:1, y:i}
            assert ans.subs(reps) == p.subs(reps).integrate(lim.subs(reps))


def test_piecewise_integrate5_independent_conditions():
    p = Piecewise((0, Eq(y, 0)), (x*y, True))
    assert integrate(p, (x, 1, 3)) == Piecewise((0, Eq(y, 0)), (4*y, True))


def test_piecewise_simplify():
    p = Piecewise(((x**2 + 1)/x**2, Eq(x*(1 + x) - x**2, 0)),
                  ((-1)**x*(-1), True))
    assert p.simplify() == \
        Piecewise((zoo, Eq(x, 0)), ((-1)**(x + 1), True))
    # simplify when there are Eq in conditions
    assert Piecewise(
        (a, And(Eq(a, 0), Eq(a + b, 0))), (1, True)).simplify(
        ) == Piecewise(
        (0, And(Eq(a, 0), Eq(b, 0))), (1, True))
    assert Piecewise((2*x*factorial(a)/(factorial(y)*factorial(-y + a)),
        Eq(y, 0) & Eq(-y + a, 0)), (2*factorial(a)/(factorial(y)*factorial(-y
        + a)), Eq(y, 0) & Eq(-y + a, 1)), (0, True)).simplify(
        ) == Piecewise(
            (2*x, And(Eq(a, 0), Eq(y, 0))),
            (2, And(Eq(a, 1), Eq(y, 0))),
            (0, True))
    args = (2, And(Eq(x, 2), Ge(y ,0))), (x, True)
    assert Piecewise(*args).simplify() == Piecewise(*args)
    args = (1, Eq(x, 0)), (sin(x)/x, True)
    assert Piecewise(*args).simplify() == Piecewise(*args)
    assert Piecewise((2 + y, And(Eq(x, 2), Eq(y, 0))), (x, True)
        ).simplify() == x
    # check that x or f(x) are recognized as being Symbol-like for lhs
    args = Tuple((1, Eq(x, 0)), (sin(x) + 1 + x, True))
    ans = x + sin(x) + 1
    f = Function('f')
    assert Piecewise(*args).simplify() == ans
    assert Piecewise(*args.subs(x, f(x))).simplify() == ans.subs(x, f(x))


def test_piecewise_solve():
    abs2 = Piecewise((-x, x <= 0), (x, x > 0))
    f = abs2.subs(x, x - 2)
    assert solve(f, x) == [2]
    assert solve(f - 1, x) == [1, 3]

    f = Piecewise(((x - 2)**2, x >= 0), (1, True))
    assert solve(f, x) == [2]

    g = Piecewise(((x - 5)**5, x >= 4), (f, True))
    assert solve(g, x) == [2, 5]

    g = Piecewise(((x - 5)**5, x >= 4), (f, x < 4))
    assert solve(g, x) == [2, 5]

    g = Piecewise(((x - 5)**5, x >= 2), (f, x < 2))
    assert solve(g, x) == [5]

    g = Piecewise(((x - 5)**5, x >= 2), (f, True))
    assert solve(g, x) == [5]

    g = Piecewise(((x - 5)**5, x >= 2), (f, True), (10, False))
    assert solve(g, x) == [5]

    g = Piecewise(((x - 5)**5, x >= 2),
                  (-x + 2, x - 2 <= 0), (x - 2, x - 2 > 0))
    assert solve(g, x) == [5]

    # if no symbol is given the piecewise detection must still work
    assert solve(Piecewise((x - 2, x > 2), (2 - x, True)) - 3) == [-1, 5]

    f = Piecewise(((x - 2)**2, x >= 0), (0, True))
    raises(NotImplementedError, lambda: solve(f, x))

    def nona(ans):
        return list(filter(lambda x: x is not S.NaN, ans))
    p = Piecewise((x**2 - 4, x < y), (x - 2, True))
    ans = solve(p, x)
    assert nona([i.subs(y, -2) for i in ans]) == [2]
    assert nona([i.subs(y, 2) for i in ans]) == [-2, 2]
    assert nona([i.subs(y, 3) for i in ans]) == [-2, 2]
    assert ans == [
        Piecewise((-2, y > -2), (S.NaN, True)),
        Piecewise((2, y <= 2), (S.NaN, True)),
        Piecewise((2, y > 2), (S.NaN, True))]

    # issue 6060
    absxm3 = Piecewise(
        (x - 3, S(0) <= x - 3),
        (3 - x, S(0) > x - 3)
    )
    assert solve(absxm3 - y, x) == [
        Piecewise((-y + 3, -y < 0), (S.NaN, True)),
        Piecewise((y + 3, y >= 0), (S.NaN, True))]
    p = Symbol('p', positive=True)
    assert solve(absxm3 - p, x) == [-p + 3, p + 3]

    # issue 6989
    f = Function('f')
    assert solve(Eq(-f(x), Piecewise((1, x > 0), (0, True))), f(x)) == \
        [Piecewise((-1, x > 0), (0, True))]

    # issue 8587
    f = Piecewise((2*x**2, And(S(0) < x, x < 1)), (2, True))
    assert solve(f - 1) == [1/sqrt(2)]


def test_piecewise_fold():
    p = Piecewise((x, x < 1), (1, 1 <= x))

    assert piecewise_fold(x*p) == Piecewise((x**2, x < 1), (x, 1 <= x))
    assert piecewise_fold(p + p) == Piecewise((2*x, x < 1), (2, 1 <= x))
    assert piecewise_fold(Piecewise((1, x < 0), (2, True))
                          + Piecewise((10, x < 0), (-10, True))) == \
        Piecewise((11, x < 0), (-8, True))

    p1 = Piecewise((0, x < 0), (x, x <= 1), (0, True))
    p2 = Piecewise((0, x < 0), (1 - x, x <= 1), (0, True))

    p = 4*p1 + 2*p2
    assert integrate(
        piecewise_fold(p), (x, -oo, oo)) == integrate(2*x + 2, (x, 0, 1))

    assert piecewise_fold(
        Piecewise((1, y <= 0), (-Piecewise((2, y >= 0)), True)
        )) == Piecewise((1, y <= 0), (-2, y >= 0))

    assert piecewise_fold(Piecewise((x, ITE(x > 0, y < 1, y > 1)))
        ) == Piecewise((x, ((x <= 0) | (y < 1)) & ((x > 0) | (y > 1))))

    a, b = (Piecewise((2, Eq(x, 0)), (0, True)),
        Piecewise((x, Eq(-x + y, 0)), (1, Eq(-x + y, 1)), (0, True)))
    assert piecewise_fold(Mul(a, b, evaluate=False)
        ) == piecewise_fold(Mul(b, a, evaluate=False))


def test_piecewise_fold_piecewise_in_cond():
    p1 = Piecewise((cos(x), x < 0), (0, True))
    p2 = Piecewise((0, Eq(p1, 0)), (p1 / Abs(p1), True))
    p3 = piecewise_fold(p2)
    assert(p2.subs(x, -pi/2) == 0.0)
    assert(p2.subs(x, 1) == 0.0)
    assert(p2.subs(x, -pi/4) == 1.0)
    p4 = Piecewise((0, Eq(p1, 0)), (1,True))
    ans = piecewise_fold(p4)
    for i in range(-1, 1):
        assert ans.subs(x, i) == p4.subs(x, i)

    r1 = 1 < Piecewise((1, x < 1), (3, True))
    ans = piecewise_fold(r1)
    for i in range(2):
        assert ans.subs(x, i) == r1.subs(x, i)

    p5 = Piecewise((1, x < 0), (3, True))
    p6 = Piecewise((1, x < 1), (3, True))
    p7 = Piecewise((1, p5 < p6), (0, True))
    ans = piecewise_fold(p7)
    for i in range(-1, 2):
        assert ans.subs(x, i) == p7.subs(x, i)


def test_piecewise_fold_piecewise_in_cond_2():
    p1 = Piecewise((cos(x), x < 0), (0, True))
    p2 = Piecewise((0, Eq(p1, 0)), (1 / p1, True))
    p3 = Piecewise(
        (0, (x >= 0) | Eq(cos(x), 0)),
        (1/cos(x), x < 0),
        (zoo, True))  # redundant b/c all x are already covered
    assert(piecewise_fold(p2) == p3)


def test_piecewise_fold_expand():
    p1 = Piecewise((1, Interval(0, 1, False, True).contains(x)), (0, True))

    p2 = piecewise_fold(expand((1 - x)*p1))
    assert p2 == Piecewise((1 - x, (x >= 0) & (x < 1)), (0, True))
    assert p2 == expand(piecewise_fold((1 - x)*p1))


def test_piecewise_duplicate():
    p = Piecewise((x, x < -10), (x**2, x <= -1), (x, 1 < x))
    assert p == Piecewise(*p.args)


def test_doit():
    p1 = Piecewise((x, x < 1), (x**2, -1 <= x), (x, 3 < x))
    p2 = Piecewise((x, x < 1), (Integral(2 * x), -1 <= x), (x, 3 < x))
    assert p2.doit() == p1
    assert p2.doit(deep=False) == p2


def test_piecewise_interval():
    p1 = Piecewise((x, Interval(0, 1).contains(x)), (0, True))
    assert p1.subs(x, -0.5) == 0
    assert p1.subs(x, 0.5) == 0.5
    assert p1.diff(x) == Piecewise((1, Interval(0, 1).contains(x)), (0, True))
    assert integrate(p1, x) == Piecewise(
        (0, x <= 0),
        (x**2/2, x <= 1),
        (S(1)/2, True))


def test_piecewise_collapse():
    assert Piecewise((x, True)) == x
    a = x < 1
    assert Piecewise((x, a), (x + 1, a)) == Piecewise((x, a))
    assert Piecewise((x, a), (x + 1, a.reversed)) == Piecewise((x, a))
    b = x < 5
    def canonical(i):
        if isinstance(i, Piecewise):
            return Piecewise(*i.args)
        return i
    for args in [
        ((1, a), (Piecewise((2, a), (3, b)), b)),
        ((1, a), (Piecewise((2, a), (3, b.reversed)), b)),
        ((1, a), (Piecewise((2, a), (3, b)), b), (4, True)),
        ((1, a), (Piecewise((2, a), (3, b), (4, True)), b)),
        ((1, a), (Piecewise((2, a), (3, b), (4, True)), b), (5, True))]:
        for i in (0, 2, 10):
            assert canonical(
                Piecewise(*args, evaluate=False).subs(x, i)
                ) == canonical(Piecewise(*args).subs(x, i))
    r1, r2, r3, r4 = symbols('r1:5')
    a = x < r1
    b = x < r2
    c = x < r3
    d = x < r4
    assert Piecewise((1, a), (Piecewise(
        (2, a), (3, b), (4, c)), b), (5, c)
        ) == Piecewise((1, a), (3, b), (5, c))
    assert Piecewise((1, a), (Piecewise(
        (2, a), (3, b), (4, c), (6, True)), c), (5, d)
        ) == Piecewise((1, a), (Piecewise(
        (3, b), (4, c)), c), (5, d))
    assert Piecewise((1, Or(a, d)), (Piecewise(
        (2, d), (3, b), (4, c)), b), (5, c)
        ) == Piecewise((1, Or(a, d)), (Piecewise(
        (2, d), (3, b)), b), (5, c))
    assert Piecewise((1, c), (2, ~c), (3, S.true)
        ) == Piecewise((1, c), (2, S.true))
    assert Piecewise((1, c), (2, And(~c, b)), (3,True)
        ) == Piecewise((1, c), (2, b), (3, True))
    assert Piecewise((1, c), (2, Or(~c, b)), (3,True)
        ).subs(dict(zip((r1, r2, r3, r4, x), (1, 2, 3, 4, 3.5))))  == 2
    assert Piecewise((1, c), (2, ~c)) == Piecewise((1, c), (2, True))


def test_piecewise_lambdify():
    p = Piecewise(
        (x**2, x < 0),
        (x, Interval(0, 1, False, True).contains(x)),
        (2 - x, x >= 1),
        (0, True)
    )

    f = lambdify(x, p)
    assert f(-2.0) == 4.0
    assert f(0.0) == 0.0
    assert f(0.5) == 0.5
    assert f(2.0) == 0.0


def test_piecewise_series():
    from sympy import sin, cos, O
    p1 = Piecewise((sin(x), x < 0), (cos(x), x > 0))
    p2 = Piecewise((x + O(x**2), x < 0), (1 + O(x**2), x > 0))
    assert p1.nseries(x, n=2) == p2


def test_piecewise_as_leading_term():
    p1 = Piecewise((1/x, x > 1), (0, True))
    p2 = Piecewise((x, x > 1), (0, True))
    p3 = Piecewise((1/x, x > 1), (x, True))
    p4 = Piecewise((x, x > 1), (1/x, True))
    p5 = Piecewise((1/x, x > 1), (x, True))
    p6 = Piecewise((1/x, x < 1), (x, True))
    p7 = Piecewise((x, x < 1), (1/x, True))
    p8 = Piecewise((x, x > 1), (1/x, True))
    assert p1.as_leading_term(x) == 0
    assert p2.as_leading_term(x) == 0
    assert p3.as_leading_term(x) == x
    assert p4.as_leading_term(x) == 1/x
    assert p5.as_leading_term(x) == x
    assert p6.as_leading_term(x) == 1/x
    assert p7.as_leading_term(x) == x
    assert p8.as_leading_term(x) == 1/x


def test_piecewise_complex():
    p1 = Piecewise((2, x < 0), (1, 0 <= x))
    p2 = Piecewise((2*I, x < 0), (I, 0 <= x))
    p3 = Piecewise((I*x, x > 1), (1 + I, True))
    p4 = Piecewise((-I*conjugate(x), x > 1), (1 - I, True))

    assert conjugate(p1) == p1
    assert conjugate(p2) == piecewise_fold(-p2)
    assert conjugate(p3) == p4

    assert p1.is_imaginary is False
    assert p1.is_real is True
    assert p2.is_imaginary is True
    assert p2.is_real is False
    assert p3.is_imaginary is None
    assert p3.is_real is None

    assert p1.as_real_imag() == (p1, 0)
    assert p2.as_real_imag() == (0, -I*p2)


def test_conjugate_transpose():
    A, B = symbols("A B", commutative=False)
    p = Piecewise((A*B**2, x > 0), (A**2*B, True))
    assert p.adjoint() == \
        Piecewise((adjoint(A*B**2), x > 0), (adjoint(A**2*B), True))
    assert p.conjugate() == \
        Piecewise((conjugate(A*B**2), x > 0), (conjugate(A**2*B), True))
    assert p.transpose() == \
        Piecewise((transpose(A*B**2), x > 0), (transpose(A**2*B), True))


def test_piecewise_evaluate():
    assert Piecewise((x, True)) == x
    assert Piecewise((x, True), evaluate=True) == x
    p = Piecewise((x, True), evaluate=False)
    assert p != x
    assert p.is_Piecewise
    assert all(isinstance(i, Basic) for i in p.args)
    assert Piecewise((1, Eq(1, x))).args == ((1, Eq(x, 1)),)
    assert Piecewise((1, Eq(1, x)), evaluate=False).args == (
        (1, Eq(1, x)),)


def test_as_expr_set_pairs():
    assert Piecewise((x, x > 0), (-x, x <= 0)).as_expr_set_pairs() == \
        [(x, Interval(0, oo, True, True)), (-x, Interval(-oo, 0))]

    assert Piecewise(((x - 2)**2, x >= 0), (0, True)).as_expr_set_pairs() == \
        [((x - 2)**2, Interval(0, oo)), (0, Interval(-oo, 0, True, True))]


def test_S_srepr_is_identity():
    p = Piecewise((10, Eq(x, 0)), (12, True))
    q = S(srepr(p))
    assert p == q


def test_issue_12587():
    # sort holes into intervals
    p = Piecewise((1, x > 4), (2, Not((x <= 3) & (x > -1))), (3, True))
    assert p.integrate((x, -5, 5)) == 23
    p = Piecewise((1, x > 1), (2, x < y), (3, True))
    lim = x, -3, 3
    ans = p.integrate(lim)
    for i in range(-1, 3):
        assert ans.subs(y, i) == p.subs(y, i).integrate(lim)


def test_issue_11045():
    assert integrate(1/(x*sqrt(x**2 - 1)), (x, 1, 2)) == pi/3

    # handle And with Or arguments
    assert Piecewise((1, And(Or(x < 1, x > 3), x < 2)), (0, True)
        ).integrate((x, 0, 3)) == 1

    # hidden false
    assert Piecewise((1, x > 1), (2, x > x + 1), (3, True)
        ).integrate((x, 0, 3)) == 5
    # targetcond is Eq
    assert Piecewise((1, x > 1), (2, Eq(1, x)), (3, True)
        ).integrate((x, 0, 4)) == 6
    # And has Relational needing to be solved
    assert Piecewise((1, And(2*x > x + 1, x < 2)), (0, True)
        ).integrate((x, 0, 3)) == 1
    # Or has Relational needing to be solved
    assert Piecewise((1, Or(2*x > x + 2, x < 1)), (0, True)
        ).integrate((x, 0, 3)) == 2
    # ignore hidden false (handled in canonicalization)
    assert Piecewise((1, x > 1), (2, x > x + 1), (3, True)
        ).integrate((x, 0, 3)) == 5
    # watch for hidden True Piecewise
    assert Piecewise((2, Eq(1 - x, x*(1/x - 1))), (0, True)
        ).integrate((x, 0, 3)) == 6

    # overlapping conditions of targetcond are recognized and ignored;
    # the condition x > 3 will be pre-empted by the first condition
    assert Piecewise((1, Or(x < 1, x > 2)), (2, x > 3), (3, True)
        ).integrate((x, 0, 4)) == 6

    # convert Ne to Or
    assert Piecewise((1, Ne(x, 0)), (2, True)
        ).integrate((x, -1, 1)) == 2

    # no default but well defined
    assert Piecewise((x, (x > 1) & (x < 3)), (1, (x < 4))
        ).integrate((x, 1, 4)) == 5

    p = Piecewise((x, (x > 1) & (x < 3)), (1, (x < 4)))
    nan = Undefined
    i = p.integrate((x, 1, y))
    assert i == Piecewise(
        (y - 1, y < 1),
        (Min(3, y)**2/2 - Min(3, y) + Min(4, y) - S(1)/2,
            y <= Min(4, y)),
        (nan, True))
    assert p.integrate((x, 1, -1)) == i.subs(y, -1)
    assert p.integrate((x, 1, 4)) == 5
    assert p.integrate((x, 1, 5)) == nan

    # handle Not
    p = Piecewise((1, x > 1), (2, Not(And(x > 1, x< 3))), (3, True))
    assert p.integrate((x, 0, 3)) == 4

    # handle updating of int_expr when there is overlap
    p = Piecewise(
        (1, And(5 > x, x > 1)),
        (2, Or(x < 3, x > 7)),
        (4, x < 8))
    assert p.integrate((x, 0, 10)) == 20

    # And with Eq arg handling
    assert Piecewise((1, x < 1), (2, And(Eq(x, 3), x > 1))
        ).integrate((x, 0, 3)) == S.NaN
    assert Piecewise((1, x < 1), (2, And(Eq(x, 3), x > 1)), (3, True)
        ).integrate((x, 0, 3)) == 7
    assert Piecewise((1, x < 0), (2, And(Eq(x, 3), x < 1)), (3, True)
        ).integrate((x, -1, 1)) == 4
    # middle condition doesn't matter: it's a zero width interval
    assert Piecewise((1, x < 1), (2, Eq(x, 3) & (y < x)), (3, True)
        ).integrate((x, 0, 3)) == 7


def test_holes():
    nan = Undefined
    assert Piecewise((1, x < 2)).integrate(x) == Piecewise(
        (x, x < 2), (nan, True))
    assert Piecewise((1, And(x > 1, x < 2))).integrate(x) == Piecewise(
        (nan, x < 1), (x - 1, x < 2), (nan, True))
    assert Piecewise((1, And(x > 1, x < 2))).integrate((x, 0, 3)) == nan
    assert Piecewise((1, And(x > 0, x < 4))).integrate((x, 1, 3)) == 2

    # this also tests that the integrate method is used on non-Piecwise
    # arguments in _eval_integral
    A, B = symbols("A B")
    a, b = symbols('a b', finite=True)
    assert Piecewise((A, And(x < 0, a < 1)), (B, Or(x < 1, a > 2))
        ).integrate(x) == Piecewise(
        (B*x, a > 2),
        (Piecewise((A*x, x < 0), (B*x, x < 1), (nan, True)), a < 1),
        (Piecewise((B*x, x < 1), (nan, True)), True))


def test_issue_11922():
    def f(x):
        return Piecewise((0, x < -1), (1 - x**2, x < 1), (0, True))
    autocorr = lambda k: (
        f(x) * f(x + k)).integrate((x, -1, 1))
    assert autocorr(1.9) > 0
    k = symbols('k')
    good_autocorr = lambda k: (
        (1 - x**2) * f(x + k)).integrate((x, -1, 1))
    a = good_autocorr(k)
    assert a.subs(k, 3) == 0
    k = symbols('k', positive=True)
    a = good_autocorr(k)
    assert a.subs(k, 3) == 0
    assert Piecewise((0, x < 1), (10, (x >= 1))
        ).integrate() == Piecewise((0, x < 1), (10*x - 10, True))


def test_issue_5227():
    f = 0.0032513612725229*Piecewise((0, x < -80.8461538461539),
        (-0.0160799238820171*x + 1.33215984776403, x < 2),
        (Piecewise((0.3, x > 123), (0.7, True)) +
        Piecewise((0.4, x > 2), (0.6, True)), x <=
        123), (-0.00817409766454352*x + 2.10541401273885, x <
        380.571428571429), (0, True))
    i = integrate(f, (x, -oo, oo))
    assert i == Integral(f, (x, -oo, oo)).doit()
    assert str(i) == '1.00195081676351'
    assert Piecewise((1, x - y < 0), (0, True)
        ).integrate(y) == Piecewise((0, y <= x), (-x + y, True))


def test_issue_10137():
    a = Symbol('a', real=True, finite=True)
    b = Symbol('b', real=True, finite=True)
    x = Symbol('x', real=True, finite=True)
    y = Symbol('y', real=True, finite=True)
    p0 = Piecewise((0, Or(x < a, x > b)), (1, True))
    p1 = Piecewise((0, Or(a > x, b < x)), (1, True))
    assert integrate(p0, (x, y, oo)) == integrate(p1, (x, y, oo))
    p3 = Piecewise((1, And(0 < x, x < a)), (0, True))
    p4 = Piecewise((1, And(a > x, x > 0)), (0, True))
    ip3 = integrate(p3, x)
    assert ip3 == Piecewise(
        (0, x <= 0),
        (x, x <= Max(0, a)),
        (Max(0, a), True))
    ip4 = integrate(p4, x)
    assert ip4 == ip3
    assert p3.integrate((x, 2, 4)) == Min(4, Max(2, a)) - 2
    assert p4.integrate((x, 2, 4)) == Min(4, Max(2, a)) - 2


def test_stackoverflow_43852159():
    f = lambda x: Piecewise((1 , (x >= -1) & (x <= 1)) , (0, True))
    Conv = lambda x: integrate(f(x - y)*f(y), (y, -oo, +oo))
    cx = Conv(x)
    assert cx.subs(x, -1.5) == cx.subs(x, 1.5)
    assert cx.subs(x, 3) == 0
    assert piecewise_fold(f(x - y)*f(y)) == Piecewise(
        (1, (y >= -1) & (y <= 1) & (x - y >= -1) & (x - y <= 1)),
        (0, True))


def test_issue_12557():
    '''
    # 3200 seconds to compute the fourier part of issue
    import sympy as sym
    x,y,z,t = sym.symbols('x y z t')
    k = sym.symbols("k", integer=True)
    fourier = sym.fourier_series(sym.cos(k*x)*sym.sqrt(x**2),
                                 (x, -sym.pi, sym.pi))
    assert fourier == FourierSeries(
    sqrt(x**2)*cos(k*x), (x, -pi, pi), (Piecewise((pi**2,
    Eq(k, 0)), (2*(-1)**k/k**2 - 2/k**2, True))/(2*pi),
    SeqFormula(Piecewise((pi**2, (Eq(_n, 0) & Eq(k, 0)) | (Eq(_n, 0) &
    Eq(_n, k) & Eq(k, 0)) | (Eq(_n, 0) & Eq(k, 0) & Eq(_n, -k)) | (Eq(_n,
    0) & Eq(_n, k) & Eq(k, 0) & Eq(_n, -k))), (pi**2/2, Eq(_n, k) | Eq(_n,
    -k) | (Eq(_n, 0) & Eq(_n, k)) | (Eq(_n, k) & Eq(k, 0)) | (Eq(_n, 0) &
    Eq(_n, -k)) | (Eq(_n, k) & Eq(_n, -k)) | (Eq(k, 0) & Eq(_n, -k)) |
    (Eq(_n, 0) & Eq(_n, k) & Eq(_n, -k)) | (Eq(_n, k) & Eq(k, 0) & Eq(_n,
    -k))), ((-1)**k*pi**2*_n**3*sin(pi*_n)/(pi*_n**4 - 2*pi*_n**2*k**2 +
    pi*k**4) - (-1)**k*pi**2*_n**3*sin(pi*_n)/(-pi*_n**4 + 2*pi*_n**2*k**2
    - pi*k**4) + (-1)**k*pi*_n**2*cos(pi*_n)/(pi*_n**4 - 2*pi*_n**2*k**2 +
    pi*k**4) - (-1)**k*pi*_n**2*cos(pi*_n)/(-pi*_n**4 + 2*pi*_n**2*k**2 -
    pi*k**4) - (-1)**k*pi**2*_n*k**2*sin(pi*_n)/(pi*_n**4 -
    2*pi*_n**2*k**2 + pi*k**4) +
    (-1)**k*pi**2*_n*k**2*sin(pi*_n)/(-pi*_n**4 + 2*pi*_n**2*k**2 -
    pi*k**4) + (-1)**k*pi*k**2*cos(pi*_n)/(pi*_n**4 - 2*pi*_n**2*k**2 +
    pi*k**4) - (-1)**k*pi*k**2*cos(pi*_n)/(-pi*_n**4 + 2*pi*_n**2*k**2 -
    pi*k**4) - (2*_n**2 + 2*k**2)/(_n**4 - 2*_n**2*k**2 + k**4),
    True))*cos(_n*x)/pi, (_n, 1, oo)), SeqFormula(0, (_k, 1, oo))))
    '''
    x = symbols("x", real=True)
    k = symbols('k', integer=True, finite=True)
    abs2 = lambda x: Piecewise((-x, x <= 0), (x, x > 0))
    assert integrate(abs2(x), (x, -pi, pi)) == pi**2
    func = cos(k*x)*sqrt(x**2)
    assert integrate(func, (x, -pi, pi)) == Piecewise(
        (2*(-1)**k/k**2 - 2/k**2, Ne(k, 0)), (pi**2, True))

def test_issue_6900():
    from itertools import permutations
    t0, t1, T, t = symbols('t0, t1 T t')
    f = Piecewise((0, t < t0), (x, And(t0 <= t, t < t1)), (0, t >= t1))
    g = f.integrate(t)
    assert g == Piecewise(
        (0, t <= t0),
        (t*x - t0*x, t <= Max(t0, t1)),
        (-t0*x + x*Max(t0, t1), True))
    for i in permutations(range(2)):
        reps = dict(zip((t0,t1), i))
        for tt in range(-1,3):
            assert (g.xreplace(reps).subs(t,tt) ==
                f.xreplace(reps).integrate(t).subs(t,tt))
    lim = Tuple(t, t0, T)
    g = f.integrate(lim)
    ans = Piecewise(
        (-t0*x + x*Min(T, Max(t0, t1)), T > t0),
        (0, True))
    for i in permutations(range(3)):
        reps = dict(zip((t0,t1,T), i))
        tru = f.xreplace(reps).integrate(lim.xreplace(reps))
        assert tru == ans.xreplace(reps)
    assert g == ans


def test_issue_10122():
    assert solve(abs(x) + abs(x - 1) - 1 > 0, x
        ) == Or(And(-oo < x, x < 0), And(S.One < x, x < oo))


def test_issue_4313():
    u = Piecewise((0, x <= 0), (1, x >= a), (x/a, True))
    e = (u - u.subs(x, y))**2/(x - y)**2
    M = Max(0, a)
    assert integrate(e,  x).expand() == Piecewise(
        (Piecewise(
            (0, x <= 0),
            (-y**2/(a**2*x - a**2*y) + x/a**2 - 2*y*log(-y)/a**2 +
                2*y*log(x - y)/a**2 - y/a**2, x <= M),
            (-y**2/(-a**2*y + a**2*M) + 1/(-y + M) -
                1/(x - y) - 2*y*log(-y)/a**2 + 2*y*log(-y +
                M)/a**2 - y/a**2 + M/a**2, True)),
        ((a <= y) & (y <= 0)) | ((y <= 0) & (y > -oo))),
        (Piecewise(
            (-1/(x - y), x <= 0),
            (-a**2/(a**2*x - a**2*y) + 2*a*y/(a**2*x - a**2*y) -
                y**2/(a**2*x - a**2*y) + 2*log(-y)/a - 2*log(x - y)/a +
                2/a + x/a**2 - 2*y*log(-y)/a**2 + 2*y*log(x - y)/a**2 -
                y/a**2, x <= M),
            (-a**2/(-a**2*y + a**2*M) + 2*a*y/(-a**2*y +
                a**2*M) - y**2/(-a**2*y + a**2*M) +
                2*log(-y)/a - 2*log(-y + M)/a + 2/a -
                2*y*log(-y)/a**2 + 2*y*log(-y + M)/a**2 -
                y/a**2 + M/a**2, True)),
        a <= y),
        (Piecewise(
            (-y**2/(a**2*x - a**2*y), x <= 0),
            (x/a**2 + y/a**2, x <= M),
            (a**2/(-a**2*y + a**2*M) -
                a**2/(a**2*x - a**2*y) - 2*a*y/(-a**2*y + a**2*M) +
                2*a*y/(a**2*x - a**2*y) + y**2/(-a**2*y + a**2*M) -
                y**2/(a**2*x - a**2*y) + y/a**2 + M/a**2, True)),
        True))


def test__intervals():
    assert Piecewise((x + 2, Eq(x, 3)))._intervals(x) == []
    assert Piecewise(
        (1, x > x + 1),
        (Piecewise((1, x < x + 1)), 2*x < 2*x + 1),
        (1, True))._intervals(x) == [(-oo, oo, 1, 1)]
    assert Piecewise((1, Ne(x, I)), (0, True))._intervals(x) == [
        (-oo, oo, 1, 0)]
    assert Piecewise((-cos(x), sin(x) >= 0), (cos(x), True)
        )._intervals(x) == [(0, pi, -cos(x), 0), (-oo, oo, cos(x), 1)]
    # the following tests that duplicates are removed and that non-Eq
    # generated zero-width intervals are removed
    assert Piecewise((1, Abs(x**(-2)) > 1), (0, True)
        )._intervals(x) == [(-1, 0, 1, 0), (0, 1, 1, 0), (-oo, oo, 0, 1)]


def test_containment():
    a, b, c, d, e = [1, 2, 3, 4, 5]
    p = (Piecewise((d, x > 1), (e, True))*
        Piecewise((a, Abs(x - 1) < 1), (b, Abs(x - 2) < 2), (c, True)))
    assert p.integrate(x).diff(x) == Piecewise(
        (c*e, x <= 0),
        (a*e, x <= 1),
        (a*d, x < 2),  # this is what we want to get right
        (b*d, x < 4),
        (c*d, True))


def test_piecewise_with_DiracDelta():
    d1 = DiracDelta(x - 1)
    assert integrate(d1, (x, -oo, oo)) == 1
    assert integrate(d1, (x, 0, 2)) == 1
    assert Piecewise((d1, Eq(x, 2)), (0, True)).integrate(x) == 0
    assert Piecewise((d1, x < 2), (0, True)).integrate(x) == Piecewise(
        (Heaviside(x - 1), x < 2), (1, True))
    # TODO raise error if function is discontinuous at limit of
    # integration, e.g. integrate(d1, (x, -2, 1)) or Piecewise(
    # (d1, Eq(x ,1)


def test_issue_10258():
    assert Piecewise((0, x < 1), (1, True)).is_zero is None
    assert Piecewise((-1, x < 1), (1, True)).is_zero is False
    a = Symbol('a', zero=True)
    assert Piecewise((0, x < 1), (a, True)).is_zero
    assert Piecewise((1, x < 1), (a, x < 3)).is_zero is None
    a = Symbol('a')
    assert Piecewise((0, x < 1), (a, True)).is_zero is None
    assert Piecewise((0, x < 1), (1, True)).is_nonzero is None
    assert Piecewise((1, x < 1), (2, True)).is_nonzero
    assert Piecewise((0, x < 1), (oo, True)).is_finite is None
    assert Piecewise((0, x < 1), (1, True)).is_finite
    b = Basic()
    assert Piecewise((b, x < 1)).is_finite is None

    # 10258
    c = Piecewise((1, x < 0), (2, True)) < 3
    assert c != True
    assert piecewise_fold(c) == True


def test_issue_10087():
    a, b = Piecewise((x, x > 1), (2, True)), Piecewise((x, x > 3), (3, True))
    m = a*b
    f = piecewise_fold(m)
    for i in (0, 2, 4):
        assert m.subs(x, i) == f.subs(x, i)
    m = a + b
    f = piecewise_fold(m)
    for i in (0, 2, 4):
        assert m.subs(x, i) == f.subs(x, i)


def test_issue_8919():
    c = symbols('c:5')
    x = symbols("x")
    f1 = Piecewise((c[1], x < 1), (c[2], True))
    f2 = Piecewise((c[3], x < S(1)/3), (c[4], True))
    assert integrate(f1*f2, (x, 0, 2)
        ) == c[1]*c[3]/3 + 2*c[1]*c[4]/3 + c[2]*c[4]
    f1 = Piecewise((0, x < 1), (2, True))
    f2 = Piecewise((3, x < 2), (0, True))
    assert integrate(f1*f2, (x, 0, 3)) == 6

    y = symbols("y", positive=True)
    a, b, c, x, z = symbols("a,b,c,x,z", real=True)
    I = Integral(Piecewise(
        (0, (x >= y) | (x < 0) | (b > c)),
        (a, True)), (x, 0, z))
    ans = I.doit()
    assert ans == Piecewise((0, b > c), (a*Min(y, z) - a*Min(0, z), True))
    for cond in (True, False):
         for yy in range(1, 3):
             for zz in range(-yy, 0, yy):
                 reps = [(b > c, cond), (y, yy), (z, zz)]
                 assert ans.subs(reps) == I.subs(reps).doit()


def test_unevaluated_integrals():
    f = Function('f')
    p = Piecewise((1, Eq(f(x) - 1, 0)), (2, x - 10 < 0), (0, True))
    assert p.integrate(x) == Integral(p, x)
    assert p.integrate((x, 0, 5)) == Integral(p, (x, 0, 5))
    # test it by replacing f(x) with x%2 which will not
    # affect the answer: the integrand is essentially 2 over
    # the domain of integration
    assert Integral(p, (x, 0, 5)).subs(f(x), x%2).n() == 10

    # this is a test of using _solve_inequality when
    # solve_univariate_inequality fails
    assert p.integrate(y) == Piecewise(
        (y, Eq(f(x), 1) | ((x < 10) & Eq(f(x), 1))),
        (2*y, (x >= -oo) & (x < 10)), (0, True))


def test_conditions_as_alternate_booleans():
    a, b, c = symbols('a:c')
    assert Piecewise((x, Piecewise((y < 1, x > 0), (y > 1, True)))
        ) == Piecewise((x, ITE(x > 0, y < 1, y > 1)))


def test_Piecewise_rewrite_as_ITE():
    a, b, c, d = symbols('a:d')

    def _ITE(*args):
        return Piecewise(*args).rewrite(ITE)

    assert _ITE((a, x < 1), (b, x >= 1)) == ITE(x < 1, a, b)
    assert _ITE((a, x < 1), (b, x < oo)) == ITE(x < 1, a, b)
    assert _ITE((a, x < 1), (b, Or(y < 1, x < oo)), (c, y > 0)
               ) == ITE(x < 1, a, b)
    assert _ITE((a, x < 1), (b, True)) == ITE(x < 1, a, b)
    assert _ITE((a, x < 1), (b, x < 2), (c, True)
               ) == ITE(x < 1, a, ITE(x < 2, b, c))
    assert _ITE((a, x < 1), (b, y < 2), (c, True)
               ) == ITE(x < 1, a, ITE(y < 2, b, c))
    assert _ITE((a, x < 1), (b, x < oo), (c, y < 1)
               ) == ITE(x < 1, a, b)
    assert _ITE((a, x < 1), (c, y < 1), (b, x < oo), (d, True)
               ) == ITE(x < 1, a, ITE(y < 1, c, b))
    assert _ITE((a, x < 0), (b, Or(x < oo, y < 1))
               ) == ITE(x < 0, a, b)
    raises(TypeError, lambda: _ITE((x + 1, x < 1), (x, True)))
    # if `a` in the following were replaced with y then the coverage
    # is complete but something other than as_set would need to be
    # used to detect this
    raises(NotImplementedError, lambda: _ITE((x, x < y), (y, x >= a)))
    raises(ValueError, lambda: _ITE((a, x < 2), (b, x > 3)))


def test_issue_14052():
    assert integrate(abs(sin(x)), (x, 0, 2*pi)) == 4


def test_issue_14240():
    assert piecewise_fold(
        Piecewise((1, a), (2, b), (4, True)) +
        Piecewise((8, a), (16, True))
        ) == Piecewise((9, a), (18, b), (20, True))
    assert piecewise_fold(
        Piecewise((2, a), (3, b), (5, True)) *
        Piecewise((7, a), (11, True))
        ) == Piecewise((14, a), (33, b), (55, True))
    # these will hang if naive folding is used
    assert piecewise_fold(Add(*[
        Piecewise((i, a), (0, True)) for i in range(40)])
        ) == Piecewise((780, a), (0, True))
    assert piecewise_fold(Mul(*[
        Piecewise((i, a), (0, True)) for i in range(1, 41)])
        ) == Piecewise((factorial(40), a), (0, True))


def test_issue_14787():
    x = Symbol('x')
    f = Piecewise((x, x < 1), ((S(58) / 7), True))
    assert str(f.evalf()) == "Piecewise((x, x < 1), (8.28571428571429, True))"


def test_issue_8458():
    x, y = symbols('x y')
    # Original issue
    p1 = Piecewise((0, Eq(x, 0)), (sin(x), True))
    assert p1.simplify() == sin(x)
    # Slightly larger variant
    p2 = Piecewise((x, Eq(x, 0)), (4*x + (y-2)**4, Eq(x, 0) & Eq(x+y, 2)), (sin(x), True))
    assert p2.simplify() == sin(x)
    # Test for problem highlighted during review
    p3 = Piecewise((x+1, Eq(x, -1)), (4*x + (y-2)**4, Eq(x, 0) & Eq(x+y, 2)), (sin(x), True))
    assert p3.simplify() == Piecewise((0, Eq(x, -1)), (sin(x), True))
