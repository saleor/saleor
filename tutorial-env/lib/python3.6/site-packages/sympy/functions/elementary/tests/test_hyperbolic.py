from sympy import (symbols, Symbol, sinh, nan, oo, zoo, pi, asinh, acosh, log,
    sqrt, coth, I, cot, E, tanh, tan, cosh, cos, S, sin, Rational, atanh, acoth,
    Integer, O, exp, sech, sec, csch, asech, acsch, acos, asin, expand_mul,
    AccumBounds)

from sympy.utilities.pytest import raises


def test_sinh():
    x, y = symbols('x,y')

    k = Symbol('k', integer=True)

    assert sinh(nan) == nan
    assert sinh(zoo) == nan

    assert sinh(oo) == oo
    assert sinh(-oo) == -oo

    assert sinh(0) == 0

    assert sinh(1) == sinh(1)
    assert sinh(-1) == -sinh(1)

    assert sinh(x) == sinh(x)
    assert sinh(-x) == -sinh(x)

    assert sinh(pi) == sinh(pi)
    assert sinh(-pi) == -sinh(pi)

    assert sinh(2**1024 * E) == sinh(2**1024 * E)
    assert sinh(-2**1024 * E) == -sinh(2**1024 * E)

    assert sinh(pi*I) == 0
    assert sinh(-pi*I) == 0
    assert sinh(2*pi*I) == 0
    assert sinh(-2*pi*I) == 0
    assert sinh(-3*10**73*pi*I) == 0
    assert sinh(7*10**103*pi*I) == 0

    assert sinh(pi*I/2) == I
    assert sinh(-pi*I/2) == -I
    assert sinh(5*pi*I/2) == I
    assert sinh(7*pi*I/2) == -I

    assert sinh(pi*I/3) == S.Half*sqrt(3)*I
    assert sinh(-2*pi*I/3) == -S.Half*sqrt(3)*I

    assert sinh(pi*I/4) == S.Half*sqrt(2)*I
    assert sinh(-pi*I/4) == -S.Half*sqrt(2)*I
    assert sinh(17*pi*I/4) == S.Half*sqrt(2)*I
    assert sinh(-3*pi*I/4) == -S.Half*sqrt(2)*I

    assert sinh(pi*I/6) == S.Half*I
    assert sinh(-pi*I/6) == -S.Half*I
    assert sinh(7*pi*I/6) == -S.Half*I
    assert sinh(-5*pi*I/6) == -S.Half*I

    assert sinh(pi*I/105) == sin(pi/105)*I
    assert sinh(-pi*I/105) == -sin(pi/105)*I

    assert sinh(2 + 3*I) == sinh(2 + 3*I)

    assert sinh(x*I) == sin(x)*I

    assert sinh(k*pi*I) == 0
    assert sinh(17*k*pi*I) == 0

    assert sinh(k*pi*I/2) == sin(k*pi/2)*I


def test_sinh_series():
    x = Symbol('x')
    assert sinh(x).series(x, 0, 10) == \
        x + x**3/6 + x**5/120 + x**7/5040 + x**9/362880 + O(x**10)


def test_cosh():
    x, y = symbols('x,y')

    k = Symbol('k', integer=True)

    assert cosh(nan) == nan
    assert cosh(zoo) == nan

    assert cosh(oo) == oo
    assert cosh(-oo) == oo

    assert cosh(0) == 1

    assert cosh(1) == cosh(1)
    assert cosh(-1) == cosh(1)

    assert cosh(x) == cosh(x)
    assert cosh(-x) == cosh(x)

    assert cosh(pi*I) == cos(pi)
    assert cosh(-pi*I) == cos(pi)

    assert cosh(2**1024 * E) == cosh(2**1024 * E)
    assert cosh(-2**1024 * E) == cosh(2**1024 * E)

    assert cosh(pi*I/2) == 0
    assert cosh(-pi*I/2) == 0
    assert cosh((-3*10**73 + 1)*pi*I/2) == 0
    assert cosh((7*10**103 + 1)*pi*I/2) == 0

    assert cosh(pi*I) == -1
    assert cosh(-pi*I) == -1
    assert cosh(5*pi*I) == -1
    assert cosh(8*pi*I) == 1

    assert cosh(pi*I/3) == S.Half
    assert cosh(-2*pi*I/3) == -S.Half

    assert cosh(pi*I/4) == S.Half*sqrt(2)
    assert cosh(-pi*I/4) == S.Half*sqrt(2)
    assert cosh(11*pi*I/4) == -S.Half*sqrt(2)
    assert cosh(-3*pi*I/4) == -S.Half*sqrt(2)

    assert cosh(pi*I/6) == S.Half*sqrt(3)
    assert cosh(-pi*I/6) == S.Half*sqrt(3)
    assert cosh(7*pi*I/6) == -S.Half*sqrt(3)
    assert cosh(-5*pi*I/6) == -S.Half*sqrt(3)

    assert cosh(pi*I/105) == cos(pi/105)
    assert cosh(-pi*I/105) == cos(pi/105)

    assert cosh(2 + 3*I) == cosh(2 + 3*I)

    assert cosh(x*I) == cos(x)

    assert cosh(k*pi*I) == cos(k*pi)
    assert cosh(17*k*pi*I) == cos(17*k*pi)

    assert cosh(k*pi) == cosh(k*pi)


