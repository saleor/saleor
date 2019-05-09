from __future__ import print_function, division

from sympy import S
from sympy.core.basic import Basic
from sympy.core.containers import Tuple
from sympy.core.expr import Expr
from sympy.core.function import Lambda
from sympy.core.logic import fuzzy_bool
from sympy.core.symbol import Symbol, Dummy
from sympy.logic.boolalg import And, as_Boolean
from sympy.sets.contains import Contains
from sympy.sets.sets import Set, EmptySet, Union, FiniteSet
from sympy.utilities.iterables import sift
from sympy.utilities.misc import filldedent


class ConditionSet(Set):
    """
    Set of elements which satisfies a given condition.

    {x | condition(x) is True for x in S}

    Examples
    ========

    >>> from sympy import Symbol, S, ConditionSet, pi, Eq, sin, Interval
    >>> from sympy.abc import x, y, z

    >>> sin_sols = ConditionSet(x, Eq(sin(x), 0), Interval(0, 2*pi))
    >>> 2*pi in sin_sols
    True
    >>> pi/2 in sin_sols
    False
    >>> 3*pi in sin_sols
    False
    >>> 5 in ConditionSet(x, x**2 > 4, S.Reals)
    True

    If the value is not in the base set, the result is false:

    >>> 5 in ConditionSet(x, x**2 > 4, Interval(2, 4))
    False

    Notes
    =====

    Symbols with assumptions should be avoided or else the
    condition may evaluate without consideration of the set:

    >>> n = Symbol('n', negative=True)
    >>> cond = (n > 0); cond
    False
    >>> ConditionSet(n, cond, S.Integers)
    EmptySet()

    In addition, substitution of a dummy symbol can only be
    done with a generic symbol with matching commutativity
    or else a symbol that has identical assumptions. If the
    base set contains the dummy symbol it is logically distinct
    and will be the target of substitution.

    >>> c = ConditionSet(x, x < 1, {x, z})
    >>> c.subs(x, y)
    ConditionSet(x, x < 1, {y, z})

    A second substitution is needed to change the dummy symbol, too:

    >>> _.subs(x, y)
    ConditionSet(y, y < 1, {y, z})

    And trying to replace the dummy symbol with anything but a symbol
    is ignored: the only change possible will be in the base set:

    >>> ConditionSet(y, y < 1, {y, z}).subs(y, 1)
    ConditionSet(y, y < 1, {z})
    >>> _.subs(y, 1)
    ConditionSet(y, y < 1, {z})

    Notes
    =====

    If no base set is specified, the universal set is implied:

    >>> ConditionSet(x, x < 1).base_set
    UniversalSet()

    Although expressions other than symbols may be used, this
    is discouraged and will raise an error if the expression
    is not found in the condition:

    >>> ConditionSet(x + 1, x + 1 < 1, S.Integers)
    ConditionSet(x + 1, x + 1 < 1, Integers)

    >>> ConditionSet(x + 1, x < 1, S.Integers)
    Traceback (most recent call last):
    ...
    ValueError: non-symbol dummy not recognized in condition

    Although the name is usually respected, it must be replaced if
    the base set is another ConditionSet and the dummy symbol
    and appears as a free symbol in the base set and the dummy symbol
    of the base set appears as a free symbol in the condition:

    >>> ConditionSet(x, x < y, ConditionSet(y, x + y < 2, S.Integers))
    ConditionSet(lambda, (lambda < y) & (lambda + x < 2), Integers)

    The best way to do anything with the dummy symbol is to access
    it with the sym property.

    >>> _.subs(_.sym, Symbol('_x'))
    ConditionSet(_x, (_x < y) & (_x + x < 2), Integers)
    """
    def __new__(cls, sym, condition, base_set=S.UniversalSet):
        # nonlinsolve uses ConditionSet to return an unsolved system
        # of equations (see _return_conditionset in solveset) so until
        # that is changed we do minimal checking of the args
        if isinstance(sym, (Tuple, tuple)):  # unsolved eqns syntax
            sym = Tuple(*sym)
            condition = FiniteSet(*condition)
            return Basic.__new__(cls, sym, condition, base_set)
        condition = as_Boolean(condition)
        if isinstance(base_set, set):
            base_set = FiniteSet(*base_set)
        elif not isinstance(base_set, Set):
            raise TypeError('expecting set for base_set')
        if condition is S.false:
            return S.EmptySet
        if condition is S.true:
            return base_set
        if isinstance(base_set, EmptySet):
            return base_set
        know = None
        if isinstance(base_set, FiniteSet):
            sifted = sift(
                base_set, lambda _: fuzzy_bool(
                    condition.subs(sym, _)))
            if sifted[None]:
                know = FiniteSet(*sifted[True])
                base_set = FiniteSet(*sifted[None])
            else:
                return FiniteSet(*sifted[True])
        if isinstance(base_set, cls):
            s, c, base_set = base_set.args
            if sym == s:
                condition = And(condition, c)
            elif sym not in c.free_symbols:
                condition = And(condition, c.xreplace({s: sym}))
            elif s not in condition.free_symbols:
                condition = And(condition.xreplace({sym: s}), c)
                sym = s
            else:
                # user will have to use cls.sym to get symbol
                dum = Symbol('lambda')
                if dum in condition.free_symbols or \
                        dum in c.free_symbols:
                    dum = Dummy(str(dum))
                condition = And(
                    condition.xreplace({sym: dum}),
                    c.xreplace({s: dum}))
                sym = dum
        if not isinstance(sym, Symbol):
            s = Dummy('lambda')
            if s not in condition.xreplace({sym: s}).free_symbols:
                raise ValueError(
                    'non-symbol dummy not recognized in condition')
        rv = Basic.__new__(cls, sym, condition, base_set)
        return rv if know is None else Union(know, rv)

    sym = property(lambda self: self.args[0])
    condition = property(lambda self: self.args[1])
    base_set = property(lambda self: self.args[2])

    @property
    def free_symbols(self):
        s, c, b = self.args
        return (c.free_symbols - s.free_symbols) | b.free_symbols

    def contains(self, other):
        return And(Lambda(self.sym, self.condition)(
            other), self.base_set.contains(other))

    def _eval_subs(self, old, new):
        if not isinstance(self.sym, Expr):
            # Don't do anything with the equation set syntax;
            # that should go away, eventually.
            return self
        sym, cond, base = self.args
        if old == sym:
            # we try to be as lenient as possible to allow
            # the dummy symbol to be changed
            base = base.subs(old, new)
            if isinstance(new, Symbol):
                # if the assumptions don't match, the cond
                # might evaluate or change
                if (new.assumptions0 == old.assumptions0 or
                        len(new.assumptions0) == 1 and
                        old.is_commutative == new.is_commutative):
                    if base != self.base_set:
                        # it will be aggravating to have the dummy
                        # symbol change if you are trying to target
                        # the base set so if the base set is changed
                        # leave the dummy symbol alone -- a second
                        # subs will be needed to change the dummy
                        return self.func(sym, cond, base)
                    else:
                        return self.func(new, cond.subs(old, new), base)
                raise ValueError(filldedent('''
                    A dummy symbol can only be
                    replaced with a symbol having the same
                    assumptions or one having a single assumption
                    having the same commutativity.
                '''))
            # don't target cond: it is there to tell how
            # the base set should be filtered and if new is not in
            # the base set then this substitution is ignored
            return self.func(sym, cond, base)
        cond = self.condition.subs(old, new)
        base = self.base_set.subs(old, new)
        if cond is S.true:
            return ConditionSet(new, Contains(new, base), base)
        return self.func(self.sym, cond, base)

    def dummy_eq(self, other, symbol=None):
        if not isinstance(other, self.func):
            return False
        if isinstance(self.sym, Symbol) != isinstance(other.sym, Symbol):
            # this test won't be necessary when unsolved equations
            # syntax is removed
            return False
        if symbol:
            raise ValueError('symbol arg not supported for ConditionSet')
        o = other
        if isinstance(self.sym, Symbol) and isinstance(other.sym, Symbol):
            # this code will not need to be in an if-block when
            # the unsolved equations syntax is removed
            o = other.func(self.sym,
                other.condition.subs(other.sym, self.sym),
                other.base_set)
        return self == o
