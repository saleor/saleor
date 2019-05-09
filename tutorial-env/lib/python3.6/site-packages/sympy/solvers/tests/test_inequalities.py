"""Tests for tools for solving inequalities and systems of inequalities. """

from sympy import (And, Eq, FiniteSet, Ge, Gt, Interval, Le, Lt, Ne, oo, I,
                   Or, S, sin, cos, tan, sqrt, Symbol, Union, Integral, Sum,
                   Function, Poly, PurePoly, pi, root, log, exp, Dummy, Abs)
from sympy.solvers.inequalities import (reduce_inequalities,
                                        solve_poly_inequality as psolve,
                                        reduce_rational_inequalities,
                                        solve_univariate_inequality as isolve,
                                        reduce_abs_inequality,
                                        _solve_inequality)
from sympy.polys.rootoftools import rootof
from sympy.solvers.solvers import solve
from sympy.solvers.solveset import solveset
from sympy.abc import x, y

from sympy.utilities.pytest import raises, slow, XFAIL


inf = oo.evalf()


def test_solve_poly_inequality():
    assert psolve(Poly(0, x), '==') == [S.Reals]
    assert psolve(Poly(1, x), '==') == [S.EmptySet]
    assert psolve(PurePoly(x + 1, x), ">") == [Interval(-1, oo, True, False)]


def test_reduce_poly_inequalities_real_interval():
    assert reduce_rational_inequalities(
        [[Eq(x**2, 0)]], x, relational=False) == FiniteSet(0)
    assert reduce_rational_inequalities(
        [[Le(x**2, 0)]], x, relational=False) == FiniteSet(0)
    assert reduce_rational_inequalities(
        [[Lt(x**2, 0)]], x, relational=False) == S.EmptySet
    assert reduce_rational_inequalities(
        [[Ge(x**2, 0)]], x, relational=False) == \
        S.Reals if x.is_real else Interval(-oo, oo)
    assert reduce_rational_inequalities(
        [[Gt(x**2, 0)]], x, relational=False) == \
        FiniteSet(0).complement(S.Reals)
    assert reduce_rational_inequalities(
        [[Ne(x**2, 0)]], x, relational=False) == \
        FiniteSet(0).complement(S.Reals)

    assert reduce_rational_inequalities(
        [[Eq(x**2, 1)]], x, relational=False) == FiniteSet(-1, 1)
    assert reduce_rational_inequalities(
        [[Le(x**2, 1)]], x, relational=False) == Interval(-1, 1)
    assert reduce_rational_inequalities(
        [[Lt(x**2, 1)]], x, relational=False) == Interval(-1, 1, True, True)
    assert reduce_rational_inequalities(
        [[Ge(x**2, 1)]], x, relational=False) == \
        Union(Interval(-oo, -1), Interval(1, oo))
    assert reduce_rational_inequalities(
        [[Gt(x**2, 1)]], x, relational=False) == \
        Interval(-1, 1).complement(S.Reals)
    assert reduce_rational_inequalities(
        [[Ne(x**2, 1)]], x, relational=False) == \
        FiniteSet(-1, 1).complement(S.Reals)
    assert reduce_rational_inequalities([[Eq(
        x**2, 1.0)]], x, relational=False) == FiniteSet(-1.0, 1.0).evalf()
    assert reduce_rational_inequalities(
        [[Le(x**2, 1.0)]], x, relational=False) == Interval(-1.0, 1.0)
    assert reduce_rational_inequalities([[Lt(
        x**2, 1.0)]], x, relational=False) == Interval(-1.0, 1.0, True, True)
    assert reduce_rational_inequalities(
        [[Ge(x**2, 1.0)]], x, relational=False) == \
        Union(Interval(-inf, -1.0), Interval(1.0, inf))
    assert reduce_rational_inequalities(
        [[Gt(x**2, 1.0)]], x, relational=False) == \
        Union(Interval(-inf, -1.0, right_open=True),
        Interval(1.0, inf, left_open=True))
    assert reduce_rational_inequalities([[Ne(
        x**2, 1.0)]], x, relational=False) == \
        FiniteSet(-1.0, 1.0).complement(S.Reals)

    s = sqrt(2)

    assert reduce_rational_inequalities([[Lt(
        x**2 - 1, 0), Gt(x**2 - 1, 0)]], x, relational=False) == S.EmptySet
    assert reduce_rational_inequalities([[Le(x**2 - 1, 0), Ge(
        x**2 - 1, 0)]], x, relational=False) == FiniteSet(-1, 1)
    assert reduce_rational_inequalities(
        [[Le(x**2 - 2, 0), Ge(x**2 - 1, 0)]], x, relational=False
        ) == Union(Interval(-s, -1, False, False), Interval(1, s, False, False))
    assert reduce_rational_inequalities(
        [[Le(x**2 - 2, 0), Gt(x**2 - 1, 0)]], x, relational=False
        ) == Union(Interval(-s, -1, False, True), Interval(1, s, True, False))
    assert reduce_rational_inequalities(
        [[Lt(x**2 - 2, 0), Ge(x**2 - 1, 0)]], x, relational=False
        ) == Union(Interval(-s, -1, True, False), Interval(1, s, False, True))
    assert reduce_rational_inequalities(
        [[Lt(x**2 - 2, 0), Gt(x**2 - 1, 0)]], x, relational=False
        ) == Union(Interval(-s, -1, True, True), Interval(1, s, True, True))
    assert reduce_rational_inequalities(
        [[Lt(x**2 - 2, 0), Ne(x**2 - 1, 0)]], x, relational=False
        ) == Union(Interval(-s, -1, True, True), Interval(-1, 1, True, True),
        Interval(1, s, True, True))

    assert reduce_rational_inequalities([[Lt(x**2, -1.)]], x) is S.false


