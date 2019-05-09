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
from sympy.integrals.rubi.utility_function import EllipticE, EllipticF, EllipticPi, hypergeom, rubi_test, AppellF1
from sympy import pi as Pi
from sympy import S, hyper, I, simplify, exp_polar, symbols, Integral
from sympy.utilities.pytest import XFAIL

A, B, C, D, a, b, c, d, e, f, g, h, i, m, n, p, x, u = symbols('A B C D a b c d e f g h i m n p x u')

def test_1():
    '''
    Tests for Rubi Algebraic 1.2 rules. Parsed from Maple syntax
    All tests: http://www.apmaths.uwo.ca/~arich/IntegrationProblems/MapleSyntaxFiles/MapleSyntaxFiles.html
    Note: Some tests are commented since they depend rules other than Algebraic1.2.
    '''
    test = [
        [(a + b*x)**S(2)*(e + f*x)*sqrt(c + d*x)/x, x, S(5), S(2)/S(7)*f*(a + b*x)**S(2)*(c + d*x)**(S(3)/S(2))/d + S(2)/S(105)*(c + d*x)**(S(3)/S(2))*(S(2)*(S(10)*a**S(2)*d**S(2)*f - b**S(2)*c*(S(7)*d*e - S(4)*c*f) + S(7)*a*b*d*(S(5)*d*e - S(2)*c*f)) + S(3)*b*d*(S(7)*b*d*e - S(4)*b*c*f + S(4)*a*d*f)*x)/d**S(3) - S(2)*a**S(2)*e*arctanh(sqrt(c + d*x)/sqrt(c))*sqrt(c) + S(2)*a**S(2)*e*sqrt(c + d*x)],
        [(a + b*x)*(e + f*x)*sqrt(c + d*x)/x, x, S(4), - S(2)/S(15)*(c + d*x)**(S(3)/S(2))*(S(2)*b*c*f - S(5)*d*(b*e + a*f) - S(3)*b*d*f*x)/d**S(2) - S(2)*a*e*arctanh(sqrt(c + d*x)/sqrt(c))*sqrt(c) + S(2)*a*e*sqrt(c + d*x)],
        [(c + d*x)**S(2)*(e + f*x)*sqrt(a + b*x)/x, x, S(5), S(2)/S(7)*f*(a + b*x)**(S(3)/S(2))*(c + d*x)**S(2)/b + S(2)/S(105)*(a + b*x)**(S(3)/S(2))*(S(2)*(S(4)*a**S(2)*d**S(2)*f - S(7)*a*b*d*(d*e + S(2)*c*f) + S(5)*b**S(2)*c*(S(7)*d*e + S(2)*c*f)) + S(3)*b*d*(S(7)*b*d*e + S(4)*b*c*f - S(4)*a*d*f)*x)/b**S(3) - S(2)*c**S(2)*e*arctanh(sqrt(a + b*x)/sqrt(a))*sqrt(a) + S(2)*c**S(2)*e*sqrt(a + b*x)],
        [(c + d*x)*(e + f*x)*sqrt(a + b*x)/x, x, S(4), - S(2)/S(15)*(a + b*x)**(S(3)/S(2))*(S(2)*a*d*f - S(5)*b*(d*e + c*f) - S(3)*b*d*f*x)/b**S(2) - S(2)*c*e*arctanh(sqrt(a + b*x)/sqrt(a))*sqrt(a) + S(2)*c*e*sqrt(a + b*x)],
        [x**S(4)*(e + f*x)**n/((a + b*x)*(c + d*x)), x, S(8), e**S(2)*(e + f*x)**(S(1) + n)/(b*d*f**S(3)*(S(1) + n)) + (b*c + a*d)*e*(e + f*x)**(S(1) + n)/(b**S(2)*d**S(2)*f**S(2)*(S(1) + n)) + (b**S(2)*c**S(2) + a*b*c*d + a**S(2)*d**S(2))*(e + f*x)**(S(1) + n)/(b**S(3)*d**S(3)*f*(S(1) + n)) - S(2)*e*(e + f*x)**(S(2) + n)/(b*d*f**S(3)*(S(2) + n)) - (b*c + a*d)*(e + f*x)**(S(2) + n)/(b**S(2)*d**S(2)*f**S(2)*(S(2) + n)) + (e + f*x)**(S(3) + n)/(b*d*f**S(3)*(S(3) + n)) - a**S(4)*(e + f*x)**(S(1) + n)*hypergeom([S(1), S(1) + n], [S(2) + n], b*(e + f*x)/(b*e - a*f))/(b**S(3)*(b*c - a*d)*(b*e - a*f)*(S(1) + n)) + c**S(4)*(e + f*x)**(S(1) + n)*hypergeom([S(1), S(1) + n], [S(2) + n], d*(e + f*x)/(d*e - c*f))/(d**S(3)*(b*c - a*d)*(d*e - c*f)*(S(1) + n))],
        [(a + b*x)*(c + d*x)*(e + f*x)*(g + h*x), x, S(2), a*c*e*g*x + S(1)/S(2)*(b*c*e*g + a*(d*e*g + c*f*g + c*e*h))*x**S(2) + S(1)/S(3)*(b*(d*e*g + c*f*g + c*e*h) + a*(d*f*g + d*e*h + c*f*h))*x**S(3) + S(1)/S(4)*(a*d*f*h + b*(d*f*g + d*e*h + c*f*h))*x**S(4) + S(1)/S(5)*b*d*f*h*x**S(5)],
        [(a + b*x)*(c + d*x)*(e + f*x)/(g + h*x), x, S(2), (b*(d*g - c*h)*(f*g - e*h) - a*h*(d*f*g - d*e*h - c*f*h))*x/h**S(3) + S(1)/S(2)*(a*d*f*h - b*(d*f*g - d*e*h - c*f*h))*x**S(2)/h**S(2) + S(1)/S(3)*b*d*f*x**S(3)/h - (b*g - a*h)*(d*g - c*h)*(f*g - e*h)*log(g + h*x)/h**S(4)],
        [(a + b*x)**m*(c + d*x)*(e + f*x)*(g + h*x), x, S(2), (b*c - a*d)*(b*e - a*f)*(b*g - a*h)*(a + b*x)**(S(1) + m)/(b**S(4)*(S(1) + m)) + (S(3)*a**S(2)*d*f*h + b**S(2)*(d*e*g + c*f*g + c*e*h) - S(2)*a*b*(d*f*g + d*e*h + c*f*h))*(a + b*x)**(S(2) + m)/(b**S(4)*(S(2) + m)) - (S(3)*a*d*f*h - b*(d*f*g + d*e*h + c*f*h))*(a + b*x)**(S(3) + m)/(b**S(4)*(S(3) + m)) + d*f*h*(a + b*x)**(S(4) + m)/(b**S(4)*(S(4) + m))],
        [(c + d*x)**( - S(4) - m)*(e + f*x)**m*(g + h*x), x, S(3), - (d*g - c*h)*(c + d*x)**( - S(3) - m)*(e + f*x)**(S(1) + m)/(d*(d*e - c*f)*(S(3) + m)) + (c*f*h*(S(1) + m) + d*(S(2)*f*g - e*h*(S(3) + m)))*(c + d*x)**( - S(2) - m)*(e + f*x)**(S(1) + m)/(d*(d*e - c*f)**S(2)*(S(2) + m)*(S(3) + m)) - f*(c*f*h*(S(1) + m) + d*(S(2)*f*g - e*h*(S(3) + m)))*(c + d*x)**( - S(1) - m)*(e + f*x)**(S(1) + m)/(d*(d*e - c*f)**S(3)*(S(1) + m)*(S(2) + m)*(S(3) + m))],
    ]
    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True)