def test_cosh_series():
    x = Symbol('x')
    assert cosh(x).series(x, 0, 10) == \
        1 + x**2/2 + x**4/24 + x**6/720 + x**8/40320 + O(x**10)


def test_tanh():
    x, y = symbols('x,y')

    k = Symbol('k', integer=True)

    assert tanh(nan) == nan
    assert tanh(zoo) == nan

    assert tanh(oo) == 1
    assert tanh(-oo) == -1

    assert tanh(0) == 0

    assert tanh(1) == tanh(1)
    assert tanh(-1) == -tanh(1)

    assert tanh(x) == tanh(x)
    assert tanh(-x) == -tanh(x)

    assert tanh(pi) == tanh(pi)
    assert tanh(-pi) == -tanh(pi)

    assert tanh(2**1024 * E) == tanh(2**1024 * E)
    assert tanh(-2**1024 * E) == -tanh(2**1024 * E)

    assert tanh(pi*I) == 0
    assert tanh(-pi*I) == 0
    assert tanh(2*pi*I) == 0
    assert tanh(-2*pi*I) == 0
    assert tanh(-3*10**73*pi*I) == 0
    assert tanh(7*10**103*pi*I) == 0

    assert tanh(pi*I/2) == tanh(pi*I/2)
    assert tanh(-pi*I/2) == -tanh(pi*I/2)
    assert tanh(5*pi*I/2) == tanh(5*pi*I/2)
    assert tanh(7*pi*I/2) == tanh(7*pi*I/2)

    assert tanh(pi*I/3) == sqrt(3)*I
    assert tanh(-2*pi*I/3) == sqrt(3)*I

    assert tanh(pi*I/4) == I
    assert tanh(-pi*I/4) == -I
    assert tanh(17*pi*I/4) == I
    assert tanh(-3*pi*I/4) == I

    assert tanh(pi*I/6) == I/sqrt(3)
    assert tanh(-pi*I/6) == -I/sqrt(3)
    assert tanh(7*pi*I/6) == I/sqrt(3)
    assert tanh(-5*pi*I/6) == I/sqrt(3)

    assert tanh(pi*I/105) == tan(pi/105)*I
    assert tanh(-pi*I/105) == -tan(pi/105)*I

    assert tanh(2 + 3*I) == tanh(2 + 3*I)

    assert tanh(x*I) == tan(x)*I

    assert tanh(k*pi*I) == 0
    assert tanh(17*k*pi*I) == 0

    assert tanh(k*pi*I/2) == tan(k*pi/2)*I


def test_tanh_series():
    x = Symbol('x')
    assert tanh(x).series(x, 0, 10) == \
        x - x**3/3 + 2*x**5/15 - 17*x**7/315 + 62*x**9/2835 + O(x**10)


def test_coth():
    x, y = symbols('x,y')

    k = Symbol('k', integer=True)

    assert coth(nan) == nan
    assert coth(zoo) == nan

    assert coth(oo) == 1
    assert coth(-oo) == -1

    assert coth(0) == coth(0)
    assert coth(0) == zoo
    assert coth(1) == coth(1)
    assert coth(-1) == -coth(1)

    assert coth(x) == coth(x)
    assert coth(-x) == -coth(x)

    assert coth(pi*I) == -I*cot(pi)
    assert coth(-pi*I) == cot(pi)*I

    assert coth(2**1024 * E) == coth(2**1024 * E)
    assert coth(-2**1024 * E) == -coth(2**1024 * E)

    assert coth(pi*I) == -I*cot(pi)
    assert coth(-pi*I) == I*cot(pi)
    assert coth(2*pi*I) == -I*cot(2*pi)
    assert coth(-2*pi*I) == I*cot(2*pi)
    assert coth(-3*10**73*pi*I) == I*cot(3*10**73*pi)
    assert coth(7*10**103*pi*I) == -I*cot(7*10**103*pi)

    assert coth(pi*I/2) == 0
    assert coth(-pi*I/2) == 0
    assert coth(5*pi*I/2) == 0
    assert coth(7*pi*I/2) == 0

    assert coth(pi*I/3) == -I/sqrt(3)
    assert coth(-2*pi*I/3) == -I/sqrt(3)

    assert coth(pi*I/4) == -I
    assert coth(-pi*I/4) == I
    assert coth(17*pi*I/4) == -I
    assert coth(-3*pi*I/4) == -I

    assert coth(pi*I/6) == -sqrt(3)*I
    assert coth(-pi*I/6) == sqrt(3)*I
    assert coth(7*pi*I/6) == -sqrt(3)*I
    assert coth(-5*pi*I/6) == -sqrt(3)*I

    assert coth(pi*I/105) == -cot(pi/105)*I
    assert coth(-pi*I/105) == cot(pi/105)*I

    assert coth(2 + 3*I) == coth(2 + 3*I)

    assert coth(x*I) == -cot(x)*I

    assert coth(k*pi*I) == -cot(k*pi)*I
    assert coth(17*k*pi*I) == -cot(17*k*pi)*I

    assert coth(k*pi*I) == -cot(k*pi)*I

    assert coth(log(tan(2))) == coth(log(-tan(2)))
    assert coth(1 + I*pi/2) == tanh(1)

def test_coth_series():
    x = Symbol('x')
    assert coth(x).series(x, 0, 8) == \
        1/x + x/3 - x**3/45 + 2*x**5/945 - x**7/4725 + O(x**8)


