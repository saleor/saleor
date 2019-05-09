from sympy import (
    symbols, log, ln, Float, nan, oo, zoo, I, pi, E, exp, Symbol,
    LambertW, sqrt, Rational, expand_log, S, sign, conjugate, refine,
    sin, cos, sinh, cosh, tanh, exp_polar, re, Function, simplify,
    AccumBounds, MatrixSymbol, Pow)
from sympy.abc import x, y, z


def test_exp_values():
    k = Symbol('k', integer=True)

    assert exp(nan) == nan

    assert exp(oo) == oo
    assert exp(-oo) == 0

    assert exp(0) == 1
    assert exp(1) == E
    assert exp(-1 + x).as_base_exp() == (S.Exp1, x - 1)
    assert exp(1 + x).as_base_exp() == (S.Exp1, x + 1)

    assert exp(pi*I/2) == I
    assert exp(pi*I) == -1
    assert exp(3*pi*I/2) == -I
    assert exp(2*pi*I) == 1

    assert refine(exp(pi*I*2*k)) == 1
    assert refine(exp(pi*I*2*(k + Rational(1, 2)))) == -1
    assert refine(exp(pi*I*2*(k + Rational(1, 4)))) == I
    assert refine(exp(pi*I*2*(k + Rational(3, 4)))) == -I

    assert exp(log(x)) == x
    assert exp(2*log(x)) == x**2
    assert exp(pi*log(x)) == x**pi

    assert exp(17*log(x) + E*log(y)) == x**17 * y**E

    assert exp(x*log(x)) != x**x
    assert exp(sin(x)*log(x)) != x

    assert exp(3*log(x) + oo*x) == exp(oo*x) * x**3
    assert exp(4*log(x)*log(y) + 3*log(x)) == x**3 * exp(4*log(x)*log(y))


def test_exp_log():
    x = Symbol("x", real=True)
    assert log(exp(x)) == x
    assert exp(log(x)) == x
    assert log(x).inverse() == exp
    assert exp(x).inverse() == log

    y = Symbol("y", polar=True)
    assert log(exp_polar(z)) == z
    assert exp(log(y)) == y


def test_exp_expand():
    e = exp(log(Rational(2))*(1 + x) - log(Rational(2))*x)
    assert e.expand() == 2
    assert exp(x + y) != exp(x)*exp(y)
    assert exp(x + y).expand() == exp(x)*exp(y)


def test_exp__as_base_exp():
    assert exp(x).as_base_exp() == (E, x)
    assert exp(2*x).as_base_exp() == (E, 2*x)
    assert exp(x*y).as_base_exp() == (E, x*y)
    assert exp(-x).as_base_exp() == (E, -x)

    # Pow( *expr.as_base_exp() ) == expr    invariant should hold
    assert E**x == exp(x)
    assert E**(2*x) == exp(2*x)
    assert E**(x*y) == exp(x*y)

    assert exp(x).base is S.Exp1
    assert exp(x).exp == x


def test_exp_infinity():
    assert exp(I*y) != nan
    assert refine(exp(I*oo)) == nan
    assert refine(exp(-I*oo)) == nan
    assert exp(y*I*oo) != nan
    assert exp(zoo) == nan


def test_exp_subs():
    x = Symbol('x')
    e = (exp(3*log(x), evaluate=False))  # evaluates to x**3
    assert e.subs(x**3, y**3) == e
    assert e.subs(x**2, 5) == e
    assert (x**3).subs(x**2, y) != y**(3/S(2))
    assert exp(exp(x) + exp(x**2)).subs(exp(exp(x)), y) == y * exp(exp(x**2))
    assert exp(x).subs(E, y) == y**x
    x = symbols('x', real=True)
    assert exp(5*x).subs(exp(7*x), y) == y**Rational(5, 7)
    assert exp(2*x + 7).subs(exp(3*x), y) == y**Rational(2, 3) * exp(7)
    x = symbols('x', positive=True)
    assert exp(3*log(x)).subs(x**2, y) == y**Rational(3, 2)
    # differentiate between E and exp
    assert exp(exp(x + E)).subs(exp, 3) == 3**(3**(x + E))
    assert exp(exp(x + E)).subs(E, 3) == 3**(3**(x + 3))
    assert exp(3).subs(E, sin) == sin(3)


