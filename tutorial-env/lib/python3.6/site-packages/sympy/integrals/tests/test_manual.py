from sympy import (sin, cos, tan, sec, csc, cot, log, exp, atan, asin, acos,
                   Symbol, Integral, integrate, pi, Dummy, Derivative,
                   diff, I, sqrt, erf, Piecewise, Eq, Ne, symbols, Rational,
                   And, Heaviside, S, asinh, acosh, atanh, acoth, expand,
                   Function, jacobi, gegenbauer, chebyshevt, chebyshevu,
                   legendre, hermite, laguerre, assoc_laguerre, uppergamma, li,
                   Ei, Ci, Si, Chi, Shi, fresnels, fresnelc, polylog, erf, erfi,
                   sinh, cosh, elliptic_f, elliptic_e)
from sympy.integrals.manualintegrate import (manualintegrate, find_substitutions,
    _parts_rule, integral_steps, contains_dont_know, manual_subs)
from sympy.utilities.pytest import slow

x, y, z, u, n, a, b, c = symbols('x y z u n a b c')
f = Function('f')

def test_find_substitutions():
    assert find_substitutions((cot(x)**2 + 1)**2*csc(x)**2*cot(x)**2, x, u) == \
        [(cot(x), 1, -u**6 - 2*u**4 - u**2)]
    assert find_substitutions((sec(x)**2 + tan(x) * sec(x)) / (sec(x) + tan(x)),
                              x, u) == [(sec(x) + tan(x), 1, 1/u)]
    assert find_substitutions(x * exp(-x**2), x, u) == [(-x**2, -S.Half, exp(u))]


def test_manualintegrate_polynomials():
    assert manualintegrate(y, x) == x*y
    assert manualintegrate(exp(2), x) == x * exp(2)
    assert manualintegrate(x**2, x) == x**3 / 3
    assert manualintegrate(3 * x**2 + 4 * x**3, x) == x**3 + x**4

    assert manualintegrate((x + 2)**3, x) == (x + 2)**4 / 4
    assert manualintegrate((3*x + 4)**2, x) == (3*x + 4)**3 / 9

    assert manualintegrate((u + 2)**3, u) == (u + 2)**4 / 4
    assert manualintegrate((3*u + 4)**2, u) == (3*u + 4)**3 / 9


def test_manualintegrate_exponentials():
    assert manualintegrate(exp(2*x), x) == exp(2*x) / 2
    assert manualintegrate(2**x, x) == (2 ** x) / log(2)

    assert manualintegrate(1 / x, x) == log(x)
    assert manualintegrate(1 / (2*x + 3), x) == log(2*x + 3) / 2
    assert manualintegrate(log(x)**2 / x, x) == log(x)**3 / 3


def test_manualintegrate_parts():
    assert manualintegrate(exp(x) * sin(x), x) == \
        (exp(x) * sin(x)) / 2 - (exp(x) * cos(x)) / 2
    assert manualintegrate(2*x*cos(x), x) == 2*x*sin(x) + 2*cos(x)
    assert manualintegrate(x * log(x), x) == x**2*log(x)/2 - x**2/4
    assert manualintegrate(log(x), x) == x * log(x) - x
    assert manualintegrate((3*x**2 + 5) * exp(x), x) == \
        3*x**2*exp(x) - 6*x*exp(x) + 11*exp(x)
    assert manualintegrate(atan(x), x) == x*atan(x) - log(x**2 + 1)/2
    # Make sure _parts_rule does not go into an infinite loop here
    assert manualintegrate(log(1/x)/(x + 1), x).has(Integral)

    # Make sure _parts_rule doesn't pick u = constant but can pick dv =
    # constant if necessary, e.g. for integrate(atan(x))
    assert _parts_rule(cos(x), x) == None
    assert _parts_rule(exp(x), x) == None
    assert _parts_rule(x**2, x) == None
    result = _parts_rule(atan(x), x)
    assert result[0] == atan(x) and result[1] == 1


