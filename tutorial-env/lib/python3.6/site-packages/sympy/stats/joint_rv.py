"""
Joint Random Variables Module

See Also
========
sympy.stats.rv
sympy.stats.frv
sympy.stats.crv
sympy.stats.drv
"""

from __future__ import print_function, division

# __all__ = ['marginal_distribution']

from sympy import (Basic, Lambda, sympify, Indexed, Symbol, ProductSet, S,
 Dummy)
from sympy.concrete.summations import Sum, summation
from sympy.core.compatibility import string_types
from sympy.core.containers import Tuple
from sympy.integrals.integrals import Integral, integrate
from sympy.matrices import ImmutableMatrix
from sympy.stats.crv import (ContinuousDistribution,
    SingleContinuousDistribution, SingleContinuousPSpace)
from sympy.stats.drv import (DiscreteDistribution,
    SingleDiscreteDistribution, SingleDiscretePSpace)
from sympy.stats.rv import (ProductPSpace, NamedArgsMixin,
     ProductDomain, RandomSymbol, random_symbols, SingleDomain)
from sympy.utilities.misc import filldedent


class JointPSpace(ProductPSpace):
    """
    Represents a joint probability space. Represented using symbols for
    each component and a distribution.
    """
    def __new__(cls, sym, dist):
        if isinstance(dist, SingleContinuousDistribution):
            return SingleContinuousPSpace(sym, dist)
        if isinstance(dist, SingleDiscreteDistribution):
            return SingleDiscretePSpace(sym, dist)
        if isinstance(sym, string_types):
            sym = Symbol(sym)
        if not isinstance(sym, Symbol):
            raise TypeError("s should have been string or Symbol")
        return Basic.__new__(cls, sym, dist)

    @property
    def set(self):
        return self.domain.set

    @property
    def symbol(self):
        return self.args[0]

    @property
    def distribution(self):
        return self.args[1]

    @property
    def value(self):
        return JointRandomSymbol(self.symbol, self)

    @property
    def component_count(self):
        _set = self.distribution.set
        return len(_set.args) if isinstance(_set, ProductSet) else 1

    @property
    def pdf(self):
        sym = [Indexed(self.symbol, i) for i in range(self.component_count)]
        return self.distribution(*sym)

    @property
    def domain(self):
        rvs = random_symbols(self.distribution)
        if len(rvs) == 0:
            return SingleDomain(self.symbol, self.set)
        return ProductDomain(*[rv.pspace.domain for rv in rvs])

    def component_domain(self, index):
        return self.set.args[index]

    @property
    def symbols(self):
        return self.domain.symbols

    def marginal_distribution(self, *indices):
        count = self.component_count
        orig = [Indexed(self.symbol, i) for i in range(count)]
        all_syms = [Symbol(str(i)) for i in orig]
        replace_dict = dict(zip(all_syms, orig))
        sym = [Symbol(str(Indexed(self.symbol, i))) for i in indices]
        limits = list([i,] for i in all_syms if i not in sym)
        index = 0
        for i in range(count):
            if i not in indices:
                limits[index].append(self.distribution.set.args[i])
                limits[index] = tuple(limits[index])
                index += 1
        limits = tuple(limits)
        if self.distribution.is_Continuous:
            f = Lambda(sym, integrate(self.distribution(*all_syms), limits))
        elif self.distribution.is_Discrete:
            f = Lambda(sym, summation(self.distribution(all_syms), limits))
        return f.xreplace(replace_dict)

    def compute_expectation(self, expr, rvs=None, evaluate=False, **kwargs):
        syms = tuple(self.value[i] for i in range(self.component_count))
        rvs = rvs or syms
        if not any([i in rvs for i in syms]):
            return expr
        expr = expr*self.pdf
        for rv in rvs:
            if isinstance(rv, Indexed):
                expr = expr.xreplace({rv: Indexed(str(rv.base), rv.args[1])})
            elif isinstance(rv, RandomSymbol):
                expr = expr.xreplace({rv: rv.symbol})
        if self.value in random_symbols(expr):
            raise NotImplementedError(filldedent('''
            Expectations of expression with unindexed joint random symbols
            cannot be calculated yet.'''))
        limits = tuple((Indexed(str(rv.base),rv.args[1]),
            self.distribution.set.args[rv.args[1]]) for rv in syms)
        return Integral(expr, *limits)

    def where(self, condition):
        raise NotImplementedError()

    def compute_density(self, expr):
        raise NotImplementedError()

    def sample(self):
        raise NotImplementedError()

    def probability(self, condition):
        raise NotImplementedError()

