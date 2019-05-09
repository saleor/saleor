""" Integral Transforms """

from __future__ import print_function, division

from sympy.core import S
from sympy.core.compatibility import reduce, range, iterable
from sympy.core.function import Function
from sympy.core.relational import _canonical, Ge, Gt
from sympy.core.numbers import oo
from sympy.core.symbol import Dummy
from sympy.integrals import integrate, Integral
from sympy.integrals.meijerint import _dummy
from sympy.logic.boolalg import to_cnf, conjuncts, disjuncts, Or, And
from sympy.simplify import simplify
from sympy.utilities import default_sort_key
from sympy.matrices.matrices import MatrixBase


##########################################################################
# Helpers / Utilities
##########################################################################


class IntegralTransformError(NotImplementedError):
    """
    Exception raised in relation to problems computing transforms.

    This class is mostly used internally; if integrals cannot be computed
    objects representing unevaluated transforms are usually returned.

    The hint ``needeval=True`` can be used to disable returning transform
    objects, and instead raise this exception if an integral cannot be
    computed.
    """
    def __init__(self, transform, function, msg):
        super(IntegralTransformError, self).__init__(
            "%s Transform could not be computed: %s." % (transform, msg))
        self.function = function


class IntegralTransform(Function):
    """
    Base class for integral transforms.

    This class represents unevaluated transforms.

    To implement a concrete transform, derive from this class and implement
    the _compute_transform(f, x, s, **hints) and _as_integral(f, x, s)
    functions. If the transform cannot be computed, raise IntegralTransformError.

    Also set cls._name.

    Implement self._collapse_extra if your function returns more than just a
    number and possibly a convergence condition.
    """

    @property
    def function(self):
        """ The function to be transformed. """
        return self.args[0]

    @property
    def function_variable(self):
        """ The dependent variable of the function to be transformed. """
        return self.args[1]

    @property
    def transform_variable(self):
        """ The independent transform variable. """
        return self.args[2]

    @property
    def free_symbols(self):
        """
        This method returns the symbols that will exist when the transform
        is evaluated.
        """
        return self.function.free_symbols.union({self.transform_variable}) \
            - {self.function_variable}

    def _compute_transform(self, f, x, s, **hints):
        raise NotImplementedError

    def _as_integral(self, f, x, s):
        raise NotImplementedError

    def _collapse_extra(self, extra):
        cond = And(*extra)
        if cond == False:
            raise IntegralTransformError(self.__class__.name, None, '')
        return cond

    def doit(self, **hints):
        """
        Try to evaluate the transform in closed form.

        This general function handles linearity, but apart from that leaves
        pretty much everything to _compute_transform.

        Standard hints are the following:

        - ``simplify``: whether or not to simplify the result
        - ``noconds``: if True, don't return convergence conditions
        - ``needeval``: if True, raise IntegralTransformError instead of
                        returning IntegralTransform objects

        The default values of these hints depend on the concrete transform,
        usually the default is
        ``(simplify, noconds, needeval) = (True, False, False)``.
        """
        from sympy import Add, expand_mul, Mul
        from sympy.core.function import AppliedUndef
        needeval = hints.pop('needeval', False)
        try_directly = not any(func.has(self.function_variable)
                               for func in self.function.atoms(AppliedUndef))
        if try_directly:
            try:
                return self._compute_transform(self.function,
                    self.function_variable, self.transform_variable, **hints)
            except IntegralTransformError:
                pass

        fn = self.function
        if not fn.is_Add:
            fn = expand_mul(fn)

        if fn.is_Add:
            hints['needeval'] = needeval
            res = [self.__class__(*([x] + list(self.args[1:]))).doit(**hints)
                   for x in fn.args]
            extra = []
            ress = []
            for x in res:
                if not isinstance(x, tuple):
                    x = [x]
                ress.append(x[0])
                if len(x) == 2:
                    # only a condition
                    extra.append(x[1])
                elif len(x) > 2:
                    # some region parameters and a condition (Mellin, Laplace)
                    extra += [x[1:]]
            res = Add(*ress)
            if not extra:
                return res
            try:
                extra = self._collapse_extra(extra)
                if iterable(extra):
                    return tuple([res]) + tuple(extra)
                else:
                    return (res, extra)
            except IntegralTransformError:
                pass

        if needeval:
            raise IntegralTransformError(
                self.__class__._name, self.function, 'needeval')

        # TODO handle derivatives etc

        # pull out constant coefficients
        coeff, rest = fn.as_coeff_mul(self.function_variable)
        return coeff*self.__class__(*([Mul(*rest)] + list(self.args[1:])))

    @property
    def as_integral(self):
        return self._as_integral(self.function, self.function_variable,
                                 self.transform_variable)

    def _eval_rewrite_as_Integral(self, *args, **kwargs):
        return self.as_integral

from sympy.solvers.inequalities import _solve_inequality


def _simplify(expr, doit):
    from sympy import powdenest, piecewise_fold
    if doit:
        return simplify(powdenest(piecewise_fold(expr), polar=True))
    return expr


def _noconds_(default):
    """
    This is a decorator generator for dropping convergence conditions.

    Suppose you define a function ``transform(*args)`` which returns a tuple of
    the form ``(result, cond1, cond2, ...)``.

    Decorating it ``@_noconds_(default)`` will add a new keyword argument
    ``noconds`` to it. If ``noconds=True``, the return value will be altered to
    be only ``result``, whereas if ``noconds=False`` the return value will not
    be altered.

    The default value of the ``noconds`` keyword will be ``default`` (i.e. the
    argument of this function).
    """
    def make_wrapper(func):
        from sympy.core.decorators import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            noconds = kwargs.pop('noconds', default)
            res = func(*args, **kwargs)
            if noconds:
                return res[0]
            return res
        return wrapper
    return make_wrapper
_noconds = _noconds_(False)


##########################################################################
# Mellin Transform
##########################################################################

def _default_integrator(f, x):
    return integrate(f, (x, 0, oo))


@_noconds
def _mellin_transform(f, x, s_, integrator=_default_integrator, simplify=True):
    """ Backend function to compute Mellin transforms. """
    from sympy import re, Max, Min, count_ops
    # We use a fresh dummy, because assumptions on s might drop conditions on
    # convergence of the integral.
    s = _dummy('s', 'mellin-transform', f)
    F = integrator(x**(s - 1) * f, x)

    if not F.has(Integral):
        return _simplify(F.subs(s, s_), simplify), (-oo, oo), S.true

    if not F.is_Piecewise:  # XXX can this work if integration gives continuous result now?
        raise IntegralTransformError('Mellin', f, 'could not compute integral')

    F, cond = F.args[0]
    if F.has(Integral):
        raise IntegralTransformError(
            'Mellin', f, 'integral in unexpected form')

    def process_conds(cond):
        """
        Turn ``cond`` into a strip (a, b), and auxiliary conditions.
        """
        a = -oo
        b = oo
        aux = S.true
        conds = conjuncts(to_cnf(cond))
        t = Dummy('t', real=True)
        for c in conds:
            a_ = oo
            b_ = -oo
            aux_ = []
            for d in disjuncts(c):
                d_ = d.replace(
                    re, lambda x: x.as_real_imag()[0]).subs(re(s), t)
                if not d.is_Relational or \
                    d.rel_op in ('==', '!=') \
                        or d_.has(s) or not d_.has(t):
                    aux_ += [d]
                    continue
                soln = _solve_inequality(d_, t)
                if not soln.is_Relational or \
                        soln.rel_op in ('==', '!='):
                    aux_ += [d]
                    continue
                if soln.lts == t:
                    b_ = Max(soln.gts, b_)
                else:
                    a_ = Min(soln.lts, a_)
            if a_ != oo and a_ != b:
                a = Max(a_, a)
            elif b_ != -oo and b_ != a:
                b = Min(b_, b)
            else:
                aux = And(aux, Or(*aux_))
        return a, b, aux

    conds = [process_conds(c) for c in disjuncts(cond)]
    conds = [x for x in conds if x[2] != False]
    conds.sort(key=lambda x: (x[0] - x[1], count_ops(x[2])))

    if not conds:
        raise IntegralTransformError('Mellin', f, 'no convergence found')

    a, b, aux = conds[0]
    return _simplify(F.subs(s, s_), simplify), (a, b), aux


