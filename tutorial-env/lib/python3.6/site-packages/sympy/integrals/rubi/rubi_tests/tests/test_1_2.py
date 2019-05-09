'''
Tests for Rubi Algebraic 1.2 rules. Parsed from Maple syntax
All tests: http://www.apmaths.uwo.ca/~arich/IntegrationProblems/MapleSyntaxFiles/MapleSyntaxFiles.html
Note: Some tests are commented since they depend rules other than Algebraic1.2.
'''

import sys
from sympy.external import import_module
matchpy = import_module("matchpy")

if not matchpy:
    #bin/test will not execute any tests now
    disabled = True

if sys.version_info[:2] < (3, 6):
    disabled = True

from sympy.integrals.rubi.rubi import rubi_integrate
from sympy.functions import log, sqrt, exp, cos, sin, tan, sec, csc, cot
from sympy.functions.elementary.hyperbolic import atanh as arctanh
from sympy.functions.elementary.hyperbolic import asinh as arcsinh
from sympy.functions.elementary.hyperbolic import acosh as arccosh
from sympy.functions.elementary.trigonometric import atan as arctan
from sympy.functions.elementary.trigonometric import asin as arcsin
from sympy.functions.elementary.trigonometric import acos as arccos
from sympy.integrals.rubi.utility_function import EllipticE, EllipticF, hypergeom, rubi_test
from sympy import pi as Pi
from sympy import S, hyper, I, simplify, exp_polar, symbols


a, b, c, d, e, f, m, n, x, u = symbols('a b c d e f m n x u')

def test_1():
    test = [
        [ - S(3)/S(2), x, S(1), - S(3)/S(2)*x],
        [Pi, x, S(1), Pi*x],
        [a, x, S(1), a*x],
        [x**m, x, S(1), x**(S(1) + m)/(S(1) + m)],
        [x**S(100), x, S(1), S(1)/S(101)*x**S(101)],
        [x**(S(5)/S(2)), x, S(1), S(2)/S(7)*x**(S(7)/S(2))],
        [x**(S(5)/S(3)), x, S(1), S(3)/S(8)*x**(S(8)/S(3))],
        [S(1)/x**(S(1)/S(3)), x, S(1), S(3)/S(2)*x**(S(2)/S(3))],
        [x**S(3)*(a + b*x), x, S(2), S(1)/S(4)*a*x**S(4) + S(1)/S(5)*b*x**S(5)],
        [(a + b*x)**S(2)/x**S(2), x, S(2), - a**S(2)/x + b**S(2)*x + S(2)*a*b*log(x)],
    ]

    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True)

def test_2():
    test = [
        [(a + b*x)/x, x, S(2), b*x + a*log(x)],
        [x**S(5)/(a + b*x), x, S(2), a**S(4)*x/b**S(5) - S(1)/S(2)*a**S(3)*x**S(2)/b**S(4) + S(1)/S(3)*a**S(2)*x**S(3)/b**S(3) - S(1)/S(4)*a*x**S(4)/b**S(2) + S(1)/S(5)*x**S(5)/b - a**S(5)*log(a + b*x)/b**S(6)],
        [S(1)/(a + b*x)**S(2), x, S(1), ( - S(1))/(b*(a + b*x))],
        [S(1)/(x*(a + b*x)**S(3)), x, S(2), S(1)/S(2)/(a*(a + b*x)**S(2)) + S(1)/(a**S(2)*(a + b*x)) + log(x)/a**S(3) - log(a + b*x)/a**S(3)],
        [S(1)/(S(2) + S(2)*x), x, S(1), S(1)/S(2)*log(S(1) + x)],
        [S(1)/(x*(S(1) + b*x)), x, S(3), log(x) - log(S(1) + b*x)],
        [x**S(3)*sqrt(a + b*x), x, S(2), - S(2)/S(3)*a**S(3)*(a + b*x)**(S(3)/S(2))/b**S(4) + S(6)/S(5)*a**S(2)*(a + b*x)**(S(5)/S(2))/b**S(4) - S(6)/S(7)*a*(a + b*x)**(S(7)/S(2))/b**S(4) + S(2)/S(9)*(a + b*x)**(S(9)/S(2))/b**S(4)],
        [(a + b*x)**(S(3)/S(2)), x, S(1), S(2)/S(5)*(a + b*x)**(S(5)/S(2))/b],
        [x**S(4)/sqrt(a + b*x), x, S(2), - S(8)/S(3)*a**S(3)*(a + b*x)**(S(3)/S(2))/b**S(5) + S(12)/S(5)*a**S(2)*(a + b*x)**(S(5)/S(2))/b**S(5) - S(8)/S(7)*a*(a + b*x)**(S(7)/S(2))/b**S(5) + S(2)/S(9)*(a + b*x)**(S(9)/S(2))/b**S(5) + S(2)*a**S(4)*sqrt(a + b*x)/b**S(5)],
        [S(1)/sqrt(a + b*x), x, S(1), S(2)*sqrt(a + b*x)/b],
        [S(1)/(x*(a + b*x)**(S(3)/S(2))), x, S(3), - S(2)*arctanh(sqrt(a + b*x)/sqrt(a))/a**(S(3)/S(2)) + S(2)/(a*sqrt(a + b*x))],
        [S(1)/(x**S(2)*( - a + b*x)**(S(3)/S(2))), x, S(4), - S(3)*b*arctan(sqrt( - a + b*x)/sqrt(a))/a**(S(5)/S(2)) + ( - S(2))/(a*x*sqrt( - a + b*x)) - S(3)*sqrt( - a + b*x)/(a**S(2)*x)],
        [x**S(3)*(a + b*x)**(S(1)/S(3)), x, S(2), - S(3)/S(4)*a**S(3)*(a + b*x)**(S(4)/S(3))/b**S(4) + S(9)/S(7)*a**S(2)*(a + b*x)**(S(7)/S(3))/b**S(4) - S(9)/S(10)*a*(a + b*x)**(S(10)/S(3))/b**S(4) + S(3)/S(13)*(a + b*x)**(S(13)/S(3))/b**S(4)],
        [x**S(2)*(a + b*x)**(S(2)/S(3)), x, S(2), S(3)/S(5)*a**S(2)*(a + b*x)**(S(5)/S(3))/b**S(3) - S(3)/S(4)*a*(a + b*x)**(S(8)/S(3))/b**S(3) + S(3)/S(11)*(a + b*x)**(S(11)/S(3))/b**S(3)],
        [x**S(2)/(a + b*x)**(S(1)/S(3)), x, S(2), S(3)/S(2)*a**S(2)*(a + b*x)**(S(2)/S(3))/b**S(3) - S(6)/S(5)*a*(a + b*x)**(S(5)/S(3))/b**S(3) + S(3)/S(8)*(a + b*x)**(S(8)/S(3))/b**S(3)],
        [x**S(3)/( - a + b*x)**(S(1)/S(3)), x, S(2), S(3)/S(2)*a**S(3)*( - a + b*x)**(S(2)/S(3))/b**S(4) + S(9)/S(5)*a**S(2)*( - a + b*x)**(S(5)/S(3))/b**S(4) + S(9)/S(8)*a*( - a + b*x)**(S(8)/S(3))/b**S(4) + S(3)/S(11)*( - a + b*x)**(S(11)/S(3))/b**S(4)],
    ]

    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True)


