"""A module for solving all kinds of equations.

    Examples
    ========

    >>> from sympy.solvers import solve
    >>> from sympy.abc import x
    >>> solve(x**5+5*x**4+10*x**3+10*x**2+5*x+1,x)
    [-1]
"""
from .solvers import solve, solve_linear_system, solve_linear_system_LU, \
    solve_undetermined_coeffs, nsolve, solve_linear, checksol, \
    det_quick, inv_quick, check_assumptions, failing_assumptions

from .diophantine import diophantine

from .recurr import rsolve, rsolve_poly, rsolve_ratio, rsolve_hyper

from .ode import checkodesol, classify_ode, dsolve, \
    homogeneous_order

from .polysys import solve_poly_system, solve_triangulated

from .pde import pde_separate, pde_separate_add, pde_separate_mul, \
    pdsolve, classify_pde, checkpdesol

from .deutils import ode_order

from .inequalities import reduce_inequalities, reduce_abs_inequality, \
    reduce_abs_inequalities, solve_poly_inequality, solve_rational_inequalities, solve_univariate_inequality

from .decompogen import decompogen

from .solveset import solveset, linsolve, linear_eq_to_matrix, nonlinsolve, substitution

# This is here instead of sympy/sets/__init__.py to avoid circular import issues
from ..core.singleton import S
Complexes = S.Complexes
del S
