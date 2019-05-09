from sympy import (Abs, Add, atan, ceiling, cos, E, Eq, exp,
    factorial, fibonacci, floor, Function, GoldenRatio, I, Integral,
    integrate, log, Mul, N, oo, pi, Pow, product, Product,
    Rational, S, Sum, sin, sqrt, sstr, sympify, Symbol, Max, nfloat)
from sympy.core.evalf import (complex_accuracy, PrecisionExhausted,
    scaled_zero, get_integer_part, as_mpmath)
from mpmath import inf, ninf
from mpmath.libmp.libmpf import from_float
from sympy.core.compatibility import long, range
from sympy.utilities.pytest import raises, XFAIL

from sympy.abc import n, x, y

def NS(e, n=15, **options):
    return sstr(sympify(e).evalf(n, **options), full_prec=True)


def test_evalf_helpers():
    assert complex_accuracy((from_float(2.0), None, 35, None)) == 35
    assert complex_accuracy((from_float(2.0), from_float(10.0), 35, 100)) == 37
    assert complex_accuracy(
        (from_float(2.0), from_float(1000.0), 35, 100)) == 43
    assert complex_accuracy((from_float(2.0), from_float(10.0), 100, 35)) == 35
    assert complex_accuracy(
        (from_float(2.0), from_float(1000.0), 100, 35)) == 35


def test_evalf_basic():
    assert NS('pi', 15) == '3.14159265358979'
    assert NS('2/3', 10) == '0.6666666667'
    assert NS('355/113-pi', 6) == '2.66764e-7'
    assert NS('16*atan(1/5)-4*atan(1/239)', 15) == '3.14159265358979'


def test_cancellation():
    assert NS(Add(pi, Rational(1, 10**1000), -pi, evaluate=False), 15,
              maxn=1200) == '1.00000000000000e-1000'


def test_evalf_powers():
    assert NS('pi**(10**20)', 10) == '1.339148777e+49714987269413385435'
    assert NS(pi**(10**100), 10) == ('4.946362032e+4971498726941338543512682882'
          '9089887365167832438044244613405349992494711208'
          '95526746555473864642912223')
    assert NS('2**(1/10**50)', 15) == '1.00000000000000'
    assert NS('2**(1/10**50)-1', 15) == '6.93147180559945e-51'

# Evaluation of Rump's ill-conditioned polynomial


def test_evalf_rump():
    a = 1335*y**6/4 + x**2*(11*x**2*y**2 - y**6 - 121*y**4 - 2) + 11*y**8/2 + x/(2*y)
    assert NS(a, 15, subs={x: 77617, y: 33096}) == '-0.827396059946821'


def test_evalf_complex():
    assert NS('2*sqrt(pi)*I', 10) == '3.544907702*I'
    assert NS('3+3*I', 15) == '3.00000000000000 + 3.00000000000000*I'
    assert NS('E+pi*I', 15) == '2.71828182845905 + 3.14159265358979*I'
    assert NS('pi * (3+4*I)', 15) == '9.42477796076938 + 12.5663706143592*I'
    assert NS('I*(2+I)', 15) == '-1.00000000000000 + 2.00000000000000*I'


@XFAIL
def test_evalf_complex_bug():
    assert NS('(pi+E*I)*(E+pi*I)', 15) in ('0.e-15 + 17.25866050002*I',
              '0.e-17 + 17.25866050002*I', '-0.e-17 + 17.25866050002*I')