def test_3():
    test = [
        [x**m*(a + b*x), x, S(2), a*x**(S(1) + m)/(S(1) + m) + b*x**(S(2) + m)/(S(2) + m)],
        [x**(S(5)/S(2))*(a + b*x), x, S(2), S(2)/S(7)*a*x**(S(7)/S(2)) + S(2)/S(9)*b*x**(S(9)/S(2))],
        [x**(S(5)/S(2))/(a + b*x), x, S(5), - S(2)/S(3)*a*x**(S(3)/S(2))/b**S(2) + S(2)/S(5)*x**(S(5)/S(2))/b - S(2)*a**(S(5)/S(2))*arctan(sqrt(b)*sqrt(x)/sqrt(a))/b**(S(7)/S(2)) + S(2)*a**S(2)*sqrt(x)/b**S(3)],
        [x**(S(3)/S(2))/(a + b*x), x, S(4), S(2)/S(3)*x**(S(3)/S(2))/b + S(2)*a**(S(3)/S(2))*arctan(sqrt(b)*sqrt(x)/sqrt(a))/b**(S(5)/S(2)) - S(2)*a*sqrt(x)/b**S(2)],
        [x**(S(5)/S(2))/( - a + b*x), x, S(5), S(2)/S(3)*a*x**(S(3)/S(2))/b**S(2) + S(2)/S(5)*x**(S(5)/S(2))/b - S(2)*a**(S(5)/S(2))*arctanh(sqrt(b)*sqrt(x)/sqrt(a))/b**(S(7)/S(2)) + S(2)*a**S(2)*sqrt(x)/b**S(3)],
        [x**(S(5)/S(2))*sqrt(a + b*x), x, S(6), - S(5)/S(64)*a**S(4)*arctanh(sqrt(b)*sqrt(x)/sqrt(a + b*x))/b**(S(7)/S(2)) - S(5)/S(96)*a**S(2)*x**(S(3)/S(2))*sqrt(a + b*x)/b**S(2) + S(1)/S(24)*a*x**(S(5)/S(2))*sqrt(a + b*x)/b + S(1)/S(4)*x**(S(7)/S(2))*sqrt(a + b*x) + S(5)/S(64)*a**S(3)*sqrt(x)*sqrt(a + b*x)/b**S(3)],
        [x**(S(3)/S(2))*sqrt(a + b*x), x, S(5), S(1)/S(8)*a**S(3)*arctanh(sqrt(b)*sqrt(x)/sqrt(a + b*x))/b**(S(5)/S(2)) + S(1)/S(12)*a*x**(S(3)/S(2))*sqrt(a + b*x)/b + S(1)/S(3)*x**(S(5)/S(2))*sqrt(a + b*x) - S(1)/S(8)*a**S(2)*sqrt(x)*sqrt(a + b*x)/b**S(2)],
        [x**(S(5)/S(2))/sqrt(a + b*x), x, S(5), - S(5)/S(8)*a**S(3)*arctanh(sqrt(b)*sqrt(x)/sqrt(a + b*x))/b**(S(7)/S(2)) - S(5)/S(12)*a*x**(S(3)/S(2))*sqrt(a + b*x)/b**S(2) + S(1)/S(3)*x**(S(5)/S(2))*sqrt(a + b*x)/b + S(5)/S(8)*a**S(2)*sqrt(x)*sqrt(a + b*x)/b**S(3)],
        [sqrt(x)/sqrt(a + b*x), x, S(3), - a*arctanh(sqrt(b)*sqrt(x)/sqrt(a + b*x))/b**(S(3)/S(2)) + sqrt(x)*sqrt(a + b*x)/b],
        [x**(S(2)/S(3))*(a + b*x), x, S(2), S(3)/S(5)*a*x**(S(5)/S(3)) + S(3)/S(8)*b*x**(S(8)/S(3))],
        [x**(S(1)/S(3))*(a + b*x), x, S(2), S(3)/S(4)*a*x**(S(4)/S(3)) + S(3)/S(7)*b*x**(S(7)/S(3))],
        [x**(S(5)/S(3))/(a + b*x), x, S(6), - S(3)/S(2)*a*x**(S(2)/S(3))/b**S(2) + S(3)/S(5)*x**(S(5)/S(3))/b - S(3)/S(2)*a**(S(5)/S(3))*log(a**(S(1)/S(3)) + b**(S(1)/S(3))*x**(S(1)/S(3)))/b**(S(8)/S(3)) + S(1)/S(2)*a**(S(5)/S(3))*log(a + b*x)/b**(S(8)/S(3)) - a**(S(5)/S(3))*arctan((a**(S(1)/S(3)) - S(2)*b**(S(1)/S(3))*x**(S(1)/S(3)))/(a**(S(1)/S(3))*sqrt(S(3))))*sqrt(S(3))/b**(S(8)/S(3))],
        [x**(S(4)/S(3))/(a + b*x), x, S(6), - S(3)*a*x**(S(1)/S(3))/b**S(2) + S(3)/S(4)*x**(S(4)/S(3))/b + S(3)/S(2)*a**(S(4)/S(3))*log(a**(S(1)/S(3)) + b**(S(1)/S(3))*x**(S(1)/S(3)))/b**(S(7)/S(3)) - S(1)/S(2)*a**(S(4)/S(3))*log(a + b*x)/b**(S(7)/S(3)) - a**(S(4)/S(3))*arctan((a**(S(1)/S(3)) - S(2)*b**(S(1)/S(3))*x**(S(1)/S(3)))/(a**(S(1)/S(3))*sqrt(S(3))))*sqrt(S(3))/b**(S(7)/S(3))],
        [(S(1) - x)**(S(1)/S(4))/(S(1) + x), x, S(5), S(4)*(S(1) - x)**(S(1)/S(4)) - S(2)*S(2)**(S(1)/S(4))*arctan((S(1) - x)**(S(1)/S(4))/S(2)**(S(1)/S(4))) - S(2)*S(2)**(S(1)/S(4))*arctanh((S(1) - x)**(S(1)/S(4))/S(2)**(S(1)/S(4)))],
        [x**m*(a + b*x)**S(2), x, S(2), a**S(2)*x**(S(1) + m)/(S(1) + m) + S(2)*a*b*x**(S(2) + m)/(S(2) + m) + b**S(2)*x**(S(3) + m)/(S(3) + m)],
    ]

    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True)