def test_exp_conjugate():
    assert conjugate(exp(x)) == exp(conjugate(x))


def test_exp_rewrite():
    from sympy.concrete.summations import Sum
    assert exp(x).rewrite(sin) == sinh(x) + cosh(x)
    assert exp(x*I).rewrite(cos) == cos(x) + I*sin(x)
    assert exp(1).rewrite(cos) == sinh(1) + cosh(1)
    assert exp(1).rewrite(sin) == sinh(1) + cosh(1)
    assert exp(1).rewrite(sin) == sinh(1) + cosh(1)
    assert exp(x).rewrite(tanh) == (1 + tanh(x/2))/(1 - tanh(x/2))
    assert exp(pi*I/4).rewrite(sqrt) == sqrt(2)/2 + sqrt(2)*I/2
    assert exp(pi*I/3).rewrite(sqrt) == S(1)/2 + sqrt(3)*I/2
    assert exp(x*log(y)).rewrite(Pow) == y**x
    assert exp(log(x)*log(y)).rewrite(Pow) in [x**log(y), y**log(x)]
    assert exp(log(log(x))*y).rewrite(Pow) == log(x)**y

    n = Symbol('n', integer=True)

    assert Sum((exp(pi*I/2)/2)**n, (n, 0, oo)).rewrite(sqrt).doit() == S(4)/5 + 2*I/5
    assert Sum((exp(pi*I/4)/2)**n, (n, 0, oo)).rewrite(sqrt).doit() == 1/(1 - sqrt(2)*(1 + I)/4)
    assert Sum((exp(pi*I/3)/2)**n, (n, 0, oo)).rewrite(sqrt).doit() == 1/(S(3)/4 - sqrt(3)*I/4)


def test_exp_leading_term():
    assert exp(x).as_leading_term(x) == 1
    assert exp(1/x).as_leading_term(x) == exp(1/x)
    assert exp(2 + x).as_leading_term(x) == exp(2)

def test_exp_taylor_term():
    x = symbols('x')
    assert exp(x).taylor_term(1, x) == x
    assert exp(x).taylor_term(3, x) == x**3/6
    assert exp(x).taylor_term(4, x) == x**4/24


def test_exp_MatrixSymbol():
    A = MatrixSymbol("A", 2, 2)
    assert exp(A).has(exp)


def test_log_values():
    assert log(nan) == nan

    assert log(oo) == oo
    assert log(-oo) == oo

    assert log(zoo) == zoo
    assert log(-zoo) == zoo

    assert log(0) == zoo

    assert log(1) == 0
    assert log(-1) == I*pi

    assert log(E) == 1
    assert log(-E).expand() == 1 + I*pi

    assert log(pi) == log(pi)
    assert log(-pi).expand() == log(pi) + I*pi

    assert log(17) == log(17)
    assert log(-17) == log(17) + I*pi

    assert log(I) == I*pi/2
    assert log(-I) == -I*pi/2

    assert log(17*I) == I*pi/2 + log(17)
    assert log(-17*I).expand() == -I*pi/2 + log(17)

    assert log(oo*I) == oo
    assert log(-oo*I) == oo
    assert log(0, 2) == zoo
    assert log(0, 5) == zoo

    assert exp(-log(3))**(-1) == 3

    assert log(S.Half) == -log(2)
    assert log(2*3).func is log
    assert log(2*3**2).func is log