def test_reduce_poly_inequalities_complex_relational():
    assert reduce_rational_inequalities(
        [[Eq(x**2, 0)]], x, relational=True) == Eq(x, 0)
    assert reduce_rational_inequalities(
        [[Le(x**2, 0)]], x, relational=True) == Eq(x, 0)
    assert reduce_rational_inequalities(
        [[Lt(x**2, 0)]], x, relational=True) == False
    assert reduce_rational_inequalities(
        [[Ge(x**2, 0)]], x, relational=True) == And(Lt(-oo, x), Lt(x, oo))
    assert reduce_rational_inequalities(
        [[Gt(x**2, 0)]], x, relational=True) == \
        And(Gt(x, -oo), Lt(x, oo), Ne(x, 0))
    assert reduce_rational_inequalities(
        [[Ne(x**2, 0)]], x, relational=True) == \
        And(Gt(x, -oo), Lt(x, oo), Ne(x, 0))

    for one in (S(1), S(1.0)):
        inf = one*oo
        assert reduce_rational_inequalities(
            [[Eq(x**2, one)]], x, relational=True) == \
            Or(Eq(x, -one), Eq(x, one))
        assert reduce_rational_inequalities(
            [[Le(x**2, one)]], x, relational=True) == \
            And(And(Le(-one, x), Le(x, one)))
        assert reduce_rational_inequalities(
            [[Lt(x**2, one)]], x, relational=True) == \
            And(And(Lt(-one, x), Lt(x, one)))
        assert reduce_rational_inequalities(
            [[Ge(x**2, one)]], x, relational=True) == \
            And(Or(And(Le(one, x), Lt(x, inf)), And(Le(x, -one), Lt(-inf, x))))
        assert reduce_rational_inequalities(
            [[Gt(x**2, one)]], x, relational=True) == \
            And(Or(And(Lt(-inf, x), Lt(x, -one)), And(Lt(one, x), Lt(x, inf))))
        assert reduce_rational_inequalities(
            [[Ne(x**2, one)]], x, relational=True) == \
            Or(And(Lt(-inf, x), Lt(x, -one)),
               And(Lt(-one, x), Lt(x, one)),
               And(Lt(one, x), Lt(x, inf)))


