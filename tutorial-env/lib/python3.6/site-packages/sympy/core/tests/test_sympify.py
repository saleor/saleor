from sympy import (Symbol, exp, Integer, Float, sin, cos, log, Poly, Lambda,
    Function, I, S, N, sqrt, srepr, Rational, Tuple, Matrix, Interval, Add, Mul,
    Pow, Or, true, false, Abs, pi, Range, Xor)
from sympy.abc import x, y
from sympy.core.sympify import sympify, _sympify, SympifyError, kernS
from sympy.core.decorators import _sympifyit
from sympy.external import import_module
from sympy.utilities.pytest import raises, XFAIL, skip
from sympy.utilities.decorator import conserve_mpmath_dps
from sympy.geometry import Point, Line
from sympy.functions.combinatorial.factorials import factorial, factorial2
from sympy.abc import _clash, _clash1, _clash2
from sympy.core.compatibility import exec_, HAS_GMPY, PY3
from sympy.sets import FiniteSet, EmptySet
from sympy.tensor.array.dense_ndim_array import ImmutableDenseNDimArray
from sympy.external import import_module

import mpmath
from mpmath.rational import mpq


numpy = import_module('numpy')


def test_issue_3538():
    v = sympify("exp(x)")
    assert v == exp(x)
    assert type(v) == type(exp(x))
    assert str(type(v)) == str(type(exp(x)))


def test_sympify1():
    assert sympify("x") == Symbol("x")
    assert sympify("   x") == Symbol("x")
    assert sympify("   x   ") == Symbol("x")
    # issue 4877
    n1 = Rational(1, 2)
    assert sympify('--.5') == n1
    assert sympify('-1/2') == -n1
    assert sympify('-+--.5') == -n1
    assert sympify('-.[3]') == Rational(-1, 3)
    assert sympify('.[3]') == Rational(1, 3)
    assert sympify('+.[3]') == Rational(1, 3)
    assert sympify('+0.[3]*10**-2') == Rational(1, 300)
    assert sympify('.[052631578947368421]') == Rational(1, 19)
    assert sympify('.0[526315789473684210]') == Rational(1, 19)
    assert sympify('.034[56]') == Rational(1711, 49500)
    # options to make reals into rationals
    assert sympify('1.22[345]', rational=True) == \
        1 + Rational(22, 100) + Rational(345, 99900)
    assert sympify('2/2.6', rational=True) == Rational(10, 13)
    assert sympify('2.6/2', rational=True) == Rational(13, 10)
    assert sympify('2.6e2/17', rational=True) == Rational(260, 17)
    assert sympify('2.6e+2/17', rational=True) == Rational(260, 17)
    assert sympify('2.6e-2/17', rational=True) == Rational(26, 17000)
    assert sympify('2.1+3/4', rational=True) == \
        Rational(21, 10) + Rational(3, 4)
    assert sympify('2.234456', rational=True) == Rational(279307, 125000)
    assert sympify('2.234456e23', rational=True) == 223445600000000000000000
    assert sympify('2.234456e-23', rational=True) == \
        Rational(279307, 12500000000000000000000000000)
    assert sympify('-2.234456e-23', rational=True) == \
        Rational(-279307, 12500000000000000000000000000)
    assert sympify('12345678901/17', rational=True) == \
        Rational(12345678901, 17)
    assert sympify('1/.3 + x', rational=True) == Rational(10, 3) + x
    # make sure longs in fractions work
    assert sympify('222222222222/11111111111') == \
        Rational(222222222222, 11111111111)
    # ... even if they come from repetend notation
    assert sympify('1/.2[123456789012]') == Rational(333333333333, 70781892967)
    # ... or from high precision reals
    assert sympify('.1234567890123456', rational=True) == \
        Rational(19290123283179, 156250000000000)


def test_sympify_Fraction():
    try:
        import fractions
    except ImportError:
        pass
    else:
        value = sympify(fractions.Fraction(101, 127))
        assert value == Rational(101, 127) and type(value) is Rational


