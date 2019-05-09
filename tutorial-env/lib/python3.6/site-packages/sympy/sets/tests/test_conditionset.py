from sympy.sets import (ConditionSet, Intersection, FiniteSet,
    EmptySet, Union)
from sympy import (Symbol, Eq, S, Abs, sin, pi, Interval,
    And, Mod, oo, Function)
from sympy.utilities.pytest import raises


w = Symbol('w')
x = Symbol('x')
y = Symbol('y')
z = Symbol('z')
L = Symbol('lambda')
f = Function('f')


def test_CondSet():
    sin_sols_principal = ConditionSet(x, Eq(sin(x), 0),
                                      Interval(0, 2*pi, False, True))
    assert pi in sin_sols_principal
    assert pi/2 not in sin_sols_principal
    assert 3*pi not in sin_sols_principal
    assert 5 in ConditionSet(x, x**2 > 4, S.Reals)
    assert 1 not in ConditionSet(x, x**2 > 4, S.Reals)
    # in this case, 0 is not part of the base set so
    # it can't be in any subset selected by the condition
    assert 0 not in ConditionSet(x, y > 5, Interval(1, 7))
    # since 'in' requires a true/false, the following raises
    # an error because the given value provides no information
    # for the condition to evaluate (since the condition does
    # not depend on the dummy symbol): the result is `y > 5`.
    # In this case, ConditionSet is just acting like
    # Piecewise((Interval(1, 7), y > 5), (S.EmptySet, True)).
    raises(TypeError, lambda: 6 in ConditionSet(x, y > 5, Interval(1, 7)))

    assert isinstance(ConditionSet(x, x < 1, {x, y}).base_set, FiniteSet)
    raises(TypeError, lambda: ConditionSet(x, x + 1, {x, y}))
    raises(TypeError, lambda: ConditionSet(x, x, 1))

    I = S.Integers
    C = ConditionSet
    assert C(x, x < 1, C(x, x < 2, I)
        ) == C(x, (x < 1) & (x < 2), I)
    assert C(y, y < 1, C(x, y < 2, I)
        ) == C(x, (x < 1) & (y < 2), I)
    assert C(y, y < 1, C(x, x < 2, I)
        ) == C(y, (y < 1) & (y < 2), I)
    assert C(y, y < 1, C(x, y < x, I)
        ) == C(x, (x < 1) & (y < x), I)
    assert C(y, x < 1, C(x, y < x, I)
        ) == C(L, (x < 1) & (y < L), I)
    c = C(y, x < 1, C(x, L < y, I))
    assert c == C(c.sym, (L < y) & (x < 1), I)
    assert c.sym not in (x, y, L)
    c = C(y, x < 1, C(x, y < x, FiniteSet(L)))
    assert c == C(L, And(x < 1, y < L), FiniteSet(L))


def test_CondSet_intersect():
    input_conditionset = ConditionSet(x, x**2 > 4, Interval(1, 4, False, False))
    other_domain = Interval(0, 3, False, False)
    output_conditionset = ConditionSet(x, x**2 > 4, Interval(1, 3, False, False))
    assert Intersection(input_conditionset, other_domain) == output_conditionset


def test_issue_9849():
    assert ConditionSet(x, Eq(x, x), S.Naturals) == S.Naturals
    assert ConditionSet(x, Eq(Abs(sin(x)), -1), S.Naturals) == S.EmptySet


def test_simplified_FiniteSet_in_CondSet():
    assert ConditionSet(x, And(x < 1, x > -3), FiniteSet(0, 1, 2)) == FiniteSet(0)
    assert ConditionSet(x, x < 0, FiniteSet(0, 1, 2)) == EmptySet()
    assert ConditionSet(x, And(x < -3), EmptySet()) == EmptySet()
    y = Symbol('y')
    assert (ConditionSet(x, And(x > 0), FiniteSet(-1, 0, 1, y)) ==
        Union(FiniteSet(1), ConditionSet(x, And(x > 0), FiniteSet(y))))
    assert (ConditionSet(x, Eq(Mod(x, 3), 1), FiniteSet(1, 4, 2, y)) ==
        Union(FiniteSet(1, 4), ConditionSet(x, Eq(Mod(x, 3), 1), FiniteSet(y))))


