"""Tools for constructing domains for expressions. """

from __future__ import print_function, division

from sympy.core import sympify
from sympy.polys.domains import ZZ, QQ, EX
from sympy.polys.domains.realfield import RealField
from sympy.polys.polyoptions import build_options
from sympy.polys.polyutils import parallel_dict_from_basic
from sympy.utilities import public


def _construct_simple(coeffs, opt):
    """Handle simple domains, e.g.: ZZ, QQ, RR and algebraic domains. """
    result, rationals, reals, algebraics = {}, False, False, False

    if opt.extension is True:
        is_algebraic = lambda coeff: coeff.is_number and coeff.is_algebraic
    else:
        is_algebraic = lambda coeff: False

    # XXX: add support for a + b*I coefficients
    for coeff in coeffs:
        if coeff.is_Rational:
            if not coeff.is_Integer:
                rationals = True
        elif coeff.is_Float:
            if not algebraics:
                reals = True
            else:
                # there are both reals and algebraics -> EX
                return False
        elif is_algebraic(coeff):
            if not reals:
                algebraics = True
            else:
                # there are both algebraics and reals -> EX
                return False
        else:
            # this is a composite domain, e.g. ZZ[X], EX
            return None

    if algebraics:
        domain, result = _construct_algebraic(coeffs, opt)
    else:
        if reals:
            # Use the maximum precision of all coefficients for the RR's
            # precision
            max_prec = max([c._prec for c in coeffs])
            domain = RealField(prec=max_prec)
        else:
            if opt.field or rationals:
                domain = QQ
            else:
                domain = ZZ

        result = []

        for coeff in coeffs:
            result.append(domain.from_sympy(coeff))

    return domain, result


def _construct_algebraic(coeffs, opt):
    """We know that coefficients are algebraic so construct the extension. """
    from sympy.polys.numberfields import primitive_element

    result, exts = [], set([])

    for coeff in coeffs:
        if coeff.is_Rational:
            coeff = (None, 0, QQ.from_sympy(coeff))
        else:
            a = coeff.as_coeff_add()[0]
            coeff -= a

            b = coeff.as_coeff_mul()[0]
            coeff /= b

            exts.add(coeff)

            a = QQ.from_sympy(a)
            b = QQ.from_sympy(b)

            coeff = (coeff, b, a)

        result.append(coeff)

    exts = list(exts)

    g, span, H = primitive_element(exts, ex=True, polys=True)
    root = sum([ s*ext for s, ext in zip(span, exts) ])

    domain, g = QQ.algebraic_field((g, root)), g.rep.rep

    for i, (coeff, a, b) in enumerate(result):
        if coeff is not None:
            coeff = a*domain.dtype.from_list(H[exts.index(coeff)], g, QQ) + b
        else:
            coeff = domain.dtype.from_list([b], g, QQ)

        result[i] = coeff

    return domain, result


def _construct_composite(coeffs, opt):
    """Handle composite domains, e.g.: ZZ[X], QQ[X], ZZ(X), QQ(X). """
    numers, denoms = [], []

    for coeff in coeffs:
        numer, denom = coeff.as_numer_denom()

        numers.append(numer)
        denoms.append(denom)

    polys, gens = parallel_dict_from_basic(numers + denoms)  # XXX: sorting
    if not gens:
        return None

    if opt.composite is None:
        if any(gen.is_number and gen.is_algebraic for gen in gens):
            return None # generators are number-like so lets better use EX

        all_symbols = set([])

        for gen in gens:
            symbols = gen.free_symbols

            if all_symbols & symbols:
                return None # there could be algebraic relations between generators
            else:
                all_symbols |= symbols

    n = len(gens)
    k = len(polys)//2

    numers = polys[:k]
    denoms = polys[k:]

    if opt.field:
        fractions = True
    else:
        fractions, zeros = False, (0,)*n

        for denom in denoms:
            if len(denom) > 1 or zeros not in denom:
                fractions = True
                break

    coeffs = set([])

    if not fractions:
        for numer, denom in zip(numers, denoms):
            denom = denom[zeros]

            for monom, coeff in numer.items():
                coeff /= denom
                coeffs.add(coeff)
                numer[monom] = coeff
    else:
        for numer, denom in zip(numers, denoms):
            coeffs.update(list(numer.values()))
            coeffs.update(list(denom.values()))

    rationals, reals = False, False

    for coeff in coeffs:
        if coeff.is_Rational:
            if not coeff.is_Integer:
                rationals = True
        elif coeff.is_Float:
            reals = True
            break

    if reals:
        max_prec = max([c._prec for c in coeffs])
        ground = RealField(prec=max_prec)
    elif rationals:
        ground = QQ
    else:
        ground = ZZ

    result = []

    if not fractions:
        domain = ground.poly_ring(*gens)

        for numer in numers:
            for monom, coeff in numer.items():
                numer[monom] = ground.from_sympy(coeff)

            result.append(domain(numer))
    else:
        domain = ground.frac_field(*gens)

        for numer, denom in zip(numers, denoms):
            for monom, coeff in numer.items():
                numer[monom] = ground.from_sympy(coeff)

            for monom, coeff in denom.items():
                denom[monom] = ground.from_sympy(coeff)

            result.append(domain((numer, denom)))

    return domain, result


def _construct_expression(coeffs, opt):
    """The last resort case, i.e. use the expression domain. """
    domain, result = EX, []

    for coeff in coeffs:
        result.append(domain.from_sympy(coeff))

    return domain, result


@public
def construct_domain(obj, **args):
    """Construct a minimal domain for the list of coefficients. """
    opt = build_options(args)

    if hasattr(obj, '__iter__'):
        if isinstance(obj, dict):
            if not obj:
                monoms, coeffs = [], []
            else:
                monoms, coeffs = list(zip(*list(obj.items())))
        else:
            coeffs = obj
    else:
        coeffs = [obj]

    coeffs = list(map(sympify, coeffs))
    result = _construct_simple(coeffs, opt)

    if result is not None:
        if result is not False:
            domain, coeffs = result
        else:
            domain, coeffs = _construct_expression(coeffs, opt)
    else:
        if opt.composite is False:
            result = None
        else:
            result = _construct_composite(coeffs, opt)

        if result is not None:
            domain, coeffs = result
        else:
            domain, coeffs = _construct_expression(coeffs, opt)

    if hasattr(obj, '__iter__'):
        if isinstance(obj, dict):
            return domain, dict(list(zip(monoms, coeffs)))
        else:
            return domain, coeffs
    else:
        return domain, coeffs[0]
