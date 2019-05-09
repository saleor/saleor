"""Square-free decomposition algorithms and related tools. """

from __future__ import print_function, division

from sympy.polys.densearith import (
    dup_neg, dmp_neg,
    dup_sub, dmp_sub,
    dup_mul,
    dup_quo, dmp_quo,
    dup_mul_ground, dmp_mul_ground)
from sympy.polys.densebasic import (
    dup_strip,
    dup_LC, dmp_ground_LC,
    dmp_zero_p,
    dmp_ground,
    dup_degree, dmp_degree,
    dmp_raise, dmp_inject,
    dup_convert)
from sympy.polys.densetools import (
    dup_diff, dmp_diff,
    dup_shift, dmp_compose,
    dup_monic, dmp_ground_monic,
    dup_primitive, dmp_ground_primitive)
from sympy.polys.euclidtools import (
    dup_inner_gcd, dmp_inner_gcd,
    dup_gcd, dmp_gcd,
    dmp_resultant)
from sympy.polys.galoistools import (
    gf_sqf_list, gf_sqf_part)
from sympy.polys.polyerrors import (
    MultivariatePolynomialError,
    DomainError)

def dup_sqf_p(f, K):
    """
    Return ``True`` if ``f`` is a square-free polynomial in ``K[x]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x = ring("x", ZZ)

    >>> R.dup_sqf_p(x**2 - 2*x + 1)
    False
    >>> R.dup_sqf_p(x**2 - 1)
    True

    """
    if not f:
        return True
    else:
        return not dup_degree(dup_gcd(f, dup_diff(f, 1, K), K))


def dmp_sqf_p(f, u, K):
    """
    Return ``True`` if ``f`` is a square-free polynomial in ``K[X]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x,y = ring("x,y", ZZ)

    >>> R.dmp_sqf_p(x**2 + 2*x*y + y**2)
    False
    >>> R.dmp_sqf_p(x**2 + y**2)
    True

    """
    if dmp_zero_p(f, u):
        return True
    else:
        return not dmp_degree(dmp_gcd(f, dmp_diff(f, 1, u, K), u, K), u)


def dup_sqf_norm(f, K):
    """
    Square-free norm of ``f`` in ``K[x]``, useful over algebraic domains.

    Returns ``s``, ``f``, ``r``, such that ``g(x) = f(x-sa)`` and ``r(x) = Norm(g(x))``
    is a square-free polynomial over K, where ``a`` is the algebraic extension of ``K``.

    Examples
    ========

    >>> from sympy.polys import ring, QQ
    >>> from sympy import sqrt

    >>> K = QQ.algebraic_field(sqrt(3))
    >>> R, x = ring("x", K)
    >>> _, X = ring("x", QQ)

    >>> s, f, r = R.dup_sqf_norm(x**2 - 2)

    >>> s == 1
    True
    >>> f == x**2 + K([QQ(-2), QQ(0)])*x + 1
    True
    >>> r == X**4 - 10*X**2 + 1
    True

    """
    if not K.is_Algebraic:
        raise DomainError("ground domain must be algebraic")

    s, g = 0, dmp_raise(K.mod.rep, 1, 0, K.dom)

    while True:
        h, _ = dmp_inject(f, 0, K, front=True)
        r = dmp_resultant(g, h, 1, K.dom)

        if dup_sqf_p(r, K.dom):
            break
        else:
            f, s = dup_shift(f, -K.unit, K), s + 1

    return s, f, r


def dmp_sqf_norm(f, u, K):
    """
    Square-free norm of ``f`` in ``K[X]``, useful over algebraic domains.

    Returns ``s``, ``f``, ``r``, such that ``g(x) = f(x-sa)`` and ``r(x) = Norm(g(x))``
    is a square-free polynomial over K, where ``a`` is the algebraic extension of ``K``.

    Examples
    ========

    >>> from sympy.polys import ring, QQ
    >>> from sympy import I

    >>> K = QQ.algebraic_field(I)
    >>> R, x, y = ring("x,y", K)
    >>> _, X, Y = ring("x,y", QQ)

    >>> s, f, r = R.dmp_sqf_norm(x*y + y**2)

    >>> s == 1
    True
    >>> f == x*y + y**2 + K([QQ(-1), QQ(0)])*y
    True
    >>> r == X**2*Y**2 + 2*X*Y**3 + Y**4 + Y**2
    True

    """
    if not u:
        return dup_sqf_norm(f, K)

    if not K.is_Algebraic:
        raise DomainError("ground domain must be algebraic")

    g = dmp_raise(K.mod.rep, u + 1, 0, K.dom)
    F = dmp_raise([K.one, -K.unit], u, 0, K)

    s = 0

    while True:
        h, _ = dmp_inject(f, u, K, front=True)
        r = dmp_resultant(g, h, u + 1, K.dom)

        if dmp_sqf_p(r, u, K.dom):
            break
        else:
            f, s = dmp_compose(f, F, u, K), s + 1

    return s, f, r