def test_4():
    test = [
        [x**m/(a + b*x)**S(2), x, S(1), x**(S(1) + m)*hypergeom([S(2), S(1) + m], [S(2) + m], - b*x/a)/(a**S(2)*(S(1) + m))],
        [x**m/sqrt(S(2) + S(3)*x), x, S(1), x**(S(1) + m)*hypergeom([S(1)/S(2), S(1) + m], [S(2) + m], - S(3)/S(2)*x)/((S(1) + m)*sqrt(S(2)))],
        [x**m*(a + b*x)**n, x, S(2), x**(S(1) + m)*(a + b*x)**n*hypergeom([S(1) + m, - n], [S(2) + m], - b*x/a)/((S(1) + m)*(S(1) + b*x/a)**n)],
        [x**( - S(1) + n)/(a + b*x)**n, x, S(2), x**n*(S(1) + b*x/a)**n*hypergeom([n, n], [S(1) + n], - b*x/a)/(n*(a + b*x)**n)],
        [(c + d*(a + b*x))**(S(5)/S(2)), x, S(2), S(2)/S(7)*(c + d*(a + b*x))**(S(7)/S(2))/(b*d)],
        [(c + d*(a + b*x))**(S(3)/S(2)), x, S(2), S(2)/S(5)*(c + d*(a + b*x))**(S(5)/S(2))/(b*d)],
        [(a + b*x)**S(3)/(a*d/b + d*x)**S(3), x, S(2), b**S(3)*x/d**S(3)],
        [(a + b*x)*(a*c - b*c*x)**S(3), x, S(2), - S(1)/S(2)*a*c**S(3)*(a - b*x)**S(4)/b + S(1)/S(5)*c**S(3)*(a - b*x)**S(5)/b],
        [(a*c - b*c*x)**S(3)/(a + b*x), x, S(2), - S(4)*a**S(2)*c**S(3)*x + a*c**S(3)*(a - b*x)**S(2)/b + S(1)/S(3)*c**S(3)*(a - b*x)**S(3)/b + S(8)*a**S(3)*c**S(3)*log(a + b*x)/b],
        [S(1)/((a + b*x)**S(2)*(a*c - b*c*x)), x, S(3), ( - S(1)/S(2))/(a*b*c*(a + b*x)) + S(1)/S(2)*arctanh(b*x/a)/(a**S(2)*b*c)],
        [(S(1) + x)**(S(1)/S(2))/(S(1) - x)**(S(9)/S(2)), x, S(3), S(1)/S(7)*(S(1) + x)**(S(3)/S(2))/(S(1) - x)**(S(7)/S(2)) + S(2)/S(35)*(S(1) + x)**(S(3)/S(2))/(S(1) - x)**(S(5)/S(2)) + S(2)/S(105)*(S(1) + x)**(S(3)/S(2))/(S(1) - x)**(S(3)/S(2))],
        [(S(1) + x)**(S(5)/S(2))/(S(1) - x)**(S(1)/S(2)), x, S(5), S(5)/S(2)*arcsin(x) - S(5)/S(6)*(S(1) + x)**(S(3)/S(2))*sqrt(S(1) - x) - S(1)/S(3)*(S(1) + x)**(S(5)/S(2))*sqrt(S(1) - x) - S(5)/S(2)*sqrt(S(1) - x)*sqrt(S(1) + x)],
    ]
    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True)


