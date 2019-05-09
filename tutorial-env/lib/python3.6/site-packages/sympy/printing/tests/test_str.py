from sympy import (Abs, Catalan, cos, Derivative, E, EulerGamma, exp,
    factorial, factorial2, Function, GoldenRatio, TribonacciConstant, I,
    Integer, Integral, Interval, Lambda, Limit, Matrix, nan, O, oo, pi, Pow,
    Rational, Float, Rel, S, sin, SparseMatrix, sqrt, summation, Sum, Symbol,
    symbols, Wild, WildFunction, zeta, zoo, Dummy, Dict, Tuple, FiniteSet, factor,
    subfactorial, true, false, Equivalent, Xor, Complement, SymmetricDifference,
    AccumBounds, UnevaluatedExpr, Eq, Ne, Quaternion, Subs)
from sympy.core import Expr, Mul
from sympy.physics.units import second, joule
from sympy.polys import Poly, rootof, RootSum, groebner, ring, field, ZZ, QQ, lex, grlex
from sympy.geometry import Point, Circle

from sympy.utilities.pytest import raises
from sympy.core.compatibility import range

from sympy.printing import sstr, sstrrepr, StrPrinter
from sympy.core.trace import Tr
from sympy import MatrixSymbol
from sympy import factorial, log, integrate

x, y, z, w, t = symbols('x,y,z,w,t')
d = Dummy('d')


def test_printmethod():
    class R(Abs):
        def _sympystr(self, printer):
            return "foo(%s)" % printer._print(self.args[0])
    assert sstr(R(x)) == "foo(x)"

    class R(Abs):
        def _sympystr(self, printer):
            return "foo"
    assert sstr(R(x)) == "foo"


def test_Abs():
    assert str(Abs(x)) == "Abs(x)"
    assert str(Abs(Rational(1, 6))) == "1/6"
    assert str(Abs(Rational(-1, 6))) == "1/6"


def test_Add():
    assert str(x + y) == "x + y"
    assert str(x + 1) == "x + 1"
    assert str(x + x**2) == "x**2 + x"
    assert str(5 + x + y + x*y + x**2 + y**2) == "x**2 + x*y + x + y**2 + y + 5"
    assert str(1 + x + x**2/2 + x**3/3) == "x**3/3 + x**2/2 + x + 1"
    assert str(2*x - 7*x**2 + 2 + 3*y) == "-7*x**2 + 2*x + 3*y + 2"
    assert str(x - y) == "x - y"
    assert str(2 - x) == "2 - x"
    assert str(x - 2) == "x - 2"
    assert str(x - y - z - w) == "-w + x - y - z"
    assert str(x - z*y**2*z*w) == "-w*y**2*z**2 + x"
    assert str(x - 1*y*x*y) == "-x*y**2 + x"
    assert str(sin(x).series(x, 0, 15)) == "x - x**3/6 + x**5/120 - x**7/5040 + x**9/362880 - x**11/39916800 + x**13/6227020800 + O(x**15)"


def test_Catalan():
    assert str(Catalan) == "Catalan"


def test_ComplexInfinity():
    assert str(zoo) == "zoo"


def test_Derivative():
    assert str(Derivative(x, y)) == "Derivative(x, y)"
    assert str(Derivative(x**2, x, evaluate=False)) == "Derivative(x**2, x)"
    assert str(Derivative(
        x**2/y, x, y, evaluate=False)) == "Derivative(x**2/y, x, y)"


def test_dict():
    assert str({1: 1 + x}) == sstr({1: 1 + x}) == "{1: x + 1}"
    assert str({1: x**2, 2: y*x}) in ("{1: x**2, 2: x*y}", "{2: x*y, 1: x**2}")
    assert sstr({1: x**2, 2: y*x}) == "{1: x**2, 2: x*y}"


def test_Dict():
    assert str(Dict({1: 1 + x})) == sstr({1: 1 + x}) == "{1: x + 1}"
    assert str(Dict({1: x**2, 2: y*x})) in (
        "{1: x**2, 2: x*y}", "{2: x*y, 1: x**2}")
    assert sstr(Dict({1: x**2, 2: y*x})) == "{1: x**2, 2: x*y}"


def test_Dummy():
    assert str(d) == "_d"
    assert str(d + x) == "_d + x"


def test_EulerGamma():
    assert str(EulerGamma) == "EulerGamma"


def test_Exp():
    assert str(E) == "E"


