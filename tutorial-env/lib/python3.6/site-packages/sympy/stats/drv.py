from __future__ import print_function, division

from sympy import (Basic, sympify, symbols, Dummy, Lambda, summation,
                   Piecewise, S, cacheit, Sum, exp, I, Ne, Eq, poly,
                   series, factorial, And)

from sympy.polys.polyerrors import PolynomialError
from sympy.solvers.solveset import solveset
from sympy.stats.crv import reduce_rational_inequalities_wrap
from sympy.stats.rv import (NamedArgsMixin, SinglePSpace, SingleDomain,
                            random_symbols, PSpace, ConditionalDomain, RandomDomain,
                            ProductDomain)
from sympy.stats.symbolic_probability import Probability
from sympy.functions.elementary.integers import floor
from sympy.sets.fancysets import Range, FiniteSet
from sympy.sets.sets import Union
from sympy.sets.contains import Contains
from sympy.utilities import filldedent
import random


class DiscreteDistribution(Basic):
    def __call__(self, *args):
        return self.pdf(*args)


class SingleDiscreteDistribution(DiscreteDistribution, NamedArgsMixin):
    """ Discrete distribution of a single variable

    Serves as superclass for PoissonDistribution etc....

    Provides methods for pdf, cdf, and sampling

    See Also:
        sympy.stats.crv_types.*
    """

    set = S.Integers

    def __new__(cls, *args):
        args = list(map(sympify, args))
        return Basic.__new__(cls, *args)

    @staticmethod
    def check(*args):
        pass

    def sample(self):
        """ A random realization from the distribution """
        icdf = self._inverse_cdf_expression()
        while True:
            sample_ = floor(list(icdf(random.uniform(0, 1)))[0])
            if sample_ >= self.set.inf:
                return sample_

    @cacheit
    def _inverse_cdf_expression(self):
        """ Inverse of the CDF

        Used by sample
        """
        x = symbols('x', positive=True,
         integer=True, cls=Dummy)
        z = symbols('z', positive=True, cls=Dummy)
        cdf_temp = self.cdf(x)
        # Invert CDF
        try:
            inverse_cdf = solveset(cdf_temp - z, x, domain=S.Reals)
        except NotImplementedError:
            inverse_cdf = None
        if not inverse_cdf or len(inverse_cdf.free_symbols) != 1:
            raise NotImplementedError("Could not invert CDF")
        return Lambda(z, inverse_cdf)

    @cacheit
    def compute_cdf(self, **kwargs):
        """ Compute the CDF from the PDF

        Returns a Lambda
        """
        x, z = symbols('x, z', integer=True, finite=True, cls=Dummy)
        left_bound = self.set.inf

        # CDF is integral of PDF from left bound to z
        pdf = self.pdf(x)
        cdf = summation(pdf, (x, left_bound, z), **kwargs)
        # CDF Ensure that CDF left of left_bound is zero
        cdf = Piecewise((cdf, z >= left_bound), (0, True))
        return Lambda(z, cdf)

    def _cdf(self, x):
        return None

    def cdf(self, x, **kwargs):
        """ Cumulative density function """
        if not kwargs:
            cdf = self._cdf(x)
            if cdf is not None:
                return cdf
        return self.compute_cdf(**kwargs)(x)

    @cacheit
    def compute_characteristic_function(self, **kwargs):
        """ Compute the characteristic function from the PDF

        Returns a Lambda
        """
        x, t = symbols('x, t', real=True, finite=True, cls=Dummy)
        pdf = self.pdf(x)
        cf = summation(exp(I*t*x)*pdf, (x, self.set.inf, self.set.sup))
        return Lambda(t, cf)

    def _characteristic_function(self, t):
        return None

    def characteristic_function(self, t, **kwargs):
        """ Characteristic function """
        if not kwargs:
            cf = self._characteristic_function(t)
            if cf is not None:
                return cf
        return self.compute_characteristic_function(**kwargs)(t)

    @cacheit
    def compute_moment_generating_function(self, **kwargs):
        x, t = symbols('x, t', real=True, finite=True, cls=Dummy)
        pdf = self.pdf(x)
        mgf = summation(exp(t*x)*pdf, (x, self.set.inf, self.set.sup))
        return Lambda(t, mgf)

    def _moment_generating_function(self, t):
        return None

    def moment_generating_function(self, t, **kwargs):
        if not kwargs:
            mgf = self._moment_generating_function(t)
            if mgf is not None:
                return mgf
        return self.compute_moment_generating_function(**kwargs)(t)

    def expectation(self, expr, var, evaluate=True, **kwargs):
        """ Expectation of expression over distribution """
        # TODO: support discrete sets with non integer stepsizes

        if evaluate:
            try:
                p = poly(expr, var)

                t = Dummy('t', real=True)

                mgf = self.moment_generating_function(t)
                deg = p.degree()
                taylor = poly(series(mgf, t, 0, deg + 1).removeO(), t)
                result = 0
                for k in range(deg+1):
                    result += p.coeff_monomial(var ** k) * taylor.coeff_monomial(t ** k) * factorial(k)

                return result

            except PolynomialError:
                return summation(expr * self.pdf(var),
                                 (var, self.set.inf, self.set.sup), **kwargs)

        else:
            return Sum(expr * self.pdf(var),
                         (var, self.set.inf, self.set.sup), **kwargs)

    def __call__(self, *args):
        return self.pdf(*args)