class MellinTransform(IntegralTransform):
    """
    Class representing unevaluated Mellin transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute Mellin transforms, see the :func:`mellin_transform`
    docstring.
    """

    _name = 'Mellin'

    def _compute_transform(self, f, x, s, **hints):
        return _mellin_transform(f, x, s, **hints)

    def _as_integral(self, f, x, s):
        return Integral(f*x**(s - 1), (x, 0, oo))

    def _collapse_extra(self, extra):
        from sympy import Max, Min
        a = []
        b = []
        cond = []
        for (sa, sb), c in extra:
            a += [sa]
            b += [sb]
            cond += [c]
        res = (Max(*a), Min(*b)), And(*cond)
        if (res[0][0] >= res[0][1]) == True or res[1] == False:
            raise IntegralTransformError(
                'Mellin', None, 'no combined convergence.')
        return res


def mellin_transform(f, x, s, **hints):
    r"""
    Compute the Mellin transform `F(s)` of `f(x)`,

    .. math :: F(s) = \int_0^\infty x^{s-1} f(x) \mathrm{d}x.

    For all "sensible" functions, this converges absolutely in a strip
      `a < \operatorname{Re}(s) < b`.

    The Mellin transform is related via change of variables to the Fourier
    transform, and also to the (bilateral) Laplace transform.

    This function returns ``(F, (a, b), cond)``
    where ``F`` is the Mellin transform of ``f``, ``(a, b)`` is the fundamental strip
    (as above), and ``cond`` are auxiliary convergence conditions.

    If the integral cannot be computed in closed form, this function returns
    an unevaluated :class:`MellinTransform` object.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`. If ``noconds=False``,
    then only `F` will be returned (i.e. not ``cond``, and also not the strip
    ``(a, b)``).

    >>> from sympy.integrals.transforms import mellin_transform
    >>> from sympy import exp
    >>> from sympy.abc import x, s
    >>> mellin_transform(exp(-x), x, s)
    (gamma(s), (0, oo), True)

    See Also
    ========

    inverse_mellin_transform, laplace_transform, fourier_transform
    hankel_transform, inverse_hankel_transform
    """
    return MellinTransform(f, x, s).doit(**hints)


def _rewrite_sin(m_n, s, a, b):
    """
    Re-write the sine function ``sin(m*s + n)`` as gamma functions, compatible
    with the strip (a, b).

    Return ``(gamma1, gamma2, fac)`` so that ``f == fac/(gamma1 * gamma2)``.

    >>> from sympy.integrals.transforms import _rewrite_sin
    >>> from sympy import pi, S
    >>> from sympy.abc import s
    >>> _rewrite_sin((pi, 0), s, 0, 1)
    (gamma(s), gamma(1 - s), pi)
    >>> _rewrite_sin((pi, 0), s, 1, 0)
    (gamma(s - 1), gamma(2 - s), -pi)
    >>> _rewrite_sin((pi, 0), s, -1, 0)
    (gamma(s + 1), gamma(-s), -pi)
    >>> _rewrite_sin((pi, pi/2), s, S(1)/2, S(3)/2)
    (gamma(s - 1/2), gamma(3/2 - s), -pi)
    >>> _rewrite_sin((pi, pi), s, 0, 1)
    (gamma(s), gamma(1 - s), -pi)
    >>> _rewrite_sin((2*pi, 0), s, 0, S(1)/2)
    (gamma(2*s), gamma(1 - 2*s), pi)
    >>> _rewrite_sin((2*pi, 0), s, S(1)/2, 1)
    (gamma(2*s - 1), gamma(2 - 2*s), -pi)
    """
    # (This is a separate function because it is moderately complicated,
    #  and I want to doctest it.)
    # We want to use pi/sin(pi*x) = gamma(x)*gamma(1-x).
    # But there is one comlication: the gamma functions determine the
    # inegration contour in the definition of the G-function. Usually
    # it would not matter if this is slightly shifted, unless this way
    # we create an undefined function!
    # So we try to write this in such a way that the gammas are
    # eminently on the right side of the strip.
    from sympy import expand_mul, pi, ceiling, gamma
    m, n = m_n

    m = expand_mul(m/pi)
    n = expand_mul(n/pi)
    r = ceiling(-m*a - n.as_real_imag()[0])  # Don't use re(n), does not expand
    return gamma(m*s + n + r), gamma(1 - n - r - m*s), (-1)**r*pi


class MellinTransformStripError(ValueError):
    """
    Exception raised by _rewrite_gamma. Mainly for internal use.
    """
    pass


