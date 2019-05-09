from sympy import (
    adjoint, conjugate, DiracDelta, Heaviside, nan, pi, sign, sqrt,
    symbols, transpose, Symbol, Piecewise, I, S, Eq, oo,
    SingularityFunction, signsimp
)

from sympy.utilities.pytest import raises, warns_deprecated_sympy

from sympy.core.function import ArgumentIndexError

from sympy.utilities.misc import filldedent

x, y = symbols('x y')
i = symbols('t', nonzero=True)
j = symbols('j', positive=True)
k = symbols('k', negative=True)

def test_DiracDelta():
    assert DiracDelta(1) == 0
    assert DiracDelta(5.1) == 0
    assert DiracDelta(-pi) == 0
    assert DiracDelta(5, 7) == 0
    assert DiracDelta(i) == 0
    assert DiracDelta(j) == 0
    assert DiracDelta(k) == 0
    assert DiracDelta(nan) == nan
    assert DiracDelta(0).func is DiracDelta
    assert DiracDelta(x).func is DiracDelta
    # FIXME: this is generally undefined @ x=0
    #         But then limit(Delta(c)*Heaviside(x),x,-oo)
    #         need's to be implemented.
    # assert 0*DiracDelta(x) == 0

    assert adjoint(DiracDelta(x)) == DiracDelta(x)
    assert adjoint(DiracDelta(x - y)) == DiracDelta(x - y)
    assert conjugate(DiracDelta(x)) == DiracDelta(x)
    assert conjugate(DiracDelta(x - y)) == DiracDelta(x - y)
    assert transpose(DiracDelta(x)) == DiracDelta(x)
    assert transpose(DiracDelta(x - y)) == DiracDelta(x - y)

    assert DiracDelta(x).diff(x) == DiracDelta(x, 1)
    assert DiracDelta(x, 1).diff(x) == DiracDelta(x, 2)

    assert DiracDelta(x).is_simple(x) is True
    assert DiracDelta(3*x).is_simple(x) is True
    assert DiracDelta(x**2).is_simple(x) is False
    assert DiracDelta(sqrt(x)).is_simple(x) is False
    assert DiracDelta(x).is_simple(y) is False

    assert DiracDelta(x*y).expand(diracdelta=True, wrt=x) == DiracDelta(x)/abs(y)
    assert DiracDelta(x*y).expand(diracdelta=True, wrt=y) == DiracDelta(y)/abs(x)
    assert DiracDelta(x**2*y).expand(diracdelta=True, wrt=x) == DiracDelta(x**2*y)
    assert DiracDelta(y).expand(diracdelta=True, wrt=x) == DiracDelta(y)
    assert DiracDelta((x - 1)*(x - 2)*(x - 3)).expand(diracdelta=True, wrt=x) == (
        DiracDelta(x - 3)/2 + DiracDelta(x - 2) + DiracDelta(x - 1)/2)

    assert DiracDelta(2*x) != DiracDelta(x)  # scaling property
    assert DiracDelta(x) == DiracDelta(-x)  # even function
    assert DiracDelta(-x, 2) == DiracDelta(x, 2)
    assert DiracDelta(-x, 1) == -DiracDelta(x, 1)  # odd deriv is odd
    assert DiracDelta(-oo*x) == DiracDelta(oo*x)
    assert DiracDelta(x - y) != DiracDelta(y - x)
    assert signsimp(DiracDelta(x - y) - DiracDelta(y - x)) == 0

    with warns_deprecated_sympy():
        assert DiracDelta(x*y).simplify(x) == DiracDelta(x)/abs(y)
    with warns_deprecated_sympy():
        assert DiracDelta(x*y).simplify(y) == DiracDelta(y)/abs(x)
    with warns_deprecated_sympy():
        assert DiracDelta(x**2*y).simplify(x) == DiracDelta(x**2*y)
    with warns_deprecated_sympy():
        assert DiracDelta(y).simplify(x) == DiracDelta(y)
    with warns_deprecated_sympy():
        assert DiracDelta((x - 1)*(x - 2)*(x - 3)).simplify(x) == (
            DiracDelta(x - 3)/2 + DiracDelta(x - 2) + DiracDelta(x - 1)/2)

    raises(ArgumentIndexError, lambda: DiracDelta(x).fdiff(2))
    raises(ValueError, lambda: DiracDelta(x, -1))
    raises(ValueError, lambda: DiracDelta(I))
    raises(ValueError, lambda: DiracDelta(2 + 3*I))