def test_log_base():
    assert log(1, 2) == 0
    assert log(2, 2) == 1
    assert log(3, 2) == log(3)/log(2)
    assert log(6, 2) == 1 + log(3)/log(2)
    assert log(6, 3) == 1 + log(2)/log(3)
    assert log(2**3, 2) == 3
    assert log(3**3, 3) == 3
    assert log(5, 1) == zoo
    assert log(1, 1) == nan
    assert log(Rational(2, 3), 10) == log(S(2)/3)/log(10)
    assert log(Rational(2, 3), Rational(1, 3)) == -log(2)/log(3) + 1
    assert log(Rational(2, 3), Rational(2, 5)) == \
        log(S(2)/3)/log(S(2)/5)


def test_log_symbolic():
    assert log(x, exp(1)) == log(x)
    assert log(exp(x)) != x

    assert log(x, exp(1)) == log(x)
    assert log(x*y) != log(x) + log(y)
    assert log(x/y).expand() != log(x) - log(y)
    assert log(x/y).expand(force=True) == log(x) - log(y)
    assert log(x**y).expand() != y*log(x)
    assert log(x**y).expand(force=True) == y*log(x)

    assert log(x, 2) == log(x)/log(2)
    assert log(E, 2) == 1/log(2)

    p, q = symbols('p,q', positive=True)
    r = Symbol('r', real=True)

    assert log(p**2) != 2*log(p)
    assert log(p**2).expand() == 2*log(p)
    assert log(x**2).expand() != 2*log(x)
    assert log(p**q) != q*log(p)
    assert log(exp(p)) == p
    assert log(p*q) != log(p) + log(q)
    assert log(p*q).expand() == log(p) + log(q)

    assert log(-sqrt(3)) == log(sqrt(3)) + I*pi
    assert log(-exp(p)) != p + I*pi
    assert log(-exp(x)).expand() != x + I*pi
    assert log(-exp(r)).expand() == r + I*pi

    assert log(x**y) != y*log(x)

    assert (log(x**-5)**-1).expand() != -1/log(x)/5
    assert (log(p**-5)**-1).expand() == -1/log(p)/5
    assert log(-x).func is log and log(-x).args[0] == -x
    assert log(-p).func is log and log(-p).args[0] == -p


def test_exp_assumptions():
    r = Symbol('r', real=True)
    i = Symbol('i', imaginary=True)
    for e in exp, exp_polar:
        assert e(x).is_real is None
        assert e(x).is_imaginary is None
        assert e(i).is_real is None
        assert e(i).is_imaginary is None
        assert e(r).is_real is True
        assert e(r).is_imaginary is False
        assert e(re(x)).is_real is True
        assert e(re(x)).is_imaginary is False

    assert exp(0, evaluate=False).is_algebraic

    a = Symbol('a', algebraic=True)
    an = Symbol('an', algebraic=True, nonzero=True)
    r = Symbol('r', rational=True)
    rn = Symbol('rn', rational=True, nonzero=True)
    assert exp(a).is_algebraic is None
    assert exp(an).is_algebraic is False
    assert exp(pi*r).is_algebraic is None
    assert exp(pi*rn).is_algebraic is False


def test_exp_AccumBounds():
    assert exp(AccumBounds(1, 2)) == AccumBounds(E, E**2)


def test_log_assumptions():
    p = symbols('p', positive=True)
    n = symbols('n', negative=True)
    z = symbols('z', zero=True)
    x = symbols('x', infinite=True, positive=True)

    assert log(z).is_positive is False
    assert log(x).is_positive is True
    assert log(2) > 0
    assert log(1, evaluate=False).is_zero
    assert log(1 + z).is_zero
    assert log(p).is_zero is None
    assert log(n).is_zero is False
    assert log(0.5).is_negative is True
    assert log(exp(p) + 1).is_positive

    assert log(1, evaluate=False).is_algebraic
    assert log(42, evaluate=False).is_algebraic is False

    assert log(1 + z).is_rational


def test_log_hashing():
    assert x != log(log(x))
    assert hash(x) != hash(log(log(x)))
    assert log(x) != log(log(log(x)))

    e = 1/log(log(x) + log(log(x)))
    assert e.base.func is log
    e = 1/log(log(x) + log(log(log(x))))
    assert e.base.func is log

    e = log(log(x))
    assert e.func is log
    assert not x.func is log
    assert hash(log(log(x))) != hash(x)
    assert e != x