def test_factorial():
    n = Symbol('n', integer=True)
    assert str(factorial(-2)) == "zoo"
    assert str(factorial(0)) == "1"
    assert str(factorial(7)) == "5040"
    assert str(factorial(n)) == "factorial(n)"
    assert str(factorial(2*n)) == "factorial(2*n)"
    assert str(factorial(factorial(n))) == 'factorial(factorial(n))'
    assert str(factorial(factorial2(n))) == 'factorial(factorial2(n))'
    assert str(factorial2(factorial(n))) == 'factorial2(factorial(n))'
    assert str(factorial2(factorial2(n))) == 'factorial2(factorial2(n))'
    assert str(subfactorial(3)) == "2"
    assert str(subfactorial(n)) == "subfactorial(n)"
    assert str(subfactorial(2*n)) == "subfactorial(2*n)"


def test_Function():
    f = Function('f')
    fx = f(x)
    w = WildFunction('w')
    assert str(f) == "f"
    assert str(fx) == "f(x)"
    assert str(w) == "w_"


def test_Geometry():
    assert sstr(Point(0, 0)) == 'Point2D(0, 0)'
    assert sstr(Circle(Point(0, 0), 3)) == 'Circle(Point2D(0, 0), 3)'
    # TODO test other Geometry entities


def test_GoldenRatio():
    assert str(GoldenRatio) == "GoldenRatio"


def test_TribonacciConstant():
    assert str(TribonacciConstant) == "TribonacciConstant"


def test_ImaginaryUnit():
    assert str(I) == "I"


def test_Infinity():
    assert str(oo) == "oo"
    assert str(oo*I) == "oo*I"


def test_Integer():
    assert str(Integer(-1)) == "-1"
    assert str(Integer(1)) == "1"
    assert str(Integer(-3)) == "-3"
    assert str(Integer(0)) == "0"
    assert str(Integer(25)) == "25"


def test_Integral():
    assert str(Integral(sin(x), y)) == "Integral(sin(x), y)"
    assert str(Integral(sin(x), (y, 0, 1))) == "Integral(sin(x), (y, 0, 1))"


def test_Interval():
    n = (S.NegativeInfinity, 1, 2, S.Infinity)
    for i in range(len(n)):
        for j in range(i + 1, len(n)):
            for l in (True, False):
                for r in (True, False):
                    ival = Interval(n[i], n[j], l, r)
                    assert S(str(ival)) == ival


def test_AccumBounds():
    a = Symbol('a', real=True)
    assert str(AccumBounds(0, a)) == "AccumBounds(0, a)"
    assert str(AccumBounds(0, 1)) == "AccumBounds(0, 1)"


def test_Lambda():
    assert str(Lambda(d, d**2)) == "Lambda(_d, _d**2)"
    # issue 2908
    assert str(Lambda((), 1)) == "Lambda((), 1)"
    assert str(Lambda((), x)) == "Lambda((), x)"


def test_Limit():
    assert str(Limit(sin(x)/x, x, y)) == "Limit(sin(x)/x, x, y)"
    assert str(Limit(1/x, x, 0)) == "Limit(1/x, x, 0)"
    assert str(
        Limit(sin(x)/x, x, y, dir="-")) == "Limit(sin(x)/x, x, y, dir='-')"


def test_list():
    assert str([x]) == sstr([x]) == "[x]"
    assert str([x**2, x*y + 1]) == sstr([x**2, x*y + 1]) == "[x**2, x*y + 1]"
    assert str([x**2, [y + x]]) == sstr([x**2, [y + x]]) == "[x**2, [x + y]]"


def test_Matrix_str():
    M = Matrix([[x**+1, 1], [y, x + y]])
    assert str(M) == "Matrix([[x, 1], [y, x + y]])"
    assert sstr(M) == "Matrix([\n[x,     1],\n[y, x + y]])"
    M = Matrix([[1]])
    assert str(M) == sstr(M) == "Matrix([[1]])"
    M = Matrix([[1, 2]])
    assert str(M) == sstr(M) ==  "Matrix([[1, 2]])"
    M = Matrix()
    assert str(M) == sstr(M) == "Matrix(0, 0, [])"
    M = Matrix(0, 1, lambda i, j: 0)
    assert str(M) == sstr(M) == "Matrix(0, 1, [])"