def test_csch():
    x, y = symbols('x,y')

    k = Symbol('k', integer=True)
    n = Symbol('n', positive=True)

    assert csch(nan) == nan
    assert csch(zoo) == nan

    assert csch(oo) == 0
    assert csch(-oo) == 0

    assert csch(0) == zoo

    assert csch(-1) == -csch(1)

    assert csch(-x) == -csch(x)
    assert csch(-pi) == -csch(pi)
    assert csch(-2**1024 * E) == -csch(2**1024 * E)

    assert csch(pi*I) == zoo
    assert csch(-pi*I) == zoo
    assert csch(2*pi*I) == zoo
    assert csch(-2*pi*I) == zoo
    assert csch(-3*10**73*pi*I) == zoo
    assert csch(7*10**103*pi*I) == zoo

    assert csch(pi*I/2) == -I
    assert csch(-pi*I/2) == I
    assert csch(5*pi*I/2) == -I
    assert csch(7*pi*I/2) == I

    assert csch(pi*I/3) == -2/sqrt(3)*I
    assert csch(-2*pi*I/3) == 2/sqrt(3)*I

    assert csch(pi*I/4) == -sqrt(2)*I
    assert csch(-pi*I/4) == sqrt(2)*I
    assert csch(7*pi*I/4) == sqrt(2)*I
    assert csch(-3*pi*I/4) == sqrt(2)*I

    assert csch(pi*I/6) == -2*I
    assert csch(-pi*I/6) == 2*I
    assert csch(7*pi*I/6) == 2*I
    assert csch(-7*pi*I/6) == -2*I
    assert csch(-5*pi*I/6) == 2*I

    assert csch(pi*I/105) == -1/sin(pi/105)*I
    assert csch(-pi*I/105) == 1/sin(pi/105)*I

    assert csch(x*I) == -1/sin(x)*I

    assert csch(k*pi*I) == zoo
    assert csch(17*k*pi*I) == zoo

    assert csch(k*pi*I/2) == -1/sin(k*pi/2)*I

    assert csch(n).is_real is True


def test_csch_series():
    x = Symbol('x')
    assert csch(x).series(x, 0, 10) == \
       1/ x - x/6 + 7*x**3/360 - 31*x**5/15120 + 127*x**7/604800 \
          - 73*x**9/3421440 + O(x**10)


def test_sech():
    x, y = symbols('x, y')

    k = Symbol('k', integer=True)
    n = Symbol('n', positive=True)

    assert sech(nan) == nan
    assert sech(zoo) == nan

    assert sech(oo) == 0
    assert sech(-oo) == 0

    assert sech(0) == 1

    assert sech(-1) == sech(1)
    assert sech(-x) == sech(x)

    assert sech(pi*I) == sec(pi)

    assert sech(-pi*I) == sec(pi)
    assert sech(-2**1024 * E) == sech(2**1024 * E)

    assert sech(pi*I/2) == zoo
    assert sech(-pi*I/2) == zoo
    assert sech((-3*10**73 + 1)*pi*I/2) == zoo
    assert sech((7*10**103 + 1)*pi*I/2) == zoo

    assert sech(pi*I) == -1
    assert sech(-pi*I) == -1
    assert sech(5*pi*I) == -1
    assert sech(8*pi*I) == 1

    assert sech(pi*I/3) == 2
    assert sech(-2*pi*I/3) == -2

    assert sech(pi*I/4) == sqrt(2)
    assert sech(-pi*I/4) == sqrt(2)
    assert sech(5*pi*I/4) == -sqrt(2)
    assert sech(-5*pi*I/4) == -sqrt(2)

    assert sech(pi*I/6) == 2/sqrt(3)
    assert sech(-pi*I/6) == 2/sqrt(3)
    assert sech(7*pi*I/6) == -2/sqrt(3)
    assert sech(-5*pi*I/6) == -2/sqrt(3)

    assert sech(pi*I/105) == 1/cos(pi/105)
    assert sech(-pi*I/105) == 1/cos(pi/105)

    assert sech(x*I) == 1/cos(x)

    assert sech(k*pi*I) == 1/cos(k*pi)
    assert sech(17*k*pi*I) == 1/cos(17*k*pi)

    assert sech(n).is_real is True


def test_sech_series():
    x = Symbol('x')
    assert sech(x).series(x, 0, 10) == \
        1 - x**2/2 + 5*x**4/24 - 61*x**6/720 + 277*x**8/8064 + O(x**10)


def test_asinh():
    x, y = symbols('x,y')
    assert asinh(x) == asinh(x)
    assert asinh(-x) == -asinh(x)

    #at specific points
    assert asinh(nan) == nan
    assert asinh( 0) == 0
    assert asinh(+1) == log(sqrt(2) + 1)

    assert asinh(-1) == log(sqrt(2) - 1)
    assert asinh(I) == pi*I/2
    assert asinh(-I) == -pi*I/2
    assert asinh(I/2) == pi*I/6
    assert asinh(-I/2) == -pi*I/6

    # at infinites
    assert asinh(oo) == oo
    assert asinh(-oo) == -oo

    assert asinh(I*oo) == oo
    assert asinh(-I *oo) == -oo

    assert asinh(zoo) == zoo

    #properties
    assert asinh(I *(sqrt(3) - 1)/(2**(S(3)/2))) == pi*I/12
    assert asinh(-I *(sqrt(3) - 1)/(2**(S(3)/2))) == -pi*I/12

    assert asinh(I*(sqrt(5) - 1)/4) == pi*I/10
    assert asinh(-I*(sqrt(5) - 1)/4) == -pi*I/10

    assert asinh(I*(sqrt(5) + 1)/4) == 3*pi*I/10
    assert asinh(-I*(sqrt(5) + 1)/4) == -3*pi*I/10