def test_heaviside():
    assert Heaviside(0).func == Heaviside
    assert Heaviside(-5) == 0
    assert Heaviside(1) == 1
    assert Heaviside(nan) == nan

    assert Heaviside(0, x) == x
    assert Heaviside(0, nan) == nan
    assert Heaviside(x, None) == Heaviside(x)
    assert Heaviside(0, None) == Heaviside(0)
    # we do not want None in the args:
    assert None not in Heaviside(x, None).args

    assert adjoint(Heaviside(x)) == Heaviside(x)
    assert adjoint(Heaviside(x - y)) == Heaviside(x - y)
    assert conjugate(Heaviside(x)) == Heaviside(x)
    assert conjugate(Heaviside(x - y)) == Heaviside(x - y)
    assert transpose(Heaviside(x)) == Heaviside(x)
    assert transpose(Heaviside(x - y)) == Heaviside(x - y)

    assert Heaviside(x).diff(x) == DiracDelta(x)
    assert Heaviside(x + I).is_Function is True
    assert Heaviside(I*x).is_Function is True

    raises(ArgumentIndexError, lambda: Heaviside(x).fdiff(2))
    raises(ValueError, lambda: Heaviside(I))
    raises(ValueError, lambda: Heaviside(2 + 3*I))


def test_rewrite():
    x, y = Symbol('x', real=True), Symbol('y')
    assert Heaviside(x).rewrite(Piecewise) == (
        Piecewise((0, x < 0), (Heaviside(0), Eq(x, 0)), (1, x > 0)))
    assert Heaviside(y).rewrite(Piecewise) == (
        Piecewise((0, y < 0), (Heaviside(0), Eq(y, 0)), (1, y > 0)))
    assert Heaviside(x, y).rewrite(Piecewise) == (
        Piecewise((0, x < 0), (y, Eq(x, 0)), (1, x > 0)))
    assert Heaviside(x, 0).rewrite(Piecewise) == (
        Piecewise((0, x <= 0), (1, x > 0)))
    assert Heaviside(x, 1).rewrite(Piecewise) == (
        Piecewise((0, x < 0), (1, x >= 0)))

    assert Heaviside(x).rewrite(sign) == (sign(x)+1)/2
    assert Heaviside(y).rewrite(sign) == Heaviside(y)
    assert Heaviside(x, S.Half).rewrite(sign) == (sign(x)+1)/2
    assert Heaviside(x, y).rewrite(sign) == Heaviside(x, y)

    assert DiracDelta(y).rewrite(Piecewise) == Piecewise((DiracDelta(0), Eq(y, 0)), (0, True))
    assert DiracDelta(y, 1).rewrite(Piecewise) == DiracDelta(y, 1)
    assert DiracDelta(x - 5).rewrite(Piecewise) == (
        Piecewise((DiracDelta(0), Eq(x - 5, 0)), (0, True)))

    assert (x*DiracDelta(x - 10)).rewrite(SingularityFunction) == x*SingularityFunction(x, 10, -1)
    assert 5*x*y*DiracDelta(y, 1).rewrite(SingularityFunction) == 5*x*y*SingularityFunction(y, 0, -2)
    assert DiracDelta(0).rewrite(SingularityFunction) == SingularityFunction(0, 0, -1)
    assert DiracDelta(0, 1).rewrite(SingularityFunction) == SingularityFunction(0, 0, -2)

    assert Heaviside(x).rewrite(SingularityFunction) == SingularityFunction(x, 0, 0)
    assert 5*x*y*Heaviside(y + 1).rewrite(SingularityFunction) == 5*x*y*SingularityFunction(y, -1, 0)
    assert ((x - 3)**3*Heaviside(x - 3)).rewrite(SingularityFunction) == (x - 3)**3*SingularityFunction(x, 3, 0)
    assert Heaviside(0).rewrite(SingularityFunction) == SingularityFunction(0, 0, 0)

def test_issue_15923():
    x = Symbol('x', real=True)
    assert Heaviside(x).rewrite(Piecewise, H0=0) == (
        Piecewise((0, x <= 0), (1, True)))
    assert Heaviside(x).rewrite(Piecewise, H0=1) == (
        Piecewise((0, x < 0), (1, True)))
    assert Heaviside(x).rewrite(Piecewise, H0=S(1)/2) == (
        Piecewise((0, x < 0), (S(1)/2, Eq(x, 0)), (1, x > 0)))
