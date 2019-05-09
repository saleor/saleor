from sympy import (symbols, factorial, sqrt, Rational, atan, I, log, fps, O,
                   Sum, oo, S, pi, cos, sin, Function, exp, Derivative, asin,
                   airyai, acos, acosh, gamma, erf, asech, Add, Integral, Mul,
                   integrate)
from sympy.series.formal import (rational_algorithm, FormalPowerSeries,
                                 rational_independent, simpleDE, exp_re,
                                 hyper_re)
from sympy.utilities.pytest import raises, XFAIL, slow

x, y, z = symbols('x y z')
n, m, k = symbols('n m k', integer=True)
f, r = Function('f'), Function('r')


def test_rational_algorithm():
    f = 1 / ((x - 1)**2 * (x - 2))
    assert rational_algorithm(f, x, k) == \
        (-2**(-k - 1) + 1 - (factorial(k + 1) / factorial(k)), 0, 0)

    f = (1 + x + x**2 + x**3) / ((x - 1) * (x - 2))
    assert rational_algorithm(f, x, k) == \
        (-15*2**(-k - 1) + 4, x + 4, 0)

    f = z / (y*m - m*x - y*x + x**2)
    assert rational_algorithm(f, x, k) == \
        (((-y**(-k - 1)*z) / (y - m)) + ((m**(-k - 1)*z) / (y - m)), 0, 0)

    f = x / (1 - x - x**2)
    assert rational_algorithm(f, x, k) is None
    assert rational_algorithm(f, x, k, full=True) == \
        (((-Rational(1, 2) + sqrt(5)/2)**(-k - 1) *
         (-sqrt(5)/10 + Rational(1, 2))) +
         ((-sqrt(5)/2 - Rational(1, 2))**(-k - 1) *
         (sqrt(5)/10 + Rational(1, 2))), 0, 0)

    f = 1 / (x**2 + 2*x + 2)
    assert rational_algorithm(f, x, k) is None
    assert rational_algorithm(f, x, k, full=True) == \
        ((I*(-1 + I)**(-k - 1)) / 2 - (I*(-1 - I)**(-k - 1)) / 2, 0, 0)

    f = log(1 + x)
    assert rational_algorithm(f, x, k) == \
        (-(-1)**(-k) / k, 0, 1)

    f = atan(x)
    assert rational_algorithm(f, x, k) is None
    assert rational_algorithm(f, x, k, full=True) == \
        (((I*I**(-k)) / 2 - (I*(-I)**(-k)) / 2) / k, 0, 1)

    f = x*atan(x) - log(1 + x**2) / 2
    assert rational_algorithm(f, x, k) is None
    assert rational_algorithm(f, x, k, full=True) == \
        (((I*I**(-k + 1)) / 2 - (I*(-I)**(-k + 1)) / 2) /
         (k*(k - 1)), 0, 2)

    f = log((1 + x) / (1 - x)) / 2 - atan(x)
    assert rational_algorithm(f, x, k) is None
    assert rational_algorithm(f, x, k, full=True) == \
        ((-(-1)**(-k) / 2 - (I*I**(-k)) / 2 + (I*(-I)**(-k)) / 2 +
          Rational(1, 2)) / k, 0, 1)

    assert rational_algorithm(cos(x), x, k) is None


def test_rational_independent():
    ri = rational_independent
    assert ri([], x) == []
    assert ri([cos(x), sin(x)], x) == [cos(x), sin(x)]
    assert ri([x**2, sin(x), x*sin(x), x**3], x) == \
        [x**3 + x**2, x*sin(x) + sin(x)]
    assert ri([S.One, x*log(x), log(x), sin(x)/x, cos(x), sin(x), x], x) == \
        [x + 1, x*log(x) + log(x), sin(x)/x + sin(x), cos(x)]