def test_Mul():
    assert str(x/y) == "x/y"
    assert str(y/x) == "y/x"
    assert str(x/y/z) == "x/(y*z)"
    assert str((x + 1)/(y + 2)) == "(x + 1)/(y + 2)"
    assert str(2*x/3) == '2*x/3'
    assert str(-2*x/3) == '-2*x/3'
    assert str(-1.0*x) == '-1.0*x'
    assert str(1.0*x) == '1.0*x'
    # For issue 14160
    assert str(Mul(-2, x, Pow(Mul(y,y,evaluate=False), -1, evaluate=False),
                                                evaluate=False)) == '-2*x/(y*y)'


    class CustomClass1(Expr):
        is_commutative = True

    class CustomClass2(Expr):
        is_commutative = True
    cc1 = CustomClass1()
    cc2 = CustomClass2()
    assert str(Rational(2)*cc1) == '2*CustomClass1()'
    assert str(cc1*Rational(2)) == '2*CustomClass1()'
    assert str(cc1*Float("1.5")) == '1.5*CustomClass1()'
    assert str(cc2*Rational(2)) == '2*CustomClass2()'
    assert str(cc2*Rational(2)*cc1) == '2*CustomClass1()*CustomClass2()'
    assert str(cc1*Rational(2)*cc2) == '2*CustomClass1()*CustomClass2()'


def test_NaN():
    assert str(nan) == "nan"


def test_NegativeInfinity():
    assert str(-oo) == "-oo"

def test_Order():
    assert str(O(x)) == "O(x)"
    assert str(O(x**2)) == "O(x**2)"
    assert str(O(x*y)) == "O(x*y, x, y)"
    assert str(O(x, x)) == "O(x)"
    assert str(O(x, (x, 0))) == "O(x)"
    assert str(O(x, (x, oo))) == "O(x, (x, oo))"
    assert str(O(x, x, y)) == "O(x, x, y)"
    assert str(O(x, x, y)) == "O(x, x, y)"
    assert str(O(x, (x, oo), (y, oo))) == "O(x, (x, oo), (y, oo))"


def test_Permutation_Cycle():
    from sympy.combinatorics import Permutation, Cycle

    # general principle: economically, canonically show all moved elements
    # and the size of the permutation.

    for p, s in [
        (Cycle(),
        '()'),
        (Cycle(2),
        '(2)'),
        (Cycle(2, 1),
        '(1 2)'),
        (Cycle(1, 2)(5)(6, 7)(10),
        '(1 2)(6 7)(10)'),
        (Cycle(3, 4)(1, 2)(3, 4),
        '(1 2)(4)'),
    ]:
        assert str(p) == s

    Permutation.print_cyclic = False
    for p, s in [
        (Permutation([]),
        'Permutation([])'),
        (Permutation([], size=1),
        'Permutation([0])'),
        (Permutation([], size=2),
        'Permutation([0, 1])'),
        (Permutation([], size=10),
        'Permutation([], size=10)'),
        (Permutation([1, 0, 2]),
        'Permutation([1, 0, 2])'),
        (Permutation([1, 0, 2, 3, 4, 5]),
        'Permutation([1, 0], size=6)'),
        (Permutation([1, 0, 2, 3, 4, 5], size=10),
        'Permutation([1, 0], size=10)'),
    ]:
        assert str(p) == s

    Permutation.print_cyclic = True
    for p, s in [
        (Permutation([]),
        '()'),
        (Permutation([], size=1),
        '(0)'),
        (Permutation([], size=2),
        '(1)'),
        (Permutation([], size=10),
        '(9)'),
        (Permutation([1, 0, 2]),
        '(2)(0 1)'),
        (Permutation([1, 0, 2, 3, 4, 5]),
        '(5)(0 1)'),
        (Permutation([1, 0, 2, 3, 4, 5], size=10),
        '(9)(0 1)'),
        (Permutation([0, 1, 3, 2, 4, 5], size=10),
        '(9)(2 3)'),
    ]:
        assert str(p) == s


def test_Pi():
    assert str(pi) == "pi"