def _rewrite_gamma(f, s, a, b):
    """
    Try to rewrite the product f(s) as a product of gamma functions,
    so that the inverse Mellin transform of f can be expressed as a meijer
    G function.

    Return (an, ap), (bm, bq), arg, exp, fac such that
    G((an, ap), (bm, bq), arg/z**exp)*fac is the inverse Mellin transform of f(s).

    Raises IntegralTransformError or MellinTransformStripError on failure.

    It is asserted that f has no poles in the fundamental strip designated by
    (a, b). One of a and b is allowed to be None. The fundamental strip is
    important, because it determines the inversion contour.

    This function can handle exponentials, linear factors, trigonometric
    functions.

    This is a helper function for inverse_mellin_transform that will not
    attempt any transformations on f.

    >>> from sympy.integrals.transforms import _rewrite_gamma
    >>> from sympy.abc import s
    >>> from sympy import oo
    >>> _rewrite_gamma(s*(s+3)*(s-1), s, -oo, oo)
    (([], [-3, 0, 1]), ([-2, 1, 2], []), 1, 1, -1)
    >>> _rewrite_gamma((s-1)**2, s, -oo, oo)
    (([], [1, 1]), ([2, 2], []), 1, 1, 1)

    Importance of the fundamental strip:

    >>> _rewrite_gamma(1/s, s, 0, oo)
    (([1], []), ([], [0]), 1, 1, 1)
    >>> _rewrite_gamma(1/s, s, None, oo)
    (([1], []), ([], [0]), 1, 1, 1)
    >>> _rewrite_gamma(1/s, s, 0, None)
    (([1], []), ([], [0]), 1, 1, 1)
    >>> _rewrite_gamma(1/s, s, -oo, 0)
    (([], [1]), ([0], []), 1, 1, -1)
    >>> _rewrite_gamma(1/s, s, None, 0)
    (([], [1]), ([0], []), 1, 1, -1)
    >>> _rewrite_gamma(1/s, s, -oo, None)
    (([], [1]), ([0], []), 1, 1, -1)

    >>> _rewrite_gamma(2**(-s+3), s, -oo, oo)
    (([], []), ([], []), 1/2, 1, 8)
    """
    from itertools import repeat
    from sympy import (Poly, gamma, Mul, re, CRootOf, exp as exp_, expand,
                       roots, ilcm, pi, sin, cos, tan, cot, igcd, exp_polar)
    # Our strategy will be as follows:
    # 1) Guess a constant c such that the inversion integral should be
    #    performed wrt s'=c*s (instead of plain s). Write s for s'.
    # 2) Process all factors, rewrite them independently as gamma functions in
    #    argument s, or exponentials of s.
    # 3) Try to transform all gamma functions s.t. they have argument
    #    a+s or a-s.
    # 4) Check that the resulting G function parameters are valid.
    # 5) Combine all the exponentials.

    a_, b_ = S([a, b])

    def left(c, is_numer):
        """
        Decide whether pole at c lies to the left of the fundamental strip.
        """
        # heuristically, this is the best chance for us to solve the inequalities
        c = expand(re(c))
        if a_ is None and b_ is oo:
            return True
        if a_ is None:
            return c < b_
        if b_ is None:
            return c <= a_
        if (c >= b_) == True:
            return False
        if (c <= a_) == True:
            return True
        if is_numer:
            return None
        if a_.free_symbols or b_.free_symbols or c.free_symbols:
            return None  # XXX
            #raise IntegralTransformError('Inverse Mellin', f,
            #                     'Could not determine position of singularity %s'
            #                     ' relative to fundamental strip' % c)
        raise MellinTransformStripError('Pole inside critical strip?')

    # 1)
    s_multipliers = []
    for g in f.atoms(gamma):
        if not g.has(s):
            continue
        arg = g.args[0]
        if arg.is_Add:
            arg = arg.as_independent(s)[1]
        coeff, _ = arg.as_coeff_mul(s)
        s_multipliers += [coeff]
    for g in f.atoms(sin, cos, tan, cot):
        if not g.has(s):
            continue
        arg = g.args[0]
        if arg.is_Add:
            arg = arg.as_independent(s)[1]
        coeff, _ = arg.as_coeff_mul(s)
        s_multipliers += [coeff/pi]
    s_multipliers = [abs(x) if x.is_real else x for x in s_multipliers]
    common_coefficient = S(1)
    for x in s_multipliers:
        if not x.is_Rational:
            common_coefficient = x
            break
    s_multipliers = [x/common_coefficient for x in s_multipliers]
    if (any(not x.is_Rational for x in s_multipliers) or
        not common_coefficient.is_real):
        raise IntegralTransformError("Gamma", None, "Nonrational multiplier")
    s_multiplier = common_coefficient/reduce(ilcm, [S(x.q)
                                             for x in s_multipliers], S(1))
    if s_multiplier == common_coefficient:
        if len(s_multipliers) == 0:
            s_multiplier = common_coefficient
        else:
            s_multiplier = common_coefficient \
                *reduce(igcd, [S(x.p) for x in s_multipliers])

    f = f.subs(s, s/s_multiplier)
    fac = S(1)/s_multiplier
    exponent = S(1)/s_multiplier
    if a_ is not None:
        a_ *= s_multiplier
    if b_ is not None:
        b_ *= s_multiplier

    # 2)
    numer, denom = f.as_numer_denom()
    numer = Mul.make_args(numer)
    denom = Mul.make_args(denom)
    args = list(zip(numer, repeat(True))) + list(zip(denom, repeat(False)))

    facs = []
    dfacs = []
    # *_gammas will contain pairs (a, c) representing Gamma(a*s + c)
    numer_gammas = []
    denom_gammas = []
    # exponentials will contain bases for exponentials of s
    exponentials = []

    def exception(fact):
        return IntegralTransformError("Inverse Mellin", f, "Unrecognised form '%s'." % fact)
    while args:
        fact, is_numer = args.pop()
        if is_numer:
            ugammas, lgammas = numer_gammas, denom_gammas
            ufacs, lfacs = facs, dfacs
        else:
            ugammas, lgammas = denom_gammas, numer_gammas
            ufacs, lfacs = dfacs, facs

        def linear_arg(arg):
            """ Test if arg is of form a*s+b, raise exception if not. """
            if not arg.is_polynomial(s):
                raise exception(fact)
            p = Poly(arg, s)
            if p.degree() != 1:
                raise exception(fact)
            return p.all_coeffs()

        # constants
        if not fact.has(s):
            ufacs += [fact]
        # exponentials
        elif fact.is_Pow or isinstance(fact, exp_):
            if fact.is_Pow:
                base = fact.base
                exp = fact.exp
            else:
                base = exp_polar(1)
                exp = fact.args[0]
            if exp.is_Integer:
                cond = is_numer
                if exp < 0:
                    cond = not cond
                args += [(base, cond)]*abs(exp)
                continue
            elif not base.has(s):
                a, b = linear_arg(exp)
                if not is_numer:
                    base = 1/base
                exponentials += [base**a]
                facs += [base**b]
            else:
                raise exception(fact)
        # linear factors
        elif fact.is_polynomial(s):
            p = Poly(fact, s)
            if p.degree() != 1:
                # We completely factor the poly. For this we need the roots.
                # Now roots() only works in some cases (low degree), and CRootOf
                # only works without parameters. So try both...
                coeff = p.LT()[1]
                rs = roots(p, s)
                if len(rs) != p.degree():
                    rs = CRootOf.all_roots(p)
                ufacs += [coeff]
                args += [(s - c, is_numer) for c in rs]
                continue
            a, c = p.all_coeffs()
            ufacs += [a]
            c /= -a
            # Now need to convert s - c
            if left(c, is_numer):
                ugammas += [(S(1), -c + 1)]
                lgammas += [(S(1), -c)]
            else:
                ufacs += [-1]
                ugammas += [(S(-1), c + 1)]
                lgammas += [(S(-1), c)]
        elif isinstance(fact, gamma):
            a, b = linear_arg(fact.args[0])
            if is_numer:
                if (a > 0 and (left(-b/a, is_numer) == False)) or \
                   (a < 0 and (left(-b/a, is_numer) == True)):
                    raise NotImplementedError(
                        'Gammas partially over the strip.')
            ugammas += [(a, b)]
        elif isinstance(fact, sin):
            # We try to re-write all trigs as gammas. This is not in
            # general the best strategy, since sometimes this is impossible,
            # but rewriting as exponentials would work. However trig functions
            # in inverse mellin transforms usually all come from simplifying
            # gamma terms, so this should work.
            a = fact.args[0]
            if is_numer:
                # No problem with the poles.
                gamma1, gamma2, fac_ = gamma(a/pi), gamma(1 - a/pi), pi
            else:
                gamma1, gamma2, fac_ = _rewrite_sin(linear_arg(a), s, a_, b_)
            args += [(gamma1, not is_numer), (gamma2, not is_numer)]
            ufacs += [fac_]
        elif isinstance(fact, tan):
            a = fact.args[0]
            args += [(sin(a, evaluate=False), is_numer),
                     (sin(pi/2 - a, evaluate=False), not is_numer)]
        elif isinstance(fact, cos):
            a = fact.args[0]
            args += [(sin(pi/2 - a, evaluate=False), is_numer)]
        elif isinstance(fact, cot):
            a = fact.args[0]
            args += [(sin(pi/2 - a, evaluate=False), is_numer),
                     (sin(a, evaluate=False), not is_numer)]
        else:
            raise exception(fact)

    fac *= Mul(*facs)/Mul(*dfacs)

    # 3)
    an, ap, bm, bq = [], [], [], []
    for gammas, plus, minus, is_numer in [(numer_gammas, an, bm, True),
                                          (denom_gammas, bq, ap, False)]:
        while gammas:
            a, c = gammas.pop()
            if a != -1 and a != +1:
                # We use the gamma function multiplication theorem.
                p = abs(S(a))
                newa = a/p
                newc = c/p
                if not a.is_Integer:
                    raise TypeError("a is not an integer")
                for k in range(p):
                    gammas += [(newa, newc + k/p)]
                if is_numer:
                    fac *= (2*pi)**((1 - p)/2) * p**(c - S(1)/2)
                    exponentials += [p**a]
                else:
                    fac /= (2*pi)**((1 - p)/2) * p**(c - S(1)/2)
                    exponentials += [p**(-a)]
                continue
            if a == +1:
                plus.append(1 - c)
            else:
                minus.append(c)

    # 4)
    # TODO

    # 5)
    arg = Mul(*exponentials)

    # for testability, sort the arguments
    an.sort(key=default_sort_key)
    ap.sort(key=default_sort_key)
    bm.sort(key=default_sort_key)
    bq.sort(key=default_sort_key)

    return (an, ap), (bm, bq), arg, exponent, fac


