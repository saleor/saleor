from __future__ import print_function, division

from sympy import (factorial, exp, S, sympify, And, I, zeta, polylog, log, beta, hyper, binomial,
                   Piecewise, floor)
from sympy.stats import density
from sympy.stats.drv import SingleDiscreteDistribution, SingleDiscretePSpace
from sympy.stats.joint_rv import JointPSpace, CompoundDistribution
from sympy.stats.rv import _value_check, RandomSymbol
import random

__all__ = ['Geometric', 'Logarithmic', 'NegativeBinomial', 'Poisson', 'YuleSimon', 'Zeta']


def rv(symbol, cls, *args):
    args = list(map(sympify, args))
    dist = cls(*args)
    dist.check(*args)
    pspace = SingleDiscretePSpace(symbol, dist)
    if any(isinstance(arg, RandomSymbol) for arg in args):
        pspace = JointPSpace(symbol, CompoundDistribution(dist))
    return pspace.value


#-------------------------------------------------------------------------------
# Geometric distribution ------------------------------------------------------------

class GeometricDistribution(SingleDiscreteDistribution):
    _argnames = ('p',)
    set = S.Naturals

    @staticmethod
    def check(p):
        _value_check(And(0 < p, p <= 1), "p must be between 0 and 1")

    def pdf(self, k):
        return (1 - self.p)**(k - 1) * self.p

    def _characteristic_function(self, t):
        p = self.p
        return p * exp(I*t) / (1 - (1 - p)*exp(I*t))

    def _moment_generating_function(self, t):
        p = self.p
        return p * exp(t) / (1 - (1 - p) * exp(t))

def Geometric(name, p):
    r"""
    Create a discrete random variable with a Geometric distribution.

    The density of the Geometric distribution is given by

    .. math::
        f(k) := p (1 - p)^{k - 1}

    Parameters
    ==========

    p: A probability between 0 and 1

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Geometric, density, E, variance
    >>> from sympy import Symbol, S

    >>> p = S.One / 5
    >>> z = Symbol("z")

    >>> X = Geometric("x", p)

    >>> density(X)(z)
    (4/5)**(z - 1)/5

    >>> E(X)
    5

    >>> variance(X)
    20

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Geometric_distribution
    .. [2] http://mathworld.wolfram.com/GeometricDistribution.html

    """
    return rv(name, GeometricDistribution, p)


#-------------------------------------------------------------------------------
# Logarithmic distribution ------------------------------------------------------------

class LogarithmicDistribution(SingleDiscreteDistribution):
    _argnames = ('p',)

    set = S.Naturals

    @staticmethod
    def check(p):
        _value_check(And(p > 0, p < 1), "p should be between 0 and 1")

    def pdf(self, k):
        p = self.p
        return (-1) * p**k / (k * log(1 - p))

    def _characteristic_function(self, t):
        p = self.p
        return log(1 - p * exp(I*t)) / log(1 - p)

    def _moment_generating_function(self, t):
        p = self.p
        return log(1 - p * exp(t)) / log(1 - p)

    def sample(self):
        ### TODO
        raise NotImplementedError("Sampling of %s is not implemented" % density(self))


def Logarithmic(name, p):
    r"""
    Create a discrete random variable with a Logarithmic distribution.

    The density of the Logarithmic distribution is given by

    .. math::
        f(k) := \frac{-p^k}{k \ln{(1 - p)}}

    Parameters
    ==========

    p: A value between 0 and 1

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Logarithmic, density, E, variance
    >>> from sympy import Symbol, S

    >>> p = S.One / 5
    >>> z = Symbol("z")

    >>> X = Logarithmic("x", p)

    >>> density(X)(z)
    -5**(-z)/(z*log(4/5))

    >>> E(X)
    -1/(-4*log(5) + 8*log(2))

    >>> variance(X)
    -1/((-4*log(5) + 8*log(2))*(-2*log(5) + 4*log(2))) + 1/(-64*log(2)*log(5) + 64*log(2)**2 + 16*log(5)**2) - 10/(-32*log(5) + 64*log(2))

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Logarithmic_distribution
    .. [2] http://mathworld.wolfram.com/LogarithmicDistribution.html

    """
    return rv(name, LogarithmicDistribution, p)


#-------------------------------------------------------------------------------
# Negative binomial distribution ------------------------------------------------------------

class NegativeBinomialDistribution(SingleDiscreteDistribution):
    _argnames = ('r', 'p')
    set = S.Naturals0

    @staticmethod
    def check(r, p):
        _value_check(r > 0, 'r should be positive')
        _value_check(And(p > 0, p < 1), 'p should be between 0 and 1')

    def pdf(self, k):
        r = self.r
        p = self.p

        return binomial(k + r - 1, k) * (1 - p)**r * p**k

    def _characteristic_function(self, t):
        r = self.r
        p = self.p

        return ((1 - p) / (1 - p * exp(I*t)))**r

    def _moment_generating_function(self, t):
        r = self.r
        p = self.p

        return ((1 - p) / (1 - p * exp(t)))**r

    def sample(self):
        ### TODO
        raise NotImplementedError("Sampling of %s is not implemented" % density(self))


