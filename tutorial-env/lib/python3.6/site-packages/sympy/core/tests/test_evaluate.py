from sympy.abc import x, y
from sympy.core.evaluate import evaluate
from sympy.core import Mul, Add, Pow, S
from sympy import sqrt

def test_add():
    with evaluate(False):
        expr = x + x
        assert isinstance(expr, Add)
        assert expr.args == (x, x)

        with evaluate(True):
            assert (x + x).args == (2, x)

        assert (x + x).args == (x, x)

    assert isinstance(x + x, Mul)

    with evaluate(False):
        assert S(1) + 1 == Add(1, 1)
        assert 1 + S(1) == Add(1, 1)

        assert S(4) - 3 == Add(4, -3)
        assert -3 + S(4) == Add(4, -3)

        assert S(2) * 4 == Mul(2, 4)
        assert 4 * S(2) == Mul(2, 4)

        assert S(6) / 3 == Mul(6, S(1) / 3)
        assert S(1) / 3 * 6 == Mul(S(1) / 3, 6)

        assert 9 ** S(2) == Pow(9, 2)
        assert S(2) ** 9 == Pow(2, 9)

        assert S(2) / 2 == Mul(2, S(1) / 2)
        assert S(1) / 2 * 2 == Mul(S(1) / 2, 2)

        assert S(2) / 3 + 1 == Add(S(2) / 3, 1)
        assert 1 + S(2) / 3 == Add(1, S(2) / 3)

        assert S(4) / 7 - 3 == Add(S(4) / 7, -3)
        assert -3 + S(4) / 7 == Add(-3, S(4) / 7)

        assert S(2) / 4 * 4 == Mul(S(2) / 4, 4)
        assert 4 * (S(2) / 4) == Mul(4, S(2) / 4)

        assert S(6) / 3 == Mul(6, S(1) / 3)
        assert S(1) / 3 * 6 == Mul(S(1) / 3, 6)

        assert S(1) / 3 + sqrt(3) == Add(S(1) / 3, sqrt(3))
        assert sqrt(3) + S(1) / 3 == Add(sqrt(3), S(1) / 3)

        assert S(1) / 2 * 10.333 == Mul(S(1) / 2, 10.333)
        assert 10.333 * S(1) / 2 == Mul(10.333, S(1) / 2)

        assert sqrt(2) * sqrt(2) == Mul(sqrt(2), sqrt(2))

        assert S(1) / 2 + x == Add(S(1) / 2, x)
        assert x + S(1) / 2 == Add(x, S(1) / 2)

        assert S(1) / x * x == Mul(S(1) / x, x)
        assert x * S(1) / x == Mul(x, S(1) / x)

def test_nested():
    with evaluate(False):
        expr = (x + x) + (y + y)
        assert expr.args == ((x + x), (y + y))
        assert expr.args[0].args == (x, x)