def test_evalf_complex_powers():
    assert NS('(E+pi*I)**100000000000000000') == \
        '-3.58896782867793e+61850354284995199 + 4.58581754997159e+61850354284995199*I'
    # XXX: rewrite if a+a*I simplification introduced in sympy
    #assert NS('(pi + pi*I)**2') in ('0.e-15 + 19.7392088021787*I', '0.e-16 + 19.7392088021787*I')
    assert NS('(pi + pi*I)**2', chop=True) == '19.7392088021787*I'
    assert NS(
        '(pi + 1/10**8 + pi*I)**2') == '6.2831853e-8 + 19.7392088650106*I'
    assert NS('(pi + 1/10**12 + pi*I)**2') == '6.283e-12 + 19.7392088021850*I'
    assert NS('(pi + pi*I)**4', chop=True) == '-389.636364136010'
    assert NS(
        '(pi + 1/10**8 + pi*I)**4') == '-389.636366616512 + 2.4805021e-6*I'
    assert NS('(pi + 1/10**12 + pi*I)**4') == '-389.636364136258 + 2.481e-10*I'
    assert NS(
        '(10000*pi + 10000*pi*I)**4', chop=True) == '-3.89636364136010e+18'


@XFAIL
def test_evalf_complex_powers_bug():
    assert NS('(pi + pi*I)**4') == '-389.63636413601 + 0.e-14*I'


def test_evalf_exponentiation():
    assert NS(sqrt(-pi)) == '1.77245385090552*I'
    assert NS(Pow(pi*I, Rational(
        1, 2), evaluate=False)) == '1.25331413731550 + 1.25331413731550*I'
    assert NS(pi**I) == '0.413292116101594 + 0.910598499212615*I'
    assert NS(pi**(E + I/3)) == '20.8438653991931 + 8.36343473930031*I'
    assert NS((pi + I/3)**(E + I/3)) == '17.2442906093590 + 13.6839376767037*I'
    assert NS(exp(pi)) == '23.1406926327793'
    assert NS(exp(pi + E*I)) == '-21.0981542849657 + 9.50576358282422*I'
    assert NS(pi**pi) == '36.4621596072079'
    assert NS((-pi)**pi) == '-32.9138577418939 - 15.6897116534332*I'
    assert NS((-pi)**(-pi)) == '-0.0247567717232697 + 0.0118013091280262*I'

# An example from Smith, "Multiple Precision Complex Arithmetic and Functions"


def test_evalf_complex_cancellation():
    A = Rational('63287/100000')
    B = Rational('52498/100000')
    C = Rational('69301/100000')
    D = Rational('83542/100000')
    F = Rational('2231321613/2500000000')
    # XXX: the number of returned mantissa digits in the real part could
    # change with the implementation. What matters is that the returned digits are
    # correct; those that are showing now are correct.
    # >>> ((A+B*I)*(C+D*I)).expand()
    # 64471/10000000000 + 2231321613*I/2500000000
    # >>> 2231321613*4
    # 8925286452L
    assert NS((A + B*I)*(C + D*I), 6) == '6.44710e-6 + 0.892529*I'
    assert NS((A + B*I)*(C + D*I), 10) == '6.447100000e-6 + 0.8925286452*I'
    assert NS((A + B*I)*(
        C + D*I) - F*I, 5) in ('6.4471e-6 + 0.e-14*I', '6.4471e-6 - 0.e-14*I')


def test_evalf_logs():
    assert NS("log(3+pi*I)", 15) == '1.46877619736226 + 0.808448792630022*I'
    assert NS("log(pi*I)", 15) == '1.14472988584940 + 1.57079632679490*I'
    assert NS('log(-1 + 0.00001)', 2) == '-1.0e-5 + 3.1*I'
    assert NS('log(100, 10, evaluate=False)', 15) == '2.00000000000000'
    assert NS('-2*I*log(-(-1)**(S(1)/9))', 15) == '-5.58505360638185'


def test_evalf_trig():
    assert NS('sin(1)', 15) == '0.841470984807897'
    assert NS('cos(1)', 15) == '0.540302305868140'
    assert NS('sin(10**-6)', 15) == '9.99999999999833e-7'
    assert NS('cos(10**-6)', 15) == '0.999999999999500'
    assert NS('sin(E*10**100)', 15) == '0.409160531722613'
    # Some input near roots
    assert NS(sin(exp(pi*sqrt(163))*pi), 15) == '-2.35596641936785e-12'
    assert NS(sin(pi*10**100 + Rational(7, 10**5), evaluate=False), 15, maxn=120) == \
        '6.99999999428333e-5'
    assert NS(sin(Rational(7, 10**5), evaluate=False), 15) == \
        '6.99999999428333e-5'

