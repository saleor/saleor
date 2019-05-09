from sympy.core import (Function, Pow, sympify, Expr)
from sympy.core.relational import Relational
from sympy.polys import Poly, decompose
from sympy.utilities.misc import func_name


def decompogen(f, symbol):
    """
    Computes General functional decomposition of ``f``.
    Given an expression ``f``, returns a list ``[f_1, f_2, ..., f_n]``,
    where::
              f = f_1 o f_2 o ... f_n = f_1(f_2(... f_n))

    Note: This is a General decomposition function. It also decomposes
    Polynomials. For only Polynomial decomposition see ``decompose`` in polys.

    Examples
    ========

    >>> from sympy.solvers.decompogen import decompogen
    >>> from sympy.abc import x
    >>> from sympy import sqrt, sin, cos
    >>> decompogen(sin(cos(x)), x)
    [sin(x), cos(x)]
    >>> decompogen(sin(x)**2 + sin(x) + 1, x)
    [x**2 + x + 1, sin(x)]
    >>> decompogen(sqrt(6*x**2 - 5), x)
    [sqrt(x), 6*x**2 - 5]
    >>> decompogen(sin(sqrt(cos(x**2 + 1))), x)
    [sin(x), sqrt(x), cos(x), x**2 + 1]
    >>> decompogen(x**4 + 2*x**3 - x - 1, x)
    [x**2 - x - 1, x**2 + x]

    """
    f = sympify(f)
    if not isinstance(f, Expr) or isinstance(f, Relational):
        raise TypeError('expecting Expr but got: `%s`' % func_name(f))
    if symbol not in f.free_symbols:
        return [f]

    result = []

    # ===== Simple Functions ===== #
    if isinstance(f, (Function, Pow)):
        if f.args[0] == symbol:
            return [f]
        result += [f.subs(f.args[0], symbol)] + decompogen(f.args[0], symbol)
        return result

    # ===== Convert to Polynomial ===== #
    fp = Poly(f)
    gens = list(filter(lambda x: symbol in x.free_symbols , fp.gens))

    if len(gens) == 1 and gens[0] != symbol:
        f1 = f.subs(gens[0], symbol)
        f2 = gens[0]
        result += [f1] + decompogen(f2, symbol)
        return result

    # ===== Polynomial decompose() ====== #
    try:
        result += decompose(f)
        return result
    except ValueError:
        return [f]


def compogen(g_s, symbol):
    """
    Returns the composition of functions.
    Given a list of functions ``g_s``, returns their composition ``f``,
    where:
        f = g_1 o g_2 o .. o g_n

    Note: This is a General composition function. It also composes Polynomials.
    For only Polynomial composition see ``compose`` in polys.

    Examples
    ========

    >>> from sympy.solvers.decompogen import compogen
    >>> from sympy.abc import x
    >>> from sympy import sqrt, sin, cos
    >>> compogen([sin(x), cos(x)], x)
    sin(cos(x))
    >>> compogen([x**2 + x + 1, sin(x)], x)
    sin(x)**2 + sin(x) + 1
    >>> compogen([sqrt(x), 6*x**2 - 5], x)
    sqrt(6*x**2 - 5)
    >>> compogen([sin(x), sqrt(x), cos(x), x**2 + 1], x)
    sin(sqrt(cos(x**2 + 1)))
    >>> compogen([x**2 - x - 1, x**2 + x], x)
    -x**2 - x + (x**2 + x)**2 - 1
    """
    if len(g_s) == 1:
        return g_s[0]

    foo = g_s[0].subs(symbol, g_s[1])

    if len(g_s) == 2:
        return foo

    return compogen([foo] + g_s[2:], symbol)
