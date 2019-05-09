from sympy.abc import t, w, x, y, z, n, k, m, p, i
from sympy.assumptions import (ask, AssumptionsContext, Q, register_handler,
        remove_handler)
from sympy.assumptions.assume import global_assumptions
from sympy.assumptions.ask import compute_known_facts, single_fact_lookup
from sympy.assumptions.handlers import AskHandler
from sympy.core.add import Add
from sympy.core.numbers import (I, Integer, Rational, oo, pi)
from sympy.core.singleton import S
from sympy.core.power import Pow
from sympy.core.symbol import symbols
from sympy.functions.combinatorial.factorials import factorial
from sympy.functions.elementary.complexes import (Abs, im, re, sign)
from sympy.functions.elementary.exponential import (exp, log)
from sympy.functions.elementary.miscellaneous import sqrt
from sympy.functions.elementary.trigonometric import (
    acos, acot, asin, atan, cos, cot, sin, tan)
from sympy.logic.boolalg import Equivalent, Implies, Xor, And, to_cnf
from sympy.utilities.pytest import XFAIL, slow, raises, warns_deprecated_sympy
from sympy.assumptions.assume import assuming
import math

def test_int_1():
    z = 1
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is True
    assert ask(Q.rational(z)) is True
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is False
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is True
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_int_11():
    z = 11
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is True
    assert ask(Q.rational(z)) is True
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is False
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is True
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is True
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_int_12():
    z = 12
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is True
    assert ask(Q.rational(z)) is True
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is False
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is True
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is True
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_float_1():
    z = 1.0
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is None
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is None
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False

    z = 7.2123
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is None
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is None
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False

    # test for issue #12168
    assert ask(Q.rational(math.pi)) is None


def test_zero_0():
    z = Integer(0)
    assert ask(Q.nonzero(z)) is False
    assert ask(Q.zero(z)) is True
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is True
    assert ask(Q.rational(z)) is True
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is False
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is True
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_negativeone():
    z = Integer(-1)
    assert ask(Q.nonzero(z)) is True
    assert ask(Q.zero(z)) is False
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is True
    assert ask(Q.rational(z)) is True
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is False
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is False
    assert ask(Q.negative(z)) is True
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is True
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_infinity():
    assert ask(Q.commutative(oo)) is True
    assert ask(Q.integer(oo)) is False
    assert ask(Q.rational(oo)) is False
    assert ask(Q.algebraic(oo)) is False
    assert ask(Q.real(oo)) is False
    assert ask(Q.extended_real(oo)) is True
    assert ask(Q.complex(oo)) is False
    assert ask(Q.irrational(oo)) is False
    assert ask(Q.imaginary(oo)) is False
    assert ask(Q.positive(oo)) is True
    assert ask(Q.negative(oo)) is False
    assert ask(Q.even(oo)) is False
    assert ask(Q.odd(oo)) is False
    assert ask(Q.finite(oo)) is False
    assert ask(Q.prime(oo)) is False
    assert ask(Q.composite(oo)) is False
    assert ask(Q.hermitian(oo)) is False
    assert ask(Q.antihermitian(oo)) is False


def test_neg_infinity():
    mm = S.NegativeInfinity
    assert ask(Q.commutative(mm)) is True
    assert ask(Q.integer(mm)) is False
    assert ask(Q.rational(mm)) is False
    assert ask(Q.algebraic(mm)) is False
    assert ask(Q.real(mm)) is False
    assert ask(Q.extended_real(mm)) is True
    assert ask(Q.complex(mm)) is False
    assert ask(Q.irrational(mm)) is False
    assert ask(Q.imaginary(mm)) is False
    assert ask(Q.positive(mm)) is False
    assert ask(Q.negative(mm)) is True
    assert ask(Q.even(mm)) is False
    assert ask(Q.odd(mm)) is False
    assert ask(Q.finite(mm)) is False
    assert ask(Q.prime(mm)) is False
    assert ask(Q.composite(mm)) is False
    assert ask(Q.hermitian(mm)) is False
    assert ask(Q.antihermitian(mm)) is False


def test_nan():
    nan = S.NaN
    assert ask(Q.commutative(nan)) is True
    assert ask(Q.integer(nan)) is False
    assert ask(Q.rational(nan)) is False
    assert ask(Q.algebraic(nan)) is False
    assert ask(Q.real(nan)) is False
    assert ask(Q.extended_real(nan)) is False
    assert ask(Q.complex(nan)) is False
    assert ask(Q.irrational(nan)) is False
    assert ask(Q.imaginary(nan)) is False
    assert ask(Q.positive(nan)) is False
    assert ask(Q.nonzero(nan)) is True
    assert ask(Q.zero(nan)) is False
    assert ask(Q.even(nan)) is False
    assert ask(Q.odd(nan)) is False
    assert ask(Q.finite(nan)) is False
    assert ask(Q.prime(nan)) is False
    assert ask(Q.composite(nan)) is False
    assert ask(Q.hermitian(nan)) is False
    assert ask(Q.antihermitian(nan)) is False


def test_Rational_number():
    r = Rational(3, 4)
    assert ask(Q.commutative(r)) is True
    assert ask(Q.integer(r)) is False
    assert ask(Q.rational(r)) is True
    assert ask(Q.real(r)) is True
    assert ask(Q.complex(r)) is True
    assert ask(Q.irrational(r)) is False
    assert ask(Q.imaginary(r)) is False
    assert ask(Q.positive(r)) is True
    assert ask(Q.negative(r)) is False
    assert ask(Q.even(r)) is False
    assert ask(Q.odd(r)) is False
    assert ask(Q.finite(r)) is True
    assert ask(Q.prime(r)) is False
    assert ask(Q.composite(r)) is False
    assert ask(Q.hermitian(r)) is True
    assert ask(Q.antihermitian(r)) is False

    r = Rational(1, 4)
    assert ask(Q.positive(r)) is True
    assert ask(Q.negative(r)) is False

    r = Rational(5, 4)
    assert ask(Q.negative(r)) is False
    assert ask(Q.positive(r)) is True

    r = Rational(5, 3)
    assert ask(Q.positive(r)) is True
    assert ask(Q.negative(r)) is False

    r = Rational(-3, 4)
    assert ask(Q.positive(r)) is False
    assert ask(Q.negative(r)) is True

    r = Rational(-1, 4)
    assert ask(Q.positive(r)) is False
    assert ask(Q.negative(r)) is True

    r = Rational(-5, 4)
    assert ask(Q.negative(r)) is True
    assert ask(Q.positive(r)) is False

    r = Rational(-5, 3)
    assert ask(Q.positive(r)) is False
    assert ask(Q.negative(r)) is True


def test_sqrt_2():
    z = sqrt(2)
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_pi():
    z = S.Pi
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is False
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False

    z = S.Pi + 1
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is False
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False

    z = 2*S.Pi
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is False
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False

    z = S.Pi ** 2
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is False
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False

    z = (1 + S.Pi) ** 2
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is False
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_E():
    z = S.Exp1
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is False
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_GoldenRatio():
    z = S.GoldenRatio
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is True
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_TribonacciConstant():
    z = S.TribonacciConstant
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is True
    assert ask(Q.real(z)) is True
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is True
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is True
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is True
    assert ask(Q.antihermitian(z)) is False


def test_I():
    z = I
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is True
    assert ask(Q.real(z)) is False
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is False
    assert ask(Q.imaginary(z)) is True
    assert ask(Q.positive(z)) is False
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is False
    assert ask(Q.antihermitian(z)) is True

    z = 1 + I
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is True
    assert ask(Q.real(z)) is False
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is False
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is False
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is False
    assert ask(Q.antihermitian(z)) is False

    z = I*(1 + I)
    assert ask(Q.commutative(z)) is True
    assert ask(Q.integer(z)) is False
    assert ask(Q.rational(z)) is False
    assert ask(Q.algebraic(z)) is True
    assert ask(Q.real(z)) is False
    assert ask(Q.complex(z)) is True
    assert ask(Q.irrational(z)) is False
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.positive(z)) is False
    assert ask(Q.negative(z)) is False
    assert ask(Q.even(z)) is False
    assert ask(Q.odd(z)) is False
    assert ask(Q.finite(z)) is True
    assert ask(Q.prime(z)) is False
    assert ask(Q.composite(z)) is False
    assert ask(Q.hermitian(z)) is False
    assert ask(Q.antihermitian(z)) is False

    z = I**(I)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is True

    z = (-I)**(I)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is True

    z = (3*I)**(I)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is False

    z = (1)**(I)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is True

    z = (-1)**(I)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is True

    z = (1+I)**(I)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is False

    z = (I)**(I+3)
    assert ask(Q.imaginary(z)) is True
    assert ask(Q.real(z)) is False

    z = (I)**(I+2)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is True

    z = (I)**(2)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is True

    z = (I)**(3)
    assert ask(Q.imaginary(z)) is True
    assert ask(Q.real(z)) is False

    z = (3)**(I)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is False

    z = (I)**(0)
    assert ask(Q.imaginary(z)) is False
    assert ask(Q.real(z)) is True