def test_free_symbols():
    assert ConditionSet(x, Eq(y, 0), FiniteSet(z)
        ).free_symbols == {y, z}
    assert ConditionSet(x, Eq(x, 0), FiniteSet(z)
        ).free_symbols == {z}
    assert ConditionSet(x, Eq(x, 0), FiniteSet(x, z)
        ).free_symbols == {x, z}


def test_subs_CondSet():
    s = FiniteSet(z, y)
    c = ConditionSet(x, x < 2, s)
    # you can only replace sym with a symbol that is not in
    # the free symbols
    assert c.subs(x, 1) == c
    assert c.subs(x, y) == ConditionSet(y, y < 2, s)

    # double subs needed to change dummy if the base set
    # also contains the dummy
    orig = ConditionSet(y, y < 2, s)
    base = orig.subs(y, w)
    and_dummy = base.subs(y, w)
    assert base == ConditionSet(y, y < 2, {w, z})
    assert and_dummy == ConditionSet(w, w < 2, {w, z})

    assert c.subs(x, w) == ConditionSet(w, w < 2, s)
    assert ConditionSet(x, x < y, s
        ).subs(y, w) == ConditionSet(x, x < w, s.subs(y, w))
    # if the user uses assumptions that cause the condition
    # to evaluate, that can't be helped from SymPy's end
    n = Symbol('n', negative=True)
    assert ConditionSet(n, 0 < n, S.Integers) is S.EmptySet
    p = Symbol('p', positive=True)
    assert ConditionSet(n, n < y, S.Integers
        ).subs(n, x) == ConditionSet(x, x < y, S.Integers)
    nc = Symbol('nc', commutative=False)
    raises(ValueError, lambda: ConditionSet(
        x, x < p, S.Integers).subs(x, nc))
    raises(ValueError, lambda: ConditionSet(
        x, x < p, S.Integers).subs(x, n))
    raises(ValueError, lambda: ConditionSet(
        x + 1, x < 1, S.Integers))
    raises(ValueError, lambda: ConditionSet(
        x + 1, x < 1, s))
    assert ConditionSet(
        n, n < x, Interval(0, oo)).subs(x, p) == Interval(0, oo)
    assert ConditionSet(
        n, n < x, Interval(-oo, 0)).subs(x, p) == S.EmptySet
    assert ConditionSet(f(x), f(x) < 1, {w, z}
        ).subs(f(x), y) == ConditionSet(y, y < 1, {w, z})


def test_subs_CondSet_tebr():
    # to eventually be removed
    c = ConditionSet((x, y), {x + 1, x + y}, S.Reals)
    assert c.subs(x, z) == c


def test_dummy_eq():
    C = ConditionSet
    I = S.Integers
    c = C(x, x < 1, I)
    assert c.dummy_eq(C(y, y < 1, I))
    assert c.dummy_eq(1) == False
    assert c.dummy_eq(C(x, x < 1, S.Reals)) == False
    raises(ValueError, lambda: c.dummy_eq(C(x, x < 1, S.Reals), z))

    # to eventually be removed
    c1 = ConditionSet((x, y), {x + 1, x + y}, S.Reals)
    c2 = ConditionSet((x, y), {x + 1, x + y}, S.Reals)
    c3 = ConditionSet((x, y), {x + 1, x + y}, S.Complexes)
    assert c1.dummy_eq(c2)
    assert c1.dummy_eq(c3) is False
    assert c.dummy_eq(c1) is False
    assert c1.dummy_eq(c) is False


def test_contains():
    assert 6 in ConditionSet(x, x > 5, Interval(1, 7))
    assert (8 in ConditionSet(x, y > 5, Interval(1, 7))) is False
    # `in` should give True or False; in this case there is not
    # enough information for that result
    raises(TypeError,
        lambda: 6 in ConditionSet(x, y > 5, Interval(1, 7)))
    assert ConditionSet(x, y > 5, Interval(1, 7)
        ).contains(6) == (y > 5)
    assert ConditionSet(x, y > 5, Interval(1, 7)
        ).contains(8) is S.false
    assert ConditionSet(x, y > 5, Interval(1, 7)
        ).contains(w) == And(w >= 1, w <= 7, y > 5)
