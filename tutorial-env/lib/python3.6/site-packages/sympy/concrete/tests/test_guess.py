from sympy.concrete.guess import (
            find_simple_recurrence_vector,
            find_simple_recurrence,
            rationalize,
            guess_generating_function_rational,
            guess_generating_function,
            guess
        )
from sympy import (Function, Symbol, sympify, Rational, symbols, S,
                   fibonacci, factorial, exp, Product, RisingFactorial)


def test_find_simple_recurrence_vector():
    assert find_simple_recurrence_vector(
            [fibonacci(k) for k in range(12)]) == [1, -1, -1]


def test_find_simple_recurrence():
    a = Function('a')
    n = Symbol('n')
    assert find_simple_recurrence([fibonacci(k) for k in range(12)]) == (
        -a(n) - a(n + 1) + a(n + 2))

    f = Function('a')
    i = Symbol('n')
    a = [1, 1, 1]
    for k in range(15): a.append(5*a[-1]-3*a[-2]+8*a[-3])
    assert find_simple_recurrence(a, A=f, N=i) == (
        -8*f(i) + 3*f(i + 1) - 5*f(i + 2) + f(i + 3))
    assert find_simple_recurrence([0, 2, 15, 74, 12, 3, 0,
                                    1, 2, 85, 4, 5, 63]) == 0


def test_rationalize():
    from mpmath import cos, pi, mpf
    assert rationalize(cos(pi/3)) == Rational(1, 2)
    assert rationalize(mpf("0.333333333333333")) == Rational(1, 3)
    assert rationalize(mpf("-0.333333333333333")) == Rational(-1, 3)
    assert rationalize(pi, maxcoeff = 250) == Rational(355, 113)


def test_guess_generating_function_rational():
    x = Symbol('x')
    assert guess_generating_function_rational([fibonacci(k)
        for k in range(5, 15)]) == ((3*x + 5)/(-x**2 - x + 1))


def test_guess_generating_function():
    x = Symbol('x')
    assert guess_generating_function([fibonacci(k)
        for k in range(5, 15)])['ogf'] == ((3*x + 5)/(-x**2 - x + 1))
    assert guess_generating_function(
        [1, 2, 5, 14, 41, 124, 383, 1200, 3799, 12122, 38919])['ogf'] == (
        (1/(x**4 + 2*x**2 - 4*x + 1))**Rational(1, 2))
    assert guess_generating_function(sympify(
       "[3/2, 11/2, 0, -121/2, -363/2, 121, 4719/2, 11495/2, -8712, -178717/2]")
       )['ogf'] == (x + Rational(3, 2))/(11*x**2 - 3*x + 1)
    assert guess_generating_function([factorial(k) for k in range(12)],
       types=['egf'])['egf'] == 1/(-x + 1)
    assert guess_generating_function([k+1 for k in range(12)],
       types=['egf']) == {'egf': (x + 1)*exp(x), 'lgdegf': (x + 2)/(x + 1)}


def test_guess():
    i0, i1 = symbols('i0 i1')
    assert guess([1, 2, 6, 24, 120], evaluate=False) == [Product(i1 + 1, (i1, 1, i0 - 1))]
    assert guess([1, 2, 6, 24, 120]) == [RisingFactorial(2, i0 - 1)]
    assert guess([1, 2, 7, 42, 429, 7436, 218348, 10850216], niter=4) == [
        2**(i0 - 1)*(S(27)/16)**(i0**2/2 - 3*i0/2 +
        1)*Product(RisingFactorial(S(5)/3, i1 - 1)*RisingFactorial(S(7)/3, i1
        - 1)/(RisingFactorial(S(3)/2, i1 - 1)*RisingFactorial(S(5)/2, i1 -
        1)), (i1, 1, i0 - 1))]