def test_log_sign():
    assert sign(log(2)) == 1


def test_log_expand_complex():
    assert log(1 + I).expand(complex=True) == log(2)/2 + I*pi/4
    assert log(1 - sqrt(2)).expand(complex=True) == log(sqrt(2) - 1) + I*pi


def test_log_apply_evalf():
    value = (log(3)/log(2) - 1).evalf()
    assert value.epsilon_eq(Float("0.58496250072115618145373"))


def test_log_expand():
    w = Symbol("w", positive=True)
    e = log(w**(log(5)/log(3)))
    assert e.expand() == log(5)/log(3) * log(w)
    x, y, z = symbols('x,y,z', positive=True)
    assert log(x*(y + z)).expand(mul=False) == log(x) + log(y + z)
    assert log(log(x**2)*log(y*z)).expand() in [log(2*log(x)*log(y) +
        2*log(x)*log(z)), log(log(x)*log(z) + log(y)*log(x)) + log(2),
        log((log(y) + log(z))*log(x)) + log(2)]
    assert log(x**log(x**2)).expand(deep=False) == log(x)*log(x**2)
    assert log(x**log(x**2)).expand() == 2*log(x)**2
    assert (log(x*(y + z))*(x + y)), expand(mul=True, log=True) == y*log(
        x) + y*log(y + z) + z*log(x) + z*log(y + z)
    x, y = symbols('x,y')
    assert log(x*y).expand(force=True) == log(x) + log(y)
    assert log(x**y).expand(force=True) == y*log(x)
    assert log(exp(x)).expand(force=True) == x

    # there's generally no need to expand out logs since this requires
    # factoring and if simplification is sought, it's cheaper to put
    # logs together than it is to take them apart.
    assert log(2*3**2).expand() != 2*log(3) + log(2)


def test_log_simplify():
    x = Symbol("x", positive=True)
    assert log(x**2).expand() == 2*log(x)
    assert expand_log(log(x**(2 + log(2)))) == (2 + log(2))*log(x)

    z = Symbol('z')
    assert log(sqrt(z)).expand() == log(z)/2
    assert expand_log(log(z**(log(2) - 1))) == (log(2) - 1)*log(z)
    assert log(z**(-1)).expand() != -log(z)
    assert log(z**(x/(x+1))).expand() == x*log(z)/(x + 1)


def test_log_AccumBounds():
    assert log(AccumBounds(1, E)) == AccumBounds(0, 1)


def test_lambertw():
    k = Symbol('k')

    assert LambertW(x, 0) == LambertW(x)
    assert LambertW(x, 0, evaluate=False) != LambertW(x)
    assert LambertW(0) == 0
    assert LambertW(E) == 1
    assert LambertW(-1/E) == -1
    assert LambertW(-log(2)/2) == -log(2)
    assert LambertW(oo) == oo
    assert LambertW(0, 1) == -oo
    assert LambertW(0, 42) == -oo
    assert LambertW(-pi/2, -1) == -I*pi/2
    assert LambertW(-1/E, -1) == -1
    assert LambertW(-2*exp(-2), -1) == -2

    assert LambertW(x**2).diff(x) == 2*LambertW(x**2)/x/(1 + LambertW(x**2))
    assert LambertW(x, k).diff(x) == LambertW(x, k)/x/(1 + LambertW(x, k))

    assert LambertW(sqrt(2)).evalf(30).epsilon_eq(
        Float("0.701338383413663009202120278965", 30), 1e-29)
    assert re(LambertW(2, -1)).evalf().epsilon_eq(Float("-0.834310366631110"))

    assert LambertW(-1).is_real is False  # issue 5215
    assert LambertW(2, evaluate=False).is_real
    p = Symbol('p', positive=True)
    assert LambertW(p, evaluate=False).is_real
    assert LambertW(p - 1, evaluate=False).is_real is None
    assert LambertW(-p - 2/S.Exp1, evaluate=False).is_real is False
    assert LambertW(S.Half, -1, evaluate=False).is_real is False
    assert LambertW(-S.One/10, -1, evaluate=False).is_real
    assert LambertW(-10, -1, evaluate=False).is_real is False
    assert LambertW(-2, 2, evaluate=False).is_real is False

    assert LambertW(0, evaluate=False).is_algebraic
    na = Symbol('na', nonzero=True, algebraic=True)
    assert LambertW(na).is_algebraic is False