# Check detection of various false identities


def test_evalf_near_integers():
    # Binet's formula
    f = lambda n: ((1 + sqrt(5))**n)/(2**n * sqrt(5))
    assert NS(f(5000) - fibonacci(5000), 10, maxn=1500) == '5.156009964e-1046'
    # Some near-integer identities from
    # http://mathworld.wolfram.com/AlmostInteger.html
    assert NS('sin(2017*2**(1/5))', 15) == '-1.00000000000000'
    assert NS('sin(2017*2**(1/5))', 20) == '-0.99999999999999997857'
    assert NS('1+sin(2017*2**(1/5))', 15) == '2.14322287389390e-17'
    assert NS('45 - 613*E/37 + 35/991', 15) == '6.03764498766326e-11'


def test_evalf_ramanujan():
    assert NS(exp(pi*sqrt(163)) - 640320**3 - 744, 10) == '-7.499274028e-13'
    # A related identity
    A = 262537412640768744*exp(-pi*sqrt(163))
    B = 196884*exp(-2*pi*sqrt(163))
    C = 103378831900730205293632*exp(-3*pi*sqrt(163))
    assert NS(1 - A - B + C, 10) == '1.613679005e-59'

# Input that for various reasons have failed at some point


def test_evalf_bugs():
    assert NS(sin(1) + exp(-10**10), 10) == NS(sin(1), 10)
    assert NS(exp(10**10) + sin(1), 10) == NS(exp(10**10), 10)
    assert NS('expand_log(log(1+1/10**50))', 20) == '1.0000000000000000000e-50'
    assert NS('log(10**100,10)', 10) == '100.0000000'
    assert NS('log(2)', 10) == '0.6931471806'
    assert NS(
        '(sin(x)-x)/x**3', 15, subs={x: '1/10**50'}) == '-0.166666666666667'
    assert NS(sin(1) + Rational(
        1, 10**100)*I, 15) == '0.841470984807897 + 1.00000000000000e-100*I'
    assert x.evalf() == x
    assert NS((1 + I)**2*I, 6) == '-2.00000'
    d = {n: (
        -1)**Rational(6, 7), y: (-1)**Rational(4, 7), x: (-1)**Rational(2, 7)}
    assert NS((x*(1 + y*(1 + n))).subs(d).evalf(), 6) == '0.346011 + 0.433884*I'
    assert NS(((-I - sqrt(2)*I)**2).evalf()) == '-5.82842712474619'
    assert NS((1 + I)**2*I, 15) == '-2.00000000000000'
    # issue 4758 (1/2):
    assert NS(pi.evalf(69) - pi) == '-4.43863937855894e-71'
    # issue 4758 (2/2): With the bug present, this still only fails if the
    # terms are in the order given here. This is not generally the case,
    # because the order depends on the hashes of the terms.
    assert NS(20 - 5008329267844*n**25 - 477638700*n**37 - 19*n,
              subs={n: .01}) == '19.8100000000000'
    assert NS(((x - 1)*((1 - x))**1000).n()
              ) == '(1.00000000000000 - x)**1000*(x - 1.00000000000000)'
    assert NS((-x).n()) == '-x'
    assert NS((-2*x).n()) == '-2.00000000000000*x'
    assert NS((-2*x*y).n()) == '-2.00000000000000*x*y'
    assert cos(x).n(subs={x: 1+I}) == cos(x).subs(x, 1+I).n()
    # issue 6660. Also NaN != mpmath.nan
    # In this order:
    # 0*nan, 0/nan, 0*inf, 0/inf
    # 0+nan, 0-nan, 0+inf, 0-inf
    # >>> n = Some Number
    # n*nan, n/nan, n*inf, n/inf
    # n+nan, n-nan, n+inf, n-inf
    assert (0*E**(oo)).n() == S.NaN
    assert (0/E**(oo)).n() == S.Zero

    assert (0+E**(oo)).n() == S.Infinity
    assert (0-E**(oo)).n() == S.NegativeInfinity

    assert (5*E**(oo)).n() == S.Infinity
    assert (5/E**(oo)).n() == S.Zero

    assert (5+E**(oo)).n() == S.Infinity
    assert (5-E**(oo)).n() == S.NegativeInfinity

    #issue 7416
    assert as_mpmath(0.0, 10, {'chop': True}) == 0

    #issue 5412
    assert ((oo*I).n() == S.Infinity*I)
    assert ((oo+oo*I).n() == S.Infinity + S.Infinity*I)

    #issue 11518
    assert NS(2*x**2.5, 5) == '2.0000*x**2.5000'

    #issue 13076
    assert NS(Mul(Max(0, y), x, evaluate=False).evalf()) == 'x*Max(0, y)'