def test_reduce_rational_inequalities_real_relational():
    assert reduce_rational_inequalities([], x) == False
    assert reduce_rational_inequalities(
        [[(x**2 + 3*x + 2)/(x**2 - 16) >= 0]], x, relational=False) == \
        Union(Interval.open(-oo, -4), Interval(-2, -1), Interval.open(4, oo))

    assert reduce_rational_inequalities(
        [[((-2*x - 10)*(3 - x))/((x**2 + 5)*(x - 2)**2) < 0]], x,
        relational=False) == \
        Union(Interval.open(-5, 2), Interval.open(2, 3))

    assert reduce_rational_inequalities([[(x + 1)/(x - 5) <= 0]], x,
        relational=False) == \
        Interval.Ropen(-1, 5)

    assert reduce_rational_inequalities([[(x**2 + 4*x + 3)/(x - 1) > 0]], x,
        relational=False) == \
        Union(Interval.open(-3, -1), Interval.open(1, oo))

    assert reduce_rational_inequalities([[(x**2 - 16)/(x - 1)**2 < 0]], x,
        relational=False) == \
        Union(Interval.open(-4, 1), Interval.open(1, 4))

    assert reduce_rational_inequalities([[(3*x + 1)/(x + 4) >= 1]], x,
        relational=False) == \
        Union(Interval.open(-oo, -4), Interval.Ropen(S(3)/2, oo))

    assert reduce_rational_inequalities([[(x - 8)/x <= 3 - x]], x,
        relational=False) == \
        Union(Interval.Lopen(-oo, -2), Interval.Lopen(0, 4))

    # issue sympy/sympy#10237
    assert reduce_rational_inequalities(
        [[x < oo, x >= 0, -oo < x]], x, relational=False) == Interval(0, oo)


def test_reduce_abs_inequalities():
    e = abs(x - 5) < 3
    ans = And(Lt(2, x), Lt(x, 8))
    assert reduce_inequalities(e) == ans
    assert reduce_inequalities(e, x) == ans
    assert reduce_inequalities(abs(x - 5)) == Eq(x, 5)
    assert reduce_inequalities(
        abs(2*x + 3) >= 8) == Or(And(Le(S(5)/2, x), Lt(x, oo)),
        And(Le(x, -S(11)/2), Lt(-oo, x)))
    assert reduce_inequalities(abs(x - 4) + abs(
        3*x - 5) < 7) == And(Lt(S(1)/2, x), Lt(x, 4))
    assert reduce_inequalities(abs(x - 4) + abs(3*abs(x) - 5) < 7) == \
        Or(And(S(-2) < x, x < -1), And(S(1)/2 < x, x < 4))

    nr = Symbol('nr', real=False)
    raises(TypeError, lambda: reduce_inequalities(abs(nr - 5) < 3))
    assert reduce_inequalities(x < 3, symbols=[x, nr]) == And(-oo < x, x < 3)


def test_reduce_inequalities_general():
    assert reduce_inequalities(Ge(sqrt(2)*x, 1)) == And(sqrt(2)/2 <= x, x < oo)
    assert reduce_inequalities(PurePoly(x + 1, x) > 0) == And(S(-1) < x, x < oo)


def test_reduce_inequalities_boolean():
    assert reduce_inequalities(
        [Eq(x**2, 0), True]) == Eq(x, 0)
    assert reduce_inequalities([Eq(x**2, 0), False]) == False
    assert reduce_inequalities(x**2 >= 0) is S.true  # issue 10196


def test_reduce_inequalities_multivariate():
    assert reduce_inequalities([Ge(x**2, 1), Ge(y**2, 1)]) == And(
        Or(And(Le(1, x), Lt(x, oo)), And(Le(x, -1), Lt(-oo, x))),
        Or(And(Le(1, y), Lt(y, oo)), And(Le(y, -1), Lt(-oo, y))))


def test_reduce_inequalities_errors():
    raises(NotImplementedError, lambda: reduce_inequalities(Ge(sin(x) + x, 1)))
    raises(NotImplementedError, lambda: reduce_inequalities(Ge(x**2*y + y, 1)))