def test_manualintegrate_trigonometry():
    assert manualintegrate(sin(x), x) == -cos(x)
    assert manualintegrate(tan(x), x) == -log(cos(x))

    assert manualintegrate(sec(x), x) == log(sec(x) + tan(x))
    assert manualintegrate(csc(x), x) == -log(csc(x) + cot(x))

    assert manualintegrate(sin(x) * cos(x), x) in [sin(x) ** 2 / 2, -cos(x)**2 / 2]
    assert manualintegrate(-sec(x) * tan(x), x) == -sec(x)
    assert manualintegrate(csc(x) * cot(x), x) == -csc(x)
    assert manualintegrate(sec(x)**2, x) == tan(x)
    assert manualintegrate(csc(x)**2, x) == -cot(x)

    assert manualintegrate(x * sec(x**2), x) == log(tan(x**2) + sec(x**2))/2
    assert manualintegrate(cos(x)*csc(sin(x)), x) == -log(cot(sin(x)) + csc(sin(x)))
    assert manualintegrate(cos(3*x)*sec(x), x) == -x + sin(2*x)
    assert manualintegrate(sin(3*x)*sec(x), x) == \
        -3*log(cos(x)) + 2*log(cos(x)**2) - 2*cos(x)**2


def test_manualintegrate_trigpowers():
    assert manualintegrate(sin(x)**2 * cos(x), x) == sin(x)**3 / 3
    assert manualintegrate(sin(x)**2 * cos(x) **2, x) == \
        x / 8 - sin(4*x) / 32
    assert manualintegrate(sin(x) * cos(x)**3, x) == -cos(x)**4 / 4
    assert manualintegrate(sin(x)**3 * cos(x)**2, x) == \
        cos(x)**5 / 5 - cos(x)**3 / 3

    assert manualintegrate(tan(x)**3 * sec(x), x) == sec(x)**3/3 - sec(x)
    assert manualintegrate(tan(x) * sec(x) **2, x) == sec(x)**2/2

    assert manualintegrate(cot(x)**5 * csc(x), x) == \
        -csc(x)**5/5 + 2*csc(x)**3/3 - csc(x)
    assert manualintegrate(cot(x)**2 * csc(x)**6, x) == \
        -cot(x)**7/7 - 2*cot(x)**5/5 - cot(x)**3/3