def test_5():
    test = [
        [(S(1) + a*x)**(S(3)/S(2))/sqrt(S(1) - a*x), x, S(4), S(3)/S(2)*arcsin(a*x)/a - S(1)/S(2)*(S(1) + a*x)**(S(3)/S(2))*sqrt(S(1) - a*x)/a - S(3)/S(2)*sqrt(S(1) - a*x)*sqrt(S(1) + a*x)/a],
        [(S(1) - x)**(S(1)/S(2))/(S(1) + x)**(S(1)/S(2)), x, S(3), arcsin(x) + sqrt(S(1) - x)*sqrt(S(1) + x)],
        [S(1)/((S(1) - x)**(S(1)/S(2))*(S(1) + x)**(S(3)/S(2))), x, S(1), - sqrt(S(1) - x)/sqrt(S(1) + x)],
        [(a + a*x)**(S(5)/S(2))*(c - c*x)**(S(5)/S(2)), x, S(5), S(5)/S(24)*a*c*x*(a + a*x)**(S(3)/S(2))*(c - c*x)**(S(3)/S(2)) + S(1)/S(6)*x*(a + a*x)**(S(5)/S(2))*(c - c*x)**(S(5)/S(2)) + S(5)/S(8)*a**(S(5)/S(2))*c**(S(5)/S(2))*arctan(sqrt(c)*sqrt(a + a*x)/(sqrt(a)*sqrt(c - c*x))) + S(5)/S(16)*a**S(2)*c**S(2)*x*sqrt(a + a*x)*sqrt(c - c*x)],
        [S(1)/((a + a*x)**(S(5)/S(2))*(c - c*x)**(S(5)/S(2))), x, S(2), S(1)/S(3)*x/(a*c*(a + a*x)**(S(3)/S(2))*(c - c*x)**(S(3)/S(2))) + S(2)/S(3)*x/(a**S(2)*c**S(2)*sqrt(a + a*x)*sqrt(c - c*x))],
        [(S(3) - x)**(S(1)/S(2))*( - S(2) + x)**(S(1)/S(2)), x, S(5), - S(1)/S(8)*arcsin(S(5) - S(2)*x) - S(1)/S(2)*(S(3) - x)**(S(3)/S(2))*sqrt( - S(2) + x) + S(1)/S(4)*sqrt(S(3) - x)*sqrt( - S(2) + x)],
        [S(1)/(sqrt(a + b*x)*sqrt( - a*d + b*d*x)), x, S(2), S(2)*arctanh(sqrt(d)*sqrt(a + b*x)/sqrt( - a*d + b*d*x))/(b*sqrt(d))],
        [S(1)/((a - I*a*x)**(S(7)/S(4))*(a + I*a*x)**(S(1)/S(4))), x, S(1), - S(2)/S(3)*I*(a + I*a*x)**(S(3)/S(4))/(a**S(2)*(a - I*a*x)**(S(3)/S(4)))],
        [(a + b*x)**S(2)*(a*c - b*c*x)**n, x, S(2), - S(4)*a**S(2)*(a*c - b*c*x)**(S(1) + n)/(b*c*(S(1) + n)) + S(4)*a*(a*c - b*c*x)**(S(2) + n)/(b*c**S(2)*(S(2) + n)) - (a*c - b*c*x)**(S(3) + n)/(b*c**S(3)*(S(3) + n))],
        [(a + b*x)**S(4)*(c + d*x), x, S(2), S(1)/S(5)*(b*c - a*d)*(a + b*x)**S(5)/b**S(2) + S(1)/S(6)*d*(a + b*x)**S(6)/b**S(2)],
        [(a + b*x)*(c + d*x), x, S(2), a*c*x + S(1)/S(2)*(b*c + a*d)*x**S(2) + S(1)/S(3)*b*d*x**S(3)],
        [(a + b*x)**S(5)/(c + d*x), x, S(2), b*(b*c - a*d)**S(4)*x/d**S(5) - S(1)/S(2)*(b*c - a*d)**S(3)*(a + b*x)**S(2)/d**S(4) + S(1)/S(3)*(b*c - a*d)**S(2)*(a + b*x)**S(3)/d**S(3) - S(1)/S(4)*(b*c - a*d)*(a + b*x)**S(4)/d**S(2) + S(1)/S(5)*(a + b*x)**S(5)/d - (b*c - a*d)**S(5)*log(c + d*x)/d**S(6)],
        [(a + b*x)/(c + d*x)**S(3), x, S(1), S(1)/S(2)*(a + b*x)**S(2)/((b*c - a*d)*(c + d*x)**S(2))],
        [(a + b*x)**S(5)*(c + d*x)**(S(1)/S(2)), x, S(2), - S(2)/S(3)*(b*c - a*d)**S(5)*(c + d*x)**(S(3)/S(2))/d**S(6) + S(2)*b*(b*c - a*d)**S(4)*(c + d*x)**(S(5)/S(2))/d**S(6) - S(20)/S(7)*b**S(2)*(b*c - a*d)**S(3)*(c + d*x)**(S(7)/S(2))/d**S(6) + S(20)/S(9)*b**S(3)*(b*c - a*d)**S(2)*(c + d*x)**(S(9)/S(2))/d**S(6) - S(10)/S(11)*b**S(4)*(b*c - a*d)*(c + d*x)**(S(11)/S(2))/d**S(6) + S(2)/S(13)*b**S(5)*(c + d*x)**(S(13)/S(2))/d**S(6)],
        [(c + d*x)**(S(1)/S(2))/(a + b*x)**S(2), x, S(3), - d*arctanh(sqrt(b)*sqrt(c + d*x)/sqrt(b*c - a*d))/(b**(S(3)/S(2))*sqrt(b*c - a*d)) - sqrt(c + d*x)/(b*(a + b*x))],
    ]

    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True)


