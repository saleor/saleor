"""Functions for reordering operator expressions."""

import warnings

from sympy import Add, Mul, Pow, Integer
from sympy.core.compatibility import range
from sympy.physics.quantum import Operator, Commutator, AntiCommutator
from sympy.physics.quantum.boson import BosonOp
from sympy.physics.quantum.fermion import FermionOp

__all__ = [
    'normal_order',
    'normal_ordered_form'
]


def _expand_powers(factors):
    """
    Helper function for normal_ordered_form and normal_order: Expand a
    power expression to a multiplication expression so that that the
    expression can be handled by the normal ordering functions.
    """

    new_factors = []
    for factor in factors.args:
        if (isinstance(factor, Pow)
                and isinstance(factor.args[1], Integer)
                and factor.args[1] > 0):
            for n in range(factor.args[1]):
                new_factors.append(factor.args[0])
        else:
            new_factors.append(factor)

    return new_factors


def _normal_ordered_form_factor(product, independent=False, recursive_limit=10,
                                _recursive_depth=0):
    """
    Helper function for normal_ordered_form_factor: Write multiplication
    expression with bosonic or fermionic operators on normally ordered form,
    using the bosonic and fermionic commutation relations. The resulting
    operator expression is equivalent to the argument, but will in general be
    a sum of operator products instead of a simple product.
    """

    factors = _expand_powers(product)

    new_factors = []
    n = 0
    while n < len(factors) - 1:

        if isinstance(factors[n], BosonOp):
            # boson
            if not isinstance(factors[n + 1], BosonOp):
                new_factors.append(factors[n])

            elif factors[n].is_annihilation == factors[n + 1].is_annihilation:
                if (independent and
                        str(factors[n].name) > str(factors[n + 1].name)):
                    new_factors.append(factors[n + 1])
                    new_factors.append(factors[n])
                    n += 1
                else:
                    new_factors.append(factors[n])

            elif not factors[n].is_annihilation:
                new_factors.append(factors[n])

            else:
                if factors[n + 1].is_annihilation:
                    new_factors.append(factors[n])
                else:
                    if factors[n].args[0] != factors[n + 1].args[0]:
                        if independent:
                            c = 0
                        else:
                            c = Commutator(factors[n], factors[n + 1])
                        new_factors.append(factors[n + 1] * factors[n] + c)
                    else:
                        c = Commutator(factors[n], factors[n + 1])
                        new_factors.append(
                            factors[n + 1] * factors[n] + c.doit())
                    n += 1

        elif isinstance(factors[n], FermionOp):
            # fermion
            if not isinstance(factors[n + 1], FermionOp):
                new_factors.append(factors[n])

            elif factors[n].is_annihilation == factors[n + 1].is_annihilation:
                if (independent and
                        str(factors[n].name) > str(factors[n + 1].name)):
                    new_factors.append(factors[n + 1])
                    new_factors.append(factors[n])
                    n += 1
                else:
                    new_factors.append(factors[n])

            elif not factors[n].is_annihilation:
                new_factors.append(factors[n])

            else:
                if factors[n + 1].is_annihilation:
                    new_factors.append(factors[n])
                else:
                    if factors[n].args[0] != factors[n + 1].args[0]:
                        if independent:
                            c = 0
                        else:
                            c = AntiCommutator(factors[n], factors[n + 1])
                        new_factors.append(-factors[n + 1] * factors[n] + c)
                    else:
                        c = AntiCommutator(factors[n], factors[n + 1])
                        new_factors.append(
                            -factors[n + 1] * factors[n] + c.doit())
                    n += 1

        elif isinstance(factors[n], Operator):

            if isinstance(factors[n + 1], (BosonOp, FermionOp)):
                new_factors.append(factors[n + 1])
                new_factors.append(factors[n])
                n += 1
            else:
                new_factors.append(factors[n])

        else:
            new_factors.append(factors[n])

        n += 1

    if n == len(factors) - 1:
        new_factors.append(factors[-1])

    if new_factors == factors:
        return product
    else:
        expr = Mul(*new_factors).expand()
        return normal_ordered_form(expr,
                                   recursive_limit=recursive_limit,
                                   _recursive_depth=_recursive_depth + 1,
                                   independent=independent)


def _normal_ordered_form_terms(expr, independent=False, recursive_limit=10,
                               _recursive_depth=0):
    """
    Helper function for normal_ordered_form: loop through each term in an
    addition expression and call _normal_ordered_form_factor to perform the
    factor to an normally ordered expression.
    """

    new_terms = []
    for term in expr.args:
        if isinstance(term, Mul):
            new_term = _normal_ordered_form_factor(
                term, recursive_limit=recursive_limit,
                _recursive_depth=_recursive_depth, independent=independent)
            new_terms.append(new_term)
        else:
            new_terms.append(term)

    return Add(*new_terms)


