"""OO layer for several polynomial representations. """

from __future__ import print_function, division

from sympy import oo
from sympy.core.sympify import CantSympify
from sympy.polys.polyerrors import CoercionFailed, NotReversible, NotInvertible
from sympy.polys.polyutils import PicklableWithSlots


class GenericPoly(PicklableWithSlots):
    """Base class for low-level polynomial representations. """

    def ground_to_ring(f):
        """Make the ground domain a ring. """
        return f.set_domain(f.dom.get_ring())

    def ground_to_field(f):
        """Make the ground domain a field. """
        return f.set_domain(f.dom.get_field())

    def ground_to_exact(f):
        """Make the ground domain exact. """
        return f.set_domain(f.dom.get_exact())

    @classmethod
    def _perify_factors(per, result, include):
        if include:
            coeff, factors = result
        else:
            coeff = result

        factors = [ (per(g), k) for g, k in factors ]

        if include:
            return coeff, factors
        else:
            return factors

from sympy.polys.densebasic import (
    dmp_validate,
    dup_normal, dmp_normal,
    dup_convert, dmp_convert,
    dmp_from_sympy,
    dup_strip,
    dup_degree, dmp_degree_in,
    dmp_degree_list,
    dmp_negative_p,
    dup_LC, dmp_ground_LC,
    dup_TC, dmp_ground_TC,
    dmp_ground_nth,
    dmp_one, dmp_ground,
    dmp_zero_p, dmp_one_p, dmp_ground_p,
    dup_from_dict, dmp_from_dict,
    dmp_to_dict,
    dmp_deflate,
    dmp_inject, dmp_eject,
    dmp_terms_gcd,
    dmp_list_terms, dmp_exclude,
    dmp_slice_in, dmp_permute,
    dmp_to_tuple,)

from sympy.polys.densearith import (
    dmp_add_ground,
    dmp_sub_ground,
    dmp_mul_ground,
    dmp_quo_ground,
    dmp_exquo_ground,
    dmp_abs,
    dup_neg, dmp_neg,
    dup_add, dmp_add,
    dup_sub, dmp_sub,
    dup_mul, dmp_mul,
    dmp_sqr,
    dup_pow, dmp_pow,
    dmp_pdiv,
    dmp_prem,
    dmp_pquo,
    dmp_pexquo,
    dmp_div,
    dup_rem, dmp_rem,
    dmp_quo,
    dmp_exquo,
    dmp_add_mul, dmp_sub_mul,
    dmp_max_norm,
    dmp_l1_norm)

from sympy.polys.densetools import (
    dmp_clear_denoms,
    dmp_integrate_in,
    dmp_diff_in,
    dmp_eval_in,
    dup_revert,
    dmp_ground_trunc,
    dmp_ground_content,
    dmp_ground_primitive,
    dmp_ground_monic,
    dmp_compose,
    dup_decompose,
    dup_shift,
    dup_transform,
    dmp_lift)

from sympy.polys.euclidtools import (
    dup_half_gcdex, dup_gcdex, dup_invert,
    dmp_subresultants,
    dmp_resultant,
    dmp_discriminant,
    dmp_inner_gcd,
    dmp_gcd,
    dmp_lcm,
    dmp_cancel)

from sympy.polys.sqfreetools import (
    dup_gff_list,
    dmp_norm,
    dmp_sqf_p,
    dmp_sqf_norm,
    dmp_sqf_part,
    dmp_sqf_list, dmp_sqf_list_include)

from sympy.polys.factortools import (
    dup_cyclotomic_p, dmp_irreducible_p,
    dmp_factor_list, dmp_factor_list_include)

from sympy.polys.rootisolation import (
    dup_isolate_real_roots_sqf,
    dup_isolate_real_roots,
    dup_isolate_all_roots_sqf,
    dup_isolate_all_roots,
    dup_refine_real_root,
    dup_count_real_roots,
    dup_count_complex_roots,
    dup_sturm)

from sympy.polys.polyerrors import (
    UnificationFailed,
    PolynomialError)


def init_normal_DMP(rep, lev, dom):
    return DMP(dmp_normal(rep, lev, dom), dom, lev)