@_noconds_(True)
def _inverse_mellin_transform(F, s, x_, strip, as_meijerg=False):
    """ A helper for the real inverse_mellin_transform function, this one here
        assumes x to be real and positive. """
    from sympy import (expand, expand_mul, hyperexpand, meijerg,
                       arg, pi, re, factor, Heaviside, gamma, Add)
    x = _dummy('t', 'inverse-mellin-transform', F, positive=True)
    # Actually, we won't try integration at all. Instead we use the definition
    # of the Meijer G function as a fairly general inverse mellin transform.
    F = F.rewrite(gamma)
    for g in [factor(F), expand_mul(F), expand(F)]:
        if g.is_Add:
            # do all terms separately
            ress = [_inverse_mellin_transform(G, s, x, strip, as_meijerg,
                                              noconds=False)
                    for G in g.args]
            conds = [p[1] for p in ress]
            ress = [p[0] for p in ress]
            res = Add(*ress)
            if not as_meijerg:
                res = factor(res, gens=res.atoms(Heaviside))
            return res.subs(x, x_), And(*conds)

        try:
            a, b, C, e, fac = _rewrite_gamma(g, s, strip[0], strip[1])
        except IntegralTransformError:
            continue
        G = meijerg(a, b, C/x**e)
        if as_meijerg:
            h = G
        else:
            try:
                h = hyperexpand(G)
            except NotImplementedError as detail:
                raise IntegralTransformError(
                    'Inverse Mellin', F, 'Could not calculate integral')

            if h.is_Piecewise and len(h.args) == 3:
                # XXX we break modularity here!
                h = Heaviside(x - abs(C))*h.args[0].args[0] \
                    + Heaviside(abs(C) - x)*h.args[1].args[0]
        # We must ensure that the integral along the line we want converges,
        # and return that value.
        # See [L], 5.2
        cond = [abs(arg(G.argument)) < G.delta*pi]
        # Note: we allow ">=" here, this corresponds to convergence if we let
        # limits go to oo symmetrically. ">" corresponds to absolute convergence.
        cond += [And(Or(len(G.ap) != len(G.bq), 0 >= re(G.nu) + 1),
                     abs(arg(G.argument)) == G.delta*pi)]
        cond = Or(*cond)
        if cond == False:
            raise IntegralTransformError(
                'Inverse Mellin', F, 'does not converge')
        return (h*fac).subs(x, x_), cond

    raise IntegralTransformError('Inverse Mellin', F, '')

_allowed = None


class InverseMellinTransform(IntegralTransform):
    """
    Class representing unevaluated inverse Mellin transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute inverse Mellin transforms, see the
    :func:`inverse_mellin_transform` docstring.
    """

    _name = 'Inverse Mellin'
    _none_sentinel = Dummy('None')
    _c = Dummy('c')

    def __new__(cls, F, s, x, a, b, **opts):
        if a is None:
            a = InverseMellinTransform._none_sentinel
        if b is None:
            b = InverseMellinTransform._none_sentinel
        return IntegralTransform.__new__(cls, F, s, x, a, b, **opts)

    @property
    def fundamental_strip(self):
        a, b = self.args[3], self.args[4]
        if a is InverseMellinTransform._none_sentinel:
            a = None
        if b is InverseMellinTransform._none_sentinel:
            b = None
        return a, b

    def _compute_transform(self, F, s, x, **hints):
        from sympy import postorder_traversal
        global _allowed
        if _allowed is None:
            from sympy import (
                exp, gamma, sin, cos, tan, cot, cosh, sinh, tanh,
                coth, factorial, rf)
            _allowed = set(
                [exp, gamma, sin, cos, tan, cot, cosh, sinh, tanh, coth,
                 factorial, rf])
        for f in postorder_traversal(F):
            if f.is_Function and f.has(s) and f.func not in _allowed:
                raise IntegralTransformError('Inverse Mellin', F,
                                     'Component %s not recognised.' % f)
        strip = self.fundamental_strip
        return _inverse_mellin_transform(F, s, x, strip, **hints)

    def _as_integral(self, F, s, x):
        from sympy import I
        c = self.__class__._c
        return Integral(F*x**(-s), (s, c - I*oo, c + I*oo))/(2*S.Pi*S.ImaginaryUnit)


def inverse_mellin_transform(F, s, x, strip, **hints):
    r"""
    Compute the inverse Mellin transform of `F(s)` over the fundamental
    strip given by ``strip=(a, b)``.

    This can be defined as

    .. math:: f(x) = \frac{1}{2\pi i} \int_{c - i\infty}^{c + i\infty} x^{-s} F(s) \mathrm{d}s,

    for any `c` in the fundamental strip. Under certain regularity
    conditions on `F` and/or `f`,
    this recovers `f` from its Mellin transform `F`
    (and vice versa), for positive real `x`.

    One of `a` or `b` may be passed as ``None``; a suitable `c` will be
    inferred.

    If the integral cannot be computed in closed form, this function returns
    an unevaluated :class:`InverseMellinTransform` object.

    Note that this function will assume x to be positive and real, regardless
    of the sympy assumptions!

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.

    >>> from sympy.integrals.transforms import inverse_mellin_transform
    >>> from sympy import oo, gamma
    >>> from sympy.abc import x, s
    >>> inverse_mellin_transform(gamma(s), s, x, (0, oo))
    exp(-x)

    The fundamental strip matters:

    >>> f = 1/(s**2 - 1)
    >>> inverse_mellin_transform(f, s, x, (-oo, -1))
    (x/2 - 1/(2*x))*Heaviside(x - 1)
    >>> inverse_mellin_transform(f, s, x, (-1, 1))
    -x*Heaviside(1 - x)/2 - Heaviside(x - 1)/(2*x)
    >>> inverse_mellin_transform(f, s, x, (1, oo))
    (-x/2 + 1/(2*x))*Heaviside(1 - x)

    See Also
    ========

    mellin_transform
    hankel_transform, inverse_hankel_transform
    """
    return InverseMellinTransform(F, s, x, strip[0], strip[1]).doit(**hints)


##########################################################################
# Laplace Transform
##########################################################################