class DiscreteDistributionHandmade(SingleDiscreteDistribution):
    _argnames = ('pdf',)

    @property
    def set(self):
        return self.args[1]

    def __new__(cls, pdf, set=S.Integers):
        return Basic.__new__(cls, pdf, set)

class DiscreteDomain(RandomDomain):
    """
    A domain with discrete support with step size one.
    Represented using symbols and Range.
    """
    is_Discrete = True

class SingleDiscreteDomain(DiscreteDomain, SingleDomain):
    def as_boolean(self):
        return Contains(self.symbol, self.set)


class ConditionalDiscreteDomain(DiscreteDomain, ConditionalDomain):
    """
    Domain with discrete support of step size one, that is restricted by
    some condition.
    """
    @property
    def set(self):
        rv = self.symbols
        if len(self.symbols) > 1:
            raise NotImplementedError(filldedent('''
                Multivariate condtional domains are not yet implemented.'''))
        rv = list(rv)[0]
        return reduce_rational_inequalities_wrap(self.condition,
            rv).intersect(self.fulldomain.set)


class DiscretePSpace(PSpace):
    is_real = True
    is_Discrete = True

    @property
    def pdf(self):
        return self.density(*self.symbols)

    def where(self, condition):
        rvs = random_symbols(condition)
        assert all(r.symbol in self.symbols for r in rvs)
        if len(rvs) > 1:
            raise NotImplementedError(filldedent('''Multivariate discrete
            random variables are not yet supported.'''))
        conditional_domain = reduce_rational_inequalities_wrap(condition,
            rvs[0])
        conditional_domain = conditional_domain.intersect(self.domain.set)
        return SingleDiscreteDomain(rvs[0].symbol, conditional_domain)

    def probability(self, condition):
        complement = isinstance(condition, Ne)
        if complement:
            condition = Eq(condition.args[0], condition.args[1])
        try:
            _domain = self.where(condition).set
            if condition == False or _domain is S.EmptySet:
                return S.Zero
            if condition == True or _domain == self.domain.set:
                return S.One
            prob = self.eval_prob(_domain)
        except NotImplementedError:
            from sympy.stats.rv import density
            expr = condition.lhs - condition.rhs
            dens = density(expr)
            if not isinstance(dens, DiscreteDistribution):
                dens = DiscreteDistributionHandmade(dens)
            z = Dummy('z', real = True)
            space = SingleDiscretePSpace(z, dens)
            prob = space.probability(condition.__class__(space.value, 0))
        if prob is None:
            prob = Probability(condition)
        return prob if not complement else S.One - prob

    def eval_prob(self, _domain):
        sym = list(self.symbols)[0]
        if isinstance(_domain, Range):
            n = symbols('n', integer=True, finite=True)
            inf, sup, step = (r for r in _domain.args)
            summand = ((self.pdf).replace(
              sym, n*step))
            rv = summation(summand,
                (n, inf/step, (sup)/step - 1)).doit()
            return rv
        elif isinstance(_domain, FiniteSet):
            pdf = Lambda(sym, self.pdf)
            rv = sum(pdf(x) for x in _domain)
            return rv
        elif isinstance(_domain, Union):
            rv = sum(self.eval_prob(x) for x in _domain.args)
            return rv

    def conditional_space(self, condition):
        density = Lambda(self.symbols, self.pdf/self.probability(condition))
        condition = condition.xreplace(dict((rv, rv.symbol) for rv in self.values))
        domain = ConditionalDiscreteDomain(self.domain, condition)
        return DiscretePSpace(domain, density)

class ProductDiscreteDomain(ProductDomain, DiscreteDomain):
     def as_boolean(self):
        return And(*[domain.as_boolean for domain in self.domains])

class SingleDiscretePSpace(DiscretePSpace, SinglePSpace):
    """ Discrete probability space over a single univariate variable """
    is_real = True

    @property
    def set(self):
        return self.distribution.set

    @property
    def domain(self):
        return SingleDiscreteDomain(self.symbol, self.set)

    def sample(self):
        """
        Internal sample method

        Returns dictionary mapping RandomSymbol to realization value.
        """
        return {self.value: self.distribution.sample()}

    def compute_expectation(self, expr, rvs=None, evaluate=True, **kwargs):
        rvs = rvs or (self.value,)
        if self.value not in rvs:
            return expr

        expr = expr.xreplace(dict((rv, rv.symbol) for rv in rvs))

        x = self.value.symbol
        try:
            return self.distribution.expectation(expr, x, evaluate=evaluate,
                    **kwargs)
        except NotImplementedError:
            return Sum(expr * self.pdf, (x, self.set.inf, self.set.sup),
                    **kwargs)

    def compute_cdf(self, expr, **kwargs):
        if expr == self.value:
            x = symbols("x", real=True, cls=Dummy)
            return Lambda(x, self.distribution.cdf(x, **kwargs))
        else:
            raise NotImplementedError()

    def compute_density(self, expr, **kwargs):
        if expr == self.value:
            return self.distribution
        raise NotImplementedError()

    def compute_characteristic_function(self, expr, **kwargs):
        if expr == self.value:
            t = symbols("t", real=True, cls=Dummy)
            return Lambda(t, self.distribution.characteristic_function(t, **kwargs))
        else:
            raise NotImplementedError()

    def compute_moment_generating_function(self, expr, **kwargs):
        if expr == self.value:
            t = symbols("t", real=True, cls=Dummy)
            return Lambda(t, self.distribution.moment_generating_function(t, **kwargs))
        else:
            raise NotImplementedError()
