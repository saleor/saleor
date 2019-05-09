from sympy.core.containers import Tuple
from sympy.core.function import (Function, Lambda, nfloat)
from sympy.core.mod import Mod
from sympy.core.numbers import (E, I, Rational, oo, pi)
from sympy.core.relational import (Eq, Gt,
    Ne)
from sympy.core.singleton import S
from sympy.core.symbol import (Dummy, Symbol, symbols)
from sympy.functions.elementary.complexes import (Abs, arg, im, re, sign)
from sympy.functions.elementary.exponential import (LambertW, exp, log)
from sympy.functions.elementary.hyperbolic import (HyperbolicFunction,
    atanh, sinh, tanh)
from sympy.functions.elementary.miscellaneous import sqrt, Min, Max
from sympy.functions.elementary.piecewise import Piecewise
from sympy.functions.elementary.trigonometric import (
    TrigonometricFunction, acos, acot, acsc, asec, asin, atan, atan2,
    cos, cot, csc, sec, sin, tan)
from sympy.functions.special.error_functions import (erf, erfc,
    erfcinv, erfinv)
from sympy.logic.boolalg import And
from sympy.matrices.dense import MutableDenseMatrix as Matrix
from sympy.polys.polytools import Poly
from sympy.polys.rootoftools import CRootOf
from sympy.sets.contains import Contains
from sympy.sets.conditionset import ConditionSet
from sympy.sets.fancysets import ImageSet
from sympy.sets.sets import (Complement, EmptySet, FiniteSet,
    Intersection, Interval, Union, imageset)
from sympy.tensor.indexed import Indexed
from sympy.utilities.iterables import numbered_symbols

from sympy.utilities.pytest import XFAIL, raises, skip, slow, SKIP
from sympy.utilities.randtest import verify_numerically as tn
from sympy.physics.units import cm
from sympy.core.containers import Dict

from sympy.solvers.solveset import (
    solveset_real, domain_check, solveset_complex, linear_eq_to_matrix,
    linsolve, _is_function_class_equation, invert_real, invert_complex,
    solveset, solve_decomposition, substitution, nonlinsolve, solvify,
    _is_finite_with_finite_vars, _transolve, _is_exponential,
    _solve_exponential, _is_logarithmic,
    _solve_logarithm, _term_factors)


a = Symbol('a', real=True)
b = Symbol('b', real=True)
c = Symbol('c', real=True)
x = Symbol('x', real=True)
y = Symbol('y', real=True)
z = Symbol('z', real=True)
q = Symbol('q', real=True)
m = Symbol('m', real=True)
n = Symbol('n', real=True)


def test_invert_real():
    x = Symbol('x', real=True)
    y = Symbol('y')
    n = Symbol('n')

    def ireal(x, s=S.Reals):
        return Intersection(s, x)

    # issue 14223
    assert invert_real(x, 0, x, Interval(1, 2)) == (x, S.EmptySet)

    assert invert_real(exp(x), y, x) == (x, ireal(FiniteSet(log(y))))

    y = Symbol('y', positive=True)
    n = Symbol('n', real=True)
    assert invert_real(x + 3, y, x) == (x, FiniteSet(y - 3))
    assert invert_real(x*3, y, x) == (x, FiniteSet(y / 3))

    assert invert_real(exp(x), y, x) == (x, FiniteSet(log(y)))
    assert invert_real(exp(3*x), y, x) == (x, FiniteSet(log(y) / 3))
    assert invert_real(exp(x + 3), y, x) == (x, FiniteSet(log(y) - 3))

    assert invert_real(exp(x) + 3, y, x) == (x, ireal(FiniteSet(log(y - 3))))
    assert invert_real(exp(x)*3, y, x) == (x, FiniteSet(log(y / 3)))

    assert invert_real(log(x), y, x) == (x, FiniteSet(exp(y)))
    assert invert_real(log(3*x), y, x) == (x, FiniteSet(exp(y) / 3))
    assert invert_real(log(x + 3), y, x) == (x, FiniteSet(exp(y) - 3))

    assert invert_real(Abs(x), y, x) == (x, FiniteSet(y, -y))

    assert invert_real(2**x, y, x) == (x, FiniteSet(log(y)/log(2)))
    assert invert_real(2**exp(x), y, x) == (x, ireal(FiniteSet(log(log(y)/log(2)))))

    assert invert_real(x**2, y, x) == (x, FiniteSet(sqrt(y), -sqrt(y)))
    assert invert_real(x**Rational(1, 2), y, x) == (x, FiniteSet(y**2))

    raises(ValueError, lambda: invert_real(x, x, x))
    raises(ValueError, lambda: invert_real(x**pi, y, x))
    raises(ValueError, lambda: invert_real(S.One, y, x))

    assert invert_real(x**31 + x, y, x) == (x**31 + x, FiniteSet(y))

    lhs = x**31 + x
    conditions = Contains(y, Interval(0, oo), evaluate=False)
    base_values =  FiniteSet(y - 1, -y - 1)
    assert invert_real(Abs(x**31 + x + 1), y, x) == (lhs, base_values)

    assert invert_real(sin(x), y, x) == \
        (x, imageset(Lambda(n, n*pi + (-1)**n*asin(y)), S.Integers))

    assert invert_real(sin(exp(x)), y, x) == \
        (x, imageset(Lambda(n, log((-1)**n*asin(y) + n*pi)), S.Integers))

    assert invert_real(csc(x), y, x) == \
        (x, imageset(Lambda(n, n*pi + (-1)**n*acsc(y)), S.Integers))

    assert invert_real(csc(exp(x)), y, x) == \
        (x, imageset(Lambda(n, log((-1)**n*acsc(y) + n*pi)), S.Integers))

    assert invert_real(cos(x), y, x) == \
        (x, Union(imageset(Lambda(n, 2*n*pi + acos(y)), S.Integers), \
                imageset(Lambda(n, 2*n*pi - acos(y)), S.Integers)))

    assert invert_real(cos(exp(x)), y, x) == \
        (x, Union(imageset(Lambda(n, log(2*n*pi + Mod(acos(y), 2*pi))), S.Integers), \
                imageset(Lambda(n, log(2*n*pi + Mod(-acos(y), 2*pi))), S.Integers)))

    assert invert_real(sec(x), y, x) == \
        (x, Union(imageset(Lambda(n, 2*n*pi + asec(y)), S.Integers), \
                imageset(Lambda(n, 2*n*pi - asec(y)), S.Integers)))

    assert invert_real(sec(exp(x)), y, x) == \
        (x, Union(imageset(Lambda(n, log(2*n*pi + Mod(asec(y), 2*pi))), S.Integers), \
                imageset(Lambda(n, log(2*n*pi + Mod(-asec(y), 2*pi))), S.Integers)))

    assert invert_real(tan(x), y, x) == \
        (x, imageset(Lambda(n, n*pi + atan(y) % pi), S.Integers))

    assert invert_real(tan(exp(x)), y, x) == \
        (x, imageset(Lambda(n, log(n*pi + atan(y) % pi)), S.Integers))

    assert invert_real(cot(x), y, x) == \
        (x, imageset(Lambda(n, n*pi + acot(y) % pi), S.Integers))

    assert invert_real(cot(exp(x)), y, x) == \
        (x, imageset(Lambda(n, log(n*pi + acot(y) % pi)), S.Integers))

    assert invert_real(tan(tan(x)), y, x) == \
        (tan(x), imageset(Lambda(n, n*pi + atan(y) % pi), S.Integers))

    x = Symbol('x', positive=True)
    assert invert_real(x**pi, y, x) == (x, FiniteSet(y**(1/pi)))


def test_invert_complex():
    assert invert_complex(x + 3, y, x) == (x, FiniteSet(y - 3))
    assert invert_complex(x*3, y, x) == (x, FiniteSet(y / 3))

    assert invert_complex(exp(x), y, x) == \
        (x, imageset(Lambda(n, I*(2*pi*n + arg(y)) + log(Abs(y))), S.Integers))

    assert invert_complex(log(x), y, x) == (x, FiniteSet(exp(y)))

    raises(ValueError, lambda: invert_real(1, y, x))
    raises(ValueError, lambda: invert_complex(x, x, x))
    raises(ValueError, lambda: invert_complex(x, x, 1))

    # https://github.com/skirpichev/omg/issues/16
    assert invert_complex(sinh(x), 0, x) != (x, FiniteSet(0))


def test_domain_check():
    assert domain_check(1/(1 + (1/(x+1))**2), x, -1) is False
    assert domain_check(x**2, x, 0) is True
    assert domain_check(x, x, oo) is False
    assert domain_check(0, x, oo) is False


def test_issue_11536():
    assert solveset(0**x - 100, x, S.Reals) == S.EmptySet
    assert solveset(0**x - 1, x, S.Reals) == FiniteSet(0)


def test_is_function_class_equation():
    from sympy.abc import x, a
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x), x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x) - 1, x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x) + sin(x), x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x) + sin(x) - a, x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       sin(x)*tan(x) + sin(x), x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       sin(x)*tan(x + a) + sin(x), x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       sin(x)*tan(x*a) + sin(x), x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       a*tan(x) - 1, x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x)**2 + sin(x) - 1, x) is True
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x) + x, x) is False
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x**2), x) is False
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x**2) + sin(x), x) is False
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(x)**sin(x), x) is False
    assert _is_function_class_equation(TrigonometricFunction,
                                       tan(sin(x)) + sin(x), x) is False
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x), x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x) - 1, x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x) + sinh(x), x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x) + sinh(x) - a, x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       sinh(x)*tanh(x) + sinh(x), x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       sinh(x)*tanh(x + a) + sinh(x), x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       sinh(x)*tanh(x*a) + sinh(x), x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       a*tanh(x) - 1, x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x)**2 + sinh(x) - 1, x) is True
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x) + x, x) is False
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x**2), x) is False
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x**2) + sinh(x), x) is False
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(x)**sinh(x), x) is False
    assert _is_function_class_equation(HyperbolicFunction,
                                       tanh(sinh(x)) + sinh(x), x) is False


def test_garbage_input():
    raises(ValueError, lambda: solveset_real([x], x))
    assert solveset_real(x, 1) == S.EmptySet
    assert solveset_real(x - 1, 1) == FiniteSet(x)
    assert solveset_real(x, pi) == S.EmptySet
    assert solveset_real(x, x**2) == S.EmptySet

    raises(ValueError, lambda: solveset_complex([x], x))
    assert solveset_complex(x, pi) == S.EmptySet

    raises(ValueError, lambda: solveset((x, y), x))
    raises(ValueError, lambda: solveset(x + 1, S.Reals))
    raises(ValueError, lambda: solveset(x + 1, x, 2))


def test_solve_mul():
    assert solveset_real((a*x + b)*(exp(x) - 3), x) == \
        FiniteSet(-b/a, log(3))
    assert solveset_real((2*x + 8)*(8 + exp(x)), x) == FiniteSet(S(-4))
    assert solveset_real(x/log(x), x) == EmptySet()


def test_solve_invert():
    assert solveset_real(exp(x) - 3, x) == FiniteSet(log(3))
    assert solveset_real(log(x) - 3, x) == FiniteSet(exp(3))

    assert solveset_real(3**(x + 2), x) == FiniteSet()
    assert solveset_real(3**(2 - x), x) == FiniteSet()

    assert solveset_real(y - b*exp(a/x), x) == Intersection(
        S.Reals, FiniteSet(a/log(y/b)))

    # issue 4504
    assert solveset_real(2**x - 10, x) == FiniteSet(1 + log(5)/log(2))


def test_errorinverses():
    assert solveset_real(erf(x) - S.One/2, x) == \
        FiniteSet(erfinv(S.One/2))
    assert solveset_real(erfinv(x) - 2, x) == \
        FiniteSet(erf(2))
    assert solveset_real(erfc(x) - S.One, x) == \
        FiniteSet(erfcinv(S.One))
    assert solveset_real(erfcinv(x) - 2, x) == FiniteSet(erfc(2))