def test_Poly():
    assert str(Poly(0, x)) == "Poly(0, x, domain='ZZ')"
    assert str(Poly(1, x)) == "Poly(1, x, domain='ZZ')"
    assert str(Poly(x, x)) == "Poly(x, x, domain='ZZ')"

    assert str(Poly(2*x + 1, x)) == "Poly(2*x + 1, x, domain='ZZ')"
    assert str(Poly(2*x - 1, x)) == "Poly(2*x - 1, x, domain='ZZ')"

    assert str(Poly(-1, x)) == "Poly(-1, x, domain='ZZ')"
    assert str(Poly(-x, x)) == "Poly(-x, x, domain='ZZ')"

    assert str(Poly(-2*x + 1, x)) == "Poly(-2*x + 1, x, domain='ZZ')"
    assert str(Poly(-2*x - 1, x)) == "Poly(-2*x - 1, x, domain='ZZ')"

    assert str(Poly(x - 1, x)) == "Poly(x - 1, x, domain='ZZ')"
    assert str(Poly(2*x + x**5, x)) == "Poly(x**5 + 2*x, x, domain='ZZ')"

    assert str(Poly(3**(2*x), 3**x)) == "Poly((3**x)**2, 3**x, domain='ZZ')"
    assert str(Poly((x**2)**x)) == "Poly(((x**2)**x), (x**2)**x, domain='ZZ')"

    assert str(Poly((x + y)**3, (x + y), expand=False)
                ) == "Poly((x + y)**3, x + y, domain='ZZ')"
    assert str(Poly((x - 1)**2, (x - 1), expand=False)
                ) == "Poly((x - 1)**2, x - 1, domain='ZZ')"

    assert str(
        Poly(x**2 + 1 + y, x)) == "Poly(x**2 + y + 1, x, domain='ZZ[y]')"
    assert str(
        Poly(x**2 - 1 + y, x)) == "Poly(x**2 + y - 1, x, domain='ZZ[y]')"

    assert str(Poly(x**2 + I*x, x)) == "Poly(x**2 + I*x, x, domain='EX')"
    assert str(Poly(x**2 - I*x, x)) == "Poly(x**2 - I*x, x, domain='EX')"

    assert str(Poly(-x*y*z + x*y - 1, x, y, z)
               ) == "Poly(-x*y*z + x*y - 1, x, y, z, domain='ZZ')"
    assert str(Poly(-w*x**21*y**7*z + (1 + w)*z**3 - 2*x*z + 1, x, y, z)) == \
        "Poly(-w*x**21*y**7*z - 2*x*z + (w + 1)*z**3 + 1, x, y, z, domain='ZZ[w]')"

    assert str(Poly(x**2 + 1, x, modulus=2)) == "Poly(x**2 + 1, x, modulus=2)"
    assert str(Poly(2*x**2 + 3*x + 4, x, modulus=17)) == "Poly(2*x**2 + 3*x + 4, x, modulus=17)"


def test_PolyRing():
    assert str(ring("x", ZZ, lex)[0]) == "Polynomial ring in x over ZZ with lex order"
    assert str(ring("x,y", QQ, grlex)[0]) == "Polynomial ring in x, y over QQ with grlex order"
    assert str(ring("x,y,z", ZZ["t"], lex)[0]) == "Polynomial ring in x, y, z over ZZ[t] with lex order"


def test_FracField():
    assert str(field("x", ZZ, lex)[0]) == "Rational function field in x over ZZ with lex order"
    assert str(field("x,y", QQ, grlex)[0]) == "Rational function field in x, y over QQ with grlex order"
    assert str(field("x,y,z", ZZ["t"], lex)[0]) == "Rational function field in x, y, z over ZZ[t] with lex order"


def test_PolyElement():
    Ruv, u,v = ring("u,v", ZZ)
    Rxyz, x,y,z = ring("x,y,z", Ruv)

    assert str(x - x) == "0"
    assert str(x - 1) == "x - 1"
    assert str(x + 1) == "x + 1"
    assert str(x**2) == "x**2"
    assert str(x**(-2)) == "x**(-2)"
    assert str(x**QQ(1, 2)) == "x**(1/2)"

    assert str((u**2 + 3*u*v + 1)*x**2*y + u + 1) == "(u**2 + 3*u*v + 1)*x**2*y + u + 1"
    assert str((u**2 + 3*u*v + 1)*x**2*y + (u + 1)*x) == "(u**2 + 3*u*v + 1)*x**2*y + (u + 1)*x"
    assert str((u**2 + 3*u*v + 1)*x**2*y + (u + 1)*x + 1) == "(u**2 + 3*u*v + 1)*x**2*y + (u + 1)*x + 1"
    assert str((-u**2 + 3*u*v - 1)*x**2*y - (u + 1)*x - 1) == "-(u**2 - 3*u*v + 1)*x**2*y - (u + 1)*x - 1"

    assert str(-(v**2 + v + 1)*x + 3*u*v + 1) == "-(v**2 + v + 1)*x + 3*u*v + 1"
    assert str(-(v**2 + v + 1)*x - 3*u*v + 1) == "-(v**2 + v + 1)*x - 3*u*v + 1"