def _simplifyconds(expr, s, a):
    r"""
    Naively simplify some conditions occurring in ``expr``, given that `\operatorname{Re}(s) > a`.

    >>> from sympy.integrals.transforms import _simplifyconds as simp
    >>> from sympy.abc import x
    >>> from sympy import sympify as S
    >>> simp(abs(x**2) < 1, x, 1)
    False
    >>> simp(abs(x**2) < 1, x, 2)
    False
    >>> simp(abs(x**2) < 1, x, 0)
    Abs(x**2) < 1
    >>> simp(abs(1/x**2) < 1, x, 1)
    True
    >>> simp(S(1) < abs(x), x, 1)
    True
    >>> simp(S(1) < abs(1/x), x, 1)
    False

    >>> from sympy import Ne
    >>> simp(Ne(1, x**3), x, 1)
    True
    >>> simp(Ne(1, x**3), x, 2)
    True
    >>> simp(Ne(1, x**3), x, 0)
    Ne(1, x**3)
    """
    from sympy.core.relational import ( StrictGreaterThan, StrictLessThan,
        Unequality )
    from sympy import Abs

    def power(ex):
        if ex == s:
            return 1
        if ex.is_Pow and ex.base == s:
            return ex.exp
        return None

    def bigger(ex1, ex2):
        """ Return True only if |ex1| > |ex2|, False only if |ex1| < |ex2|.
            Else return None. """
        if ex1.has(s) and ex2.has(s):
            return None
        if isinstance(ex1, Abs):
            ex1 = ex1.args[0]
        if isinstance(ex2, Abs):
            ex2 = ex2.args[0]
        if ex1.has(s):
            return bigger(1/ex2, 1/ex1)
        n = power(ex2)
        if n is None:
            return None
        try:
            if n > 0 and (abs(ex1) <= abs(a)**n) == True:
                return False
            if n < 0 and (abs(ex1) >= abs(a)**n) == True:
                return True
        except TypeError:
            pass

    def replie(x, y):
        """ simplify x < y """
        if not (x.is_positive or isinstance(x, Abs)) \
                or not (y.is_positive or isinstance(y, Abs)):
            return (x < y)
        r = bigger(x, y)
        if r is not None:
            return not r
        return (x < y)

    def replue(x, y):
        b = bigger(x, y)
        if b == True or b == False:
            return True
        return Unequality(x, y)

    def repl(ex, *args):
        if ex == True or ex == False:
            return bool(ex)
        return ex.replace(*args)
    expr = repl(expr, StrictLessThan, replie)
    expr = repl(expr, StrictGreaterThan, lambda x, y: replie(y, x))
    expr = repl(expr, Unequality, replue)
    return S(expr)


@_noconds
def _laplace_transform(f, t, s_, simplify=True):
    """ The backend function for Laplace transforms. """
    from sympy import (re, Max, exp, pi, Min, periodic_argument as arg_,
                       arg, cos, Wild, symbols, polar_lift)
    s = Dummy('s')
    F = integrate(exp(-s*t) * f, (t, 0, oo))

    if not F.has(Integral):
        return _simplify(F.subs(s, s_), simplify), -oo, S.true

    if not F.is_Piecewise:
        raise IntegralTransformError(
            'Laplace', f, 'could not compute integral')

    F, cond = F.args[0]
    if F.has(Integral):
        raise IntegralTransformError(
            'Laplace', f, 'integral in unexpected form')

    def process_conds(conds):
        """ Turn ``conds`` into a strip and auxiliary conditions. """
        a = -oo
        aux = S.true
        conds = conjuncts(to_cnf(conds))
        p, q, w1, w2, w3, w4, w5 = symbols(
            'p q w1 w2 w3 w4 w5', cls=Wild, exclude=[s])
        patterns = (
            p*abs(arg((s + w3)*q)) < w2,
            p*abs(arg((s + w3)*q)) <= w2,
            abs(arg_((s + w3)**p*q, w1)) < w2,
            abs(arg_((s + w3)**p*q, w1)) <= w2,
            abs(arg_((polar_lift(s + w3))**p*q, w1)) < w2,
            abs(arg_((polar_lift(s + w3))**p*q, w1)) <= w2)
        for c in conds:
            a_ = oo
            aux_ = []
            for d in disjuncts(c):
                if d.is_Relational and s in d.rhs.free_symbols:
                    d = d.reversed
                if d.is_Relational and isinstance(d, (Ge, Gt)):
                    d = d.reversedsign
                for pat in patterns:
                    m = d.match(pat)
                    if m:
                        break
                if m:
                    if m[q].is_positive and m[w2]/m[p] == pi/2:
                        d = -re(s + m[w3]) < 0
                m = d.match(p - cos(w1*abs(arg(s*w5))*w2)*abs(s**w3)**w4 < 0)
                if not m:
                    m = d.match(
                        cos(p - abs(arg_(s**w1*w5, q))*w2)*abs(s**w3)**w4 < 0)
                if not m:
                    m = d.match(
                        p - cos(abs(arg_(polar_lift(s)**w1*w5, q))*w2
                            )*abs(s**w3)**w4 < 0)
                if m and all(m[wild].is_positive for wild in [w1, w2, w3, w4, w5]):
                    d = re(s) > m[p]
                d_ = d.replace(
                    re, lambda x: x.expand().as_real_imag()[0]).subs(re(s), t)
                if not d.is_Relational or \
                    d.rel_op in ('==', '!=') \
                        or d_.has(s) or not d_.has(t):
                    aux_ += [d]
                    continue
                soln = _solve_inequality(d_, t)
                if not soln.is_Relational or \
                        soln.rel_op in ('==', '!='):
                    aux_ += [d]
                    continue
                if soln.lts == t:
                    raise IntegralTransformError('Laplace', f,
                                         'convergence not in half-plane?')
                else:
                    a_ = Min(soln.lts, a_)
            if a_ != oo:
                a = Max(a_, a)
            else:
                aux = And(aux, Or(*aux_))
        return a, aux

    conds = [process_conds(c) for c in disjuncts(cond)]
    conds2 = [x for x in conds if x[1] != False and x[0] != -oo]
    if not conds2:
        conds2 = [x for x in conds if x[1] != False]
    conds = conds2

    def cnt(expr):
        if expr == True or expr == False:
            return 0
        return expr.count_ops()
    conds.sort(key=lambda x: (-x[0], cnt(x[1])))

    if not conds:
        raise IntegralTransformError('Laplace', f, 'no convergence found')
    a, aux = conds[0]

    def sbs(expr):
        return expr.subs(s, s_)
    if simplify:
        F = _simplifyconds(F, s, a)
        aux = _simplifyconds(aux, s, a)
    return _simplify(F.subs(s, s_), simplify), sbs(a), _canonical(sbs(aux))


class LaplaceTransform(IntegralTransform):
    """
    Class representing unevaluated Laplace transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute Laplace transforms, see the :func:`laplace_transform`
    docstring.
    """

    _name = 'Laplace'

    def _compute_transform(self, f, t, s, **hints):
        return _laplace_transform(f, t, s, **hints)

    def _as_integral(self, f, t, s):
        from sympy import exp
        return Integral(f*exp(-s*t), (t, 0, oo))

    def _collapse_extra(self, extra):
        from sympy import Max
        conds = []
        planes = []
        for plane, cond in extra:
            conds.append(cond)
            planes.append(plane)
        cond = And(*conds)
        plane = Max(*planes)
        if cond == False:
            raise IntegralTransformError(
                'Laplace', None, 'No combined convergence.')
        return plane, cond


def laplace_transform(f, t, s, **hints):
    r"""
    Compute the Laplace Transform `F(s)` of `f(t)`,

    .. math :: F(s) = \int_0^\infty e^{-st} f(t) \mathrm{d}t.

    For all "sensible" functions, this converges absolutely in a
    half plane  `a < \operatorname{Re}(s)`.

    This function returns ``(F, a, cond)``
    where ``F`` is the Laplace transform of ``f``, `\operatorname{Re}(s) > a` is the half-plane
    of convergence, and ``cond`` are auxiliary convergence conditions.

    If the integral cannot be computed in closed form, this function returns
    an unevaluated :class:`LaplaceTransform` object.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`. If ``noconds=True``,
    only `F` will be returned (i.e. not ``cond``, and also not the plane ``a``).

    >>> from sympy.integrals import laplace_transform
    >>> from sympy.abc import t, s, a
    >>> laplace_transform(t**a, t, s)
    (s**(-a)*gamma(a + 1)/s, 0, re(a) > -1)

    See Also
    ========

    inverse_laplace_transform, mellin_transform, fourier_transform
    hankel_transform, inverse_hankel_transform
    """
    if isinstance(f, MatrixBase) and hasattr(f, 'applyfunc'):
        return f.applyfunc(lambda fij: laplace_transform(fij, t, s, **hints))
    return LaplaceTransform(f, t, s).doit(**hints)


