# -*- coding: utf-8 -*-

"""
Several methods to simplify expressions involving unit objects.
"""

from __future__ import division

from sympy.utilities.exceptions import SymPyDeprecationWarning

from sympy import Add, Function, Mul, Pow, Rational, Tuple, sympify
from sympy.core.compatibility import reduce, Iterable, ordered
from sympy.physics.units.dimensions import Dimension, dimsys_default
from sympy.physics.units.quantities import Quantity
from sympy.physics.units.prefixes import Prefix
from sympy.utilities.iterables import sift


def dim_simplify(expr):
    """
    NOTE: this function could be deprecated in the future.

    Simplify expression by recursively evaluating the dimension arguments.

    This function proceeds to a very rough dimensional analysis. It tries to
    simplify expression with dimensions, and it deletes all what multiplies a
    dimension without being a dimension. This is necessary to avoid strange
    behavior when Add(L, L) be transformed into Mul(2, L).
    """
    SymPyDeprecationWarning(
        deprecated_since_version="1.2",
        feature="dimensional simplification function",
        issue=13336,
        useinstead="don't use",
    ).warn()
    _, expr = Quantity._collect_factor_and_dimension(expr)
    return expr


def _get_conversion_matrix_for_expr(expr, target_units):
    from sympy import Matrix

    expr_dim = Dimension(Quantity.get_dimensional_expr(expr))
    dim_dependencies = dimsys_default.get_dimensional_dependencies(expr_dim, mark_dimensionless=True)
    target_dims = [Dimension(Quantity.get_dimensional_expr(x)) for x in target_units]
    canon_dim_units = {i for x in target_dims for i in dimsys_default.get_dimensional_dependencies(x, mark_dimensionless=True)}
    canon_expr_units = {i for i in dim_dependencies}

    if not canon_expr_units.issubset(canon_dim_units):
        return None

    canon_dim_units = sorted(canon_dim_units)

    camat = Matrix([[dimsys_default.get_dimensional_dependencies(i, mark_dimensionless=True).get(j, 0)  for i in target_dims] for j in canon_dim_units])
    exprmat = Matrix([dim_dependencies.get(k, 0) for k in canon_dim_units])

    res_exponents = camat.solve_least_squares(exprmat, method=None)
    return res_exponents


def convert_to(expr, target_units):
    """
    Convert ``expr`` to the same expression with all of its units and quantities
    represented as factors of ``target_units``, whenever the dimension is compatible.

    ``target_units`` may be a single unit/quantity, or a collection of
    units/quantities.

    Examples
    ========

    >>> from sympy.physics.units import speed_of_light, meter, gram, second, day
    >>> from sympy.physics.units import mile, newton, kilogram, atomic_mass_constant
    >>> from sympy.physics.units import kilometer, centimeter
    >>> from sympy.physics.units import convert_to
    >>> convert_to(mile, kilometer)
    25146*kilometer/15625
    >>> convert_to(mile, kilometer).n()
    1.609344*kilometer
    >>> convert_to(speed_of_light, meter/second)
    299792458*meter/second
    >>> convert_to(day, second)
    86400*second
    >>> 3*newton
    3*newton
    >>> convert_to(3*newton, kilogram*meter/second**2)
    3*kilogram*meter/second**2
    >>> convert_to(atomic_mass_constant, gram)
    1.66053904e-24*gram

    Conversion to multiple units:

    >>> convert_to(speed_of_light, [meter, second])
    299792458*meter/second
    >>> convert_to(3*newton, [centimeter, gram, second])
    300000*centimeter*gram/second**2

    Conversion to Planck units:

    >>> from sympy.physics.units import gravitational_constant, hbar
    >>> convert_to(atomic_mass_constant, [gravitational_constant, speed_of_light, hbar]).n()
    7.62950196312651e-20*gravitational_constant**(-0.5)*hbar**0.5*speed_of_light**0.5

    """
    if not isinstance(target_units, (Iterable, Tuple)):
        target_units = [target_units]

    if isinstance(expr, Add):
        return Add.fromiter(convert_to(i, target_units) for i in expr.args)

    expr = sympify(expr)

    if not isinstance(expr, Quantity) and expr.has(Quantity):
        expr = expr.replace(lambda x: isinstance(x, Quantity), lambda x: x.convert_to(target_units))

    def get_total_scale_factor(expr):
        if isinstance(expr, Mul):
            return reduce(lambda x, y: x * y, [get_total_scale_factor(i) for i in expr.args])
        elif isinstance(expr, Pow):
            return get_total_scale_factor(expr.base) ** expr.exp
        elif isinstance(expr, Quantity):
            return expr.scale_factor
        return expr

    depmat = _get_conversion_matrix_for_expr(expr, target_units)
    if depmat is None:
        return expr

    expr_scale_factor = get_total_scale_factor(expr)
    return expr_scale_factor * Mul.fromiter((1/get_total_scale_factor(u) * u) ** p for u, p in zip(target_units, depmat))


def quantity_simplify(expr):
    """Return an equivalent expression in which prefixes are replaced
    with numerical values and all units of a given dimension are the
    unified in a canonical manner.

    Examples
    ========

    >>> from sympy.physics.units.util import quantity_simplify
    >>> from sympy.physics.units.prefixes import kilo
    >>> from sympy.physics.units import foot, inch
    >>> quantity_simplify(kilo*foot*inch)
    250*foot**2/3
    >>> quantity_simplify(foot - 6*inch)
    foot/2
    """

    if expr.is_Atom or not expr.has(Prefix, Quantity):
        return expr

    # replace all prefixes with numerical values
    p = expr.atoms(Prefix)
    expr = expr.xreplace({p: p.scale_factor for p in p})

    # replace all quantities of given dimension with a canonical
    # quantity, chosen from those in the expression
    d = sift(expr.atoms(Quantity), lambda i: i.dimension)
    for k in d:
        if len(d[k]) == 1:
            continue
        v = list(ordered(d[k]))
        ref = v[0]/v[0].scale_factor
        expr = expr.xreplace({vi: ref*vi.scale_factor for vi in v[1:]})

    return expr


def check_dimensions(expr):
    """Return expr if there are not unitless values added to
    dimensional quantities, else raise a ValueError."""
    from sympy.solvers.solveset import _term_factors
    # the case of adding a number to a dimensional quantity
    # is ignored for the sake of SymPy core routines, so this
    # function will raise an error now if such an addend is
    # found.
    # Also, when doing substitutions, multiplicative constants
    # might be introduced, so remove those now
    adds = expr.atoms(Add)
    DIM_OF = dimsys_default.get_dimensional_dependencies
    for a in adds:
        deset = set()
        for ai in a.args:
            if ai.is_number:
                deset.add(())
                continue
            dims = []
            skip = False
            for i in Mul.make_args(ai):
                if i.has(Quantity):
                    i = Dimension(Quantity.get_dimensional_expr(i))
                if i.has(Dimension):
                    dims.extend(DIM_OF(i).items())
                elif i.free_symbols:
                    skip = True
                    break
            if not skip:
                deset.add(tuple(sorted(dims)))
                if len(deset) > 1:
                    raise ValueError(
                        "addends have incompatible dimensions")

    # clear multiplicative constants on Dimensions which may be
    # left after substitution
    reps = {}
    for m in expr.atoms(Mul):
        if any(isinstance(i, Dimension) for i in m.args):
            reps[m] = m.func(*[
                i for i in m.args if not i.is_number])

    return expr.xreplace(reps)