def test__solve_inequalities():
    assert reduce_inequalities(x + y < 1, symbols=[x]) == (x < 1 - y)
    assert reduce_inequalities(x + y >= 1, symbols=[x]) == (x < oo) & (x >= -y + 1)
    assert reduce_inequalities(Eq(0, x - y), symbols=[x]) == Eq(x, y)
    assert reduce_inequalities(Ne(0, x - y), symbols=[x]) == Ne(x, y)


def test_issue_6343():
    eq = -3*x**2/2 - 45*x/4 + S(33)/2 > 0
    assert reduce_inequalities(eq) == \
        And(x < -S(15)/4 + sqrt(401)/4, -sqrt(401)/4 - S(15)/4 < x)


def test_issue_8235():
    assert reduce_inequalities(x**2 - 1 < 0) == \
        And(S(-1) < x, x < S(1))
    assert reduce_inequalities(x**2 - 1 <= 0) == \
        And(S(-1) <= x, x <= 1)
    assert reduce_inequalities(x**2 - 1 > 0) == \
        Or(And(-oo < x, x < -1), And(x < oo, S(1) < x))
    assert reduce_inequalities(x**2 - 1 >= 0) == \
        Or(And(-oo < x, x <= S(-1)), And(S(1) <= x, x < oo))

    eq = x**8 + x - 9  # we want CRootOf solns here
    sol = solve(eq >= 0)
    tru = Or(And(rootof(eq, 1) <= x, x < oo), And(-oo < x, x <= rootof(eq, 0)))
    assert sol == tru

    # recast vanilla as real
    assert solve(sqrt((-x + 1)**2) < 1) == And(S(0) < x, x < 2)


def test_issue_5526():
    assert reduce_inequalities(S(0) <=
        x + Integral(y**2, (y, 1, 3)) - 1, [x]) == \
        (x >= -Integral(y**2, (y, 1, 3)) + 1)
    f = Function('f')
    e = Sum(f(x), (x, 1, 3))
    assert reduce_inequalities(S(0) <= x + e + y**2, [x]) == \
        (x >= -y**2 - Sum(f(x), (x, 1, 3)))


def test_solve_univariate_inequality():
    assert isolve(x**2 >= 4, x, relational=False) == Union(Interval(-oo, -2),
        Interval(2, oo))
    assert isolve(x**2 >= 4, x) == Or(And(Le(2, x), Lt(x, oo)), And(Le(x, -2),
        Lt(-oo, x)))
    assert isolve((x - 1)*(x - 2)*(x - 3) >= 0, x, relational=False) == \
        Union(Interval(1, 2), Interval(3, oo))
    assert isolve((x - 1)*(x - 2)*(x - 3) >= 0, x) == \
        Or(And(Le(1, x), Le(x, 2)), And(Le(3, x), Lt(x, oo)))
    assert isolve((x - 1)*(x - 2)*(x - 4) < 0, x, domain = FiniteSet(0, 3)) == \
        Or(Eq(x, 0), Eq(x, 3))
    # issue 2785:
    assert isolve(x**3 - 2*x - 1 > 0, x, relational=False) == \
        Union(Interval(-1, -sqrt(5)/2 + S(1)/2, True, True),
              Interval(S(1)/2 + sqrt(5)/2, oo, True, True))
    # issue 2794:
    assert isolve(x**3 - x**2 + x - 1 > 0, x, relational=False) == \
        Interval(1, oo, True)
    #issue 13105
    assert isolve((x + I)*(x + 2*I) < 0, x) == Eq(x, 0)
    assert isolve(((x - 1)*(x - 2) + I)*((x - 1)*(x - 2) + 2*I) < 0, x) == Or(Eq(x, 1), Eq(x, 2))
    assert isolve((((x - 1)*(x - 2) + I)*((x - 1)*(x - 2) + 2*I))/(x - 2) > 0, x) == Eq(x, 1)
    raises (ValueError, lambda: isolve((x**2 - 3*x*I + 2)/x < 0, x))

    # numerical testing in valid() is needed
    assert isolve(x**7 - x - 2 > 0, x) == \
        And(rootof(x**7 - x - 2, 0) < x, x < oo)

    # handle numerator and denominator; although these would be handled as
    # rational inequalities, these test confirm that the right thing is done
    # when the domain is EX (e.g. when 2 is replaced with sqrt(2))
    assert isolve(1/(x - 2) > 0, x) == And(S(2) < x, x < oo)
    den = ((x - 1)*(x - 2)).expand()
    assert isolve((x - 1)/den <= 0, x) == \
        Or(And(-oo < x, x < 1), And(S(1) < x, x < 2))

    n = Dummy('n')
    raises(NotImplementedError, lambda: isolve(Abs(x) <= n, x, relational=False))
    c1 = Dummy("c1", positive=True)
    raises(NotImplementedError, lambda: isolve(n/c1 < 0, c1))
    n = Dummy('n', negative=True)
    assert isolve(n/c1 > -2, c1) == (-n/2 < c1)
    assert isolve(n/c1 < 0, c1) == True
    assert isolve(n/c1 > 0, c1) == False

    zero = cos(1)**2 + sin(1)**2 - 1
    raises(NotImplementedError, lambda: isolve(x**2 < zero, x))
    raises(NotImplementedError, lambda: isolve(
        x**2 < zero*I, x))
    raises(NotImplementedError, lambda: isolve(1/(x - y) < 2, x))
    raises(NotImplementedError, lambda: isolve(1/(x - y) < 0, x))
    raises(TypeError, lambda: isolve(x - I < 0, x))

    zero = x**2 + x - x*(x + 1)
    assert isolve(zero < 0, x, relational=False) is S.EmptySet
    assert isolve(zero <= 0, x, relational=False) is S.Reals

    # make sure iter_solutions gets a default value
    raises(NotImplementedError, lambda: isolve(
        Eq(cos(x)**2 + sin(x)**2, 1), x))


