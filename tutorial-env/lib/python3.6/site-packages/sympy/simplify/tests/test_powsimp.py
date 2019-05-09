from sympy import (
    symbols, powsimp, symbols, MatrixSymbol, sqrt, pi, Mul, gamma, Function,
    S, I, exp, simplify, sin, E, log, hyper, Symbol, Dummy, powdenest, root,
    Rational, oo)

from sympy.abc import x, y, z, t, a, b, c, d, e, f, g, h, i, k


def test_powsimp():
    x, y, z, n = symbols('x,y,z,n')
    f = Function('f')
    assert powsimp( 4**x * 2**(-x) * 2**(-x) ) == 1
    assert powsimp( (-4)**x * (-2)**(-x) * 2**(-x) ) == 1

    assert powsimp(
        f(4**x * 2**(-x) * 2**(-x)) ) == f(4**x * 2**(-x) * 2**(-x))
    assert powsimp( f(4**x * 2**(-x) * 2**(-x)), deep=True ) == f(1)
    assert exp(x)*exp(y) == exp(x)*exp(y)
    assert powsimp(exp(x)*exp(y)) == exp(x + y)
    assert powsimp(exp(x)*exp(y)*2**x*2**y) == (2*E)**(x + y)
    assert powsimp(exp(x)*exp(y)*2**x*2**y, combine='exp') == \
        exp(x + y)*2**(x + y)
    assert powsimp(exp(x)*exp(y)*exp(2)*sin(x) + sin(y) + 2**x*2**y) == \
        exp(2 + x + y)*sin(x) + sin(y) + 2**(x + y)
    assert powsimp(sin(exp(x)*exp(y))) == sin(exp(x)*exp(y))
    assert powsimp(sin(exp(x)*exp(y)), deep=True) == sin(exp(x + y))
    assert powsimp(x**2*x**y) == x**(2 + y)
    # This should remain factored, because 'exp' with deep=True is supposed
    # to act like old automatic exponent combining.
    assert powsimp((1 + E*exp(E))*exp(-E), combine='exp', deep=True) == \
        (1 + exp(1 + E))*exp(-E)
    assert powsimp((1 + E*exp(E))*exp(-E), deep=True) == \
        (1 + exp(1 + E))*exp(-E)
    assert powsimp((1 + E*exp(E))*exp(-E)) == (1 + exp(1 + E))*exp(-E)
    assert powsimp((1 + E*exp(E))*exp(-E), combine='exp') == \
        (1 + exp(1 + E))*exp(-E)
    assert powsimp((1 + E*exp(E))*exp(-E), combine='base') == \
        (1 + E*exp(E))*exp(-E)
    x, y = symbols('x,y', nonnegative=True)
    n = Symbol('n', real=True)
    assert powsimp(y**n * (y/x)**(-n)) == x**n
    assert powsimp(x**(x**(x*y)*y**(x*y))*y**(x**(x*y)*y**(x*y)), deep=True) \
        == (x*y)**(x*y)**(x*y)
    assert powsimp(2**(2**(2*x)*x), deep=False) == 2**(2**(2*x)*x)
    assert powsimp(2**(2**(2*x)*x), deep=True) == 2**(x*4**x)
    assert powsimp(
        exp(-x + exp(-x)*exp(-x*log(x))), deep=False, combine='exp') == \
        exp(-x + exp(-x)*exp(-x*log(x)))
    assert powsimp(
        exp(-x + exp(-x)*exp(-x*log(x))), deep=False, combine='exp') == \
        exp(-x + exp(-x)*exp(-x*log(x)))
    assert powsimp((x + y)/(3*z), deep=False, combine='exp') == (x + y)/(3*z)
    assert powsimp((x/3 + y/3)/z, deep=True, combine='exp') == (x/3 + y/3)/z
    assert powsimp(exp(x)/(1 + exp(x)*exp(y)), deep=True) == \
        exp(x)/(1 + exp(x + y))
    assert powsimp(x*y**(z**x*z**y), deep=True) == x*y**(z**(x + y))
    assert powsimp((z**x*z**y)**x, deep=True) == (z**(x + y))**x
    assert powsimp(x*(z**x*z**y)**x, deep=True) == x*(z**(x + y))**x
    p = symbols('p', positive=True)
    assert powsimp((1/x)**log(2)/x) == (1/x)**(1 + log(2))
    assert powsimp((1/p)**log(2)/p) == p**(-1 - log(2))

    # coefficient of exponent can only be simplified for positive bases
    assert powsimp(2**(2*x)) == 4**x
    assert powsimp((-1)**(2*x)) == (-1)**(2*x)
    i = symbols('i', integer=True)
    assert powsimp((-1)**(2*i)) == 1
    assert powsimp((-1)**(-x)) != (-1)**x  # could be 1/((-1)**x), but is not
    # force=True overrides assumptions
    assert powsimp((-1)**(2*x), force=True) == 1

    # rational exponents allow combining of negative terms
    w, n, m = symbols('w n m', negative=True)
    e = i/a  # not a rational exponent if `a` is unknown
    ex = w**e*n**e*m**e
    assert powsimp(ex) == m**(i/a)*n**(i/a)*w**(i/a)
    e = i/3
    ex = w**e*n**e*m**e
    assert powsimp(ex) == (-1)**i*(-m*n*w)**(i/3)
    e = (3 + i)/i
    ex = w**e*n**e*m**e
    assert powsimp(ex) == (-1)**(3*e)*(-m*n*w)**e

    eq = x**(2*a/3)
    # eq != (x**a)**(2/3) (try x = -1 and a = 3 to see)
    assert powsimp(eq).exp == eq.exp == 2*a/3
    # powdenest goes the other direction
    assert powsimp(2**(2*x)) == 4**x

    assert powsimp(exp(p/2)) == exp(p/2)

    # issue 6368
    eq = Mul(*[sqrt(Dummy(imaginary=True)) for i in range(3)])
    assert powsimp(eq) == eq and eq.is_Mul

    assert all(powsimp(e) == e for e in (sqrt(x**a), sqrt(x**2)))

    # issue 8836
    assert str( powsimp(exp(I*pi/3)*root(-1,3)) ) == '(-1)**(2/3)'

    # issue 9183
    assert powsimp(-0.1**x) == -0.1**x

    # issue 10095
    assert powsimp((1/(2*E))**oo) == (exp(-1)/2)**oo

    # PR 13131
    eq = sin(2*x)**2*sin(2.0*x)**2
    assert powsimp(eq) == eq

    # issue 14615
    assert powsimp(x**2*y**3*(x*y**2)**(S(3)/2)
        ) == x*y*(x*y**2)**(S(5)/2)