def test_issue_5673():
    e = LambertW(-1)
    assert e.is_comparable is False
    assert e.is_positive is not True
    e2 = 1 - 1/(1 - exp(-1000))
    assert e.is_positive is not True
    e3 = -2 + exp(exp(LambertW(log(2)))*LambertW(log(2)))
    assert e3.is_nonzero is not True


def test_exp_expand_NC():
    A, B, C = symbols('A,B,C', commutative=False)

    assert exp(A + B).expand() == exp(A + B)
    assert exp(A + B + C).expand() == exp(A + B + C)
    assert exp(x + y).expand() == exp(x)*exp(y)
    assert exp(x + y + z).expand() == exp(x)*exp(y)*exp(z)


def test_as_numer_denom():
    n = symbols('n', negative=True)
    assert exp(x).as_numer_denom() == (exp(x), 1)
    assert exp(-x).as_numer_denom() == (1, exp(x))
    assert exp(-2*x).as_numer_denom() == (1, exp(2*x))
    assert exp(-2).as_numer_denom() == (1, exp(2))
    assert exp(n).as_numer_denom() == (1, exp(-n))
    assert exp(-n).as_numer_denom() == (exp(-n), 1)
    assert exp(-I*x).as_numer_denom() == (1, exp(I*x))
    assert exp(-I*n).as_numer_denom() == (1, exp(I*n))
    assert exp(-n).as_numer_denom() == (exp(-n), 1)


def test_polar():
    x, y = symbols('x y', polar=True)

    assert abs(exp_polar(I*4)) == 1
    assert abs(exp_polar(0)) == 1
    assert abs(exp_polar(2 + 3*I)) == exp(2)
    assert exp_polar(I*10).n() == exp_polar(I*10)

    assert log(exp_polar(z)) == z
    assert log(x*y).expand() == log(x) + log(y)
    assert log(x**z).expand() == z*log(x)

    assert exp_polar(3).exp == 3

    # Compare exp(1.0*pi*I).
    assert (exp_polar(1.0*pi*I).n(n=5)).as_real_imag()[1] >= 0

    assert exp_polar(0).is_rational is True  # issue 8008


def test_log_product():
    from sympy.abc import n, m
    i, j = symbols('i,j', positive=True, integer=True)
    x, y = symbols('x,y', positive=True)
    from sympy.concrete import Product, Sum
    f, g = Function('f'), Function('g')
    assert simplify(log(Product(x**i, (i, 1, n)))) == Sum(i*log(x), (i, 1, n))
    assert simplify(log(Product(x**i*y**j, (i, 1, n), (j, 1, m)))) == \
            log(Product(x**i*y**j, (i, 1, n), (j, 1, m)))

    expr = log(Product(-2, (n, 0, 4)))
    assert simplify(expr) == expr


def test_issue_8866():
    assert simplify(log(x, 10, evaluate=False)) == simplify(log(x, 10))
    assert expand_log(log(x, 10, evaluate=False)) == expand_log(log(x, 10))

    y = Symbol('y', positive=True)
    l1 = log(exp(y), exp(10))
    b1 = log(exp(y), exp(5))
    l2 = log(exp(y), exp(10), evaluate=False)
    b2 = log(exp(y), exp(5), evaluate=False)
    assert simplify(log(l1, b1)) == simplify(log(l2, b2))
    assert expand_log(log(l1, b1)) == expand_log(log(l2, b2))


def test_issue_9116():
    n = Symbol('n', positive=True, integer=True)

    assert ln(n).is_nonnegative is True
    assert log(n).is_nonnegative is True