def test_evalf_integer_parts():
    a = floor(log(8)/log(2) - exp(-1000), evaluate=False)
    b = floor(log(8)/log(2), evaluate=False)
    assert a.evalf() == 3
    assert b.evalf() == 3
    # equals, as a fallback, can still fail but it might succeed as here
    assert ceiling(10*(sin(1)**2 + cos(1)**2)) == 10

    assert int(floor(factorial(50)/E, evaluate=False).evalf(70)) == \
        long(11188719610782480504630258070757734324011354208865721592720336800)
    assert int(ceiling(factorial(50)/E, evaluate=False).evalf(70)) == \
        long(11188719610782480504630258070757734324011354208865721592720336801)
    assert int(floor((GoldenRatio**999 / sqrt(5) + Rational(1, 2)))
               .evalf(1000)) == fibonacci(999)
    assert int(floor((GoldenRatio**1000 / sqrt(5) + Rational(1, 2)))
               .evalf(1000)) == fibonacci(1000)

    assert ceiling(x).evalf(subs={x: 3}) == 3
    assert ceiling(x).evalf(subs={x: 3*I}) == 3*I
    assert ceiling(x).evalf(subs={x: 2 + 3*I}) == 2 + 3*I
    assert ceiling(x).evalf(subs={x: 3.}) == 3
    assert ceiling(x).evalf(subs={x: 3.*I}) == 3*I
    assert ceiling(x).evalf(subs={x: 2. + 3*I}) == 2 + 3*I

    assert float((floor(1.5, evaluate=False)+1/9).evalf()) == 1 + 1/9
    assert float((floor(0.5, evaluate=False)+20).evalf()) == 20

def test_evalf_trig_zero_detection():
    a = sin(160*pi, evaluate=False)
    t = a.evalf(maxn=100)
    assert abs(t) < 1e-100
    assert t._prec < 2
    assert a.evalf(chop=True) == 0
    raises(PrecisionExhausted, lambda: a.evalf(strict=True))


def test_evalf_sum():
    assert Sum(n,(n,1,2)).evalf() == 3.
    assert Sum(n,(n,1,2)).doit().evalf() == 3.
    # the next test should return instantly
    assert Sum(1/n,(n,1,2)).evalf() == 1.5

    # issue 8219
    assert Sum(E/factorial(n), (n, 0, oo)).evalf() == (E*E).evalf()
    # issue 8254
    assert Sum(2**n*n/factorial(n), (n, 0, oo)).evalf() == (2*E*E).evalf()
    # issue 8411
    s = Sum(1/x**2, (x, 100, oo))
    assert s.n() == s.doit().n()