def test_manualintegrate_inversetrig():
    # atan
    assert manualintegrate(exp(x) / (1 + exp(2*x)), x) == atan(exp(x))
    assert manualintegrate(1 / (4 + 9 * x**2), x) == atan(3 * x/2) / 6
    assert manualintegrate(1 / (16 + 16 * x**2), x) == atan(x) / 16
    assert manualintegrate(1 / (4 + x**2), x) == atan(x / 2) / 2
    assert manualintegrate(1 / (1 + 4 * x**2), x) == atan(2*x) / 2
    assert manualintegrate(1/(a + b*x**2), x) == \
        Piecewise((atan(x/sqrt(a/b))/(b*sqrt(a/b)), a/b > 0), \
                  (-acoth(x/sqrt(-a/b))/(b*sqrt(-a/b)), And(a/b < 0, x**2 > -a/b)), \
                  (-atanh(x/sqrt(-a/b))/(b*sqrt(-a/b)), And(a/b < 0, x**2 < -a/b)))
    assert manualintegrate(1/(4 + b*x**2), x) == \
        Piecewise((atan(x/(2*sqrt(1/b)))/(2*b*sqrt(1/b)), 4/b > 0), \
                  (-acoth(x/(2*sqrt(-1/b)))/(2*b*sqrt(-1/b)), And(4/b < 0, x**2 > -4/b)), \
                  (-atanh(x/(2*sqrt(-1/b)))/(2*b*sqrt(-1/b)), And(4/b < 0, x**2 < -4/b)))
    assert manualintegrate(1/(a + 4*x**2), x) == \
        Piecewise((atan(2*x/sqrt(a))/(2*sqrt(a)), a/4 > 0), \
                  (-acoth(2*x/sqrt(-a))/(2*sqrt(-a)), And(a/4 < 0, x**2 > -a/4)), \
                  (-atanh(2*x/sqrt(-a))/(2*sqrt(-a)), And(a/4 < 0, x**2 < -a/4)))
    assert manualintegrate(1/(4 + 4*x**2), x) == atan(x) / 4

    # asin
    assert manualintegrate(1/sqrt(1-x**2), x) == asin(x)
    assert manualintegrate(1/sqrt(4-4*x**2), x) == asin(x)/2
    assert manualintegrate(3/sqrt(1-9*x**2), x) == asin(3*x)
    assert manualintegrate(1/sqrt(4-9*x**2), x) == asin(3*x/2)/3

    # asinh
    assert manualintegrate(1/sqrt(x**2 + 1), x) == \
        asinh(x)
    assert manualintegrate(1/sqrt(x**2 + 4), x) == \
        asinh(x/2)
    assert manualintegrate(1/sqrt(4*x**2 + 4), x) == \
        asinh(x)/2
    assert manualintegrate(1/sqrt(4*x**2 + 1), x) == \
        asinh(2*x)/2
    assert manualintegrate(1/sqrt(a*x**2 + 1), x) == \
        Piecewise((sqrt(-1/a)*asin(x*sqrt(-a)), a < 0), (sqrt(1/a)*asinh(sqrt(a)*x), a > 0))
    assert manualintegrate(1/sqrt(a + x**2), x) == \
        Piecewise((asinh(x*sqrt(1/a)), a > 0), (acosh(x*sqrt(-1/a)), a < 0))

    # acosh
    assert manualintegrate(1/sqrt(x**2 - 1), x) == \
        acosh(x)
    assert manualintegrate(1/sqrt(x**2 - 4), x) == \
        acosh(x/2)
    assert manualintegrate(1/sqrt(4*x**2 - 4), x) == \
        acosh(x)/2
    assert manualintegrate(1/sqrt(9*x**2 - 1), x) == \
        acosh(3*x)/3
    assert manualintegrate(1/sqrt(a*x**2 - 4), x) == \
        Piecewise((sqrt(1/a)*acosh(sqrt(a)*x/2), a > 0))
    assert manualintegrate(1/sqrt(-a + 4*x**2), x) == \
        Piecewise((asinh(2*x*sqrt(-1/a))/2, -a > 0), (acosh(2*x*sqrt(1/a))/2, -a < 0))

    # piecewise
    assert manualintegrate(1/sqrt(a-b*x**2), x) == \
        Piecewise((sqrt(a/b)*asin(x*sqrt(b/a))/sqrt(a), And(-b < 0, a > 0)),
                  (sqrt(-a/b)*asinh(x*sqrt(-b/a))/sqrt(a), And(-b > 0, a > 0)),
                  (sqrt(a/b)*acosh(x*sqrt(b/a))/sqrt(-a), And(-b > 0, a < 0)))
    assert manualintegrate(1/sqrt(a + b*x**2), x) == \
        Piecewise((sqrt(-a/b)*asin(x*sqrt(-b/a))/sqrt(a), And(a > 0, b < 0)),
                  (sqrt(a/b)*asinh(x*sqrt(b/a))/sqrt(a), And(a > 0, b > 0)),
                  (sqrt(-a/b)*acosh(x*sqrt(-b/a))/sqrt(-a), And(a < 0, b > 0)))