def dmp_norm(f, u, K):
    """
    Norm of ``f`` in ``K[X1, ..., Xn]``, often not square-free.
    """
    if not K.is_Algebraic:
        raise DomainError("ground domain must be algebraic")

    g = dmp_raise(K.mod.rep, u + 1, 0, K.dom)
    h, _ = dmp_inject(f, u, K, front=True)

    return dmp_resultant(g, h, u + 1, K.dom)


def dup_gf_sqf_part(f, K):
    """Compute square-free part of ``f`` in ``GF(p)[x]``. """
    f = dup_convert(f, K, K.dom)
    g = gf_sqf_part(f, K.mod, K.dom)
    return dup_convert(g, K.dom, K)


def dmp_gf_sqf_part(f, u, K):
    """Compute square-free part of ``f`` in ``GF(p)[X]``. """
    raise NotImplementedError('multivariate polynomials over finite fields')


def dup_sqf_part(f, K):
    """
    Returns square-free part of a polynomial in ``K[x]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x = ring("x", ZZ)

    >>> R.dup_sqf_part(x**3 - 3*x - 2)
    x**2 - x - 2

    """
    if K.is_FiniteField:
        return dup_gf_sqf_part(f, K)

    if not f:
        return f

    if K.is_negative(dup_LC(f, K)):
        f = dup_neg(f, K)

    gcd = dup_gcd(f, dup_diff(f, 1, K), K)
    sqf = dup_quo(f, gcd, K)

    if K.is_Field:
        return dup_monic(sqf, K)
    else:
        return dup_primitive(sqf, K)[1]


def dmp_sqf_part(f, u, K):
    """
    Returns square-free part of a polynomial in ``K[X]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x,y = ring("x,y", ZZ)

    >>> R.dmp_sqf_part(x**3 + 2*x**2*y + x*y**2)
    x**2 + x*y

    """
    if not u:
        return dup_sqf_part(f, K)

    if K.is_FiniteField:
        return dmp_gf_sqf_part(f, u, K)

    if dmp_zero_p(f, u):
        return f

    if K.is_negative(dmp_ground_LC(f, u, K)):
        f = dmp_neg(f, u, K)

    gcd = dmp_gcd(f, dmp_diff(f, 1, u, K), u, K)
    sqf = dmp_quo(f, gcd, u, K)

    if K.is_Field:
        return dmp_ground_monic(sqf, u, K)
    else:
        return dmp_ground_primitive(sqf, u, K)[1]


def dup_gf_sqf_list(f, K, all=False):
    """Compute square-free decomposition of ``f`` in ``GF(p)[x]``. """
    f = dup_convert(f, K, K.dom)

    coeff, factors = gf_sqf_list(f, K.mod, K.dom, all=all)

    for i, (f, k) in enumerate(factors):
        factors[i] = (dup_convert(f, K.dom, K), k)

    return K.convert(coeff, K.dom), factors


def dmp_gf_sqf_list(f, u, K, all=False):
    """Compute square-free decomposition of ``f`` in ``GF(p)[X]``. """
    raise NotImplementedError('multivariate polynomials over finite fields')


def dup_sqf_list(f, K, all=False):
    """
    Return square-free decomposition of a polynomial in ``K[x]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x = ring("x", ZZ)

    >>> f = 2*x**5 + 16*x**4 + 50*x**3 + 76*x**2 + 56*x + 16

    >>> R.dup_sqf_list(f)
    (2, [(x + 1, 2), (x + 2, 3)])
    >>> R.dup_sqf_list(f, all=True)
    (2, [(1, 1), (x + 1, 2), (x + 2, 3)])

    """
    if K.is_FiniteField:
        return dup_gf_sqf_list(f, K, all=all)

    if K.is_Field:
        coeff = dup_LC(f, K)
        f = dup_monic(f, K)
    else:
        coeff, f = dup_primitive(f, K)

        if K.is_negative(dup_LC(f, K)):
            f = dup_neg(f, K)
            coeff = -coeff

    if dup_degree(f) <= 0:
        return coeff, []

    result, i = [], 1

    h = dup_diff(f, 1, K)
    g, p, q = dup_inner_gcd(f, h, K)

    while True:
        d = dup_diff(p, 1, K)
        h = dup_sub(q, d, K)

        if not h:
            result.append((p, i))
            break

        g, p, q = dup_inner_gcd(p, h, K)

        if all or dup_degree(g) > 0:
            result.append((g, i))

        i += 1

    return coeff, result