def test_simpleDE():
    # Tests just the first valid DE
    for DE in simpleDE(exp(x), x, f):
        assert DE == (-f(x) + Derivative(f(x), x), 1)
        break
    for DE in simpleDE(sin(x), x, f):
        assert DE == (f(x) + Derivative(f(x), x, x), 2)
        break
    for DE in simpleDE(log(1 + x), x, f):
        assert DE == ((x + 1)*Derivative(f(x), x, 2) + Derivative(f(x), x), 2)
        break
    for DE in simpleDE(asin(x), x, f):
        assert DE == (x*Derivative(f(x), x) + (x**2 - 1)*Derivative(f(x), x, x),
                      2)
        break
    for DE in simpleDE(exp(x)*sin(x), x, f):
        assert DE == (2*f(x) - 2*Derivative(f(x)) + Derivative(f(x), x, x), 2)
        break
    for DE in simpleDE(((1 + x)/(1 - x))**n, x, f):
        assert DE == (2*n*f(x) + (x**2 - 1)*Derivative(f(x), x), 1)
        break
    for DE in simpleDE(airyai(x), x, f):
        assert DE == (-x*f(x) + Derivative(f(x), x, x), 2)
        break


def test_exp_re():
    d = -f(x) + Derivative(f(x), x)
    assert exp_re(d, r, k) == -r(k) + r(k + 1)

    d = f(x) + Derivative(f(x), x, x)
    assert exp_re(d, r, k) == r(k) + r(k + 2)

    d = f(x) + Derivative(f(x), x) + Derivative(f(x), x, x)
    assert exp_re(d, r, k) == r(k) + r(k + 1) + r(k + 2)

    d = Derivative(f(x), x) + Derivative(f(x), x, x)
    assert exp_re(d, r, k) == r(k) + r(k + 1)

    d = Derivative(f(x), x, 3) + Derivative(f(x), x, 4) + Derivative(f(x))
    assert exp_re(d, r, k) == r(k) + r(k + 2) + r(k + 3)


def test_hyper_re():
    d = f(x) + Derivative(f(x), x, x)
    assert hyper_re(d, r, k) == r(k) + (k+1)*(k+2)*r(k + 2)

    d = -x*f(x) + Derivative(f(x), x, x)
    assert hyper_re(d, r, k) == (k + 2)*(k + 3)*r(k + 3) - r(k)

    d = 2*f(x) - 2*Derivative(f(x), x) + Derivative(f(x), x, x)
    assert hyper_re(d, r, k) == \
        (-2*k - 2)*r(k + 1) + (k + 1)*(k + 2)*r(k + 2) + 2*r(k)

    d = 2*n*f(x) + (x**2 - 1)*Derivative(f(x), x)
    assert hyper_re(d, r, k) == \
        k*r(k) + 2*n*r(k + 1) + (-k - 2)*r(k + 2)

    d = (x**10 + 4)*Derivative(f(x), x) + x*(x**10 - 1)*Derivative(f(x), x, x)
    assert hyper_re(d, r, k) == \
        (k*(k - 1) + k)*r(k) + (4*k - (k + 9)*(k + 10) + 40)*r(k + 10)

    d = ((x**2 - 1)*Derivative(f(x), x, 3) + 3*x*Derivative(f(x), x, x) +
         Derivative(f(x), x))
    assert hyper_re(d, r, k) == \
        ((k*(k - 2)*(k - 1) + 3*k*(k - 1) + k)*r(k) +
         (-k*(k + 1)*(k + 2))*r(k + 2))


def test_fps():
    assert fps(1) == 1
    assert fps(2, x) == 2
    assert fps(2, x, dir='+') == 2
    assert fps(2, x, dir='-') == 2
    assert fps(x**2 + x + 1) == x**2 + x + 1
    assert fps(1/x + 1/x**2) == 1/x + 1/x**2
    assert fps(log(1 + x), hyper=False, rational=False) == log(1 + x)

    f = fps(log(1 + x))
    assert isinstance(f, FormalPowerSeries)
    assert f.function == log(1 + x)
    assert f.subs(x, y) == f
    assert f[:5] == [0, x, -x**2/2, x**3/3, -x**4/4]
    assert f.as_leading_term(x) == x
    assert f.polynomial(6) == x - x**2/2 + x**3/3 - x**4/4 + x**5/5

    k = f.ak.variables[0]
    assert f.infinite == Sum((-(-1)**(-k)*x**k)/k, (k, 1, oo))

    ft, s = f.truncate(n=None), f[:5]
    for i, t in enumerate(ft):
        if i == 5:
            break
        assert s[i] == t

    f = sin(x).fps(x)
    assert isinstance(f, FormalPowerSeries)
    assert f.truncate() == x - x**3/6 + x**5/120 + O(x**6)

    raises(NotImplementedError, lambda: fps(y*x))
    raises(ValueError, lambda: fps(x, dir=0))