def test_powsimp_negated_base():
    assert powsimp((-x + y)/sqrt(x - y)) == -sqrt(x - y)
    assert powsimp((-x + y)*(-z + y)/sqrt(x - y)/sqrt(z - y)) == sqrt(x - y)*sqrt(z - y)
    p = symbols('p', positive=True)
    assert powsimp((-p)**a/p**a) == (-1)**a
    n = symbols('n', negative=True)
    assert powsimp((-n)**a/n**a) == (-1)**a
    # if x is 0 then the lhs is 0**a*oo**a which is not (-1)**a
    assert powsimp((-x)**a/x**a) != (-1)**a


def test_powsimp_nc():
    x, y, z = symbols('x,y,z')
    A, B, C = symbols('A B C', commutative=False)

    assert powsimp(A**x*A**y, combine='all') == A**(x + y)
    assert powsimp(A**x*A**y, combine='base') == A**x*A**y
    assert powsimp(A**x*A**y, combine='exp') == A**(x + y)

    assert powsimp(A**x*B**x, combine='all') == A**x*B**x
    assert powsimp(A**x*B**x, combine='base') == A**x*B**x
    assert powsimp(A**x*B**x, combine='exp') == A**x*B**x

    assert powsimp(B**x*A**x, combine='all') == B**x*A**x
    assert powsimp(B**x*A**x, combine='base') == B**x*A**x
    assert powsimp(B**x*A**x, combine='exp') == B**x*A**x

    assert powsimp(A**x*A**y*A**z, combine='all') == A**(x + y + z)
    assert powsimp(A**x*A**y*A**z, combine='base') == A**x*A**y*A**z
    assert powsimp(A**x*A**y*A**z, combine='exp') == A**(x + y + z)

    assert powsimp(A**x*B**x*C**x, combine='all') == A**x*B**x*C**x
    assert powsimp(A**x*B**x*C**x, combine='base') == A**x*B**x*C**x
    assert powsimp(A**x*B**x*C**x, combine='exp') == A**x*B**x*C**x

    assert powsimp(B**x*A**x*C**x, combine='all') == B**x*A**x*C**x
    assert powsimp(B**x*A**x*C**x, combine='base') == B**x*A**x*C**x
    assert powsimp(B**x*A**x*C**x, combine='exp') == B**x*A**x*C**x