@_noconds_(True)
def _inverse_laplace_transform(F, s, t_, plane, simplify=True):
    """ The backend function for inverse Laplace transforms. """
    from sympy import exp, Heaviside, log, expand_complex, Integral, Piecewise
    from sympy.integrals.meijerint import meijerint_inversion, _get_coeff_exp
    # There are two strategies we can try:
    # 1) Use inverse mellin transforms - related by a simple change of variables.
    # 2) Use the inversion integral.

    t = Dummy('t', real=True)

    def pw_simp(*args):
        """ Simplify a piecewise expression from hyperexpand. """
        # XXX we break modularity here!
        if len(args) != 3:
            return Piecewise(*args)
        arg = args[2].args[0].argument
        coeff, exponent = _get_coeff_exp(arg, t)
        e1 = args[0].args[0]
        e2 = args[1].args[0]
        return Heaviside(1/abs(coeff) - t**exponent)*e1 \
            + Heaviside(t**exponent - 1/abs(coeff))*e2

    try:
        f, cond = inverse_mellin_transform(F, s, exp(-t), (None, oo),
                                           needeval=True, noconds=False)
    except IntegralTransformError:
        f = None
    if f is None:
        f = meijerint_inversion(F, s, t)
        if f is None:
            raise IntegralTransformError('Inverse Laplace', f, '')
        if f.is_Piecewise:
            f, cond = f.args[0]
            if f.has(Integral):
                raise IntegralTransformError('Inverse Laplace', f,
                                     'inversion integral of unrecognised form.')
        else:
            cond = S.true
        f = f.replace(Piecewise, pw_simp)

    if f.is_Piecewise:
        # many of the functions called below can't work with piecewise
        # (b/c it has a bool in args)
        return f.subs(t, t_), cond

    u = Dummy('u')

    def simp_heaviside(arg):
        a = arg.subs(exp(-t), u)
        if a.has(t):
            return Heaviside(arg)
        rel = _solve_inequality(a > 0, u)
        if rel.lts == u:
            k = log(rel.gts)
            return Heaviside(t + k)
        else:
            k = log(rel.lts)
            return Heaviside(-(t + k))
    f = f.replace(Heaviside, simp_heaviside)

    def simp_exp(arg):
        return expand_complex(exp(arg))
    f = f.replace(exp, simp_exp)

    # TODO it would be nice to fix cosh and sinh ... simplify messes these
    #      exponentials up

    return _simplify(f.subs(t, t_), simplify), cond


class InverseLaplaceTransform(IntegralTransform):
    """
    Class representing unevaluated inverse Laplace transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute inverse Laplace transforms, see the
    :func:`inverse_laplace_transform` docstring.
    """

    _name = 'Inverse Laplace'
    _none_sentinel = Dummy('None')
    _c = Dummy('c')

    def __new__(cls, F, s, x, plane, **opts):
        if plane is None:
            plane = InverseLaplaceTransform._none_sentinel
        return IntegralTransform.__new__(cls, F, s, x, plane, **opts)

    @property
    def fundamental_plane(self):
        plane = self.args[3]
        if plane is InverseLaplaceTransform._none_sentinel:
            plane = None
        return plane

    def _compute_transform(self, F, s, t, **hints):
        return _inverse_laplace_transform(F, s, t, self.fundamental_plane, **hints)

    def _as_integral(self, F, s, t):
        from sympy import I, exp
        c = self.__class__._c
        return Integral(exp(s*t)*F, (s, c - I*oo, c + I*oo))/(2*S.Pi*S.ImaginaryUnit)


def inverse_laplace_transform(F, s, t, plane=None, **hints):
    r"""
    Compute the inverse Laplace transform of `F(s)`, defined as

    .. math :: f(t) = \frac{1}{2\pi i} \int_{c-i\infty}^{c+i\infty} e^{st} F(s) \mathrm{d}s,

    for `c` so large that `F(s)` has no singularites in the
    half-plane `\operatorname{Re}(s) > c-\epsilon`.

    The plane can be specified by
    argument ``plane``, but will be inferred if passed as None.

    Under certain regularity conditions, this recovers `f(t)` from its
    Laplace Transform `F(s)`, for non-negative `t`, and vice
    versa.

    If the integral cannot be computed in closed form, this function returns
    an unevaluated :class:`InverseLaplaceTransform` object.

    Note that this function will always assume `t` to be real,
    regardless of the sympy assumption on `t`.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.

    >>> from sympy.integrals.transforms import inverse_laplace_transform
    >>> from sympy import exp, Symbol
    >>> from sympy.abc import s, t
    >>> a = Symbol('a', positive=True)
    >>> inverse_laplace_transform(exp(-a*s)/s, s, t)
    Heaviside(-a + t)

    See Also
    ========

    laplace_transform
    hankel_transform, inverse_hankel_transform
    """
    if isinstance(F, MatrixBase) and hasattr(F, 'applyfunc'):
        return F.applyfunc(lambda Fij: inverse_laplace_transform(Fij, s, t, plane, **hints))
    return InverseLaplaceTransform(F, s, t, plane).doit(**hints)


##########################################################################
# Fourier Transform
##########################################################################

@_noconds_(True)
def _fourier_transform(f, x, k, a, b, name, simplify=True):
    """
    Compute a general Fourier-type transform
        F(k) = a int_-oo^oo exp(b*I*x*k) f(x) dx.

    For suitable choice of a and b, this reduces to the standard Fourier
    and inverse Fourier transforms.
    """
    from sympy import exp, I
    F = integrate(a*f*exp(b*I*x*k), (x, -oo, oo))

    if not F.has(Integral):
        return _simplify(F, simplify), S.true

    integral_f = integrate(f, (x, -oo, oo))
    if integral_f in (-oo, oo, S.NaN) or integral_f.has(Integral):
        raise IntegralTransformError(name, f, 'function not integrable on real axis')

    if not F.is_Piecewise:
        raise IntegralTransformError(name, f, 'could not compute integral')

    F, cond = F.args[0]
    if F.has(Integral):
        raise IntegralTransformError(name, f, 'integral in unexpected form')

    return _simplify(F, simplify), cond


class FourierTypeTransform(IntegralTransform):
    """ Base class for Fourier transforms."""

    def a(self):
        raise NotImplementedError(
            "Class %s must implement a(self) but does not" % self.__class__)

    def b(self):
        raise NotImplementedError(
            "Class %s must implement b(self) but does not" % self.__class__)

    def _compute_transform(self, f, x, k, **hints):
        return _fourier_transform(f, x, k,
                                  self.a(), self.b(),
                                  self.__class__._name, **hints)

    def _as_integral(self, f, x, k):
        from sympy import exp, I
        a = self.a()
        b = self.b()
        return Integral(a*f*exp(b*I*x*k), (x, -oo, oo))


class FourierTransform(FourierTypeTransform):
    """
    Class representing unevaluated Fourier transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute Fourier transforms, see the :func:`fourier_transform`
    docstring.
    """

    _name = 'Fourier'

    def a(self):
        return 1

    def b(self):
        return -2*S.Pi


