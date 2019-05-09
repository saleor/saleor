from sympy import AccumBounds, Symbol, floor, nan, oo, zoo, E, symbols, \
        ceiling, pi, Rational, Float, I, sin, exp, log, factorial, frac, Eq

from sympy.utilities.pytest import XFAIL

x = Symbol('x')
i = Symbol('i', imaginary=True)
y = Symbol('y', real=True)
k, n = symbols('k,n', integer=True)

def test_floor():

    assert floor(nan) == nan

    assert floor(oo) == oo
    assert floor(-oo) == -oo
    assert floor(zoo) == zoo

    assert floor(0) == 0

    assert floor(1) == 1
    assert floor(-1) == -1

    assert floor(E) == 2
    assert floor(-E) == -3

    assert floor(2*E) == 5
    assert floor(-2*E) == -6

    assert floor(pi) == 3
    assert floor(-pi) == -4

    assert floor(Rational(1, 2)) == 0
    assert floor(-Rational(1, 2)) == -1

    assert floor(Rational(7, 3)) == 2
    assert floor(-Rational(7, 3)) == -3

    assert floor(Float(17.0)) == 17
    assert floor(-Float(17.0)) == -17

    assert floor(Float(7.69)) == 7
    assert floor(-Float(7.69)) == -8

    assert floor(I) == I
    assert floor(-I) == -I
    e = floor(i)
    assert e.func is floor and e.args[0] == i

    assert floor(oo*I) == oo*I
    assert floor(-oo*I) == -oo*I
    assert floor(exp(I*pi/4)*oo) == exp(I*pi/4)*oo

    assert floor(2*I) == 2*I
    assert floor(-2*I) == -2*I

    assert floor(I/2) == 0
    assert floor(-I/2) == -I

    assert floor(E + 17) == 19
    assert floor(pi + 2) == 5

    assert floor(E + pi) == floor(E + pi)
    assert floor(I + pi) == floor(I + pi)

    assert floor(floor(pi)) == 3
    assert floor(floor(y)) == floor(y)
    assert floor(floor(x)) == floor(floor(x))

    assert floor(x) == floor(x)
    assert floor(2*x) == floor(2*x)
    assert floor(k*x) == floor(k*x)

    assert floor(k) == k
    assert floor(2*k) == 2*k
    assert floor(k*n) == k*n

    assert floor(k/2) == floor(k/2)

    assert floor(x + y) == floor(x + y)

    assert floor(x + 3) == floor(x + 3)
    assert floor(x + k) == floor(x + k)

    assert floor(y + 3) == floor(y) + 3
    assert floor(y + k) == floor(y) + k

    assert floor(3 + I*y + pi) == 6 + floor(y)*I

    assert floor(k + n) == k + n

    assert floor(x*I) == floor(x*I)
    assert floor(k*I) == k*I

    assert floor(Rational(23, 10) - E*I) == 2 - 3*I

    assert floor(sin(1)) == 0
    assert floor(sin(-1)) == -1

    assert floor(exp(2)) == 7

    assert floor(log(8)/log(2)) != 2
    assert int(floor(log(8)/log(2)).evalf(chop=True)) == 3

    assert floor(factorial(50)/exp(1)) == \
        11188719610782480504630258070757734324011354208865721592720336800

    assert (floor(y) <= y) == True
    assert (floor(y) > y) == False
    assert (floor(x) <= x).is_Relational  # x could be non-real
    assert (floor(x) > x).is_Relational
    assert (floor(x) <= y).is_Relational  # arg is not same as rhs
    assert (floor(x) > y).is_Relational

    assert floor(y).rewrite(frac) == y - frac(y)
    assert floor(y).rewrite(ceiling) == -ceiling(-y)
    assert floor(y).rewrite(frac).subs(y, -pi) == floor(-pi)
    assert floor(y).rewrite(frac).subs(y, E) == floor(E)
    assert floor(y).rewrite(ceiling).subs(y, E) == -ceiling(-E)
    assert floor(y).rewrite(ceiling).subs(y, -pi) == -ceiling(pi)

    assert Eq(floor(y), y - frac(y))
    assert Eq(floor(y), -ceiling(-y))