def test_sympify_gmpy():
    if HAS_GMPY:
        if HAS_GMPY == 2:
            import gmpy2 as gmpy
        elif HAS_GMPY == 1:
            import gmpy

        value = sympify(gmpy.mpz(1000001))
        assert value == Integer(1000001) and type(value) is Integer

        value = sympify(gmpy.mpq(101, 127))
        assert value == Rational(101, 127) and type(value) is Rational


@conserve_mpmath_dps
def test_sympify_mpmath():
    value = sympify(mpmath.mpf(1.0))
    assert value == Float(1.0) and type(value) is Float

    mpmath.mp.dps = 12
    assert sympify(
        mpmath.pi).epsilon_eq(Float("3.14159265359"), Float("1e-12")) == True
    assert sympify(
        mpmath.pi).epsilon_eq(Float("3.14159265359"), Float("1e-13")) == False

    mpmath.mp.dps = 6
    assert sympify(
        mpmath.pi).epsilon_eq(Float("3.14159"), Float("1e-5")) == True
    assert sympify(
        mpmath.pi).epsilon_eq(Float("3.14159"), Float("1e-6")) == False

    assert sympify(mpmath.mpc(1.0 + 2.0j)) == Float(1.0) + Float(2.0)*I

    assert sympify(mpq(1, 2)) == S.Half


def test_sympify2():
    class A:
        def _sympy_(self):
            return Symbol("x")**3

    a = A()

    assert _sympify(a) == x**3
    assert sympify(a) == x**3
    assert a == x**3


def test_sympify3():
    assert sympify("x**3") == x**3
    assert sympify("x^3") == x**3
    assert sympify("1/2") == Integer(1)/2

    raises(SympifyError, lambda: _sympify('x**3'))
    raises(SympifyError, lambda: _sympify('1/2'))


def test_sympify_keywords():
    raises(SympifyError, lambda: sympify('if'))
    raises(SympifyError, lambda: sympify('for'))
    raises(SympifyError, lambda: sympify('while'))
    raises(SympifyError, lambda: sympify('lambda'))


def test_sympify_float():
    assert sympify("1e-64") != 0
    assert sympify("1e-20000") != 0


def test_sympify_bool():
    assert sympify(True) is true
    assert sympify(False) is false


def test_sympyify_iterables():
    ans = [Rational(3, 10), Rational(1, 5)]
    assert sympify(['.3', '.2'], rational=True) == ans
    assert sympify(tuple(['.3', '.2']), rational=True) == Tuple(*ans)
    assert sympify(dict(x=0, y=1)) == {x: 0, y: 1}
    assert sympify(['1', '2', ['3', '4']]) == [S(1), S(2), [S(3), S(4)]]


def test_sympify4():
    class A:
        def _sympy_(self):
            return Symbol("x")

    a = A()

    assert _sympify(a)**3 == x**3
    assert sympify(a)**3 == x**3
    assert a == x


def test_sympify_text():
    assert sympify('some') == Symbol('some')
    assert sympify('core') == Symbol('core')

    assert sympify('True') is True
    assert sympify('False') is False

    assert sympify('Poly') == Poly
    assert sympify('sin') == sin


def test_sympify_function():
    assert sympify('factor(x**2-1, x)') == -(1 - x)*(x + 1)
    assert sympify('sin(pi/2)*cos(pi)') == -Integer(1)


def test_sympify_poly():
    p = Poly(x**2 + x + 1, x)

    assert _sympify(p) is p
    assert sympify(p) is p


def test_sympify_factorial():
    assert sympify('x!') == factorial(x)
    assert sympify('(x+1)!') == factorial(x + 1)
    assert sympify('(1 + y*(x + 1))!') == factorial(1 + y*(x + 1))
    assert sympify('(1 + y*(x + 1)!)^2') == (1 + y*factorial(x + 1))**2
    assert sympify('y*x!') == y*factorial(x)
    assert sympify('x!!') == factorial2(x)
    assert sympify('(x+1)!!') == factorial2(x + 1)
    assert sympify('(1 + y*(x + 1))!!') == factorial2(1 + y*(x + 1))
    assert sympify('(1 + y*(x + 1)!!)^2') == (1 + y*factorial2(x + 1))**2
    assert sympify('y*x!!') == y*factorial2(x)
    assert sympify('factorial2(x)!') == factorial(factorial2(x))

    raises(SympifyError, lambda: sympify("+!!"))
    raises(SympifyError, lambda: sympify(")!!"))
    raises(SympifyError, lambda: sympify("!"))
    raises(SympifyError, lambda: sympify("(!)"))
    raises(SympifyError, lambda: sympify("x!!!"))