@XFAIL
def test_2():
    test = [
        [x**m*(e + f*x)**n/((a + b*x)*(c + d*x)), x, S(6), b*x**(S(1) + m)*(e + f*x)**n*AppellF1(S(1) + m, - n, S(1), S(2) + m, - f*x/e, - b*x/a)/(a*(b*c - a*d)*(S(1) + m)*(S(1) + f*x/e)**n) - d*x**(S(1) + m)*(e + f*x)**n*AppellF1(S(1) + m, - n, S(1), S(2) + m, - f*x/e, - d*x/c)/(c*(b*c - a*d)*(S(1) + m)*(S(1) + f*x/e)**n)],
        [(a + b*x)**m*(c + d*x)**n*(e + f*x)*(g + h*x), x, S(3), - (a + b*x)**(S(1) + m)*(c + d*x)**(S(1) + n)*(b*c*f*h*(S(2) + m) + a*d*f*h*(S(2) + n) - b*d*(f*g + e*h)*(S(3) + m + n) - b*d*f*h*(S(2) + m + n)*x)/(b**S(2)*d**S(2)*(S(2) + m + n)*(S(3) + m + n)) + (a**S(2)*d**S(2)*f*h*(S(1) + n)*(S(2) + n) + a*b*d*(S(1) + n)*(S(2)*c*f*h*(S(1) + m) - d*(f*g + e*h)*(S(3) + m + n)) + b**S(2)*(c**S(2)*f*h*(S(1) + m)*(S(2) + m) - c*d*(f*g + e*h)*(S(1) + m)*(S(3) + m + n) + d**S(2)*e*g*(S(2) + m + n)*(S(3) + m + n)))*(a + b*x)**(S(1) + m)*(c + d*x)**n*hypergeom([S(1) + m, - n], [S(2) + m], - d*(a + b*x)/(b*c - a*d))/(b**S(3)*d**S(2)*(S(1) + m)*(S(2) + m + n)*(S(3) + m + n)*(b*(c + d*x)/(b*c - a*d))**n)],
        [(a + b*x)**m*(A + B*x)*(c + d*x)**n*(e + f*x)**p, x, S(7), (A*b - a*B)*(a + b*x)**(S(1) + m)*(c + d*x)**n*(e + f*x)**p*AppellF1(S(1) + m, - n, - p, S(2) + m, - d*(a + b*x)/(b*c - a*d), - f*(a + b*x)/(b*e - a*f))/(b**S(2)*(S(1) + m)*(b*(c + d*x)/(b*c - a*d))**n*(b*(e + f*x)/(b*e - a*f))**p) + B*(a + b*x)**(S(2) + m)*(c + d*x)**n*(e + f*x)**p*AppellF1(S(2) + m, - n, - p, S(3) + m, - d*(a + b*x)/(b*c - a*d), - f*(a + b*x)/(b*e - a*f))/(b**S(2)*(S(2) + m)*(b*(c + d*x)/(b*c - a*d))**n*(b*(e + f*x)/(b*e - a*f))**p)],
        [(A + B*x)*(c + d*x)**n*(e + f*x)**p/(a + b*x), x, S(5), - (A*b - a*B)*(c + d*x)**(S(1) + n)*(e + f*x)**p*AppellF1(S(1) + n, S(1), - p, S(2) + n, b*(c + d*x)/(b*c - a*d), - f*(c + d*x)/(d*e - c*f))/(b*(b*c - a*d)*(S(1) + n)*(d*(e + f*x)/(d*e - c*f))**p) - B*(c + d*x)**(S(1) + n)*(e + f*x)**(S(1) + p)*hypergeom([S(1), S(2) + n + p], [S(2) + p], d*(e + f*x)/(d*e - c*f))/(b*(d*e - c*f)*(S(1) + p)), - (A*b - a*B)*(c + d*x)**(S(1) + n)*(e + f*x)**p*AppellF1(S(1) + n, - p, S(1), S(2) + n, - f*(c + d*x)/(d*e - c*f), b*(c + d*x)/(b*c - a*d))/(b*(b*c - a*d)*(S(1) + n)*(d*(e + f*x)/(d*e - c*f))**p) + B*(c + d*x)**(S(1) + n)*(e + f*x)**p*hypergeom([S(1) + n, - p], [S(2) + n], - f*(c + d*x)/(d*e - c*f))/(b*d*(S(1) + n)*(d*(e + f*x)/(d*e - c*f))**p)],
        [(c*i + d*i*x)/(sqrt(c + d*x)*sqrt(e + f*x)*sqrt(g + h*x)), x, S(3), S(2)*i*EllipticE(sqrt(h)*sqrt(e + f*x)/sqrt( - f*g + e*h), sqrt( - d*(f*g - e*h)/((d*e - c*f)*h)))*sqrt( - f*g + e*h)*sqrt(c + d*x)*sqrt(f*(g + h*x)/(f*g - e*h))/(f*sqrt(h)*sqrt( - f*(c + d*x)/(d*e - c*f))*sqrt(g + h*x))],
        [(a + b*x)**m*(c + d*x)**n*(e + f*x)**p, x, S(3), (a + b*x)**(S(1) + m)*(c + d*x)**n*(e + f*x)**p*AppellF1(S(1) + m, - n, - p, S(2) + m, - d*(a + b*x)/(b*c - a*d), - f*(a + b*x)/(b*e - a*f))/(b*(S(1) + m)*(b*(c + d*x)/(b*c - a*d))**n*(b*(e + f*x)/(b*e - a*f))**p)],
        [(a + b*x)**m*(c + d*x)**n*(e + f*x)**p/(g + h*x), x, S(0), Integral((a + b*x)**m*(c + d*x)**n*(e + f*x)**p/(g + h*x), x)],
        [x**S(3)*(S(1) + a*x)/(sqrt(a*x)*sqrt(S(1) - a*x)), x, S(8), - S(75)/S(128)*arcsin(S(1) - S(2)*a*x)/a**S(4) - S(25)/S(32)*(a*x)**(S(3)/S(2))*sqrt(S(1) - a*x)/a**S(4) - S(5)/S(8)*(a*x)**(S(5)/S(2))*sqrt(S(1) - a*x)/a**S(4) - S(1)/S(4)*(a*x)**(S(7)/S(2))*sqrt(S(1) - a*x)/a**S(4) - S(75)/S(64)*sqrt(a*x)*sqrt(S(1) - a*x)/a**S(4)],
    ]
    for index in test:
        r = rubi_integrate(index[0], index[1])
        if len(index) == 5:
            assert rubi_test(r, index[1], index[3], expand=True, _diff=True) or rubi_test(r, index[1], index[4], expand=True, _diff=True)
        else:
            assert rubi_test(r, index[1], index[3], expand=True, _diff=True)