def test_FracElement():
    Fuv, u,v = field("u,v", ZZ)
    Fxyzt, x,y,z,t = field("x,y,z,t", Fuv)

    assert str(x - x) == "0"
    assert str(x - 1) == "x - 1"
    assert str(x + 1) == "x + 1"

    assert str(x/3) == "x/3"
    assert str(x/z) == "x/z"
    assert str(x*y/z) == "x*y/z"
    assert str(x/(z*t)) == "x/(z*t)"
    assert str(x*y/(z*t)) == "x*y/(z*t)"

    assert str((x - 1)/y) == "(x - 1)/y"
    assert str((x + 1)/y) == "(x + 1)/y"
    assert str((-x - 1)/y) == "(-x - 1)/y"
    assert str((x + 1)/(y*z)) == "(x + 1)/(y*z)"
    assert str(-y/(x + 1)) == "-y/(x + 1)"
    assert str(y*z/(x + 1)) == "y*z/(x + 1)"

    assert str(((u + 1)*x*y + 1)/((v - 1)*z - 1)) == "((u + 1)*x*y + 1)/((v - 1)*z - 1)"
    assert str(((u + 1)*x*y + 1)/((v - 1)*z - t*u*v - 1)) == "((u + 1)*x*y + 1)/((v - 1)*z - u*v*t - 1)"


def test_Pow():
    assert str(x**-1) == "1/x"
    assert str(x**-2) == "x**(-2)"
    assert str(x**2) == "x**2"
    assert str((x + y)**-1) == "1/(x + y)"
    assert str((x + y)**-2) == "(x + y)**(-2)"
    assert str((x + y)**2) == "(x + y)**2"
    assert str((x + y)**(1 + x)) == "(x + y)**(x + 1)"
    assert str(x**Rational(1, 3)) == "x**(1/3)"
    assert str(1/x**Rational(1, 3)) == "x**(-1/3)"
    assert str(sqrt(sqrt(x))) == "x**(1/4)"
    # not the same as x**-1
    assert str(x**-1.0) == 'x**(-1.0)'
    # see issue #2860
    assert str(Pow(S(2), -1.0, evaluate=False)) == '2**(-1.0)'


def test_sqrt():
    assert str(sqrt(x)) == "sqrt(x)"
    assert str(sqrt(x**2)) == "sqrt(x**2)"
    assert str(1/sqrt(x)) == "1/sqrt(x)"
    assert str(1/sqrt(x**2)) == "1/sqrt(x**2)"
    assert str(y/sqrt(x)) == "y/sqrt(x)"
    assert str(x**0.5) == "x**0.5"
    assert str(1/x**0.5) == "x**(-0.5)"


def test_Rational():
    n1 = Rational(1, 4)
    n2 = Rational(1, 3)
    n3 = Rational(2, 4)
    n4 = Rational(2, -4)
    n5 = Rational(0)
    n7 = Rational(3)
    n8 = Rational(-3)
    assert str(n1*n2) == "1/12"
    assert str(n1*n2) == "1/12"
    assert str(n3) == "1/2"
    assert str(n1*n3) == "1/8"
    assert str(n1 + n3) == "3/4"
    assert str(n1 + n2) == "7/12"
    assert str(n1 + n4) == "-1/4"
    assert str(n4*n4) == "1/4"
    assert str(n4 + n2) == "-1/6"
    assert str(n4 + n5) == "-1/2"
    assert str(n4*n5) == "0"
    assert str(n3 + n4) == "0"
    assert str(n1**n7) == "1/64"
    assert str(n2**n7) == "1/27"
    assert str(n2**n8) == "27"
    assert str(n7**n8) == "1/27"
    assert str(Rational("-25")) == "-25"
    assert str(Rational("1.25")) == "5/4"
    assert str(Rational("-2.6e-2")) == "-13/500"
    assert str(S("25/7")) == "25/7"
    assert str(S("-123/569")) == "-123/569"
    assert str(S("0.1[23]", rational=1)) == "61/495"
    assert str(S("5.1[666]", rational=1)) == "31/6"
    assert str(S("-5.1[666]", rational=1)) == "-31/6"
    assert str(S("0.[9]", rational=1)) == "1"
    assert str(S("-0.[9]", rational=1)) == "-1"

    assert str(sqrt(Rational(1, 4))) == "1/2"
    assert str(sqrt(Rational(1, 36))) == "1/6"

    assert str((123**25) ** Rational(1, 25)) == "123"
    assert str((123**25 + 1)**Rational(1, 25)) != "123"
    assert str((123**25 - 1)**Rational(1, 25)) != "123"
    assert str((123**25 - 1)**Rational(1, 25)) != "122"

    assert str(sqrt(Rational(81, 36))**3) == "27/8"
    assert str(1/sqrt(Rational(81, 36))**3) == "8/27"

    assert str(sqrt(-4)) == str(2*I)
    assert str(2**Rational(1, 10**10)) == "2**(1/10000000000)"

    assert sstr(Rational(2, 3), sympy_integers=True) == "S(2)/3"
    x = Symbol("x")
    assert sstr(x**Rational(2, 3), sympy_integers=True) == "x**(S(2)/3)"
    assert sstr(Eq(x, Rational(2, 3)), sympy_integers=True) == "Eq(x, S(2)/3)"
    assert sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True) == \
        "Limit(x, x, S(7)/2)"