def test_trig_inequalities():
    # all the inequalities are solved in a periodic interval.
    assert isolve(sin(x) < S.Half, x, relational=False) == \
        Union(Interval(0, pi/6, False, True), Interval(5*pi/6, 2*pi, True, False))
    assert isolve(sin(x) > S.Half, x, relational=False) == \
        Interval(pi/6, 5*pi/6, True, True)
    assert isolve(cos(x) < S.Zero, x, relational=False) == \
        Interval(pi/2, 3*pi/2, True, True)
    assert isolve(cos(x) >= S.Zero, x, relational=False) == \
        Union(Interval(0, pi/2), Interval(3*pi/2, 2*pi))

    assert isolve(tan(x) < S.One, x, relational=False) == \
        Union(Interval.Ropen(0, pi/4), Interval.Lopen(pi/2, pi))

    assert isolve(sin(x) <= S.Zero, x, relational=False) == \
        Union(FiniteSet(S(0)), Interval(pi, 2*pi))

    assert isolve(sin(x) <= S(1), x, relational=False) == S.Reals
    assert isolve(cos(x) < S(-2), x, relational=False) == S.EmptySet
    assert isolve(sin(x) >= S(-1), x, relational=False) == S.Reals
    assert isolve(cos(x) > S(1), x, relational=False) == S.EmptySet


def test_issue_9954():
    assert isolve(x**2 >= 0, x, relational=False) == S.Reals
    assert isolve(x**2 >= 0, x, relational=True) == S.Reals.as_relational(x)
    assert isolve(x**2 < 0, x, relational=False) == S.EmptySet
    assert isolve(x**2 < 0, x, relational=True) == S.EmptySet.as_relational(x)


@XFAIL
def test_slow_general_univariate():
    r = rootof(x**5 - x**2 + 1, 0)
    assert solve(sqrt(x) + 1/root(x, 3) > 1) == \
        Or(And(S(0) < x, x < r**6), And(r**6 < x, x < oo))


def test_issue_8545():
    eq = 1 - x - abs(1 - x)
    ans = And(Lt(1, x), Lt(x, oo))
    assert reduce_abs_inequality(eq, '<', x) == ans
    eq = 1 - x - sqrt((1 - x)**2)
    assert reduce_inequalities(eq < 0) == ans