def test_6():
    test = [
        [(S(1) + a*x)**(S(3)/S(2))/sqrt(S(1) - a*x), x, S(4), S(3)/S(2)*arcsin(a*x)/a - S(1)/S(2)*(S(1) + a*x)**(S(3)/S(2))*sqrt(S(1) - a*x)/a - S(3)/S(2)*sqrt(S(1) - a*x)*sqrt(S(1) + a*x)/a],
        [(S(1) - x)**(S(1)/S(2))/(S(1) + x)**(S(1)/S(2)), x, S(3), arcsin(x) + sqrt(S(1) - x)*sqrt(S(1) + x)],
        [S(1)/((S(1) - x)**(S(1)/S(2))*(S(1) + x)**(S(3)/S(2))), x, S(1), - sqrt(S(1) - x)/sqrt(S(1) + x)],
        [(a + a*x)**(S(5)/S(2))*(c - c*x)**(S(5)/S(2)), x, S(5), S(5)/S(24)*a*c*x*(a + a*x)**(S(3)/S(2))*(c - c*x)**(S(3)/S(2)) + S(1)/S(6)*x*(a + a*x)**(S(5)/S(2))*(c - c*x)**(S(5)/S(2)) + S(5)/S(8)*a**(S(5)/S(2))*c**(S(5)/S(2))*arctan(sqrt(c)*sqrt(a + a*x)/(sqrt(a)*sqrt(c - c*x))) + S(5)/S(16)*a**S(2)*c**S(2)*x*sqrt(a + a*x)*sqrt(c - c*x)],
        [S(1)/((a + a*x)**(S(5)/S(2))*(c - c*x)**(S(5)/S(2))), x, S(2), S(1)/S(3)*x/(a*c*(a + a*x)**(S(3)/S(2))*(c - c*x)**(S(3)/S(2))) + S(2)/S(3)*x/(a**S(2)*c**S(2)*sqrt(a + a*x)*sqrt(c - c*x))],
        [(S(3) - x)**(S(1)/S(2))*( - S(2) + x)**(S(1)/S(2)), x, S(5), - S(1)/S(8)*arcsin(S(5) - S(2)*x) - S(1)/S(2)*(S(3) - x)**(S(3)/S(2))*sqrt( - S(2) + x) + S(1)/S(4)*sqrt(S(3) - x)*sqrt( - S(2) + x)],
        [S(1)/(sqrt(a + b*x)*sqrt( - a*d + b*d*x)), x, S(2), S(2)*arctanh(sqrt(d)*sqrt(a + b*x)/sqrt( - a*d + b*d*x))/(b*sqrt(d))],
        [S(1)/((a - I*a*x)**(S(7)/S(4))*(a + I*a*x)**(S(1)/S(4))), x, S(1), - S(2)/S(3)*I*(a + I*a*x)**(S(3)/S(4))/(a**S(2)*(a - I*a*x)**(S(3)/S(4)))],
        [(a + b*x)**S(2)*(a*c - b*c*x)**n, x, S(2), - S(4)*a**S(2)*(a*c - b*c*x)**(S(1) + n)/(b*c*(S(1) + n)) + S(4)*a*(a*c - b*c*x)**(S(2) + n)/(b*c**S(2)*(S(2) + n)) - (a*c - b*c*x)**(S(3) + n)/(b*c**S(3)*(S(3) + n))],
        [(a + b*x)**S(4)*(c + d*x), x, S(2), S(1)/S(5)*(b*c - a*d)*(a + b*x)**S(5)/b**S(2) + S(1)/S(6)*d*(a + b*x)**S(6)/b**S(2)],
        [(a + b*x)*(c + d*x), x, S(2), a*c*x + S(1)/S(2)*(b*c + a*d)*x**S(2) + S(1)/S(3)*b*d*x**S(3)],
        [(a + b*x)**S(5)/(c + d*x), x, S(2), b*(b*c - a*d)**S(4)*x/d**S(5) - S(1)/S(2)*(b*c - a*d)**S(3)*(a + b*x)**S(2)/d**S(4) + S(1)/S(3)*(b*c - a*d)**S(2)*(a + b*x)**S(3)/d**S(3) - S(1)/S(4)*(b*c - a*d)*(a + b*x)**S(4)/d**S(2) + S(1)/S(5)*(a + b*x)**S(5)/d - (b*c - a*d)**S(5)*log(c + d*x)/d**S(6)],
        [(a + b*x)/(c + d*x)**S(3), x, S(1), S(1)/S(2)*(a + b*x)**S(2)/((b*c - a*d)*(c + d*x)**S(2))],
        [(a + b*x)**S(5)*(c + d*x)**(S(1)/S(2)), x, S(2), - S(2)/S(3)*(b*c - a*d)**S(5)*(c + d*x)**(S(3)/S(2))/d**S(6) + S(2)*b*(b*c - a*d)**S(4)*(c + d*x)**(S(5)/S(2))/d**S(6) - S(20)/S(7)*b**S(2)*(b*c - a*d)**S(3)*(c + d*x)**(S(7)/S(2))/d**S(6) + S(20)/S(9)*b**S(3)*(b*c - a*d)**S(2)*(c + d*x)**(S(9)/S(2))/d**S(6) - S(10)/S(11)*b**S(4)*(b*c - a*d)*(c + d*x)**(S(11)/S(2))/d**S(6) + S(2)/S(13)*b**S(5)*(c + d*x)**(S(13)/S(2))/d**S(6)],
        [(c + d*x)**(S(1)/S(2))/(a + b*x)**S(2), x, S(3), - d*arctanh(sqrt(b)*sqrt(c + d*x)/sqrt(b*c - a*d))/(b**(S(3)/S(2))*sqrt(b*c - a*d)) - sqrt(c + d*x)/(b*(a + b*x))],
        [(a + b*x)**S(4)/(c + d*x)**(S(1)/S(2)), x, S(2), - S(8)/S(3)*b*(b*c - a*d)**S(3)*(c + d*x)**(S(3)/S(2))/d**S(5) + S(12)/S(5)*b**S(2)*(b*c - a*d)**S(2)*(c + d*x)**(S(5)/S(2))/d**S(5) - S(8)/S(7)*b**S(3)*(b*c - a*d)*(c + d*x)**(S(7)/S(2))/d**S(5) + S(2)/S(9)*b**S(4)*(c + d*x)**(S(9)/S(2))/d**S(5) + S(2)*(b*c - a*d)**S(4)*sqrt(c + d*x)/d**S(5)],
        [(a + b*x)**S(2)/(c + d*x)**(S(1)/S(2)), x, S(2), - S(4)/S(3)*b*(b*c - a*d)*(c + d*x)**(S(3)/S(2))/d**S(3) + S(2)/S(5)*b**S(2)*(c + d*x)**(S(5)/S(2))/d**S(3) + S(2)*(b*c - a*d)**S(2)*sqrt(c + d*x)/d**S(3)],
        [(S(1) - x)**(S(1)/S(3))/(S(1) + x), x, S(5), S(3)*(S(1) - x)**(S(1)/S(3)) + S(3)*log(S(2)**(S(1)/S(3)) - (S(1) - x)**(S(1)/S(3)))/S(2)**(S(2)/S(3)) - log(S(1) + x)/S(2)**(S(2)/S(3)) - S(2)**(S(1)/S(3))*arctan((S(1) + S(2)**(S(2)/S(3))*(S(1) - x)**(S(1)/S(3)))/sqrt(S(3)))*sqrt(S(3))],
        [(c + d*x)**(S(1)/S(2))/(a + b*x)**(S(1)/S(2)), x, S(3), (b*c - a*d)*arctanh(sqrt(d)*sqrt(a + b*x)/(sqrt(b)*sqrt(c + d*x)))/(b**(S(3)/S(2))*sqrt(d)) + sqrt(a + b*x)*sqrt(c + d*x)/b],
        [(a + b*x)**(S(1)/S(2))*(c + d*x)**(S(3)/S(2)), x, S(5), S(1)/S(3)*(a + b*x)**(S(3)/S(2))*(c + d*x)**(S(3)/S(2))/b - S(1)/S(8)*(b*c - a*d)**S(3)*arctanh(sqrt(d)*sqrt(a + b*x)/(sqrt(b)*sqrt(c + d*x)))/(b**(S(5)/S(2))*d**(S(3)/S(2))) + S(1)/S(4)*(b*c - a*d)*(a + b*x)**(S(3)/S(2))*sqrt(c + d*x)/b**S(2) + S(1)/S(8)*(b*c - a*d)**S(2)*sqrt(a + b*x)*sqrt(c + d*x)/(b**S(2)*d)],
        [(a + b*x)**(S(1)/S(2))/(c + d*x)**(S(1)/S(2)), x, S(3), - (b*c - a*d)*arctanh(sqrt(d)*sqrt(a + b*x)/(sqrt(b)*sqrt(c + d*x)))/(d**(S(3)/S(2))*sqrt(b)) + sqrt(a + b*x)*sqrt(c + d*x)/d],
        [S(1)/((a + b*x)**(S(1)/S(2))*(c + d*x)**(S(5)/S(2))), x, S(2), S(2)/S(3)*sqrt(a + b*x)/((b*c - a*d)*(c + d*x)**(S(3)/S(2))) + S(4)/S(3)*b*sqrt(a + b*x)/((b*c - a*d)**S(2)*sqrt(c + d*x))],
        [(a + b*x)**m*(c + d*x)**(S(1) + S(2)*n - S(2)*(S(1) + n)), x, S(2), (a + b*x)**(S(1) + m)*hypergeom([S(1), S(1) + m], [S(2) + m], - d*(a + b*x)/(b*c - a*d))/((b*c - a*d)*(S(1) + m))],
        [a + b*x + c*x**S(2) + d*x**S(3), x, S(1), a*x + S(1)/S(2)*b*x**S(2) + S(1)/S(3)*c*x**S(3) + S(1)/S(4)*d*x**S(4)],
        [a + d/x**S(3) + c/x**S(2) + b/x, x, S(1), - S(1)/S(2)*d/x**S(2) - c/x + a*x + b*log(x)],
    ]

    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True)