@slow
def test_bounded1():
    x, y, z = symbols('x,y,z')
    assert ask(Q.finite(x)) is None
    assert ask(Q.finite(x), Q.finite(x)) is True
    assert ask(Q.finite(x), Q.finite(y)) is None
    assert ask(Q.finite(x), Q.complex(x)) is None

    assert ask(Q.finite(x + 1)) is None
    assert ask(Q.finite(x + 1), Q.finite(x)) is True
    a = x + y
    x, y = a.args
    # B + B
    assert ask(Q.finite(a), Q.finite(x) & Q.finite(y)) is True
    assert ask(
        Q.finite(a), Q.finite(x) & Q.finite(y) & Q.positive(x)) is True
    assert ask(
        Q.finite(a), Q.finite(x) & Q.finite(y) & Q.positive(y)) is True
    assert ask(Q.finite(a),
        Q.finite(x) & Q.finite(y) & Q.positive(x) & Q.positive(y)) is True
    assert ask(Q.finite(a),
        Q.finite(x) & Q.finite(y) & Q.positive(x) & ~Q.positive(y)) is True
    assert ask(Q.finite(a),
        Q.finite(x) & Q.finite(y) & ~Q.positive(x) & Q.positive(y)) is True
    assert ask(Q.finite(a),
        Q.finite(x) & Q.finite(y) & ~Q.positive(x) & ~Q.positive(y)) is True
    # B + U
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(y)) is False
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.finite(y) & Q.positive(x)) is False
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.finite(y) & Q.positive(y)) is False
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(y) & Q.positive(x) &
        Q.positive(y)) is False
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(y) & Q.positive(x) &
        ~Q.positive(y)) is False
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(y) & ~Q.positive(x) &
        Q.positive(y)) is False
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(y) & ~Q.positive(x) &
        ~Q.positive(y)) is False
    # B + ?
    assert ask(Q.finite(a), Q.finite(x)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.positive(x)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.positive(y)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & Q.positive(x) & Q.positive(y)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & Q.positive(x) & ~Q.positive(y)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.positive(x) & Q.positive(y)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.positive(x) & ~Q.positive(y)) is None
    # U + U
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(y)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & Q.positive(x)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & Q.positive(y)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & Q.positive(x) &
        Q.positive(y)) is False
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & Q.positive(x) &
        ~Q.positive(y)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & ~Q.positive(x) &
        Q.positive(y)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & ~Q.positive(x) &
        ~Q.positive(y)) is False
    # U + ?
    assert ask(Q.finite(a), ~Q.finite(y)) is None
    assert ask(Q.finite(a), ~Q.finite(y) & Q.positive(x)) is None
    assert ask(Q.finite(a), ~Q.finite(y) & Q.positive(y)) is None
    assert ask(
        Q.finite(a), ~Q.finite(y) & Q.positive(x) & Q.positive(y)) is False
    assert ask(
        Q.finite(a), ~Q.finite(y) & Q.positive(x) & ~Q.positive(y)) is None
    assert ask(
        Q.finite(a), ~Q.finite(y) & ~Q.positive(x) & Q.positive(y)) is None
    assert ask(
        Q.finite(a), ~Q.finite(y) & ~Q.positive(x) & ~Q.positive(y)) is False
    # ? + ?
    assert ask(Q.finite(a),) is None
    assert ask(Q.finite(a), Q.positive(x)) is None
    assert ask(Q.finite(a), Q.positive(y)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.positive(y)) is None
    assert ask(Q.finite(a), Q.positive(x) & ~Q.positive(y)) is None
    assert ask(Q.finite(a), ~Q.positive(x) & Q.positive(y)) is None
    assert ask(Q.finite(a), ~Q.positive(x) & ~Q.positive(y)) is None