def test_sage():
    # how to effectivelly test for the _sage_() method without having SAGE
    # installed?
    assert hasattr(x, "_sage_")
    assert hasattr(Integer(3), "_sage_")
    assert hasattr(sin(x), "_sage_")
    assert hasattr(cos(x), "_sage_")
    assert hasattr(x**2, "_sage_")
    assert hasattr(x + y, "_sage_")
    assert hasattr(exp(x), "_sage_")
    assert hasattr(log(x), "_sage_")


def test_issue_3595():
    assert sympify("a_") == Symbol("a_")
    assert sympify("_a") == Symbol("_a")


def test_lambda():
    x = Symbol('x')
    assert sympify('lambda: 1') == Lambda((), 1)
    assert sympify('lambda x: x') == Lambda(x, x)
    assert sympify('lambda x: 2*x') == Lambda(x, 2*x)
    assert sympify('lambda x, y: 2*x+y') == Lambda([x, y], 2*x + y)


def test_lambda_raises():
    raises(SympifyError, lambda: sympify("lambda *args: args")) # args argument error
    raises(SympifyError, lambda: sympify("lambda **kwargs: kwargs[0]")) # kwargs argument error
    raises(SympifyError, lambda: sympify("lambda x = 1: x"))    # Keyword argument error
    with raises(SympifyError):
        _sympify('lambda: 1')


def test_sympify_raises():
    raises(SympifyError, lambda: sympify("fx)"))


def test__sympify():
    x = Symbol('x')
    f = Function('f')

    # positive _sympify
    assert _sympify(x) is x
    assert _sympify(f) is f
    assert _sympify(1) == Integer(1)
    assert _sympify(0.5) == Float("0.5")
    assert _sympify(1 + 1j) == 1.0 + I*1.0

    class A:
        def _sympy_(self):
            return Integer(5)

    a = A()
    assert _sympify(a) == Integer(5)

    # negative _sympify
    raises(SympifyError, lambda: _sympify('1'))
    raises(SympifyError, lambda: _sympify([1, 2, 3]))


def test_sympifyit():
    x = Symbol('x')
    y = Symbol('y')

    @_sympifyit('b', NotImplemented)
    def add(a, b):
        return a + b

    assert add(x, 1) == x + 1
    assert add(x, 0.5) == x + Float('0.5')
    assert add(x, y) == x + y

    assert add(x, '1') == NotImplemented

    @_sympifyit('b')
    def add_raises(a, b):
        return a + b

    assert add_raises(x, 1) == x + 1
    assert add_raises(x, 0.5) == x + Float('0.5')
    assert add_raises(x, y) == x + y

    raises(SympifyError, lambda: add_raises(x, '1'))