def test_Float():
    # NOTE dps is the whole number of decimal digits
    assert str(Float('1.23', dps=1 + 2)) == '1.23'
    assert str(Float('1.23456789', dps=1 + 8)) == '1.23456789'
    assert str(
        Float('1.234567890123456789', dps=1 + 18)) == '1.234567890123456789'
    assert str(pi.evalf(1 + 2)) == '3.14'
    assert str(pi.evalf(1 + 14)) == '3.14159265358979'
    assert str(pi.evalf(1 + 64)) == ('3.141592653589793238462643383279'
                                     '5028841971693993751058209749445923')
    assert str(pi.round(-1)) == '0.'
    assert str((pi**400 - (pi**400).round(1)).n(2)) == '-0.e+88'
    assert str(Float(S.Infinity)) == 'inf'
    assert str(Float(S.NegativeInfinity)) == '-inf'


def test_Relational():
    assert str(Rel(x, y, "<")) == "x < y"
    assert str(Rel(x + y, y, "==")) == "Eq(x + y, y)"
    assert str(Rel(x, y, "!=")) == "Ne(x, y)"
    assert str(Eq(x, 1) | Eq(x, 2)) == "Eq(x, 1) | Eq(x, 2)"
    assert str(Ne(x, 1) & Ne(x, 2)) == "Ne(x, 1) & Ne(x, 2)"


def test_CRootOf():
    assert str(rootof(x**5 + 2*x - 1, 0)) == "CRootOf(x**5 + 2*x - 1, 0)"


def test_RootSum():
    f = x**5 + 2*x - 1

    assert str(
        RootSum(f, Lambda(z, z), auto=False)) == "RootSum(x**5 + 2*x - 1)"
    assert str(RootSum(f, Lambda(
        z, z**2), auto=False)) == "RootSum(x**5 + 2*x - 1, Lambda(z, z**2))"


def test_GroebnerBasis():
    assert str(groebner(
        [], x, y)) == "GroebnerBasis([], x, y, domain='ZZ', order='lex')"

    F = [x**2 - 3*y - x + 1, y**2 - 2*x + y - 1]

    assert str(groebner(F, order='grlex')) == \
        "GroebnerBasis([x**2 - x - 3*y + 1, y**2 - 2*x + y - 1], x, y, domain='ZZ', order='grlex')"
    assert str(groebner(F, order='lex')) == \
        "GroebnerBasis([2*x - y**2 - y + 1, y**4 + 2*y**3 - 3*y**2 - 16*y + 7], x, y, domain='ZZ', order='lex')"

def test_set():
    assert sstr(set()) == 'set()'
    assert sstr(frozenset()) == 'frozenset()'

    assert sstr(set([1])) == '{1}'
    assert sstr(frozenset([1])) == 'frozenset({1})'
    assert sstr(set([1, 2, 3])) == '{1, 2, 3}'
    assert sstr(frozenset([1, 2, 3])) == 'frozenset({1, 2, 3})'

    assert sstr(
        set([1, x, x**2, x**3, x**4])) == '{1, x, x**2, x**3, x**4}'
    assert sstr(
        frozenset([1, x, x**2, x**3, x**4])) == 'frozenset({1, x, x**2, x**3, x**4})'


def test_SparseMatrix():
    M = SparseMatrix([[x**+1, 1], [y, x + y]])
    assert str(M) == "Matrix([[x, 1], [y, x + y]])"
    assert sstr(M) == "Matrix([\n[x,     1],\n[y, x + y]])"


def test_Sum():
    assert str(summation(cos(3*z), (z, x, y))) == "Sum(cos(3*z), (z, x, y))"
    assert str(Sum(x*y**2, (x, -2, 2), (y, -5, 5))) == \
        "Sum(x*y**2, (x, -2, 2), (y, -5, 5))"