@slow
def test_fps__rational():
    assert fps(1/x) == (1/x)
    assert fps((x**2 + x + 1) / x**3, dir=-1) == (x**2 + x + 1) / x**3

    f = 1 / ((x - 1)**2 * (x - 2))
    assert fps(f, x).truncate() == \
        (-Rational(1, 2) - 5*x/4 - 17*x**2/8 - 49*x**3/16 - 129*x**4/32 -
         321*x**5/64 + O(x**6))

    f = (1 + x + x**2 + x**3) / ((x - 1) * (x - 2))
    assert fps(f, x).truncate() == \
        (Rational(1, 2) + 5*x/4 + 17*x**2/8 + 49*x**3/16 + 113*x**4/32 +
         241*x**5/64 + O(x**6))

    f = x / (1 - x - x**2)
    assert fps(f, x, full=True).truncate() == \
        x + x**2 + 2*x**3 + 3*x**4 + 5*x**5 + O(x**6)

    f = 1 / (x**2 + 2*x + 2)
    assert fps(f, x, full=True).truncate() == \
        Rational(1, 2) - x/2 + x**2/4 - x**4/8 + x**5/8 + O(x**6)

    f = log(1 + x)
    assert fps(f, x).truncate() == \
        x - x**2/2 + x**3/3 - x**4/4 + x**5/5 + O(x**6)
    assert fps(f, x, dir=1).truncate() == fps(f, x, dir=-1).truncate()
    assert fps(f, x, 2).truncate() == \
        (log(3) - Rational(2, 3) - (x - 2)**2/18 + (x - 2)**3/81 -
         (x - 2)**4/324 + (x - 2)**5/1215 + x/3 + O((x - 2)**6, (x, 2)))
    assert fps(f, x, 2, dir=-1).truncate() == \
        (log(3) - Rational(2, 3) - (-x + 2)**2/18 - (-x + 2)**3/81 -
         (-x + 2)**4/324 - (-x + 2)**5/1215 + x/3 + O((x - 2)**6, (x, 2)))

    f = atan(x)
    assert fps(f, x, full=True).truncate() == x - x**3/3 + x**5/5 + O(x**6)
    assert fps(f, x, full=True, dir=1).truncate() == \
        fps(f, x, full=True, dir=-1).truncate()
    assert fps(f, x, 2, full=True).truncate() == \
        (atan(2) - Rational(2, 5) - 2*(x - 2)**2/25 + 11*(x - 2)**3/375 -
         6*(x - 2)**4/625 + 41*(x - 2)**5/15625 + x/5 + O((x - 2)**6, (x, 2)))
    assert fps(f, x, 2, full=True, dir=-1).truncate() == \
        (atan(2) - Rational(2, 5) - 2*(-x + 2)**2/25 - 11*(-x + 2)**3/375 -
         6*(-x + 2)**4/625 - 41*(-x + 2)**5/15625 + x/5 + O((x - 2)**6, (x, 2)))

    f = x*atan(x) - log(1 + x**2) / 2
    assert fps(f, x, full=True).truncate() == x**2/2 - x**4/12 + O(x**6)

    f = log((1 + x) / (1 - x)) / 2 - atan(x)
    assert fps(f, x, full=True).truncate(n=10) == 2*x**3/3 + 2*x**7/7 + O(x**10)