class DMP(PicklableWithSlots, CantSympify):
    """Dense Multivariate Polynomials over `K`. """

    __slots__ = ['rep', 'lev', 'dom', 'ring']

    def __init__(self, rep, dom, lev=None, ring=None):
        if lev is not None:
            if type(rep) is dict:
                rep = dmp_from_dict(rep, lev, dom)
            elif type(rep) is not list:
                rep = dmp_ground(dom.convert(rep), lev)
        else:
            rep, lev = dmp_validate(rep)

        self.rep = rep
        self.lev = lev
        self.dom = dom
        self.ring = ring

    def __repr__(f):
        return "%s(%s, %s, %s)" % (f.__class__.__name__, f.rep, f.dom, f.ring)

    def __hash__(f):
        return hash((f.__class__.__name__, f.to_tuple(), f.lev, f.dom, f.ring))

    def unify(f, g):
        """Unify representations of two multivariate polynomials. """
        if not isinstance(g, DMP) or f.lev != g.lev:
            raise UnificationFailed("can't unify %s with %s" % (f, g))

        if f.dom == g.dom and f.ring == g.ring:
            return f.lev, f.dom, f.per, f.rep, g.rep
        else:
            lev, dom = f.lev, f.dom.unify(g.dom)
            ring = f.ring
            if g.ring is not None:
                if ring is not None:
                    ring = ring.unify(g.ring)
                else:
                    ring = g.ring

            F = dmp_convert(f.rep, lev, f.dom, dom)
            G = dmp_convert(g.rep, lev, g.dom, dom)

            def per(rep, dom=dom, lev=lev, kill=False):
                if kill:
                    if not lev:
                        return rep
                    else:
                        lev -= 1

                return DMP(rep, dom, lev, ring)

            return lev, dom, per, F, G

    def per(f, rep, dom=None, kill=False, ring=None):
        """Create a DMP out of the given representation. """
        lev = f.lev

        if kill:
            if not lev:
                return rep
            else:
                lev -= 1

        if dom is None:
            dom = f.dom

        if ring is None:
            ring = f.ring

        return DMP(rep, dom, lev, ring)

    @classmethod
    def zero(cls, lev, dom, ring=None):
        return DMP(0, dom, lev, ring)

    @classmethod
    def one(cls, lev, dom, ring=None):
        return DMP(1, dom, lev, ring)

    @classmethod
    def from_list(cls, rep, lev, dom):
        """Create an instance of ``cls`` given a list of native coefficients. """
        return cls(dmp_convert(rep, lev, None, dom), dom, lev)

    @classmethod
    def from_sympy_list(cls, rep, lev, dom):
        """Create an instance of ``cls`` given a list of SymPy coefficients. """
        return cls(dmp_from_sympy(rep, lev, dom), dom, lev)

    def to_dict(f, zero=False):
        """Convert ``f`` to a dict representation with native coefficients. """
        return dmp_to_dict(f.rep, f.lev, f.dom, zero=zero)

    def to_sympy_dict(f, zero=False):
        """Convert ``f`` to a dict representation with SymPy coefficients. """
        rep = dmp_to_dict(f.rep, f.lev, f.dom, zero=zero)

        for k, v in rep.items():
            rep[k] = f.dom.to_sympy(v)

        return rep

    def to_list(f):
        """Convert ``f`` to a list representation with native coefficients. """
        return f.rep

    def to_sympy_list(f):
        """Convert ``f`` to a list representation with SymPy coefficients. """
        def sympify_nested_list(rep):
            out = []
            for val in rep:
                if isinstance(val, list):
                    out.append(sympify_nested_list(val))
                else:
                    out.append(f.dom.to_sympy(val))
            return out

        return sympify_nested_list(f.rep)

    def to_tuple(f):
        """
        Convert ``f`` to a tuple representation with native coefficients.

        This is needed for hashing.
        """
        return dmp_to_tuple(f.rep, f.lev)

    @classmethod
    def from_dict(cls, rep, lev, dom):
        """Construct and instance of ``cls`` from a ``dict`` representation. """
        return cls(dmp_from_dict(rep, lev, dom), dom, lev)

    @classmethod
    def from_monoms_coeffs(cls, monoms, coeffs, lev, dom, ring=None):
        return DMP(dict(list(zip(monoms, coeffs))), dom, lev, ring)

    def to_ring(f):
        """Make the ground domain a ring. """
        return f.convert(f.dom.get_ring())

    def to_field(f):
        """Make the ground domain a field. """
        return f.convert(f.dom.get_field())

    def to_exact(f):
        """Make the ground domain exact. """
        return f.convert(f.dom.get_exact())

    def convert(f, dom):
        """Convert the ground domain of ``f``. """
        if f.dom == dom:
            return f
        else:
            return DMP(dmp_convert(f.rep, f.lev, f.dom, dom), dom, f.lev)

    def slice(f, m, n, j=0):
        """Take a continuous subsequence of terms of ``f``. """
        return f.per(dmp_slice_in(f.rep, m, n, j, f.lev, f.dom))

    def coeffs(f, order=None):
        """Returns all non-zero coefficients from ``f`` in lex order. """
        return [ c for _, c in dmp_list_terms(f.rep, f.lev, f.dom, order=order) ]

    def monoms(f, order=None):
        """Returns all non-zero monomials from ``f`` in lex order. """
        return [ m for m, _ in dmp_list_terms(f.rep, f.lev, f.dom, order=order) ]

    def terms(f, order=None):
        """Returns all non-zero terms from ``f`` in lex order. """
        return dmp_list_terms(f.rep, f.lev, f.dom, order=order)

    def all_coeffs(f):
        """Returns all coefficients from ``f``. """
        if not f.lev:
            if not f:
                return [f.dom.zero]
            else:
                return [ c for c in f.rep ]
        else:
            raise PolynomialError('multivariate polynomials not supported')

    def all_monoms(f):
        """Returns all monomials from ``f``. """
        if not f.lev:
            n = dup_degree(f.rep)

            if n < 0:
                return [(0,)]
            else:
                return [ (n - i,) for i, c in enumerate(f.rep) ]
        else:
            raise PolynomialError('multivariate polynomials not supported')

    def all_terms(f):
        """Returns all terms from a ``f``. """
        if not f.lev:
            n = dup_degree(f.rep)

            if n < 0:
                return [((0,), f.dom.zero)]
            else:
                return [ ((n - i,), c) for i, c in enumerate(f.rep) ]
        else:
            raise PolynomialError('multivariate polynomials not supported')

    def lift(f):
        """Convert algebraic coefficients to rationals. """
        return f.per(dmp_lift(f.rep, f.lev, f.dom), dom=f.dom.dom)

    def deflate(f):
        """Reduce degree of `f` by mapping `x_i^m` to `y_i`. """
        J, F = dmp_deflate(f.rep, f.lev, f.dom)
        return J, f.per(F)

    def inject(f, front=False):
        """Inject ground domain generators into ``f``. """
        F, lev = dmp_inject(f.rep, f.lev, f.dom, front=front)
        return f.__class__(F, f.dom.dom, lev)

    def eject(f, dom, front=False):
        """Eject selected generators into the ground domain. """
        F = dmp_eject(f.rep, f.lev, dom, front=front)
        return f.__class__(F, dom, f.lev - len(dom.symbols))

    def exclude(f):
        r"""
        Remove useless generators from ``f``.

        Returns the removed generators and the new excluded ``f``.

        Examples
        ========

        >>> from sympy.polys.polyclasses import DMP
        >>> from sympy.polys.domains import ZZ

        >>> DMP([[[ZZ(1)]], [[ZZ(1)], [ZZ(2)]]], ZZ).exclude()
        ([2], DMP([[1], [1, 2]], ZZ, None))

        """
        J, F, u = dmp_exclude(f.rep, f.lev, f.dom)
        return J, f.__class__(F, f.dom, u)

    def permute(f, P):
        r"""
        Returns a polynomial in `K[x_{P(1)}, ..., x_{P(n)}]`.

        Examples
        ========

        >>> from sympy.polys.polyclasses import DMP
        >>> from sympy.polys.domains import ZZ

        >>> DMP([[[ZZ(2)], [ZZ(1), ZZ(0)]], [[]]], ZZ).permute([1, 0, 2])
        DMP([[[2], []], [[1, 0], []]], ZZ, None)

        >>> DMP([[[ZZ(2)], [ZZ(1), ZZ(0)]], [[]]], ZZ).permute([1, 2, 0])
        DMP([[[1], []], [[2, 0], []]], ZZ, None)

        """
        return f.per(dmp_permute(f.rep, P, f.lev, f.dom))

    def terms_gcd(f):
        """Remove GCD of terms from the polynomial ``f``. """
        J, F = dmp_terms_gcd(f.rep, f.lev, f.dom)
        return J, f.per(F)

    def add_ground(f, c):
        """Add an element of the ground domain to ``f``. """
        return f.per(dmp_add_ground(f.rep, f.dom.convert(c), f.lev, f.dom))

    def sub_ground(f, c):
        """Subtract an element of the ground domain from ``f``. """
        return f.per(dmp_sub_ground(f.rep, f.dom.convert(c), f.lev, f.dom))

    def mul_ground(f, c):
        """Multiply ``f`` by a an element of the ground domain. """
        return f.per(dmp_mul_ground(f.rep, f.dom.convert(c), f.lev, f.dom))

    def quo_ground(f, c):
        """Quotient of ``f`` by a an element of the ground domain. """
        return f.per(dmp_quo_ground(f.rep, f.dom.convert(c), f.lev, f.dom))

    def exquo_ground(f, c):
        """Exact quotient of ``f`` by a an element of the ground domain. """
        return f.per(dmp_exquo_ground(f.rep, f.dom.convert(c), f.lev, f.dom))

    def abs(f):
        """Make all coefficients in ``f`` positive. """
        return f.per(dmp_abs(f.rep, f.lev, f.dom))

    def neg(f):
        """Negate all coefficients in ``f``. """
        return f.per(dmp_neg(f.rep, f.lev, f.dom))

    def add(f, g):
        """Add two multivariate polynomials ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_add(F, G, lev, dom))

    def sub(f, g):
        """Subtract two multivariate polynomials ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_sub(F, G, lev, dom))

    def mul(f, g):
        """Multiply two multivariate polynomials ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_mul(F, G, lev, dom))

    def sqr(f):
        """Square a multivariate polynomial ``f``. """
        return f.per(dmp_sqr(f.rep, f.lev, f.dom))

    def pow(f, n):
        """Raise ``f`` to a non-negative power ``n``. """
        if isinstance(n, int):
            return f.per(dmp_pow(f.rep, n, f.lev, f.dom))
        else:
            raise TypeError("``int`` expected, got %s" % type(n))

    def pdiv(f, g):
        """Polynomial pseudo-division of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        q, r = dmp_pdiv(F, G, lev, dom)
        return per(q), per(r)

    def prem(f, g):
        """Polynomial pseudo-remainder of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_prem(F, G, lev, dom))

    def pquo(f, g):
        """Polynomial pseudo-quotient of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_pquo(F, G, lev, dom))

    def pexquo(f, g):
        """Polynomial exact pseudo-quotient of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_pexquo(F, G, lev, dom))

    def div(f, g):
        """Polynomial division with remainder of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        q, r = dmp_div(F, G, lev, dom)
        return per(q), per(r)

    def rem(f, g):
        """Computes polynomial remainder of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_rem(F, G, lev, dom))

    def quo(f, g):
        """Computes polynomial quotient of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_quo(F, G, lev, dom))

    def exquo(f, g):
        """Computes polynomial exact quotient of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        res = per(dmp_exquo(F, G, lev, dom))
        if f.ring and res not in f.ring:
            from sympy.polys.polyerrors import ExactQuotientFailed
            raise ExactQuotientFailed(f, g, f.ring)
        return res

    def degree(f, j=0):
        """Returns the leading degree of ``f`` in ``x_j``. """
        if isinstance(j, int):
            return dmp_degree_in(f.rep, j, f.lev)
        else:
            raise TypeError("``int`` expected, got %s" % type(j))

    def degree_list(f):
        """Returns a list of degrees of ``f``. """
        return dmp_degree_list(f.rep, f.lev)

    def total_degree(f):
        """Returns the total degree of ``f``. """
        return max(sum(m) for m in f.monoms())

    def homogenize(f, s):
        """Return homogeneous polynomial of ``f``"""
        td = f.total_degree()
        result = {}
        new_symbol = (s == len(f.terms()[0][0]))
        for term in f.terms():
            d = sum(term[0])
            if d < td:
                i = td - d
            else:
                i = 0
            if new_symbol:
                result[term[0] + (i,)] = term[1]
            else:
                l = list(term[0])
                l[s] += i
                result[tuple(l)] = term[1]
        return DMP(result, f.dom, f.lev + int(new_symbol), f.ring)

    def homogeneous_order(f):
        """Returns the homogeneous order of ``f``. """
        if f.is_zero:
            return -oo

        monoms = f.monoms()
        tdeg = sum(monoms[0])

        for monom in monoms:
            _tdeg = sum(monom)

            if _tdeg != tdeg:
                return None

        return tdeg

    def LC(f):
        """Returns the leading coefficient of ``f``. """
        return dmp_ground_LC(f.rep, f.lev, f.dom)

    def TC(f):
        """Returns the trailing coefficient of ``f``. """
        return dmp_ground_TC(f.rep, f.lev, f.dom)

    def nth(f, *N):
        """Returns the ``n``-th coefficient of ``f``. """
        if all(isinstance(n, int) for n in N):
            return dmp_ground_nth(f.rep, N, f.lev, f.dom)
        else:
            raise TypeError("a sequence of integers expected")

    def max_norm(f):
        """Returns maximum norm of ``f``. """
        return dmp_max_norm(f.rep, f.lev, f.dom)

    def l1_norm(f):
        """Returns l1 norm of ``f``. """
        return dmp_l1_norm(f.rep, f.lev, f.dom)

    def clear_denoms(f):
        """Clear denominators, but keep the ground domain. """
        coeff, F = dmp_clear_denoms(f.rep, f.lev, f.dom)
        return coeff, f.per(F)

    def integrate(f, m=1, j=0):
        """Computes the ``m``-th order indefinite integral of ``f`` in ``x_j``. """
        if not isinstance(m, int):
            raise TypeError("``int`` expected, got %s" % type(m))

        if not isinstance(j, int):
            raise TypeError("``int`` expected, got %s" % type(j))

        return f.per(dmp_integrate_in(f.rep, m, j, f.lev, f.dom))

    def diff(f, m=1, j=0):
        """Computes the ``m``-th order derivative of ``f`` in ``x_j``. """
        if not isinstance(m, int):
            raise TypeError("``int`` expected, got %s" % type(m))

        if not isinstance(j, int):
            raise TypeError("``int`` expected, got %s" % type(j))

        return f.per(dmp_diff_in(f.rep, m, j, f.lev, f.dom))

    def eval(f, a, j=0):
        """Evaluates ``f`` at the given point ``a`` in ``x_j``. """
        if not isinstance(j, int):
            raise TypeError("``int`` expected, got %s" % type(j))

        return f.per(dmp_eval_in(f.rep,
            f.dom.convert(a), j, f.lev, f.dom), kill=True)

    def half_gcdex(f, g):
        """Half extended Euclidean algorithm, if univariate. """
        lev, dom, per, F, G = f.unify(g)

        if not lev:
            s, h = dup_half_gcdex(F, G, dom)
            return per(s), per(h)
        else:
            raise ValueError('univariate polynomial expected')

    def gcdex(f, g):
        """Extended Euclidean algorithm, if univariate. """
        lev, dom, per, F, G = f.unify(g)

        if not lev:
            s, t, h = dup_gcdex(F, G, dom)
            return per(s), per(t), per(h)
        else:
            raise ValueError('univariate polynomial expected')

    def invert(f, g):
        """Invert ``f`` modulo ``g``, if possible. """
        lev, dom, per, F, G = f.unify(g)

        if not lev:
            return per(dup_invert(F, G, dom))
        else:
            raise ValueError('univariate polynomial expected')

    def revert(f, n):
        """Compute ``f**(-1)`` mod ``x**n``. """
        if not f.lev:
            return f.per(dup_revert(f.rep, n, f.dom))
        else:
            raise ValueError('univariate polynomial expected')

    def subresultants(f, g):
        """Computes subresultant PRS sequence of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        R = dmp_subresultants(F, G, lev, dom)
        return list(map(per, R))

    def resultant(f, g, includePRS=False):
        """Computes resultant of ``f`` and ``g`` via PRS. """
        lev, dom, per, F, G = f.unify(g)
        if includePRS:
            res, R = dmp_resultant(F, G, lev, dom, includePRS=includePRS)
            return per(res, kill=True), list(map(per, R))
        return per(dmp_resultant(F, G, lev, dom), kill=True)

    def discriminant(f):
        """Computes discriminant of ``f``. """
        return f.per(dmp_discriminant(f.rep, f.lev, f.dom), kill=True)

    def cofactors(f, g):
        """Returns GCD of ``f`` and ``g`` and their cofactors. """
        lev, dom, per, F, G = f.unify(g)
        h, cff, cfg = dmp_inner_gcd(F, G, lev, dom)
        return per(h), per(cff), per(cfg)

    def gcd(f, g):
        """Returns polynomial GCD of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_gcd(F, G, lev, dom))

    def lcm(f, g):
        """Returns polynomial LCM of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_lcm(F, G, lev, dom))

    def cancel(f, g, include=True):
        """Cancel common factors in a rational function ``f/g``. """
        lev, dom, per, F, G = f.unify(g)

        if include:
            F, G = dmp_cancel(F, G, lev, dom, include=True)
        else:
            cF, cG, F, G = dmp_cancel(F, G, lev, dom, include=False)

        F, G = per(F), per(G)

        if include:
            return F, G
        else:
            return cF, cG, F, G

    def trunc(f, p):
        """Reduce ``f`` modulo a constant ``p``. """
        return f.per(dmp_ground_trunc(f.rep, f.dom.convert(p), f.lev, f.dom))

    def monic(f):
        """Divides all coefficients by ``LC(f)``. """
        return f.per(dmp_ground_monic(f.rep, f.lev, f.dom))

    def content(f):
        """Returns GCD of polynomial coefficients. """
        return dmp_ground_content(f.rep, f.lev, f.dom)

    def primitive(f):
        """Returns content and a primitive form of ``f``. """
        cont, F = dmp_ground_primitive(f.rep, f.lev, f.dom)
        return cont, f.per(F)

    def compose(f, g):
        """Computes functional composition of ``f`` and ``g``. """
        lev, dom, per, F, G = f.unify(g)
        return per(dmp_compose(F, G, lev, dom))

    def decompose(f):
        """Computes functional decomposition of ``f``. """
        if not f.lev:
            return list(map(f.per, dup_decompose(f.rep, f.dom)))
        else:
            raise ValueError('univariate polynomial expected')

    def shift(f, a):
        """Efficiently compute Taylor shift ``f(x + a)``. """
        if not f.lev:
            return f.per(dup_shift(f.rep, f.dom.convert(a), f.dom))
        else:
            raise ValueError('univariate polynomial expected')

    def transform(f, p, q):
        """Evaluate functional transformation ``q**n * f(p/q)``."""
        if f.lev:
            raise ValueError('univariate polynomial expected')

        lev, dom, per, P, Q = p.unify(q)
        lev, dom, per, F, P = f.unify(per(P, dom, lev))
        lev, dom, per, F, Q = per(F, dom, lev).unify(per(Q, dom, lev))

        if not lev:
            return per(dup_transform(F, P, Q, dom))
        else:
            raise ValueError('univariate polynomial expected')

    def sturm(f):
        """Computes the Sturm sequence of ``f``. """
        if not f.lev:
            return list(map(f.per, dup_sturm(f.rep, f.dom)))
        else:
            raise ValueError('univariate polynomial expected')

    def gff_list(f):
        """Computes greatest factorial factorization of ``f``. """
        if not f.lev:
            return [ (f.per(g), k) for g, k in dup_gff_list(f.rep, f.dom) ]
        else:
            raise ValueError('univariate polynomial expected')

    def norm(f):
        """Computes ``Norm(f)``."""
        r = dmp_norm(f.rep, f.lev, f.dom)
        return f.per(r, dom=f.dom.dom)

    def sqf_norm(f):
        """Computes square-free norm of ``f``. """
        s, g, r = dmp_sqf_norm(f.rep, f.lev, f.dom)
        return s, f.per(g), f.per(r, dom=f.dom.dom)

    def sqf_part(f):
        """Computes square-free part of ``f``. """
        return f.per(dmp_sqf_part(f.rep, f.lev, f.dom))

    def sqf_list(f, all=False):
        """Returns a list of square-free factors of ``f``. """
        coeff, factors = dmp_sqf_list(f.rep, f.lev, f.dom, all)
        return coeff, [ (f.per(g), k) for g, k in factors ]

    def sqf_list_include(f, all=False):
        """Returns a list of square-free factors of ``f``. """
        factors = dmp_sqf_list_include(f.rep, f.lev, f.dom, all)
        return [ (f.per(g), k) for g, k in factors ]

    def factor_list(f):
        """Returns a list of irreducible factors of ``f``. """
        coeff, factors = dmp_factor_list(f.rep, f.lev, f.dom)
        return coeff, [ (f.per(g), k) for g, k in factors ]

    def factor_list_include(f):
        """Returns a list of irreducible factors of ``f``. """
        factors = dmp_factor_list_include(f.rep, f.lev, f.dom)
        return [ (f.per(g), k) for g, k in factors ]

    def intervals(f, all=False, eps=None, inf=None, sup=None, fast=False, sqf=False):
        """Compute isolating intervals for roots of ``f``. """
        if not f.lev:
            if not all:
                if not sqf:
                    return dup_isolate_real_roots(f.rep, f.dom, eps=eps, inf=inf, sup=sup, fast=fast)
                else:
                    return dup_isolate_real_roots_sqf(f.rep, f.dom, eps=eps, inf=inf, sup=sup, fast=fast)
            else:
                if not sqf:
                    return dup_isolate_all_roots(f.rep, f.dom, eps=eps, inf=inf, sup=sup, fast=fast)
                else:
                    return dup_isolate_all_roots_sqf(f.rep, f.dom, eps=eps, inf=inf, sup=sup, fast=fast)
        else:
            raise PolynomialError(
                "can't isolate roots of a multivariate polynomial")

    def refine_root(f, s, t, eps=None, steps=None, fast=False):
        """
        Refine an isolating interval to the given precision.

        ``eps`` should be a rational number.

        """
        if not f.lev:
            return dup_refine_real_root(f.rep, s, t, f.dom, eps=eps, steps=steps, fast=fast)
        else:
            raise PolynomialError(
                "can't refine a root of a multivariate polynomial")

    def count_real_roots(f, inf=None, sup=None):
        """Return the number of real roots of ``f`` in ``[inf, sup]``. """
        return dup_count_real_roots(f.rep, f.dom, inf=inf, sup=sup)

    def count_complex_roots(f, inf=None, sup=None):
        """Return the number of complex roots of ``f`` in ``[inf, sup]``. """
        return dup_count_complex_roots(f.rep, f.dom, inf=inf, sup=sup)

    @property
    def is_zero(f):
        """Returns ``True`` if ``f`` is a zero polynomial. """
        return dmp_zero_p(f.rep, f.lev)

    @property
    def is_one(f):
        """Returns ``True`` if ``f`` is a unit polynomial. """
        return dmp_one_p(f.rep, f.lev, f.dom)

    @property
    def is_ground(f):
        """Returns ``True`` if ``f`` is an element of the ground domain. """
        return dmp_ground_p(f.rep, None, f.lev)

    @property
    def is_sqf(f):
        """Returns ``True`` if ``f`` is a square-free polynomial. """
        return dmp_sqf_p(f.rep, f.lev, f.dom)

    @property
    def is_monic(f):
        """Returns ``True`` if the leading coefficient of ``f`` is one. """
        return f.dom.is_one(dmp_ground_LC(f.rep, f.lev, f.dom))

    @property
    def is_primitive(f):
        """Returns ``True`` if the GCD of the coefficients of ``f`` is one. """
        return f.dom.is_one(dmp_ground_content(f.rep, f.lev, f.dom))

    @property
    def is_linear(f):
        """Returns ``True`` if ``f`` is linear in all its variables. """
        return all(sum(monom) <= 1 for monom in dmp_to_dict(f.rep, f.lev, f.dom).keys())

    @property
    def is_quadratic(f):
        """Returns ``True`` if ``f`` is quadratic in all its variables. """
        return all(sum(monom) <= 2 for monom in dmp_to_dict(f.rep, f.lev, f.dom).keys())

    @property
    def is_monomial(f):
        """Returns ``True`` if ``f`` is zero or has only one term. """
        return len(f.to_dict()) <= 1

    @property
    def is_homogeneous(f):
        """Returns ``True`` if ``f`` is a homogeneous polynomial. """
        return f.homogeneous_order() is not None

    @property
    def is_irreducible(f):
        """Returns ``True`` if ``f`` has no factors over its domain. """
        return dmp_irreducible_p(f.rep, f.lev, f.dom)

    @property
    def is_cyclotomic(f):
        """Returns ``True`` if ``f`` is a cyclotomic polynomial. """
        if not f.lev:
            return dup_cyclotomic_p(f.rep, f.dom)
        else:
            return False

    def __abs__(f):
        return f.abs()

    def __neg__(f):
        return f.neg()

    def __add__(f, g):
        if not isinstance(g, DMP):
            try:
                g = f.per(dmp_ground(f.dom.convert(g), f.lev))
            except TypeError:
                return NotImplemented
            except (CoercionFailed, NotImplementedError):
                if f.ring is not None:
                    try:
                        g = f.ring.convert(g)
                    except (CoercionFailed, NotImplementedError):
                        return NotImplemented

        return f.add(g)

    def __radd__(f, g):
        return f.__add__(g)

    def __sub__(f, g):
        if not isinstance(g, DMP):
            try:
                g = f.per(dmp_ground(f.dom.convert(g), f.lev))
            except TypeError:
                return NotImplemented
            except (CoercionFailed, NotImplementedError):
                if f.ring is not None:
                    try:
                        g = f.ring.convert(g)
                    except (CoercionFailed, NotImplementedError):
                        return NotImplemented

        return f.sub(g)

    def __rsub__(f, g):
        return (-f).__add__(g)

    def __mul__(f, g):
        if isinstance(g, DMP):
            return f.mul(g)
        else:
            try:
                return f.mul_ground(g)
            except TypeError:
                return NotImplemented
            except (CoercionFailed, NotImplementedError):
                if f.ring is not None:
                    try:
                        return f.mul(f.ring.convert(g))
                    except (CoercionFailed, NotImplementedError):
                        pass
                return NotImplemented

    def __div__(f, g):
        if isinstance(g, DMP):
            return f.exquo(g)
        else:
            try:
                return f.mul_ground(g)
            except TypeError:
                return NotImplemented
            except (CoercionFailed, NotImplementedError):
                if f.ring is not None:
                    try:
                        return f.exquo(f.ring.convert(g))
                    except (CoercionFailed, NotImplementedError):
                        pass
                return NotImplemented

    def __rdiv__(f, g):
        if isinstance(g, DMP):
            return g.exquo(f)
        elif f.ring is not None:
            try:
                return f.ring.convert(g).exquo(f)
            except (CoercionFailed, NotImplementedError):
                pass
        return NotImplemented

    __truediv__ = __div__
    __rtruediv__ = __rdiv__

    def __rmul__(f, g):
        return f.__mul__(g)

    def __pow__(f, n):
        return f.pow(n)

    def __divmod__(f, g):
        return f.div(g)

    def __mod__(f, g):
        return f.rem(g)

    def __floordiv__(f, g):
        if isinstance(g, DMP):
            return f.quo(g)
        else:
            try:
                return f.quo_ground(g)
            except TypeError:
                return NotImplemented

    def __eq__(f, g):
        try:
            _, _, _, F, G = f.unify(g)

            if f.lev == g.lev:
                return F == G
        except UnificationFailed:
            pass

        return False

    def __ne__(f, g):
        return not f == g

    def eq(f, g, strict=False):
        if not strict:
            return f == g
        else:
            return f._strict_eq(g)

    def ne(f, g, strict=False):
        return not f.eq(g, strict=strict)

    def _strict_eq(f, g):
        return isinstance(g, f.__class__) and f.lev == g.lev \
            and f.dom == g.dom \
            and f.rep == g.rep

    def __lt__(f, g):
        _, _, _, F, G = f.unify(g)
        return F < G

    def __le__(f, g):
        _, _, _, F, G = f.unify(g)
        return F <= G

    def __gt__(f, g):
        _, _, _, F, G = f.unify(g)
        return F > G

    def __ge__(f, g):
        _, _, _, F, G = f.unify(g)
        return F >= G

    def __nonzero__(f):
        return not dmp_zero_p(f.rep, f.lev)

    __bool__ = __nonzero__