def fourier_transform(f, x, k, **hints):
    r"""
    Compute the unitary, ordinary-frequency Fourier transform of `f`, defined
    as

    .. math:: F(k) = \int_{-\infty}^\infty f(x) e^{-2\pi i x k} \mathrm{d} x.

    If the transform cannot be computed in closed form, this
    function returns an unevaluated :class:`FourierTransform` object.

    For other Fourier transform conventions, see the function
    :func:`sympy.integrals.transforms._fourier_transform`.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.
    Note that for this transform, by default ``noconds=True``.

    >>> from sympy import fourier_transform, exp
    >>> from sympy.abc import x, k
    >>> fourier_transform(exp(-x**2), x, k)
    sqrt(pi)*exp(-pi**2*k**2)
    >>> fourier_transform(exp(-x**2), x, k, noconds=False)
    (sqrt(pi)*exp(-pi**2*k**2), True)

    See Also
    ========

    inverse_fourier_transform
    sine_transform, inverse_sine_transform
    cosine_transform, inverse_cosine_transform
    hankel_transform, inverse_hankel_transform
    mellin_transform, laplace_transform
    """
    return FourierTransform(f, x, k).doit(**hints)


class InverseFourierTransform(FourierTypeTransform):
    """
    Class representing unevaluated inverse Fourier transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute inverse Fourier transforms, see the
    :func:`inverse_fourier_transform` docstring.
    """

    _name = 'Inverse Fourier'

    def a(self):
        return 1

    def b(self):
        return 2*S.Pi


def inverse_fourier_transform(F, k, x, **hints):
    r"""
    Compute the unitary, ordinary-frequency inverse Fourier transform of `F`,
    defined as

    .. math:: f(x) = \int_{-\infty}^\infty F(k) e^{2\pi i x k} \mathrm{d} k.

    If the transform cannot be computed in closed form, this
    function returns an unevaluated :class:`InverseFourierTransform` object.

    For other Fourier transform conventions, see the function
    :func:`sympy.integrals.transforms._fourier_transform`.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.
    Note that for this transform, by default ``noconds=True``.

    >>> from sympy import inverse_fourier_transform, exp, sqrt, pi
    >>> from sympy.abc import x, k
    >>> inverse_fourier_transform(sqrt(pi)*exp(-(pi*k)**2), k, x)
    exp(-x**2)
    >>> inverse_fourier_transform(sqrt(pi)*exp(-(pi*k)**2), k, x, noconds=False)
    (exp(-x**2), True)

    See Also
    ========

    fourier_transform
    sine_transform, inverse_sine_transform
    cosine_transform, inverse_cosine_transform
    hankel_transform, inverse_hankel_transform
    mellin_transform, laplace_transform
    """
    return InverseFourierTransform(F, k, x).doit(**hints)


##########################################################################
# Fourier Sine and Cosine Transform
##########################################################################

from sympy import sin, cos, sqrt, pi


@_noconds_(True)
def _sine_cosine_transform(f, x, k, a, b, K, name, simplify=True):
    """
    Compute a general sine or cosine-type transform
        F(k) = a int_0^oo b*sin(x*k) f(x) dx.
        F(k) = a int_0^oo b*cos(x*k) f(x) dx.

    For suitable choice of a and b, this reduces to the standard sine/cosine
    and inverse sine/cosine transforms.
    """
    F = integrate(a*f*K(b*x*k), (x, 0, oo))

    if not F.has(Integral):
        return _simplify(F, simplify), S.true

    if not F.is_Piecewise:
        raise IntegralTransformError(name, f, 'could not compute integral')

    F, cond = F.args[0]
    if F.has(Integral):
        raise IntegralTransformError(name, f, 'integral in unexpected form')

    return _simplify(F, simplify), cond


class SineCosineTypeTransform(IntegralTransform):
    """
    Base class for sine and cosine transforms.
    Specify cls._kern.
    """

    def a(self):
        raise NotImplementedError(
            "Class %s must implement a(self) but does not" % self.__class__)

    def b(self):
        raise NotImplementedError(
            "Class %s must implement b(self) but does not" % self.__class__)


    def _compute_transform(self, f, x, k, **hints):
        return _sine_cosine_transform(f, x, k,
                                      self.a(), self.b(),
                                      self.__class__._kern,
                                      self.__class__._name, **hints)

    def _as_integral(self, f, x, k):
        a = self.a()
        b = self.b()
        K = self.__class__._kern
        return Integral(a*f*K(b*x*k), (x, 0, oo))


class SineTransform(SineCosineTypeTransform):
    """
    Class representing unevaluated sine transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute sine transforms, see the :func:`sine_transform`
    docstring.
    """

    _name = 'Sine'
    _kern = sin

    def a(self):
        return sqrt(2)/sqrt(pi)

    def b(self):
        return 1


def sine_transform(f, x, k, **hints):
    r"""
    Compute the unitary, ordinary-frequency sine transform of `f`, defined
    as

    .. math:: F(k) = \sqrt{\frac{2}{\pi}} \int_{0}^\infty f(x) \sin(2\pi x k) \mathrm{d} x.

    If the transform cannot be computed in closed form, this
    function returns an unevaluated :class:`SineTransform` object.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.
    Note that for this transform, by default ``noconds=True``.

    >>> from sympy import sine_transform, exp
    >>> from sympy.abc import x, k, a
    >>> sine_transform(x*exp(-a*x**2), x, k)
    sqrt(2)*k*exp(-k**2/(4*a))/(4*a**(3/2))
    >>> sine_transform(x**(-a), x, k)
    2**(1/2 - a)*k**(a - 1)*gamma(1 - a/2)/gamma(a/2 + 1/2)

    See Also
    ========

    fourier_transform, inverse_fourier_transform
    inverse_sine_transform
    cosine_transform, inverse_cosine_transform
    hankel_transform, inverse_hankel_transform
    mellin_transform, laplace_transform
    """
    return SineTransform(f, x, k).doit(**hints)


class InverseSineTransform(SineCosineTypeTransform):
    """
    Class representing unevaluated inverse sine transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute inverse sine transforms, see the
    :func:`inverse_sine_transform` docstring.
    """

    _name = 'Inverse Sine'
    _kern = sin

    def a(self):
        return sqrt(2)/sqrt(pi)

    def b(self):
        return 1


def inverse_sine_transform(F, k, x, **hints):
    r"""
    Compute the unitary, ordinary-frequency inverse sine transform of `F`,
    defined as

    .. math:: f(x) = \sqrt{\frac{2}{\pi}} \int_{0}^\infty F(k) \sin(2\pi x k) \mathrm{d} k.

    If the transform cannot be computed in closed form, this
    function returns an unevaluated :class:`InverseSineTransform` object.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.
    Note that for this transform, by default ``noconds=True``.

    >>> from sympy import inverse_sine_transform, exp, sqrt, gamma, pi
    >>> from sympy.abc import x, k, a
    >>> inverse_sine_transform(2**((1-2*a)/2)*k**(a - 1)*
    ...     gamma(-a/2 + 1)/gamma((a+1)/2), k, x)
    x**(-a)
    >>> inverse_sine_transform(sqrt(2)*k*exp(-k**2/(4*a))/(4*sqrt(a)**3), k, x)
    x*exp(-a*x**2)

    See Also
    ========

    fourier_transform, inverse_fourier_transform
    sine_transform
    cosine_transform, inverse_cosine_transform
    hankel_transform, inverse_hankel_transform
    mellin_transform, laplace_transform
    """
    return InverseSineTransform(F, k, x).doit(**hints)


class CosineTransform(SineCosineTypeTransform):
    """
    Class representing unevaluated cosine transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute cosine transforms, see the :func:`cosine_transform`
    docstring.
    """

    _name = 'Cosine'
    _kern = cos

    def a(self):
        return sqrt(2)/sqrt(pi)

    def b(self):
        return 1