def test_Symbol():
    assert str(y) == "y"
    assert str(x) == "x"
    e = x
    assert str(e) == "x"


def test_tuple():
    assert str((x,)) == sstr((x,)) == "(x,)"
    assert str((x + y, 1 + x)) == sstr((x + y, 1 + x)) == "(x + y, x + 1)"
    assert str((x + y, (
        1 + x, x**2))) == sstr((x + y, (1 + x, x**2))) == "(x + y, (x + 1, x**2))"


def test_Quaternion_str_printer():
    q = Quaternion(x, y, z, t)
    assert str(q) == "x + y*i + z*j + t*k"
    q = Quaternion(x,y,z,x*t)
    assert str(q) == "x + y*i + z*j + t*x*k"
    q = Quaternion(x,y,z,x+t)
    assert str(q) == "x + y*i + z*j + (t + x)*k"


def test_Quantity_str():
    assert sstr(second, abbrev=True) == "s"
    assert sstr(joule, abbrev=True) == "J"
    assert str(second) == "second"
    assert str(joule) == "joule"


def test_wild_str():
    # Check expressions containing Wild not causing infinite recursion
    w = Wild('x')
    assert str(w + 1) == 'x_ + 1'
    assert str(exp(2**w) + 5) == 'exp(2**x_) + 5'
    assert str(3*w + 1) == '3*x_ + 1'
    assert str(1/w + 1) == '1 + 1/x_'
    assert str(w**2 + 1) == 'x_**2 + 1'
    assert str(1/(1 - w)) == '1/(1 - x_)'


def test_zeta():
    assert str(zeta(3)) == "zeta(3)"


def test_issue_3101():
    e = x - y
    a = str(e)
    b = str(e)
    assert a == b


def test_issue_3103():
    e = -2*sqrt(x) - y/sqrt(x)/2
    assert str(e) not in ["(-2)*x**1/2(-1/2)*x**(-1/2)*y",
            "-2*x**1/2(-1/2)*x**(-1/2)*y", "-2*x**1/2-1/2*x**-1/2*w"]
    assert str(e) == "-2*sqrt(x) - y/(2*sqrt(x))"


def test_issue_4021():
    e = Integral(x, x) + 1
    assert str(e) == 'Integral(x, x) + 1'


def test_sstrrepr():
    assert sstr('abc') == 'abc'
    assert sstrrepr('abc') == "'abc'"

    e = ['a', 'b', 'c', x]
    assert sstr(e) == "[a, b, c, x]"
    assert sstrrepr(e) == "['a', 'b', 'c', x]"


def test_infinity():
    assert sstr(oo*I) == "oo*I"


def test_full_prec():
    assert sstr(S("0.3"), full_prec=True) == "0.300000000000000"
    assert sstr(S("0.3"), full_prec="auto") == "0.300000000000000"
    assert sstr(S("0.3"), full_prec=False) == "0.3"
    assert sstr(S("0.3")*x, full_prec=True) in [
        "0.300000000000000*x",
        "x*0.300000000000000"
    ]
    assert sstr(S("0.3")*x, full_prec="auto") in [
        "0.3*x",
        "x*0.3"
    ]
    assert sstr(S("0.3")*x, full_prec=False) in [
        "0.3*x",
        "x*0.3"
    ]


def test_noncommutative():
    A, B, C = symbols('A,B,C', commutative=False)

    assert sstr(A*B*C**-1) == "A*B*C**(-1)"
    assert sstr(C**-1*A*B) == "C**(-1)*A*B"
    assert sstr(A*C**-1*B) == "A*C**(-1)*B"
    assert sstr(sqrt(A)) == "sqrt(A)"
    assert sstr(1/sqrt(A)) == "A**(-1/2)"


def test_empty_printer():
    str_printer = StrPrinter()
    assert str_printer.emptyPrinter("foo") == "foo"
    assert str_printer.emptyPrinter(x*y) == "x*y"
    assert str_printer.emptyPrinter(32) == "32"


def test_settings():
    raises(TypeError, lambda: sstr(S(4), method="garbage"))


def test_RandomDomain():
    from sympy.stats import Normal, Die, Exponential, pspace, where
    X = Normal('x1', 0, 1)
    assert str(where(X > 0)) == "Domain: (0 < x1) & (x1 < oo)"

    D = Die('d1', 6)
    assert str(where(D > 4)) == "Domain: Eq(d1, 5) | Eq(d1, 6)"

    A = Exponential('a', 1)
    B = Exponential('b', 1)
    assert str(pspace(Tuple(A, B)).domain) == "Domain: (0 <= a) & (0 <= b) & (a < oo) & (b < oo)"