def test_asinh_rewrite():
    x = Symbol('x')
    assert asinh(x).rewrite(log) == log(x + sqrt(x**2 + 1))


def test_asinh_series():
    x = Symbol('x')
    assert asinh(x).series(x, 0, 8) == \
        x - x**3/6 + 3*x**5/40 - 5*x**7/112 + O(x**8)
    t5 = asinh(x).taylor_term(5, x)
    assert t5 == 3*x**5/40
    assert asinh(x).taylor_term(7, x, t5, 0) == -5*x**7/112


def test_acosh():
    x = Symbol('x')

    assert acosh(-x) == acosh(-x)

    #at specific points
    assert acosh(1) == 0
    assert acosh(-1) == pi*I
    assert acosh(0) == I*pi/2
    assert acosh(Rational(1, 2)) == I*pi/3
    assert acosh(Rational(-1, 2)) == 2*pi*I/3

    # at infinites
    assert acosh(oo) == oo
    assert acosh(-oo) == oo

    assert acosh(I*oo) == oo + I*pi/2
    assert acosh(-I*oo) == oo - I*pi/2

    assert acosh(zoo) == zoo

    assert acosh(I) == log(I*(1 + sqrt(2)))
    assert acosh(-I) == log(-I*(1 + sqrt(2)))
    assert acosh((sqrt(3) - 1)/(2*sqrt(2))) == 5*pi*I/12
    assert acosh(-(sqrt(3) - 1)/(2*sqrt(2))) == 7*pi*I/12
    assert acosh(sqrt(2)/2) == I*pi/4
    assert acosh(-sqrt(2)/2) == 3*I*pi/4
    assert acosh(sqrt(3)/2) == I*pi/6
    assert acosh(-sqrt(3)/2) == 5*I*pi/6
    assert acosh(sqrt(2 + sqrt(2))/2) == I*pi/8
    assert acosh(-sqrt(2 + sqrt(2))/2) == 7*I*pi/8
    assert acosh(sqrt(2 - sqrt(2))/2) == 3*I*pi/8
    assert acosh(-sqrt(2 - sqrt(2))/2) == 5*I*pi/8
    assert acosh((1 + sqrt(3))/(2*sqrt(2))) == I*pi/12
    assert acosh(-(1 + sqrt(3))/(2*sqrt(2))) == 11*I*pi/12
    assert acosh((sqrt(5) + 1)/4) == I*pi/5
    assert acosh(-(sqrt(5) + 1)/4) == 4*I*pi/5

    assert str(acosh(5*I).n(6)) == '2.31244 + 1.5708*I'
    assert str(acosh(-5*I).n(6)) == '2.31244 - 1.5708*I'


def test_acosh_rewrite():
    x = Symbol('x')
    assert acosh(x).rewrite(log) == log(x + sqrt(x - 1)*sqrt(x + 1))


def test_acosh_series():
    x = Symbol('x')
    assert acosh(x).series(x, 0, 8) == \
        -I*x + pi*I/2 - I*x**3/6 - 3*I*x**5/40 - 5*I*x**7/112 + O(x**8)
    t5 = acosh(x).taylor_term(5, x)
    assert t5 == - 3*I*x**5/40
    assert acosh(x).taylor_term(7, x, t5, 0) == - 5*I*x**7/112