def test_manualintegrate_trig_substitution():
    assert manualintegrate(sqrt(16*x**2 - 9)/x, x) == \
        Piecewise((sqrt(16*x**2 - 9) - 3*acos(3/(4*x)),
                   And(x < 3*S.One/4, x > -3*S.One/4)))
    assert manualintegrate(1/(x**4 * sqrt(25-x**2)), x) == \
        Piecewise((-sqrt(-x**2/25 + 1)/(125*x) -
                   (-x**2/25 + 1)**(3*S.Half)/(15*x**3), And(x < 5, x > -5)))
    assert manualintegrate(x**7/(49*x**2 + 1)**(3 * S.Half), x) == \
        ((49*x**2 + 1)**(5*S.Half)/28824005 -
         (49*x**2 + 1)**(3*S.Half)/5764801 +
         3*sqrt(49*x**2 + 1)/5764801 + 1/(5764801*sqrt(49*x**2 + 1)))

def test_manualintegrate_trivial_substitution():
    assert manualintegrate((exp(x) - exp(-x))/x, x) == -Ei(-x) + Ei(x)
    f = Function('f')
    assert manualintegrate((f(x) - f(-x))/x, x) == \
        -Integral(f(-x)/x, x) + Integral(f(x)/x, x)

def test_manualintegrate_rational():
    assert manualintegrate(1/(4 - x**2), x) == Piecewise((acoth(x/2)/2, x**2 > 4), (atanh(x/2)/2, x**2 < 4))
    assert manualintegrate(1/(-1 + x**2), x) == Piecewise((-acoth(x), x**2 > 1), (-atanh(x), x**2 < 1))

def test_manualintegrate_special():
    f, F = 4*exp(-x**2/3), 2*sqrt(3)*sqrt(pi)*erf(sqrt(3)*x/3)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = 3*exp(4*x**2), 3*sqrt(pi)*erfi(2*x)/4
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = x**(S(1)/3)*exp(-x/8), -16*uppergamma(S(4)/3, x/8)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = exp(2*x)/x, Ei(2*x)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = exp(1 + 2*x - x**2), sqrt(pi)*exp(2)*erf(x - 1)/2
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f = sin(x**2 + 4*x + 1)
    F = (sqrt(2)*sqrt(pi)*(-sin(3)*fresnelc(sqrt(2)*(2*x + 4)/(2*sqrt(pi))) +
        cos(3)*fresnels(sqrt(2)*(2*x + 4)/(2*sqrt(pi))))/2)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = cos(4*x**2), sqrt(2)*sqrt(pi)*fresnelc(2*sqrt(2)*x/sqrt(pi))/4
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = sin(3*x + 2)/x, sin(2)*Ci(3*x) + cos(2)*Si(3*x)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = sinh(3*x - 2)/x, -sinh(2)*Chi(3*x) + cosh(2)*Shi(3*x)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = 5*cos(2*x - 3)/x, 5*cos(3)*Ci(2*x) + 5*sin(3)*Si(2*x)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = cosh(x/2)/x, Chi(x/2)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = cos(x**2)/x, Ci(x**2)/2
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = 1/log(2*x + 1), li(2*x + 1)/2
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = polylog(2, 5*x)/x, polylog(3, 5*x)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = 5/sqrt(3 - 2*sin(x)**2), 5*sqrt(3)*elliptic_f(x, S(2)/3)/3
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
    f, F = sqrt(4 + 9*sin(x)**2), 2*elliptic_e(x, -S(9)/4)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)


def test_manualintegrate_derivative():
    assert manualintegrate(pi * Derivative(x**2 + 2*x + 3), x) == \
        pi * ((x**2 + 2*x + 3))
    assert manualintegrate(Derivative(x**2 + 2*x + 3, y), x) == \
        Integral(Derivative(x**2 + 2*x + 3, y))
    assert manualintegrate(Derivative(sin(x), x, x, x, y), x) == \
        Derivative(sin(x), x, x, y)