def test_solve_polynomial():
    assert solveset_real(3*x - 2, x) == FiniteSet(Rational(2, 3))

    assert solveset_real(x**2 - 1, x) == FiniteSet(-S(1), S(1))
    assert solveset_real(x - y**3, x) == FiniteSet(y ** 3)

    a11, a12, a21, a22, b1, b2 = symbols('a11, a12, a21, a22, b1, b2')

    assert solveset_real(x**3 - 15*x - 4, x) == FiniteSet(
        -2 + 3 ** Rational(1, 2),
        S(4),
        -2 - 3 ** Rational(1, 2))

    assert solveset_real(sqrt(x) - 1, x) == FiniteSet(1)
    assert solveset_real(sqrt(x) - 2, x) == FiniteSet(4)
    assert solveset_real(x**Rational(1, 4) - 2, x) == FiniteSet(16)
    assert solveset_real(x**Rational(1, 3) - 3, x) == FiniteSet(27)
    assert len(solveset_real(x**5 + x**3 + 1, x)) == 1
    assert len(solveset_real(-2*x**3 + 4*x**2 - 2*x + 6, x)) > 0

    assert solveset_real(x**6 + x**4  + I, x) == ConditionSet(x,
                                        Eq(x**6 + x**4 + I, 0), S.Reals)


def test_return_root_of():
    f = x**5 - 15*x**3 - 5*x**2 + 10*x + 20
    s = list(solveset_complex(f, x))
    for root in s:
        assert root.func == CRootOf

    # if one uses solve to get the roots of a polynomial that has a CRootOf
    # solution, make sure that the use of nfloat during the solve process
    # doesn't fail. Note: if you want numerical solutions to a polynomial
    # it is *much* faster to use nroots to get them than to solve the
    # equation only to get CRootOf solutions which are then numerically
    # evaluated. So for eq = x**5 + 3*x + 7 do Poly(eq).nroots() rather
    # than [i.n() for i in solve(eq)] to get the numerical roots of eq.
    assert nfloat(list(solveset_complex(x**5 + 3*x**3 + 7, x))[0],
                  exponent=False) == CRootOf(x**5 + 3*x**3 + 7, 0).n()

    sol = list(solveset_complex(x**6 - 2*x + 2, x))
    assert all(isinstance(i, CRootOf) for i in sol) and len(sol) == 6

    f = x**5 - 15*x**3 - 5*x**2 + 10*x + 20
    s = list(solveset_complex(f, x))
    for root in s:
        assert root.func == CRootOf

    s = x**5 + 4*x**3 + 3*x**2 + S(7)/4
    assert solveset_complex(s, x) == \
        FiniteSet(*Poly(s*4, domain='ZZ').all_roots())

    # Refer issue #7876
    eq = x*(x - 1)**2*(x + 1)*(x**6 - x + 1)
    assert solveset_complex(eq, x) == \
        FiniteSet(-1, 0, 1, CRootOf(x**6 - x + 1, 0),
                       CRootOf(x**6 - x + 1, 1),
                       CRootOf(x**6 - x + 1, 2),
                       CRootOf(x**6 - x + 1, 3),
                       CRootOf(x**6 - x + 1, 4),
                       CRootOf(x**6 - x + 1, 5))


def test__has_rational_power():
    from sympy.solvers.solveset import _has_rational_power
    assert _has_rational_power(sqrt(2), x)[0] is False
    assert _has_rational_power(x*sqrt(2), x)[0] is False

    assert _has_rational_power(x**2*sqrt(x), x) == (True, 2)
    assert _has_rational_power(sqrt(2)*x**(S(1)/3), x) == (True, 3)
    assert _has_rational_power(sqrt(x)*x**(S(1)/3), x) == (True, 6)


def test_solveset_sqrt_1():
    assert solveset_real(sqrt(5*x + 6) - 2 - x, x) == \
        FiniteSet(-S(1), S(2))
    assert solveset_real(sqrt(x - 1) - x + 7, x) == FiniteSet(10)
    assert solveset_real(sqrt(x - 2) - 5, x) == FiniteSet(27)
    assert solveset_real(sqrt(x) - 2 - 5, x) == FiniteSet(49)
    assert solveset_real(sqrt(x**3), x) == FiniteSet(0)
    assert solveset_real(sqrt(x - 1), x) == FiniteSet(1)


def test_solveset_sqrt_2():
    # http://tutorial.math.lamar.edu/Classes/Alg/SolveRadicalEqns.aspx#Solve_Rad_Ex2_a
    assert solveset_real(sqrt(2*x - 1) - sqrt(x - 4) - 2, x) == \
        FiniteSet(S(5), S(13))
    assert solveset_real(sqrt(x + 7) + 2 - sqrt(3 - x), x) == \
        FiniteSet(-6)

    # http://www.purplemath.com/modules/solverad.htm
    assert solveset_real(sqrt(17*x - sqrt(x**2 - 5)) - 7, x) == \
        FiniteSet(3)

    eq = x + 1 - (x**4 + 4*x**3 - x)**Rational(1, 4)
    assert solveset_real(eq, x) == FiniteSet(-S(1)/2, -S(1)/3)

    eq = sqrt(2*x + 9) - sqrt(x + 1) - sqrt(x + 4)
    assert solveset_real(eq, x) == FiniteSet(0)

    eq = sqrt(x + 4) + sqrt(2*x - 1) - 3*sqrt(x - 1)
    assert solveset_real(eq, x) == FiniteSet(5)

    eq = sqrt(x)*sqrt(x - 7) - 12
    assert solveset_real(eq, x) == FiniteSet(16)

    eq = sqrt(x - 3) + sqrt(x) - 3
    assert solveset_real(eq, x) == FiniteSet(4)

    eq = sqrt(2*x**2 - 7) - (3 - x)
    assert solveset_real(eq, x) == FiniteSet(-S(8), S(2))

    # others
    eq = sqrt(9*x**2 + 4) - (3*x + 2)
    assert solveset_real(eq, x) == FiniteSet(0)

    assert solveset_real(sqrt(x - 3) - sqrt(x) - 3, x) == FiniteSet()

    eq = (2*x - 5)**Rational(1, 3) - 3
    assert solveset_real(eq, x) == FiniteSet(16)

    assert solveset_real(sqrt(x) + sqrt(sqrt(x)) - 4, x) == \
        FiniteSet((-S.Half + sqrt(17)/2)**4)

    eq = sqrt(x) - sqrt(x - 1) + sqrt(sqrt(x))
    assert solveset_real(eq, x) == FiniteSet()

    eq = (sqrt(x) + sqrt(x + 1) + sqrt(1 - x) - 6*sqrt(5)/5)
    ans = solveset_real(eq, x)
    ra = S('''-1484/375 - 4*(-1/2 + sqrt(3)*I/2)*(-12459439/52734375 +
    114*sqrt(12657)/78125)**(1/3) - 172564/(140625*(-1/2 +
    sqrt(3)*I/2)*(-12459439/52734375 + 114*sqrt(12657)/78125)**(1/3))''')
    rb = S(4)/5
    assert all(abs(eq.subs(x, i).n()) < 1e-10 for i in (ra, rb)) and \
        len(ans) == 2 and \
        set([i.n(chop=True) for i in ans]) == \
        set([i.n(chop=True) for i in (ra, rb)])

    assert solveset_real(sqrt(x) + x**Rational(1, 3) +
                                 x**Rational(1, 4), x) == FiniteSet(0)

    assert solveset_real(x/sqrt(x**2 + 1), x) == FiniteSet(0)

    eq = (x - y**3)/((y**2)*sqrt(1 - y**2))
    assert solveset_real(eq, x) == FiniteSet(y**3)

    # issue 4497
    assert solveset_real(1/(5 + x)**(S(1)/5) - 9, x) == \
        FiniteSet(-295244/S(59049))


@XFAIL
def test_solve_sqrt_fail():
    # this only works if we check real_root(eq.subs(x, S(1)/3))
    # but checksol doesn't work like that
    eq = (x**3 - 3*x**2)**Rational(1, 3) + 1 - x
    assert solveset_real(eq, x) == FiniteSet(S(1)/3)


@slow
def test_solve_sqrt_3():
    R = Symbol('R')
    eq = sqrt(2)*R*sqrt(1/(R + 1)) + (R + 1)*(sqrt(2)*sqrt(1/(R + 1)) - 1)
    sol = solveset_complex(eq, R)
    fset = [S(5)/3 + 4*sqrt(10)*cos(atan(3*sqrt(111)/251)/3)/3,
            -sqrt(10)*cos(atan(3*sqrt(111)/251)/3)/3 +
            40*re(1/((-S(1)/2 - sqrt(3)*I/2)*(S(251)/27 + sqrt(111)*I/9)**(S(1)/3)))/9 +
            sqrt(30)*sin(atan(3*sqrt(111)/251)/3)/3 + S(5)/3 +
            I*(-sqrt(30)*cos(atan(3*sqrt(111)/251)/3)/3 -
               sqrt(10)*sin(atan(3*sqrt(111)/251)/3)/3 +
               40*im(1/((-S(1)/2 - sqrt(3)*I/2)*(S(251)/27 + sqrt(111)*I/9)**(S(1)/3)))/9)]
    cset = [40*re(1/((-S(1)/2 + sqrt(3)*I/2)*(S(251)/27 + sqrt(111)*I/9)**(S(1)/3)))/9 -
            sqrt(10)*cos(atan(3*sqrt(111)/251)/3)/3 - sqrt(30)*sin(atan(3*sqrt(111)/251)/3)/3 +
            S(5)/3 +
            I*(40*im(1/((-S(1)/2 + sqrt(3)*I/2)*(S(251)/27 + sqrt(111)*I/9)**(S(1)/3)))/9 -
               sqrt(10)*sin(atan(3*sqrt(111)/251)/3)/3 +
               sqrt(30)*cos(atan(3*sqrt(111)/251)/3)/3)]

    assert sol._args[0] == FiniteSet(*fset)
    assert sol._args[1] == ConditionSet(
        R,
        Eq(sqrt(2)*R*sqrt(1/(R + 1)) + (R + 1)*(sqrt(2)*sqrt(1/(R + 1)) - 1), 0),
        FiniteSet(*cset))

    # the number of real roots will depend on the value of m: for m=1 there are 4
    # and for m=-1 there are none.
    eq = -sqrt((m - q)**2 + (-m/(2*q) + S(1)/2)**2) + sqrt((-m**2/2 - sqrt(
        4*m**4 - 4*m**2 + 8*m + 1)/4 - S(1)/4)**2 + (m**2/2 - m - sqrt(
            4*m**4 - 4*m**2 + 8*m + 1)/4 - S(1)/4)**2)
    unsolved_object = ConditionSet(q, Eq(sqrt((m - q)**2 + (-m/(2*q) + S(1)/2)**2) -
        sqrt((-m**2/2 - sqrt(4*m**4 - 4*m**2 + 8*m + 1)/4 - S(1)/4)**2 + (m**2/2 - m -
        sqrt(4*m**4 - 4*m**2 + 8*m + 1)/4 - S(1)/4)**2), 0), S.Reals)
    assert solveset_real(eq, q) == unsolved_object


def test_solve_polynomial_symbolic_param():
    assert solveset_complex((x**2 - 1)**2 - a, x) == \
        FiniteSet(sqrt(1 + sqrt(a)), -sqrt(1 + sqrt(a)),
                  sqrt(1 - sqrt(a)), -sqrt(1 - sqrt(a)))

    # issue 4507
    assert solveset_complex(y - b/(1 + a*x), x) == \
        FiniteSet((b/y - 1)/a) - FiniteSet(-1/a)

    # issue 4508
    assert solveset_complex(y - b*x/(a + x), x) == \
        FiniteSet(-a*y/(y - b)) - FiniteSet(-a)


def test_solve_rational():
    assert solveset_real(1/x + 1, x) == FiniteSet(-S.One)
    assert solveset_real(1/exp(x) - 1, x) == FiniteSet(0)
    assert solveset_real(x*(1 - 5/x), x) == FiniteSet(5)
    assert solveset_real(2*x/(x + 2) - 1, x) == FiniteSet(2)
    assert solveset_real((x**2/(7 - x)).diff(x), x) == \
        FiniteSet(S(0), S(14))


def test_solveset_real_gen_is_pow():
    assert solveset_real(sqrt(1) + 1, x) == EmptySet()


def test_no_sol():
    assert solveset(1 - oo*x) == EmptySet()
    assert solveset(oo*x, x) == EmptySet()
    assert solveset(oo*x - oo, x) == EmptySet()
    assert solveset_real(4, x) == EmptySet()
    assert solveset_real(exp(x), x) == EmptySet()
    assert solveset_real(x**2 + 1, x) == EmptySet()
    assert solveset_real(-3*a/sqrt(x), x) == EmptySet()
    assert solveset_real(1/x, x) == EmptySet()
    assert solveset_real(-(1 + x)/(2 + x)**2 + 1/(2 + x), x) == \
        EmptySet()


def test_sol_zero_real():
    assert solveset_real(0, x) == S.Reals
    assert solveset(0, x, Interval(1, 2)) == Interval(1, 2)
    assert solveset_real(-x**2 - 2*x + (x + 1)**2 - 1, x) == S.Reals