def NegativeBinomial(name, r, p):
    r"""
    Create a discrete random variable with a Negative Binomial distribution.

    The density of the Negative Binomial distribution is given by

    .. math::
        f(k) := \binom{k + r - 1}{k} (1 - p)^r p^k

    Parameters
    ==========

    r: A positive value
    p: A value between 0 and 1

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import NegativeBinomial, density, E, variance
    >>> from sympy import Symbol, S

    >>> r = 5
    >>> p = S.One / 5
    >>> z = Symbol("z")

    >>> X = NegativeBinomial("x", r, p)

    >>> density(X)(z)
    1024*5**(-z)*binomial(z + 4, z)/3125

    >>> E(X)
    5/4

    >>> variance(X)
    25/16

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Negative_binomial_distribution
    .. [2] http://mathworld.wolfram.com/NegativeBinomialDistribution.html

    """
    return rv(name, NegativeBinomialDistribution, r, p)


#-------------------------------------------------------------------------------
# Poisson distribution ------------------------------------------------------------

class PoissonDistribution(SingleDiscreteDistribution):
    _argnames = ('lamda',)

    set = S.Naturals0

    @staticmethod
    def check(lamda):
        _value_check(lamda > 0, "Lambda must be positive")

    def pdf(self, k):
        return self.lamda**k / factorial(k) * exp(-self.lamda)

    def sample(self):
        def search(x, y, u):
            while x < y:
                mid = (x + y)//2
                if u <= self.cdf(mid):
                    y = mid
                else:
                    x = mid + 1
            return x

        u = random.uniform(0, 1)
        if u <= self.cdf(S.Zero):
            return S.Zero
        n = S.One
        while True:
            if u > self.cdf(2*n):
                n *= 2
            else:
                return search(n, 2*n, u)

    def _characteristic_function(self, t):
        return exp(self.lamda * (exp(I*t) - 1))

    def _moment_generating_function(self, t):
        return exp(self.lamda * (exp(t) - 1))


def Poisson(name, lamda):
    r"""
    Create a discrete random variable with a Poisson distribution.

    The density of the Poisson distribution is given by

    .. math::
        f(k) := \frac{\lambda^{k} e^{- \lambda}}{k!}

    Parameters
    ==========

    lamda: Positive number, a rate

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Poisson, density, E, variance
    >>> from sympy import Symbol, simplify

    >>> rate = Symbol("lambda", positive=True)
    >>> z = Symbol("z")

    >>> X = Poisson("x", rate)

    >>> density(X)(z)
    lambda**z*exp(-lambda)/factorial(z)

    >>> E(X)
    lambda

    >>> simplify(variance(X))
    lambda

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Poisson_distribution
    .. [2] http://mathworld.wolfram.com/PoissonDistribution.html

    """
    return rv(name, PoissonDistribution, lamda)


#-------------------------------------------------------------------------------
# Yule-Simon distribution ------------------------------------------------------------

class YuleSimonDistribution(SingleDiscreteDistribution):
    _argnames = ('rho',)
    set = S.Naturals

    @staticmethod
    def check(rho):
        _value_check(rho > 0, 'rho should be positive')

    def pdf(self, k):
        rho = self.rho
        return rho * beta(k, rho + 1)

    def _cdf(self, x):
        return Piecewise((1 - floor(x) * beta(floor(x), self.rho + 1), x >= 1), (0, True))

    def _characteristic_function(self, t):
        rho = self.rho
        return rho * hyper((1, 1), (rho + 2,), exp(I*t)) * exp(I*t) / (rho + 1)

    def _moment_generating_function(self, t):
        rho = self.rho
        return rho * hyper((1, 1), (rho + 2,), exp(t)) * exp(t) / (rho + 1)

    def sample(self):
        ### TODO
        raise NotImplementedError("Sampling of %s is not implemented" % density(self))


def YuleSimon(name, rho):
    r"""
    Create a discrete random variable with a Yule-Simon distribution.

    The density of the Yule-Simon distribution is given by

    .. math::
        f(k) := \rho B(k, \rho + 1)

    Parameters
    ==========

    rho: A positive value

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import YuleSimon, density, E, variance
    >>> from sympy import Symbol, simplify

    >>> p = 5
    >>> z = Symbol("z")

    >>> X = YuleSimon("x", p)

    >>> density(X)(z)
    5*beta(z, 6)

    >>> simplify(E(X))
    5/4

    >>> simplify(variance(X))
    25/48

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Yule%E2%80%93Simon_distribution

    """
    return rv(name, YuleSimonDistribution, rho)


#-------------------------------------------------------------------------------
# Zeta distribution ------------------------------------------------------------

class ZetaDistribution(SingleDiscreteDistribution):
    _argnames = ('s',)
    set = S.Naturals

    @staticmethod
    def check(s):
        _value_check(s > 1, 's should be greater than 1')

    def pdf(self, k):
        s = self.s
        return 1 / (k**s * zeta(s))

    def _characteristic_function(self, t):
        return polylog(self.s, exp(I*t)) / zeta(self.s)

    def _moment_generating_function(self, t):
        return polylog(self.s, exp(t)) / zeta(self.s)

    def sample(self):
        ### TODO
        raise NotImplementedError("Sampling of %s is not implemented" % density(self))


def Zeta(name, s):
    r"""
    Create a discrete random variable with a Zeta distribution.

    The density of the Zeta distribution is given by

    .. math::
        f(k) := \frac{1}{k^s \zeta{(s)}}

    Parameters
    ==========

    s: A value greater than 1

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Zeta, density, E, variance
    >>> from sympy import Symbol

    >>> s = 5
    >>> z = Symbol("z")

    >>> X = Zeta("x", s)

    >>> density(X)(z)
    1/(z**5*zeta(5))

    >>> E(X)
    pi**4/(90*zeta(5))

    >>> variance(X)
    -pi**8/(8100*zeta(5)**2) + zeta(3)/zeta(5)

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Zeta_distribution

    """
    return rv(name, ZetaDistribution, s)