class JointDistribution(Basic, NamedArgsMixin):
    """
    Represented by the random variables part of the joint distribution.
    Contains methods for PDF, CDF, sampling, marginal densities, etc.
    """

    _argnames = ('pdf', )

    def __new__(cls, *args):
        args = list(map(sympify, args))
        for i in range(len(args)):
            if isinstance(args[i], list):
                args[i] = ImmutableMatrix(args[i])
        return Basic.__new__(cls, *args)

    @property
    def domain(self):
        return ProductDomain(self.symbols)

    @property
    def pdf(self, *args):
        return self.density.args[1]

    def cdf(self, other):
        assert isinstance(other, dict)
        rvs = other.keys()
        _set = self.domain.set
        expr = self.pdf(tuple(i.args[0] for i in self.symbols))
        for i in range(len(other)):
            if rvs[i].is_Continuous:
                density = Integral(expr, (rvs[i], _set[i].inf,
                    other[rvs[i]]))
            elif rvs[i].is_Discrete:
                density = Sum(expr, (rvs[i], _set[i].inf,
                    other[rvs[i]]))
        return density

    def __call__(self, *args):
        return self.pdf(*args)

class JointRandomSymbol(RandomSymbol):
    """
    Representation of random symbols with joint probability distributions
    to allow indexing."
    """
    def __getitem__(self, key):
        if isinstance(self.pspace, JointPSpace):
            if self.pspace.component_count <= key:
                raise ValueError("Index keys for %s can only up to %s." %
                    (self.name, self.pspace.component_count - 1))
            return Indexed(self, key)

class JointDistributionHandmade(JointDistribution, NamedArgsMixin):

    _argnames = ('pdf',)
    is_Continuous = True

    @property
    def set(self):
        return self.args[1]

def marginal_distribution(rv, *indices):
    """
    Marginal distribution function of a joint random variable.

    Parameters
    ==========

    rv: A random variable with a joint probability distribution.
    indices: component indices or the indexed random symbol
        for whom the joint distribution is to be calculated

    Returns
    =======

    A Lambda expression n `sym`.

    Examples
    ========

    >>> from sympy.stats.crv_types import Normal
    >>> from sympy.stats.joint_rv import marginal_distribution
    >>> m = Normal('X', [1, 2], [[2, 1], [1, 2]])
    >>> marginal_distribution(m, m[0])(1)
    1/(2*sqrt(pi))

    """
    indices = list(indices)
    for i in range(len(indices)):
        if isinstance(indices[i], Indexed):
            indices[i] = indices[i].args[1]
    prob_space = rv.pspace
    if indices == ():
        raise ValueError(
            "At least one component for marginal density is needed.")
    if hasattr(prob_space.distribution, 'marginal_distribution'):
        return prob_space.distribution.marginal_distribution(indices, rv.symbol)
    return prob_space.marginal_distribution(*indices)