def test_no_sol_rational_extragenous():
    assert solveset_real((x/(x + 1) + 3)**(-2), x) == EmptySet()
    assert solveset_real((x - 1)/(1 + 1/(x - 1)), x) == EmptySet()


def test_solve_polynomial_cv_1a():
    """
    Test for solving on equations that can be converted to
    a polynomial equation using the change of variable y -> x**Rational(p, q)
    """
    assert solveset_real(sqrt(x) - 1, x) == FiniteSet(1)
    assert solveset_real(sqrt(x) - 2, x) == FiniteSet(4)
    assert solveset_real(x**Rational(1, 4) - 2, x) == FiniteSet(16)
    assert solveset_real(x**Rational(1, 3) - 3, x) == FiniteSet(27)
    assert solveset_real(x*(x**(S(1) / 3) - 3), x) == \
        FiniteSet(S(0), S(27))


def test_solveset_real_rational():
    """Test solveset_real for rational functions"""
    assert solveset_real((x - y**3) / ((y**2)*sqrt(1 - y**2)), x) \
        == FiniteSet(y**3)
    # issue 4486
    assert solveset_real(2*x/(x + 2) - 1, x) == FiniteSet(2)


def test_solveset_real_log():
    assert solveset_real(log((x-1)*(x+1)), x) == \
        FiniteSet(sqrt(2), -sqrt(2))


def test_poly_gens():
    assert solveset_real(4**(2*(x**2) + 2*x) - 8, x) == \
        FiniteSet(-Rational(3, 2), S.Half)


def test_solve_abs():
    x = Symbol('x')
    n = Dummy('n')
    raises(ValueError, lambda: solveset(Abs(x) - 1, x))
    assert solveset(Abs(x) - n, x, S.Reals) == ConditionSet(x, Contains(n, Interval(0, oo)), {-n, n})
    assert solveset_real(Abs(x) - 2, x) == FiniteSet(-2, 2)
    assert solveset_real(Abs(x) + 2, x) is S.EmptySet
    assert solveset_real(Abs(x + 3) - 2*Abs(x - 3), x) == \
        FiniteSet(1, 9)
    assert solveset_real(2*Abs(x) - Abs(x - 1), x) == \
        FiniteSet(-1, Rational(1, 3))

    sol = ConditionSet(
            x,
            And(
                Contains(b, Interval(0, oo)),
                Contains(a + b, Interval(0, oo)),
                Contains(a - b, Interval(0, oo))),
            FiniteSet(-a - b - 3, -a + b - 3, a - b - 3, a + b - 3))
    eq = Abs(Abs(x + 3) - a) - b
    assert invert_real(eq, 0, x)[1] == sol
    reps = {a: 3, b: 1}
    eqab = eq.subs(reps)
    for i in sol.subs(reps):
        assert not eqab.subs(x, i)
    assert solveset(Eq(sin(Abs(x)), 1), x, domain=S.Reals) == Union(
        Intersection(Interval(0, oo),
            ImageSet(Lambda(n, (-1)**n*pi/2 + n*pi), S.Integers)),
        Intersection(Interval(-oo, 0),
            ImageSet(Lambda(n, n*pi - (-1)**(-n)*pi/2), S.Integers)))



def test_issue_9565():
    assert solveset_real(Abs((x - 1)/(x - 5)) <= S(1)/3, x) == Interval(-1, 2)


def test_issue_10069():
    eq = abs(1/(x - 1)) - 1 > 0
    u = Union(Interval.open(0, 1), Interval.open(1, 2))
    assert solveset_real(eq, x) == u


@XFAIL
def test_rewrite_trigh():
    # if this import passes then the test below should also pass
    from sympy import sech
    assert solveset_real(sinh(x) + sech(x), x) == FiniteSet(
        2*atanh(-S.Half + sqrt(5)/2 - sqrt(-2*sqrt(5) + 2)/2),
        2*atanh(-S.Half + sqrt(5)/2 + sqrt(-2*sqrt(5) + 2)/2),
        2*atanh(-sqrt(5)/2 - S.Half + sqrt(2 + 2*sqrt(5))/2),
        2*atanh(-sqrt(2 + 2*sqrt(5))/2 - sqrt(5)/2 - S.Half))


def test_real_imag_splitting():
    a, b = symbols('a b', real=True, finite=True)
    assert solveset_real(sqrt(a**2 - b**2) - 3, a) == \
        FiniteSet(-sqrt(b**2 + 9), sqrt(b**2 + 9))
    assert solveset_real(sqrt(a**2 + b**2) - 3, a) != \
        S.EmptySet


def test_units():
    assert solveset_real(1/x - 1/(2*cm), x) == FiniteSet(2*cm)


def test_solve_only_exp_1():
    y = Symbol('y', positive=True, finite=True)
    assert solveset_real(exp(x) - y, x) == FiniteSet(log(y))
    assert solveset_real(exp(x) + exp(-x) - 4, x) == \
        FiniteSet(log(-sqrt(3) + 2), log(sqrt(3) + 2))
    assert solveset_real(exp(x) + exp(-x) - y, x) != S.EmptySet


def test_atan2():
    # The .inverse() method on atan2 works only if x.is_real is True and the
    # second argument is a real constant
    assert solveset_real(atan2(x, 2) - pi/3, x) == FiniteSet(2*sqrt(3))


def test_piecewise_solveset():
    eq = Piecewise((x - 2, Gt(x, 2)), (2 - x, True)) - 3
    assert set(solveset_real(eq, x)) == set(FiniteSet(-1, 5))

    absxm3 = Piecewise(
        (x - 3, S(0) <= x - 3),
        (3 - x, S(0) > x - 3))
    y = Symbol('y', positive=True)
    assert solveset_real(absxm3 - y, x) == FiniteSet(-y + 3, y + 3)

    f = Piecewise(((x - 2)**2, x >= 0), (0, True))
    assert solveset(f, x, domain=S.Reals) == Union(FiniteSet(2), Interval(-oo, 0, True, True))

    assert solveset(
        Piecewise((x + 1, x > 0), (I, True)) - I, x, S.Reals
        ) == Interval(-oo, 0)

    assert solveset(Piecewise((x - 1, Ne(x, I)), (x, True)), x) == FiniteSet(1)


def test_solveset_complex_polynomial():
    from sympy.abc import x, a, b, c
    assert solveset_complex(a*x**2 + b*x + c, x) == \
        FiniteSet(-b/(2*a) - sqrt(-4*a*c + b**2)/(2*a),
                  -b/(2*a) + sqrt(-4*a*c + b**2)/(2*a))

    assert solveset_complex(x - y**3, y) == FiniteSet(
        (-x**Rational(1, 3))/2 + I*sqrt(3)*x**Rational(1, 3)/2,
        x**Rational(1, 3),
        (-x**Rational(1, 3))/2 - I*sqrt(3)*x**Rational(1, 3)/2)

    assert solveset_complex(x + 1/x - 1, x) == \
        FiniteSet(Rational(1, 2) + I*sqrt(3)/2, Rational(1, 2) - I*sqrt(3)/2)


def test_sol_zero_complex():
    assert solveset_complex(0, x) == S.Complexes


def test_solveset_complex_rational():
    assert solveset_complex((x - 1)*(x - I)/(x - 3), x) == \
        FiniteSet(1, I)

    assert solveset_complex((x - y**3)/((y**2)*sqrt(1 - y**2)), x) == \
        FiniteSet(y**3)
    assert solveset_complex(-x**2 - I, x) == \
        FiniteSet(-sqrt(2)/2 + sqrt(2)*I/2, sqrt(2)/2 - sqrt(2)*I/2)


def test_solve_quintics():
    skip("This test is too slow")
    f = x**5 - 110*x**3 - 55*x**2 + 2310*x + 979
    s = solveset_complex(f, x)
    for root in s:
        res = f.subs(x, root.n()).n()
        assert tn(res, 0)

    f = x**5 + 15*x + 12
    s = solveset_complex(f, x)
    for root in s:
        res = f.subs(x, root.n()).n()
        assert tn(res, 0)


def test_solveset_complex_exp():
    from sympy.abc import x, n
    assert solveset_complex(exp(x) - 1, x) == \
        imageset(Lambda(n, I*2*n*pi), S.Integers)
    assert solveset_complex(exp(x) - I, x) == \
        imageset(Lambda(n, I*(2*n*pi + pi/2)), S.Integers)
    assert solveset_complex(1/exp(x), x) == S.EmptySet
    assert solveset_complex(sinh(x).rewrite(exp), x) == \
        imageset(Lambda(n, n*pi*I), S.Integers)


def test_solveset_real_exp():
    from sympy.abc import x, y
    assert solveset(Eq((-2)**x, 4), x, S.Reals) == FiniteSet(2)
    assert solveset(Eq(-2**x, 4), x, S.Reals) == S.EmptySet
    assert solveset(Eq((-3)**x, 27), x, S.Reals) == S.EmptySet
    assert solveset(Eq((-5)**(x+1), 625), x, S.Reals) == FiniteSet(3)
    assert solveset(Eq(2**(x-3), -16), x, S.Reals) == S.EmptySet
    assert solveset(Eq((-3)**(x - 3), -3**39), x, S.Reals) == FiniteSet(42)
    assert solveset(Eq(2**x, y), x, S.Reals) == Intersection(S.Reals, FiniteSet(log(y)/log(2)))

    assert invert_real((-2)**(2*x) - 16, 0, x) == (x, FiniteSet(2))


def test_solve_complex_log():
    assert solveset_complex(log(x), x) == FiniteSet(1)
    assert solveset_complex(1 - log(a + 4*x**2), x) == \
        FiniteSet(-sqrt(-a + E)/2, sqrt(-a + E)/2)


def test_solve_complex_sqrt():
    assert solveset_complex(sqrt(5*x + 6) - 2 - x, x) == \
        FiniteSet(-S(1), S(2))
    assert solveset_complex(sqrt(5*x + 6) - (2 + 2*I) - x, x) == \
        FiniteSet(-S(2), 3 - 4*I)
    assert solveset_complex(4*x*(1 - a * sqrt(x)), x) == \
        FiniteSet(S(0), 1 / a ** 2)


def test_solveset_complex_tan():
    s = solveset_complex(tan(x).rewrite(exp), x)
    assert s == imageset(Lambda(n, pi*n), S.Integers) - \
        imageset(Lambda(n, pi*n + pi/2), S.Integers)


def test_solve_trig():
    from sympy.abc import n
    assert solveset_real(sin(x), x) == \
        Union(imageset(Lambda(n, 2*pi*n), S.Integers),
              imageset(Lambda(n, 2*pi*n + pi), S.Integers))

    assert solveset_real(sin(x) - 1, x) == \
        imageset(Lambda(n, 2*pi*n + pi/2), S.Integers)

    assert solveset_real(cos(x), x) == \
        Union(imageset(Lambda(n, 2*pi*n + pi/2), S.Integers),
              imageset(Lambda(n, 2*pi*n + 3*pi/2), S.Integers))

    assert solveset_real(sin(x) + cos(x), x) == \
        Union(imageset(Lambda(n, 2*n*pi + 3*pi/4), S.Integers),
              imageset(Lambda(n, 2*n*pi + 7*pi/4), S.Integers))

    assert solveset_real(sin(x)**2 + cos(x)**2, x) == S.EmptySet

    assert solveset_complex(cos(x) - S.Half, x) == \
        Union(imageset(Lambda(n, 2*n*pi + 5*pi/3), S.Integers),
              imageset(Lambda(n, 2*n*pi + pi/3), S.Integers))

    y, a = symbols('y,a')
    assert solveset(sin(y + a) - sin(y), a, domain=S.Reals) == \
        imageset(Lambda(n, 2*n*pi), S.Integers)

    assert solveset_real(sin(2*x)*cos(x) + cos(2*x)*sin(x)-1, x) == \
                            ImageSet(Lambda(n, 2*n*pi/3 + pi/6), S.Integers)

    # Tests for _solve_trig2() function
    assert solveset_real(2*cos(x)*cos(2*x) - 1, x) == \
          Union(ImageSet(Lambda(n, 2*n*pi + 2*atan(sqrt(-2*2**(S(1)/3)*(67 +
                  9*sqrt(57))**(S(2)/3) + 8*2**(S(2)/3) + 11*(67 +
                  9*sqrt(57))**(S(1)/3))/(3*(67 + 9*sqrt(57))**(S(1)/6)))), S.Integers),
                  ImageSet(Lambda(n, 2*n*pi - 2*atan(sqrt(-2*2**(S(1)/3)*(67 +
                  9*sqrt(57))**(S(2)/3) + 8*2**(S(2)/3) + 11*(67 +
                  9*sqrt(57))**(S(1)/3))/(3*(67 + 9*sqrt(57))**(S(1)/6))) +
                  2*pi), S.Integers))

    assert solveset_real(2*tan(x)*sin(x) + 1, x) == Union(
        ImageSet(Lambda(n, 2*n*pi + atan(sqrt(2)*sqrt(-1 + sqrt(17))/
            (-sqrt(17) + 1)) + pi), S.Integers),
        ImageSet(Lambda(n, 2*n*pi - atan(sqrt(2)*sqrt(-1 + sqrt(17))/
            (-sqrt(17) + 1)) + pi), S.Integers))

    assert solveset_real(cos(2*x)*cos(4*x) - 1, x) == \
                            ImageSet(Lambda(n, n*pi), S.Integers)