def test_asech():
    x = Symbol('x')

    assert asech(-x) == asech(-x)

    # values at fixed points
    assert asech(1) == 0
    assert asech(-1) == pi*I
    assert asech(0) == oo
    assert asech(2) == I*pi/3
    assert asech(-2) == 2*I*pi / 3

    # at infinites
    assert asech(oo) == I*pi/2
    assert asech(-oo) == I*pi/2
    assert asech(zoo) == I*AccumBounds(-pi/2, pi/2)

    assert asech(I) == log(1 + sqrt(2)) - I*pi/2
    assert asech(-I) == log(1 + sqrt(2)) + I*pi/2
    assert asech(sqrt(2) - sqrt(6)) == 11*I*pi / 12
    assert asech(sqrt(2 - 2/sqrt(5))) == I*pi / 10
    assert asech(-sqrt(2 - 2/sqrt(5))) == 9*I*pi / 10
    assert asech(2 / sqrt(2 + sqrt(2))) == I*pi / 8
    assert asech(-2 / sqrt(2 + sqrt(2))) == 7*I*pi / 8
    assert asech(sqrt(5) - 1) == I*pi / 5
    assert asech(1 - sqrt(5)) == 4*I*pi / 5
    assert asech(-sqrt(2*(2 + sqrt(2)))) == 5*I*pi / 8

    # properties
    # asech(x) == acosh(1/x)
    assert asech(sqrt(2)) == acosh(1/sqrt(2))
    assert asech(2/sqrt(3)) == acosh(sqrt(3)/2)
    assert asech(2/sqrt(2 + sqrt(2))) == acosh(sqrt(2 + sqrt(2))/2)
    assert asech(S(2)) == acosh(1/S(2))

    # asech(x) == I*acos(1/x)
    # (Note: the exact formula is asech(x) == +/- I*acos(1/x))
    assert asech(-sqrt(2)) == I*acos(-1/sqrt(2))
    assert asech(-2/sqrt(3)) == I*acos(-sqrt(3)/2)
    assert asech(-S(2)) == I*acos(-S.Half)
    assert asech(-2/sqrt(2)) == I*acos(-sqrt(2)/2)

    # sech(asech(x)) / x == 1
    assert expand_mul(sech(asech(sqrt(6) - sqrt(2))) / (sqrt(6) - sqrt(2))) == 1
    assert expand_mul(sech(asech(sqrt(6) + sqrt(2))) / (sqrt(6) + sqrt(2))) == 1
    assert (sech(asech(sqrt(2 + 2/sqrt(5)))) / (sqrt(2 + 2/sqrt(5)))).simplify() == 1
    assert (sech(asech(-sqrt(2 + 2/sqrt(5)))) / (-sqrt(2 + 2/sqrt(5)))).simplify() == 1
    assert (sech(asech(sqrt(2*(2 + sqrt(2))))) / (sqrt(2*(2 + sqrt(2))))).simplify() == 1
    assert expand_mul(sech(asech((1 + sqrt(5)))) / ((1 + sqrt(5)))) == 1
    assert expand_mul(sech(asech((-1 - sqrt(5)))) / ((-1 - sqrt(5)))) == 1
    assert expand_mul(sech(asech((-sqrt(6) - sqrt(2)))) / ((-sqrt(6) - sqrt(2)))) == 1

    # numerical evaluation
    assert str(asech(5*I).n(6)) == '0.19869 - 1.5708*I'
    assert str(asech(-5*I).n(6)) == '0.19869 + 1.5708*I'


def test_asech_series():
    x = Symbol('x')
    t6 = asech(x).expansion_term(6, x)
    assert t6 == -5*x**6/96
    assert asech(x).expansion_term(8, x, t6, 0) == -35*x**8/1024


def test_asech_rewrite():
    x = Symbol('x')
    assert asech(x).rewrite(log) == log(1/x + sqrt(1/x - 1) * sqrt(1/x + 1))


def test_acsch():
    x = Symbol('x')

    assert acsch(-x) == acsch(-x)
    assert acsch(x) == -acsch(-x)

    # values at fixed points
    assert acsch(1) == log(1 + sqrt(2))
    assert acsch(-1) == - log(1 + sqrt(2))
    assert acsch(0) == zoo
    assert acsch(2) == log((1+sqrt(5))/2)
    assert acsch(-2) == - log((1+sqrt(5))/2)

    assert acsch(I) == - I*pi/2
    assert acsch(-I) == I*pi/2
    assert acsch(-I*(sqrt(6) + sqrt(2))) == I*pi / 12
    assert acsch(I*(sqrt(2) + sqrt(6))) == -I*pi / 12
    assert acsch(-I*(1 + sqrt(5))) == I*pi / 10
    assert acsch(I*(1 + sqrt(5))) == -I*pi / 10
    assert acsch(-I*2 / sqrt(2 - sqrt(2))) == I*pi / 8
    assert acsch(I*2 / sqrt(2 - sqrt(2))) == -I*pi / 8
    assert acsch(-I*2) == I*pi / 6
    assert acsch(I*2) == -I*pi / 6
    assert acsch(-I*sqrt(2 + 2/sqrt(5))) == I*pi / 5
    assert acsch(I*sqrt(2 + 2/sqrt(5))) == -I*pi / 5
    assert acsch(-I*sqrt(2)) == I*pi / 4
    assert acsch(I*sqrt(2)) == -I*pi / 4
    assert acsch(-I*(sqrt(5)-1)) == 3*I*pi / 10
    assert acsch(I*(sqrt(5)-1)) == -3*I*pi / 10
    assert acsch(-I*2 / sqrt(3)) == I*pi / 3
    assert acsch(I*2 / sqrt(3)) == -I*pi / 3
    assert acsch(-I*2 / sqrt(2 + sqrt(2))) == 3*I*pi / 8
    assert acsch(I*2 / sqrt(2 + sqrt(2))) == -3*I*pi / 8
    assert acsch(-I*sqrt(2 - 2/sqrt(5))) == 2*I*pi / 5
    assert acsch(I*sqrt(2 - 2/sqrt(5))) == -2*I*pi / 5
    assert acsch(-I*(sqrt(6) - sqrt(2))) == 5*I*pi / 12
    assert acsch(I*(sqrt(6) - sqrt(2))) == -5*I*pi / 12

    # properties
    # acsch(x) == asinh(1/x)
    assert acsch(-I*sqrt(2)) == asinh(I/sqrt(2))
    assert acsch(-I*2 / sqrt(3)) == asinh(I*sqrt(3) / 2)

    # acsch(x) == -I*asin(I/x)
    assert acsch(-I*sqrt(2)) == -I*asin(-1/sqrt(2))
    assert acsch(-I*2 / sqrt(3)) == -I*asin(-sqrt(3)/2)

    # csch(acsch(x)) / x == 1
    assert expand_mul(csch(acsch(-I*(sqrt(6) + sqrt(2)))) / (-I*(sqrt(6) + sqrt(2)))) == 1
    assert expand_mul(csch(acsch(I*(1 + sqrt(5)))) / ((I*(1 + sqrt(5))))) == 1
    assert (csch(acsch(I*sqrt(2 - 2/sqrt(5)))) / (I*sqrt(2 - 2/sqrt(5)))).simplify() == 1
    assert (csch(acsch(-I*sqrt(2 - 2/sqrt(5)))) / (-I*sqrt(2 - 2/sqrt(5)))).simplify() == 1

    # numerical evaluation
    assert str(acsch(5*I+1).n(6)) == '0.0391819 - 0.193363*I'
    assert str(acsch(-5*I+1).n(6)) == '0.0391819 + 0.193363*I'