def test_int_float():
    class F1_1(object):
        def __float__(self):
            return 1.1

    class F1_1b(object):
        """
        This class is still a float, even though it also implements __int__().
        """
        def __float__(self):
            return 1.1

        def __int__(self):
            return 1

    class F1_1c(object):
        """
        This class is still a float, because it implements _sympy_()
        """
        def __float__(self):
            return 1.1

        def __int__(self):
            return 1

        def _sympy_(self):
            return Float(1.1)

    class I5(object):
        def __int__(self):
            return 5

    class I5b(object):
        """
        This class implements both __int__() and __float__(), so it will be
        treated as Float in SymPy. One could change this behavior, by using
        float(a) == int(a), but deciding that integer-valued floats represent
        exact numbers is arbitrary and often not correct, so we do not do it.
        If, in the future, we decide to do it anyway, the tests for I5b need to
        be changed.
        """
        def __float__(self):
            return 5.0

        def __int__(self):
            return 5

    class I5c(object):
        """
        This class implements both __int__() and __float__(), but also
        a _sympy_() method, so it will be Integer.
        """
        def __float__(self):
            return 5.0

        def __int__(self):
            return 5

        def _sympy_(self):
            return Integer(5)

    i5 = I5()
    i5b = I5b()
    i5c = I5c()
    f1_1 = F1_1()
    f1_1b = F1_1b()
    f1_1c = F1_1c()
    assert sympify(i5) == 5
    assert isinstance(sympify(i5), Integer)
    assert sympify(i5b) == 5
    assert isinstance(sympify(i5b), Float)
    assert sympify(i5c) == 5
    assert isinstance(sympify(i5c), Integer)
    assert abs(sympify(f1_1) - 1.1) < 1e-5
    assert abs(sympify(f1_1b) - 1.1) < 1e-5
    assert abs(sympify(f1_1c) - 1.1) < 1e-5

    assert _sympify(i5) == 5
    assert isinstance(_sympify(i5), Integer)
    assert _sympify(i5b) == 5
    assert isinstance(_sympify(i5b), Float)
    assert _sympify(i5c) == 5
    assert isinstance(_sympify(i5c), Integer)
    assert abs(_sympify(f1_1) - 1.1) < 1e-5
    assert abs(_sympify(f1_1b) - 1.1) < 1e-5
    assert abs(_sympify(f1_1c) - 1.1) < 1e-5


def test_evaluate_false():
    cases = {
        '2 + 3': Add(2, 3, evaluate=False),
        '2**2 / 3': Mul(Pow(2, 2, evaluate=False), Pow(3, -1, evaluate=False), evaluate=False),
        '2 + 3 * 5': Add(2, Mul(3, 5, evaluate=False), evaluate=False),
        '2 - 3 * 5': Add(2, Mul(-1, Mul(3, 5,evaluate=False), evaluate=False), evaluate=False),
        '1 / 3': Mul(1, Pow(3, -1, evaluate=False), evaluate=False),
        'True | False': Or(True, False, evaluate=False),
        '1 + 2 + 3 + 5*3 + integrate(x)': Add(1, 2, 3, Mul(5, 3, evaluate=False), x**2/2, evaluate=False),
        '2 * 4 * 6 + 8': Add(Mul(2, 4, 6, evaluate=False), 8, evaluate=False),
        '2 - 8 / 4': Add(2, Mul(-1, Mul(8, Pow(4, -1, evaluate=False), evaluate=False), evaluate=False), evaluate=False),
        '2 - 2**2': Add(2, Mul(-1, Pow(2, 2, evaluate=False), evaluate=False), evaluate=False),
    }
    for case, result in cases.items():
        assert sympify(case, evaluate=False) == result


def test_issue_4133():
    a = sympify('Integer(4)')

    assert a == Integer(4)
    assert a.is_Integer


def test_issue_3982():
    a = [3, 2.0]
    assert sympify(a) == [Integer(3), Float(2.0)]
    assert sympify(tuple(a)) == Tuple(Integer(3), Float(2.0))
    assert sympify(set(a)) == FiniteSet(Integer(3), Float(2.0))


def test_S_sympify():
    assert S(1)/2 == sympify(1)/2
    assert (-2)**(S(1)/2) == sqrt(2)*I


def test_issue_4788():
    assert srepr(S(1.0 + 0J)) == srepr(S(1.0)) == srepr(Float(1.0))


def test_issue_4798_None():
    assert S(None) is None


def test_issue_3218():
    assert sympify("x+\ny") == x + y


def test_issue_4988_builtins():
    C = Symbol('C')
    vars = {'C': C}
    exp1 = sympify('C')
    assert exp1 == C  # Make sure it did not get mixed up with sympy.C

    exp2 = sympify('C', vars)
    assert exp2 == C  # Make sure it did not get mixed up with sympy.C