def test_manualintegrate_Heaviside():
    assert manualintegrate(Heaviside(x), x) == x*Heaviside(x)
    assert manualintegrate(x*Heaviside(2), x) == x**2/2
    assert manualintegrate(x*Heaviside(-2), x) == 0
    assert manualintegrate(x*Heaviside( x), x) == x**2*Heaviside( x)/2
    assert manualintegrate(x*Heaviside(-x), x) == x**2*Heaviside(-x)/2
    assert manualintegrate(Heaviside(2*x + 4), x) == (x+2)*Heaviside(2*x + 4)
    assert manualintegrate(x*Heaviside(x), x) == x**2*Heaviside(x)/2
    assert manualintegrate(Heaviside(x + 1)*Heaviside(1 - x)*x**2, x) == \
        ((x**3/3 + S(1)/3)*Heaviside(x + 1) - S(2)/3)*Heaviside(-x + 1)

    y = Symbol('y')
    assert manualintegrate(sin(7 + x)*Heaviside(3*x - 7), x) == \
            (- cos(x + 7) + cos(S(28)/3))*Heaviside(3*x - S(7))

    assert manualintegrate(sin(y + x)*Heaviside(3*x - y), x) == \
            (cos(4*y/3) - cos(x + y))*Heaviside(3*x - y)


def test_manualintegrate_orthogonal_poly():
    n = symbols('n')
    a, b = 7, S(5)/3
    polys = [jacobi(n, a, b, x), gegenbauer(n, a, x), chebyshevt(n, x),
        chebyshevu(n, x), legendre(n, x), hermite(n, x), laguerre(n, x),
        assoc_laguerre(n, a, x)]
    for p in polys:
        integral = manualintegrate(p, x)
        for deg in [-2, -1, 0, 1, 3, 5, 8]:
            # some accept negative "degree", some do not
            try:
                p_subbed = p.subs(n, deg)
            except ValueError:
                continue
            assert (integral.subs(n, deg).diff(x) - p_subbed).expand() == 0

        # can also integrate simple expressions with these polynomials
        q = x*p.subs(x, 2*x + 1)
        integral = manualintegrate(q, x)
        for deg in [2, 4, 7]:
            assert (integral.subs(n, deg).diff(x) - q.subs(n, deg)).expand() == 0

        # cannot integrate with respect to any other parameter
        t = symbols('t')
        for i in range(len(p.args) - 1):
            new_args = list(p.args)
            new_args[i] = t
            assert isinstance(manualintegrate(p.func(*new_args), t), Integral)

def test_issue_6799():
    r, x, phi = map(Symbol, 'r x phi'.split())
    n = Symbol('n', integer=True, positive=True)

    integrand = (cos(n*(x-phi))*cos(n*x))
    limits = (x, -pi, pi)
    assert manualintegrate(integrand, x) == \
        ((n*x/2 + sin(2*n*x)/4)*cos(n*phi) - sin(n*phi)*cos(n*x)**2/2)/n
    assert r * integrate(integrand, limits).trigsimp() / pi == r * cos(n * phi)
    assert not integrate(integrand, limits).has(Dummy)


def test_issue_12251():
    assert manualintegrate(x**y, x) == Piecewise(
        (x**(y + 1)/(y + 1), Ne(y, -1)), (log(x), True))


def test_issue_3796():
    assert manualintegrate(diff(exp(x + x**2)), x) == exp(x + x**2)
    assert integrate(x * exp(x**4), x, risch=False) == -I*sqrt(pi)*erf(I*x**2)/4


def test_manual_true():
    assert integrate(exp(x) * sin(x), x, manual=True) == \
        (exp(x) * sin(x)) / 2 - (exp(x) * cos(x)) / 2
    assert integrate(sin(x) * cos(x), x, manual=True) in \
        [sin(x) ** 2 / 2, -cos(x)**2 / 2]