def test_acsch_infinities():
    assert acsch(oo) == 0
    assert acsch(-oo) == 0
    assert acsch(zoo) == 0


def test_acsch_rewrite():
    x = Symbol('x')
    assert acsch(x).rewrite(log) == log(1/x + sqrt(1/x**2 + 1))


def test_atanh():
    x = Symbol('x')

    #at specific points
    assert atanh(0) == 0
    assert atanh(I) == I*pi/4
    assert atanh(-I) == -I*pi/4
    assert atanh(1) == oo
    assert atanh(-1) == -oo

    # at infinites
    assert atanh(oo) == -I*pi/2
    assert atanh(-oo) == I*pi/2

    assert atanh(I*oo) == I*pi/2
    assert atanh(-I*oo) == -I*pi/2

    assert atanh(zoo) == I*AccumBounds(-pi/2, pi/2)

    #properties
    assert atanh(-x) == -atanh(x)

    assert atanh(I/sqrt(3)) == I*pi/6
    assert atanh(-I/sqrt(3)) == -I*pi/6
    assert atanh(I*sqrt(3)) == I*pi/3
    assert atanh(-I*sqrt(3)) == -I*pi/3
    assert atanh(I*(1 + sqrt(2))) == 3*pi*I/8
    assert atanh(I*(sqrt(2) - 1)) == pi*I/8
    assert atanh(I*(1 - sqrt(2))) == -pi*I/8
    assert atanh(-I*(1 + sqrt(2))) == -3*pi*I/8
    assert atanh(I*sqrt(5 + 2*sqrt(5))) == 2*I*pi/5
    assert atanh(-I*sqrt(5 + 2*sqrt(5))) == -2*I*pi/5
    assert atanh(I*(2 - sqrt(3))) == pi*I/12
    assert atanh(I*(sqrt(3) - 2)) == -pi*I/12
    assert atanh(oo) == -I*pi/2


def test_atanh_rewrite():
    x = Symbol('x')
    assert atanh(x).rewrite(log) == (log(1 + x) - log(1 - x)) / 2


def test_atanh_series():
    x = Symbol('x')
    assert atanh(x).series(x, 0, 10) == \
        x + x**3/3 + x**5/5 + x**7/7 + x**9/9 + O(x**10)


def test_acoth():
    x = Symbol('x')

    #at specific points
    assert acoth(0) == I*pi/2
    assert acoth(I) == -I*pi/4
    assert acoth(-I) == I*pi/4
    assert acoth(1) == oo
    assert acoth(-1) == -oo

    # at infinites
    assert acoth(oo) == 0
    assert acoth(-oo) == 0
    assert acoth(I*oo) == 0
    assert acoth(-I*oo) == 0
    assert acoth(zoo) == 0

    #properties
    assert acoth(-x) == -acoth(x)

    assert acoth(I/sqrt(3)) == -I*pi/3
    assert acoth(-I/sqrt(3)) == I*pi/3
    assert acoth(I*sqrt(3)) == -I*pi/6
    assert acoth(-I*sqrt(3)) == I*pi/6
    assert acoth(I*(1 + sqrt(2))) == -pi*I/8
    assert acoth(-I*(sqrt(2) + 1)) == pi*I/8
    assert acoth(I*(1 - sqrt(2))) == 3*pi*I/8
    assert acoth(I*(sqrt(2) - 1)) == -3*pi*I/8
    assert acoth(I*sqrt(5 + 2*sqrt(5))) == -I*pi/10
    assert acoth(-I*sqrt(5 + 2*sqrt(5))) == I*pi/10
    assert acoth(I*(2 + sqrt(3))) == -pi*I/12
    assert acoth(-I*(2 + sqrt(3))) == pi*I/12
    assert acoth(I*(2 - sqrt(3))) == -5*pi*I/12
    assert acoth(I*(sqrt(3) - 2)) == 5*pi*I/12


def test_acoth_rewrite():
    x = Symbol('x')
    assert acoth(x).rewrite(log) == (log(1 + 1/x) - log(1 - 1/x)) / 2


def test_acoth_series():
    x = Symbol('x')
    assert acoth(x).series(x, 0, 10) == \
        I*pi/2 + x + x**3/3 + x**5/5 + x**7/7 + x**9/9 + O(x**10)


def test_inverses():
    x = Symbol('x')
    assert sinh(x).inverse() == asinh
    raises(AttributeError, lambda: cosh(x).inverse())
    assert tanh(x).inverse() == atanh
    assert coth(x).inverse() == acoth
    assert asinh(x).inverse() == sinh
    assert acosh(x).inverse() == cosh
    assert atanh(x).inverse() == tanh
    assert acoth(x).inverse() == coth
    assert asech(x).inverse() == sech
    assert acsch(x).inverse() == csch