def test_evalf_divergent_series():
    raises(ValueError, lambda: Sum(1/n, (n, 1, oo)).evalf())
    raises(ValueError, lambda: Sum(n/(n**2 + 1), (n, 1, oo)).evalf())
    raises(ValueError, lambda: Sum((-1)**n, (n, 1, oo)).evalf())
    raises(ValueError, lambda: Sum((-1)**n, (n, 1, oo)).evalf())
    raises(ValueError, lambda: Sum(n**2, (n, 1, oo)).evalf())
    raises(ValueError, lambda: Sum(2**n, (n, 1, oo)).evalf())
    raises(ValueError, lambda: Sum((-2)**n, (n, 1, oo)).evalf())
    raises(ValueError, lambda: Sum((2*n + 3)/(3*n**2 + 4), (n, 0, oo)).evalf())
    raises(ValueError, lambda: Sum((0.5*n**3)/(n**4 + 1), (n, 0, oo)).evalf())


def test_evalf_product():
    assert Product(n, (n, 1, 10)).evalf() == 3628800.
    assert Product(1 - S.Half**2/n**2, (n, 1, oo)).evalf(5)==0.63662
    assert Product(n, (n, -1, 3)).evalf() == 0


def test_evalf_py_methods():
    assert abs(float(pi + 1) - 4.1415926535897932) < 1e-10
    assert abs(complex(pi + 1) - 4.1415926535897932) < 1e-10
    assert abs(
        complex(pi + E*I) - (3.1415926535897931 + 2.7182818284590451j)) < 1e-10
    raises(TypeError, lambda: float(pi + x))


def test_evalf_power_subs_bugs():
    assert (x**2).evalf(subs={x: 0}) == 0
    assert sqrt(x).evalf(subs={x: 0}) == 0
    assert (x**Rational(2, 3)).evalf(subs={x: 0}) == 0
    assert (x**x).evalf(subs={x: 0}) == 1
    assert (3**x).evalf(subs={x: 0}) == 1
    assert exp(x).evalf(subs={x: 0}) == 1
    assert ((2 + I)**x).evalf(subs={x: 0}) == 1
    assert (0**x).evalf(subs={x: 0}) == 1


def test_evalf_arguments():
    raises(TypeError, lambda: pi.evalf(method="garbage"))


def test_implemented_function_evalf():
    from sympy.utilities.lambdify import implemented_function
    f = Function('f')
    f = implemented_function(f, lambda x: x + 1)
    assert str(f(x)) == "f(x)"
    assert str(f(2)) == "f(2)"
    assert f(2).evalf() == 3
    assert f(x).evalf() == f(x)
    f = implemented_function(Function('sin'), lambda x: x + 1)
    assert f(2).evalf() != sin(2)
    del f._imp_     # XXX: due to caching _imp_ would influence all other tests


def test_evaluate_false():
    for no in [0, False]:
        assert Add(3, 2, evaluate=no).is_Add
        assert Mul(3, 2, evaluate=no).is_Mul
        assert Pow(3, 2, evaluate=no).is_Pow
    assert Pow(y, 2, evaluate=True) - Pow(y, 2, evaluate=True) == 0


def test_evalf_relational():
    assert Eq(x/5, y/10).evalf() == Eq(0.2*x, 0.1*y)


def test_issue_5486():
    assert not cos(sqrt(0.5 + I)).n().is_Function


def test_issue_5486_bug():
    from sympy import I, Expr
    assert abs(Expr._from_mpmath(I._to_mpmath(15), 15) - I) < 1.0e-15


def test_bugs():
    from sympy import polar_lift, re

    assert abs(re((1 + I)**2)) < 1e-15

    # anything that evalf's to 0 will do in place of polar_lift
    assert abs(polar_lift(0)).n() == 0


def test_subs():
    assert NS('besseli(-x, y) - besseli(x, y)', subs={x: 3.5, y: 20.0}) == \
        '-4.92535585957223e-10'
    assert NS('Piecewise((x, x>0)) + Piecewise((1-x, x>0))', subs={x: 0.1}) == \
        '1.00000000000000'
    raises(TypeError, lambda: x.evalf(subs=(x, 1)))


