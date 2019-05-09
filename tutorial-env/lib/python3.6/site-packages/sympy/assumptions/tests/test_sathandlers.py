from sympy import Mul, Basic, Q, Expr, And, symbols, Equivalent, Implies, Or

from sympy.assumptions.sathandlers import (ClassFactRegistry, AllArgs,
    UnevaluatedOnFree, AnyArgs, CheckOldAssump, ExactlyOneArg)

from sympy.utilities.pytest import raises


x, y, z = symbols('x y z')


def test_class_handler_registry():
    my_handler_registry = ClassFactRegistry()

    # The predicate doesn't matter here, so just use is_true
    fact1 = Equivalent(Q.is_true, AllArgs(Q.is_true))
    fact2 = Equivalent(Q.is_true, AnyArgs(Q.is_true))

    my_handler_registry[Mul] = {fact1}
    my_handler_registry[Expr] = {fact2}

    assert my_handler_registry[Basic] == set()
    assert my_handler_registry[Expr] == {fact2}
    assert my_handler_registry[Mul] == {fact1, fact2}


def test_UnevaluatedOnFree():
    a = UnevaluatedOnFree(Q.positive)
    b = UnevaluatedOnFree(Q.positive | Q.negative)
    c = UnevaluatedOnFree(Q.positive & ~Q.positive) # It shouldn't do any deduction
    assert a.rcall(x) == UnevaluatedOnFree(Q.positive(x))
    assert b.rcall(x) == UnevaluatedOnFree(Q.positive(x) | Q.negative(x))
    assert c.rcall(x) == UnevaluatedOnFree(Q.positive(x) & ~Q.positive(x))
    assert a.rcall(x).expr == x
    assert a.rcall(x).pred == Q.positive
    assert b.rcall(x).pred == Q.positive | Q.negative
    raises(ValueError, lambda: UnevaluatedOnFree(Q.positive(x) | Q.negative))
    raises(ValueError, lambda: UnevaluatedOnFree(Q.positive(x) |
        Q.negative(y)))

    class MyUnevaluatedOnFree(UnevaluatedOnFree):
        def apply(self):
            return self.args[0]

    a = MyUnevaluatedOnFree(Q.positive)
    b = MyUnevaluatedOnFree(Q.positive | Q.negative)
    c = MyUnevaluatedOnFree(Q.positive(x))
    d = MyUnevaluatedOnFree(Q.positive(x) | Q.negative(x))

    assert a.rcall(x) == c == Q.positive(x)
    assert b.rcall(x) == d == Q.positive(x) | Q.negative(x)

    raises(ValueError, lambda: MyUnevaluatedOnFree(Q.positive(x) | Q.negative(y)))


def test_AllArgs():
    a = AllArgs(Q.zero)
    b = AllArgs(Q.positive | Q.negative)
    assert a.rcall(x*y) == And(Q.zero(x), Q.zero(y))
    assert b.rcall(x*y) == And(Q.positive(x) | Q.negative(x), Q.positive(y) | Q.negative(y))


def test_AnyArgs():
    a = AnyArgs(Q.zero)
    b = AnyArgs(Q.positive & Q.negative)
    assert a.rcall(x*y) == Or(Q.zero(x), Q.zero(y))
    assert b.rcall(x*y) == Or(Q.positive(x) & Q.negative(x), Q.positive(y) & Q.negative(y))


def test_CheckOldAssump():
    # TODO: Make these tests more complete

    class Test1(Expr):
        def _eval_is_positive(self):
            return True
        def _eval_is_negative(self):
            return False

    class Test2(Expr):
        def _eval_is_finite(self):
            return True
        def _eval_is_positive(self):
            return True
        def _eval_is_negative(self):
            return False

    t1 = Test1()
    t2 = Test2()

    # We can't say if it's positive or negative in the old assumptions without
    # bounded. Remember, True means "no new knowledge", and
    # Q.positive(t2) means "t2 is positive."
    assert CheckOldAssump(Q.positive(t1)) == True
    assert CheckOldAssump(Q.negative(t1)) == ~Q.negative(t1)

    assert CheckOldAssump(Q.positive(t2)) == Q.positive(t2)
    assert CheckOldAssump(Q.negative(t2)) == ~Q.negative(t2)


def test_ExactlyOneArg():
    a = ExactlyOneArg(Q.zero)
    b = ExactlyOneArg(Q.positive | Q.negative)
    assert a.rcall(x*y) == Or(Q.zero(x) & ~Q.zero(y), Q.zero(y) & ~Q.zero(x))
    assert a.rcall(x*y*z) == Or(Q.zero(x) & ~Q.zero(y) & ~Q.zero(z), Q.zero(y)
        & ~Q.zero(x) & ~Q.zero(z), Q.zero(z) & ~Q.zero(x) & ~Q.zero(y))
    assert b.rcall(x*y) == Or((Q.positive(x) | Q.negative(x)) &
        ~(Q.positive(y) | Q.negative(y)), (Q.positive(y) | Q.negative(y)) &
        ~(Q.positive(x) | Q.negative(x)))
