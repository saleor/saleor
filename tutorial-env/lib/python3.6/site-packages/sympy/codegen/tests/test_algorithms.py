from __future__ import (absolute_import, print_function)

import sys

import sympy as sp
from sympy.core.compatibility import exec_
from sympy.codegen.ast import Assignment
from sympy.codegen.algorithms import newtons_method, newtons_method_function
from sympy.codegen.fnodes import bind_C
from sympy.codegen.futils import render_as_module as f_module
from sympy.codegen.pyutils import render_as_module as py_module
from sympy.external import import_module
from sympy.printing.ccode import ccode
from sympy.utilities._compilation import compile_link_import_strings, has_c, has_fortran
from sympy.utilities._compilation.util import TemporaryDirectory, may_xfail
from sympy.utilities.pytest import skip, USE_PYTEST, raises

cython = import_module('cython')
wurlitzer = import_module('wurlitzer')

def test_newtons_method():
    x, dx, atol = sp.symbols('x dx atol')
    expr = sp.cos(x) - x**3
    algo = newtons_method(expr, x, atol, dx)
    assert algo.has(Assignment(dx, -expr/expr.diff(x)))


@may_xfail
def test_newtons_method_function__ccode():
    x = sp.Symbol('x', real=True)
    expr = sp.cos(x) - x**3
    func = newtons_method_function(expr, x)

    if not cython:
        skip("cython not installed.")
    if not has_c():
        skip("No C compiler found.")

    compile_kw = dict(std='c99')
    with TemporaryDirectory() as folder:
        mod, info = compile_link_import_strings([
            ('newton.c', ('#include <math.h>\n'
                          '#include <stdio.h>\n') + ccode(func)),
            ('_newton.pyx', ("cdef extern double newton(double)\n"
                             "def py_newton(x):\n"
                             "    return newton(x)\n"))
        ], build_dir=folder, compile_kwargs=compile_kw)
        assert abs(mod.py_newton(0.5) - 0.865474033102) < 1e-12


@may_xfail
def test_newtons_method_function__fcode():
    x = sp.Symbol('x', real=True)
    expr = sp.cos(x) - x**3
    func = newtons_method_function(expr, x, attrs=[bind_C(name='newton')])

    if not cython:
        skip("cython not installed.")
    if not has_fortran():
        skip("No Fortran compiler found.")

    f_mod = f_module([func], 'mod_newton')
    with TemporaryDirectory() as folder:
        mod, info = compile_link_import_strings([
            ('newton.f90', f_mod),
            ('_newton.pyx', ("cdef extern double newton(double*)\n"
                             "def py_newton(double x):\n"
                             "    return newton(&x)\n"))
        ], build_dir=folder)
        assert abs(mod.py_newton(0.5) - 0.865474033102) < 1e-12


def test_newtons_method_function__pycode():
    x = sp.Symbol('x', real=True)
    expr = sp.cos(x) - x**3
    func = newtons_method_function(expr, x)
    py_mod = py_module(func)
    namespace = {}
    exec_(py_mod, namespace, namespace)
    res = eval('newton(0.5)', namespace)
    assert abs(res - 0.865474033102) < 1e-12


@may_xfail
def test_newtons_method_function__ccode_parameters():
    args = x, A, k, p = sp.symbols('x A k p')
    expr = A*sp.cos(k*x) - p*x**3
    raises(ValueError, lambda: newtons_method_function(expr, x))
    use_wurlitzer = wurlitzer

    func = newtons_method_function(expr, x, args, debug=use_wurlitzer)

    if not has_c():
        skip("No C compiler found.")
    if not cython:
        skip("cython not installed.")

    compile_kw = dict(std='c99')
    with TemporaryDirectory() as folder:
        mod, info = compile_link_import_strings([
            ('newton_par.c', ('#include <math.h>\n'
                          '#include <stdio.h>\n') + ccode(func)),
            ('_newton_par.pyx', ("cdef extern double newton(double, double, double, double)\n"
                             "def py_newton(x, A=1, k=1, p=1):\n"
                             "    return newton(x, A, k, p)\n"))
        ], compile_kwargs=compile_kw, build_dir=folder)

        if use_wurlitzer:
            with wurlitzer.pipes() as (out, err):
                result = mod.py_newton(0.5)
        else:
            result = mod.py_newton(0.5)

        assert abs(result - 0.865474033102) < 1e-12

        if not use_wurlitzer:
            skip("C-level output only tested when package 'wurlitzer' is available.")

        out, err = out.read(), err.read()
        assert err == ''
        assert out == """\
x=         0.5 d_x=     0.61214
x=      1.1121 d_x=    -0.20247
x=     0.90967 d_x=   -0.042409
x=     0.86726 d_x=  -0.0017867
x=     0.86548 d_x= -3.1022e-06
x=     0.86547 d_x= -9.3421e-12
x=     0.86547 d_x=  3.6902e-17
"""  # try to run tests with LC_ALL=C if this assertion fails