def normal_ordered_form(expr, independent=False, recursive_limit=10,
                        _recursive_depth=0):
    """Write an expression with bosonic or fermionic operators on normal
    ordered form, where each term is normally ordered. Note that this
    normal ordered form is equivalent to the original expression.

    Parameters
    ==========

    expr : expression
        The expression write on normal ordered form.

    recursive_limit : int (default 10)
        The number of allowed recursive applications of the function.

    Examples
    ========

    >>> from sympy.physics.quantum import Dagger
    >>> from sympy.physics.quantum.boson import BosonOp
    >>> from sympy.physics.quantum.operatorordering import normal_ordered_form
    >>> a = BosonOp("a")
    >>> normal_ordered_form(a * Dagger(a))
    1 + Dagger(a)*a
    """

    if _recursive_depth > recursive_limit:
        warnings.warn("Too many recursions, aborting")
        return expr

    if isinstance(expr, Add):
        return _normal_ordered_form_terms(expr,
                                          recursive_limit=recursive_limit,
                                          _recursive_depth=_recursive_depth,
                                          independent=independent)
    elif isinstance(expr, Mul):
        return _normal_ordered_form_factor(expr,
                                           recursive_limit=recursive_limit,
                                           _recursive_depth=_recursive_depth,
                                           independent=independent)
    else:
        return expr


def _normal_order_factor(product, recursive_limit=10, _recursive_depth=0):
    """
    Helper function for normal_order: Normal order a multiplication expression
    with bosonic or fermionic operators. In general the resulting operator
    expression will not be equivalent to original product.
    """

    factors = _expand_powers(product)

    n = 0
    new_factors = []
    while n < len(factors) - 1:

        if (isinstance(factors[n], BosonOp) and
                factors[n].is_annihilation):
            # boson
            if not isinstance(factors[n + 1], BosonOp):
                new_factors.append(factors[n])
            else:
                if factors[n + 1].is_annihilation:
                    new_factors.append(factors[n])
                else:
                    if factors[n].args[0] != factors[n + 1].args[0]:
                        new_factors.append(factors[n + 1] * factors[n])
                    else:
                        new_factors.append(factors[n + 1] * factors[n])
                    n += 1

        elif (isinstance(factors[n], FermionOp) and
              factors[n].is_annihilation):
            # fermion
            if not isinstance(factors[n + 1], FermionOp):
                new_factors.append(factors[n])
            else:
                if factors[n + 1].is_annihilation:
                    new_factors.append(factors[n])
                else:
                    if factors[n].args[0] != factors[n + 1].args[0]:
                        new_factors.append(-factors[n + 1] * factors[n])
                    else:
                        new_factors.append(-factors[n + 1] * factors[n])
                    n += 1

        else:
            new_factors.append(factors[n])

        n += 1

    if n == len(factors) - 1:
        new_factors.append(factors[-1])

    if new_factors == factors:
        return product
    else:
        expr = Mul(*new_factors).expand()
        return normal_order(expr,
                            recursive_limit=recursive_limit,
                            _recursive_depth=_recursive_depth + 1)


def _normal_order_terms(expr, recursive_limit=10, _recursive_depth=0):
    """
    Helper function for normal_order: look through each term in an addition
    expression and call _normal_order_factor to perform the normal ordering
    on the factors.
    """

    new_terms = []
    for term in expr.args:
        if isinstance(term, Mul):
            new_term = _normal_order_factor(term,
                                            recursive_limit=recursive_limit,
                                            _recursive_depth=_recursive_depth)
            new_terms.append(new_term)
        else:
            new_terms.append(term)

    return Add(*new_terms)


def normal_order(expr, recursive_limit=10, _recursive_depth=0):
    """Normal order an expression with bosonic or fermionic operators. Note
    that this normal order is not equivalent to the original expression, but
    the creation and annihilation operators in each term in expr is reordered
    so that the expression becomes normal ordered.

    Parameters
    ==========

    expr : expression
        The expression to normal order.

    recursive_limit : int (default 10)
        The number of allowed recursive applications of the function.

    Examples
    ========

    >>> from sympy.physics.quantum import Dagger
    >>> from sympy.physics.quantum.boson import BosonOp
    >>> from sympy.physics.quantum.operatorordering import normal_order
    >>> a = BosonOp("a")
    >>> normal_order(a * Dagger(a))
    Dagger(a)*a
    """
    if _recursive_depth > recursive_limit:
        warnings.warn("Too many recursions, aborting")
        return expr

    if isinstance(expr, Add):
        return _normal_order_terms(expr, recursive_limit=recursive_limit,
                                   _recursive_depth=_recursive_depth)
    elif isinstance(expr, Mul):
        return _normal_order_factor(expr, recursive_limit=recursive_limit,
                                    _recursive_depth=_recursive_depth)
    else:
        return expr