def test_issue_6440():
    assert powsimp(16*2**a*8**b) == 2**(a + 3*b + 4)


def test_powdenest():
    from sympy import powdenest
    from sympy.abc import x, y, z, a, b
    p, q = symbols('p q', positive=True)
    i, j = symbols('i,j', integer=True)

    assert powdenest(x) == x
    assert powdenest(x + 2*(x**(2*a/3))**(3*x)) == (x + 2*(x**(2*a/3))**(3*x))
    assert powdenest((exp(2*a/3))**(3*x))  # -X-> (exp(a/3))**(6*x)
    assert powdenest((x**(2*a/3))**(3*x)) == ((x**(2*a/3))**(3*x))
    assert powdenest(exp(3*x*log(2))) == 2**(3*x)
    assert powdenest(sqrt(p**2)) == p
    i, j = symbols('i,j', integer=True)
    eq = p**(2*i)*q**(4*i)
    assert powdenest(eq) == (p*q**2)**(2*i)
    # -X-> (x**x)**i*(x**x)**j == x**(x*(i + j))
    assert powdenest((x**x)**(i + j))
    assert powdenest(exp(3*y*log(x))) == x**(3*y)
    assert powdenest(exp(y*(log(a) + log(b)))) == (a*b)**y
    assert powdenest(exp(3*(log(a) + log(b)))) == a**3*b**3
    assert powdenest(((x**(2*i))**(3*y))**x) == ((x**(2*i))**(3*y))**x
    assert powdenest(((x**(2*i))**(3*y))**x, force=True) == x**(6*i*x*y)
    assert powdenest(((x**(2*a/3))**(3*y/i))**x) == \
        (((x**(2*a/3))**(3*y/i))**x)
    assert powdenest((x**(2*i)*y**(4*i))**z, force=True) == (x*y**2)**(2*i*z)
    assert powdenest((p**(2*i)*q**(4*i))**j) == (p*q**2)**(2*i*j)
    e = ((p**(2*a))**(3*y))**x
    assert powdenest(e) == e
    e = ((x**2*y**4)**a)**(x*y)
    assert powdenest(e) == e
    e = (((x**2*y**4)**a)**(x*y))**3
    assert powdenest(e) == ((x**2*y**4)**a)**(3*x*y)
    assert powdenest((((x**2*y**4)**a)**(x*y)), force=True) == \
        (x*y**2)**(2*a*x*y)
    assert powdenest((((x**2*y**4)**a)**(x*y))**3, force=True) == \
        (x*y**2)**(6*a*x*y)
    assert powdenest((x**2*y**6)**i) != (x*y**3)**(2*i)
    x, y = symbols('x,y', positive=True)
    assert powdenest((x**2*y**6)**i) == (x*y**3)**(2*i)

    assert powdenest((x**(2*i/3)*y**(i/2))**(2*i)) == (x**(S(4)/3)*y)**(i**2)
    assert powdenest(sqrt(x**(2*i)*y**(6*i))) == (x*y**3)**i

    assert powdenest(4**x) == 2**(2*x)
    assert powdenest((4**x)**y) == 2**(2*x*y)
    assert powdenest(4**x*y) == 2**(2*x)*y


def test_powdenest_polar():
    x, y, z = symbols('x y z', polar=True)
    a, b, c = symbols('a b c')
    assert powdenest((x*y*z)**a) == x**a*y**a*z**a
    assert powdenest((x**a*y**b)**c) == x**(a*c)*y**(b*c)
    assert powdenest(((x**a)**b*y**c)**c) == x**(a*b*c)*y**(c**2)


def test_issue_5805():
    arg = ((gamma(x)*hyper((), (), x))*pi)**2
    assert powdenest(arg) == (pi*gamma(x)*hyper((), (), x))**2
    assert arg.is_positive is None


def test_issue_9324_powsimp_on_matrix_symbol():
    M = MatrixSymbol('M', 10, 10)
    expr = powsimp(M, deep=True)
    assert expr == M
    assert expr.args[0] == Symbol('M')


def test_issue_6367():
    z = -5*sqrt(2)/(2*sqrt(2*sqrt(29) + 29)) + sqrt(-sqrt(29)/29 + S(1)/2)
    assert Mul(*[powsimp(a) for a in Mul.make_args(z.normal())]) == 0
    assert powsimp(z.normal()) == 0
    assert simplify(z) == 0
    assert powsimp(sqrt(2 + sqrt(3))*sqrt(2 - sqrt(3)) + 1) == 2
    assert powsimp(z) != 0