def test_issue_4956_5204():
    # issue 4956
    v = S('''(-27*12**(1/3)*sqrt(31)*I +
    27*2**(2/3)*3**(1/3)*sqrt(31)*I)/(-2511*2**(2/3)*3**(1/3) +
    (29*18**(1/3) + 9*2**(1/3)*3**(2/3)*sqrt(31)*I +
    87*2**(1/3)*3**(1/6)*I)**2)''')
    assert NS(v, 1) == '0.e-118 - 0.e-118*I'

    # issue 5204
    v = S('''-(357587765856 + 18873261792*249**(1/2) + 56619785376*I*83**(1/2) +
    108755765856*I*3**(1/2) + 41281887168*6**(1/3)*(1422 +
    54*249**(1/2))**(1/3) - 1239810624*6**(1/3)*249**(1/2)*(1422 +
    54*249**(1/2))**(1/3) - 3110400000*I*6**(1/3)*83**(1/2)*(1422 +
    54*249**(1/2))**(1/3) + 13478400000*I*3**(1/2)*6**(1/3)*(1422 +
    54*249**(1/2))**(1/3) + 1274950152*6**(2/3)*(1422 +
    54*249**(1/2))**(2/3) + 32347944*6**(2/3)*249**(1/2)*(1422 +
    54*249**(1/2))**(2/3) - 1758790152*I*3**(1/2)*6**(2/3)*(1422 +
    54*249**(1/2))**(2/3) - 304403832*I*6**(2/3)*83**(1/2)*(1422 +
    4*249**(1/2))**(2/3))/(175732658352 + (1106028 + 25596*249**(1/2) +
    76788*I*83**(1/2))**2)''')
    assert NS(v, 5) == '0.077284 + 1.1104*I'
    assert NS(v, 1) == '0.08 + 1.*I'


def test_old_docstring():
    a = (E + pi*I)*(E - pi*I)
    assert NS(a) == '17.2586605000200'
    assert a.n() == 17.25866050002001


def test_issue_4806():
    assert integrate(atan(x)**2, (x, -1, 1)).evalf().round(1) == 0.5
    assert atan(0, evaluate=False).n() == 0


def test_evalf_mul():
    # sympy should not try to expand this; it should be handled term-wise
    # in evalf through mpmath
    assert NS(product(1 + sqrt(n)*I, (n, 1, 500)), 1) == '5.e+567 + 2.e+568*I'


def test_scaled_zero():
    a, b = (([0], 1, 100, 1), -1)
    assert scaled_zero(100) == (a, b)
    assert scaled_zero(a) == (0, 1, 100, 1)
    a, b = (([1], 1, 100, 1), -1)
    assert scaled_zero(100, -1) == (a, b)
    assert scaled_zero(a) == (1, 1, 100, 1)
    raises(ValueError, lambda: scaled_zero(scaled_zero(100)))
    raises(ValueError, lambda: scaled_zero(100, 2))
    raises(ValueError, lambda: scaled_zero(100, 0))
    raises(ValueError, lambda: scaled_zero((1, 5, 1, 3)))


def test_chop_value():
    for i in range(-27, 28):
        assert (Pow(10, i)*2).n(chop=10**i) and not (Pow(10, i)).n(chop=10**i)


def test_infinities():
    assert oo.evalf(chop=True) == inf
    assert (-oo).evalf(chop=True) == ninf


def test_to_mpmath():
    assert sqrt(3)._to_mpmath(20)._mpf_ == (0, long(908093), -19, 20)
    assert S(3.2)._to_mpmath(20)._mpf_ == (0, long(838861), -18, 20)


def test_issue_6632_evalf():
    add = (-100000*sqrt(2500000001) + 5000000001)
    assert add.n() == 9.999999998e-11
    assert (add*add).n() == 9.999999996e-21


