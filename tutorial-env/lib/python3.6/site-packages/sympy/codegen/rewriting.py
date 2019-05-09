# -*- coding: utf-8 -*-
"""
Classes and functions useful for rewriting expressions for optimized code
generation. Some languages (or standards thereof), e.g. C99, offer specialized
math functions for better performance and/or precision.

Using the ``optimize`` function in this module, together with a collection of
rules (represented as instances of ``Optimization``), one can rewrite the
expressions for this purpose::

    >>> from sympy import Symbol, exp, log
    >>> from sympy.codegen.rewriting import optimize, optims_c99
    >>> x = Symbol('x')
    >>> optimize(3*exp(2*x) - 3, optims_c99)
    3*expm1(2*x)
    >>> optimize(exp(2*x) - 3, optims_c99)
    exp(2*x) - 3
    >>> optimize(log(3*x + 3), optims_c99)
    log1p(x) + log(3)
    >>> optimize(log(2*x + 3), optims_c99)
    log(2*x + 3)

The ``optims_c99`` imported above is tuple containing the following instances
(which may be imported from ``sympy.codegen.rewriting``):

- ``expm1_opt``
- ``log1p_opt``
- ``exp2_opt``
- ``log2_opt``
- ``log2const_opt``


"""
from __future__ import (absolute_import, division, print_function)
from itertools import chain
from sympy import log, exp, Max, Min, Wild, expand_log, Dummy
from sympy.codegen.cfunctions import log1p, log2, exp2, expm1
from sympy.core.mul import Mul
from sympy.utilities.iterables import sift


class Optimization(object):
    """ Abstract base class for rewriting optimization.

    Subclasses should implement ``__call__`` taking an expression
    as argument.

    Parameters
    ==========
    cost_function : callable returning number
    priority : number

    """
    def __init__(self, cost_function=None, priority=1):
        self.cost_function = cost_function
        self.priority=priority


class ReplaceOptim(Optimization):
    """ Rewriting optimization calling replace on expressions.

    The instance can be used as a function on expressions for which
    it will apply the ``replace`` method (see
    :meth:`sympy.core.basic.Basic.replace`).

    Parameters
    ==========
    query : first argument passed to replace
    value : second argument passed to replace

    Examples
    ========

    >>> from sympy import Symbol, Pow
    >>> from sympy.codegen.rewriting import ReplaceOptim
    >>> from sympy.codegen.cfunctions import exp2
    >>> x = Symbol('x')
    >>> exp2_opt = ReplaceOptim(lambda p: p.is_Pow and p.base == 2,
    ...     lambda p: exp2(p.exp))
    >>> exp2_opt(2**x)
    exp2(x)

    """

    def __init__(self, query, value, **kwargs):
        super(ReplaceOptim, self).__init__(**kwargs)
        self.query = query
        self.value = value

    def __call__(self, expr):
        return expr.replace(self.query, self.value)


def optimize(expr, optimizations):
    """ Apply optimizations to an expression.

    Parameters
    ==========

    expr : expression
    optimizations : iterable of ``Optimization`` instances
        The optimizations will be sorted with respect to ``priority`` (highest first).

    Examples
    ========

    >>> from sympy import log, Symbol
    >>> from sympy.codegen.rewriting import optims_c99, optimize
    >>> x = Symbol('x')
    >>> optimize(log(x+3)/log(2) + log(x**2 + 1), optims_c99)
    log1p(x**2) + log2(x + 3)

    """

    for optim in sorted(optimizations, key=lambda opt: opt.priority, reverse=True):
        new_expr = optim(expr)
        if optim.cost_function is None:
            expr = new_expr
        else:
            before, after = map(lambda x: optim.cost_function(x), (expr, new_expr))
            if before > after:
                expr = new_expr
    return expr


exp2_opt = ReplaceOptim(
    lambda p: p.is_Pow and p.base == 2,
    lambda p: exp2(p.exp)
)

_d = Wild('d', properties=[lambda x: x.is_Dummy])
_u = Wild('u', properties=[lambda x: not x.is_number and not x.is_Add])
_v = Wild('v')
_w = Wild('w')


log2_opt = ReplaceOptim(_v*log(_w)/log(2), _v*log2(_w), cost_function=lambda expr: expr.count(
    lambda e: (  # division & eval of transcendentals are expensive floating point operations...
        e.is_Pow and e.exp.is_negative  # division
        or (isinstance(e, (log, log2)) and not e.args[0].is_number))  # transcendental
    )
)

log2const_opt = ReplaceOptim(log(2)*log2(_w), log(_w))

logsumexp_2terms_opt = ReplaceOptim(
    lambda l: (isinstance(l, log)
               and l.args[0].is_Add
               and len(l.args[0].args) == 2
               and all(isinstance(t, exp) for t in l.args[0].args)),
    lambda l: (
        Max(*[e.args[0] for e in l.args[0].args]) +
        log1p(exp(Min(*[e.args[0] for e in l.args[0].args])))
    )
)


def _try_expm1(expr):
    protected, old_new =  expr.replace(exp, lambda arg: Dummy(), map=True)
    factored = protected.factor()
    new_old = {v: k for k, v in old_new.items()}
    return factored.replace(_d - 1, lambda d: expm1(new_old[d].args[0])).xreplace(new_old)


def _expm1_value(e):
    numbers, non_num = sift(e.args, lambda arg: arg.is_number, binary=True)
    non_num_exp, non_num_other = sift(non_num, lambda arg: arg.has(exp),
        binary=True)
    numsum = sum(numbers)
    new_exp_terms, done = [], False
    for exp_term in non_num_exp:
        if done:
            new_exp_terms.append(exp_term)
        else:
            looking_at = exp_term + numsum
            attempt = _try_expm1(looking_at)
            if looking_at == attempt:
                new_exp_terms.append(exp_term)
            else:
                done = True
                new_exp_terms.append(attempt)
    if not done:
        new_exp_terms.append(numsum)
    return e.func(*chain(new_exp_terms, non_num_other))


expm1_opt = ReplaceOptim(lambda e: e.is_Add, _expm1_value)


log1p_opt = ReplaceOptim(
    lambda e: isinstance(e, log),
    lambda l: expand_log(l.replace(
        log, lambda arg: log(arg.factor())
    )).replace(log(_u+1), log1p(_u))
)

def create_expand_pow_optimization(limit):
    """ Creates an instance of :class:`ReplaceOptim` for expanding ``Pow``.

    The requirements for expansions are that the base needs to be a symbol
    and the exponent needs to be an integer (and be less than or equal to
    ``limit``).

    Parameters
    ==========

    limit : int
         The highest power which is expanded into multiplication.

    Examples
    ========

    >>> from sympy import Symbol, sin
    >>> from sympy.codegen.rewriting import create_expand_pow_optimization
    >>> x = Symbol('x')
    >>> expand_opt = create_expand_pow_optimization(3)
    >>> expand_opt(x**5 + x**3)
    x**5 + x*x*x
    >>> expand_opt(x**5 + x**3 + sin(x)**3)
    x**5 + x*x*x + sin(x)**3

    """
    return ReplaceOptim(
        lambda e: e.is_Pow and e.base.is_symbol and e.exp.is_integer and e.exp.is_nonnegative and e.exp <= limit,
        lambda p: Mul(*([p.base]*p.exp), evaluate=False)
    )

# Collections of optimizations:
optims_c99 = (expm1_opt, log1p_opt, exp2_opt, log2_opt, log2const_opt)