def test_leading_term():
    x = Symbol('x')
    assert cosh(x).as_leading_term(x) == 1
    assert coth(x).as_leading_term(x) == 1/x
    assert acosh(x).as_leading_term(x) == I*pi/2
    assert acoth(x).as_leading_term(x) == I*pi/2
    for func in [sinh, tanh, asinh, atanh]:
        assert func(x).as_leading_term(x) == x
    for func in [sinh, cosh, tanh, coth, asinh, acosh, atanh, acoth]:
        for arg in (1/x, S.Half):
            eq = func(arg)
            assert eq.as_leading_term(x) == eq
    for func in [csch, sech]:
        eq = func(S.Half)
        assert eq.as_leading_term(x) == eq


def test_complex():
    a, b = symbols('a,b', real=True)
    z = a + b*I
    for func in [sinh, cosh, tanh, coth, sech, csch]:
        assert func(z).conjugate() == func(a - b*I)
    for deep in [True, False]:
        assert sinh(z).expand(
            complex=True, deep=deep) == sinh(a)*cos(b) + I*cosh(a)*sin(b)
        assert cosh(z).expand(
            complex=True, deep=deep) == cosh(a)*cos(b) + I*sinh(a)*sin(b)
        assert tanh(z).expand(complex=True, deep=deep) == sinh(a)*cosh(
            a)/(cos(b)**2 + sinh(a)**2) + I*sin(b)*cos(b)/(cos(b)**2 + sinh(a)**2)
        assert coth(z).expand(complex=True, deep=deep) == sinh(a)*cosh(
            a)/(sin(b)**2 + sinh(a)**2) - I*sin(b)*cos(b)/(sin(b)**2 + sinh(a)**2)
        assert csch(z).expand(complex=True, deep=deep) == cos(b) * sinh(a) / (sin(b)**2\
            *cosh(a)**2 + cos(b)**2 * sinh(a)**2) - I*sin(b) * cosh(a) / (sin(b)**2\
            *cosh(a)**2 + cos(b)**2 * sinh(a)**2)
        assert sech(z).expand(complex=True, deep=deep) == cos(b) * cosh(a) / (sin(b)**2\
            *sinh(a)**2 + cos(b)**2 * cosh(a)**2) - I*sin(b) * sinh(a) / (sin(b)**2\
            *sinh(a)**2 + cos(b)**2 * cosh(a)**2)


def test_complex_2899():
    a, b = symbols('a,b', real=True)
    for deep in [True, False]:
        for func in [sinh, cosh, tanh, coth]:
            assert func(a).expand(complex=True, deep=deep) == func(a)


def test_simplifications():
    x = Symbol('x')
    assert sinh(asinh(x)) == x
    assert sinh(acosh(x)) == sqrt(x - 1) * sqrt(x + 1)
    assert sinh(atanh(x)) == x/sqrt(1 - x**2)
    assert sinh(acoth(x)) == 1/(sqrt(x - 1) * sqrt(x + 1))

    assert cosh(asinh(x)) == sqrt(1 + x**2)
    assert cosh(acosh(x)) == x
    assert cosh(atanh(x)) == 1/sqrt(1 - x**2)
    assert cosh(acoth(x)) == x/(sqrt(x - 1) * sqrt(x + 1))

    assert tanh(asinh(x)) == x/sqrt(1 + x**2)
    assert tanh(acosh(x)) == sqrt(x - 1) * sqrt(x + 1) / x
    assert tanh(atanh(x)) == x
    assert tanh(acoth(x)) == 1/x

    assert coth(asinh(x)) == sqrt(1 + x**2)/x
    assert coth(acosh(x)) == x/(sqrt(x - 1) * sqrt(x + 1))
    assert coth(atanh(x)) == 1/x
    assert coth(acoth(x)) == x

    assert csch(asinh(x)) == 1/x
    assert csch(acosh(x)) == 1/(sqrt(x - 1) * sqrt(x + 1))
    assert csch(atanh(x)) == sqrt(1 - x**2)/x
    assert csch(acoth(x)) == sqrt(x - 1) * sqrt(x + 1)

    assert sech(asinh(x)) == 1/sqrt(1 + x**2)
    assert sech(acosh(x)) == 1/x
    assert sech(atanh(x)) == sqrt(1 - x**2)
    assert sech(acoth(x)) == sqrt(x - 1) * sqrt(x + 1)/x


def test_issue_4136():
    assert cosh(asinh(Integer(3)/2)) == sqrt(Integer(13)/4)


def test_sinh_rewrite():
    x = Symbol('x')
    assert sinh(x).rewrite(exp) == (exp(x) - exp(-x))/2 \
        == sinh(x).rewrite('tractable')
    assert sinh(x).rewrite(cosh) == -I*cosh(x + I*pi/2)
    tanh_half = tanh(S.Half*x)
    assert sinh(x).rewrite(tanh) == 2*tanh_half/(1 - tanh_half**2)
    coth_half = coth(S.Half*x)
    assert sinh(x).rewrite(coth) == 2*coth_half/(coth_half**2 - 1)