def test_geometry():
    p = sympify(Point(0, 1))
    assert p == Point(0, 1) and isinstance(p, Point)
    L = sympify(Line(p, (1, 0)))
    assert L == Line((0, 1), (1, 0)) and isinstance(L, Line)


def test_kernS():
    s =   '-1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x)))'
    # when 1497 is fixed, this no longer should pass: the expression
    # should be unchanged
    assert -1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x))) == -1
    # sympification should not allow the constant to enter a Mul
    # or else the structure can change dramatically
    ss = kernS(s)
    assert ss != -1 and ss.simplify() == -1
    s = '-1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x)))'.replace(
        'x', '_kern')
    ss = kernS(s)
    assert ss != -1 and ss.simplify() == -1
    # issue 6687
    assert kernS('Interval(-1,-2 - 4*(-3))') == Interval(-1, 10)
    assert kernS('_kern') == Symbol('_kern')
    assert kernS('E**-(x)') == exp(-x)
    e = 2*(x + y)*y
    assert kernS(['2*(x + y)*y', ('2*(x + y)*y',)]) == [e, (e,)]
    assert kernS('-(2*sin(x)**2 + 2*sin(x)*cos(x))*y/2') == \
        -y*(2*sin(x)**2 + 2*sin(x)*cos(x))/2
    # issue 15132
    assert kernS('(1 - x)/(1 - x*(1-y))') == kernS('(1-x)/(1-(1-y)*x)')
    assert kernS('(1-2**-(4+1)*(1-y)*x)') == (1 - x*(1 - y)/32)
    assert kernS('(1-2**(4+1)*(1-y)*x)') == (1 - 32*x*(1 - y))
    assert kernS('(1-2.*(1-y)*x)') == 1 - 2.*x*(1 - y)
    one = kernS('x - (x - 1)')
    assert one != 1 and one.expand() == 1


def test_issue_6540_6552():
    assert S('[[1/3,2], (2/5,)]') == [[Rational(1, 3), 2], (Rational(2, 5),)]
    assert S('[[2/6,2], (2/4,)]') == [[Rational(1, 3), 2], (Rational(1, 2),)]
    assert S('[[[2*(1)]]]') == [[[2]]]
    assert S('Matrix([2*(1)])') == Matrix([2])


def test_issue_6046():
    assert str(S("Q & C", locals=_clash1)) == 'C & Q'
    assert str(S('pi(x)', locals=_clash2)) == 'pi(x)'
    assert str(S('pi(C, Q)', locals=_clash)) == 'pi(C, Q)'
    locals = {}
    exec_("from sympy.abc import Q, C", locals)
    assert str(S('C&Q', locals)) == 'C & Q'


def test_issue_8821_highprec_from_str():
    s = str(pi.evalf(128))
    p = sympify(s)
    assert Abs(sin(p)) < 1e-127


def test_issue_10295():
    if not numpy:
        skip("numpy not installed.")

    A = numpy.array([[1, 3, -1],
                     [0, 1, 7]])
    sA = S(A)
    assert sA.shape == (2, 3)
    for (ri, ci), val in numpy.ndenumerate(A):
        assert sA[ri, ci] == val

    B = numpy.array([-7, x, 3*y**2])
    sB = S(B)
    assert B[0] == -7
    assert B[1] == x
    assert B[2] == 3*y**2

    C = numpy.arange(0, 24)
    C.resize(2,3,4)
    sC = S(C)
    assert sC[0, 0, 0].is_integer
    assert sC[0, 0, 0] == 0

    a1 = numpy.array([1, 2, 3])
    a2 = numpy.array([i for i in range(24)])
    a2.resize(2, 4, 3)
    assert sympify(a1) == ImmutableDenseNDimArray([1, 2, 3])
    assert sympify(a2) == ImmutableDenseNDimArray([i for i in range(24)], (2, 4, 3))


def test_Range():
    # Only works in Python 3 where range returns a range type
    if PY3:
        builtin_range = range
    else:
        builtin_range = xrange

    assert sympify(builtin_range(10)) == Range(10)
    assert _sympify(builtin_range(10)) == Range(10)


