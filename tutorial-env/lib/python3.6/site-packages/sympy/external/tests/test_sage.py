# This testfile tests SymPy <-> Sage compatibility
#
# Execute this test inside Sage, e.g. with:
# sage -python bin/test sympy/external/tests/test_sage.py
#
# This file can be tested by Sage itself by:
# sage -t sympy/external/tests/test_sage.py
# and if all tests pass, it should be copied (verbatim) to Sage, so that it is
# automatically doctested by Sage.  Note that this second method imports the
# version of SymPy in Sage, whereas the -python method imports the local version
# of SymPy (both use the local version of the tests, however).
#
# Don't test any SymPy features here. Just pure interaction with Sage.
# Always write regular SymPy tests for anything, that can be tested in pure
# Python (without Sage). Here we test everything, that a user may need when
# using SymPy with Sage.

import os
import re
import sys

from sympy.external import import_module

sage = import_module('sage.all', __import__kwargs={'fromlist': ['all']})
if not sage:
    #bin/test will not execute any tests now
    disabled = True

import sympy

from sympy.utilities.pytest import XFAIL

def is_trivially_equal(lhs, rhs):
    """
    True if lhs and rhs are trivially equal.

    Use this for comparison of Sage expressions. Otherwise you
    may start the whole proof machinery which may not exist at
    the time of testing.
    """
    assert (lhs - rhs).is_trivial_zero()

def check_expression(expr, var_symbols, only_from_sympy=False):
    """
    Does eval(expr) both in Sage and SymPy and does other checks.
    """

    # evaluate the expression in the context of Sage:
    if var_symbols:
        sage.var(var_symbols)
    a = globals().copy()
    # safety checks...
    a.update(sage.__dict__)
    assert "sin" in a
    is_different = False
    try:
        e_sage = eval(expr, a)
        assert not isinstance(e_sage, sympy.Basic)
    except (NameError, TypeError):
        is_different = True
        pass

    # evaluate the expression in the context of SymPy:
    if var_symbols:
        sympy_vars = sympy.var(var_symbols)
    b = globals().copy()
    b.update(sympy.__dict__)
    assert "sin" in b
    b.update(sympy.__dict__)
    e_sympy = eval(expr, b)
    assert isinstance(e_sympy, sympy.Basic)

    # Sympy func may have specific _sage_ method
    if is_different:
        _sage_method = getattr(e_sympy.func, "_sage_")
        e_sage = _sage_method(sympy.S(e_sympy))

    # Do the actual checks:
    if not only_from_sympy:
        assert sympy.S(e_sage) == e_sympy
    is_trivially_equal(e_sage, sage.SR(e_sympy))


def test_basics():
    check_expression("x", "x")
    check_expression("x**2", "x")
    check_expression("x**2+y**3", "x y")
    check_expression("1/(x+y)**2-x**3/4", "x y")


def test_complex():
    check_expression("I", "")
    check_expression("23+I*4", "x")


@XFAIL
def test_complex_fail():
    # Sage doesn't properly implement _sympy_ on I
    check_expression("I*y", "y")
    check_expression("x+I*y", "x y")


def test_integer():
    check_expression("4*x", "x")
    check_expression("-4*x", "x")


def test_real():
    check_expression("1.123*x", "x")
    check_expression("-18.22*x", "x")


def test_E():
    assert sympy.sympify(sage.e) == sympy.E
    is_trivially_equal(sage.e, sage.SR(sympy.E))


def test_pi():
    assert sympy.sympify(sage.pi) == sympy.pi
    is_trivially_equal(sage.pi, sage.SR(sympy.pi))


def test_euler_gamma():
    assert sympy.sympify(sage.euler_gamma) == sympy.EulerGamma
    is_trivially_equal(sage.euler_gamma, sage.SR(sympy.EulerGamma))


def test_oo():
    assert sympy.sympify(sage.oo) == sympy.oo
    assert sage.oo == sage.SR(sympy.oo).pyobject()
    assert sympy.sympify(-sage.oo) == -sympy.oo
    assert -sage.oo == sage.SR(-sympy.oo).pyobject()
    #assert sympy.sympify(sage.UnsignedInfinityRing.gen()) == sympy.zoo
    #assert sage.UnsignedInfinityRing.gen() == sage.SR(sympy.zoo)

def test_NaN():
    assert sympy.sympify(sage.NaN) == sympy.nan
    is_trivially_equal(sage.NaN, sage.SR(sympy.nan))


def test_Catalan():
    assert sympy.sympify(sage.catalan) == sympy.Catalan
    is_trivially_equal(sage.catalan, sage.SR(sympy.Catalan))


def test_GoldenRation():
    assert sympy.sympify(sage.golden_ratio) == sympy.GoldenRatio
    is_trivially_equal(sage.golden_ratio, sage.SR(sympy.GoldenRatio))