@slow
def test_fps__hyper():
    f = sin(x)
    assert fps(f, x).truncate() == x - x**3/6 + x**5/120 + O(x**6)

    f = cos(x)
    assert fps(f, x).truncate() == 1 - x**2/2 + x**4/24 + O(x**6)

    f = exp(x)
    assert fps(f, x).truncate() == \
        1 + x + x**2/2 + x**3/6 + x**4/24 + x**5/120 + O(x**6)

    f = atan(x)
    assert fps(f, x).truncate() == x - x**3/3 + x**5/5 + O(x**6)

    f = exp(acos(x))
    assert fps(f, x).truncate() == \
        (exp(pi/2) - x*exp(pi/2) + x**2*exp(pi/2)/2 - x**3*exp(pi/2)/3 +
         5*x**4*exp(pi/2)/24 - x**5*exp(pi/2)/6 + O(x**6))

    f = exp(acosh(x))
    assert fps(f, x).truncate() == I + x - I*x**2/2 - I*x**4/8 + O(x**6)

    f = atan(1/x)
    assert fps(f, x).truncate() == pi/2 - x + x**3/3 - x**5/5 + O(x**6)

    f = x*atan(x) - log(1 + x**2) / 2
    assert fps(f, x, rational=False).truncate() == x**2/2 - x**4/12 + O(x**6)

    f = log(1 + x)
    assert fps(f, x, rational=False).truncate() == \
        x - x**2/2 + x**3/3 - x**4/4 + x**5/5 + O(x**6)

    f = airyai(x**2)
    assert fps(f, x).truncate() == \
        (3**Rational(5, 6)*gamma(Rational(1, 3))/(6*pi) -
         3**Rational(2, 3)*x**2/(3*gamma(Rational(1, 3))) + O(x**6))

    f = exp(x)*sin(x)
    assert fps(f, x).truncate() == x + x**2 + x**3/3 - x**5/30 + O(x**6)

    f = exp(x)*sin(x)/x
    assert fps(f, x).truncate() == 1 + x + x**2/3 - x**4/30 - x**5/90 + O(x**6)

    f = sin(x) * cos(x)
    assert fps(f, x).truncate() == x - 2*x**3/3 + 2*x**5/15 + O(x**6)


def test_fps_shift():
    f = x**-5*sin(x)
    assert fps(f, x).truncate() == \
        1/x**4 - 1/(6*x**2) + S.One/120 - x**2/5040 + x**4/362880 + O(x**6)

    f = x**2*atan(x)
    assert fps(f, x, rational=False).truncate() == \
        x**3 - x**5/3 + O(x**6)

    f = cos(sqrt(x))*x
    assert fps(f, x).truncate() == \
        x - x**2/2 + x**3/24 - x**4/720 + x**5/40320 + O(x**6)

    f = x**2*cos(sqrt(x))
    assert fps(f, x).truncate() == \
        x**2 - x**3/2 + x**4/24 - x**5/720 + O(x**6)


def test_fps__Add_expr():
    f = x*atan(x) - log(1 + x**2) / 2
    assert fps(f, x).truncate() == x**2/2 - x**4/12 + O(x**6)

    f = sin(x) + cos(x) - exp(x) + log(1 + x)
    assert fps(f, x).truncate() == x - 3*x**2/2 - x**4/4 + x**5/5 + O(x**6)

    f = 1/x + sin(x)
    assert fps(f, x).truncate() == 1/x + x - x**3/6 + x**5/120 + O(x**6)

    f = sin(x) - cos(x) + 1/(x - 1)
    assert fps(f, x).truncate() == \
        -2 - x**2/2 - 7*x**3/6 - 25*x**4/24 - 119*x**5/120 + O(x**6)


def test_fps__asymptotic():
    f = exp(x)
    assert fps(f, x, oo) == f
    assert fps(f, x, -oo).truncate() == O(1/x**6, (x, oo))

    f = erf(x)
    assert fps(f, x, oo).truncate() == 1 + O(1/x**6, (x, oo))
    assert fps(f, x, -oo).truncate() == -1 + O(1/x**6, (x, oo))

    f = atan(x)
    assert fps(f, x, oo, full=True).truncate() == \
        -1/(5*x**5) + 1/(3*x**3) - 1/x + pi/2 + O(1/x**6, (x, oo))
    assert fps(f, x, -oo, full=True).truncate() == \
        -1/(5*x**5) + 1/(3*x**3) - 1/x - pi/2 + O(1/x**6, (x, oo))

    f = log(1 + x)
    assert fps(f, x, oo) != \
        (-1/(5*x**5) - 1/(4*x**4) + 1/(3*x**3) - 1/(2*x**2) + 1/x - log(1/x) +
         O(1/x**6, (x, oo)))
    assert fps(f, x, -oo) != \
        (-1/(5*x**5) - 1/(4*x**4) + 1/(3*x**3) - 1/(2*x**2) + 1/x + I*pi -
         log(-1/x) + O(1/x**6, (x, oo)))