def test_solve_invalid_sol():
    assert 0 not in solveset_real(sin(x)/x, x)
    assert 0 not in solveset_complex((exp(x) - 1)/x, x)


@XFAIL
def test_solve_trig_simplified():
    from sympy.abc import n
    assert solveset_real(sin(x), x) == \
        imageset(Lambda(n, n*pi), S.Integers)

    assert solveset_real(cos(x), x) == \
        imageset(Lambda(n, n*pi + pi/2), S.Integers)

    assert solveset_real(cos(x) + sin(x), x) == \
        imageset(Lambda(n, n*pi - pi/4), S.Integers)


@XFAIL
def test_solve_lambert():
    assert solveset_real(x*exp(x) - 1, x) == FiniteSet(LambertW(1))
    assert solveset_real(exp(x) + x, x) == FiniteSet(-LambertW(1))
    assert solveset_real(x + 2**x, x) == \
        FiniteSet(-LambertW(log(2))/log(2))

    # issue 4739
    ans = solveset_real(3*x + 5 + 2**(-5*x + 3), x)
    assert ans == FiniteSet(-Rational(5, 3) +
                            LambertW(-10240*2**(S(1)/3)*log(2)/3)/(5*log(2)))

    eq = 2*(3*x + 4)**5 - 6*7**(3*x + 9)
    result = solveset_real(eq, x)
    ans = FiniteSet((log(2401) +
                     5*LambertW(-log(7**(7*3**Rational(1, 5)/5))))/(3*log(7))/-1)
    assert result == ans
    assert solveset_real(eq.expand(), x) == result

    assert solveset_real(5*x - 1 + 3*exp(2 - 7*x), x) == \
        FiniteSet(Rational(1, 5) + LambertW(-21*exp(Rational(3, 5))/5)/7)

    assert solveset_real(2*x + 5 + log(3*x - 2), x) == \
        FiniteSet(Rational(2, 3) + LambertW(2*exp(-Rational(19, 3))/3)/2)

    assert solveset_real(3*x + log(4*x), x) == \
        FiniteSet(LambertW(Rational(3, 4))/3)

    assert solveset_real(x**x - 2) == FiniteSet(exp(LambertW(log(2))))

    a = Symbol('a')
    assert solveset_real(-a*x + 2*x*log(x), x) == FiniteSet(exp(a/2))
    a = Symbol('a', real=True)
    assert solveset_real(a/x + exp(x/2), x) == \
        FiniteSet(2*LambertW(-a/2))
    assert solveset_real((a/x + exp(x/2)).diff(x), x) == \
        FiniteSet(4*LambertW(sqrt(2)*sqrt(a)/4))

    # coverage test
    assert solveset_real(tanh(x + 3)*tanh(x - 3) - 1, x) == EmptySet()

    assert solveset_real((x**2 - 2*x + 1).subs(x, log(x) + 3*x), x) == \
        FiniteSet(LambertW(3*S.Exp1)/3)
    assert solveset_real((x**2 - 2*x + 1).subs(x, (log(x) + 3*x)**2 - 1), x) == \
        FiniteSet(LambertW(3*exp(-sqrt(2)))/3, LambertW(3*exp(sqrt(2)))/3)
    assert solveset_real((x**2 - 2*x - 2).subs(x, log(x) + 3*x), x) == \
        FiniteSet(LambertW(3*exp(1 + sqrt(3)))/3, LambertW(3*exp(-sqrt(3) + 1))/3)
    assert solveset_real(x*log(x) + 3*x + 1, x) == \
        FiniteSet(exp(-3 + LambertW(-exp(3))))
    eq = (x*exp(x) - 3).subs(x, x*exp(x))
    assert solveset_real(eq, x) == \
        FiniteSet(LambertW(3*exp(-LambertW(3))))

    assert solveset_real(3*log(a**(3*x + 5)) + a**(3*x + 5), x) == \
        FiniteSet(-((log(a**5) + LambertW(S(1)/3))/(3*log(a))))
    p = symbols('p', positive=True)
    assert solveset_real(3*log(p**(3*x + 5)) + p**(3*x + 5), x) == \
        FiniteSet(
        log((-3**(S(1)/3) - 3**(S(5)/6)*I)*LambertW(S(1)/3)**(S(1)/3)/(2*p**(S(5)/3)))/log(p),
        log((-3**(S(1)/3) + 3**(S(5)/6)*I)*LambertW(S(1)/3)**(S(1)/3)/(2*p**(S(5)/3)))/log(p),
        log((3*LambertW(S(1)/3)/p**5)**(1/(3*log(p)))),)  # checked numerically
    # check collection
    b = Symbol('b')
    eq = 3*log(a**(3*x + 5)) + b*log(a**(3*x + 5)) + a**(3*x + 5)
    assert solveset_real(eq, x) == FiniteSet(
        -((log(a**5) + LambertW(1/(b + 3)))/(3*log(a))))

    # issue 4271
    assert solveset_real((a/x + exp(x/2)).diff(x, 2), x) == FiniteSet(
        6*LambertW((-1)**(S(1)/3)*a**(S(1)/3)/3))

    assert solveset_real(x**3 - 3**x, x) == \
        FiniteSet(-3/log(3)*LambertW(-log(3)/3))
    assert solveset_real(3**cos(x) - cos(x)**3) == FiniteSet(
        acos(-3*LambertW(-log(3)/3)/log(3)))

    assert solveset_real(x**2 - 2**x, x) == \
        solveset_real(-x**2 + 2**x, x)

    assert solveset_real(3*log(x) - x*log(3)) == FiniteSet(
        -3*LambertW(-log(3)/3)/log(3),
        -3*LambertW(-log(3)/3, -1)/log(3))

    assert solveset_real(LambertW(2*x) - y) == FiniteSet(
        y*exp(y)/2)


@XFAIL
def test_other_lambert():
    a = S(6)/5
    assert solveset_real(x**a - a**x, x) == FiniteSet(
        a, -a*LambertW(-log(a)/a)/log(a))


def test_solveset():
    x = Symbol('x')
    f = Function('f')
    raises(ValueError, lambda: solveset(x + y))
    assert solveset(x, 1) == S.EmptySet
    assert solveset(f(1)**2 + y + 1, f(1)
        ) == FiniteSet(-sqrt(-y - 1), sqrt(-y - 1))
    assert solveset(f(1)**2 - 1, f(1), S.Reals) == FiniteSet(-1, 1)
    assert solveset(f(1)**2 + 1, f(1)) == FiniteSet(-I, I)
    assert solveset(x - 1, 1) == FiniteSet(x)
    assert solveset(sin(x) - cos(x), sin(x)) == FiniteSet(cos(x))

    assert solveset(0, domain=S.Reals) == S.Reals
    assert solveset(1) == S.EmptySet
    assert solveset(True, domain=S.Reals) == S.Reals  # issue 10197
    assert solveset(False, domain=S.Reals) == S.EmptySet

    assert solveset(exp(x) - 1, domain=S.Reals) == FiniteSet(0)
    assert solveset(exp(x) - 1, x, S.Reals) == FiniteSet(0)
    assert solveset(Eq(exp(x), 1), x, S.Reals) == FiniteSet(0)
    assert solveset(exp(x) - 1, exp(x), S.Reals) == FiniteSet(1)
    A = Indexed('A', x)
    assert solveset(A - 1, A, S.Reals) == FiniteSet(1)

    assert solveset(x - 1 >= 0, x, S.Reals) == Interval(1, oo)
    assert solveset(exp(x) - 1 >= 0, x, S.Reals) == Interval(0, oo)

    assert solveset(exp(x) - 1, x) == imageset(Lambda(n, 2*I*pi*n), S.Integers)
    assert solveset(Eq(exp(x), 1), x) == imageset(Lambda(n, 2*I*pi*n),
                                                  S.Integers)
    # issue 13825
    assert solveset(x**2 + f(0) + 1, x) == {-sqrt(-f(0) - 1), sqrt(-f(0) - 1)}


def test_conditionset():
    assert solveset(Eq(sin(x)**2 + cos(x)**2, 1), x, domain=S.Reals) == \
        ConditionSet(x, True, S.Reals)

    assert solveset(Eq(x**2 + x*sin(x), 1), x, domain=S.Reals
        ) == ConditionSet(x, Eq(x**2 + x*sin(x) - 1, 0), S.Reals)

    assert solveset(Eq(-I*(exp(I*x) - exp(-I*x))/2, 1), x
        ) == imageset(Lambda(n, 2*n*pi + pi/2), S.Integers)

    assert solveset(x + sin(x) > 1, x, domain=S.Reals
        ) == ConditionSet(x, x + sin(x) > 1, S.Reals)

    assert solveset(Eq(sin(Abs(x)), x), x, domain=S.Reals
        ) == ConditionSet(x, Eq(-x + sin(Abs(x)), 0), S.Reals)

    assert solveset(y**x-z, x, S.Reals) == \
        ConditionSet(x, Eq(y**x - z, 0), S.Reals)


@XFAIL
def test_conditionset_equality():
    ''' Checking equality of different representations of ConditionSet'''
    assert solveset(Eq(tan(x), y), x) == ConditionSet(x, Eq(tan(x), y), S.Complexes)


def test_solveset_domain():
    x = Symbol('x')

    assert solveset(x**2 - x - 6, x, Interval(0, oo)) == FiniteSet(3)
    assert solveset(x**2 - 1, x, Interval(0, oo)) == FiniteSet(1)
    assert solveset(x**4 - 16, x, Interval(0, 10)) == FiniteSet(2)


def test_improve_coverage():
    from sympy.solvers.solveset import _has_rational_power
    x = Symbol('x')
    solution = solveset(exp(x) + sin(x), x, S.Reals)
    unsolved_object = ConditionSet(x, Eq(exp(x) + sin(x), 0), S.Reals)
    assert solution == unsolved_object

    assert _has_rational_power(sin(x)*exp(x) + 1, x) == (False, S.One)
    assert _has_rational_power((sin(x)**2)*(exp(x) + 1)**3, x) == (False, S.One)


def test_issue_9522():
    x = Symbol('x')
    expr1 = Eq(1/(x**2 - 4) + x, 1/(x**2 - 4) + 2)
    expr2 = Eq(1/x + x, 1/x)

    assert solveset(expr1, x, S.Reals) == EmptySet()
    assert solveset(expr2, x, S.Reals) == EmptySet()


def test_solvify():
    x = Symbol('x')

    assert solvify(x**2 + 10, x, S.Reals) == []
    assert solvify(x**3 + 1, x, S.Complexes) == [-1, S(1)/2 - sqrt(3)*I/2,
                                                 S(1)/2 + sqrt(3)*I/2]
    assert solvify(log(x), x, S.Reals) == [1]
    assert solvify(cos(x), x, S.Reals) == [pi/2, 3*pi/2]
    assert solvify(sin(x) + 1, x, S.Reals) == [3*pi/2]
    raises(NotImplementedError, lambda: solvify(sin(exp(x)), x, S.Complexes))


def test_abs_invert_solvify():
    assert solvify(sin(Abs(x)), x, S.Reals) is None