def test_FiniteSet():
    assert str(FiniteSet(*range(1, 51))) == '{1, 2, 3, ..., 48, 49, 50}'
    assert str(FiniteSet(*range(1, 6))) == '{1, 2, 3, 4, 5}'


def test_PrettyPoly():
    from sympy.polys.domains import QQ
    F = QQ.frac_field(x, y)
    R = QQ[x, y]
    assert sstr(F.convert(x/(x + y))) == sstr(x/(x + y))
    assert sstr(R.convert(x + y)) == sstr(x + y)


def test_categories():
    from sympy.categories import (Object, NamedMorphism,
        IdentityMorphism, Category)

    A = Object("A")
    B = Object("B")

    f = NamedMorphism(A, B, "f")
    id_A = IdentityMorphism(A)

    K = Category("K")

    assert str(A) == 'Object("A")'
    assert str(f) == 'NamedMorphism(Object("A"), Object("B"), "f")'
    assert str(id_A) == 'IdentityMorphism(Object("A"))'

    assert str(K) == 'Category("K")'


def test_Tr():
    A, B = symbols('A B', commutative=False)
    t = Tr(A*B)
    assert str(t) == 'Tr(A*B)'


def test_issue_6387():
    assert str(factor(-3.0*z + 3)) == '-3.0*(1.0*z - 1.0)'


def test_MatMul_MatAdd():
    from sympy import MatrixSymbol
    assert str(2*(MatrixSymbol("X", 2, 2) + MatrixSymbol("Y", 2, 2))) == \
        "2*(X + Y)"

def test_MatrixSlice():
    from sympy.matrices.expressions import MatrixSymbol
    assert str(MatrixSymbol('X', 10, 10)[:5, 1:9:2]) == 'X[:5, 1:9:2]'
    assert str(MatrixSymbol('X', 10, 10)[5, :5:2]) == 'X[5, :5:2]'

def test_true_false():
    assert str(true) == repr(true) == sstr(true) == "True"
    assert str(false) == repr(false) == sstr(false) == "False"

def test_Equivalent():
    assert str(Equivalent(y, x)) == "Equivalent(x, y)"

def test_Xor():
    assert str(Xor(y, x, evaluate=False)) == "Xor(x, y)"

def test_Complement():
    assert str(Complement(S.Reals, S.Naturals)) == 'Reals \\ Naturals'

def test_SymmetricDifference():
    assert str(SymmetricDifference(Interval(2, 3), Interval(3, 4),evaluate=False)) == \
           'SymmetricDifference(Interval(2, 3), Interval(3, 4))'


def test_UnevaluatedExpr():
    a, b = symbols("a b")
    expr1 = 2*UnevaluatedExpr(a+b)
    assert str(expr1) == "2*(a + b)"


def test_MatrixElement_printing():
    # test cases for issue #11821
    A = MatrixSymbol("A", 1, 3)
    B = MatrixSymbol("B", 1, 3)
    C = MatrixSymbol("C", 1, 3)

    assert(str(A[0, 0]) == "A[0, 0]")
    assert(str(3 * A[0, 0]) == "3*A[0, 0]")

    F = C[0, 0].subs(C, A - B)
    assert str(F) == "(A - B)[0, 0]"


def test_MatrixSymbol_printing():
    A = MatrixSymbol("A", 3, 3)
    B = MatrixSymbol("B", 3, 3)

    assert str(A - A*B - B) == "A - A*B - B"
    assert str(A*B - (A+B)) == "-(A + B) + A*B"
    assert str(A**(-1)) == "A**(-1)"
    assert str(A**3) == "A**3"


def test_Subs_printing():
    assert str(Subs(x, (x,), (1,))) == 'Subs(x, x, 1)'
    assert str(Subs(x + y, (x, y), (1, 2))) == 'Subs(x + y, (x, y), (1, 2))'

def test_issue_15716():
    x = Symbol('x')
    e = -3**x*exp(-3)*log(3**x*exp(-3)/factorial(x))/factorial(x)
    assert str(Integral(e, (x, -oo, oo)).doit()) ==  '-(Integral(-3*3**x/factorial(x), (x, -oo, oo))' \
    ' + Integral(3**x*log(3**x/factorial(x))/factorial(x), (x, -oo, oo)))*exp(-3)'
