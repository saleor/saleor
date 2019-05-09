import sys
from sympy.external import import_module
matchpy = import_module("matchpy")

if not matchpy:
    #bin/test will not execute any tests now
    disabled = True

if sys.version_info[:2] < (3, 6):
    disabled = True

from sympy.core.symbol import symbols, Symbol
from sympy.functions import log
from sympy import (sqrt, simplify, S, atanh, hyper, I, atan, pi, Sum, cos, sin,
    log, atan)
from sympy.integrals.rubi.utility_function import rubi_test
from sympy.utilities.pytest import SKIP
# from sympy.integrals.rubi.rubi import rubi_integrate

a, b, c, d, e, f, x, m, n, p, k = symbols('a b c d e f x m n p k', real=True, imaginary=False)

@SKIP
def test_rubi_integrate():
    assert rubi_integrate(x, x) == x**2/2
    assert rubi_integrate(x**a, x) == x**(a + S(1))/(a + S(1))
    assert rubi_integrate(S(1)/x, x) == log(x)
    assert rubi_integrate(a*x, x) == a*(S(1)/S(2))*x**S(2)
    assert rubi_integrate(1/(x**2*(a + b*x)**2), x) == -b/(a**2*(a + b*x)) - 1/(a**2*x) - 2*b*log(x)/a**3 + 2*b*log(a + b*x)/a**3
    assert rubi_integrate(x**6/(a + b*x)**2, x) == (-a**6/(b**7*(a + b*x)) - S(6)*a**5*log(a + b*x)/b**7 + 5*a**4*x/b**6 - S(2)*a**3*x**2/b**5 + a**2*x**3/b**4 - a*x**4/(S(2)*b**3) + x**5/(S(5)*b**2))
    assert rubi_integrate(1/(x**2*(a + b*x)**2), x) == -b/(a**2*(a + b*x)) - 1/(a**2*x) - 2*b*log(x)/a**3 + 2*b*log(a + b*x)/a**3
    assert rubi_integrate(a + S(1)/x, x) == a*x + log(x)
    assert rubi_integrate((a + b*x)**2/x**3, x) == -a**2/(2*x**2) - 2*a*b/x + b**2*log(x)
    assert rubi_integrate(a**3*x, x) == S(1)/S(2)*a**3*x**2
    assert rubi_integrate((a + b*x)**3/x**3, x) == -a**3/(2*x**2) - 3*a**2*b/x + 3*a*b**2*log(x) + b**3*x
    assert rubi_integrate(x**3*(a + b*x), x) == a*x**4/4 + b*x**5/5
    assert rubi_integrate((b*x)**m*(d*x + 2)**n, x) == 2**n*(b*x)**(m + 1)*hyper((-n, m + 1), (m + 2,), -d*x/2)/(b*(m + 1))
    assert rubi_test(rubi_integrate(1/(1 + x**5), x), x, log(x + S(1))/S(5) + S(2)*Sum(-log((S(2)*x - S(2)*cos(pi*(S(2)*k/S(5) + S(-1)/5)))**S(2) - S(4)*sin(S(2)*pi*k/S(5) + S(3)*pi/S(10))**S(2) + S(4))*cos(pi*(S(2)*k/S(5) + S(-1)/5))/S(2) - (-S(2)*cos(pi*(S(2)*k/S(5) + S(-1)/5))**S(2) + S(2))*atan((-x/cos(pi*(S(2)*k/S(5) + S(-1)/5)) + S(1))/sqrt(-(cos(S(2)*pi*k/S(5) - pi/S(5)) + S(-1))*(cos(S(2)*pi*k/S(5) - pi/S(5)) + S(1))/cos(S(2)*pi*k/S(5) - pi/S(5))**S(2)))/(S(2)*sqrt(-(cos(S(2)*pi*k/S(5) - pi/S(5)) + S(-1))*(cos(S(2)*pi*k/S(5) - pi/S(5)) + S(1))/cos(S(2)*pi*k/S(5) - pi/S(5))**S(2))*cos(pi*(S(2)*k/S(5) + S(-1)/5))), (k, S(1), S(2)))/S(5), _numerical=True)