def cosine_transform(f, x, k, **hints):
    r"""
    Compute the unitary, ordinary-frequency cosine transform of `f`, defined
    as

    .. math:: F(k) = \sqrt{\frac{2}{\pi}} \int_{0}^\infty f(x) \cos(2\pi x k) \mathrm{d} x.

    If the transform cannot be computed in closed form, this
    function returns an unevaluated :class:`CosineTransform` object.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.
    Note that for this transform, by default ``noconds=True``.

    >>> from sympy import cosine_transform, exp, sqrt, cos
    >>> from sympy.abc import x, k, a
    >>> cosine_transform(exp(-a*x), x, k)
    sqrt(2)*a/(sqrt(pi)*(a**2 + k**2))
    >>> cosine_transform(exp(-a*sqrt(x))*cos(a*sqrt(x)), x, k)
    a*exp(-a**2/(2*k))/(2*k**(3/2))

    See Also
    ========

    fourier_transform, inverse_fourier_transform,
    sine_transform, inverse_sine_transform
    inverse_cosine_transform
    hankel_transform, inverse_hankel_transform
    mellin_transform, laplace_transform
    """
    return CosineTransform(f, x, k).doit(**hints)


class InverseCosineTransform(SineCosineTypeTransform):
    """
    Class representing unevaluated inverse cosine transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute inverse cosine transforms, see the
    :func:`inverse_cosine_transform` docstring.
    """

    _name = 'Inverse Cosine'
    _kern = cos

    def a(self):
        return sqrt(2)/sqrt(pi)

    def b(self):
        return 1


def inverse_cosine_transform(F, k, x, **hints):
    r"""
    Compute the unitary, ordinary-frequency inverse cosine transform of `F`,
    defined as

    .. math:: f(x) = \sqrt{\frac{2}{\pi}} \int_{0}^\infty F(k) \cos(2\pi x k) \mathrm{d} k.

    If the transform cannot be computed in closed form, this
    function returns an unevaluated :class:`InverseCosineTransform` object.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.
    Note that for this transform, by default ``noconds=True``.

    >>> from sympy import inverse_cosine_transform, exp, sqrt, pi
    >>> from sympy.abc import x, k, a
    >>> inverse_cosine_transform(sqrt(2)*a/(sqrt(pi)*(a**2 + k**2)), k, x)
    exp(-a*x)
    >>> inverse_cosine_transform(1/sqrt(k), k, x)
    1/sqrt(x)

    See Also
    ========

    fourier_transform, inverse_fourier_transform,
    sine_transform, inverse_sine_transform
    cosine_transform
    hankel_transform, inverse_hankel_transform
    mellin_transform, laplace_transform
    """
    return InverseCosineTransform(F, k, x).doit(**hints)


##########################################################################
# Hankel Transform
##########################################################################

@_noconds_(True)
def _hankel_transform(f, r, k, nu, name, simplify=True):
    r"""
    Compute a general Hankel transform

    .. math:: F_\nu(k) = \int_{0}^\infty f(r) J_\nu(k r) r \mathrm{d} r.
    """
    from sympy import besselj
    F = integrate(f*besselj(nu, k*r)*r, (r, 0, oo))

    if not F.has(Integral):
        return _simplify(F, simplify), S.true

    if not F.is_Piecewise:
        raise IntegralTransformError(name, f, 'could not compute integral')

    F, cond = F.args[0]
    if F.has(Integral):
        raise IntegralTransformError(name, f, 'integral in unexpected form')

    return _simplify(F, simplify), cond


class HankelTypeTransform(IntegralTransform):
    """
    Base class for Hankel transforms.
    """

    def doit(self, **hints):
        return self._compute_transform(self.function,
                                       self.function_variable,
                                       self.transform_variable,
                                       self.args[3],
                                       **hints)

    def _compute_transform(self, f, r, k, nu, **hints):
        return _hankel_transform(f, r, k, nu, self._name, **hints)

    def _as_integral(self, f, r, k, nu):
        from sympy import besselj
        return Integral(f*besselj(nu, k*r)*r, (r, 0, oo))

    @property
    def as_integral(self):
        return self._as_integral(self.function,
                                 self.function_variable,
                                 self.transform_variable,
                                 self.args[3])


class HankelTransform(HankelTypeTransform):
    """
    Class representing unevaluated Hankel transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute Hankel transforms, see the :func:`hankel_transform`
    docstring.
    """

    _name = 'Hankel'


def hankel_transform(f, r, k, nu, **hints):
    r"""
    Compute the Hankel transform of `f`, defined as

    .. math:: F_\nu(k) = \int_{0}^\infty f(r) J_\nu(k r) r \mathrm{d} r.

    If the transform cannot be computed in closed form, this
    function returns an unevaluated :class:`HankelTransform` object.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.
    Note that for this transform, by default ``noconds=True``.

    >>> from sympy import hankel_transform, inverse_hankel_transform
    >>> from sympy import gamma, exp, sinh, cosh
    >>> from sympy.abc import r, k, m, nu, a

    >>> ht = hankel_transform(1/r**m, r, k, nu)
    >>> ht
    2*2**(-m)*k**(m - 2)*gamma(-m/2 + nu/2 + 1)/gamma(m/2 + nu/2)

    >>> inverse_hankel_transform(ht, k, r, nu)
    r**(-m)

    >>> ht = hankel_transform(exp(-a*r), r, k, 0)
    >>> ht
    a/(k**3*(a**2/k**2 + 1)**(3/2))

    >>> inverse_hankel_transform(ht, k, r, 0)
    exp(-a*r)

    See Also
    ========

    fourier_transform, inverse_fourier_transform
    sine_transform, inverse_sine_transform
    cosine_transform, inverse_cosine_transform
    inverse_hankel_transform
    mellin_transform, laplace_transform
    """
    return HankelTransform(f, r, k, nu).doit(**hints)


class InverseHankelTransform(HankelTypeTransform):
    """
    Class representing unevaluated inverse Hankel transforms.

    For usage of this class, see the :class:`IntegralTransform` docstring.

    For how to compute inverse Hankel transforms, see the
    :func:`inverse_hankel_transform` docstring.
    """

    _name = 'Inverse Hankel'


def inverse_hankel_transform(F, k, r, nu, **hints):
    r"""
    Compute the inverse Hankel transform of `F` defined as

    .. math:: f(r) = \int_{0}^\infty F_\nu(k) J_\nu(k r) k \mathrm{d} k.

    If the transform cannot be computed in closed form, this
    function returns an unevaluated :class:`InverseHankelTransform` object.

    For a description of possible hints, refer to the docstring of
    :func:`sympy.integrals.transforms.IntegralTransform.doit`.
    Note that for this transform, by default ``noconds=True``.

    >>> from sympy import hankel_transform, inverse_hankel_transform, gamma
    >>> from sympy import gamma, exp, sinh, cosh
    >>> from sympy.abc import r, k, m, nu, a

    >>> ht = hankel_transform(1/r**m, r, k, nu)
    >>> ht
    2*2**(-m)*k**(m - 2)*gamma(-m/2 + nu/2 + 1)/gamma(m/2 + nu/2)

    >>> inverse_hankel_transform(ht, k, r, nu)
    r**(-m)

    >>> ht = hankel_transform(exp(-a*r), r, k, 0)
    >>> ht
    a/(k**3*(a**2/k**2 + 1)**(3/2))

    >>> inverse_hankel_transform(ht, k, r, 0)
    exp(-a*r)

    See Also
    ========

    fourier_transform, inverse_fourier_transform
    sine_transform, inverse_sine_transform
    cosine_transform, inverse_cosine_transform
    hankel_transform
    mellin_transform, laplace_transform
    """
    return InverseHankelTransform(F, k, r, nu).doit(**hints)