def dup_sqf_list_include(f, K, all=False):
    """
    Return square-free decomposition of a polynomial in ``K[x]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x = ring("x", ZZ)

    >>> f = 2*x**5 + 16*x**4 + 50*x**3 + 76*x**2 + 56*x + 16

    >>> R.dup_sqf_list_include(f)
    [(2, 1), (x + 1, 2), (x + 2, 3)]
    >>> R.dup_sqf_list_include(f, all=True)
    [(2, 1), (x + 1, 2), (x + 2, 3)]

    """
    coeff, factors = dup_sqf_list(f, K, all=all)

    if factors and factors[0][1] == 1:
        g = dup_mul_ground(factors[0][0], coeff, K)
        return [(g, 1)] + factors[1:]
    else:
        g = dup_strip([coeff])
        return [(g, 1)] + factors


def dmp_sqf_list(f, u, K, all=False):
    """
    Return square-free decomposition of a polynomial in ``K[X]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x,y = ring("x,y", ZZ)

    >>> f = x**5 + 2*x**4*y + x**3*y**2

    >>> R.dmp_sqf_list(f)
    (1, [(x + y, 2), (x, 3)])
    >>> R.dmp_sqf_list(f, all=True)
    (1, [(1, 1), (x + y, 2), (x, 3)])

    """
    if not u:
        return dup_sqf_list(f, K, all=all)

    if K.is_FiniteField:
        return dmp_gf_sqf_list(f, u, K, all=all)

    if K.is_Field:
        coeff = dmp_ground_LC(f, u, K)
        f = dmp_ground_monic(f, u, K)
    else:
        coeff, f = dmp_ground_primitive(f, u, K)

        if K.is_negative(dmp_ground_LC(f, u, K)):
            f = dmp_neg(f, u, K)
            coeff = -coeff

    if dmp_degree(f, u) <= 0:
        return coeff, []

    result, i = [], 1

    h = dmp_diff(f, 1, u, K)
    g, p, q = dmp_inner_gcd(f, h, u, K)

    while True:
        d = dmp_diff(p, 1, u, K)
        h = dmp_sub(q, d, u, K)

        if dmp_zero_p(h, u):
            result.append((p, i))
            break

        g, p, q = dmp_inner_gcd(p, h, u, K)

        if all or dmp_degree(g, u) > 0:
            result.append((g, i))

        i += 1

    return coeff, result


def dmp_sqf_list_include(f, u, K, all=False):
    """
    Return square-free decomposition of a polynomial in ``K[x]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x,y = ring("x,y", ZZ)

    >>> f = x**5 + 2*x**4*y + x**3*y**2

    >>> R.dmp_sqf_list_include(f)
    [(1, 1), (x + y, 2), (x, 3)]
    >>> R.dmp_sqf_list_include(f, all=True)
    [(1, 1), (x + y, 2), (x, 3)]

    """
    if not u:
        return dup_sqf_list_include(f, K, all=all)

    coeff, factors = dmp_sqf_list(f, u, K, all=all)

    if factors and factors[0][1] == 1:
        g = dmp_mul_ground(factors[0][0], coeff, u, K)
        return [(g, 1)] + factors[1:]
    else:
        g = dmp_ground(coeff, u)
        return [(g, 1)] + factors


def dup_gff_list(f, K):
    """
    Compute greatest factorial factorization of ``f`` in ``K[x]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x = ring("x", ZZ)

    >>> R.dup_gff_list(x**5 + 2*x**4 - x**3 - 2*x**2)
    [(x, 1), (x + 2, 4)]

    """
    if not f:
        raise ValueError("greatest factorial factorization doesn't exist for a zero polynomial")

    f = dup_monic(f, K)

    if not dup_degree(f):
        return []
    else:
        g = dup_gcd(f, dup_shift(f, K.one, K), K)
        H = dup_gff_list(g, K)

        for i, (h, k) in enumerate(H):
            g = dup_mul(g, dup_shift(h, -K(k), K), K)
            H[i] = (h, k + 1)

        f = dup_quo(f, g, K)

        if not dup_degree(f):
            return H
        else:
            return [(f, 1)] + H


def dmp_gff_list(f, u, K):
    """
    Compute greatest factorial factorization of ``f`` in ``K[X]``.

    Examples
    ========

    >>> from sympy.polys import ring, ZZ
    >>> R, x,y = ring("x,y", ZZ)

    """
    if not u:
        return dup_gff_list(f, K)
    else:
        raise MultivariatePolynomialError(f)