class CompoundDistribution(Basic, NamedArgsMixin):
    """
    Represents a compound probability distribution.

    Constructed using a single probability distribution with a parameter
    distributed according to some given distribution.
    """
    def __new__(cls, dist):
        if not isinstance(dist, (ContinuousDistribution, DiscreteDistribution)):
            raise ValueError(filldedent('''CompoundDistribution can only be
             initialized from ContinuousDistribution or DiscreteDistribution
             '''))
        _args = dist.args
        if not any([isinstance(i, RandomSymbol) for i in _args]):
            return dist
        return Basic.__new__(cls, dist)

    @property
    def latent_distributions(self):
        return random_symbols(self.args[0])

    def pdf(self, *x):
        dist = self.args[0]
        z = Dummy('z')
        if isinstance(dist, ContinuousDistribution):
            rv = SingleContinuousPSpace(z, dist).value
        elif isinstance(dist, DiscreteDistribution):
            rv = SingleDiscretePSpace(z, dist).value
        return MarginalDistribution(self, (rv,)).pdf(*x)

    def set(self):
        return self.args[0].set

    def __call__(self, *args):
        return self.pdf(*args)


class MarginalDistribution(Basic):
    """
    Represents the marginal distribution of a joint probability space.

    Initialised using a probability distribution and random variables(or
    their indexed components) which should be a part of the resultant
    distribution.
    """

    def __new__(cls, dist, rvs):
        if not all([isinstance(rv, (Indexed, RandomSymbol))] for rv in rvs):
            raise ValueError(filldedent('''Marginal distribution can be
             intitialised only in terms of random variables or indexed random
             variables'''))
        rvs = Tuple.fromiter(rv for rv in rvs)
        if not isinstance(dist, JointDistribution) and len(random_symbols(dist)) == 0:
            return dist
        return Basic.__new__(cls, dist, rvs)

    def check(self):
        pass

    @property
    def set(self):
        rvs = [i for i in random_symbols(self.args[1])]
        marginalise_out = [i for i in random_symbols(self.args[1]) \
         if i not in self.args[1]]
        for i in rvs:
            if i in marginalise_out:
                rvs.remove(i)
        return ProductSet((i.pspace.set for i in rvs))

    @property
    def symbols(self):
        rvs = self.args[1]
        return set([rv.pspace.symbol for rv in rvs])

    def pdf(self, *x):
        expr, rvs = self.args[0], self.args[1]
        marginalise_out = [i for i in random_symbols(expr) if i not in self.args[1]]
        syms = [i.pspace.symbol for i in self.args[1]]
        for i in expr.atoms(Indexed):
            if isinstance(i, Indexed) and isinstance(i.base, RandomSymbol)\
             and i not in rvs:
                marginalise_out.append(i)
        if isinstance(expr, CompoundDistribution):
            syms = Dummy('x', real=True)
            expr = expr.args[0].pdf(syms)
        elif isinstance(expr, JointDistribution):
            count = len(expr.domain.args)
            x = Dummy('x', real=True, finite=True)
            syms = [Indexed(x, i) for i in count]
            expr = expression.pdf(syms)
        return Lambda(syms, self.compute_pdf(expr, marginalise_out))(*x)

    def compute_pdf(self, expr, rvs):
        for rv in rvs:
            lpdf = 1
            if isinstance(rv, RandomSymbol):
                lpdf = rv.pspace.pdf
            expr = self.marginalise_out(expr*lpdf, rv)
        return expr

    def marginalise_out(self, expr, rv):
        from sympy.concrete.summations import Sum
        if isinstance(rv, RandomSymbol):
            dom = rv.pspace.set
        elif isinstance(rv, Indexed):
            dom = rv.base.component_domain(
                rv.pspace.component_domain(rv.args[1]))
        expr = expr.xreplace({rv: rv.pspace.symbol})
        if rv.pspace.is_Continuous:
            #TODO: Modify to support integration
            #for all kinds of sets.
            expr = Integral(expr, (rv.pspace.symbol, dom))
        elif rv.pspace.is_Discrete:
            #incorporate this into `Sum`/`summation`
            if dom in (S.Integers, S.Naturals, S.Naturals0):
                dom = (dom.inf, dom.sup)
            expr = Sum(expr, (rv.pspace.symbol, dom))
        return expr

    def __call__(self, *args):
        return self.pdf(*args)
