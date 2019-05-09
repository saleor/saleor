from sympy import (
    adjoint, conjugate, nan, pi, symbols, transpose, DiracDelta, Symbol, diff,
    Piecewise, I, Eq, Derivative, oo, SingularityFunction, Heaviside,
    Derivative, Float
)


from sympy.core.function import ArgumentIndexError
from sympy.utilities.pytest import raises

x, y, a, n = symbols('x y a n')


def test_fdiff():
    assert SingularityFunction(x, 4, 5).fdiff() == 5*SingularityFunction(x, 4, 4)
    assert SingularityFunction(x, 4, -1).fdiff() == SingularityFunction(x, 4, -2)
    assert SingularityFunction(x, 4, 0).fdiff() == SingularityFunction(x, 4, -1)

    assert SingularityFunction(y, 6, 2).diff(y) == 2*SingularityFunction(y, 6, 1)
    assert SingularityFunction(y, -4, -1).diff(y) == SingularityFunction(y, -4, -2)
    assert SingularityFunction(y, 4, 0).diff(y) == SingularityFunction(y, 4, -1)
    assert SingularityFunction(y, 4, 0).diff(y, 2) == SingularityFunction(y, 4, -2)

    n = Symbol('n', positive=True)
    assert SingularityFunction(x, a, n).fdiff() == n*SingularityFunction(x, a, n - 1)
    assert SingularityFunction(y, a, n).diff(y) == n*SingularityFunction(y, a, n - 1)

    expr_in = 4*SingularityFunction(x, a, n) + 3*SingularityFunction(x, a, -1) + -10*SingularityFunction(x, a, 0)
    expr_out = n*4*SingularityFunction(x, a, n - 1) + 3*SingularityFunction(x, a, -2) - 10*SingularityFunction(x, a, -1)
    assert diff(expr_in, x) == expr_out

    assert SingularityFunction(x, -10, 5).diff(evaluate=False) == (
        Derivative(SingularityFunction(x, -10, 5), x))

    raises(ArgumentIndexError, lambda: SingularityFunction(x, 4, 5).fdiff(2))


def test_eval():
    assert SingularityFunction(x, a, n).func == SingularityFunction
    assert SingularityFunction(x, 5, n) == SingularityFunction(x, 5, n)
    assert SingularityFunction(5, 3, 2) == 4
    assert SingularityFunction(3, 5, 1) == 0
    assert SingularityFunction(3, 3, 0) == 1
    assert SingularityFunction(4, 4, -1) == oo
    assert SingularityFunction(4, 2, -1) == 0
    assert SingularityFunction(4, 7, -1) == 0
    assert SingularityFunction(5, 6, -2) == 0
    assert SingularityFunction(4, 2, -2) == 0
    assert SingularityFunction(4, 4, -2) == oo
    assert (SingularityFunction(6.1, 4, 5)).evalf(5) == Float('40.841', '5')
    assert SingularityFunction(6.1, pi, 2) == (-pi + 6.1)**2
    assert SingularityFunction(x, a, nan) == nan
    assert SingularityFunction(x, nan, 1) == nan
    assert SingularityFunction(nan, a, n) == nan

    raises(ValueError, lambda: SingularityFunction(x, a, I))
    raises(ValueError, lambda: SingularityFunction(2*I, I, n))
    raises(ValueError, lambda: SingularityFunction(x, a, -3))


def test_rewrite():
    assert SingularityFunction(x, 4, 5).rewrite(Piecewise) == (
        Piecewise(((x - 4)**5, x - 4 > 0), (0, True)))
    assert SingularityFunction(x, -10, 0).rewrite(Piecewise) == (
        Piecewise((1, x + 10 > 0), (0, True)))
    assert SingularityFunction(x, 2, -1).rewrite(Piecewise) == (
        Piecewise((oo, Eq(x - 2, 0)), (0, True)))
    assert SingularityFunction(x, 0, -2).rewrite(Piecewise) == (
        Piecewise((oo, Eq(x, 0)), (0, True)))

    n = Symbol('n', nonnegative=True)
    assert SingularityFunction(x, a, n).rewrite(Piecewise) == (
        Piecewise(((x - a)**n, x - a > 0), (0, True)))

    expr_in = SingularityFunction(x, 4, 5) + SingularityFunction(x, -3, -1) - SingularityFunction(x, 0, -2)
    expr_out = (x - 4)**5*Heaviside(x - 4) + DiracDelta(x + 3) - DiracDelta(x, 1)
    assert expr_in.rewrite(Heaviside) == expr_out
    assert expr_in.rewrite(DiracDelta) == expr_out
    assert expr_in.rewrite('HeavisideDiracDelta') == expr_out

    expr_in = SingularityFunction(x, a, n) + SingularityFunction(x, a, -1) - SingularityFunction(x, a, -2)
    expr_out = (x - a)**n*Heaviside(x - a) + DiracDelta(x - a) + DiracDelta(a - x, 1)
    assert expr_in.rewrite(Heaviside) == expr_out
    assert expr_in.rewrite(DiracDelta) == expr_out
    assert expr_in.rewrite('HeavisideDiracDelta') == expr_out