def init_normal_DMF(num, den, lev, dom):
    return DMF(dmp_normal(num, lev, dom),
               dmp_normal(den, lev, dom), dom, lev)


class DMF(PicklableWithSlots, CantSympify):
    """Dense Multivariate Fractions over `K`. """

    __slots__ = ['num', 'den', 'lev', 'dom', 'ring']

    def __init__(self, rep, dom, lev=None, ring=None):
        num, den, lev = self._parse(rep, dom, lev)
        num, den = dmp_cancel(num, den, lev, dom)

        self.num = num
        self.den = den
        self.lev = lev
        self.dom = dom
        self.ring = ring

    @classmethod
    def new(cls, rep, dom, lev=None, ring=None):
        num, den, lev = cls._parse(rep, dom, lev)

        obj = object.__new__(cls)

        obj.num = num
        obj.den = den
        obj.lev = lev
        obj.dom = dom
        obj.ring = ring

        return obj

    @classmethod
    def _parse(cls, rep, dom, lev=None):
        if type(rep) is tuple:
            num, den = rep

            if lev is not None:
                if type(num) is dict:
                    num = dmp_from_dict(num, lev, dom)

                if type(den) is dict:
                    den = dmp_from_dict(den, lev, dom)
            else:
                num, num_lev = dmp_validate(num)
                den, den_lev = dmp_validate(den)

                if num_lev == den_lev:
                    lev = num_lev
                else:
                    raise ValueError('inconsistent number of levels')

            if dmp_zero_p(den, lev):
                raise ZeroDivisionError('fraction denominator')

            if dmp_zero_p(num, lev):
                den = dmp_one(lev, dom)
            else:
                if dmp_negative_p(den, lev, dom):
                    num = dmp_neg(num, lev, dom)
                    den = dmp_neg(den, lev, dom)
        else:
            num = rep

            if lev is not None:
                if type(num) is dict:
                    num = dmp_from_dict(num, lev, dom)
                elif type(num) is not list:
                    num = dmp_ground(dom.convert(num), lev)
            else:
                num, lev = dmp_validate(num)

            den = dmp_one(lev, dom)

        return num, den, lev

    def __repr__(f):
        return "%s((%s, %s), %s, %s)" % (f.__class__.__name__, f.num, f.den,
                                         f.dom, f.ring)

    def __hash__(f):
        return hash((f.__class__.__name__, dmp_to_tuple(f.num, f.lev),
            dmp_to_tuple(f.den, f.lev), f.lev, f.dom, f.ring))

    def poly_unify(f, g):
        """Unify a multivariate fraction and a polynomial. """
        if not isinstance(g, DMP) or f.lev != g.lev:
            raise UnificationFailed("can't unify %s with %s" % (f, g))

        if f.dom == g.dom and f.ring == g.ring:
            return (f.lev, f.dom, f.per, (f.num, f.den), g.rep)
        else:
            lev, dom = f.lev, f.dom.unify(g.dom)
            ring = f.ring
            if g.ring is not None:
                if ring is not None:
                    ring = ring.unify(g.ring)
                else:
                    ring = g.ring

            F = (dmp_convert(f.num, lev, f.dom, dom),
                 dmp_convert(f.den, lev, f.dom, dom))

            G = dmp_convert(g.rep, lev, g.dom, dom)

            def per(num, den, cancel=True, kill=False, lev=lev):
                if kill:
                    if not lev:
                        return num/den
                    else:
                        lev = lev - 1

                if cancel:
                    num, den = dmp_cancel(num, den, lev, dom)

                return f.__class__.new((num, den), dom, lev, ring=ring)

            return lev, dom, per, F, G

    def frac_unify(f, g):
        """Unify representations of two multivariate fractions. """
        if not isinstance(g, DMF) or f.lev != g.lev:
            raise UnificationFailed("can't unify %s with %s" % (f, g))

        if f.dom == g.dom and f.ring == g.ring:
            return (f.lev, f.dom, f.per, (f.num, f.den),
                                         (g.num, g.den))
        else:
            lev, dom = f.lev, f.dom.unify(g.dom)
            ring = f.ring
            if g.ring is not None:
                if ring is not None:
                    ring = ring.unify(g.ring)
                else:
                    ring = g.ring

            F = (dmp_convert(f.num, lev, f.dom, dom),
                 dmp_convert(f.den, lev, f.dom, dom))

            G = (dmp_convert(g.num, lev, g.dom, dom),
                 dmp_convert(g.den, lev, g.dom, dom))

            def per(num, den, cancel=True, kill=False, lev=lev):
                if kill:
                    if not lev:
                        return num/den
                    else:
                        lev = lev - 1

                if cancel:
                    num, den = dmp_cancel(num, den, lev, dom)

                return f.__class__.new((num, den), dom, lev, ring=ring)

            return lev, dom, per, F, G

    def per(f, num, den, cancel=True, kill=False, ring=None):
        """Create a DMF out of the given representation. """
        lev, dom = f.lev, f.dom

        if kill:
            if not lev:
                return num/den
            else:
                lev -= 1

        if cancel:
            num, den = dmp_cancel(num, den, lev, dom)

        if ring is None:
            ring = f.ring

        return f.__class__.new((num, den), dom, lev, ring=ring)

    def half_per(f, rep, kill=False):
        """Create a DMP out of the given representation. """
        lev = f.lev

        if kill:
            if not lev:
                return rep
            else:
                lev -= 1

        return DMP(rep, f.dom, lev)

    @classmethod
    def zero(cls, lev, dom, ring=None):
        return cls.new(0, dom, lev, ring=ring)

    @classmethod
    def one(cls, lev, dom, ring=None):
        return cls.new(1, dom, lev, ring=ring)

    def numer(f):
        """Returns the numerator of ``f``. """
        return f.half_per(f.num)

    def denom(f):
        """Returns the denominator of ``f``. """
        return f.half_per(f.den)

    def cancel(f):
        """Remove common factors from ``f.num`` and ``f.den``. """
        return f.per(f.num, f.den)

    def neg(f):
        """Negate all coefficients in ``f``. """
        return f.per(dmp_neg(f.num, f.lev, f.dom), f.den, cancel=False)

    def add(f, g):
        """Add two multivariate fractions ``f`` and ``g``. """
        if isinstance(g, DMP):
            lev, dom, per, (F_num, F_den), G = f.poly_unify(g)
            num, den = dmp_add_mul(F_num, F_den, G, lev, dom), F_den
        else:
            lev, dom, per, F, G = f.frac_unify(g)
            (F_num, F_den), (G_num, G_den) = F, G

            num = dmp_add(dmp_mul(F_num, G_den, lev, dom),
                          dmp_mul(F_den, G_num, lev, dom), lev, dom)
            den = dmp_mul(F_den, G_den, lev, dom)

        return per(num, den)

    def sub(f, g):
        """Subtract two multivariate fractions ``f`` and ``g``. """
        if isinstance(g, DMP):
            lev, dom, per, (F_num, F_den), G = f.poly_unify(g)
            num, den = dmp_sub_mul(F_num, F_den, G, lev, dom), F_den
        else:
            lev, dom, per, F, G = f.frac_unify(g)
            (F_num, F_den), (G_num, G_den) = F, G

            num = dmp_sub(dmp_mul(F_num, G_den, lev, dom),
                          dmp_mul(F_den, G_num, lev, dom), lev, dom)
            den = dmp_mul(F_den, G_den, lev, dom)

        return per(num, den)

    def mul(f, g):
        """Multiply two multivariate fractions ``f`` and ``g``. """
        if isinstance(g, DMP):
            lev, dom, per, (F_num, F_den), G = f.poly_unify(g)
            num, den = dmp_mul(F_num, G, lev, dom), F_den
        else:
            lev, dom, per, F, G = f.frac_unify(g)
            (F_num, F_den), (G_num, G_den) = F, G

            num = dmp_mul(F_num, G_num, lev, dom)
            den = dmp_mul(F_den, G_den, lev, dom)

        return per(num, den)

    def pow(f, n):
        """Raise ``f`` to a non-negative power ``n``. """
        if isinstance(n, int):
            return f.per(dmp_pow(f.num, n, f.lev, f.dom),
                         dmp_pow(f.den, n, f.lev, f.dom), cancel=False)
        else:
            raise TypeError("``int`` expected, got %s" % type(n))

    def quo(f, g):
        """Computes quotient of fractions ``f`` and ``g``. """
        if isinstance(g, DMP):
            lev, dom, per, (F_num, F_den), G = f.poly_unify(g)
            num, den = F_num, dmp_mul(F_den, G, lev, dom)
        else:
            lev, dom, per, F, G = f.frac_unify(g)
            (F_num, F_den), (G_num, G_den) = F, G

            num = dmp_mul(F_num, G_den, lev, dom)
            den = dmp_mul(F_den, G_num, lev, dom)

        res = per(num, den)
        if f.ring is not None and res not in f.ring:
            from sympy.polys.polyerrors import ExactQuotientFailed
            raise ExactQuotientFailed(f, g, f.ring)
        return res

    exquo = quo

    def invert(f, check=True):
        """Computes inverse of a fraction ``f``. """
        if check and f.ring is not None and not f.ring.is_unit(f):
            raise NotReversible(f, f.ring)
        res = f.per(f.den, f.num, cancel=False)
        return res

    @property
    def is_zero(f):
        """Returns ``True`` if ``f`` is a zero fraction. """
        return dmp_zero_p(f.num, f.lev)

    @property
    def is_one(f):
        """Returns ``True`` if ``f`` is a unit fraction. """
        return dmp_one_p(f.num, f.lev, f.dom) and \
            dmp_one_p(f.den, f.lev, f.dom)

    def __neg__(f):
        return f.neg()

    def __add__(f, g):
        if isinstance(g, (DMP, DMF)):
            return f.add(g)

        try:
            return f.add(f.half_per(g))
        except TypeError:
            return NotImplemented
        except (CoercionFailed, NotImplementedError):
            if f.ring is not None:
                try:
                    return f.add(f.ring.convert(g))
                except (CoercionFailed, NotImplementedError):
                    pass
            return NotImplemented

    def __radd__(f, g):
        return f.__add__(g)

    def __sub__(f, g):
        if isinstance(g, (DMP, DMF)):
            return f.sub(g)

        try:
            return f.sub(f.half_per(g))
        except TypeError:
            return NotImplemented
        except (CoercionFailed, NotImplementedError):
            if f.ring is not None:
                try:
                    return f.sub(f.ring.convert(g))
                except (CoercionFailed, NotImplementedError):
                    pass
            return NotImplemented

    def __rsub__(f, g):
        return (-f).__add__(g)

    def __mul__(f, g):
        if isinstance(g, (DMP, DMF)):
            return f.mul(g)

        try:
            return f.mul(f.half_per(g))
        except TypeError:
            return NotImplemented
        except (CoercionFailed, NotImplementedError):
            if f.ring is not None:
                try:
                    return f.mul(f.ring.convert(g))
                except (CoercionFailed, NotImplementedError):
                    pass
            return NotImplemented

    def __rmul__(f, g):
        return f.__mul__(g)

    def __pow__(f, n):
        return f.pow(n)

    def __div__(f, g):
        if isinstance(g, (DMP, DMF)):
            return f.quo(g)

        try:
            return f.quo(f.half_per(g))
        except TypeError:
            return NotImplemented
        except (CoercionFailed, NotImplementedError):
            if f.ring is not None:
                try:
                    return f.quo(f.ring.convert(g))
                except (CoercionFailed, NotImplementedError):
                    pass
            return NotImplemented

    def __rdiv__(self, g):
        r = self.invert(check=False)*g
        if self.ring and r not in self.ring:
            from sympy.polys.polyerrors import ExactQuotientFailed
            raise ExactQuotientFailed(g, self, self.ring)
        return r

    __truediv__ = __div__
    __rtruediv__ = __rdiv__

    def __eq__(f, g):
        try:
            if isinstance(g, DMP):
                _, _, _, (F_num, F_den), G = f.poly_unify(g)

                if f.lev == g.lev:
                    return dmp_one_p(F_den, f.lev, f.dom) and F_num == G
            else:
                _, _, _, F, G = f.frac_unify(g)

                if f.lev == g.lev:
                    return F == G
        except UnificationFailed:
            pass

        return False

    def __ne__(f, g):
        try:
            if isinstance(g, DMP):
                _, _, _, (F_num, F_den), G = f.poly_unify(g)

                if f.lev == g.lev:
                    return not (dmp_one_p(F_den, f.lev, f.dom) and F_num == G)
            else:
                _, _, _, F, G = f.frac_unify(g)

                if f.lev == g.lev:
                    return F != G
        except UnificationFailed:
            pass

        return True

    def __lt__(f, g):
        _, _, _, F, G = f.frac_unify(g)
        return F < G

    def __le__(f, g):
        _, _, _, F, G = f.frac_unify(g)
        return F <= G

    def __gt__(f, g):
        _, _, _, F, G = f.frac_unify(g)
        return F > G

    def __ge__(f, g):
        _, _, _, F, G = f.frac_unify(g)
        return F >= G

    def __nonzero__(f):
        return not dmp_zero_p(f.num, f.lev)

    __bool__ = __nonzero__