def test_powsimp_polar():
    from sympy import polar_lift, exp_polar
    x, y, z = symbols('x y z')
    p, q, r = symbols('p q r', polar=True)

    assert (polar_lift(-1))**(2*x) == exp_polar(2*pi*I*x)
    assert powsimp(p**x * q**x) == (p*q)**x
    assert p**x * (1/p)**x == 1
    assert (1/p)**x == p**(-x)

    assert exp_polar(x)*exp_polar(y) == exp_polar(x)*exp_polar(y)
    assert powsimp(exp_polar(x)*exp_polar(y)) == exp_polar(x + y)
    assert powsimp(exp_polar(x)*exp_polar(y)*p**x*p**y) == \
        (p*exp_polar(1))**(x + y)
    assert powsimp(exp_polar(x)*exp_polar(y)*p**x*p**y, combine='exp') == \
        exp_polar(x + y)*p**(x + y)
    assert powsimp(
        exp_polar(x)*exp_polar(y)*exp_polar(2)*sin(x) + sin(y) + p**x*p**y) \
        == p**(x + y) + sin(x)*exp_polar(2 + x + y) + sin(y)
    assert powsimp(sin(exp_polar(x)*exp_polar(y))) == \
        sin(exp_polar(x)*exp_polar(y))
    assert powsimp(sin(exp_polar(x)*exp_polar(y)), deep=True) == \
        sin(exp_polar(x + y))


def test_issue_5728():
    b = x*sqrt(y)
    a = sqrt(b)
    c = sqrt(sqrt(x)*y)
    assert powsimp(a*b) == sqrt(b)**3
    assert powsimp(a*b**2*sqrt(y)) == sqrt(y)*a**5
    assert powsimp(a*x**2*c**3*y) == c**3*a**5
    assert powsimp(a*x*c**3*y**2) == c**7*a
    assert powsimp(x*c**3*y**2) == c**7
    assert powsimp(x*c**3*y) == x*y*c**3
    assert powsimp(sqrt(x)*c**3*y) == c**5
    assert powsimp(sqrt(x)*a**3*sqrt(y)) == sqrt(x)*sqrt(y)*a**3
    assert powsimp(Mul(sqrt(x)*c**3*sqrt(y), y, evaluate=False)) == \
        sqrt(x)*sqrt(y)**3*c**3
    assert powsimp(a**2*a*x**2*y) == a**7

    # symbolic powers work, too
    b = x**y*y
    a = b*sqrt(b)
    assert a.is_Mul is True
    assert powsimp(a) == sqrt(b)**3

    # as does exp
    a = x*exp(2*y/3)
    assert powsimp(a*sqrt(a)) == sqrt(a)**3
    assert powsimp(a**2*sqrt(a)) == sqrt(a)**5
    assert powsimp(a**2*sqrt(sqrt(a))) == sqrt(sqrt(a))**9


def test_issue_from_PR1599():
    n1, n2, n3, n4 = symbols('n1 n2 n3 n4', negative=True)
    assert (powsimp(sqrt(n1)*sqrt(n2)*sqrt(n3)) ==
        -I*sqrt(-n1)*sqrt(-n2)*sqrt(-n3))
    assert (powsimp(root(n1, 3)*root(n2, 3)*root(n3, 3)*root(n4, 3)) ==
        -(-1)**(S(1)/3)*
        (-n1)**(S(1)/3)*(-n2)**(S(1)/3)*(-n3)**(S(1)/3)*(-n4)**(S(1)/3))


def test_issue_10195():
    a = Symbol('a', integer=True)
    l = Symbol('l', even=True, nonzero=True)
    n = Symbol('n', odd=True)
    e_x = (-1)**(n/2 - Rational(1, 2)) - (-1)**(3*n/2 - Rational(1, 2))
    assert powsimp((-1)**(l/2)) == I**l
    assert powsimp((-1)**(n/2)) == I**n
    assert powsimp((-1)**(3*n/2)) == -I**n
    assert powsimp(e_x) == (-1)**(n/2 - Rational(1, 2)) + (-1)**(3*n/2 +
            Rational(1,2))
    assert powsimp((-1)**(3*a/2)) == (-I)**a

def test_issue_15709():
    assert powsimp(2*3**x/3) == 2*3**(x-1)


def test_issue_11981():
    x, y = symbols('x y', commutative=False)
    assert powsimp((x*y)**2 * (y*x)**2) == (x*y)**2 * (y*x)**2