def test_linear_eq_to_matrix():
    x, y, z = symbols('x, y, z')
    a, b, c, d, e, f, g, h, i, j, k, l = symbols('a:l')

    eqns1 = [2*x + y - 2*z - 3, x - y - z, x + y + 3*z - 12]
    eqns2 = [Eq(3*x + 2*y - z, 1), Eq(2*x - 2*y + 4*z, -2), -2*x + y - 2*z]

    A, B = linear_eq_to_matrix(eqns1, x, y, z)
    assert A == Matrix([[2, 1, -2], [1, -1, -1], [1, 1, 3]])
    assert B == Matrix([[3], [0], [12]])

    A, B = linear_eq_to_matrix(eqns2, x, y, z)
    assert A == Matrix([[3, 2, -1], [2, -2, 4], [-2, 1, -2]])
    assert B == Matrix([[1], [-2], [0]])

    # Pure symbolic coefficients
    eqns3 = [a*b*x + b*y + c*z - d, e*x + d*x + f*y + g*z - h, i*x + j*y + k*z - l]
    A, B = linear_eq_to_matrix(eqns3, x, y, z)
    assert A == Matrix([[a*b, b, c], [d + e, f, g], [i, j, k]])
    assert B == Matrix([[d], [h], [l]])

    # raise ValueError if
    # 1) no symbols are given
    raises(ValueError, lambda: linear_eq_to_matrix(eqns3))
    # 2) there are duplicates
    raises(ValueError, lambda: linear_eq_to_matrix(eqns3, [x, x, y]))
    # 3) there are non-symbols
    raises(ValueError, lambda: linear_eq_to_matrix(eqns3, [x, 1/a, y]))
    # 4) a nonlinear term is detected in the original expression
    raises(ValueError, lambda: linear_eq_to_matrix(Eq(1/x + x, 1/x)))

    assert linear_eq_to_matrix(1, x) == (Matrix([[0]]), Matrix([[-1]]))
    # issue 15195
    assert linear_eq_to_matrix(x + y*(z*(3*x + 2) + 3), x) == (
        Matrix([[3*y*z + 1]]), Matrix([[-y*(2*z + 3)]]))
    assert linear_eq_to_matrix(Matrix(
        [[a*x + b*y - 7], [5*x + 6*y - c]]), x, y) == (
        Matrix([[a, b], [5, 6]]), Matrix([[7], [c]]))

    # issue 15312
    assert linear_eq_to_matrix(Eq(x + 2, 1), x) == (
        Matrix([[1]]), Matrix([[-1]]))


def test_issue_16577():
    assert linear_eq_to_matrix(Eq(a*(2*x + 3*y) + 4*y, 5), x, y) == (
        Matrix([[2*a, 3*a + 4]]), Matrix([[5]]))


def test_linsolve():
    x, y, z, u, v, w = symbols("x, y, z, u, v, w")
    x1, x2, x3, x4 = symbols('x1, x2, x3, x4')

    # Test for different input forms

    M = Matrix([[1, 2, 1, 1, 7], [1, 2, 2, -1, 12], [2, 4, 0, 6, 4]])
    system1 = A, b = M[:, :-1], M[:, -1]
    Eqns = [x1 + 2*x2 + x3 + x4 - 7, x1 + 2*x2 + 2*x3 - x4 - 12,
            2*x1 + 4*x2 + 6*x4 - 4]

    sol = FiniteSet((-2*x2 - 3*x4 + 2, x2, 2*x4 + 5, x4))
    assert linsolve(Eqns, (x1, x2, x3, x4)) == sol
    assert linsolve(Eqns, *(x1, x2, x3, x4)) == sol
    assert linsolve(system1, (x1, x2, x3, x4)) == sol
    assert linsolve(system1, *(x1, x2, x3, x4)) == sol
    # issue 9667 - symbols can be Dummy symbols
    x1, x2, x3, x4 = symbols('x:4', cls=Dummy)
    assert linsolve(system1, x1, x2, x3, x4) == FiniteSet(
        (-2*x2 - 3*x4 + 2, x2, 2*x4 + 5, x4))

    # raise ValueError for garbage value
    raises(ValueError, lambda: linsolve(Eqns))
    raises(ValueError, lambda: linsolve(x1))
    raises(ValueError, lambda: linsolve(x1, x2))
    raises(ValueError, lambda: linsolve((A,), x1, x2))
    raises(ValueError, lambda: linsolve(A, b, x1, x2))

    #raise ValueError if equations are non-linear in given variables
    raises(ValueError, lambda: linsolve([x + y - 1, x ** 2 + y - 3], [x, y]))
    raises(ValueError, lambda: linsolve([cos(x) + y, x + y], [x, y]))
    assert linsolve([x + z - 1, x ** 2 + y - 3], [z, y]) == {(-x + 1, -x**2 + 3)}

    # Fully symbolic test
    a, b, c, d, e, f = symbols('a, b, c, d, e, f')
    A = Matrix([[a, b], [c, d]])
    B = Matrix([[e], [f]])
    system2 = (A, B)
    sol = FiniteSet(((-b*f + d*e)/(a*d - b*c), (a*f - c*e)/(a*d - b*c)))
    assert linsolve(system2, [x, y]) == sol

    # No solution
    A = Matrix([[1, 2, 3], [2, 4, 6], [3, 6, 9]])
    b = Matrix([0, 0, 1])
    assert linsolve((A, b), (x, y, z)) == EmptySet()

    # Issue #10056
    A, B, J1, J2 = symbols('A B J1 J2')
    Augmatrix = Matrix([
        [2*I*J1, 2*I*J2, -2/J1],
        [-2*I*J2, -2*I*J1, 2/J2],
        [0, 2, 2*I/(J1*J2)],
        [2, 0,  0],
        ])

    assert linsolve(Augmatrix, A, B) == FiniteSet((0, I/(J1*J2)))

    # Issue #10121 - Assignment of free variables
    a, b, c, d, e = symbols('a, b, c, d, e')
    Augmatrix = Matrix([[0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0]])
    assert linsolve(Augmatrix, a, b, c, d, e) == FiniteSet((a, 0, c, 0, e))
    raises(IndexError, lambda: linsolve(Augmatrix, a, b, c))

    x0, x1, x2, _x0 = symbols('tau0 tau1 tau2 _tau0')
    assert linsolve(Matrix([[0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, _x0]])
        ) == FiniteSet((x0, 0, x1, _x0, x2))
    x0, x1, x2, _x0 = symbols('_tau0 _tau1 _tau2 tau0')
    assert linsolve(Matrix([[0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, _x0]])
        ) == FiniteSet((x0, 0, x1, _x0, x2))
    x0, x1, x2, _x0 = symbols('_tau0 _tau1 _tau2 tau1')
    assert linsolve(Matrix([[0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, _x0]])
        ) == FiniteSet((x0, 0, x1, _x0, x2))
    # symbols can be given as generators
    x0, x2, x4 = symbols('x0, x2, x4')
    assert linsolve(Augmatrix, numbered_symbols('x')
        ) == FiniteSet((x0, 0, x2, 0, x4))
    Augmatrix[-1, -1] = x0
    # use Dummy to avoid clash; the names may clash but the symbols
    # will not
    Augmatrix[-1, -1] = symbols('_x0')
    assert len(linsolve(
        Augmatrix, numbered_symbols('x', cls=Dummy)).free_symbols) == 4

    # Issue #12604
    f = Function('f')
    assert linsolve([f(x) - 5], f(x)) == FiniteSet((5,))

    # Issue #14860
    from sympy.physics.units import meter, newton, kilo
    Eqns = [8*kilo*newton + x + y, 28*kilo*newton*meter + 3*x*meter]
    assert linsolve(Eqns, x, y) == {(-28000*newton/3, 4000*newton/3)}

    # linsolve fully expands expressions, so removable singularities
    # and other nonlinearity does not raise an error
    assert linsolve([Eq(x, x + y)], [x, y]) == {(x, 0)}
    assert linsolve([Eq(1/x, 1/x + y)], [x, y]) == {(x, 0)}
    assert linsolve([Eq(y/x, y/x + y)], [x, y]) == {(x, 0)}
    assert linsolve([Eq(x*(x + 1), x**2 + y)], [x, y]) == {(y, y)}


def test_solve_decomposition():
    x = Symbol('x')
    n = Dummy('n')

    f1 = exp(3*x) - 6*exp(2*x) + 11*exp(x) - 6
    f2 = sin(x)**2 - 2*sin(x) + 1
    f3 = sin(x)**2 - sin(x)
    f4 = sin(x + 1)
    f5 = exp(x + 2) - 1
    f6 = 1/log(x)
    f7 = 1/x

    s1 = ImageSet(Lambda(n, 2*n*pi), S.Integers)
    s2 = ImageSet(Lambda(n, 2*n*pi + pi), S.Integers)
    s3 = ImageSet(Lambda(n, 2*n*pi + pi/2), S.Integers)
    s4 = ImageSet(Lambda(n, 2*n*pi - 1), S.Integers)
    s5 = ImageSet(Lambda(n, 2*n*pi - 1 + pi), S.Integers)

    assert solve_decomposition(f1, x, S.Reals) == FiniteSet(0, log(2), log(3))
    assert solve_decomposition(f2, x, S.Reals) == s3
    assert solve_decomposition(f3, x, S.Reals) == Union(s1, s2, s3)
    assert solve_decomposition(f4, x, S.Reals) == Union(s4, s5)
    assert solve_decomposition(f5, x, S.Reals) == FiniteSet(-2)
    assert solve_decomposition(f6, x, S.Reals) == S.EmptySet
    assert solve_decomposition(f7, x, S.Reals) == S.EmptySet
    assert solve_decomposition(x, x, Interval(1, 2)) == S.EmptySet

# nonlinsolve testcases
def test_nonlinsolve_basic():
    assert nonlinsolve([],[]) == S.EmptySet
    assert nonlinsolve([],[x, y]) == S.EmptySet

    system = [x, y - x - 5]
    assert nonlinsolve([x],[x, y]) == FiniteSet((0, y))
    assert nonlinsolve(system, [y]) == FiniteSet((x + 5,))
    soln = (ImageSet(Lambda(n, 2*n*pi + pi/2), S.Integers),)
    assert nonlinsolve([sin(x) - 1], [x]) == FiniteSet(tuple(soln))
    assert nonlinsolve([x**2 - 1], [x]) == FiniteSet((-1,), (1,))

    soln = FiniteSet((y, y))
    assert nonlinsolve([x - y, 0], x, y) == soln
    assert nonlinsolve([0, x - y], x, y) == soln
    assert nonlinsolve([x - y, x - y], x, y) == soln
    assert nonlinsolve([x, 0], x, y) == FiniteSet((0, y))
    f = Function('f')
    assert nonlinsolve([f(x), 0], f(x), y) == FiniteSet((0, y))
    assert nonlinsolve([f(x), 0], f(x), f(y)) == FiniteSet((0, f(y)))
    A = Indexed('A', x)
    assert nonlinsolve([A, 0], A, y) == FiniteSet((0, y))
    assert nonlinsolve([x**2 -1], [sin(x)]) == FiniteSet((S.EmptySet,))
    assert nonlinsolve([x**2 -1], sin(x)) == FiniteSet((S.EmptySet,))
    assert nonlinsolve([x**2 -1], 1) == FiniteSet((x**2,))
    assert nonlinsolve([x**2 -1], x + y) == FiniteSet((S.EmptySet,))


def test_nonlinsolve_abs():
    soln = FiniteSet((x, Abs(x)))
    assert nonlinsolve([Abs(x) - y], x, y) == soln


def test_raise_exception_nonlinsolve():
    raises(IndexError, lambda: nonlinsolve([x**2 -1], []))
    raises(ValueError, lambda: nonlinsolve([x**2 -1]))
    raises(NotImplementedError, lambda: nonlinsolve([(x+y)**2 - 9, x**2 - y**2 - 0.75], (x, y)))


def test_trig_system():
    # TODO: add more simple testcases when solveset returns
    # simplified soln for Trig eq
    assert nonlinsolve([sin(x) - 1, cos(x) -1 ], x) == S.EmptySet
    soln1 = (ImageSet(Lambda(n, 2*n*pi + pi/2), S.Integers),)
    soln = FiniteSet(soln1)
    assert nonlinsolve([sin(x) - 1, cos(x)], x) == soln


@XFAIL
def test_trig_system_fail():
    # fails because solveset trig solver is not much smart.
    sys = [x + y - pi/2, sin(x) + sin(y) - 1]
    # solveset returns conditonset for sin(x) + sin(y) - 1
    soln_1 = (ImageSet(Lambda(n, n*pi + pi/2), S.Integers),
        ImageSet(Lambda(n, n*pi)), S.Integers)
    soln_1 = FiniteSet(soln_1)
    soln_2 = (ImageSet(Lambda(n, n*pi), S.Integers),
        ImageSet(Lambda(n, n*pi+ pi/2), S.Integers))
    soln_2 = FiniteSet(soln_2)
    soln = soln_1 + soln_2
    assert nonlinsolve(sys, [x, y]) == soln

    # Add more cases from here
    # http://www.vitutor.com/geometry/trigonometry/equations_systems.html#uno
    sys = [sin(x) + sin(y) - (sqrt(3)+1)/2, sin(x) - sin(y) - (sqrt(3) - 1)/2]
    soln_x = Union(ImageSet(Lambda(n, 2*n*pi + pi/3), S.Integers),
        ImageSet(Lambda(n, 2*n*pi + 2*pi/3), S.Integers))
    soln_y = Union(ImageSet(Lambda(n, 2*n*pi + pi/6), S.Integers),
        ImageSet(Lambda(n, 2*n*pi + 5*pi/6), S.Integers))
    assert nonlinsolve(sys, [x, y]) ==FiniteSet((soln_x, soln_y))