def test_7():
    test = [
        #[(a + b*x)**(S(3)/S(2))*(c + d*x)**(S(1)/S(3)), x, S(5), S(12)/S(187)*(b*c - a*d)*(a + b*x)**(S(3)/S(2))*(c + d*x)**(S(1)/S(3))/(b*d) + S(6)/S(17)*(a + b*x)**(S(5)/S(2))*(c + d*x)**(S(1)/S(3))/b - S(108)/S(935)*(b*c - a*d)**S(2)*(c + d*x)**(S(1)/S(3))*sqrt(a + b*x)/(b*d**S(2)) - S(108)/S(935)*S(3)**(S(3)/S(4))*(b*c - a*d)**S(3)*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))*EllipticF(( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) + sqrt(S(3))))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3)))), sqrt( - S(7) + S(4)*sqrt(S(3))))*sqrt(((b*c - a*d)**(S(2)/S(3)) + b**(S(1)/S(3))*(b*c - a*d)**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + b**(S(2)/S(3))*(c + d*x)**(S(2)/S(3)))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3))))**S(2))*sqrt(S(2) - sqrt(S(3)))/(b**(S(4)/S(3))*d**S(3)*sqrt(a - b*c/d + b*(c + d*x)/d)*sqrt( - (b*c - a*d)**(S(1)/S(3))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3))))**S(2)))],
        #[(a + b*x)**(S(3)/S(2))/(c + d*x)**(S(1)/S(3)), x, S(6), S(6)/S(13)*(a + b*x)**(S(3)/S(2))*(c + d*x)**(S(2)/S(3))/d - S(54)/S(91)*(b*c - a*d)*(c + d*x)**(S(2)/S(3))*sqrt(a + b*x)/d**S(2) - S(162)/S(91)*(b*c - a*d)**S(2)*sqrt(a - b*c/d + b*(c + d*x)/d)/(b**(S(2)/S(3))*d**S(2)*( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3))))) - S(54)/S(91)*S(3)**(S(3)/S(4))*(b*c - a*d)**(S(7)/S(3))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))*EllipticF(( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) + sqrt(S(3))))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3)))), sqrt( - S(7) + S(4)*sqrt(S(3))))*sqrt(S(2))*sqrt(((b*c - a*d)**(S(2)/S(3)) + b**(S(1)/S(3))*(b*c - a*d)**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + b**(S(2)/S(3))*(c + d*x)**(S(2)/S(3)))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3))))**S(2))/(b**(S(2)/S(3))*d**S(3)*sqrt(a - b*c/d + b*(c + d*x)/d)*sqrt( - (b*c - a*d)**(S(1)/S(3))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3))))**S(2))) + S(81)/S(91)*S(3)**(S(1)/S(4))*(b*c - a*d)**(S(7)/S(3))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))*EllipticE(( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) + sqrt(S(3))))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3)))), sqrt( - S(7) + S(4)*sqrt(S(3))))*sqrt(((b*c - a*d)**(S(2)/S(3)) + b**(S(1)/S(3))*(b*c - a*d)**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + b**(S(2)/S(3))*(c + d*x)**(S(2)/S(3)))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3))))**S(2))*sqrt(S(2) + sqrt(S(3)))/(b**(S(2)/S(3))*d**S(3)*sqrt(a - b*c/d + b*(c + d*x)/d)*sqrt( - (b*c - a*d)**(S(1)/S(3))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))/( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + (b*c - a*d)**(S(1)/S(3))*(S(1) - sqrt(S(3))))**S(2)))],
        [(a + b*x)**(S(2)/S(3))*(c + d*x)**(S(1)/S(3)), x, S(3), S(1)/S(6)*(b*c - a*d)*(a + b*x)**(S(2)/S(3))*(c + d*x)**(S(1)/S(3))/(b*d) + S(1)/S(2)*(a + b*x)**(S(5)/S(3))*(c + d*x)**(S(1)/S(3))/b + S(1)/S(18)*(b*c - a*d)**S(2)*log(c + d*x)/(b**(S(4)/S(3))*d**(S(5)/S(3))) + S(1)/S(6)*(b*c - a*d)**S(2)*log( - S(1) + d**(S(1)/S(3))*(a + b*x)**(S(1)/S(3))/(b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))))/(b**(S(4)/S(3))*d**(S(5)/S(3))) + S(1)/S(3)*(b*c - a*d)**S(2)*arctan(S(1)/sqrt(S(3)) + S(2)*d**(S(1)/S(3))*(a + b*x)**(S(1)/S(3))/(b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*sqrt(S(3))))/(b**(S(4)/S(3))*d**(S(5)/S(3))*sqrt(S(3)))],
        [(a + b*x)**(S(4)/S(3))/(c + d*x)**(S(1)/S(3)), x, S(3), - S(2)/S(3)*(b*c - a*d)*(a + b*x)**(S(1)/S(3))*(c + d*x)**(S(2)/S(3))/d**S(2) + S(1)/S(2)*(a + b*x)**(S(4)/S(3))*(c + d*x)**(S(2)/S(3))/d - S(1)/S(9)*(b*c - a*d)**S(2)*log(a + b*x)/(b**(S(2)/S(3))*d**(S(7)/S(3))) - S(1)/S(3)*(b*c - a*d)**S(2)*log( - S(1) + b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))/(d**(S(1)/S(3))*(a + b*x)**(S(1)/S(3))))/(b**(S(2)/S(3))*d**(S(7)/S(3))) - S(2)/S(3)*(b*c - a*d)**S(2)*arctan(S(1)/sqrt(S(3)) + S(2)*b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))/(d**(S(1)/S(3))*(a + b*x)**(S(1)/S(3))*sqrt(S(3))))/(b**(S(2)/S(3))*d**(S(7)/S(3))*sqrt(S(3)))],
        #[(a + b*x)**(S(5)/S(2))/(c + d*x)**(S(1)/S(4)), x, S(10), - S(40)/S(117)*(b*c - a*d)*(a + b*x)**(S(3)/S(2))*(c + d*x)**(S(3)/S(4))/d**S(2) + S(4)/S(13)*(a + b*x)**(S(5)/S(2))*(c + d*x)**(S(3)/S(4))/d + S(16)/S(39)*(b*c - a*d)**S(2)*(c + d*x)**(S(3)/S(4))*sqrt(a + b*x)/d**S(3) - S(32)/S(39)*(b*c - a*d)**(S(15)/S(4))*EllipticE(b**(S(1)/S(4))*(c + d*x)**(S(1)/S(4))/(b*c - a*d)**(S(1)/S(4)), I)*sqrt(S(1) - b*(c + d*x)/(b*c - a*d))/(b**(S(3)/S(4))*d**S(4)*sqrt(a - b*c/d + b*(c + d*x)/d)) + S(32)/S(39)*(b*c - a*d)**(S(15)/S(4))*EllipticF(b**(S(1)/S(4))*(c + d*x)**(S(1)/S(4))/(b*c - a*d)**(S(1)/S(4)), I)*sqrt(S(1) - b*(c + d*x)/(b*c - a*d))/(b**(S(3)/S(4))*d**S(4)*sqrt(a - b*c/d + b*(c + d*x)/d))],
        [(c + d*x)**(S(5)/S(4))/(a + b*x)**(S(25)/S(4)), x, S(4), - S(4)/S(21)*(c + d*x)**(S(9)/S(4))/((b*c - a*d)*(a + b*x)**(S(21)/S(4))) + S(16)/S(119)*d*(c + d*x)**(S(9)/S(4))/((b*c - a*d)**S(2)*(a + b*x)**(S(17)/S(4))) - S(128)/S(1547)*d**S(2)*(c + d*x)**(S(9)/S(4))/((b*c - a*d)**S(3)*(a + b*x)**(S(13)/S(4))) + S(512)/S(13923)*d**S(3)*(c + d*x)**(S(9)/S(4))/((b*c - a*d)**S(4)*(a + b*x)**(S(9)/S(4)))],
        [(a + b*x)**(S(5)/S(4))/(c + d*x)**(S(1)/S(4)), x, S(6), - S(5)/S(8)*(b*c - a*d)*(a + b*x)**(S(1)/S(4))*(c + d*x)**(S(3)/S(4))/d**S(2) + S(1)/S(2)*(a + b*x)**(S(5)/S(4))*(c + d*x)**(S(3)/S(4))/d + S(5)/S(16)*(b*c - a*d)**S(2)*arctan(d**(S(1)/S(4))*(a + b*x)**(S(1)/S(4))/(b**(S(1)/S(4))*(c + d*x)**(S(1)/S(4))))/(b**(S(3)/S(4))*d**(S(9)/S(4))) + S(5)/S(16)*(b*c - a*d)**S(2)*arctanh(d**(S(1)/S(4))*(a + b*x)**(S(1)/S(4))/(b**(S(1)/S(4))*(c + d*x)**(S(1)/S(4))))/(b**(S(3)/S(4))*d**(S(9)/S(4)))],
        [S(1)/((a + b*x)**(S(3)/S(4))*(c + d*x)**(S(1)/S(4))), x, S(4), S(2)*arctan(d**(S(1)/S(4))*(a + b*x)**(S(1)/S(4))/(b**(S(1)/S(4))*(c + d*x)**(S(1)/S(4))))/(b**(S(3)/S(4))*d**(S(1)/S(4))) + S(2)*arctanh(d**(S(1)/S(4))*(a + b*x)**(S(1)/S(4))/(b**(S(1)/S(4))*(c + d*x)**(S(1)/S(4))))/(b**(S(3)/S(4))*d**(S(1)/S(4)))],
        #[(a + b*x)**(S(3)/S(2))/(c + d*x)**(S(1)/S(5)), x, S(2), S(2)/S(5)*(a + b*x)**(S(5)/S(2))*(b*(c + d*x)/(b*c - a*d))**(S(1)/S(5))*hypergeom([S(1)/S(5), S(5)/S(2)], [S(7)/S(2)], - d*(a + b*x)/(b*c - a*d))/(b*(c + d*x)**(S(1)/S(5)))],
        #[(a + b*x)**(S(5)/S(2))/(c + d*x)**(S(1)/S(6)), x, S(7), - S(9)/S(28)*(b*c - a*d)*(a + b*x)**(S(3)/S(2))*(c + d*x)**(S(5)/S(6))/d**S(2) + S(3)/S(10)*(a + b*x)**(S(5)/S(2))*(c + d*x)**(S(5)/S(6))/d + S(81)/S(224)*(b*c - a*d)**S(2)*(c + d*x)**(S(5)/S(6))*sqrt(a + b*x)/d**S(3) + S(243)/S(448)*(b*c - a*d)**S(3)*(c + d*x)**(S(1)/S(6))*(S(1) + sqrt(S(3)))*sqrt(a - b*c/d + b*(c + d*x)/d)/(b**(S(2)/S(3))*d**S(3)*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))) + S(243)/S(448)*S(3)**(S(1)/S(4))*(b*c - a*d)**(S(10)/S(3))*(c + d*x)**(S(1)/S(6))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))*sqrt(cos(arccos(((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) - sqrt(S(3))))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))))**S(2))/cos(arccos(((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) - sqrt(S(3))))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))))*EllipticE(sin(arccos(((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) - sqrt(S(3))))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3)))))), sqrt(S(1)/S(4)*(S(2) + sqrt(S(3)))))*sqrt(((b*c - a*d)**(S(2)/S(3)) + b**(S(1)/S(3))*(b*c - a*d)**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + b**(S(2)/S(3))*(c + d*x)**(S(2)/S(3)))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))**S(2))/(b**(S(2)/S(3))*d**S(4)*sqrt(a - b*c/d + b*(c + d*x)/d)*sqrt( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))**S(2))) + S(81)/S(896)*S(3)**(S(3)/S(4))*(b*c - a*d)**(S(10)/S(3))*(c + d*x)**(S(1)/S(6))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))*sqrt(cos(arccos(((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) - sqrt(S(3))))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))))**S(2))/cos(arccos(((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) - sqrt(S(3))))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))))*EllipticF(sin(arccos(((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) - sqrt(S(3))))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3)))))), sqrt(S(1)/S(4)*(S(2) + sqrt(S(3)))))*(S(1) - sqrt(S(3)))*sqrt(((b*c - a*d)**(S(2)/S(3)) + b**(S(1)/S(3))*(b*c - a*d)**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)) + b**(S(2)/S(3))*(c + d*x)**(S(2)/S(3)))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))**S(2))/(b**(S(2)/S(3))*d**S(4)*sqrt(a - b*c/d + b*(c + d*x)/d)*sqrt( - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3)))/((b*c - a*d)**(S(1)/S(3)) - b**(S(1)/S(3))*(c + d*x)**(S(1)/S(3))*(S(1) + sqrt(S(3))))**S(2)))],
        #[(a + b*x)**m*(c + d*x)**n, x, S(2), - (a + b*x)**(S(1) + m)*(c + d*x)**(S(1) + n)*hypergeom([S(1), S(2) + m + n], [S(2) + n], b*(c + d*x)/(b*c - a*d))/((b*c - a*d)*(S(1) + n)), (a + b*x)**(S(1) + m)*(c + d*x)**n*hypergeom([S(1) + m, - n], [S(2) + m], - d*(a + b*x)/(b*c - a*d))/(b*(S(1) + m)*(b*(c + d*x)/(b*c - a*d))**n)],
    ]

    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True)


def test_numerical():
    test = [
        [(a + b*x)**(S(1)/S(2))*(c + d*x)**(S(1)/S(4)), x, S(5), S(4)/S(7)*(a + b*x)**(S(3)/S(2))*(c + d*x)**(S(1)/S(4))/b + S(4)/S(21)*(b*c - a*d)*(c + d*x)**(S(1)/S(4))*sqrt(a + b*x)/(b*d) - S(8)/S(21)*(b*c - a*d)**(S(9)/S(4))*EllipticF(b**(S(1)/S(4))*(c + d*x)**(S(1)/S(4))/(b*c - a*d)**(S(1)/S(4)), I)*sqrt(S(1) - b*(c + d*x)/(b*c - a*d))/(b**(S(5)/S(4))*d**S(2)*sqrt(a - b*c/d + b*(c + d*x)/d))],
        [S(1)/((a + b*x)*(a*d/b + d*x)**S(3)), x, S(2), - S(1)/S(3)*b**S(2)/(d**S(3)*(a + b*x)**S(3))],
    ]

    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True, _numerical=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True, _numerical=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True, _numerical=True)