def test_fps__fractional():
    f = sin(sqrt(x)) / x
    assert fps(f, x).truncate() == \
        (1/sqrt(x) - sqrt(x)/6 + x**Rational(3, 2)/120 -
         x**Rational(5, 2)/5040 + x**Rational(7, 2)/362880 -
         x**Rational(9, 2)/39916800 + x**Rational(11, 2)/6227020800 + O(x**6))

    f = sin(sqrt(x)) * x
    assert fps(f, x).truncate() == \
        (x**Rational(3, 2) - x**Rational(5, 2)/6 + x**Rational(7, 2)/120 -
         x**Rational(9, 2)/5040 + x**Rational(11, 2)/362880 + O(x**6))

    f = atan(sqrt(x)) / x**2
    assert fps(f, x).truncate() == \
        (x**Rational(-3, 2) - x**Rational(-1, 2)/3 + x**Rational(1, 2)/5 -
         x**Rational(3, 2)/7 + x**Rational(5, 2)/9 - x**Rational(7, 2)/11 +
         x**Rational(9, 2)/13 - x**Rational(11, 2)/15 + O(x**6))

    f = exp(sqrt(x))
    assert fps(f, x).truncate().expand() == \
        (1 + x/2 + x**2/24 + x**3/720 + x**4/40320 + x**5/3628800 + sqrt(x) +
         x**Rational(3, 2)/6 + x**Rational(5, 2)/120 + x**Rational(7, 2)/5040 +
         x**Rational(9, 2)/362880 + x**Rational(11, 2)/39916800 + O(x**6))

    f = exp(sqrt(x))*x
    assert fps(f, x).truncate().expand() == \
        (x + x**2/2 + x**3/24 + x**4/720 + x**5/40320 + x**Rational(3, 2) +
         x**Rational(5, 2)/6 + x**Rational(7, 2)/120 + x**Rational(9, 2)/5040 +
         x**Rational(11, 2)/362880 + O(x**6))


def test_fps__logarithmic_singularity():
    f = log(1 + 1/x)
    assert fps(f, x) != \
        -log(x) + x - x**2/2 + x**3/3 - x**4/4 + x**5/5 + O(x**6)
    assert fps(f, x, rational=False) != \
        -log(x) + x - x**2/2 + x**3/3 - x**4/4 + x**5/5 + O(x**6)


@XFAIL
def test_fps__logarithmic_singularity_fail():
    f = asech(x)  # Algorithms for computing limits probably needs improvemnts
    assert fps(f, x) == log(2) - log(x) - x**2/4 - 3*x**4/64 + O(x**6)


@XFAIL
def test_fps__symbolic():
    f = x**n*sin(x**2)
    assert fps(f, x).truncate(8) == x**2*x**n - x**6*x**n/6 + O(x**(n + 8), x)

    f = x**(n - 2)*cos(x)
    assert fps(f, x).truncate() == \
        (x**n*(-S(1)/2 + x**(-2)) + x**2*x**n/24 - x**4*x**n/720 +
         O(x**(n + 6), x))

    f = x**n*log(1 + x)
    fp = fps(f, x)
    k = fp.ak.variables[0]
    assert fp.infinite == \
        Sum((-(-1)**(-k)*x**k*x**n)/k, (k, 1, oo))

    f = x**(n - 2)*sin(x) + x**n*exp(x)
    assert fps(f, x).truncate() == \
        (x**n*(1 + 1/x) + 5*x*x**n/6 + x**2*x**n/2 + 7*x**3*x**n/40 +
         x**4*x**n/24 + 41*x**5*x**n/5040 + O(x**(n + 6), x))

    f = (x - 2)**n*log(1 + x)
    assert fps(f, x, 2).truncate() == \
        ((x - 2)**n*log(3) - (x - 2)**2*(x - 2)**n/18 +
         (x - 2)**3*(x - 2)**n/81 - (x - 2)**4*(x - 2)**n/324 +
         (x - 2)**5*(x - 2)**n/1215 + (x/3 - S(2)/3)*(x - 2)**n +
         O((x - 2)**(n + 6), (x, 2)))

    f = x**n*atan(x)
    assert fps(f, x, oo).truncate() == \
        (-x**n/(5*x**5) + x**n/(3*x**3) + x**n*(pi/2 - 1/x) +
         O(x**(n - 6), (x, oo)))