def test_cosh_rewrite():
    x = Symbol('x')
    assert cosh(x).rewrite(exp) == (exp(x) + exp(-x))/2 \
        == cosh(x).rewrite('tractable')
    assert cosh(x).rewrite(sinh) == -I*sinh(x + I*pi/2)
    tanh_half = tanh(S.Half*x)**2
    assert cosh(x).rewrite(tanh) == (1 + tanh_half)/(1 - tanh_half)
    coth_half = coth(S.Half*x)**2
    assert cosh(x).rewrite(coth) == (coth_half + 1)/(coth_half - 1)


def test_tanh_rewrite():
    x = Symbol('x')
    assert tanh(x).rewrite(exp) == (exp(x) - exp(-x))/(exp(x) + exp(-x)) \
        == tanh(x).rewrite('tractable')
    assert tanh(x).rewrite(sinh) == I*sinh(x)/sinh(I*pi/2 - x)
    assert tanh(x).rewrite(cosh) == I*cosh(I*pi/2 - x)/cosh(x)
    assert tanh(x).rewrite(coth) == 1/coth(x)


def test_coth_rewrite():
    x = Symbol('x')
    assert coth(x).rewrite(exp) == (exp(x) + exp(-x))/(exp(x) - exp(-x)) \
        == coth(x).rewrite('tractable')
    assert coth(x).rewrite(sinh) == -I*sinh(I*pi/2 - x)/sinh(x)
    assert coth(x).rewrite(cosh) == -I*cosh(x)/cosh(I*pi/2 - x)
    assert coth(x).rewrite(tanh) == 1/tanh(x)


def test_csch_rewrite():
    x = Symbol('x')
    assert csch(x).rewrite(exp) == 1 / (exp(x)/2 - exp(-x)/2) \
        == csch(x).rewrite('tractable')
    assert csch(x).rewrite(cosh) == I/cosh(x + I*pi/2)
    tanh_half = tanh(S.Half*x)
    assert csch(x).rewrite(tanh) == (1 - tanh_half**2)/(2*tanh_half)
    coth_half = coth(S.Half*x)
    assert csch(x).rewrite(coth) == (coth_half**2 - 1)/(2*coth_half)


def test_sech_rewrite():
    x = Symbol('x')
    assert sech(x).rewrite(exp) == 1 / (exp(x)/2 + exp(-x)/2) \
        == sech(x).rewrite('tractable')
    assert sech(x).rewrite(sinh) == I/sinh(x + I*pi/2)
    tanh_half = tanh(S.Half*x)**2
    assert sech(x).rewrite(tanh) == (1 - tanh_half)/(1 + tanh_half)
    coth_half = coth(S.Half*x)**2
    assert sech(x).rewrite(coth) == (coth_half - 1)/(coth_half + 1)


def test_derivs():
    x = Symbol('x')
    assert coth(x).diff(x) == -sinh(x)**(-2)
    assert sinh(x).diff(x) == cosh(x)
    assert cosh(x).diff(x) == sinh(x)
    assert tanh(x).diff(x) == -tanh(x)**2 + 1
    assert csch(x).diff(x) == -coth(x)*csch(x)
    assert sech(x).diff(x) == -tanh(x)*sech(x)
    assert acoth(x).diff(x) == 1/(-x**2 + 1)
    assert asinh(x).diff(x) == 1/sqrt(x**2 + 1)
    assert acosh(x).diff(x) == 1/sqrt(x**2 - 1)
    assert atanh(x).diff(x) == 1/(-x**2 + 1)
    assert asech(x).diff(x) == -1/(x*sqrt(1 - x**2))
    assert acsch(x).diff(x) == -1/(x**2*sqrt(1 + x**(-2)))


def test_sinh_expansion():
    x, y = symbols('x,y')
    assert sinh(x+y).expand(trig=True) == sinh(x)*cosh(y) + cosh(x)*sinh(y)
    assert sinh(2*x).expand(trig=True) == 2*sinh(x)*cosh(x)
    assert sinh(3*x).expand(trig=True).expand() == \
        sinh(x)**3 + 3*sinh(x)*cosh(x)**2


def test_cosh_expansion():
    x, y = symbols('x,y')
    assert cosh(x+y).expand(trig=True) == cosh(x)*cosh(y) + sinh(x)*sinh(y)
    assert cosh(2*x).expand(trig=True) == cosh(x)**2 + sinh(x)**2
    assert cosh(3*x).expand(trig=True).expand() == \
        3*sinh(x)**2*cosh(x) + cosh(x)**3

def test_real_assumptions():
    z = Symbol('z', real=False)
    assert sinh(z).is_real is None
    assert cosh(z).is_real is None
    assert tanh(z).is_real is None
    assert sech(z).is_real is None
    assert csch(z).is_real is None
    assert coth(z).is_real is None

def test_sign_assumptions():
    p = Symbol('p', positive=True)
    n = Symbol('n', negative=True)
    assert sinh(n).is_negative is True
    assert sinh(p).is_positive is True
    assert cosh(n).is_positive is True
    assert cosh(p).is_positive is True
    assert tanh(n).is_negative is True
    assert tanh(p).is_positive is True
    assert csch(n).is_negative is True
    assert csch(p).is_positive is True
    assert sech(n).is_positive is True
    assert sech(p).is_positive is True
    assert coth(n).is_negative is True
    assert coth(p).is_positive is True
