from sympy import (Abs, exp, Expr, I, pi, Q, Rational, refine, S, sqrt,
                   atan, atan2, nan, Symbol)
from sympy.abc import x, y, z
from sympy.core.relational import Eq, Ne
from sympy.functions.elementary.piecewise import Piecewise
from sympy.utilities.pytest import slow


def test_Abs():
    assert refine(Abs(x), Q.positive(x)) == x
    assert refine(1 + Abs(x), Q.positive(x)) == 1 + x
    assert refine(Abs(x), Q.negative(x)) == -x
    assert refine(1 + Abs(x), Q.negative(x)) == 1 - x

    assert refine(Abs(x**2)) != x**2
    assert refine(Abs(x**2), Q.real(x)) == x**2


def test_pow1():
    assert refine((-1)**x, Q.even(x)) == 1
    assert refine((-1)**x, Q.odd(x)) == -1
    assert refine((-2)**x, Q.even(x)) == 2**x

    # nested powers
    assert refine(sqrt(x**2)) != Abs(x)
    assert refine(sqrt(x**2), Q.complex(x)) != Abs(x)
    assert refine(sqrt(x**2), Q.real(x)) == Abs(x)
    assert refine(sqrt(x**2), Q.positive(x)) == x
    assert refine((x**3)**(S(1)/3)) != x

    assert refine((x**3)**(S(1)/3), Q.real(x)) != x
    assert refine((x**3)**(S(1)/3), Q.positive(x)) == x

    assert refine(sqrt(1/x), Q.real(x)) != 1/sqrt(x)
    assert refine(sqrt(1/x), Q.positive(x)) == 1/sqrt(x)


@slow
def test_pow2():
    # powers of (-1)
    assert refine((-1)**(x + y), Q.even(x)) == (-1)**y
    assert refine((-1)**(x + y + z), Q.odd(x) & Q.odd(z)) == (-1)**y
    assert refine((-1)**(x + y + 1), Q.odd(x)) == (-1)**y
    assert refine((-1)**(x + y + 2), Q.odd(x)) == (-1)**(y + 1)
    assert refine((-1)**(x + 3)) == (-1)**(x + 1)


@slow
def test_pow3():
    # continuation
    assert refine((-1)**((-1)**x/2 - S.Half), Q.integer(x)) == (-1)**x
    assert refine((-1)**((-1)**x/2 + S.Half), Q.integer(x)) == (-1)**(x + 1)
    assert refine((-1)**((-1)**x/2 + 5*S.Half), Q.integer(x)) == (-1)**(x + 1)


@slow
def test_pow4():
    assert refine((-1)**((-1)**x/2 - 7*S.Half), Q.integer(x)) == (-1)**(x + 1)
    assert refine((-1)**((-1)**x/2 - 9*S.Half), Q.integer(x)) == (-1)**x

    # powers of Abs
    assert refine(Abs(x)**2, Q.real(x)) == x**2
    assert refine(Abs(x)**3, Q.real(x)) == Abs(x)**3
    assert refine(Abs(x)**2) == Abs(x)**2


def test_exp():
    x = Symbol('x', integer=True)
    assert refine(exp(pi*I*2*x)) == 1
    assert refine(exp(pi*I*2*(x + Rational(1, 2)))) == -1
    assert refine(exp(pi*I*2*(x + Rational(1, 4)))) == I
    assert refine(exp(pi*I*2*(x + Rational(3, 4)))) == -I


def test_Relational():
    assert not refine(x < 0, ~Q.is_true(x < 0))
    assert refine(x < 0, Q.is_true(x < 0))
    assert refine(x < 0, Q.is_true(0 > x)) == True
    assert refine(x < 0, Q.is_true(y < 0)) == (x < 0)
    assert not refine(x <= 0, ~Q.is_true(x <= 0))
    assert refine(x <= 0,  Q.is_true(x <= 0))
    assert refine(x <= 0,  Q.is_true(0 >= x)) == True
    assert refine(x <= 0,  Q.is_true(y <= 0)) == (x <= 0)
    assert not refine(x > 0, ~Q.is_true(x > 0))
    assert refine(x > 0,  Q.is_true(x > 0))
    assert refine(x > 0,  Q.is_true(0 < x)) == True
    assert refine(x > 0,  Q.is_true(y > 0)) == (x > 0)
    assert not refine(x >= 0, ~Q.is_true(x >= 0))
    assert refine(x >= 0,  Q.is_true(x >= 0))
    assert refine(x >= 0,  Q.is_true(0 <= x)) == True
    assert refine(x >= 0,  Q.is_true(y >= 0)) == (x >= 0)
    assert not refine(Eq(x, 0), ~Q.is_true(Eq(x, 0)))
    assert refine(Eq(x, 0),  Q.is_true(Eq(x, 0)))
    assert refine(Eq(x, 0),  Q.is_true(Eq(0, x))) == True
    assert refine(Eq(x, 0),  Q.is_true(Eq(y, 0))) == Eq(x, 0)
    assert not refine(Ne(x, 0), ~Q.is_true(Ne(x, 0)))
    assert refine(Ne(x, 0), Q.is_true(Ne(0, x))) == True
    assert refine(Ne(x, 0),  Q.is_true(Ne(x, 0)))
    assert refine(Ne(x, 0),  Q.is_true(Ne(y, 0))) == (Ne(x, 0))