def test_issue_4945():
    from sympy.abc import H
    from sympy import zoo
    assert (H/0).evalf(subs={H:1}) == zoo*H


def test_evalf_integral():
    # test that workprec has to increase in order to get a result other than 0
    eps = Rational(1, 1000000)
    assert Integral(sin(x), (x, -pi, pi + eps)).n(2)._prec == 10


def test_issue_8821_highprec_from_str():
    s = str(pi.evalf(128))
    p = N(s)
    assert Abs(sin(p)) < 1e-15
    p = N(s, 64)
    assert Abs(sin(p)) < 1e-64


def test_issue_8853():
    p = Symbol('x', even=True, positive=True)
    assert floor(-p - S.Half).is_even == False
    assert floor(-p + S.Half).is_even == True
    assert ceiling(p - S.Half).is_even == True
    assert ceiling(p + S.Half).is_even == False

    assert get_integer_part(S.Half, -1, {}, True) == (0, 0)
    assert get_integer_part(S.Half, 1, {}, True) == (1, 0)
    assert get_integer_part(-S.Half, -1, {}, True) == (-1, 0)
    assert get_integer_part(-S.Half, 1, {}, True) == (0, 0)


def test_issue_9326():
    from sympy import Dummy
    d1 = Dummy('d')
    d2 = Dummy('d')
    e = d1 + d2
    assert e.evalf(subs = {d1: 1, d2: 2}) == 3


def test_issue_10323():
    assert ceiling(sqrt(2**30 + 1)) == 2**15 + 1


def test_AssocOp_Function():
    # the first arg of Min is not comparable in the imaginary part
    raises(ValueError, lambda: S('''
    Min(-sqrt(3)*cos(pi/18)/6 + re(1/((-1/2 - sqrt(3)*I/2)*(1/6 +
    sqrt(3)*I/18)**(1/3)))/3 + sin(pi/18)/2 + 2 + I*(-cos(pi/18)/2 -
    sqrt(3)*sin(pi/18)/6 + im(1/((-1/2 - sqrt(3)*I/2)*(1/6 +
    sqrt(3)*I/18)**(1/3)))/3), re(1/((-1/2 + sqrt(3)*I/2)*(1/6 +
    sqrt(3)*I/18)**(1/3)))/3 - sqrt(3)*cos(pi/18)/6 - sin(pi/18)/2 + 2 +
    I*(im(1/((-1/2 + sqrt(3)*I/2)*(1/6 + sqrt(3)*I/18)**(1/3)))/3 -
    sqrt(3)*sin(pi/18)/6 + cos(pi/18)/2))'''))
    # if that is changed so a non-comparable number remains as
    # an arg, then the Min/Max instantiation needs to be changed
    # to watch out for non-comparable args when making simplifications
    # and the following test should be added instead (with e being
    # the sympified expression above):
    # raises(ValueError, lambda: e._eval_evalf(2))


def test_issue_10395():
    eq = x*Max(0, y)
    assert nfloat(eq) == eq
    eq = x*Max(y, -1.1)
    assert nfloat(eq) == eq
    assert Max(y, 4).n() == Max(4.0, y)


def test_issue_13098():
    assert floor(log(S('9.'+'9'*20), 10)) == 0
    assert ceiling(log(S('9.'+'9'*20), 10)) == 1
    assert floor(log(20 - S('9.'+'9'*20), 10)) == 1
    assert ceiling(log(20 - S('9.'+'9'*20), 10)) == 2


def test_issue_14601():
    e = 5*x*y/2 - y*(35*(x**3)/2 - 15*x/2)
    subst = {x:0.0, y:0.0}
    e2 = e.evalf(subs=subst)
    assert float(e2) == 0.0
    assert float((x + x*(x**2 + x)).evalf(subs={x: 0.0})) == 0.0