def test_fps__slow():
    f = x*exp(x)*sin(2*x)  # TODO: rsolve needs improvement
    assert fps(f, x).truncate() == 2*x**2 + 2*x**3 - x**4/3 - x**5 + O(x**6)


def test_fps__operations():
    f1, f2 = fps(sin(x)), fps(cos(x))

    fsum = f1 + f2
    assert fsum.function == sin(x) + cos(x)
    assert fsum.truncate() == \
        1 + x - x**2/2 - x**3/6 + x**4/24 + x**5/120 + O(x**6)

    fsum = f1 + 1
    assert fsum.function == sin(x) + 1
    assert fsum.truncate() == 1 + x - x**3/6 + x**5/120 + O(x**6)

    fsum = 1 + f2
    assert fsum.function == cos(x) + 1
    assert fsum.truncate() == 2 - x**2/2 + x**4/24 + O(x**6)

    assert (f1 + x) == Add(f1, x)

    assert -f2.truncate() == -1 + x**2/2 - x**4/24 + O(x**6)
    assert (f1 - f1) == S.Zero

    fsub = f1 - f2
    assert fsub.function == sin(x) - cos(x)
    assert fsub.truncate() == \
        -1 + x + x**2/2 - x**3/6 - x**4/24 + x**5/120 + O(x**6)

    fsub = f1 - 1
    assert fsub.function == sin(x) - 1
    assert fsub.truncate() == -1 + x - x**3/6 + x**5/120 + O(x**6)

    fsub = 1 - f2
    assert fsub.function == -cos(x) + 1
    assert fsub.truncate() == x**2/2 - x**4/24 + O(x**6)

    raises(ValueError, lambda: f1 + fps(exp(x), dir=-1))
    raises(ValueError, lambda: f1 + fps(exp(x), x0=1))

    fm = f1 * 3

    assert fm.function == 3*sin(x)
    assert fm.truncate() == 3*x - x**3/2 + x**5/40 + O(x**6)

    fm = 3 * f2

    assert fm.function == 3*cos(x)
    assert fm.truncate() == 3 - 3*x**2/2 + x**4/8 + O(x**6)

    assert (f1 * f2) == Mul(f1, f2)
    assert (f1 * x) == Mul(f1, x)

    fd = f1.diff()
    assert fd.function == cos(x)
    assert fd.truncate() == 1 - x**2/2 + x**4/24 + O(x**6)

    fd = f2.diff()
    assert fd.function == -sin(x)
    assert fd.truncate() == -x + x**3/6 - x**5/120 + O(x**6)

    fd = f2.diff().diff()
    assert fd.function == -cos(x)
    assert fd.truncate() == -1 + x**2/2 - x**4/24 + O(x**6)

    f3 = fps(exp(sqrt(x)))
    fd = f3.diff()
    assert fd.truncate().expand() == \
        (1/(2*sqrt(x)) + S(1)/2 + x/12 + x**2/240 + x**3/10080 + x**4/725760 +
         x**5/79833600 + sqrt(x)/4 + x**(S(3)/2)/48 + x**(S(5)/2)/1440 +
         x**(S(7)/2)/80640 + x**(S(9)/2)/7257600 + x**(S(11)/2)/958003200 +
         O(x**6))

    assert f1.integrate((x, 0, 1)) == -cos(1) + 1
    assert integrate(f1, (x, 0, 1)) == -cos(1) + 1

    fi = integrate(f1, x)
    assert fi.function == -cos(x)
    assert fi.truncate() == -1 + x**2/2 - x**4/24 + O(x**6)

    fi = f2.integrate(x)
    assert fi.function == sin(x)
    assert fi.truncate() == x - x**3/6 + x**5/120 + O(x**6)