def test_nonlinsolve_positive_dimensional():
    x, y, z, a, b, c, d = symbols('x, y, z, a, b, c, d', real = True)
    assert nonlinsolve([x*y, x*y - x], [x, y]) == FiniteSet((0, y))

    system = [a**2 + a*c, a - b]
    assert nonlinsolve(system, [a, b]) == FiniteSet((0, 0), (-c, -c))
    # here (a= 0, b = 0) is independent soln so both is printed.
    # if symbols = [a, b, c] then only {a : -c ,b : -c}

    eq1 =  a + b + c + d
    eq2 = a*b + b*c + c*d + d*a
    eq3 = a*b*c + b*c*d + c*d*a + d*a*b
    eq4 = a*b*c*d - 1
    system = [eq1, eq2, eq3, eq4]
    sol1 = (-1/d, -d, 1/d, FiniteSet(d) - FiniteSet(0))
    sol2 = (1/d, -d, -1/d, FiniteSet(d) - FiniteSet(0))
    soln = FiniteSet(sol1, sol2)
    assert nonlinsolve(system, [a, b, c, d]) == soln


def test_nonlinsolve_polysys():
    x, y, z = symbols('x, y, z', real = True)
    assert nonlinsolve([x**2 + y - 2, x**2 + y], [x, y]) == S.EmptySet

    s = (-y + 2, y)
    assert nonlinsolve([(x + y)**2 - 4, x + y - 2], [x, y]) == FiniteSet(s)

    system = [x**2 - y**2]
    soln_real = FiniteSet((-y, y), (y, y))
    soln_complex = FiniteSet((-Abs(y), y), (Abs(y), y))
    soln =soln_real + soln_complex
    assert nonlinsolve(system, [x, y]) == soln

    system = [x**2 - y**2]
    soln_real= FiniteSet((y, -y), (y, y))
    soln_complex = FiniteSet((y, -Abs(y)), (y, Abs(y)))
    soln = soln_real + soln_complex
    assert nonlinsolve(system, [y, x]) == soln

    system = [x**2 + y - 3, x - y - 4]
    assert nonlinsolve(system, (x, y)) != nonlinsolve(system, (y, x))


def test_nonlinsolve_using_substitution():
    x, y, z, n = symbols('x, y, z, n', real = True)
    system = [(x + y)*n - y**2 + 2]
    s_x = (n*y - y**2 + 2)/n
    soln = (-s_x, y)
    assert nonlinsolve(system, [x, y]) == FiniteSet(soln)

    system = [z**2*x**2 - z**2*y**2/exp(x)]
    soln_real_1 = (y, x, 0)
    soln_real_2 = (-exp(x/2)*Abs(x), x, z)
    soln_real_3 = (exp(x/2)*Abs(x), x, z)
    soln_complex_1 = (-x*exp(x/2), x, z)
    soln_complex_2 = (x*exp(x/2), x, z)
    syms = [y, x, z]
    soln = FiniteSet(soln_real_1, soln_complex_1, soln_complex_2,\
        soln_real_2, soln_real_3)
    assert nonlinsolve(system,syms) == soln


def test_nonlinsolve_complex():
    x, y, z = symbols('x, y, z')
    n = Dummy('n')
    real_soln = (log(sin(S(1)/3)), S(1)/3)
    img_lamda = Lambda(n, 2*n*I*pi + Mod(log(sin(S(1)/3)), 2*I*pi))
    complex_soln = (ImageSet(img_lamda, S.Integers), S(1)/3)
    soln = FiniteSet(real_soln, complex_soln)
    assert nonlinsolve([exp(x) - sin(y), 1/y - 3], [x, y]) == soln

    system = [exp(x) - sin(y), 1/exp(y) - 3]
    soln_x = ImageSet(Lambda(n, I*(2*n*pi + pi) + log(sin(log(3)))), S.Integers)
    soln_real = FiniteSet((soln_x, -log(S(3))))
    # Mod(-log(3), 2*I*pi) is equal to -log(3).
    expr_x = I*(2*n*pi + arg(sin(2*n*I*pi + Mod(-log(3), 2*I*pi)))) + \
                log(Abs(sin(2*n*I*pi + Mod(-log(3), 2*I*pi))))
    soln_x = ImageSet(Lambda(n, expr_x), S.Integers)
    expr_y = 2*n*I*pi + Mod(-log(3), 2*I*pi)
    soln_y = ImageSet(Lambda(n, expr_y), S.Integers)
    soln_complex = FiniteSet((soln_x, soln_y))
    soln = soln_real + soln_complex
    assert nonlinsolve(system, [x, y]) == soln

    system = [exp(x) - sin(y), y**2 - 4]
    s1 = (log(sin(2)), 2)
    s2 = (ImageSet(Lambda(n, I*(2*n*pi + pi) + log(sin(2))), S.Integers), -2 )
    img = ImageSet(Lambda(n, 2*n*I*pi + Mod(log(sin(2)), 2*I*pi)), S.Integers)
    s3 = (img, 2)
    assert nonlinsolve(system, [x, y]) == FiniteSet(s1, s2, s3)


@XFAIL
def test_solve_nonlinear_trans():
    # After the transcendental equation solver these will work
    x, y, z = symbols('x, y, z', real=True)
    soln1 = FiniteSet((2*LambertW(y/2), y))
    soln2 = FiniteSet((-x*sqrt(exp(x)), y), (x*sqrt(exp(x)), y))
    soln3 = FiniteSet((x*exp(x/2), x))
    soln4 = FiniteSet(2*LambertW(y/2), y)
    assert nonlinsolve([x**2 - y**2/exp(x)], [x, y]) == soln1
    assert nonlinsolve([x**2 - y**2/exp(x)], [y, x]) == soln2
    assert nonlinsolve([x**2 - y**2/exp(x)], [y, x]) == soln3
    assert nonlinsolve([x**2 - y**2/exp(x)], [x, y]) == soln4


def test_issue_5132_1():
    system = [sqrt(x**2 + y**2) - sqrt(10), x + y - 4]
    assert nonlinsolve(system, [x, y]) == FiniteSet((1, 3), (3, 1))

    n = Dummy('n')
    eqs = [exp(x)**2 - sin(y) + z**2, 1/exp(y) - 3]
    s_real_y = -log(3)
    s_real_z = sqrt(-exp(2*x) - sin(log(3)))
    soln_real = FiniteSet((s_real_y, s_real_z), (s_real_y, -s_real_z))
    lam = Lambda(n, 2*n*I*pi + Mod(-log(3), 2*I*pi))
    s_complex_y = ImageSet(lam, S.Integers)
    lam = Lambda(n, sqrt(-exp(2*x) + sin(2*n*I*pi + Mod(-log(3), 2*I*pi))))
    s_complex_z_1 = ImageSet(lam, S.Integers)
    lam = Lambda(n, -sqrt(-exp(2*x) + sin(2*n*I*pi + Mod(-log(3), 2*I*pi))))
    s_complex_z_2 = ImageSet(lam, S.Integers)
    soln_complex = FiniteSet(
                                            (s_complex_y, s_complex_z_1),
                                            (s_complex_y, s_complex_z_2)
                                        )
    soln = soln_real + soln_complex
    assert nonlinsolve(eqs, [y, z]) == soln


def test_issue_5132_2():
    x, y = symbols('x, y', real=True)
    eqs = [exp(x)**2 - sin(y) + z**2, 1/exp(y) - 3]
    n = Dummy('n')
    soln_real = (log(-z**2 + sin(y))/2, z)
    lam = Lambda( n, I*(2*n*pi + arg(-z**2 + sin(y)))/2 + log(Abs(z**2 - sin(y)))/2)
    img = ImageSet(lam, S.Integers)
    # not sure about the complex soln. But it looks correct.
    soln_complex = (img, z)
    soln = FiniteSet(soln_real, soln_complex)
    assert nonlinsolve(eqs, [x, z]) == soln

    r, t = symbols('r, t')
    system = [r - x**2 - y**2, tan(t) - y/x]
    s_x = sqrt(r/(tan(t)**2 + 1))
    s_y = sqrt(r/(tan(t)**2 + 1))*tan(t)
    soln = FiniteSet((s_x, s_y), (-s_x, -s_y))
    assert nonlinsolve(system, [x, y]) == soln


def test_issue_6752():
    a,b,c,d = symbols('a, b, c, d', real=True)
    assert nonlinsolve([a**2 + a, a - b], [a, b]) == {(-1, -1), (0, 0)}


@SKIP("slow")
def test_issue_5114_solveset():
    # slow testcase
    a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r = symbols('a:r')

    # there is no 'a' in the equation set but this is how the
    # problem was originally posed
    syms = [a, b, c, f, h, k, n]
    eqs = [b + r/d - c/d,
    c*(1/d + 1/e + 1/g) - f/g - r/d,
        f*(1/g + 1/i + 1/j) - c/g - h/i,
        h*(1/i + 1/l + 1/m) - f/i - k/m,
        k*(1/m + 1/o + 1/p) - h/m - n/p,
        n*(1/p + 1/q) - k/p]
    assert len(nonlinsolve(eqs, syms)) == 1


@SKIP("Hangs")
def _test_issue_5335():
    # Not able to check zero dimensional system.
    # is_zero_dimensional Hangs
    lam, a0, conc = symbols('lam a0 conc')
    eqs = [lam + 2*y - a0*(1 - x/2)*x - 0.005*x/2*x,
           a0*(1 - x/2)*x - 1*y - 0.743436700916726*y,
           x + y - conc]
    sym = [x, y, a0]
    # there are 4 solutions but only two are valid
    assert len(nonlinsolve(eqs, sym)) == 2
    # float
    lam, a0, conc = symbols('lam a0 conc')
    eqs = [lam + 2*y - a0*(1 - x/2)*x - 0.005*x/2*x,
           a0*(1 - x/2)*x - 1*y - 0.743436700916726*y,
           x + y - conc]
    sym = [x, y, a0]
    assert len(nonlinsolve(eqs, sym)) == 2


def test_issue_2777():
    # the equations represent two circles
    x, y = symbols('x y', real=True)
    e1, e2 = sqrt(x**2 + y**2) - 10, sqrt(y**2 + (-x + 10)**2) - 3
    a, b = 191/S(20), 3*sqrt(391)/20
    ans = {(a, -b), (a, b)}
    assert nonlinsolve((e1, e2), (x, y)) == ans
    assert nonlinsolve((e1, e2/(x - a)), (x, y)) == S.EmptySet
    # make the 2nd circle's radius be -3
    e2 += 6
    assert nonlinsolve((e1, e2), (x, y)) == S.EmptySet


def test_issue_8828():
    x1 = 0
    y1 = -620
    r1 = 920
    x2 = 126
    y2 = 276
    x3 = 51
    y3 = 205
    r3 = 104
    v = [x, y, z]

    f1 = (x - x1)**2 + (y - y1)**2 - (r1 - z)**2
    f2 = (x2 - x)**2 + (y2 - y)**2 - z**2
    f3 = (x - x3)**2 + (y - y3)**2 - (r3 - z)**2
    F = [f1, f2, f3]

    g1 = sqrt((x - x1)**2 + (y - y1)**2) + z - r1
    g2 = f2
    g3 = sqrt((x - x3)**2 + (y - y3)**2) + z - r3
    G = [g1, g2, g3]

    # both soln same
    A = nonlinsolve(F, v)
    B = nonlinsolve(G, v)
    assert A == B


def test_nonlinsolve_conditionset():
    # when solveset failed to solve all the eq
    # return conditionset
    f = Function('f')
    f1 = f(x) - pi/2
    f2 = f(y) - 3*pi/2
    intermediate_system = FiniteSet(2*f(x) - pi, 2*f(y) - 3*pi)
    symbols = Tuple(x, y)
    soln = ConditionSet(
        symbols,
        intermediate_system,
        S.Complexes)
    assert nonlinsolve([f1, f2], [x, y]) == soln