def test_sympify_set():
    n = Symbol('n')
    assert sympify({n}) == FiniteSet(n)
    assert sympify(set()) == EmptySet()


def test_sympify_numpy():
    if not numpy:
        skip('numpy not installed. Abort numpy tests.')
    np = numpy

    def equal(x, y):
        return x == y and type(x) == type(y)

    assert sympify(np.bool_(1)) is S(True)
    try:
        assert equal(
            sympify(np.int_(1234567891234567891)), S(1234567891234567891))
        assert equal(
            sympify(np.intp(1234567891234567891)), S(1234567891234567891))
    except OverflowError:
        # May fail on 32-bit systems: Python int too large to convert to C long
        pass
    assert equal(sympify(np.intc(1234567891)), S(1234567891))
    assert equal(sympify(np.int8(-123)), S(-123))
    assert equal(sympify(np.int16(-12345)), S(-12345))
    assert equal(sympify(np.int32(-1234567891)), S(-1234567891))
    assert equal(
        sympify(np.int64(-1234567891234567891)), S(-1234567891234567891))
    assert equal(sympify(np.uint8(123)), S(123))
    assert equal(sympify(np.uint16(12345)), S(12345))
    assert equal(sympify(np.uint32(1234567891)), S(1234567891))
    assert equal(
        sympify(np.uint64(1234567891234567891)), S(1234567891234567891))
    assert equal(sympify(np.float32(1.123456)), Float(1.123456, precision=24))
    assert equal(sympify(np.float64(1.1234567891234)),
                Float(1.1234567891234, precision=53))
    assert equal(sympify(np.longdouble(1.123456789)),
                 Float(1.123456789, precision=80))
    assert equal(sympify(np.complex64(1 + 2j)), S(1.0 + 2.0*I))
    assert equal(sympify(np.complex128(1 + 2j)), S(1.0 + 2.0*I))
    assert equal(sympify(np.longcomplex(1 + 2j)), S(1.0 + 2.0*I))

    #float96 does not exist on all platforms
    if hasattr(np, 'float96'):
        assert equal(sympify(np.float96(1.123456789)),
                    Float(1.123456789, precision=80))
    #float128 does not exist on all platforms
    if hasattr(np, 'float128'):
        assert equal(sympify(np.float128(1.123456789123)),
                    Float(1.123456789123, precision=80))


@XFAIL
def test_sympify_rational_numbers_set():
    ans = [Rational(3, 10), Rational(1, 5)]
    assert sympify({'.3', '.2'}, rational=True) == FiniteSet(*ans)


def test_issue_13924():
    if not numpy:
        skip("numpy not installed.")

    a = sympify(numpy.array([1]))
    assert isinstance(a, ImmutableDenseNDimArray)
    assert a[0] == 1

def test_numpy_sympify_args():
    # Issue 15098. Make sure sympify args work with numpy types (like numpy.str_)
    if not numpy:
        skip("numpy not installed.")

    a = sympify(numpy.str_('a'))
    assert type(a) is Symbol
    assert a == Symbol('a')

    class CustomSymbol(Symbol):
        pass

    a = sympify(numpy.str_('a'), {"Symbol": CustomSymbol})
    assert isinstance(a, CustomSymbol)

    a = sympify(numpy.str_('x^y'))
    assert a == x**y
    a = sympify(numpy.str_('x^y'), convert_xor=False)
    assert a == Xor(x, y)

    raises(SympifyError, lambda: sympify(numpy.str_('x'), strict=True))

    a = sympify(numpy.str_('1.1'))
    assert isinstance(a, Float)
    assert a == 1.1

    a = sympify(numpy.str_('1.1'), rational=True)
    assert isinstance(a, Rational)
    assert a == Rational(11, 10)

    a = sympify(numpy.str_('x + x'))
    assert isinstance(a, Mul)
    assert a == 2*x

    a = sympify(numpy.str_('x + x'), evaluate=False)
    assert isinstance(a, Add)
    assert a == Add(x, x, evaluate=False)


def test_issue_5939():
     a = Symbol('a')
     b = Symbol('b')
     assert sympify('''a+\nb''') == a + b