def test_issue_6746():
    y = Symbol('y')
    n = Symbol('n')
    assert manualintegrate(y**x, x) == Piecewise(
        (y**x/log(y), Ne(log(y), 0)), (x, True))
    assert manualintegrate(y**(n*x), x) == Piecewise(
        (Piecewise(
            (y**(n*x)/log(y), Ne(log(y), 0)),
            (n*x, True)
        )/n, Ne(n, 0)),
        (x, True))
    assert manualintegrate(exp(n*x), x) == Piecewise(
        (exp(n*x)/n, Ne(n, 0)), (x, True))

    y = Symbol('y', positive=True)
    assert manualintegrate((y + 1)**x, x) == (y + 1)**x/log(y + 1)
    y = Symbol('y', zero=True)
    assert manualintegrate((y + 1)**x, x) == x
    y = Symbol('y')
    n = Symbol('n', nonzero=True)
    assert manualintegrate(y**(n*x), x) == Piecewise(
        (y**(n*x)/log(y), Ne(log(y), 0)), (n*x, True))/n
    y = Symbol('y', positive=True)
    assert manualintegrate((y + 1)**(n*x), x) == \
        (y + 1)**(n*x)/(n*log(y + 1))
    a = Symbol('a', negative=True)
    b = Symbol('b')
    assert manualintegrate(1/(a + b*x**2), x) == \
        Piecewise((atan(x/sqrt(a/b))/(b*sqrt(a/b)), a/b > 0), \
        (-acoth(x/sqrt(-a/b))/(b*sqrt(-a/b)), And(a/b < 0, x**2 > -a/b)), \
        (-atanh(x/sqrt(-a/b))/(b*sqrt(-a/b)), And(a/b < 0, x**2 < -a/b)))
    b = Symbol('b', negative=True)
    assert manualintegrate(1/(a + b*x**2), x) == \
        atan(x/(sqrt(-a)*sqrt(-1/b)))/(b*sqrt(-a)*sqrt(-1/b))
    assert manualintegrate(1/((x**a + y**b + 4)*sqrt(a*x**2 + 1)), x) == \
        y**(-b)*Integral(x**(-a)/(y**(-b)*sqrt(a*x**2 + 1) +
        x**(-a)*sqrt(a*x**2 + 1) + 4*x**(-a)*y**(-b)*sqrt(a*x**2 + 1)), x)
    assert manualintegrate(1/((x**2 + 4)*sqrt(4*x**2 + 1)), x) == \
        Integral(1/((x**2 + 4)*sqrt(4*x**2 + 1)), x)
    assert manualintegrate(1/(x - a**x + x*b**2), x) == \
        Integral(1/(-a**x + b**2*x + x), x)


@slow
def test_issue_2850():
    assert manualintegrate(asin(x)*log(x), x) == -x*asin(x) - sqrt(-x**2 + 1) \
            + (x*asin(x) + sqrt(-x**2 + 1))*log(x) - Integral(sqrt(-x**2 + 1)/x, x)
    assert manualintegrate(acos(x)*log(x), x) == -x*acos(x) + sqrt(-x**2 + 1) + \
        (x*acos(x) - sqrt(-x**2 + 1))*log(x) + Integral(sqrt(-x**2 + 1)/x, x)
    assert manualintegrate(atan(x)*log(x), x) == -x*atan(x) + (x*atan(x) - \
            log(x**2 + 1)/2)*log(x) + log(x**2 + 1)/2 + Integral(log(x**2 + 1)/x, x)/2

def test_issue_9462():
    assert manualintegrate(sin(2*x)*exp(x), x) == exp(x)*sin(2*x)/5 - 2*exp(x)*cos(2*x)/5
    assert not contains_dont_know(integral_steps(sin(2*x)*exp(x), x))
    assert manualintegrate((x - 3) / (x**2 - 2*x + 2)**2, x) == \
                           Integral(x/(x**4 - 4*x**3 + 8*x**2 - 8*x + 4), x) \
                           - 3*Integral(1/(x**4 - 4*x**3 + 8*x**2 - 8*x + 4), x)