def init_normal_ANP(rep, mod, dom):
    return ANP(dup_normal(rep, dom),
               dup_normal(mod, dom), dom)


class ANP(PicklableWithSlots, CantSympify):
    """Dense Algebraic Number Polynomials over a field. """

    __slots__ = ['rep', 'mod', 'dom']

    def __init__(self, rep, mod, dom):
        if type(rep) is dict:
            self.rep = dup_from_dict(rep, dom)
        else:
            if type(rep) is not list:
                rep = [dom.convert(rep)]

            self.rep = dup_strip(rep)

        if isinstance(mod, DMP):
            self.mod = mod.rep
        else:
            if type(mod) is dict:
                self.mod = dup_from_dict(mod, dom)
            else:
                self.mod = dup_strip(mod)

        self.dom = dom

    def __repr__(f):
        return "%s(%s, %s, %s)" % (f.__class__.__name__, f.rep, f.mod, f.dom)

    def __hash__(f):
        return hash((f.__class__.__name__, f.to_tuple(), dmp_to_tuple(f.mod, 0), f.dom))

    def unify(f, g):
        """Unify representations of two algebraic numbers. """
        if not isinstance(g, ANP) or f.mod != g.mod:
            raise UnificationFailed("can't unify %s with %s" % (f, g))

        if f.dom == g.dom:
            return f.dom, f.per, f.rep, g.rep, f.mod
        else:
            dom = f.dom.unify(g.dom)

            F = dup_convert(f.rep, f.dom, dom)
            G = dup_convert(g.rep, g.dom, dom)

            if dom != f.dom and dom != g.dom:
                mod = dup_convert(f.mod, f.dom, dom)
            else:
                if dom == f.dom:
                    mod = f.mod
                else:
                    mod = g.mod

            per = lambda rep: ANP(rep, mod, dom)

        return dom, per, F, G, mod

    def per(f, rep, mod=None, dom=None):
        return ANP(rep, mod or f.mod, dom or f.dom)

    @classmethod
    def zero(cls, mod, dom):
        return ANP(0, mod, dom)

    @classmethod
    def one(cls, mod, dom):
        return ANP(1, mod, dom)

    def to_dict(f):
        """Convert ``f`` to a dict representation with native coefficients. """
        return dmp_to_dict(f.rep, 0, f.dom)

    def to_sympy_dict(f):
        """Convert ``f`` to a dict representation with SymPy coefficients. """
        rep = dmp_to_dict(f.rep, 0, f.dom)

        for k, v in rep.items():
            rep[k] = f.dom.to_sympy(v)

        return rep

    def to_list(f):
        """Convert ``f`` to a list representation with native coefficients. """
        return f.rep

    def to_sympy_list(f):
        """Convert ``f`` to a list representation with SymPy coefficients. """
        return [ f.dom.to_sympy(c) for c in f.rep ]

    def to_tuple(f):
        """
        Convert ``f`` to a tuple representation with native coefficients.

        This is needed for hashing.
        """
        return dmp_to_tuple(f.rep, 0)

    @classmethod
    def from_list(cls, rep, mod, dom):
        return ANP(dup_strip(list(map(dom.convert, rep))), mod, dom)

    def neg(f):
        return f.per(dup_neg(f.rep, f.dom))

    def add(f, g):
        dom, per, F, G, mod = f.unify(g)
        return per(dup_add(F, G, dom))

    def sub(f, g):
        dom, per, F, G, mod = f.unify(g)
        return per(dup_sub(F, G, dom))

    def mul(f, g):
        dom, per, F, G, mod = f.unify(g)
        return per(dup_rem(dup_mul(F, G, dom), mod, dom))

    def pow(f, n):
        """Raise ``f`` to a non-negative power ``n``. """
        if isinstance(n, int):
            if n < 0:
                F, n = dup_invert(f.rep, f.mod, f.dom), -n
            else:
                F = f.rep

            return f.per(dup_rem(dup_pow(F, n, f.dom), f.mod, f.dom))
        else:
            raise TypeError("``int`` expected, got %s" % type(n))

    def div(f, g):
        dom, per, F, G, mod = f.unify(g)
        return (per(dup_rem(dup_mul(F, dup_invert(G, mod, dom), dom), mod, dom)), f.zero(mod, dom))

    def rem(f, g):
        dom, _, _, G, mod = f.unify(g)

        s, h = dup_half_gcdex(G, mod, dom)

        if h == [dom.one]:
            return f.zero(mod, dom)
        else:
            raise NotInvertible("zero divisor")

    def quo(f, g):
        dom, per, F, G, mod = f.unify(g)
        return per(dup_rem(dup_mul(F, dup_invert(G, mod, dom), dom), mod, dom))

    exquo = quo

    def LC(f):
        """Returns the leading coefficient of ``f``. """
        return dup_LC(f.rep, f.dom)

    def TC(f):
        """Returns the trailing coefficient of ``f``. """
        return dup_TC(f.rep, f.dom)

    @property
    def is_zero(f):
        """Returns ``True`` if ``f`` is a zero algebraic number. """
        return not f

    @property
    def is_one(f):
        """Returns ``True`` if ``f`` is a unit algebraic number. """
        return f.rep == [f.dom.one]

    @property
    def is_ground(f):
        """Returns ``True`` if ``f`` is an element of the ground domain. """
        return not f.rep or len(f.rep) == 1

    def __neg__(f):
        return f.neg()

    def __add__(f, g):
        if isinstance(g, ANP):
            return f.add(g)
        else:
            try:
                return f.add(f.per(g))
            except (CoercionFailed, TypeError):
                return NotImplemented

    def __radd__(f, g):
        return f.__add__(g)

    def __sub__(f, g):
        if isinstance(g, ANP):
            return f.sub(g)
        else:
            try:
                return f.sub(f.per(g))
            except (CoercionFailed, TypeError):
                return NotImplemented

    def __rsub__(f, g):
        return (-f).__add__(g)

    def __mul__(f, g):
        if isinstance(g, ANP):
            return f.mul(g)
        else:
            try:
                return f.mul(f.per(g))
            except (CoercionFailed, TypeError):
                return NotImplemented

    def __rmul__(f, g):
        return f.__mul__(g)

    def __pow__(f, n):
        return f.pow(n)

    def __divmod__(f, g):
        return f.div(g)

    def __mod__(f, g):
        return f.rem(g)

    def __div__(f, g):
        if isinstance(g, ANP):
            return f.quo(g)
        else:
            try:
                return f.quo(f.per(g))
            except (CoercionFailed, TypeError):
                return NotImplemented

    __truediv__ = __div__

    def __eq__(f, g):
        try:
            _, _, F, G, _ = f.unify(g)

            return F == G
        except UnificationFailed:
            return False

    def __ne__(f, g):
        try:
            _, _, F, G, _ = f.unify(g)

            return F != G
        except UnificationFailed:
            return True

    def __lt__(f, g):
        _, _, F, G, _ = f.unify(g)
        return F < G

    def __le__(f, g):
        _, _, F, G, _ = f.unify(g)
        return F <= G

    def __gt__(f, g):
        _, _, F, G, _ = f.unify(g)
        return F > G

    def __ge__(f, g):
        _, _, F, G, _ = f.unify(g)
        return F >= G

    def __nonzero__(f):
        return bool(f.rep)

    __bool__ = __nonzero__