def test_substitution_basic():
    assert substitution([], [x, y]) == S.EmptySet
    assert substitution([], []) == S.EmptySet
    system = [2*x**2 + 3*y**2 - 30, 3*x**2 - 2*y**2 - 19]
    soln = FiniteSet((-3, -2), (-3, 2), (3, -2), (3, 2))
    assert substitution(system, [x, y]) == soln

    soln = FiniteSet((-1, 1))
    assert substitution([x + y], [x], [{y: 1}], [y], set([]), [x, y]) == soln
    assert substitution(
        [x + y], [x], [{y: 1}], [y],
        set([x + 1]), [y, x]) == S.EmptySet


def test_issue_5132_substitution():
    x, y, z, r, t = symbols('x, y, z, r, t', real=True)
    system = [r - x**2 - y**2, tan(t) - y/x]
    s_x_1 = Complement(FiniteSet(-sqrt(r/(tan(t)**2 + 1))), FiniteSet(0))
    s_x_2 = Complement(FiniteSet(sqrt(r/(tan(t)**2 + 1))), FiniteSet(0))
    s_y = sqrt(r/(tan(t)**2 + 1))*tan(t)
    soln = FiniteSet((s_x_2, s_y)) + FiniteSet((s_x_1, -s_y))
    assert substitution(system, [x, y]) == soln

    n = Dummy('n')
    eqs = [exp(x)**2 - sin(y) + z**2, 1/exp(y) - 3]
    s_real_y = -log(3)
    s_real_z = sqrt(-exp(2*x) - sin(log(3)))
    soln_real = FiniteSet((s_real_y, s_real_z), (s_real_y, -s_real_z))
    lam = Lambda(n, 2*n*I*pi + Mod(-log(3), 2*I*pi))
    s_complex_y = ImageSet(lam, S.Integers)
    lam = Lambda(n, sqrt(-exp(2*x) + sin(2*n*I*pi + Mod(-log(3), 2*I*pi))))
    s_complex_z_1 = ImageSet(lam, S.Integers)
    lam = Lambda(n, -sqrt(-exp(2*x) + sin(2*n*I*pi + Mod(-log(3), 2*I*pi))))
    s_complex_z_2 = ImageSet(lam, S.Integers)
    soln_complex = FiniteSet(
                                            (s_complex_y, s_complex_z_1),
                                            (s_complex_y, s_complex_z_2)
                                        )
    soln = soln_real + soln_complex
    assert substitution(eqs, [y, z]) == soln


def test_raises_substitution():
    raises(ValueError, lambda: substitution([x**2 -1], []))
    raises(TypeError, lambda: substitution([x**2 -1]))
    raises(ValueError, lambda: substitution([x**2 -1], [sin(x)]))
    raises(TypeError, lambda: substitution([x**2 -1], x))
    raises(TypeError, lambda: substitution([x**2 -1], 1))

# end of tests for nonlinsolve


def test_issue_9556():
    x = Symbol('x')
    b = Symbol('b', positive=True)

    assert solveset(Abs(x) + 1, x, S.Reals) == EmptySet()
    assert solveset(Abs(x) + b, x, S.Reals) == EmptySet()
    assert solveset(Eq(b, -1), b, S.Reals) == EmptySet()


def test_issue_9611():
    x = Symbol('x')
    a = Symbol('a')
    y = Symbol('y')

    assert solveset(Eq(x - x + a, a), x, S.Reals) == S.Reals
    assert solveset(Eq(y - y + a, a), y) == S.Complexes


def test_issue_9557():
    x = Symbol('x')
    a = Symbol('a')

    assert solveset(x**2 + a, x, S.Reals) == Intersection(S.Reals,
        FiniteSet(-sqrt(-a), sqrt(-a)))


def test_issue_9778():
    assert solveset(x**3 + 1, x, S.Reals) == FiniteSet(-1)
    assert solveset(x**(S(3)/5) + 1, x, S.Reals) == S.EmptySet
    assert solveset(x**3 + y, x, S.Reals) == \
        FiniteSet(-Abs(y)**(S(1)/3)*sign(y))


def test_issue_10214():
    assert solveset(x**(S(3)/2) + 4, x, S.Reals) == S.EmptySet
    assert solveset(x**(S(-3)/2) + 4, x, S.Reals) == S.EmptySet

    ans = FiniteSet(-2**(S(2)/3))
    assert solveset(x**(S(3)) + 4, x, S.Reals) == ans
    assert (x**(S(3)) + 4).subs(x,list(ans)[0]) == 0 # substituting ans and verifying the result.
    assert (x**(S(3)) + 4).subs(x,-(-2)**(2/S(3))) == 0


def test_issue_9849():
    assert solveset(Abs(sin(x)) + 1, x, S.Reals) == S.EmptySet


def test_issue_9953():
    assert linsolve([ ], x) == S.EmptySet


def test_issue_9913():
    assert solveset(2*x + 1/(x - 10)**2, x, S.Reals) == \
        FiniteSet(-(3*sqrt(24081)/4 + S(4027)/4)**(S(1)/3)/3 - 100/
                (3*(3*sqrt(24081)/4 + S(4027)/4)**(S(1)/3)) + S(20)/3)


def test_issue_10397():
    assert solveset(sqrt(x), x, S.Complexes) == FiniteSet(0)


def test_issue_14987():
    raises(ValueError, lambda: linear_eq_to_matrix(
        [x**2], x))
    raises(ValueError, lambda: linear_eq_to_matrix(
        [x*(-3/x + 1) + 2*y - a], [x, y]))
    raises(ValueError, lambda: linear_eq_to_matrix(
        [(x**2 - 3*x)/(x - 3) - 3], x))
    raises(ValueError, lambda: linear_eq_to_matrix(
        [(x + 1)**3 - x**3 - 3*x**2 + 7], x))
    raises(ValueError, lambda: linear_eq_to_matrix(
        [x*(1/x + 1) + y], [x, y]))
    raises(ValueError, lambda: linear_eq_to_matrix(
        [(x + 1)*y], [x, y]))
    raises(ValueError, lambda: linear_eq_to_matrix(
        [Eq(1/x, 1/x + y)], [x, y]))
    raises(ValueError, lambda: linear_eq_to_matrix(
        [Eq(y/x, y/x + y)], [x, y]))
    raises(ValueError, lambda: linear_eq_to_matrix(
        [Eq(x*(x + 1), x**2 + y)], [x, y]))


def test_simplification():
    eq = x + (a - b)/(-2*a + 2*b)
    assert solveset(eq, x) == FiniteSet(S.Half)
    assert solveset(eq, x, S.Reals) == FiniteSet(S.Half)


def test_issue_10555():
    f = Function('f')
    g = Function('g')
    assert solveset(f(x) - pi/2, x, S.Reals) == \
        ConditionSet(x, Eq(f(x) - pi/2, 0), S.Reals)
    assert solveset(f(g(x)) - pi/2, g(x), S.Reals) == \
        ConditionSet(g(x), Eq(f(g(x)) - pi/2, 0), S.Reals)


def test_issue_8715():
    eq = x + 1/x > -2 + 1/x
    assert solveset(eq, x, S.Reals) == \
        (Interval.open(-2, oo) - FiniteSet(0))
    assert solveset(eq.subs(x,log(x)), x, S.Reals) == \
        Interval.open(exp(-2), oo) - FiniteSet(1)


def test_issue_11174():
    r, t = symbols('r t')
    eq = z**2 + exp(2*x) - sin(y)
    soln = Intersection(S.Reals, FiniteSet(log(-z**2 + sin(y))/2))
    assert solveset(eq, x, S.Reals) == soln

    eq = sqrt(r)*Abs(tan(t))/sqrt(tan(t)**2 + 1) + x*tan(t)
    s = -sqrt(r)*Abs(tan(t))/(sqrt(tan(t)**2 + 1)*tan(t))
    soln = Intersection(S.Reals, FiniteSet(s))
    assert solveset(eq, x, S.Reals) == soln


def test_issue_11534():
    # eq and eq2 should give the same solution as a Complement
    eq = -y + x/sqrt(-x**2 + 1)
    eq2 = -y**2 + x**2/(-x**2 + 1)
    soln = Complement(FiniteSet(-y/sqrt(y**2 + 1), y/sqrt(y**2 + 1)), FiniteSet(-1, 1))
    assert solveset(eq, x, S.Reals) == soln
    assert solveset(eq2, x, S.Reals) == soln


def test_issue_10477():
    assert solveset((x**2 + 4*x - 3)/x < 2, x, S.Reals) == \
        Union(Interval.open(-oo, -3), Interval.open(0, 1))


def test_issue_10671():
    assert solveset(sin(y), y, Interval(0, pi)) == FiniteSet(0, pi)
    i = Interval(1, 10)
    assert solveset((1/x).diff(x) < 0, x, i) == i


def test_issue_11064():
    eq = x + sqrt(x**2 - 5)
    assert solveset(eq > 0, x, S.Reals) == \
        Interval(sqrt(5), oo)
    assert solveset(eq < 0, x, S.Reals) == \
        Interval(-oo, -sqrt(5))
    assert solveset(eq > sqrt(5), x, S.Reals) == \
        Interval.Lopen(sqrt(5), oo)


def test_issue_12478():
    eq = sqrt(x - 2) + 2
    soln = solveset_real(eq, x)
    assert soln is S.EmptySet
    assert solveset(eq < 0, x, S.Reals) is S.EmptySet
    assert solveset(eq > 0, x, S.Reals) == Interval(2, oo)


def test_issue_12429():
    eq = solveset(log(x)/x <= 0, x, S.Reals)
    sol = Interval.Lopen(0, 1)
    assert eq == sol


def test_solveset_arg():
    assert solveset(arg(x), x, S.Reals)  == Interval.open(0, oo)
    assert solveset(arg(4*x -3), x) == Interval.open(S(3)/4, oo)


def test__is_finite_with_finite_vars():
    f = _is_finite_with_finite_vars
    # issue 12482
    assert all(f(1/x) is None for x in (
        Dummy(), Dummy(real=True), Dummy(complex=True)))
    assert f(1/Dummy(real=False)) is True  # b/c it's finite but not 0


def test_issue_13550():
    assert solveset(x**2 - 2*x - 15, symbol = x, domain = Interval(-oo, 0)) == FiniteSet(-3)


def test_issue_13849():
    t = symbols('t')
    assert nonlinsolve((t*(sqrt(5) + sqrt(2)) - sqrt(2), t), t) == EmptySet()


def test_issue_14223():
    x = Symbol('x')
    assert solveset((Abs(x + Min(x, 2)) - 2).rewrite(Piecewise), x,
        S.Reals) == FiniteSet(-1, 1)
    assert solveset((Abs(x + Min(x, 2)) - 2).rewrite(Piecewise), x,
        Interval(0, 2)) == FiniteSet(1)


def test_issue_10158():
    x = Symbol('x')
    dom = S.Reals
    assert solveset(x*Max(x, 15) - 10, x, dom) == FiniteSet(2/S(3))
    assert solveset(x*Min(x, 15) - 10, x, dom) == FiniteSet(-sqrt(10), sqrt(10))
    assert solveset(Max(Abs(x - 3) - 1, x + 2) - 3, x, dom) == FiniteSet(-1, 1)
    assert solveset(Abs(x - 1) - Abs(y), x, dom) == FiniteSet(-Abs(y) + 1, Abs(y) + 1)
    assert solveset(Abs(x + 4*Abs(x + 1)), x, dom) == FiniteSet(-4/S(3), -4/S(5))
    assert solveset(2*Abs(x + Abs(x + Max(3, x))) - 2, x, S.Reals) == FiniteSet(-1, -2)
    dom = S.Complexes
    raises(ValueError, lambda: solveset(x*Max(x, 15) - 10, x, dom))
    raises(ValueError, lambda: solveset(x*Min(x, 15) - 10, x, dom))
    raises(ValueError, lambda: solveset(Max(Abs(x - 3) - 1, x + 2) - 3, x, dom))
    raises(ValueError, lambda: solveset(Abs(x - 1) - Abs(y), x, dom))
    raises(ValueError, lambda: solveset(Abs(x + 4*Abs(x + 1)), x, dom))


def test_issue_14300():
    x, y, n = symbols('x y n')

    f = 1 - exp(-18000000*x) - y
    a1 = FiniteSet(-log(-y + 1)/18000000)

    assert solveset(f, x, S.Reals) == \
        Intersection(S.Reals, a1)
    assert solveset(f, x) == \
        ImageSet(Lambda(n, -I*(2*n*pi + arg(-y + 1))/18000000 -
            log(Abs(y - 1))/18000000), S.Integers)