def test_ceiling():

    assert ceiling(nan) == nan

    assert ceiling(oo) == oo
    assert ceiling(-oo) == -oo
    assert ceiling(zoo) == zoo

    assert ceiling(0) == 0

    assert ceiling(1) == 1
    assert ceiling(-1) == -1

    assert ceiling(E) == 3
    assert ceiling(-E) == -2

    assert ceiling(2*E) == 6
    assert ceiling(-2*E) == -5

    assert ceiling(pi) == 4
    assert ceiling(-pi) == -3

    assert ceiling(Rational(1, 2)) == 1
    assert ceiling(-Rational(1, 2)) == 0

    assert ceiling(Rational(7, 3)) == 3
    assert ceiling(-Rational(7, 3)) == -2

    assert ceiling(Float(17.0)) == 17
    assert ceiling(-Float(17.0)) == -17

    assert ceiling(Float(7.69)) == 8
    assert ceiling(-Float(7.69)) == -7

    assert ceiling(I) == I
    assert ceiling(-I) == -I
    e = ceiling(i)
    assert e.func is ceiling and e.args[0] == i

    assert ceiling(oo*I) == oo*I
    assert ceiling(-oo*I) == -oo*I
    assert ceiling(exp(I*pi/4)*oo) == exp(I*pi/4)*oo

    assert ceiling(2*I) == 2*I
    assert ceiling(-2*I) == -2*I

    assert ceiling(I/2) == I
    assert ceiling(-I/2) == 0

    assert ceiling(E + 17) == 20
    assert ceiling(pi + 2) == 6

    assert ceiling(E + pi) == ceiling(E + pi)
    assert ceiling(I + pi) == ceiling(I + pi)

    assert ceiling(ceiling(pi)) == 4
    assert ceiling(ceiling(y)) == ceiling(y)
    assert ceiling(ceiling(x)) == ceiling(ceiling(x))

    assert ceiling(x) == ceiling(x)
    assert ceiling(2*x) == ceiling(2*x)
    assert ceiling(k*x) == ceiling(k*x)

    assert ceiling(k) == k
    assert ceiling(2*k) == 2*k
    assert ceiling(k*n) == k*n

    assert ceiling(k/2) == ceiling(k/2)

    assert ceiling(x + y) == ceiling(x + y)

    assert ceiling(x + 3) == ceiling(x + 3)
    assert ceiling(x + k) == ceiling(x + k)

    assert ceiling(y + 3) == ceiling(y) + 3
    assert ceiling(y + k) == ceiling(y) + k

    assert ceiling(3 + pi + y*I) == 7 + ceiling(y)*I

    assert ceiling(k + n) == k + n

    assert ceiling(x*I) == ceiling(x*I)
    assert ceiling(k*I) == k*I

    assert ceiling(Rational(23, 10) - E*I) == 3 - 2*I

    assert ceiling(sin(1)) == 1
    assert ceiling(sin(-1)) == 0

    assert ceiling(exp(2)) == 8

    assert ceiling(-log(8)/log(2)) != -2
    assert int(ceiling(-log(8)/log(2)).evalf(chop=True)) == -3

    assert ceiling(factorial(50)/exp(1)) == \
        11188719610782480504630258070757734324011354208865721592720336801

    assert (ceiling(y) >= y) == True
    assert (ceiling(y) < y) == False
    assert (ceiling(x) >= x).is_Relational  # x could be non-real
    assert (ceiling(x) < x).is_Relational
    assert (ceiling(x) >= y).is_Relational  # arg is not same as rhs
    assert (ceiling(x) < y).is_Relational

    assert ceiling(y).rewrite(floor) == -floor(-y)
    assert ceiling(y).rewrite(frac) == y + frac(-y)
    assert ceiling(y).rewrite(floor).subs(y, -pi) == -floor(pi)
    assert ceiling(y).rewrite(floor).subs(y, E) == -floor(-E)
    assert ceiling(y).rewrite(frac).subs(y, pi) == ceiling(pi)
    assert ceiling(y).rewrite(frac).subs(y, -E) == ceiling(-E)

    assert Eq(ceiling(y), y + frac(-y))
    assert Eq(ceiling(y), -floor(-y))


def test_frac():
    assert isinstance(frac(x), frac)
    assert frac(oo) == AccumBounds(0, 1)
    assert frac(-oo) == AccumBounds(0, 1)

    assert frac(n) == 0
    assert frac(nan) == nan
    assert frac(Rational(4, 3)) == Rational(1, 3)
    assert frac(-Rational(4, 3)) == Rational(2, 3)

    r = Symbol('r', real=True)
    assert frac(I*r) == I*frac(r)
    assert frac(1 + I*r) == I*frac(r)
    assert frac(0.5 + I*r) == 0.5 + I*frac(r)
    assert frac(n + I*r) == I*frac(r)
    assert frac(n + I*k) == 0
    assert frac(x + I*x) == frac(x + I*x)
    assert frac(x + I*n) == frac(x)

    assert frac(x).rewrite(floor) == x - floor(x)
    assert frac(x).rewrite(ceiling) == x + ceiling(-x)
    assert frac(y).rewrite(floor).subs(y, pi) == frac(pi)
    assert frac(y).rewrite(floor).subs(y, -E) == frac(-E)
    assert frac(y).rewrite(ceiling).subs(y, -pi) == frac(-pi)
    assert frac(y).rewrite(ceiling).subs(y, E) == frac(E)

    assert Eq(frac(y), y - floor(y))
    assert Eq(frac(y), y + ceiling(-y))


def test_series():
    x, y = symbols('x,y')
    assert floor(x).nseries(x, y, 100) == floor(y)
    assert ceiling(x).nseries(x, y, 100) == ceiling(y)
    assert floor(x).nseries(x, pi, 100) == 3
    assert ceiling(x).nseries(x, pi, 100) == 4
    assert floor(x).nseries(x, 0, 100) == 0
    assert ceiling(x).nseries(x, 0, 100) == 1
    assert floor(-x).nseries(x, 0, 100) == -1
    assert ceiling(-x).nseries(x, 0, 100) == 0


@XFAIL
def test_issue_4149():
    assert floor(3 + pi*I + y*I) == 3 + floor(pi + y)*I
    assert floor(3*I + pi*I + y*I) == floor(3 + pi + y)*I
    assert floor(3 + E + pi*I + y*I) == 5 + floor(pi + y)*I


def test_issue_11207():
    assert floor(floor(x)) == floor(x)
    assert floor(ceiling(x)) == ceiling(x)
    assert ceiling(floor(x)) == floor(x)
    assert ceiling(ceiling(x)) == ceiling(x)


def test_nested_floor_ceiling():
    assert floor(-floor(ceiling(x**3)/y)) == -floor(ceiling(x**3)/y)
    assert ceiling(-floor(ceiling(x**3)/y)) == -floor(ceiling(x**3)/y)
    assert floor(ceiling(-floor(x**Rational(7, 2)/y))) == -floor(x**Rational(7, 2)/y)
    assert -ceiling(-ceiling(floor(x)/y)) == ceiling(floor(x)/y)