def test_issue_8974():
    assert isolve(-oo < x, x) == And(-oo < x, x < oo)
    assert isolve(oo > x, x) == And(-oo < x, x < oo)


def test_issue_10198():
    assert reduce_inequalities(
        -1 + 1/abs(1/x - 1) < 0) == Or(
        And(-oo < x, x < 0), And(S(0) < x, x < S(1)/2)
        )
    assert reduce_inequalities(abs(1/sqrt(x)) - 1, x) == Eq(x, 1)
    assert reduce_abs_inequality(-3 + 1/abs(1 - 1/x), '<', x) == \
        Or(And(-oo < x, x < 0),
        And(S(0) < x, x < S(3)/4), And(S(3)/2 < x, x < oo))
    raises(ValueError,lambda: reduce_abs_inequality(-3 + 1/abs(
        1 - 1/sqrt(x)), '<', x))


def test_issue_10047():
    # this must remain an inequality, not True, since if x
    # is not real the inequality is invalid
    assert solve(sin(x) < 2) == (x <= oo)


def test_issue_10268():
    assert solve(log(x) < 1000) == And(S(0) < x, x < exp(1000))


@XFAIL
def test_isolve_Sets():
    n = Dummy('n')
    assert isolve(Abs(x) <= n, x, relational=False) == \
        Piecewise((S.EmptySet, n < 0), (Interval(-n, n), True))


def test_issue_10671_12466():
    assert solveset(sin(y), y, Interval(0, pi)) == FiniteSet(0, pi)
    i = Interval(1, 10)
    assert solveset((1/x).diff(x) < 0, x, i) == i
    assert solveset((log(x - 6)/x) <= 0, x, S.Reals) == \
        Interval.Lopen(6, 7)


def test__solve_inequality():
    for op in (Gt, Lt, Le, Ge, Eq, Ne):
        assert _solve_inequality(op(x, 1), x).lhs == x
        assert _solve_inequality(op(S.One, x), x).lhs == x
    # don't get tricked by symbol on right: solve it
    assert _solve_inequality(Eq(2*x - 1, x), x) == Eq(x, 1)
    ie = Eq(S.One, y)
    assert _solve_inequality(ie, x) == ie
    for fx in (x**2, exp(x), sin(x) + cos(x), x*(1 + x)):
        for c in (0, 1):
            e = 2*fx - c > 0
            assert _solve_inequality(e, x, linear=True) == (
                fx > c/S(2))
    assert _solve_inequality(2*x**2 + 2*x - 1 < 0, x, linear=True) == (
        x*(x + 1) < S.Half)
    assert _solve_inequality(Eq(x*y, 1), x) == Eq(x*y, 1)
    nz = Symbol('nz', nonzero=True)
    assert _solve_inequality(Eq(x*nz, 1), x) == Eq(x, 1/nz)
    assert _solve_inequality(x*nz < 1, x) == (x*nz < 1)
    a = Symbol('a', positive=True)
    assert _solve_inequality(a/x > 1, x) == (S.Zero < x) & (x < a)
    assert _solve_inequality(a/x > 1, x, linear=True) == (1/x > 1/a)
    # make sure to include conditions under which solution is valid
    e = Eq(1 - x, x*(1/x - 1))
    assert _solve_inequality(e, x) == Ne(x, 0)
    assert _solve_inequality(x < x*(1/x - 1), x) == (x < S.Half) & Ne(x, 0)


def test__pt():
    from sympy.solvers.inequalities import _pt
    assert _pt(-oo, oo) == 0
    assert _pt(S(1), S(3)) == 2
    assert _pt(S(1), oo) == _pt(oo, S(1)) == 2
    assert _pt(S(1), -oo) == _pt(-oo, S(1)) == S.Half
    assert _pt(S(-1), oo) == _pt(oo, S(-1)) == -S.Half
    assert _pt(S(-1), -oo) == _pt(-oo, S(-1)) == -2
    assert _pt(x, oo) == _pt(oo, x) == x + 1
    assert _pt(x, -oo) == _pt(-oo, x) == x - 1
    raises(ValueError, lambda: _pt(Dummy('i', infinite=True), S(1)))