def test_functions():
    # Test at least one Function without own _sage_ method
    assert not "_sage_" in sympy.factorial.__dict__
    check_expression("factorial(x)", "x")
    check_expression("sin(x)", "x")
    check_expression("cos(x)", "x")
    check_expression("tan(x)", "x")
    check_expression("cot(x)", "x")
    check_expression("asin(x)", "x")
    check_expression("acos(x)", "x")
    check_expression("atan(x)", "x")
    check_expression("atan2(y, x)", "x, y")
    check_expression("acot(x)", "x")
    check_expression("sinh(x)", "x")
    check_expression("cosh(x)", "x")
    check_expression("tanh(x)", "x")
    check_expression("coth(x)", "x")
    check_expression("asinh(x)", "x")
    check_expression("acosh(x)", "x")
    check_expression("atanh(x)", "x")
    check_expression("acoth(x)", "x")
    check_expression("exp(x)", "x")
    check_expression("gamma(x)", "x")
    check_expression("log(x)", "x")
    check_expression("re(x)", "x")
    check_expression("im(x)", "x")
    check_expression("sign(x)", "x")
    check_expression("abs(x)", "x")
    check_expression("arg(x)", "x")
    check_expression("conjugate(x)", "x")

    # The following tests differently named functions
    check_expression("besselj(y, x)", "x, y")
    check_expression("bessely(y, x)", "x, y")
    check_expression("besseli(y, x)", "x, y")
    check_expression("besselk(y, x)", "x, y")
    check_expression("DiracDelta(x)", "x")
    check_expression("KroneckerDelta(x, y)", "x, y")
    check_expression("expint(y, x)", "x, y")
    check_expression("Si(x)", "x")
    check_expression("Ci(x)", "x")
    check_expression("Shi(x)", "x")
    check_expression("Chi(x)", "x")
    check_expression("loggamma(x)", "x")
    check_expression("Ynm(n,m,x,y)", "n, m, x, y")
    check_expression("hyper((n,m),(m,n),x)", "n, m, x")
    check_expression("uppergamma(y, x)", "x, y")

def test_issue_4023():
    sage.var("a x")
    log = sage.log
    i = sympy.integrate(log(x)/a, (x, a, a + 1))
    i2 = sympy.simplify(i)
    s = sage.SR(i2)
    is_trivially_equal(s, -log(a) + log(a + 1) + log(a + 1)/a - 1/a)

def test_integral():
    #test Sympy-->Sage
    check_expression("Integral(x, (x,))", "x", only_from_sympy=True)
    check_expression("Integral(x, (x, 0, 1))", "x", only_from_sympy=True)
    check_expression("Integral(x*y, (x,), (y, ))", "x,y", only_from_sympy=True)
    check_expression("Integral(x*y, (x,), (y, 0, 1))", "x,y", only_from_sympy=True)
    check_expression("Integral(x*y, (x, 0, 1), (y,))", "x,y", only_from_sympy=True)
    check_expression("Integral(x*y, (x, 0, 1), (y, 0, 1))", "x,y", only_from_sympy=True)
    check_expression("Integral(x*y*z, (x, 0, 1), (y, 0, 1), (z, 0, 1))", "x,y,z", only_from_sympy=True)

@XFAIL
def test_integral_failing():
    # Note: sage may attempt to turn this into Integral(x, (x, x, 0))
    check_expression("Integral(x, (x, 0))", "x", only_from_sympy=True)
    check_expression("Integral(x*y, (x,), (y, 0))", "x,y", only_from_sympy=True)
    check_expression("Integral(x*y, (x, 0, 1), (y, 0))", "x,y", only_from_sympy=True)

def test_undefined_function():
    f = sympy.Function('f')
    sf = sage.function('f')
    x = sympy.symbols('x')
    sx = sage.var('x')
    is_trivially_equal(sf(sx), f(x)._sage_())
    #assert bool(f == sympy.sympify(sf))

def test_abstract_function():
    from sage.symbolic.expression import Expression
    x,y = sympy.symbols('x y')
    f = sympy.Function('f')
    expr =  f(x,y)
    sexpr = expr._sage_()
    assert isinstance(sexpr,Expression), "converted expression %r is not sage expression" % sexpr
    # This test has to be uncommented in the future: it depends on the sage ticket #22802 (https://trac.sagemath.org/ticket/22802)
    # invexpr = sexpr._sympy_()
    # assert invexpr == expr, "inverse coversion %r is not correct " % invexpr



# This string contains Sage doctests, that execute all the functions above.
# When you add a new function, please add it here as well.
"""

TESTS::

    sage: from sympy.external.tests.test_sage import *
    sage: test_basics()
    sage: test_basics()
    sage: test_complex()
    sage: test_integer()
    sage: test_real()
    sage: test_E()
    sage: test_pi()
    sage: test_euler_gamma()
    sage: test_oo()
    sage: test_NaN()
    sage: test_Catalan()
    sage: test_GoldenRation()
    sage: test_functions()
    sage: test_issue_4023()
    sage: test_integral()
    sage: test_undefined_function()
    sage: test_abstract_function()

Sage has no symbolic Lucas function at the moment::

    sage: check_expression("lucas(x)", "x")
    Traceback (most recent call last):
    ...
    AttributeError...

"""