def test_cyclic_parts():
    f = cos(x)*exp(x/4)
    F = 16*exp(x/4)*sin(x)/17 + 4*exp(x/4)*cos(x)/17
    assert manualintegrate(f, x) == F and F.diff(x) == f
    f = x*cos(x)*exp(x/4)
    F = (x*(16*exp(x/4)*sin(x)/17 + 4*exp(x/4)*cos(x)/17) -
        128*exp(x/4)*sin(x)/289 + 240*exp(x/4)*cos(x)/289)
    assert manualintegrate(f, x) == F and F.diff(x) == f


@slow
def test_issue_10847():
    assert manualintegrate(x**2 / (x**2 - c), x) == c*Piecewise((atan(x/sqrt(-c))/sqrt(-c), -c > 0), \
                                                                (-acoth(x/sqrt(c))/sqrt(c), And(-c < 0, x**2 > c)), \
                                                                (-atanh(x/sqrt(c))/sqrt(c), And(-c < 0, x**2 < c))) + x
    assert manualintegrate(sqrt(x - y) * log(z / x), x) == 4*y**2*Piecewise((atan(sqrt(x - y)/sqrt(y))/sqrt(y), y > 0), \
                                                                            (-acoth(sqrt(x - y)/sqrt(-y))/sqrt(-y), \
                                                                             And(x - y > -y, y < 0)), \
                                                                            (-atanh(sqrt(x - y)/sqrt(-y))/sqrt(-y), \
                                                                             And(x - y < -y, y < 0)))/3 \
                                                                             - 4*y*sqrt(x - y)/3 + 2*(x - y)**(S(3)/2)*log(z/x)/3 \
                                                                             + 4*(x - y)**(S(3)/2)/9

    assert manualintegrate(sqrt(x) * log(x), x) == 2*x**(S(3)/2)*log(x)/3 - 4*x**(S(3)/2)/9
    assert manualintegrate(sqrt(a*x + b) / x, x) == -2*b*Piecewise((-atan(sqrt(a*x + b)/sqrt(-b))/sqrt(-b), -b > 0), \
                                                               (acoth(sqrt(a*x + b)/sqrt(b))/sqrt(b), And(-b < 0, a*x + b > b)), \
                                                               (atanh(sqrt(a*x + b)/sqrt(b))/sqrt(b), And(-b < 0, a*x + b < b))) \
                                                               + 2*sqrt(a*x + b)

    assert expand(manualintegrate(sqrt(a*x + b) / (x + c), x)) == -2*a*c*Piecewise((atan(sqrt(a*x + b)/sqrt(a*c - b))/sqrt(a*c - b), \
        a*c - b > 0), (-acoth(sqrt(a*x + b)/sqrt(-a*c + b))/sqrt(-a*c + b), And(a*c - b < 0, a*x + b > -a*c + b)), \
        (-atanh(sqrt(a*x + b)/sqrt(-a*c + b))/sqrt(-a*c + b), And(a*c - b < 0, a*x + b < -a*c + b))) \
        + 2*b*Piecewise((atan(sqrt(a*x + b)/sqrt(a*c - b))/sqrt(a*c - b), a*c - b > 0), \
        (-acoth(sqrt(a*x + b)/sqrt(-a*c + b))/sqrt(-a*c + b), And(a*c - b < 0, a*x + b > -a*c + b)), \
        (-atanh(sqrt(a*x + b)/sqrt(-a*c + b))/sqrt(-a*c + b), And(a*c - b < 0, a*x + b < -a*c + b))) + 2*sqrt(a*x + b)

    assert manualintegrate((4*x**4 + 4*x**3 + 16*x**2 + 12*x + 8) \
                           / (x**6 + 2*x**5 + 3*x**4 + 4*x**3 + 3*x**2 + 2*x + 1), x) == \
                           2*x/(x**2 + 1) + 3*atan(x) - 1/(x**2 + 1) - 3/(x + 1)
    assert manualintegrate(sqrt(2*x + 3) / (x + 1), x) == 2*sqrt(2*x + 3) - log(sqrt(2*x + 3) + 1) + log(sqrt(2*x + 3) - 1)
    assert manualintegrate(sqrt(2*x + 3) / 2 * x, x) == (2*x + 3)**(S(5)/2)/20 - (2*x + 3)**(S(3)/2)/4
    assert manualintegrate(x**Rational(3,2) * log(x), x) == 2*x**Rational(5,2)*log(x)/5 - 4*x**Rational(5,2)/25
    assert manualintegrate(x**(-3) * log(x), x) == -log(x)/(2*x**2) - 1/(4*x**2)
    assert manualintegrate(log(y)/(y**2*(1 - 1/y)), y) == \
        log(y)*log(-1 + 1/y) - Integral(log(-1 + 1/y)/y, y)