@slow
def test_bounded2a():
    x, y, z = symbols('x,y,z')
    a = x + y + z
    x, y, z = a.args
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.negative(y) &
        Q.finite(y) & Q.negative(z) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.negative(y) & Q.finite(y) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.negative(y) &
        Q.finite(y) & Q.positive(z) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.negative(y) &
        Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.negative(y) & Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.negative(y) &
        Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.negative(y) & Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.negative(y) & Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.negative(y) & Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.finite(y) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.finite(y) & Q.positive(z) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.finite(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.negative(x) & Q.finite(x) & Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.positive(z) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.positive(y) & Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.positive(y) & Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.positive(y) & Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.positive(y) & Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.negative(y) &
        ~Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.negative(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & Q.negative(z)) is False
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.negative(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.negative(x) & Q.finite(x) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) & Q.positive(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.positive(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.positive(z)) is False
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.negative(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.negative(x) & Q.finite(x) & Q.negative(y)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.negative(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.finite(x)) is None
    assert ask(
        Q.finite(a), Q.negative(x) & Q.finite(x) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        Q.finite(x) & Q.positive(y) & Q.positive(z)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & Q.finite(y) & Q.finite(z)) is True
    assert ask(Q.finite(a),
        Q.finite(x) & Q.finite(y) & Q.positive(z) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.finite(x) &
        Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(
        Q.finite(a), Q.finite(x) & Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.finite(x) &
        Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(
        Q.finite(a), Q.finite(x) & Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.finite(y)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.positive(z) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.finite(x) &
        Q.positive(y) & Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.finite(x) &
        Q.positive(y) & Q.finite(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & Q.positive(y) & Q.finite(y)) is None
    assert ask(Q.finite(a), Q.finite(x) &
        Q.positive(y) & Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.negative(y) &
        ~Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.negative(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & Q.negative(z)) is False
    assert ask(
        Q.finite(a), Q.finite(x) & Q.negative(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.finite(x) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(y)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.positive(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False


@slow
def test_bounded2b():
    x, y, z = symbols('x,y,z')
    a = x + y + z
    x, y, z = a.args
    assert ask(Q.finite(a), Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & Q.positive(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.positive(z)) is False
    assert ask(
        Q.finite(a), Q.finite(x) & Q.negative(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.negative(y)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & Q.negative(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.finite(x)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.positive(z)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & Q.positive(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.positive(z) & Q.finite(z)) is True
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        Q.positive(y) & Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) & Q.positive(y) &
        Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        Q.positive(y) & Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & Q.positive(y) & Q.finite(y)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        Q.positive(y) & Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) & Q.negative(y) &
        ~Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) & Q.negative(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & Q.negative(z)) is False
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & Q.negative(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.positive(x) & Q.finite(x) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) & Q.positive(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & Q.positive(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.positive(z)) is False
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & Q.negative(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.positive(x) & Q.finite(x) & Q.negative(y)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & Q.negative(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & Q.finite(x)) is None
    assert ask(
        Q.finite(a), Q.positive(x) & Q.finite(x) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        Q.finite(x) & Q.positive(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) & Q.negative(y) &
        ~Q.finite(y) & Q.negative(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) & Q.negative(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & Q.negative(z)) is False
    assert ask(Q.finite(a), Q.negative(x) &
        ~Q.finite(x) & Q.negative(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) &
        Q.negative(y) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        ~Q.finite(x) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        ~Q.finite(x) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.negative(x) & ~Q.finite(x) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        ~Q.finite(x) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) & Q.positive(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        ~Q.finite(x) & Q.positive(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        ~Q.finite(x) & Q.negative(y) & Q.negative(z)) is False
    assert ask(
        Q.finite(a), Q.negative(x) & ~Q.finite(x) & Q.negative(y)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        ~Q.finite(x) & Q.negative(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & ~Q.finite(x)) is None
    assert ask(
        Q.finite(a), Q.negative(x) & ~Q.finite(x) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x) &
        ~Q.finite(x) & Q.positive(y) & Q.positive(z)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), ~Q.finite(x) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(y)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & Q.positive(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), ~Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & Q.positive(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), ~Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.positive(z)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & Q.negative(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & Q.negative(y)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & Q.negative(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), ~Q.finite(x)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & Q.positive(z)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & Q.positive(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & ~Q.finite(x) & Q.positive(y) &
        ~Q.finite(y) & Q.positive(z) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.positive(x) & ~Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        ~Q.finite(x) & Q.positive(y) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.positive(x) & ~Q.finite(x) &
        Q.positive(y) & ~Q.finite(y) & Q.positive(z)) is False
    assert ask(Q.finite(a), Q.positive(x) &
        ~Q.finite(x) & Q.negative(y) & Q.negative(z)) is None
    assert ask(
        Q.finite(a), Q.positive(x) & ~Q.finite(x) & Q.negative(y)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        ~Q.finite(x) & Q.negative(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) & ~Q.finite(x)) is None
    assert ask(
        Q.finite(a), Q.positive(x) & ~Q.finite(x) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(x) &
        ~Q.finite(x) & Q.positive(y) & Q.positive(z)) is False
    assert ask(
        Q.finite(a), Q.negative(x) & Q.negative(y) & Q.negative(z)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.negative(y)) is None
    assert ask(
        Q.finite(a), Q.negative(x) & Q.negative(y) & Q.positive(z)) is None
    assert ask(Q.finite(a), Q.negative(x)) is None
    assert ask(Q.finite(a), Q.negative(x) & Q.positive(z)) is None
    assert ask(
        Q.finite(a), Q.negative(x) & Q.positive(y) & Q.positive(z)) is None
    assert ask(Q.finite(a)) is None
    assert ask(Q.finite(a), Q.positive(z)) is None
    assert ask(Q.finite(a), Q.positive(y) & Q.positive(z)) is None
    assert ask(
        Q.finite(a), Q.positive(x) & Q.positive(y) & Q.positive(z)) is None

    assert ask(Q.finite(2*x)) is None
    assert ask(Q.finite(2*x), Q.finite(x)) is True


@slow
def test_bounded3():
    x, y, z = symbols('x,y,z')
    a = x*y
    x, y = a.args
    assert ask(Q.finite(a), Q.finite(x) & Q.finite(y)) is True
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(y)) is False
    assert ask(Q.finite(a), Q.finite(x)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & Q.finite(y)) is False
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(y)) is False
    assert ask(Q.finite(a), ~Q.finite(x)) is None
    assert ask(Q.finite(a), Q.finite(y)) is None
    assert ask(Q.finite(a), ~Q.finite(y)) is None
    assert ask(Q.finite(a)) is None
    a = x*y*z
    x, y, z = a.args
    assert ask(
        Q.finite(a), Q.finite(x) & Q.finite(y) & Q.finite(z)) is True
    assert ask(
        Q.finite(a), Q.finite(x) & Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.finite(x) & Q.finite(y)) is None
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.finite(y) & Q.finite(z)) is False
    assert ask(
        Q.finite(a), Q.finite(x) & ~Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.finite(x) & Q.finite(z)) is None
    assert ask(Q.finite(a), Q.finite(x) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.finite(x)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & Q.finite(y) & Q.finite(z)) is False
    assert ask(
        Q.finite(a), ~Q.finite(x) & Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), ~Q.finite(x) & Q.finite(y)) is None
    assert ask(
        Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & Q.finite(z)) is False
    assert ask(
        Q.finite(a), ~Q.finite(x) & ~Q.finite(y) & ~Q.finite(z)) is False
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(y)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & Q.finite(z)) is None
    assert ask(Q.finite(a), ~Q.finite(x) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), ~Q.finite(x)) is None
    assert ask(Q.finite(a), Q.finite(y) & Q.finite(z)) is None
    assert ask(Q.finite(a), Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), Q.finite(y)) is None
    assert ask(Q.finite(a), ~Q.finite(y) & Q.finite(z)) is None
    assert ask(Q.finite(a), ~Q.finite(y) & ~Q.finite(z)) is None
    assert ask(Q.finite(a), ~Q.finite(y)) is None
    assert ask(Q.finite(a), Q.finite(z)) is None
    assert ask(Q.finite(a), ~Q.finite(z)) is None
    assert ask(Q.finite(a), ~Q.finite(z) &
        Q.nonzero(x) & Q.nonzero(y) & Q.nonzero(z)) is None
    assert ask(Q.finite(a), ~Q.finite(y) & ~Q.finite(z) &
        Q.nonzero(x) & Q.nonzero(y) & Q.nonzero(z)) is False

    x, y, z = symbols('x,y,z')
    assert ask(Q.finite(x**2)) is None
    assert ask(Q.finite(2**x)) is None
    assert ask(Q.finite(2**x), Q.finite(x)) is True
    assert ask(Q.finite(x**x)) is None
    assert ask(Q.finite(Rational(1, 2) ** x)) is None
    assert ask(Q.finite(Rational(1, 2) ** x), Q.positive(x)) is True
    assert ask(Q.finite(Rational(1, 2) ** x), Q.negative(x)) is None
    assert ask(Q.finite(2**x), Q.negative(x)) is True
    assert ask(Q.finite(sqrt(x))) is None
    assert ask(Q.finite(2**x), ~Q.finite(x)) is False
    assert ask(Q.finite(x**2), ~Q.finite(x)) is False

    # sign function
    assert ask(Q.finite(sign(x))) is True
    assert ask(Q.finite(sign(x)), ~Q.finite(x)) is True

    # exponential functions
    assert ask(Q.finite(log(x))) is None
    assert ask(Q.finite(log(x)), Q.finite(x)) is True
    assert ask(Q.finite(exp(x))) is None
    assert ask(Q.finite(exp(x)), Q.finite(x)) is True
    assert ask(Q.finite(exp(2))) is True

    # trigonometric functions
    assert ask(Q.finite(sin(x))) is True
    assert ask(Q.finite(sin(x)), ~Q.finite(x)) is True
    assert ask(Q.finite(cos(x))) is True
    assert ask(Q.finite(cos(x)), ~Q.finite(x)) is True
    assert ask(Q.finite(2*sin(x))) is True
    assert ask(Q.finite(sin(x)**2)) is True
    assert ask(Q.finite(cos(x)**2)) is True
    assert ask(Q.finite(cos(x) + sin(x))) is True


@XFAIL
def test_bounded_xfail():
    """We need to support relations in ask for this to work"""
    assert ask(Q.finite(sin(x)**x)) is True
    assert ask(Q.finite(cos(x)**x)) is True


def test_commutative():
    """By default objects are Q.commutative that is why it returns True
    for both key=True and key=False"""
    assert ask(Q.commutative(x)) is True
    assert ask(Q.commutative(x), ~Q.commutative(x)) is False
    assert ask(Q.commutative(x), Q.complex(x)) is True
    assert ask(Q.commutative(x), Q.imaginary(x)) is True
    assert ask(Q.commutative(x), Q.real(x)) is True
    assert ask(Q.commutative(x), Q.positive(x)) is True
    assert ask(Q.commutative(x), ~Q.commutative(y)) is True

    assert ask(Q.commutative(2*x)) is True
    assert ask(Q.commutative(2*x), ~Q.commutative(x)) is False

    assert ask(Q.commutative(x + 1)) is True
    assert ask(Q.commutative(x + 1), ~Q.commutative(x)) is False

    assert ask(Q.commutative(x**2)) is True
    assert ask(Q.commutative(x**2), ~Q.commutative(x)) is False

    assert ask(Q.commutative(log(x))) is True


def test_complex():
    assert ask(Q.complex(x)) is None
    assert ask(Q.complex(x), Q.complex(x)) is True
    assert ask(Q.complex(x), Q.complex(y)) is None
    assert ask(Q.complex(x), ~Q.complex(x)) is False
    assert ask(Q.complex(x), Q.real(x)) is True
    assert ask(Q.complex(x), ~Q.real(x)) is None
    assert ask(Q.complex(x), Q.rational(x)) is True
    assert ask(Q.complex(x), Q.irrational(x)) is True
    assert ask(Q.complex(x), Q.positive(x)) is True
    assert ask(Q.complex(x), Q.imaginary(x)) is True
    assert ask(Q.complex(x), Q.algebraic(x)) is True

    # a+b
    assert ask(Q.complex(x + 1), Q.complex(x)) is True
    assert ask(Q.complex(x + 1), Q.real(x)) is True
    assert ask(Q.complex(x + 1), Q.rational(x)) is True
    assert ask(Q.complex(x + 1), Q.irrational(x)) is True
    assert ask(Q.complex(x + 1), Q.imaginary(x)) is True
    assert ask(Q.complex(x + 1), Q.integer(x)) is True
    assert ask(Q.complex(x + 1), Q.even(x)) is True
    assert ask(Q.complex(x + 1), Q.odd(x)) is True
    assert ask(Q.complex(x + y), Q.complex(x) & Q.complex(y)) is True
    assert ask(Q.complex(x + y), Q.real(x) & Q.imaginary(y)) is True

    # a*x +b
    assert ask(Q.complex(2*x + 1), Q.complex(x)) is True
    assert ask(Q.complex(2*x + 1), Q.real(x)) is True
    assert ask(Q.complex(2*x + 1), Q.positive(x)) is True
    assert ask(Q.complex(2*x + 1), Q.rational(x)) is True
    assert ask(Q.complex(2*x + 1), Q.irrational(x)) is True
    assert ask(Q.complex(2*x + 1), Q.imaginary(x)) is True
    assert ask(Q.complex(2*x + 1), Q.integer(x)) is True
    assert ask(Q.complex(2*x + 1), Q.even(x)) is True
    assert ask(Q.complex(2*x + 1), Q.odd(x)) is True

    # x**2
    assert ask(Q.complex(x**2), Q.complex(x)) is True
    assert ask(Q.complex(x**2), Q.real(x)) is True
    assert ask(Q.complex(x**2), Q.positive(x)) is True
    assert ask(Q.complex(x**2), Q.rational(x)) is True
    assert ask(Q.complex(x**2), Q.irrational(x)) is True
    assert ask(Q.complex(x**2), Q.imaginary(x)) is True
    assert ask(Q.complex(x**2), Q.integer(x)) is True
    assert ask(Q.complex(x**2), Q.even(x)) is True
    assert ask(Q.complex(x**2), Q.odd(x)) is True

    # 2**x
    assert ask(Q.complex(2**x), Q.complex(x)) is True
    assert ask(Q.complex(2**x), Q.real(x)) is True
    assert ask(Q.complex(2**x), Q.positive(x)) is True
    assert ask(Q.complex(2**x), Q.rational(x)) is True
    assert ask(Q.complex(2**x), Q.irrational(x)) is True
    assert ask(Q.complex(2**x), Q.imaginary(x)) is True
    assert ask(Q.complex(2**x), Q.integer(x)) is True
    assert ask(Q.complex(2**x), Q.even(x)) is True
    assert ask(Q.complex(2**x), Q.odd(x)) is True
    assert ask(Q.complex(x**y), Q.complex(x) & Q.complex(y)) is True

    # trigonometric expressions
    assert ask(Q.complex(sin(x))) is True
    assert ask(Q.complex(sin(2*x + 1))) is True
    assert ask(Q.complex(cos(x))) is True
    assert ask(Q.complex(cos(2*x + 1))) is True

    # exponential
    assert ask(Q.complex(exp(x))) is True
    assert ask(Q.complex(exp(x))) is True

    # Q.complexes
    assert ask(Q.complex(Abs(x))) is True
    assert ask(Q.complex(re(x))) is True
    assert ask(Q.complex(im(x))) is True


@slow
def test_even_query():
    assert ask(Q.even(x)) is None
    assert ask(Q.even(x), Q.integer(x)) is None
    assert ask(Q.even(x), ~Q.integer(x)) is False
    assert ask(Q.even(x), Q.rational(x)) is None
    assert ask(Q.even(x), Q.positive(x)) is None

    assert ask(Q.even(2*x)) is None
    assert ask(Q.even(2*x), Q.integer(x)) is True
    assert ask(Q.even(2*x), Q.even(x)) is True
    assert ask(Q.even(2*x), Q.irrational(x)) is False
    assert ask(Q.even(2*x), Q.odd(x)) is True
    assert ask(Q.even(2*x), ~Q.integer(x)) is None
    assert ask(Q.even(3*x), Q.integer(x)) is None
    assert ask(Q.even(3*x), Q.even(x)) is True
    assert ask(Q.even(3*x), Q.odd(x)) is False

    assert ask(Q.even(x + 1), Q.odd(x)) is True
    assert ask(Q.even(x + 1), Q.even(x)) is False
    assert ask(Q.even(x + 2), Q.odd(x)) is False
    assert ask(Q.even(x + 2), Q.even(x)) is True
    assert ask(Q.even(7 - x), Q.odd(x)) is True
    assert ask(Q.even(7 + x), Q.odd(x)) is True
    assert ask(Q.even(x + y), Q.odd(x) & Q.odd(y)) is True
    assert ask(Q.even(x + y), Q.odd(x) & Q.even(y)) is False
    assert ask(Q.even(x + y), Q.even(x) & Q.even(y)) is True

    assert ask(Q.even(2*x + 1), Q.integer(x)) is False
    assert ask(Q.even(2*x*y), Q.rational(x) & Q.rational(x)) is None
    assert ask(Q.even(2*x*y), Q.irrational(x) & Q.irrational(x)) is None

    assert ask(Q.even(x + y + z), Q.odd(x) & Q.odd(y) & Q.even(z)) is True
    assert ask(Q.even(x + y + z + t),
        Q.odd(x) & Q.odd(y) & Q.even(z) & Q.integer(t)) is None

    assert ask(Q.even(Abs(x)), Q.even(x)) is True
    assert ask(Q.even(Abs(x)), ~Q.even(x)) is None
    assert ask(Q.even(re(x)), Q.even(x)) is True
    assert ask(Q.even(re(x)), ~Q.even(x)) is None
    assert ask(Q.even(im(x)), Q.even(x)) is True
    assert ask(Q.even(im(x)), Q.real(x)) is True

    assert ask(Q.even((-1)**n), Q.integer(n)) is False

    assert ask(Q.even(k**2), Q.even(k)) is True
    assert ask(Q.even(n**2), Q.odd(n)) is False
    assert ask(Q.even(2**k), Q.even(k)) is None
    assert ask(Q.even(x**2)) is None

    assert ask(Q.even(k**m), Q.even(k) & Q.integer(m) & ~Q.negative(m)) is None
    assert ask(Q.even(n**m), Q.odd(n) & Q.integer(m) & ~Q.negative(m)) is False

    assert ask(Q.even(k**p), Q.even(k) & Q.integer(p) & Q.positive(p)) is True
    assert ask(Q.even(n**p), Q.odd(n) & Q.integer(p) & Q.positive(p)) is False

    assert ask(Q.even(m**k), Q.even(k) & Q.integer(m) & ~Q.negative(m)) is None
    assert ask(Q.even(p**k), Q.even(k) & Q.integer(p) & Q.positive(p)) is None

    assert ask(Q.even(m**n), Q.odd(n) & Q.integer(m) & ~Q.negative(m)) is None
    assert ask(Q.even(p**n), Q.odd(n) & Q.integer(p) & Q.positive(p)) is None

    assert ask(Q.even(k**x), Q.even(k)) is None
    assert ask(Q.even(n**x), Q.odd(n)) is None

    assert ask(Q.even(x*y), Q.integer(x) & Q.integer(y)) is None
    assert ask(Q.even(x*x), Q.integer(x)) is None
    assert ask(Q.even(x*(x + y)), Q.integer(x) & Q.odd(y)) is True
    assert ask(Q.even(x*(x + y)), Q.integer(x) & Q.even(y)) is None


@XFAIL
def test_evenness_in_ternary_integer_product_with_odd():
    # Tests that oddness inference is independent of term ordering.
    # Term ordering at the point of testing depends on SymPy's symbol order, so
    # we try to force a different order by modifying symbol names.
    assert ask(Q.even(x*y*(y + z)), Q.integer(x) & Q.integer(y) & Q.odd(z)) is True
    assert ask(Q.even(y*x*(x + z)), Q.integer(x) & Q.integer(y) & Q.odd(z)) is True


def test_evenness_in_ternary_integer_product_with_even():
    assert ask(Q.even(x*y*(y + z)), Q.integer(x) & Q.integer(y) & Q.even(z)) is None


def test_extended_real():
    assert ask(Q.extended_real(x), Q.positive(x)) is True
    assert ask(Q.extended_real(-x), Q.positive(x)) is True
    assert ask(Q.extended_real(-x), Q.negative(x)) is True

    assert ask(Q.extended_real(x + S.Infinity), Q.real(x)) is True


def test_rational():
    assert ask(Q.rational(x), Q.integer(x)) is True
    assert ask(Q.rational(x), Q.irrational(x)) is False
    assert ask(Q.rational(x), Q.real(x)) is None
    assert ask(Q.rational(x), Q.positive(x)) is None
    assert ask(Q.rational(x), Q.negative(x)) is None
    assert ask(Q.rational(x), Q.nonzero(x)) is None
    assert ask(Q.rational(x), ~Q.algebraic(x)) is False

    assert ask(Q.rational(2*x), Q.rational(x)) is True
    assert ask(Q.rational(2*x), Q.integer(x)) is True
    assert ask(Q.rational(2*x), Q.even(x)) is True
    assert ask(Q.rational(2*x), Q.odd(x)) is True
    assert ask(Q.rational(2*x), Q.irrational(x)) is False

    assert ask(Q.rational(x/2), Q.rational(x)) is True
    assert ask(Q.rational(x/2), Q.integer(x)) is True
    assert ask(Q.rational(x/2), Q.even(x)) is True
    assert ask(Q.rational(x/2), Q.odd(x)) is True
    assert ask(Q.rational(x/2), Q.irrational(x)) is False

    assert ask(Q.rational(1/x), Q.rational(x)) is True
    assert ask(Q.rational(1/x), Q.integer(x)) is True
    assert ask(Q.rational(1/x), Q.even(x)) is True
    assert ask(Q.rational(1/x), Q.odd(x)) is True
    assert ask(Q.rational(1/x), Q.irrational(x)) is False

    assert ask(Q.rational(2/x), Q.rational(x)) is True
    assert ask(Q.rational(2/x), Q.integer(x)) is True
    assert ask(Q.rational(2/x), Q.even(x)) is True
    assert ask(Q.rational(2/x), Q.odd(x)) is True
    assert ask(Q.rational(2/x), Q.irrational(x)) is False

    assert ask(Q.rational(x), ~Q.algebraic(x)) is False

    # with multiple symbols
    assert ask(Q.rational(x*y), Q.irrational(x) & Q.irrational(y)) is None
    assert ask(Q.rational(y/x), Q.rational(x) & Q.rational(y)) is True
    assert ask(Q.rational(y/x), Q.integer(x) & Q.rational(y)) is True
    assert ask(Q.rational(y/x), Q.even(x) & Q.rational(y)) is True
    assert ask(Q.rational(y/x), Q.odd(x) & Q.rational(y)) is True
    assert ask(Q.rational(y/x), Q.irrational(x) & Q.rational(y)) is False

    for f in [exp, sin, tan, asin, atan, cos]:
        assert ask(Q.rational(f(7))) is False
        assert ask(Q.rational(f(7, evaluate=False))) is False
        assert ask(Q.rational(f(0, evaluate=False))) is True
        assert ask(Q.rational(f(x)), Q.rational(x)) is None
        assert ask(Q.rational(f(x)), Q.rational(x) & Q.nonzero(x)) is False

    for g in [log, acos]:
        assert ask(Q.rational(g(7))) is False
        assert ask(Q.rational(g(7, evaluate=False))) is False
        assert ask(Q.rational(g(1, evaluate=False))) is True
        assert ask(Q.rational(g(x)), Q.rational(x)) is None
        assert ask(Q.rational(g(x)), Q.rational(x) & Q.nonzero(x - 1)) is False

    for h in [cot, acot]:
        assert ask(Q.rational(h(7))) is False
        assert ask(Q.rational(h(7, evaluate=False))) is False
        assert ask(Q.rational(h(x)), Q.rational(x)) is False


@slow
def test_hermitian():
    assert ask(Q.hermitian(x)) is None
    assert ask(Q.hermitian(x), Q.antihermitian(x)) is False
    assert ask(Q.hermitian(x), Q.imaginary(x)) is False
    assert ask(Q.hermitian(x), Q.prime(x)) is True
    assert ask(Q.hermitian(x), Q.real(x)) is True

    assert ask(Q.hermitian(x + 1), Q.antihermitian(x)) is False
    assert ask(Q.hermitian(x + 1), Q.complex(x)) is None
    assert ask(Q.hermitian(x + 1), Q.hermitian(x)) is True
    assert ask(Q.hermitian(x + 1), Q.imaginary(x)) is False
    assert ask(Q.hermitian(x + 1), Q.real(x)) is True
    assert ask(Q.hermitian(x + I), Q.antihermitian(x)) is None
    assert ask(Q.hermitian(x + I), Q.complex(x)) is None
    assert ask(Q.hermitian(x + I), Q.hermitian(x)) is False
    assert ask(Q.hermitian(x + I), Q.imaginary(x)) is None
    assert ask(Q.hermitian(x + I), Q.real(x)) is False
    assert ask(
        Q.hermitian(x + y), Q.antihermitian(x) & Q.antihermitian(y)) is None
    assert ask(Q.hermitian(x + y), Q.antihermitian(x) & Q.complex(y)) is None
    assert ask(
        Q.hermitian(x + y), Q.antihermitian(x) & Q.hermitian(y)) is False
    assert ask(Q.hermitian(x + y), Q.antihermitian(x) & Q.imaginary(y)) is None
    assert ask(Q.hermitian(x + y), Q.antihermitian(x) & Q.real(y)) is False
    assert ask(Q.hermitian(x + y), Q.hermitian(x) & Q.complex(y)) is None
    assert ask(Q.hermitian(x + y), Q.hermitian(x) & Q.hermitian(y)) is True
    assert ask(Q.hermitian(x + y), Q.hermitian(x) & Q.imaginary(y)) is False
    assert ask(Q.hermitian(x + y), Q.hermitian(x) & Q.real(y)) is True
    assert ask(Q.hermitian(x + y), Q.imaginary(x) & Q.complex(y)) is None
    assert ask(Q.hermitian(x + y), Q.imaginary(x) & Q.imaginary(y)) is None
    assert ask(Q.hermitian(x + y), Q.imaginary(x) & Q.real(y)) is False
    assert ask(Q.hermitian(x + y), Q.real(x) & Q.complex(y)) is None
    assert ask(Q.hermitian(x + y), Q.real(x) & Q.real(y)) is True

    assert ask(Q.hermitian(I*x), Q.antihermitian(x)) is True
    assert ask(Q.hermitian(I*x), Q.complex(x)) is None
    assert ask(Q.hermitian(I*x), Q.hermitian(x)) is False
    assert ask(Q.hermitian(I*x), Q.imaginary(x)) is True
    assert ask(Q.hermitian(I*x), Q.real(x)) is False
    assert ask(Q.hermitian(x*y), Q.hermitian(x) & Q.real(y)) is True

    assert ask(
        Q.hermitian(x + y + z), Q.real(x) & Q.real(y) & Q.real(z)) is True
    assert ask(Q.hermitian(x + y + z),
        Q.real(x) & Q.real(y) & Q.imaginary(z)) is False
    assert ask(Q.hermitian(x + y + z),
        Q.real(x) & Q.imaginary(y) & Q.imaginary(z)) is None
    assert ask(Q.hermitian(x + y + z),
        Q.imaginary(x) & Q.imaginary(y) & Q.imaginary(z)) is None

    assert ask(Q.antihermitian(x)) is None
    assert ask(Q.antihermitian(x), Q.real(x)) is False
    assert ask(Q.antihermitian(x), Q.prime(x)) is False

    assert ask(Q.antihermitian(x + 1), Q.antihermitian(x)) is False
    assert ask(Q.antihermitian(x + 1), Q.complex(x)) is None
    assert ask(Q.antihermitian(x + 1), Q.hermitian(x)) is None
    assert ask(Q.antihermitian(x + 1), Q.imaginary(x)) is False
    assert ask(Q.antihermitian(x + 1), Q.real(x)) is False
    assert ask(Q.antihermitian(x + I), Q.antihermitian(x)) is True
    assert ask(Q.antihermitian(x + I), Q.complex(x)) is None
    assert ask(Q.antihermitian(x + I), Q.hermitian(x)) is False
    assert ask(Q.antihermitian(x + I), Q.imaginary(x)) is True
    assert ask(Q.antihermitian(x + I), Q.real(x)) is False

    assert ask(
        Q.antihermitian(x + y), Q.antihermitian(x) & Q.antihermitian(y)
    ) is True
    assert ask(
        Q.antihermitian(x + y), Q.antihermitian(x) & Q.complex(y)) is None
    assert ask(
        Q.antihermitian(x + y), Q.antihermitian(x) & Q.hermitian(y)) is False
    assert ask(
        Q.antihermitian(x + y), Q.antihermitian(x) & Q.imaginary(y)) is True
    assert ask(Q.antihermitian(x + y), Q.antihermitian(x) & Q.real(y)
        ) is False
    assert ask(Q.antihermitian(x + y), Q.hermitian(x) & Q.complex(y)) is None
    assert ask(Q.antihermitian(x + y), Q.hermitian(x) & Q.hermitian(y)
        ) is None
    assert ask(
        Q.antihermitian(x + y), Q.hermitian(x) & Q.imaginary(y)) is False
    assert ask(Q.antihermitian(x + y), Q.hermitian(x) & Q.real(y)) is None
    assert ask(Q.antihermitian(x + y), Q.imaginary(x) & Q.complex(y)) is None
    assert ask(Q.antihermitian(x + y), Q.imaginary(x) & Q.imaginary(y)) is True
    assert ask(Q.antihermitian(x + y), Q.imaginary(x) & Q.real(y)) is False
    assert ask(Q.antihermitian(x + y), Q.real(x) & Q.complex(y)) is None
    assert ask(Q.antihermitian(x + y), Q.real(x) & Q.real(y)) is False

    assert ask(Q.antihermitian(I*x), Q.real(x)) is True
    assert ask(Q.antihermitian(I*x), Q.antihermitian(x)) is False
    assert ask(Q.antihermitian(I*x), Q.complex(x)) is None
    assert ask(Q.antihermitian(x*y), Q.antihermitian(x) & Q.real(y)) is True

    assert ask(Q.antihermitian(x + y + z),
        Q.real(x) & Q.real(y) & Q.real(z)) is False
    assert ask(Q.antihermitian(x + y + z),
        Q.real(x) & Q.real(y) & Q.imaginary(z)) is None
    assert ask(Q.antihermitian(x + y + z),
        Q.real(x) & Q.imaginary(y) & Q.imaginary(z)) is False
    assert ask(Q.antihermitian(x + y + z),
        Q.imaginary(x) & Q.imaginary(y) & Q.imaginary(z)) is True


@slow
def test_imaginary():
    assert ask(Q.imaginary(x)) is None
    assert ask(Q.imaginary(x), Q.real(x)) is False
    assert ask(Q.imaginary(x), Q.prime(x)) is False

    assert ask(Q.imaginary(x + 1), Q.real(x)) is False
    assert ask(Q.imaginary(x + 1), Q.imaginary(x)) is False
    assert ask(Q.imaginary(x + I), Q.real(x)) is False
    assert ask(Q.imaginary(x + I), Q.imaginary(x)) is True
    assert ask(Q.imaginary(x + y), Q.imaginary(x) & Q.imaginary(y)) is True
    assert ask(Q.imaginary(x + y), Q.real(x) & Q.real(y)) is False
    assert ask(Q.imaginary(x + y), Q.imaginary(x) & Q.real(y)) is False
    assert ask(Q.imaginary(x + y), Q.complex(x) & Q.real(y)) is None
    assert ask(
        Q.imaginary(x + y + z), Q.real(x) & Q.real(y) & Q.real(z)) is False
    assert ask(Q.imaginary(x + y + z),
        Q.real(x) & Q.real(y) & Q.imaginary(z)) is None
    assert ask(Q.imaginary(x + y + z),
        Q.real(x) & Q.imaginary(y) & Q.imaginary(z)) is False

    assert ask(Q.imaginary(I*x), Q.real(x)) is True
    assert ask(Q.imaginary(I*x), Q.imaginary(x)) is False
    assert ask(Q.imaginary(I*x), Q.complex(x)) is None
    assert ask(Q.imaginary(x*y), Q.imaginary(x) & Q.real(y)) is True
    assert ask(Q.imaginary(x*y), Q.real(x) & Q.real(y)) is False

    assert ask(Q.imaginary(I**x), Q.negative(x)) is None
    assert ask(Q.imaginary(I**x), Q.positive(x)) is None
    assert ask(Q.imaginary(I**x), Q.even(x)) is False
    assert ask(Q.imaginary(I**x), Q.odd(x)) is True
    assert ask(Q.imaginary(I**x), Q.imaginary(x)) is False
    assert ask(Q.imaginary((2*I)**x), Q.imaginary(x)) is False
    assert ask(Q.imaginary(x**0), Q.imaginary(x)) is False
    assert ask(Q.imaginary(x**y), Q.imaginary(x) & Q.imaginary(y)) is None
    assert ask(Q.imaginary(x**y), Q.imaginary(x) & Q.real(y)) is None
    assert ask(Q.imaginary(x**y), Q.real(x) & Q.imaginary(y)) is None
    assert ask(Q.imaginary(x**y), Q.real(x) & Q.real(y)) is None
    assert ask(Q.imaginary(x**y), Q.imaginary(x) & Q.integer(y)) is None
    assert ask(Q.imaginary(x**y), Q.imaginary(y) & Q.integer(x)) is None
    assert ask(Q.imaginary(x**y), Q.imaginary(x) & Q.odd(y)) is True
    assert ask(Q.imaginary(x**y), Q.imaginary(x) & Q.rational(y)) is None
    assert ask(Q.imaginary(x**y), Q.imaginary(x) & Q.even(y)) is False

    assert ask(Q.imaginary(x**y), Q.real(x) & Q.integer(y)) is False
    assert ask(Q.imaginary(x**y), Q.positive(x) & Q.real(y)) is False
    assert ask(Q.imaginary(x**y), Q.negative(x) & Q.real(y)) is None
    assert ask(Q.imaginary(x**y), Q.negative(x) & Q.real(y) & ~Q.rational(y)) is False
    assert ask(Q.imaginary(x**y), Q.integer(x) & Q.imaginary(y)) is None
    assert ask(Q.imaginary(x**y), Q.negative(x) & Q.rational(y) & Q.integer(2*y)) is True
    assert ask(Q.imaginary(x**y), Q.negative(x) & Q.rational(y) & ~Q.integer(2*y)) is False
    assert ask(Q.imaginary(x**y), Q.negative(x) & Q.rational(y)) is None
    assert ask(Q.imaginary(x**y), Q.real(x) & Q.rational(y) & ~Q.integer(2*y)) is False
    assert ask(Q.imaginary(x**y), Q.real(x) & Q.rational(y) & Q.integer(2*y)) is None

    # logarithm
    assert ask(Q.imaginary(log(I))) is True
    assert ask(Q.imaginary(log(2*I))) is False
    assert ask(Q.imaginary(log(I + 1))) is False
    assert ask(Q.imaginary(log(x)), Q.complex(x)) is None
    assert ask(Q.imaginary(log(x)), Q.imaginary(x)) is None
    assert ask(Q.imaginary(log(x)), Q.positive(x)) is False
    assert ask(Q.imaginary(log(exp(x))), Q.complex(x)) is None
    assert ask(Q.imaginary(log(exp(x))), Q.imaginary(x)) is None  # zoo/I/a+I*b
    assert ask(Q.imaginary(log(exp(I)))) is True

    # exponential
    assert ask(Q.imaginary(exp(x)**x), Q.imaginary(x)) is False
    eq = Pow(exp(pi*I*x, evaluate=False), x, evaluate=False)
    assert ask(Q.imaginary(eq), Q.even(x)) is False
    eq = Pow(exp(pi*I*x/2, evaluate=False), x, evaluate=False)
    assert ask(Q.imaginary(eq), Q.odd(x)) is True
    assert ask(Q.imaginary(exp(3*I*pi*x)**x), Q.integer(x)) is False
    assert ask(Q.imaginary(exp(2*pi*I, evaluate=False))) is False
    assert ask(Q.imaginary(exp(pi*I/2, evaluate=False))) is True

    # issue 7886
    assert ask(Q.imaginary(Pow(x, S.One/4)), Q.real(x) & Q.negative(x)) is False


def test_integer():
    assert ask(Q.integer(x)) is None
    assert ask(Q.integer(x), Q.integer(x)) is True
    assert ask(Q.integer(x), ~Q.integer(x)) is False
    assert ask(Q.integer(x), ~Q.real(x)) is False
    assert ask(Q.integer(x), ~Q.positive(x)) is None
    assert ask(Q.integer(x), Q.even(x) | Q.odd(x)) is True

    assert ask(Q.integer(2*x), Q.integer(x)) is True
    assert ask(Q.integer(2*x), Q.even(x)) is True
    assert ask(Q.integer(2*x), Q.prime(x)) is True
    assert ask(Q.integer(2*x), Q.rational(x)) is None
    assert ask(Q.integer(2*x), Q.real(x)) is None
    assert ask(Q.integer(sqrt(2)*x), Q.integer(x)) is False
    assert ask(Q.integer(sqrt(2)*x), Q.irrational(x)) is None

    assert ask(Q.integer(x/2), Q.odd(x)) is False
    assert ask(Q.integer(x/2), Q.even(x)) is True
    assert ask(Q.integer(x/3), Q.odd(x)) is None
    assert ask(Q.integer(x/3), Q.even(x)) is None


@slow
def test_negative():
    assert ask(Q.negative(x), Q.negative(x)) is True
    assert ask(Q.negative(x), Q.positive(x)) is False
    assert ask(Q.negative(x), ~Q.real(x)) is False
    assert ask(Q.negative(x), Q.prime(x)) is False
    assert ask(Q.negative(x), ~Q.prime(x)) is None

    assert ask(Q.negative(-x), Q.positive(x)) is True
    assert ask(Q.negative(-x), ~Q.positive(x)) is None
    assert ask(Q.negative(-x), Q.negative(x)) is False
    assert ask(Q.negative(-x), Q.positive(x)) is True

    assert ask(Q.negative(x - 1), Q.negative(x)) is True
    assert ask(Q.negative(x + y)) is None
    assert ask(Q.negative(x + y), Q.negative(x)) is None
    assert ask(Q.negative(x + y), Q.negative(x) & Q.negative(y)) is True
    assert ask(Q.negative(x + y), Q.negative(x) & Q.nonpositive(y)) is True
    assert ask(Q.negative(2 + I)) is False
    # although this could be False, it is representative of expressions
    # that don't evaluate to a zero with precision
    assert ask(Q.negative(cos(I)**2 + sin(I)**2 - 1)) is None
    assert ask(Q.negative(-I + I*(cos(2)**2 + sin(2)**2))) is None

    assert ask(Q.negative(x**2)) is None
    assert ask(Q.negative(x**2), Q.real(x)) is False
    assert ask(Q.negative(x**1.4), Q.real(x)) is None

    assert ask(Q.negative(x**I), Q.positive(x)) is None

    assert ask(Q.negative(x*y)) is None
    assert ask(Q.negative(x*y), Q.positive(x) & Q.positive(y)) is False
    assert ask(Q.negative(x*y), Q.positive(x) & Q.negative(y)) is True
    assert ask(Q.negative(x*y), Q.complex(x) & Q.complex(y)) is None

    assert ask(Q.negative(x**y)) is None
    assert ask(Q.negative(x**y), Q.negative(x) & Q.even(y)) is False
    assert ask(Q.negative(x**y), Q.negative(x) & Q.odd(y)) is True
    assert ask(Q.negative(x**y), Q.positive(x) & Q.integer(y)) is False

    assert ask(Q.negative(Abs(x))) is False


def test_nonzero():
    assert ask(Q.nonzero(x)) is None
    assert ask(Q.nonzero(x), Q.real(x)) is None
    assert ask(Q.nonzero(x), Q.positive(x)) is True
    assert ask(Q.nonzero(x), Q.negative(x)) is True
    assert ask(Q.nonzero(x), Q.negative(x) | Q.positive(x)) is True

    assert ask(Q.nonzero(x + y)) is None
    assert ask(Q.nonzero(x + y), Q.positive(x) & Q.positive(y)) is True
    assert ask(Q.nonzero(x + y), Q.positive(x) & Q.negative(y)) is None
    assert ask(Q.nonzero(x + y), Q.negative(x) & Q.negative(y)) is True

    assert ask(Q.nonzero(2*x)) is None
    assert ask(Q.nonzero(2*x), Q.positive(x)) is True
    assert ask(Q.nonzero(2*x), Q.negative(x)) is True
    assert ask(Q.nonzero(x*y), Q.nonzero(x)) is None
    assert ask(Q.nonzero(x*y), Q.nonzero(x) & Q.nonzero(y)) is True

    assert ask(Q.nonzero(x**y), Q.nonzero(x)) is True

    assert ask(Q.nonzero(Abs(x))) is None
    assert ask(Q.nonzero(Abs(x)), Q.nonzero(x)) is True

    assert ask(Q.nonzero(log(exp(2*I)))) is False
    # although this could be False, it is representative of expressions
    # that don't evaluate to a zero with precision
    assert ask(Q.nonzero(cos(1)**2 + sin(1)**2 - 1)) is None


@slow
def test_zero():
    assert ask(Q.zero(x)) is None
    assert ask(Q.zero(x), Q.real(x)) is None
    assert ask(Q.zero(x), Q.positive(x)) is False
    assert ask(Q.zero(x), Q.negative(x)) is False
    assert ask(Q.zero(x), Q.negative(x) | Q.positive(x)) is False

    assert ask(Q.zero(x), Q.nonnegative(x) & Q.nonpositive(x)) is True

    assert ask(Q.zero(x + y)) is None
    assert ask(Q.zero(x + y), Q.positive(x) & Q.positive(y)) is False
    assert ask(Q.zero(x + y), Q.positive(x) & Q.negative(y)) is None
    assert ask(Q.zero(x + y), Q.negative(x) & Q.negative(y)) is False

    assert ask(Q.zero(2*x)) is None
    assert ask(Q.zero(2*x), Q.positive(x)) is False
    assert ask(Q.zero(2*x), Q.negative(x)) is False
    assert ask(Q.zero(x*y), Q.nonzero(x)) is None

    assert ask(Q.zero(Abs(x))) is None
    assert ask(Q.zero(Abs(x)), Q.zero(x)) is True

    assert ask(Q.integer(x), Q.zero(x)) is True
    assert ask(Q.even(x), Q.zero(x)) is True
    assert ask(Q.odd(x), Q.zero(x)) is False
    assert ask(Q.zero(x), Q.even(x)) is None
    assert ask(Q.zero(x), Q.odd(x)) is False
    assert ask(Q.zero(x) | Q.zero(y), Q.zero(x*y)) is True


@slow
def test_odd_query():
    assert ask(Q.odd(x)) is None
    assert ask(Q.odd(x), Q.odd(x)) is True
    assert ask(Q.odd(x), Q.integer(x)) is None
    assert ask(Q.odd(x), ~Q.integer(x)) is False
    assert ask(Q.odd(x), Q.rational(x)) is None
    assert ask(Q.odd(x), Q.positive(x)) is None

    assert ask(Q.odd(-x), Q.odd(x)) is True

    assert ask(Q.odd(2*x)) is None
    assert ask(Q.odd(2*x), Q.integer(x)) is False
    assert ask(Q.odd(2*x), Q.odd(x)) is False
    assert ask(Q.odd(2*x), Q.irrational(x)) is False
    assert ask(Q.odd(2*x), ~Q.integer(x)) is None
    assert ask(Q.odd(3*x), Q.integer(x)) is None

    assert ask(Q.odd(x/3), Q.odd(x)) is None
    assert ask(Q.odd(x/3), Q.even(x)) is None

    assert ask(Q.odd(x + 1), Q.even(x)) is True
    assert ask(Q.odd(x + 2), Q.even(x)) is False
    assert ask(Q.odd(x + 2), Q.odd(x)) is True
    assert ask(Q.odd(3 - x), Q.odd(x)) is False
    assert ask(Q.odd(3 - x), Q.even(x)) is True
    assert ask(Q.odd(3 + x), Q.odd(x)) is False
    assert ask(Q.odd(3 + x), Q.even(x)) is True
    assert ask(Q.odd(x + y), Q.odd(x) & Q.odd(y)) is False
    assert ask(Q.odd(x + y), Q.odd(x) & Q.even(y)) is True
    assert ask(Q.odd(x - y), Q.even(x) & Q.odd(y)) is True
    assert ask(Q.odd(x - y), Q.odd(x) & Q.odd(y)) is False

    assert ask(Q.odd(x + y + z), Q.odd(x) & Q.odd(y) & Q.even(z)) is False
    assert ask(Q.odd(x + y + z + t),
        Q.odd(x) & Q.odd(y) & Q.even(z) & Q.integer(t)) is None

    assert ask(Q.odd(2*x + 1), Q.integer(x)) is True
    assert ask(Q.odd(2*x + y), Q.integer(x) & Q.odd(y)) is True
    assert ask(Q.odd(2*x + y), Q.integer(x) & Q.even(y)) is False
    assert ask(Q.odd(2*x + y), Q.integer(x) & Q.integer(y)) is None
    assert ask(Q.odd(x*y), Q.odd(x) & Q.even(y)) is False
    assert ask(Q.odd(x*y), Q.odd(x) & Q.odd(y)) is True
    assert ask(Q.odd(2*x*y), Q.rational(x) & Q.rational(x)) is None
    assert ask(Q.odd(2*x*y), Q.irrational(x) & Q.irrational(x)) is None

    assert ask(Q.odd(Abs(x)), Q.odd(x)) is True

    assert ask(Q.odd((-1)**n), Q.integer(n)) is True

    assert ask(Q.odd(k**2), Q.even(k)) is False
    assert ask(Q.odd(n**2), Q.odd(n)) is True
    assert ask(Q.odd(3**k), Q.even(k)) is None

    assert ask(Q.odd(k**m), Q.even(k) & Q.integer(m) & ~Q.negative(m)) is None
    assert ask(Q.odd(n**m), Q.odd(n) & Q.integer(m) & ~Q.negative(m)) is True

    assert ask(Q.odd(k**p), Q.even(k) & Q.integer(p) & Q.positive(p)) is False
    assert ask(Q.odd(n**p), Q.odd(n) & Q.integer(p) & Q.positive(p)) is True

    assert ask(Q.odd(m**k), Q.even(k) & Q.integer(m) & ~Q.negative(m)) is None
    assert ask(Q.odd(p**k), Q.even(k) & Q.integer(p) & Q.positive(p)) is None

    assert ask(Q.odd(m**n), Q.odd(n) & Q.integer(m) & ~Q.negative(m)) is None
    assert ask(Q.odd(p**n), Q.odd(n) & Q.integer(p) & Q.positive(p)) is None

    assert ask(Q.odd(k**x), Q.even(k)) is None
    assert ask(Q.odd(n**x), Q.odd(n)) is None

    assert ask(Q.odd(x*y), Q.integer(x) & Q.integer(y)) is None
    assert ask(Q.odd(x*x), Q.integer(x)) is None
    assert ask(Q.odd(x*(x + y)), Q.integer(x) & Q.odd(y)) is False
    assert ask(Q.odd(x*(x + y)), Q.integer(x) & Q.even(y)) is None


@XFAIL
def test_oddness_in_ternary_integer_product_with_odd():
    # Tests that oddness inference is independent of term ordering.
    # Term ordering at the point of testing depends on SymPy's symbol order, so
    # we try to force a different order by modifying symbol names.
    assert ask(Q.odd(x*y*(y + z)), Q.integer(x) & Q.integer(y) & Q.odd(z)) is False
    assert ask(Q.odd(y*x*(x + z)), Q.integer(x) & Q.integer(y) & Q.odd(z)) is False


def test_oddness_in_ternary_integer_product_with_even():
    assert ask(Q.odd(x*y*(y + z)), Q.integer(x) & Q.integer(y) & Q.even(z)) is None


def test_prime():
    assert ask(Q.prime(x), Q.prime(x)) is True
    assert ask(Q.prime(x), ~Q.prime(x)) is False
    assert ask(Q.prime(x), Q.integer(x)) is None
    assert ask(Q.prime(x), ~Q.integer(x)) is False

    assert ask(Q.prime(2*x), Q.integer(x)) is None
    assert ask(Q.prime(x*y)) is None
    assert ask(Q.prime(x*y), Q.prime(x)) is None
    assert ask(Q.prime(x*y), Q.integer(x) & Q.integer(y)) is None
    assert ask(Q.prime(4*x), Q.integer(x)) is False
    assert ask(Q.prime(4*x)) is None

    assert ask(Q.prime(x**2), Q.integer(x)) is False
    assert ask(Q.prime(x**2), Q.prime(x)) is False
    assert ask(Q.prime(x**y), Q.integer(x) & Q.integer(y)) is False


@slow
def test_positive():
    assert ask(Q.positive(x), Q.positive(x)) is True
    assert ask(Q.positive(x), Q.negative(x)) is False
    assert ask(Q.positive(x), Q.nonzero(x)) is None

    assert ask(Q.positive(-x), Q.positive(x)) is False
    assert ask(Q.positive(-x), Q.negative(x)) is True

    assert ask(Q.positive(x + y), Q.positive(x) & Q.positive(y)) is True
    assert ask(Q.positive(x + y), Q.positive(x) & Q.nonnegative(y)) is True
    assert ask(Q.positive(x + y), Q.positive(x) & Q.negative(y)) is None
    assert ask(Q.positive(x + y), Q.positive(x) & Q.imaginary(y)) is False

    assert ask(Q.positive(2*x), Q.positive(x)) is True
    assumptions = Q.positive(x) & Q.negative(y) & Q.negative(z) & Q.positive(w)
    assert ask(Q.positive(x*y*z)) is None
    assert ask(Q.positive(x*y*z), assumptions) is True
    assert ask(Q.positive(-x*y*z), assumptions) is False

    assert ask(Q.positive(x**I), Q.positive(x)) is None

    assert ask(Q.positive(x**2), Q.positive(x)) is True
    assert ask(Q.positive(x**2), Q.negative(x)) is True
    assert ask(Q.positive(x**3), Q.negative(x)) is False
    assert ask(Q.positive(1/(1 + x**2)), Q.real(x)) is True
    assert ask(Q.positive(2**I)) is False
    assert ask(Q.positive(2 + I)) is False
    # although this could be False, it is representative of expressions
    # that don't evaluate to a zero with precision
    assert ask(Q.positive(cos(I)**2 + sin(I)**2 - 1)) is None
    assert ask(Q.positive(-I + I*(cos(2)**2 + sin(2)**2))) is None

    #exponential
    assert ask(Q.positive(exp(x)), Q.real(x)) is True
    assert ask(~Q.negative(exp(x)), Q.real(x)) is True
    assert ask(Q.positive(x + exp(x)), Q.real(x)) is None
    assert ask(Q.positive(exp(x)), Q.imaginary(x)) is None
    assert ask(Q.positive(exp(2*pi*I, evaluate=False)), Q.imaginary(x)) is True
    assert ask(Q.negative(exp(pi*I, evaluate=False)), Q.imaginary(x)) is True
    assert ask(Q.positive(exp(x*pi*I)), Q.even(x)) is True
    assert ask(Q.positive(exp(x*pi*I)), Q.odd(x)) is False
    assert ask(Q.positive(exp(x*pi*I)), Q.real(x)) is None

    # logarithm
    assert ask(Q.positive(log(x)), Q.imaginary(x)) is False
    assert ask(Q.positive(log(x)), Q.negative(x)) is False
    assert ask(Q.positive(log(x)), Q.positive(x)) is None
    assert ask(Q.positive(log(x + 2)), Q.positive(x)) is True

    # factorial
    assert ask(Q.positive(factorial(x)), Q.integer(x) & Q.positive(x))
    assert ask(Q.positive(factorial(x)), Q.integer(x)) is None

    #absolute value
    assert ask(Q.positive(Abs(x))) is None  # Abs(0) = 0
    assert ask(Q.positive(Abs(x)), Q.positive(x)) is True


def test_nonpositive():
    assert ask(Q.nonpositive(-1))
    assert ask(Q.nonpositive(0))
    assert ask(Q.nonpositive(1)) is False
    assert ask(~Q.positive(x), Q.nonpositive(x))
    assert ask(Q.nonpositive(x), Q.positive(x)) is False
    assert ask(Q.nonpositive(sqrt(-1))) is False
    assert ask(Q.nonpositive(x), Q.imaginary(x)) is False


def test_nonnegative():
    assert ask(Q.nonnegative(-1)) is False
    assert ask(Q.nonnegative(0))
    assert ask(Q.nonnegative(1))
    assert ask(~Q.negative(x), Q.nonnegative(x))
    assert ask(Q.nonnegative(x), Q.negative(x)) is False
    assert ask(Q.nonnegative(sqrt(-1))) is False
    assert ask(Q.nonnegative(x), Q.imaginary(x)) is False

def test_real_basic():
    assert ask(Q.real(x)) is None
    assert ask(Q.real(x), Q.real(x)) is True
    assert ask(Q.real(x), Q.nonzero(x)) is True
    assert ask(Q.real(x), Q.positive(x)) is True
    assert ask(Q.real(x), Q.negative(x)) is True
    assert ask(Q.real(x), Q.integer(x)) is True
    assert ask(Q.real(x), Q.even(x)) is True
    assert ask(Q.real(x), Q.prime(x)) is True

    assert ask(Q.real(x/sqrt(2)), Q.real(x)) is True
    assert ask(Q.real(x/sqrt(-2)), Q.real(x)) is False

    assert ask(Q.real(x + 1), Q.real(x)) is True
    assert ask(Q.real(x + I), Q.real(x)) is False
    assert ask(Q.real(x + I), Q.complex(x)) is None

    assert ask(Q.real(2*x), Q.real(x)) is True
    assert ask(Q.real(I*x), Q.real(x)) is False
    assert ask(Q.real(I*x), Q.imaginary(x)) is True
    assert ask(Q.real(I*x), Q.complex(x)) is None

@slow
def test_real_pow():
    assert ask(Q.real(x**2), Q.real(x)) is True
    assert ask(Q.real(sqrt(x)), Q.negative(x)) is False
    assert ask(Q.real(x**y), Q.real(x) & Q.integer(y)) is True
    assert ask(Q.real(x**y), Q.real(x) & Q.real(y)) is None
    assert ask(Q.real(x**y), Q.positive(x) & Q.real(y)) is True
    assert ask(Q.real(x**y), Q.imaginary(x) & Q.imaginary(y)) is None  # I**I or (2*I)**I
    assert ask(Q.real(x**y), Q.imaginary(x) & Q.real(y)) is None  # I**1 or I**0
    assert ask(Q.real(x**y), Q.real(x) & Q.imaginary(y)) is None  # could be exp(2*pi*I) or 2**I
    assert ask(Q.real(x**0), Q.imaginary(x)) is True
    assert ask(Q.real(x**y), Q.real(x) & Q.integer(y)) is True
    assert ask(Q.real(x**y), Q.positive(x) & Q.real(y)) is True
    assert ask(Q.real(x**y), Q.real(x) & Q.rational(y)) is None
    assert ask(Q.real(x**y), Q.imaginary(x) & Q.integer(y)) is None
    assert ask(Q.real(x**y), Q.imaginary(x) & Q.odd(y)) is False
    assert ask(Q.real(x**y), Q.imaginary(x) & Q.even(y)) is True
    assert ask(Q.real(x**(y/z)), Q.real(x) & Q.real(y/z) & Q.rational(y/z) & Q.even(z) & Q.positive(x)) is True
    assert ask(Q.real(x**(y/z)), Q.real(x) & Q.rational(y/z) & Q.even(z) & Q.negative(x)) is False
    assert ask(Q.real(x**(y/z)), Q.real(x) & Q.integer(y/z)) is True
    assert ask(Q.real(x**(y/z)), Q.real(x) & Q.real(y/z) & Q.positive(x)) is True
    assert ask(Q.real(x**(y/z)), Q.real(x) & Q.real(y/z) & Q.negative(x)) is False
    assert ask(Q.real((-I)**i), Q.imaginary(i)) is True
    assert ask(Q.real(I**i), Q.imaginary(i)) is True
    assert ask(Q.real(i**i), Q.imaginary(i)) is None  # i might be 2*I
    assert ask(Q.real(x**i), Q.imaginary(i)) is None  # x could be 0
    assert ask(Q.real(x**(I*pi/log(x))), Q.real(x)) is True

def test_real_functions():
    # trigonometric functions
    assert ask(Q.real(sin(x))) is None
    assert ask(Q.real(cos(x))) is None
    assert ask(Q.real(sin(x)), Q.real(x)) is True
    assert ask(Q.real(cos(x)), Q.real(x)) is True

    # exponential function
    assert ask(Q.real(exp(x))) is None
    assert ask(Q.real(exp(x)), Q.real(x)) is True
    assert ask(Q.real(x + exp(x)), Q.real(x)) is True
    assert ask(Q.real(exp(2*pi*I, evaluate=False))) is True
    assert ask(Q.real(exp(pi*I, evaluate=False))) is True
    assert ask(Q.real(exp(pi*I/2, evaluate=False))) is False

    # logarithm
    assert ask(Q.real(log(I))) is False
    assert ask(Q.real(log(2*I))) is False
    assert ask(Q.real(log(I + 1))) is False
    assert ask(Q.real(log(x)), Q.complex(x)) is None
    assert ask(Q.real(log(x)), Q.imaginary(x)) is False
    assert ask(Q.real(log(exp(x))), Q.imaginary(x)) is None  # exp(2*pi*I) is 1, log(exp(pi*I)) is pi*I (disregarding periodicity)
    assert ask(Q.real(log(exp(x))), Q.complex(x)) is None
    eq = Pow(exp(2*pi*I*x, evaluate=False), x, evaluate=False)
    assert ask(Q.real(eq), Q.integer(x)) is True
    assert ask(Q.real(exp(x)**x), Q.imaginary(x)) is True
    assert ask(Q.real(exp(x)**x), Q.complex(x)) is None

    # Q.complexes
    assert ask(Q.real(re(x))) is True
    assert ask(Q.real(im(x))) is True


def test_algebraic():
    assert ask(Q.algebraic(x)) is None

    assert ask(Q.algebraic(I)) is True
    assert ask(Q.algebraic(2*I)) is True
    assert ask(Q.algebraic(I/3)) is True

    assert ask(Q.algebraic(sqrt(7))) is True
    assert ask(Q.algebraic(2*sqrt(7))) is True
    assert ask(Q.algebraic(sqrt(7)/3)) is True

    assert ask(Q.algebraic(I*sqrt(3))) is True
    assert ask(Q.algebraic(sqrt(1 + I*sqrt(3)))) is True

    assert ask(Q.algebraic((1 + I*sqrt(3)**(S(17)/31)))) is True
    assert ask(Q.algebraic((1 + I*sqrt(3)**(S(17)/pi)))) is False

    for f in [exp, sin, tan, asin, atan, cos]:
        assert ask(Q.algebraic(f(7))) is False
        assert ask(Q.algebraic(f(7, evaluate=False))) is False
        assert ask(Q.algebraic(f(0, evaluate=False))) is True
        assert ask(Q.algebraic(f(x)), Q.algebraic(x)) is None
        assert ask(Q.algebraic(f(x)), Q.algebraic(x) & Q.nonzero(x)) is False

    for g in [log, acos]:
        assert ask(Q.algebraic(g(7))) is False
        assert ask(Q.algebraic(g(7, evaluate=False))) is False
        assert ask(Q.algebraic(g(1, evaluate=False))) is True
        assert ask(Q.algebraic(g(x)), Q.algebraic(x)) is None
        assert ask(Q.algebraic(g(x)), Q.algebraic(x) & Q.nonzero(x - 1)) is False

    for h in [cot, acot]:
        assert ask(Q.algebraic(h(7))) is False
        assert ask(Q.algebraic(h(7, evaluate=False))) is False
        assert ask(Q.algebraic(h(x)), Q.algebraic(x)) is False

    assert ask(Q.algebraic(sqrt(sin(7)))) is False
    assert ask(Q.algebraic(sqrt(y + I*sqrt(7)))) is None

    assert ask(Q.algebraic(2.47)) is True

    assert ask(Q.algebraic(x), Q.transcendental(x)) is False
    assert ask(Q.transcendental(x), Q.algebraic(x)) is False


def test_global():
    """Test ask with global assumptions"""
    assert ask(Q.integer(x)) is None
    global_assumptions.add(Q.integer(x))
    assert ask(Q.integer(x)) is True
    global_assumptions.clear()
    assert ask(Q.integer(x)) is None


def test_custom_context():
    """Test ask with custom assumptions context"""
    assert ask(Q.integer(x)) is None
    local_context = AssumptionsContext()
    local_context.add(Q.integer(x))
    assert ask(Q.integer(x), context=local_context) is True
    assert ask(Q.integer(x)) is None


def test_functions_in_assumptions():
    assert ask(Q.negative(x), Q.real(x) >> Q.positive(x)) is False
    assert ask(Q.negative(x), Equivalent(Q.real(x), Q.positive(x))) is False
    assert ask(Q.negative(x), Xor(Q.real(x), Q.negative(x))) is False


def test_composite_ask():
    assert ask(Q.negative(x) & Q.integer(x),
        assumptions=Q.real(x) >> Q.positive(x)) is False


def test_composite_proposition():
    assert ask(True) is True
    assert ask(False) is False
    assert ask(~Q.negative(x), Q.positive(x)) is True
    assert ask(~Q.real(x), Q.commutative(x)) is None
    assert ask(Q.negative(x) & Q.integer(x), Q.positive(x)) is False
    assert ask(Q.negative(x) & Q.integer(x)) is None
    assert ask(Q.real(x) | Q.integer(x), Q.positive(x)) is True
    assert ask(Q.real(x) | Q.integer(x)) is None
    assert ask(Q.real(x) >> Q.positive(x), Q.negative(x)) is False
    assert ask(Implies(
        Q.real(x), Q.positive(x), evaluate=False), Q.negative(x)) is False
    assert ask(Implies(Q.real(x), Q.positive(x), evaluate=False)) is None
    assert ask(Equivalent(Q.integer(x), Q.even(x)), Q.even(x)) is True
    assert ask(Equivalent(Q.integer(x), Q.even(x))) is None
    assert ask(Equivalent(Q.positive(x), Q.integer(x)), Q.integer(x)) is None
    assert ask(Q.real(x) | Q.integer(x), Q.real(x) | Q.integer(x)) is True

def test_tautology():
    assert ask(Q.real(x) | ~Q.real(x)) is True
    assert ask(Q.real(x) & ~Q.real(x)) is False

def test_composite_assumptions():
    assert ask(Q.real(x), Q.real(x) & Q.real(y)) is True
    assert ask(Q.positive(x), Q.positive(x) | Q.positive(y)) is None
    assert ask(Q.positive(x), Q.real(x) >> Q.positive(y)) is None
    assert ask(Q.real(x), ~(Q.real(x) >> Q.real(y))) is True


def test_incompatible_resolutors():
    class Prime2AskHandler(AskHandler):
        @staticmethod
        def Number(expr, assumptions):
            return True
    register_handler('prime', Prime2AskHandler)
    raises(ValueError, lambda: ask(Q.prime(4)))
    remove_handler('prime', Prime2AskHandler)

    class InconclusiveHandler(AskHandler):
        @staticmethod
        def Number(expr, assumptions):
            return None
    register_handler('prime', InconclusiveHandler)
    assert ask(Q.prime(3)) is True
    remove_handler('prime', InconclusiveHandler)

def test_key_extensibility():
    """test that you can add keys to the ask system at runtime"""
    # make sure the key is not defined
    raises(AttributeError, lambda: ask(Q.my_key(x)))

    class MyAskHandler(AskHandler):
        @staticmethod
        def Symbol(expr, assumptions):
            return True
    register_handler('my_key', MyAskHandler)
    assert ask(Q.my_key(x)) is True
    assert ask(Q.my_key(x + 1)) is None
    remove_handler('my_key', MyAskHandler)
    del Q.my_key
    raises(AttributeError, lambda: ask(Q.my_key(x)))


def test_type_extensibility():
    """test that new types can be added to the ask system at runtime
    We create a custom type MyType, and override ask Q.prime=True with handler
    MyAskHandler for this type

    TODO: test incompatible resolutors
    """
    from sympy.core import Basic

    class MyType(Basic):
        pass

    class MyAskHandler(AskHandler):
        @staticmethod
        def MyType(expr, assumptions):
            return True

    a = MyType()
    register_handler(Q.prime, MyAskHandler)
    assert ask(Q.prime(a)) is True


def test_single_fact_lookup():
    known_facts = And(Implies(Q.integer, Q.rational),
                      Implies(Q.rational, Q.real),
                      Implies(Q.real, Q.complex))
    known_facts_keys = {Q.integer, Q.rational, Q.real, Q.complex}

    known_facts_cnf = to_cnf(known_facts)
    mapping = single_fact_lookup(known_facts_keys, known_facts_cnf)

    assert mapping[Q.rational] == {Q.real, Q.rational, Q.complex}


def test_compute_known_facts():
    known_facts = And(Implies(Q.integer, Q.rational),
                      Implies(Q.rational, Q.real),
                      Implies(Q.real, Q.complex))
    known_facts_keys = {Q.integer, Q.rational, Q.real, Q.complex}

    s = compute_known_facts(known_facts, known_facts_keys)


@slow
def test_known_facts_consistent():
    """"Test that ask_generated.py is up-to-date"""
    from sympy.assumptions.ask import get_known_facts, get_known_facts_keys
    from os.path import abspath, dirname, join
    filename = join(dirname(dirname(abspath(__file__))), 'ask_generated.py')
    with open(filename, 'r') as f:
        assert f.read() == \
            compute_known_facts(get_known_facts(), get_known_facts_keys())


def test_Add_queries():
    assert ask(Q.prime(12345678901234567890 + (cos(1)**2 + sin(1)**2))) is True
    assert ask(Q.even(Add(S(2), S(2), evaluate=0))) is True
    assert ask(Q.prime(Add(S(2), S(2), evaluate=0))) is False
    assert ask(Q.integer(Add(S(2), S(2), evaluate=0))) is True


def test_positive_assuming():
    with assuming(Q.positive(x + 1)):
        assert not ask(Q.positive(x))


def test_issue_5421():
    raises(TypeError, lambda: ask(pi/log(x), Q.real))


def test_issue_3906():
    raises(TypeError, lambda: ask(Q.positive))


def test_issue_5833():
    assert ask(Q.positive(log(x)**2), Q.positive(x)) is None
    assert ask(~Q.negative(log(x)**2), Q.positive(x)) is True


def test_issue_6732():
    raises(ValueError, lambda: ask(Q.positive(x), Q.positive(x) & Q.negative(x)))
    raises(ValueError, lambda: ask(Q.negative(x), Q.positive(x) & Q.negative(x)))


def test_issue_7246():
    assert ask(Q.positive(atan(p)), Q.positive(p)) is True
    assert ask(Q.positive(atan(p)), Q.negative(p)) is False
    assert ask(Q.positive(atan(p)), Q.zero(p)) is False
    assert ask(Q.positive(atan(x))) is None

    assert ask(Q.positive(asin(p)), Q.positive(p)) is None
    assert ask(Q.positive(asin(p)), Q.zero(p)) is None
    assert ask(Q.positive(asin(Rational(1, 7)))) is True
    assert ask(Q.positive(asin(x)), Q.positive(x) & Q.nonpositive(x - 1)) is True
    assert ask(Q.positive(asin(x)), Q.negative(x) & Q.nonnegative(x + 1)) is False

    assert ask(Q.positive(acos(p)), Q.positive(p)) is None
    assert ask(Q.positive(acos(Rational(1, 7)))) is True
    assert ask(Q.positive(acos(x)), Q.nonnegative(x + 1) & Q.nonpositive(x - 1)) is True
    assert ask(Q.positive(acos(x)), Q.nonnegative(x - 1)) is None

    assert ask(Q.positive(acot(x)), Q.positive(x)) is True
    assert ask(Q.positive(acot(x)), Q.real(x)) is True
    assert ask(Q.positive(acot(x)), Q.imaginary(x)) is False
    assert ask(Q.positive(acot(x))) is None


@XFAIL
def test_issue_7246_failing():
    #Move this test to test_issue_7246 once
    #the new assumptions module is improved.
    assert ask(Q.positive(acos(x)), Q.zero(x)) is True


def test_deprecated_Q_bounded():
    with warns_deprecated_sympy():
        Q.bounded

def test_deprecated_Q_infinity():
    with warns_deprecated_sympy():
        Q.infinity


def test_check_old_assumption():
    x = symbols('x', real=True)
    assert ask(Q.real(x)) is True
    assert ask(Q.imaginary(x)) is False
    assert ask(Q.complex(x)) is True

    x = symbols('x', imaginary=True)
    assert ask(Q.real(x)) is False
    assert ask(Q.imaginary(x)) is True
    assert ask(Q.complex(x)) is True

    x = symbols('x', complex=True)
    assert ask(Q.real(x)) is None
    assert ask(Q.complex(x)) is True

    x = symbols('x', positive=True)
    assert ask(Q.positive(x)) is True
    assert ask(Q.negative(x)) is False
    assert ask(Q.real(x)) is True

    x = symbols('x', commutative=False)
    assert ask(Q.commutative(x)) is False

    x = symbols('x', negative=True)
    assert ask(Q.positive(x)) is False
    assert ask(Q.negative(x)) is True

    x = symbols('x', nonnegative=True)
    assert ask(Q.negative(x)) is False
    assert ask(Q.positive(x)) is None
    assert ask(Q.zero(x)) is None

    x = symbols('x', finite=True)
    assert ask(Q.finite(x)) is True

    x = symbols('x', prime=True)
    assert ask(Q.prime(x)) is True
    assert ask(Q.composite(x)) is False

    x = symbols('x', composite=True)
    assert ask(Q.prime(x)) is False
    assert ask(Q.composite(x)) is True

    x = symbols('x', even=True)
    assert ask(Q.even(x)) is True
    assert ask(Q.odd(x)) is False

    x = symbols('x', odd=True)
    assert ask(Q.even(x)) is False
    assert ask(Q.odd(x)) is True

    x = symbols('x', nonzero=True)
    assert ask(Q.nonzero(x)) is True
    assert ask(Q.zero(x)) is False

    x = symbols('x', zero=True)
    assert ask(Q.zero(x)) is True

    x = symbols('x', integer=True)
    assert ask(Q.integer(x)) is True

    x = symbols('x', rational=True)
    assert ask(Q.rational(x)) is True
    assert ask(Q.irrational(x)) is False

    x = symbols('x', irrational=True)
    assert ask(Q.irrational(x)) is True
    assert ask(Q.rational(x)) is False


def test_issue_9636():
    assert ask(Q.integer(1.0)) is False
    assert ask(Q.prime(3.0)) is False
    assert ask(Q.composite(4.0)) is False
    assert ask(Q.even(2.0)) is False
    assert ask(Q.odd(3.0)) is False


def test_autosimp_used_to_fail():
    # See issue #9807
    assert ask(Q.imaginary(0**I)) is False
    assert ask(Q.imaginary(0**(-I))) is False
    assert ask(Q.real(0**I)) is False
    assert ask(Q.real(0**(-I))) is False