def test_Piecewise():
    assert refine(Piecewise((1, x < 0), (3, True)), Q.is_true(x < 0)) == 1
    assert refine(Piecewise((1, x < 0), (3, True)), ~Q.is_true(x < 0)) == 3
    assert refine(Piecewise((1, x < 0), (3, True)), Q.is_true(y < 0)) == \
        Piecewise((1, x < 0), (3, True))
    assert refine(Piecewise((1, x > 0), (3, True)), Q.is_true(x > 0)) == 1
    assert refine(Piecewise((1, x > 0), (3, True)), ~Q.is_true(x > 0)) == 3
    assert refine(Piecewise((1, x > 0), (3, True)), Q.is_true(y > 0)) == \
        Piecewise((1, x > 0), (3, True))
    assert refine(Piecewise((1, x <= 0), (3, True)), Q.is_true(x <= 0)) == 1
    assert refine(Piecewise((1, x <= 0), (3, True)), ~Q.is_true(x <= 0)) == 3
    assert refine(Piecewise((1, x <= 0), (3, True)), Q.is_true(y <= 0)) == \
        Piecewise((1, x <= 0), (3, True))
    assert refine(Piecewise((1, x >= 0), (3, True)), Q.is_true(x >= 0)) == 1
    assert refine(Piecewise((1, x >= 0), (3, True)), ~Q.is_true(x >= 0)) == 3
    assert refine(Piecewise((1, x >= 0), (3, True)), Q.is_true(y >= 0)) == \
        Piecewise((1, x >= 0), (3, True))
    assert refine(Piecewise((1, Eq(x, 0)), (3, True)), Q.is_true(Eq(x, 0)))\
        == 1
    assert refine(Piecewise((1, Eq(x, 0)), (3, True)), Q.is_true(Eq(0, x)))\
        == 1
    assert refine(Piecewise((1, Eq(x, 0)), (3, True)), ~Q.is_true(Eq(x, 0)))\
        == 3
    assert refine(Piecewise((1, Eq(x, 0)), (3, True)), ~Q.is_true(Eq(0, x)))\
        == 3
    assert refine(Piecewise((1, Eq(x, 0)), (3, True)), Q.is_true(Eq(y, 0)))\
        == Piecewise((1, Eq(x, 0)), (3, True))
    assert refine(Piecewise((1, Ne(x, 0)), (3, True)), Q.is_true(Ne(x, 0)))\
        == 1
    assert refine(Piecewise((1, Ne(x, 0)), (3, True)), ~Q.is_true(Ne(x, 0)))\
        == 3
    assert refine(Piecewise((1, Ne(x, 0)), (3, True)), Q.is_true(Ne(y, 0)))\
        == Piecewise((1, Ne(x, 0)), (3, True))


def test_atan2():
    assert refine(atan2(y, x), Q.real(y) & Q.positive(x)) == atan(y/x)
    assert refine(atan2(y, x), Q.negative(y) & Q.positive(x)) == atan(y/x)
    assert refine(atan2(y, x), Q.negative(y) & Q.negative(x)) == atan(y/x) - pi
    assert refine(atan2(y, x), Q.positive(y) & Q.negative(x)) == atan(y/x) + pi
    assert refine(atan2(y, x), Q.zero(y) & Q.negative(x)) == pi
    assert refine(atan2(y, x), Q.positive(y) & Q.zero(x)) == pi/2
    assert refine(atan2(y, x), Q.negative(y) & Q.zero(x)) == -pi/2
    assert refine(atan2(y, x), Q.zero(y) & Q.zero(x)) == nan


def test_func_args():
    class MyClass(Expr):
        # A class with nontrivial .func

        def __init__(self, *args):
            self.my_member = ""

        @property
        def func(self):
            def my_func(*args):
                obj = MyClass(*args)
                obj.my_member = self.my_member
                return obj
            return my_func

    x = MyClass()
    x.my_member = "A very important value"
    assert x.my_member == refine(x).my_member


def test_eval_refine():
    from sympy.core.expr import Expr
    class MockExpr(Expr):
        def _eval_refine(self, assumptions):
            return True

    mock_obj = MockExpr()
    assert refine(mock_obj)

def test_refine_issue_12724():
    expr1 = refine(Abs(x * y), Q.positive(x))
    expr2 = refine(Abs(x * y * z), Q.positive(x))
    assert expr1 == x * Abs(y)
    assert expr2 == x * Abs(y * z)
    y1 = Symbol('y1', real = True)
    expr3 = refine(Abs(x * y1**2 * z), Q.positive(x))
    assert expr3 == x * y1**2 * Abs(z)