def test_issue_12899():
    assert manualintegrate(f(x,y).diff(x),y) == Integral(Derivative(f(x,y),x),y)
    assert manualintegrate(f(x,y).diff(y).diff(x),y) == Derivative(f(x,y),x)


def test_constant_independent_of_symbol():
    assert manualintegrate(Integral(y, (x, 1, 2)), x) == \
        x*Integral(y, (x, 1, 2))


def test_issue_12641():
    assert manualintegrate(sin(2*x), x) == -cos(2*x)/2
    assert manualintegrate(cos(x)*sin(2*x), x) == -2*cos(x)**3/3
    assert manualintegrate((sin(2*x)*cos(x))/(1 + cos(x)), x) == \
        -2*log(cos(x) + 1) - cos(x)**2 + 2*cos(x)


def test_issue_13297():
    assert manualintegrate(sin(x) * cos(x)**5, x) == -cos(x)**6 / 6

def test_issue_14470():
    assert manualintegrate(1/(x*sqrt(x + 1)), x) == \
        log(-1 + 1/sqrt(x + 1)) - log(1 + 1/sqrt(x + 1))


@slow
def test_issue_9858():
    assert manualintegrate(exp(x)*cos(exp(x)), x) == sin(exp(x))
    assert manualintegrate(exp(2*x)*cos(exp(x)), x) == \
        exp(x)*sin(exp(x)) + cos(exp(x))
    res = manualintegrate(exp(10*x)*sin(exp(x)), x)
    assert not res.has(Integral)
    assert res.diff(x) == exp(10*x)*sin(exp(x))
    # an example with many similar integrations by parts
    assert manualintegrate(sum([x*exp(k*x) for k in range(1, 8)]), x) == (
        x*exp(7*x)/7 + x*exp(6*x)/6 + x*exp(5*x)/5 + x*exp(4*x)/4 +
        x*exp(3*x)/3 + x*exp(2*x)/2 + x*exp(x) - exp(7*x)/49 -exp(6*x)/36 -
        exp(5*x)/25 - exp(4*x)/16 - exp(3*x)/9 - exp(2*x)/4 - exp(x))


def test_issue_8520():
    assert manualintegrate(x/(x**4 + 1), x) == atan(x**2)/2
    assert manualintegrate(x**2/(x**6 + 25), x) == atan(x**3/5)/15
    f = x/(9*x**4 + 4)**2
    assert manualintegrate(f, x).diff(x).factor() == f


def test_manual_subs():
    x, y = symbols('x y')
    expr = log(x) + exp(x)
    # if log(x) is y, then exp(y) is x
    assert manual_subs(expr, log(x), y) == y + exp(exp(y))
    # if exp(x) is y, then log(y) need not be x
    assert manual_subs(expr, exp(x), y) == log(x) + y


def test_issue_15471():
    f = log(x)*cos(log(x))/x**(S(3)/4)
    F = -128*x**(S(1)/4)*sin(log(x))/289 + 240*x**(S(1)/4)*cos(log(x))/289 + (16*x**(S(1)/4)*sin(log(x))/17 + 4*x**(S(1)/4)*cos(log(x))/17)*log(x)
    assert manualintegrate(f, x) == F and F.diff(x).equals(f)