def test_issue_14454():
    x = Symbol('x')
    number = CRootOf(x**4 + x - 1, 2)
    raises(ValueError, lambda: invert_real(number, 0, x, S.Reals))
    assert invert_real(x**2, number, x, S.Reals)  # no error


def test_term_factors():
    assert list(_term_factors(3**x - 2)) == [-2, 3**x]
    expr = 4**(x + 1) + 4**(x + 2) + 4**(x - 1) - 3**(x + 2) - 3**(x + 3)
    assert set(_term_factors(expr)) == set([
        3**(x + 2), 4**(x + 2), 3**(x + 3), 4**(x - 1), -1, 4**(x + 1)])


#################### tests for transolve and its helpers ###############

def test_transolve():

    assert _transolve(3**x, x, S.Reals) == S.EmptySet
    assert _transolve(3**x - 9**(x + 5), x, S.Reals) == FiniteSet(-10)


# exponential tests
def test_exponential_real():
    from sympy.abc import x, y, z

    e1 = 3**(2*x) - 2**(x + 3)
    e2 = 4**(5 - 9*x) - 8**(2 - x)
    e3 = 2**x + 4**x
    e4 = exp(log(5)*x) - 2**x
    e5 = exp(x/y)*exp(-z/y) - 2
    e6 = 5**(x/2) - 2**(x/3)
    e7 = 4**(x + 1) + 4**(x + 2) + 4**(x - 1) - 3**(x + 2) - 3**(x + 3)
    e8 = -9*exp(-2*x + 5) + 4*exp(3*x + 1)
    e9 = 2**x + 4**x + 8**x - 84

    assert solveset(e1, x, S.Reals) == FiniteSet(
        -3*log(2)/(-2*log(3) + log(2)))
    assert solveset(e2, x, S.Reals) == FiniteSet(4/S(15))
    assert solveset(e3, x, S.Reals) == S.EmptySet
    assert solveset(e4, x, S.Reals) == FiniteSet(0)
    assert solveset(e5, x, S.Reals) == Intersection(
        S.Reals, FiniteSet(y*log(2*exp(z/y))))
    assert solveset(e6, x, S.Reals) == FiniteSet(0)
    assert solveset(e7, x, S.Reals) == FiniteSet(2)
    assert solveset(e8, x, S.Reals) == FiniteSet(-2*log(2)/5 + 2*log(3)/5 + S(4)/5)
    assert solveset(e9, x, S.Reals) == FiniteSet(2)

    assert solveset_real(-9*exp(-2*x + 5) + 2**(x + 1), x) == FiniteSet(
        -((-5 - 2*log(3) + log(2))/(log(2) + 2)))
    assert solveset_real(4**(x/2) - 2**(x/3), x) == FiniteSet(0)
    b = sqrt(6)*sqrt(log(2))/sqrt(log(5))
    assert solveset_real(5**(x/2) - 2**(3/x), x) == FiniteSet(-b, b)

    # coverage test
    C1, C2 = symbols('C1 C2')
    f = Function('f')
    assert solveset_real(C1 + C2/x**2 - exp(-f(x)), f(x)) == Intersection(
        S.Reals, FiniteSet(-log(C1 + C2/x**2)))
    y = symbols('y', positive=True)
    assert solveset_real(x**2 - y**2/exp(x), y) == Intersection(
        S.Reals, FiniteSet(-sqrt(x**2*exp(x)), sqrt(x**2*exp(x))))
    p = Symbol('p', positive=True)
    assert solveset_real((1/p + 1)**(p + 1), p) == EmptySet()


@XFAIL
def test_exponential_complex():
    from sympy.abc import x
    from sympy import Dummy
    n = Dummy('n')

    assert solveset_complex(2**x + 4**x, x) == imageset(
        Lambda(n, I*(2*n*pi + pi)/log(2)), S.Integers)
    assert solveset_complex(x**z*y**z - 2, z) == FiniteSet(
        log(2)/(log(x) + log(y)))
    assert solveset_complex(4**(x/2) - 2**(x/3), x) == imageset(
        Lambda(n, 3*n*I*pi/log(2)), S.Integers)
    assert solveset(2**x + 32, x) == imageset(
        Lambda(n, (I*(2*n*pi + pi) + 5*log(2))/log(2)), S.Integers)

    eq = (2**exp(y**2/x) + 2)/(x**2 + 15)
    a = sqrt(x)*sqrt(-log(log(2)) + log(log(2) + 2*n*I*pi))
    assert solveset_complex(eq, y) == FiniteSet(-a, a)

    union1 = imageset(Lambda(n, I*(2*n*pi - 2*pi/3)/log(2)), S.Integers)
    union2 = imageset(Lambda(n, I*(2*n*pi + 2*pi/3)/log(2)), S.Integers)
    assert solveset(2**x + 4**x + 8**x, x) == Union(union1, union2)

    eq = 4**(x + 1) + 4**(x + 2) + 4**(x - 1) - 3**(x + 2) - 3**(x + 3)
    res = solveset(eq, x)
    num = 2*n*I*pi - 4*log(2) + 2*log(3)
    den = -2*log(2) + log(3)
    ans = imageset(Lambda(n, num/den), S.Integers)
    assert res == ans


def test_expo_conditionset():
    from sympy.abc import x, y

    f1 = (exp(x) + 1)**x - 2
    f2 = (x + 2)**y*x - 3
    f3 = 2**x - exp(x) - 3
    f4 = log(x) - exp(x)
    f5 = 2**x + 3**x - 5**x

    assert solveset(f1, x, S.Reals) == ConditionSet(
        x, Eq((exp(x) + 1)**x - 2, 0), S.Reals)
    assert solveset(f2, x, S.Reals) == ConditionSet(
        x, Eq(x*(x + 2)**y - 3, 0), S.Reals)
    assert solveset(f3, x, S.Reals) == ConditionSet(
        x, Eq(2**x - exp(x) - 3, 0), S.Reals)
    assert solveset(f4, x, S.Reals) == ConditionSet(
        x, Eq(-exp(x) + log(x), 0), S.Reals)
    assert solveset(f5, x, S.Reals) == ConditionSet(
        x, Eq(2**x + 3**x - 5**x, 0), S.Reals)


def test_exponential_symbols():
    x, y, z = symbols('x y z', positive=True)
    from sympy import simplify

    assert solveset(z**x - y, x, S.Reals) == Intersection(
        S.Reals, FiniteSet(log(y)/log(z)))

    w = symbols('w')
    f1 = 2*x**w - 4*y**w
    f2 = (x/y)**w - 2
    ans1 = solveset(f1, w, S.Reals)
    ans2 = solveset(f2, w, S.Reals)
    assert ans1 == simplify(ans2)

    assert solveset(x**x, x, S.Reals) == S.EmptySet
    assert solveset(x**y - 1, y, S.Reals) == FiniteSet(0)
    assert solveset(exp(x/y)*exp(-z/y) - 2, y, S.Reals) == FiniteSet(
        (x - z)/log(2)) - FiniteSet(0)

    a, b, x, y = symbols('a b x y')
    assert solveset_real(a**x - b**x, x) == ConditionSet(
        x, (a > 0) & (b > 0), FiniteSet(0))
    assert solveset(a**x - b**x, x) == ConditionSet(
        x, Ne(a, 0) & Ne(b, 0), FiniteSet(0))


@XFAIL
def test_issue_10864():
    assert solveset(x**(y*z) - x, x, S.Reals) == FiniteSet(1)


@XFAIL
def test_solve_only_exp_2():
    assert solveset_real(sqrt(exp(x)) + sqrt(exp(-x)) - 4, x) == \
        FiniteSet(2*log(-sqrt(3) + 2), 2*log(sqrt(3) + 2))


def test_is_exponential():
    x, y, z = symbols('x y z')

    assert _is_exponential(y, x) is False
    assert _is_exponential(3**x - 2, x) is True
    assert _is_exponential(5**x - 7**(2 - x), x) is True
    assert _is_exponential(sin(2**x) - 4*x, x) is False
    assert _is_exponential(x**y - z, y) is True
    assert _is_exponential(x**y - z, x) is False
    assert _is_exponential(2**x + 4**x - 1, x) is True
    assert _is_exponential(x**(y*z) - x, x) is False
    assert _is_exponential(x**(2*x) - 3**x, x) is False
    assert _is_exponential(x**y - y*z, y) is False
    assert _is_exponential(x**y - x*z, y) is True


def test_solve_exponential():
    assert _solve_exponential(3**(2*x) - 2**(x + 3), 0, x, S.Reals) == \
        FiniteSet(-3*log(2)/(-2*log(3) + log(2)))
    assert _solve_exponential(2**y + 4**y, 1, y, S.Reals) == \
        FiniteSet(log(-S(1)/2 + sqrt(5)/2)/log(2))
    assert _solve_exponential(2**y + 4**y, 0, y, S.Reals) == \
        S.EmptySet
    assert _solve_exponential(2**x + 3**x - 5**x, 0, x, S.Reals) == \
        ConditionSet(x, Eq(2**x + 3**x - 5**x, 0), S.Reals)

# end of exponential tests


# logarithmic tests
def test_logarithmic():
    assert solveset_real(log(x - 3) + log(x + 3), x) == FiniteSet(
        -sqrt(10), sqrt(10))
    assert solveset_real(log(x + 1) - log(2*x - 1), x) == FiniteSet(2)
    assert solveset_real(log(x + 3) + log(1 + 3/x) - 3, x) == FiniteSet(
        -3 + sqrt(-12 + exp(3))*exp(S(3)/2)/2 + exp(3)/2,
        -sqrt(-12 + exp(3))*exp(S(3)/2)/2 - 3 + exp(3)/2)

    eq = z - log(x) + log(y/(x*(-1 + y**2/x**2)))
    assert solveset_real(eq, x) == \
        Intersection(S.Reals, FiniteSet(-sqrt(y**2 - y*exp(z)),
            sqrt(y**2 - y*exp(z)))) - \
        Intersection(S.Reals, FiniteSet(-sqrt(y**2), sqrt(y**2)))
    assert solveset_real(
        log(3*x) - log(-x + 1) - log(4*x + 1), x) == FiniteSet(-S(1)/2, S(1)/2)
    assert solveset(log(x**y) - y*log(x), x, S.Reals) == S.Reals

@XFAIL
def test_uselogcombine_2():
    eq = log(exp(2*x) + 1) + log(-tanh(x) + 1) - log(2)
    assert solveset_real(eq, x) == EmptySet()
    eq = log(8*x) - log(sqrt(x) + 1) - 2
    assert solveset_real(eq, x) == EmptySet()


def test_is_logarithmic():
    assert _is_logarithmic(y, x) is False
    assert _is_logarithmic(log(x), x) is True
    assert _is_logarithmic(log(x) - 3, x) is True
    assert _is_logarithmic(log(x)*log(y), x) is True
    assert _is_logarithmic(log(x)**2, x) is False
    assert _is_logarithmic(log(x - 3) + log(x + 3), x) is True
    assert _is_logarithmic(log(x**y) - y*log(x), x) is True
    assert _is_logarithmic(sin(log(x)), x) is False
    assert _is_logarithmic(x + y, x) is False
    assert _is_logarithmic(log(3*x) - log(1 - x) + 4, x) is True
    assert _is_logarithmic(log(x) + log(y) + x, x) is False
    assert _is_logarithmic(log(log(x - 3)) + log(x - 3), x) is True
    assert _is_logarithmic(log(log(3) + x) + log(x), x) is True
    assert _is_logarithmic(log(x)*(y + 3) + log(x), y) is False


def test_solve_logarithm():
    y = Symbol('y')
    assert _solve_logarithm(log(x**y) - y*log(x), 0, x, S.Reals) == S.Reals
    y = Symbol('y', positive=True)
    assert _solve_logarithm(log(x)*log(y), 0, x, S.Reals) == FiniteSet(1)

# end of logarithmic tests


def test_linear_coeffs():
    from sympy.solvers.solveset import linear_coeffs
    assert linear_coeffs(0, x) == [0, 0]
    assert all(i is S.Zero for i in linear_coeffs(0, x))
    assert linear_coeffs(x + 2*y + 3, x, y) == [1, 2, 3]
    assert linear_coeffs(x + 2*y + 3, y, x) == [2, 1, 3]
    assert linear_coeffs(x + 2*x**2 + 3, x, x**2) == [1, 2, 3]
    raises(ValueError, lambda:
        linear_coeffs(x + 2*x**2 + x**3, x, x**2))
    raises(ValueError, lambda:
        linear_coeffs(1/x*(x - 1) + 1/x, x))
    assert linear_coeffs(a*(x + y), x, y) == [a, a, 0]