@XFAIL
def test_numerical():
    test = [
        #[S(1)/((a + b*x)*sqrt(c + d*x)*sqrt(e + f*x)*sqrt(g + h*x)), x, S(1), - S(2)*EllipticPi(sqrt( - f/(d*e - c*f))*sqrt(c + d*x), - b*(d*e - c*f)/((b*c - a*d)*f), sqrt((d*e - c*f)*h/(f*(d*g - c*h))))*sqrt(d*(e + f*x)/(d*e - c*f))*sqrt(d*(g + h*x)/(d*g - c*h))/((b*c - a*d)*sqrt( - f/(d*e - c*f))*sqrt(e + f*x)*sqrt(g + h*x))],
        #[S(1)/(sqrt(a + b*x)*sqrt(c + d*x)*sqrt(e + f*x)*sqrt(g + h*x)), x, S(2), - S(2)*(a + b*x)*sqrt(cos(arctan(sqrt(b*e - a*f)*sqrt(g + h*x)/(sqrt(f*g - e*h)*sqrt(a + b*x))))**S(2))/cos(arctan(sqrt(b*e - a*f)*sqrt(g + h*x)/(sqrt(f*g - e*h)*sqrt(a + b*x))))*EllipticF(sin(arctan(sqrt(b*e - a*f)*sqrt(g + h*x)/(sqrt(f*g - e*h)*sqrt(a + b*x)))), sqrt((d*e - c*f)*(b*g - a*h)/((b*e - a*f)*(d*g - c*h))))*sqrt(f*g - e*h)*sqrt((b*g - a*h)*(c + d*x)/((d*g - c*h)*(a + b*x)))*sqrt((b*g - a*h)*(e + f*x)/((f*g - e*h)*(a + b*x)))*sqrt(S(1) + (b*c - a*d)*(g + h*x)/((d*g - c*h)*(a + b*x)))/((b*g - a*h)*sqrt(b*e - a*f)*sqrt(c + d*x)*sqrt(e + f*x)*sqrt((S(1) + (b*c - a*d)*(g + h*x)/((d*g - c*h)*(a + b*x)))/(S(1) + (b*e - a*f)*(g + h*x)/((f*g - e*h)*(a + b*x))))*sqrt(S(1) + (b*e - a*f)*(g + h*x)/((f*g - e*h)*(a + b*x))))],
    ]

    for i in test:
        r = rubi_integrate(i[0], i[1])
        if len(i) == 5:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True, _numerical=True) or rubi_test(r, i[1], i[4], expand=True, _diff=True, _numerical=True)
        else:
            assert rubi_test(r, i[1], i[3], expand=True, _diff=True, _numerical=True)
