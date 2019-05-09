"""
Continuous Random Variables - Prebuilt variables

Contains
========
Arcsin
Benini
Beta
BetaPrime
Cauchy
Chi
ChiNoncentral
ChiSquared
Dagum
Erlang
Exponential
FDistribution
FisherZ
Frechet
Gamma
GammaInverse
Gumbel
Gompertz
Kumaraswamy
Laplace
Logistic
LogNormal
Maxwell
Nakagami
Normal
Pareto
QuadraticU
RaisedCosine
Rayleigh
ShiftedGompertz
StudentT
Trapezoidal
Triangular
Uniform
UniformSum
VonMises
Weibull
WignerSemicircle
"""

from __future__ import print_function, division

from sympy import (log, sqrt, pi, S, Dummy, Interval, sympify, gamma,
                   Piecewise, And, Eq, binomial, factorial, Sum, floor, Abs,
                   Lambda, Basic, lowergamma, erf, erfi, I, hyper, uppergamma,
                   sinh, Ne, expint)

from sympy import beta as beta_fn
from sympy import cos, sin, exp, besseli, besselj, besselk
from sympy.external import import_module
from sympy.matrices import MatrixBase
from sympy.stats.crv import (SingleContinuousPSpace, SingleContinuousDistribution,
        ContinuousDistributionHandmade)
from sympy.stats.joint_rv import JointPSpace, CompoundDistribution
from sympy.stats.joint_rv_types import multivariate_rv
from sympy.stats.rv import _value_check, RandomSymbol
import random

oo = S.Infinity

__all__ = ['ContinuousRV',
'Arcsin',
'Benini',
'Beta',
'BetaPrime',
'Cauchy',
'Chi',
'ChiNoncentral',
'ChiSquared',
'Dagum',
'Erlang',
'Exponential',
'FDistribution',
'FisherZ',
'Frechet',
'Gamma',
'GammaInverse',
'Gompertz',
'Gumbel',
'Kumaraswamy',
'Laplace',
'Logistic',
'LogNormal',
'Maxwell',
'Nakagami',
'Normal',
'Pareto',
'QuadraticU',
'RaisedCosine',
'Rayleigh',
'StudentT',
'ShiftedGompertz',
'Trapezoidal',
'Triangular',
'Uniform',
'UniformSum',
'VonMises',
'Weibull',
'WignerSemicircle'
]



def ContinuousRV(symbol, density, set=Interval(-oo, oo)):
    """
    Creates a Continuous Random Variable given the following:

    -- a symbol
    -- a probability density function
    -- set on which the pdf is valid (defaults to entire real line)

    Returns a RandomSymbol.

    Many common continuous random variable types are already implemented.
    This function should be needed very rarely.

    Examples
    ========

    >>> from sympy import Symbol, sqrt, exp, pi
    >>> from sympy.stats import ContinuousRV, P, E

    >>> x = Symbol("x")

    >>> pdf = sqrt(2)*exp(-x**2/2)/(2*sqrt(pi)) # Normal distribution
    >>> X = ContinuousRV(x, pdf)

    >>> E(X)
    0
    >>> P(X>0)
    1/2
    """
    pdf = Piecewise((density, set.as_relational(symbol)), (0, True))
    pdf = Lambda(symbol, pdf)
    dist = ContinuousDistributionHandmade(pdf, set)
    return SingleContinuousPSpace(symbol, dist).value


def rv(symbol, cls, args):
    args = list(map(sympify, args))
    dist = cls(*args)
    dist.check(*args)
    pspace = SingleContinuousPSpace(symbol, dist)
    if any(isinstance(arg, RandomSymbol) for arg in args):
        pspace = JointPSpace(symbol, CompoundDistribution(dist))
    return pspace.value

########################################
# Continuous Probability Distributions #
########################################

#-------------------------------------------------------------------------------
# Arcsin distribution ----------------------------------------------------------


class ArcsinDistribution(SingleContinuousDistribution):
    _argnames = ('a', 'b')

    def pdf(self, x):
        return 1/(pi*sqrt((x - self.a)*(self.b - x)))

    def _cdf(self, x):
        from sympy import asin
        a, b = self.a, self.b
        return Piecewise(
            (S.Zero, x < a),
            (2*asin(sqrt((x - a)/(b - a)))/pi, x <= b),
            (S.One, True))


def Arcsin(name, a=0, b=1):
    r"""
    Creates a Continuous Random Variable with Arcsine distribution.

    The density of the Arcsine distribution is given by

    .. math::
        f(x) := \frac{1}{\pi\sqrt{(x-a)(b-x)}}

    with :math:`x \in (a,b)`. It must hold that :math:`-\infty < a < b < \infty`.

    Parameters
    ==========

    a : Real number, the left interval boundary
    b : Real number, the right interval boundary

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Arcsin, density, cdf
    >>> from sympy import Symbol, simplify

    >>> a = Symbol("a", real=True)
    >>> b = Symbol("b", real=True)
    >>> z = Symbol("z")

    >>> X = Arcsin("x", a, b)

    >>> density(X)(z)
    1/(pi*sqrt((-a + z)*(b - z)))

    >>> cdf(X)(z)
    Piecewise((0, a > z),
            (2*asin(sqrt((-a + z)/(-a + b)))/pi, b >= z),
            (1, True))


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Arcsine_distribution

    """

    return rv(name, ArcsinDistribution, (a, b))

#-------------------------------------------------------------------------------
# Benini distribution ----------------------------------------------------------


class BeniniDistribution(SingleContinuousDistribution):
    _argnames = ('alpha', 'beta', 'sigma')

    @staticmethod
    def check(alpha, beta, sigma):
        _value_check(alpha > 0, "Shape parameter Alpha must be positive.")
        _value_check(beta > 0, "Shape parameter Beta must be positive.")
        _value_check(sigma > 0, "Scale parameter Sigma must be positive.")

    @property
    def set(self):
        return Interval(self.sigma, oo)

    def pdf(self, x):
        alpha, beta, sigma = self.alpha, self.beta, self.sigma
        return (exp(-alpha*log(x/sigma) - beta*log(x/sigma)**2)
               *(alpha/x + 2*beta*log(x/sigma)/x))

    def _moment_generating_function(self, t):
        raise NotImplementedError('The moment generating function of the '
                                  'Benini distribution does not exist.')

def Benini(name, alpha, beta, sigma):
    r"""
    Creates a Continuous Random Variable with Benini distribution.

    The density of the Benini distribution is given by

    .. math::
        f(x) := e^{-\alpha\log{\frac{x}{\sigma}}
                -\beta\log^2\left[{\frac{x}{\sigma}}\right]}
                \left(\frac{\alpha}{x}+\frac{2\beta\log{\frac{x}{\sigma}}}{x}\right)

    This is a heavy-tailed distrubtion and is also known as the log-Rayleigh
    distribution.

    Parameters
    ==========

    alpha : Real number, `\alpha > 0`, a shape
    beta : Real number, `\beta > 0`, a shape
    sigma : Real number, `\sigma > 0`, a scale

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Benini, density, cdf
    >>> from sympy import Symbol, simplify, pprint

    >>> alpha = Symbol("alpha", positive=True)
    >>> beta = Symbol("beta", positive=True)
    >>> sigma = Symbol("sigma", positive=True)
    >>> z = Symbol("z")

    >>> X = Benini("x", alpha, beta, sigma)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
    /                  /  z  \\             /  z  \            2/  z  \
    |        2*beta*log|-----||  - alpha*log|-----| - beta*log  |-----|
    |alpha             \sigma/|             \sigma/             \sigma/
    |----- + -----------------|*e
    \  z             z        /

    >>> cdf(X)(z)
    Piecewise((1 - exp(-alpha*log(z/sigma) - beta*log(z/sigma)**2), sigma <= z),
            (0, True))


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Benini_distribution
    .. [2] http://reference.wolfram.com/legacy/v8/ref/BeniniDistribution.html

    """

    return rv(name, BeniniDistribution, (alpha, beta, sigma))

#-------------------------------------------------------------------------------
# Beta distribution ------------------------------------------------------------


class BetaDistribution(SingleContinuousDistribution):
    _argnames = ('alpha', 'beta')

    set = Interval(0, 1)

    @staticmethod
    def check(alpha, beta):
        _value_check(alpha > 0, "Shape parameter Alpha must be positive.")
        _value_check(beta > 0, "Shape parameter Beta must be positive.")

    def pdf(self, x):
        alpha, beta = self.alpha, self.beta
        return x**(alpha - 1) * (1 - x)**(beta - 1) / beta_fn(alpha, beta)

    def sample(self):
        return random.betavariate(self.alpha, self.beta)

    def _characteristic_function(self, t):
        return hyper((self.alpha,), (self.alpha + self.beta,), I*t)

    def _moment_generating_function(self, t):
        return hyper((self.alpha,), (self.alpha + self.beta,), t)

def Beta(name, alpha, beta):
    r"""
    Creates a Continuous Random Variable with Beta distribution.

    The density of the Beta distribution is given by

    .. math::
        f(x) := \frac{x^{\alpha-1}(1-x)^{\beta-1}} {\mathrm{B}(\alpha,\beta)}

    with :math:`x \in [0,1]`.

    Parameters
    ==========

    alpha : Real number, `\alpha > 0`, a shape
    beta : Real number, `\beta > 0`, a shape

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Beta, density, E, variance
    >>> from sympy import Symbol, simplify, pprint, factor

    >>> alpha = Symbol("alpha", positive=True)
    >>> beta = Symbol("beta", positive=True)
    >>> z = Symbol("z")

    >>> X = Beta("x", alpha, beta)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
     alpha - 1        beta - 1
    z         *(1 - z)
    --------------------------
          B(alpha, beta)

    >>> simplify(E(X))
    alpha/(alpha + beta)

    >>> factor(simplify(variance(X)))  #doctest: +SKIP
    alpha*beta/((alpha + beta)**2*(alpha + beta + 1))

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Beta_distribution
    .. [2] http://mathworld.wolfram.com/BetaDistribution.html

    """

    return rv(name, BetaDistribution, (alpha, beta))

#-------------------------------------------------------------------------------
# Beta prime distribution ------------------------------------------------------


class BetaPrimeDistribution(SingleContinuousDistribution):
    _argnames = ('alpha', 'beta')

    @staticmethod
    def check(alpha, beta):
        _value_check(alpha > 0, "Shape parameter Alpha must be positive.")
        _value_check(beta > 0, "Shape parameter Beta must be positive.")

    set = Interval(0, oo)

    def pdf(self, x):
        alpha, beta = self.alpha, self.beta
        return x**(alpha - 1)*(1 + x)**(-alpha - beta)/beta_fn(alpha, beta)

def BetaPrime(name, alpha, beta):
    r"""
    Creates a Continuous Random Variable with Beta prime distribution.

    The density of the Beta prime distribution is given by

    .. math::
        f(x) := \frac{x^{\alpha-1} (1+x)^{-\alpha -\beta}}{B(\alpha,\beta)}

    with :math:`x > 0`.

    Parameters
    ==========

    alpha : Real number, `\alpha > 0`, a shape
    beta : Real number, `\beta > 0`, a shape

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import BetaPrime, density
    >>> from sympy import Symbol, pprint

    >>> alpha = Symbol("alpha", positive=True)
    >>> beta = Symbol("beta", positive=True)
    >>> z = Symbol("z")

    >>> X = BetaPrime("x", alpha, beta)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
     alpha - 1        -alpha - beta
    z         *(z + 1)
    -------------------------------
             B(alpha, beta)

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Beta_prime_distribution
    .. [2] http://mathworld.wolfram.com/BetaPrimeDistribution.html

    """

    return rv(name, BetaPrimeDistribution, (alpha, beta))

#-------------------------------------------------------------------------------
# Cauchy distribution ----------------------------------------------------------


class CauchyDistribution(SingleContinuousDistribution):
    _argnames = ('x0', 'gamma')

    @staticmethod
    def check(x0, gamma):
        _value_check(gamma > 0, "Scale parameter Gamma must be positive.")

    def pdf(self, x):
        return 1/(pi*self.gamma*(1 + ((x - self.x0)/self.gamma)**2))

    def _characteristic_function(self, t):
        return exp(self.x0 * I * t -  self.gamma * Abs(t))

    def _moment_generating_function(self, t):
        raise NotImplementedError("The moment generating function for the "
                                  "Cauchy distribution does not exist.")

def Cauchy(name, x0, gamma):
    r"""
    Creates a Continuous Random Variable with Cauchy distribution.

    The density of the Cauchy distribution is given by

    .. math::
        f(x) := \frac{1}{\pi \gamma [1 + {(\frac{x-x_0}{\gamma})}^2]}

    Parameters
    ==========

    x0 : Real number, the location
    gamma : Real number, `\gamma > 0`, a scale

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Cauchy, density
    >>> from sympy import Symbol

    >>> x0 = Symbol("x0")
    >>> gamma = Symbol("gamma", positive=True)
    >>> z = Symbol("z")

    >>> X = Cauchy("x", x0, gamma)

    >>> density(X)(z)
    1/(pi*gamma*(1 + (-x0 + z)**2/gamma**2))

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Cauchy_distribution
    .. [2] http://mathworld.wolfram.com/CauchyDistribution.html

    """

    return rv(name, CauchyDistribution, (x0, gamma))

#-------------------------------------------------------------------------------
# Chi distribution -------------------------------------------------------------


class ChiDistribution(SingleContinuousDistribution):
    _argnames = ('k',)

    @staticmethod
    def check(k):
        _value_check(k > 0, "Number of degrees of freedom (k) must be positive.")
        _value_check(k.is_integer, "Number of degrees of freedom (k) must be an integer.")

    set = Interval(0, oo)

    def pdf(self, x):
        return 2**(1 - self.k/2)*x**(self.k - 1)*exp(-x**2/2)/gamma(self.k/2)

    def _characteristic_function(self, t):
        k = self.k

        part_1 = hyper((k/2,), (S(1)/2,), -t**2/2)
        part_2 = I*t*sqrt(2)*gamma((k+1)/2)/gamma(k/2)
        part_3 = hyper(((k+1)/2,), (S(3)/2,), -t**2/2)
        return part_1 + part_2*part_3

    def _moment_generating_function(self, t):
        k = self.k

        part_1 = hyper((k / 2,), (S(1) / 2,), t ** 2 / 2)
        part_2 = t * sqrt(2) * gamma((k + 1) / 2) / gamma(k / 2)
        part_3 = hyper(((k + 1) / 2,), (S(3) / 2,), t ** 2 / 2)
        return part_1 + part_2 * part_3

def Chi(name, k):
    r"""
    Creates a Continuous Random Variable with Chi distribution.

    The density of the Chi distribution is given by

    .. math::
        f(x) := \frac{2^{1-k/2}x^{k-1}e^{-x^2/2}}{\Gamma(k/2)}

    with :math:`x \geq 0`.

    Parameters
    ==========

    k : Positive integer, The number of degrees of freedom

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Chi, density, E
    >>> from sympy import Symbol, simplify

    >>> k = Symbol("k", integer=True)
    >>> z = Symbol("z")

    >>> X = Chi("x", k)

    >>> density(X)(z)
    2**(1 - k/2)*z**(k - 1)*exp(-z**2/2)/gamma(k/2)

    >>> simplify(E(X))
    sqrt(2)*gamma(k/2 + 1/2)/gamma(k/2)

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Chi_distribution
    .. [2] http://mathworld.wolfram.com/ChiDistribution.html

    """

    return rv(name, ChiDistribution, (k,))

#-------------------------------------------------------------------------------
# Non-central Chi distribution -------------------------------------------------


class ChiNoncentralDistribution(SingleContinuousDistribution):
    _argnames = ('k', 'l')

    @staticmethod
    def check(k, l):
        _value_check(k > 0, "Number of degrees of freedom (k) must be positive.")
        _value_check(k.is_integer, "Number of degrees of freedom (k) must be an integer.")
        _value_check(l > 0, "Shift parameter Lambda must be positive.")

    set = Interval(0, oo)

    def pdf(self, x):
        k, l = self.k, self.l
        return exp(-(x**2+l**2)/2)*x**k*l / (l*x)**(k/2) * besseli(k/2-1, l*x)

def ChiNoncentral(name, k, l):
    r"""
    Creates a Continuous Random Variable with Non-central Chi distribution.

    The density of the Non-central Chi distribution is given by

    .. math::
        f(x) := \frac{e^{-(x^2+\lambda^2)/2} x^k\lambda}
                {(\lambda x)^{k/2}} I_{k/2-1}(\lambda x)

    with `x \geq 0`. Here, `I_\nu (x)` is the
    :ref:`modified Bessel function of the first kind <besseli>`.

    Parameters
    ==========

    k : A positive Integer, `k > 0`, the number of degrees of freedom
    lambda : Real number, `\lambda > 0`, Shift parameter

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import ChiNoncentral, density
    >>> from sympy import Symbol

    >>> k = Symbol("k", integer=True)
    >>> l = Symbol("l")
    >>> z = Symbol("z")

    >>> X = ChiNoncentral("x", k, l)

    >>> density(X)(z)
    l*z**k*(l*z)**(-k/2)*exp(-l**2/2 - z**2/2)*besseli(k/2 - 1, l*z)

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Noncentral_chi_distribution
    """

    return rv(name, ChiNoncentralDistribution, (k, l))

#-------------------------------------------------------------------------------
# Chi squared distribution -----------------------------------------------------


class ChiSquaredDistribution(SingleContinuousDistribution):
    _argnames = ('k',)

    @staticmethod
    def check(k):
        _value_check(k > 0, "Number of degrees of freedom (k) must be positive.")
        _value_check(k.is_integer, "Number of degrees of freedom (k) must be an integer.")

    set = Interval(0, oo)

    def pdf(self, x):
        k = self.k
        return 1/(2**(k/2)*gamma(k/2))*x**(k/2 - 1)*exp(-x/2)

    def _cdf(self, x):
        k = self.k
        return Piecewise(
                (S.One/gamma(k/2)*lowergamma(k/2, x/2), x >= 0),
                (0, True)
        )

    def _characteristic_function(self, t):
        return (1 - 2*I*t)**(-self.k/2)

    def  _moment_generating_function(self, t):
        return (1 - 2*t)**(-self.k/2)

def ChiSquared(name, k):
    r"""
    Creates a Continuous Random Variable with Chi-squared distribution.

    The density of the Chi-squared distribution is given by

    .. math::
        f(x) := \frac{1}{2^{\frac{k}{2}}\Gamma\left(\frac{k}{2}\right)}
                x^{\frac{k}{2}-1} e^{-\frac{x}{2}}

    with :math:`x \geq 0`.

    Parameters
    ==========

    k : Positive integer, The number of degrees of freedom

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import ChiSquared, density, E, variance, moment
    >>> from sympy import Symbol

    >>> k = Symbol("k", integer=True, positive=True)
    >>> z = Symbol("z")

    >>> X = ChiSquared("x", k)

    >>> density(X)(z)
    2**(-k/2)*z**(k/2 - 1)*exp(-z/2)/gamma(k/2)

    >>> E(X)
    k

    >>> variance(X)
    2*k

    >>> moment(X, 3)
    k**3 + 6*k**2 + 8*k

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Chi_squared_distribution
    .. [2] http://mathworld.wolfram.com/Chi-SquaredDistribution.html
    """

    return rv(name, ChiSquaredDistribution, (k, ))

#-------------------------------------------------------------------------------
# Dagum distribution -----------------------------------------------------------


class DagumDistribution(SingleContinuousDistribution):
    _argnames = ('p', 'a', 'b')

    @staticmethod
    def check(p, a, b):
        _value_check(p > 0, "Shape parameter p must be positive.")
        _value_check(a > 0, "Shape parameter a must be positive.")
        _value_check(b > 0, "Scale parameter b must be positive.")

    def pdf(self, x):
        p, a, b = self.p, self.a, self.b
        return a*p/x*((x/b)**(a*p)/(((x/b)**a + 1)**(p + 1)))

    def _cdf(self, x):
        p, a, b = self.p, self.a, self.b
        return Piecewise(((S.One + (S(x)/b)**-a)**-p, x>=0),
                    (S.Zero, True))

def Dagum(name, p, a, b):
    r"""
    Creates a Continuous Random Variable with Dagum distribution.

    The density of the Dagum distribution is given by

    .. math::
        f(x) := \frac{a p}{x} \left( \frac{\left(\tfrac{x}{b}\right)^{a p}}
                {\left(\left(\tfrac{x}{b}\right)^a + 1 \right)^{p+1}} \right)

    with :math:`x > 0`.

    Parameters
    ==========

    p : Real number, `p > 0`, a shape
    a : Real number, `a > 0`, a shape
    b : Real number, `b > 0`, a scale

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Dagum, density, cdf
    >>> from sympy import Symbol

    >>> p = Symbol("p", positive=True)
    >>> a = Symbol("a", positive=True)
    >>> b = Symbol("b", positive=True)
    >>> z = Symbol("z")

    >>> X = Dagum("x", p, a, b)

    >>> density(X)(z)
    a*p*(z/b)**(a*p)*((z/b)**a + 1)**(-p - 1)/z

    >>> cdf(X)(z)
    Piecewise(((1 + (z/b)**(-a))**(-p), z >= 0), (0, True))


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Dagum_distribution

    """

    return rv(name, DagumDistribution, (p, a, b))

#-------------------------------------------------------------------------------
# Erlang distribution ----------------------------------------------------------


def Erlang(name, k, l):
    r"""
    Creates a Continuous Random Variable with Erlang distribution.

    The density of the Erlang distribution is given by

    .. math::
        f(x) := \frac{\lambda^k x^{k-1} e^{-\lambda x}}{(k-1)!}

    with :math:`x \in [0,\infty]`.

    Parameters
    ==========

    k : Positive integer
    l : Real number, `\lambda > 0`, the rate

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Erlang, density, cdf, E, variance
    >>> from sympy import Symbol, simplify, pprint

    >>> k = Symbol("k", integer=True, positive=True)
    >>> l = Symbol("l", positive=True)
    >>> z = Symbol("z")

    >>> X = Erlang("x", k, l)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
     k  k - 1  -l*z
    l *z     *e
    ---------------
        Gamma(k)

    >>> C = cdf(X)(z)
    >>> pprint(C, use_unicode=False)
    /lowergamma(k, l*z)
    |------------------  for z > 0
    <     Gamma(k)
    |
    \        0           otherwise


    >>> E(X)
    k/l

    >>> simplify(variance(X))
    k/l**2

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Erlang_distribution
    .. [2] http://mathworld.wolfram.com/ErlangDistribution.html

    """

    return rv(name, GammaDistribution, (k, S.One/l))

#-------------------------------------------------------------------------------
# Exponential distribution -----------------------------------------------------


class ExponentialDistribution(SingleContinuousDistribution):
    _argnames = ('rate',)

    set  = Interval(0, oo)

    @staticmethod
    def check(rate):
        _value_check(rate > 0, "Rate must be positive.")

    def pdf(self, x):
        return self.rate * exp(-self.rate*x)

    def sample(self):
        return random.expovariate(self.rate)

    def _cdf(self, x):
        return Piecewise(
                (S.One - exp(-self.rate*x), x >= 0),
                (0, True),
        )

    def _characteristic_function(self, t):
        rate = self.rate
        return rate / (rate - I*t)

    def _moment_generating_function(self, t):
        rate = self.rate
        return rate / (rate - t)

def Exponential(name, rate):
    r"""
    Create a continuous random variable with an Exponential distribution.

    The density of the exponential distribution is given by

    .. math::
        f(x) := \lambda \exp(-\lambda x)

    with `x > 0`. Note that the expected value is `1/\lambda`.

    Parameters
    ==========

    rate : A positive Real number, `\lambda > 0`, the rate (or inverse scale/inverse mean)

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Exponential, density, cdf, E
    >>> from sympy.stats import variance, std, skewness
    >>> from sympy import Symbol

    >>> l = Symbol("lambda", positive=True)
    >>> z = Symbol("z")

    >>> X = Exponential("x", l)

    >>> density(X)(z)
    lambda*exp(-lambda*z)

    >>> cdf(X)(z)
    Piecewise((1 - exp(-lambda*z), z >= 0), (0, True))

    >>> E(X)
    1/lambda

    >>> variance(X)
    lambda**(-2)

    >>> skewness(X)
    2

    >>> X = Exponential('x', 10)

    >>> density(X)(z)
    10*exp(-10*z)

    >>> E(X)
    1/10

    >>> std(X)
    1/10

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Exponential_distribution
    .. [2] http://mathworld.wolfram.com/ExponentialDistribution.html

    """

    return rv(name, ExponentialDistribution, (rate, ))

#-------------------------------------------------------------------------------
# F distribution ---------------------------------------------------------------


class FDistributionDistribution(SingleContinuousDistribution):
    _argnames = ('d1', 'd2')

    set = Interval(0, oo)

    def pdf(self, x):
        d1, d2 = self.d1, self.d2
        return (sqrt((d1*x)**d1*d2**d2 / (d1*x+d2)**(d1+d2))
               / (x * beta_fn(d1/2, d2/2)))

    def _moment_generating_function(self, t):
        raise NotImplementedError('The moment generating function for the '
                                  'F-distribution does not exist.')

def FDistribution(name, d1, d2):
    r"""
    Create a continuous random variable with a F distribution.

    The density of the F distribution is given by

    .. math::
        f(x) := \frac{\sqrt{\frac{(d_1 x)^{d_1} d_2^{d_2}}
                {(d_1 x + d_2)^{d_1 + d_2}}}}
                {x \mathrm{B} \left(\frac{d_1}{2}, \frac{d_2}{2}\right)}

    with :math:`x > 0`.

    Parameters
    ==========

    d1 : `d_1 > 0`, where d_1 is the degrees of freedom (n_1 - 1)
    d2 : `d_2 > 0`, where d_2 is the degrees of freedom (n_2 - 1)

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import FDistribution, density
    >>> from sympy import Symbol, simplify, pprint

    >>> d1 = Symbol("d1", positive=True)
    >>> d2 = Symbol("d2", positive=True)
    >>> z = Symbol("z")

    >>> X = FDistribution("x", d1, d2)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
      d2
      --    ______________________________
      2    /       d1            -d1 - d2
    d2  *\/  (d1*z)  *(d1*z + d2)
    --------------------------------------
                    /d1  d2\
                 z*B|--, --|
                    \2   2 /

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/F-distribution
    .. [2] http://mathworld.wolfram.com/F-Distribution.html

    """

    return rv(name, FDistributionDistribution, (d1, d2))

#-------------------------------------------------------------------------------
# Fisher Z distribution --------------------------------------------------------

class FisherZDistribution(SingleContinuousDistribution):
    _argnames = ('d1', 'd2')

    def pdf(self, x):
        d1, d2 = self.d1, self.d2
        return (2*d1**(d1/2)*d2**(d2/2) / beta_fn(d1/2, d2/2) *
               exp(d1*x) / (d1*exp(2*x)+d2)**((d1+d2)/2))

def FisherZ(name, d1, d2):
    r"""
    Create a Continuous Random Variable with an Fisher's Z distribution.

    The density of the Fisher's Z distribution is given by

    .. math::
        f(x) := \frac{2d_1^{d_1/2} d_2^{d_2/2}} {\mathrm{B}(d_1/2, d_2/2)}
                \frac{e^{d_1z}}{\left(d_1e^{2z}+d_2\right)^{\left(d_1+d_2\right)/2}}


    .. TODO - What is the difference between these degrees of freedom?

    Parameters
    ==========

    d1 : `d_1 > 0`, degree of freedom
    d2 : `d_2 > 0`, degree of freedom

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import FisherZ, density
    >>> from sympy import Symbol, simplify, pprint

    >>> d1 = Symbol("d1", positive=True)
    >>> d2 = Symbol("d2", positive=True)
    >>> z = Symbol("z")

    >>> X = FisherZ("x", d1, d2)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
                                d1   d2
        d1   d2               - -- - --
        --   --                 2    2
        2    2  /    2*z     \           d1*z
    2*d1  *d2  *\d1*e    + d2/         *e
    -----------------------------------------
                     /d1  d2\
                    B|--, --|
                     \2   2 /

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Fisher%27s_z-distribution
    .. [2] http://mathworld.wolfram.com/Fishersz-Distribution.html

    """

    return rv(name, FisherZDistribution, (d1, d2))

#-------------------------------------------------------------------------------
# Frechet distribution ---------------------------------------------------------

class FrechetDistribution(SingleContinuousDistribution):
    _argnames = ('a', 's', 'm')

    set = Interval(0, oo)

    def __new__(cls, a, s=1, m=0):
        a, s, m = list(map(sympify, (a, s, m)))
        return Basic.__new__(cls, a, s, m)

    def pdf(self, x):
        a, s, m = self.a, self.s, self.m
        return a/s * ((x-m)/s)**(-1-a) * exp(-((x-m)/s)**(-a))

    def _cdf(self, x):
        a, s, m = self.a, self.s, self.m
        return Piecewise((exp(-((x-m)/s)**(-a)), x >= m),
                        (S.Zero, True))

def Frechet(name, a, s=1, m=0):
    r"""
    Create a continuous random variable with a Frechet distribution.

    The density of the Frechet distribution is given by

    .. math::
        f(x) := \frac{\alpha}{s} \left(\frac{x-m}{s}\right)^{-1-\alpha}
                 e^{-(\frac{x-m}{s})^{-\alpha}}

    with :math:`x \geq m`.

    Parameters
    ==========

    a : Real number, :math:`a \in \left(0, \infty\right)` the shape
    s : Real number, :math:`s \in \left(0, \infty\right)` the scale
    m : Real number, :math:`m \in \left(-\infty, \infty\right)` the minimum

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Frechet, density, E, std, cdf
    >>> from sympy import Symbol, simplify

    >>> a = Symbol("a", positive=True)
    >>> s = Symbol("s", positive=True)
    >>> m = Symbol("m", real=True)
    >>> z = Symbol("z")

    >>> X = Frechet("x", a, s, m)

    >>> density(X)(z)
    a*((-m + z)/s)**(-a - 1)*exp(-((-m + z)/s)**(-a))/s

    >>> cdf(X)(z)
     Piecewise((exp(-((-m + z)/s)**(-a)), m <= z), (0, True))

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Fr%C3%A9chet_distribution

    """

    return rv(name, FrechetDistribution, (a, s, m))

#-------------------------------------------------------------------------------
# Gamma distribution -----------------------------------------------------------


class GammaDistribution(SingleContinuousDistribution):
    _argnames = ('k', 'theta')

    set = Interval(0, oo)

    @staticmethod
    def check(k, theta):
        _value_check(k > 0, "k must be positive")
        _value_check(theta > 0, "Theta must be positive")

    def pdf(self, x):
        k, theta = self.k, self.theta
        return x**(k - 1) * exp(-x/theta) / (gamma(k)*theta**k)

    def sample(self):
        return random.gammavariate(self.k, self.theta)

    def _cdf(self, x):
        k, theta = self.k, self.theta
        return Piecewise(
                    (lowergamma(k, S(x)/theta)/gamma(k), x > 0),
                    (S.Zero, True))

    def _characteristic_function(self, t):
        return (1 - self.theta*I*t)**(-self.k)

    def _moment_generating_function(self, t):
        return (1- self.theta*t)**(-self.k)

def Gamma(name, k, theta):
    r"""
    Create a continuous random variable with a Gamma distribution.

    The density of the Gamma distribution is given by

    .. math::
        f(x) := \frac{1}{\Gamma(k) \theta^k} x^{k - 1} e^{-\frac{x}{\theta}}

    with :math:`x \in [0,1]`.

    Parameters
    ==========

    k : Real number, `k > 0`, a shape
    theta : Real number, `\theta > 0`, a scale

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Gamma, density, cdf, E, variance
    >>> from sympy import Symbol, pprint, simplify

    >>> k = Symbol("k", positive=True)
    >>> theta = Symbol("theta", positive=True)
    >>> z = Symbol("z")

    >>> X = Gamma("x", k, theta)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
                      -z
                    -----
         -k  k - 1  theta
    theta  *z     *e
    ---------------------
           Gamma(k)

    >>> C = cdf(X, meijerg=True)(z)
    >>> pprint(C, use_unicode=False)
    /            /     z  \
    |k*lowergamma|k, -----|
    |            \   theta/
    <----------------------  for z >= 0
    |     Gamma(k + 1)
    |
    \          0             otherwise

    >>> E(X)
    k*theta

    >>> V = simplify(variance(X))
    >>> pprint(V, use_unicode=False)
           2
    k*theta


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Gamma_distribution
    .. [2] http://mathworld.wolfram.com/GammaDistribution.html

    """

    return rv(name, GammaDistribution, (k, theta))

#-------------------------------------------------------------------------------
# Inverse Gamma distribution ---------------------------------------------------


class GammaInverseDistribution(SingleContinuousDistribution):
    _argnames = ('a', 'b')

    set = Interval(0, oo)

    @staticmethod
    def check(a, b):
        _value_check(a > 0, "alpha must be positive")
        _value_check(b > 0, "beta must be positive")

    def pdf(self, x):
        a, b = self.a, self.b
        return b**a/gamma(a) * x**(-a-1) * exp(-b/x)

    def _cdf(self, x):
        a, b = self.a, self.b
        return Piecewise((uppergamma(a,b/x)/gamma(a), x > 0),
                        (S.Zero, True))

    def sample(self):
        scipy = import_module('scipy')
        if scipy:
            from scipy.stats import invgamma
            return invgamma.rvs(float(self.a), 0, float(self.b))
        else:
            raise NotImplementedError('Sampling the inverse Gamma Distribution requires Scipy.')

    def _characteristic_function(self, t):
        a, b = self.a, self.b
        return 2 * (-I*b*t)**(a/2) * besselk(sqrt(-4*I*b*t)) / gamma(a)

    def _moment_generating_function(self, t):
        raise NotImplementedError('The moment generating function for the '
                                  'gamma inverse distribution does not exist.')

def GammaInverse(name, a, b):
    r"""
    Create a continuous random variable with an inverse Gamma distribution.

    The density of the inverse Gamma distribution is given by

    .. math::
        f(x) := \frac{\beta^\alpha}{\Gamma(\alpha)} x^{-\alpha - 1}
                \exp\left(\frac{-\beta}{x}\right)

    with :math:`x > 0`.

    Parameters
    ==========

    a : Real number, `a > 0` a shape
    b : Real number, `b > 0` a scale

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import GammaInverse, density, cdf, E, variance
    >>> from sympy import Symbol, pprint

    >>> a = Symbol("a", positive=True)
    >>> b = Symbol("b", positive=True)
    >>> z = Symbol("z")

    >>> X = GammaInverse("x", a, b)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
                -b
                ---
     a  -a - 1   z
    b *z      *e
    ---------------
       Gamma(a)

    >>> cdf(X)(z)
    Piecewise((uppergamma(a, b/z)/gamma(a), z > 0), (0, True))


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Inverse-gamma_distribution

    """

    return rv(name, GammaInverseDistribution, (a, b))

#-------------------------------------------------------------------------------
# Gumbel distribution --------------------------------------------------------


class GumbelDistribution(SingleContinuousDistribution):
    _argnames = ('beta', 'mu')

    set = Interval(-oo, oo)

    def pdf(self, x):
        beta, mu = self.beta, self.mu
        z = (x - mu)/beta
        return (1/beta)*exp(-(z + exp(-z)))

    def _cdf(self, x):
        beta, mu = self.beta, self.mu
        return exp(-exp((mu - x)/beta))

    def _characteristic_function(self, t):
        return gamma(1 - I*self.beta*t) * exp(I*self.mu*t)

    def _moment_generating_function(self, t):
        return gamma(1 - self.beta*t) * exp(I*self.mu*t)

def Gumbel(name, beta, mu):
    r"""
    Create a Continuous Random Variable with Gumbel distribution.

    The density of the Gumbel distribution is given by

    .. math::
        f(x) := \dfrac{1}{\beta} \exp \left( -\dfrac{x-\mu}{\beta}
                - \exp \left( -\dfrac{x - \mu}{\beta} \right) \right)

    with :math:`x \in [ - \infty, \infty ]`.

    Parameters
    ==========

    mu: Real number, 'mu' is a location
    beta: Real number, 'beta > 0' is a scale

    Returns
    ==========

    A RandomSymbol

    Examples
    ==========
    >>> from sympy.stats import Gumbel, density, E, variance, cdf
    >>> from sympy import Symbol, simplify, pprint
    >>> x = Symbol("x")
    >>> mu = Symbol("mu")
    >>> beta = Symbol("beta", positive=True)
    >>> X = Gumbel("x", beta, mu)
    >>> density(X)(x)
    exp(-exp(-(-mu + x)/beta) - (-mu + x)/beta)/beta
    >>> cdf(X)(x)
    exp(-exp((mu - x)/beta))

    References
    ==========

    .. [1] http://mathworld.wolfram.com/GumbelDistribution.html
    .. [2] https://en.wikipedia.org/wiki/Gumbel_distribution

    """
    return rv(name, GumbelDistribution, (beta, mu))

#-------------------------------------------------------------------------------
# Gompertz distribution --------------------------------------------------------

class GompertzDistribution(SingleContinuousDistribution):
    _argnames = ('b', 'eta')

    set = Interval(0, oo)

    @staticmethod
    def check(b, eta):
        _value_check(b > 0, "b must be positive")
        _value_check(eta > 0, "eta must be positive")

    def pdf(self, x):
        eta, b = self.eta, self.b
        return b*eta*exp(b*x)*exp(eta)*exp(-eta*exp(b*x))

    def _moment_generating_function(self, t):
        eta, b = self.eta, self.b
        return eta * exp(eta) * expint(t/b, eta)

def Gompertz(name, b, eta):
    r"""
    Create a Continuous Random Variable with Gompertz distribution.

    The density of the Gompertz distribution is given by

    .. math::
        f(x) := b \eta e^{b x} e^{\eta} \exp \left(-\eta e^{bx} \right)

    with :math: 'x \in [0, \inf)'.

    Parameters
    ==========

    b: Real number, 'b > 0' a scale
    eta: Real number, 'eta > 0' a shape

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Gompertz, density, E, variance
    >>> from sympy import Symbol, simplify, pprint

    >>> b = Symbol("b", positive=True)
    >>> eta = Symbol("eta", positive=True)
    >>> z = Symbol("z")

    >>> X = Gompertz("x", b, eta)

    >>> density(X)(z)
    b*eta*exp(eta)*exp(b*z)*exp(-eta*exp(b*z))

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Gompertz_distribution

    """
    return rv(name, GompertzDistribution, (b, eta))

#-------------------------------------------------------------------------------
# Kumaraswamy distribution -----------------------------------------------------


class KumaraswamyDistribution(SingleContinuousDistribution):
    _argnames = ('a', 'b')

    set = Interval(0, oo)

    @staticmethod
    def check(a, b):
        _value_check(a > 0, "a must be positive")
        _value_check(b > 0, "b must be positive")

    def pdf(self, x):
        a, b = self.a, self.b
        return a * b * x**(a-1) * (1-x**a)**(b-1)

    def _cdf(self, x):
        a, b = self.a, self.b
        return Piecewise(
            (S.Zero, x < S.Zero),
            (1 - (1 - x**a)**b, x <= S.One),
            (S.One, True))

def Kumaraswamy(name, a, b):
    r"""
    Create a Continuous Random Variable with a Kumaraswamy distribution.

    The density of the Kumaraswamy distribution is given by

    .. math::
        f(x) := a b x^{a-1} (1-x^a)^{b-1}

    with :math:`x \in [0,1]`.

    Parameters
    ==========

    a : Real number, `a > 0` a shape
    b : Real number, `b > 0` a shape

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Kumaraswamy, density, E, variance, cdf
    >>> from sympy import Symbol, simplify, pprint

    >>> a = Symbol("a", positive=True)
    >>> b = Symbol("b", positive=True)
    >>> z = Symbol("z")

    >>> X = Kumaraswamy("x", a, b)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
                       b - 1
         a - 1 /     a\
    a*b*z     *\1 - z /

    >>> cdf(X)(z)
    Piecewise((0, z < 0), (1 - (1 - z**a)**b, z <= 1), (1, True))

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Kumaraswamy_distribution

    """

    return rv(name, KumaraswamyDistribution, (a, b))

#-------------------------------------------------------------------------------
# Laplace distribution ---------------------------------------------------------


class LaplaceDistribution(SingleContinuousDistribution):
    _argnames = ('mu', 'b')

    def pdf(self, x):
        mu, b = self.mu, self.b
        return 1/(2*b)*exp(-Abs(x - mu)/b)

    def _cdf(self, x):
        mu, b = self.mu, self.b
        return Piecewise(
                    (S.Half*exp((x - mu)/b), x < mu),
                    (S.One - S.Half*exp(-(x - mu)/b), x >= mu)
                        )

    def _characteristic_function(self, t):
        return exp(self.mu*I*t) / (1 + self.b**2*t**2)

    def _moment_generating_function(self, t):
        return exp(self.mu*t) / (1 - self.b**2*t**2)

def Laplace(name, mu, b):
    r"""
    Create a continuous random variable with a Laplace distribution.

    The density of the Laplace distribution is given by

    .. math::
        f(x) := \frac{1}{2 b} \exp \left(-\frac{|x-\mu|}b \right)

    Parameters
    ==========

    mu : Real number or a list/matrix, the location (mean) or the
        location vector
    b : Real number or a positive definite matrix, representing a scale
        or the covariance matrix.

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Laplace, density, cdf
    >>> from sympy import Symbol, pprint

    >>> mu = Symbol("mu")
    >>> b = Symbol("b", positive=True)
    >>> z = Symbol("z")

    >>> X = Laplace("x", mu, b)

    >>> density(X)(z)
    exp(-Abs(mu - z)/b)/(2*b)

    >>> cdf(X)(z)
    Piecewise((exp((-mu + z)/b)/2, mu > z), (1 - exp((mu - z)/b)/2, True))

    >>> L = Laplace('L', [1, 2], [[1, 0], [0, 1]])
    >>> pprint(density(L)(1, 2), use_unicode=False)
     5        /     ____\
    e *besselk\0, \/ 35 /
    ---------------------
              pi

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Laplace_distribution
    .. [2] http://mathworld.wolfram.com/LaplaceDistribution.html

    """

    if isinstance(mu, (list, MatrixBase)) and\
        isinstance(b, (list, MatrixBase)):
        from sympy.stats.joint_rv_types import MultivariateLaplaceDistribution
        return multivariate_rv(
            MultivariateLaplaceDistribution, name, mu, b)

    return rv(name, LaplaceDistribution, (mu, b))

#-------------------------------------------------------------------------------
# Logistic distribution --------------------------------------------------------


class LogisticDistribution(SingleContinuousDistribution):
    _argnames = ('mu', 's')

    def pdf(self, x):
        mu, s = self.mu, self.s
        return exp(-(x - mu)/s)/(s*(1 + exp(-(x - mu)/s))**2)

    def _cdf(self, x):
        mu, s = self.mu, self.s
        return S.One/(1 + exp(-(x - mu)/s))

    def _characteristic_function(self, t):
        return Piecewise((exp(I*t*self.mu) * pi*self.s*t / sinh(pi*self.s*t), Ne(t, 0)), (S.One, True))

    def _moment_generating_function(self, t):
        return exp(self.mu*t) * Beta(1 - self.s*t, 1 + self.s*t)

def Logistic(name, mu, s):
    r"""
    Create a continuous random variable with a logistic distribution.

    The density of the logistic distribution is given by

    .. math::
        f(x) := \frac{e^{-(x-\mu)/s}} {s\left(1+e^{-(x-\mu)/s}\right)^2}

    Parameters
    ==========

    mu : Real number, the location (mean)
    s : Real number, `s > 0` a scale

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Logistic, density, cdf
    >>> from sympy import Symbol

    >>> mu = Symbol("mu", real=True)
    >>> s = Symbol("s", positive=True)
    >>> z = Symbol("z")

    >>> X = Logistic("x", mu, s)

    >>> density(X)(z)
    exp((mu - z)/s)/(s*(exp((mu - z)/s) + 1)**2)

    >>> cdf(X)(z)
    1/(exp((mu - z)/s) + 1)

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Logistic_distribution
    .. [2] http://mathworld.wolfram.com/LogisticDistribution.html

    """

    return rv(name, LogisticDistribution, (mu, s))

#-------------------------------------------------------------------------------
# Log Normal distribution ------------------------------------------------------


class LogNormalDistribution(SingleContinuousDistribution):
    _argnames = ('mean', 'std')

    set = Interval(0, oo)

    def pdf(self, x):
        mean, std = self.mean, self.std
        return exp(-(log(x) - mean)**2 / (2*std**2)) / (x*sqrt(2*pi)*std)

    def sample(self):
        return random.lognormvariate(self.mean, self.std)

    def _cdf(self, x):
        mean, std = self.mean, self.std
        return Piecewise(
                (S.Half + S.Half*erf((log(x) - mean)/sqrt(2)/std), x > 0),
                (S.Zero, True)
        )

    def _moment_generating_function(self, t):
        raise NotImplementedError('Moment generating function of the log-normal distribution is not defined.')

def LogNormal(name, mean, std):
    r"""
    Create a continuous random variable with a log-normal distribution.

    The density of the log-normal distribution is given by

    .. math::
        f(x) := \frac{1}{x\sqrt{2\pi\sigma^2}}
                e^{-\frac{\left(\ln x-\mu\right)^2}{2\sigma^2}}

    with :math:`x \geq 0`.

    Parameters
    ==========

    mu : Real number, the log-scale
    sigma : Real number, :math:`\sigma^2 > 0` a shape

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import LogNormal, density
    >>> from sympy import Symbol, simplify, pprint

    >>> mu = Symbol("mu", real=True)
    >>> sigma = Symbol("sigma", positive=True)
    >>> z = Symbol("z")

    >>> X = LogNormal("x", mu, sigma)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
                          2
           -(-mu + log(z))
           -----------------
                      2
      ___      2*sigma
    \/ 2 *e
    ------------------------
            ____
        2*\/ pi *sigma*z


    >>> X = LogNormal('x', 0, 1) # Mean 0, standard deviation 1

    >>> density(X)(z)
    sqrt(2)*exp(-log(z)**2/2)/(2*sqrt(pi)*z)

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Lognormal
    .. [2] http://mathworld.wolfram.com/LogNormalDistribution.html

    """

    return rv(name, LogNormalDistribution, (mean, std))

#-------------------------------------------------------------------------------
# Maxwell distribution ---------------------------------------------------------


class MaxwellDistribution(SingleContinuousDistribution):
    _argnames = ('a',)

    set = Interval(0, oo)

    def pdf(self, x):
        a = self.a
        return sqrt(2/pi)*x**2*exp(-x**2/(2*a**2))/a**3

def Maxwell(name, a):
    r"""
    Create a continuous random variable with a Maxwell distribution.

    The density of the Maxwell distribution is given by

    .. math::
        f(x) := \sqrt{\frac{2}{\pi}} \frac{x^2 e^{-x^2/(2a^2)}}{a^3}

    with :math:`x \geq 0`.

    .. TODO - what does the parameter mean?

    Parameters
    ==========

    a : Real number, `a > 0`

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Maxwell, density, E, variance
    >>> from sympy import Symbol, simplify

    >>> a = Symbol("a", positive=True)
    >>> z = Symbol("z")

    >>> X = Maxwell("x", a)

    >>> density(X)(z)
    sqrt(2)*z**2*exp(-z**2/(2*a**2))/(sqrt(pi)*a**3)

    >>> E(X)
    2*sqrt(2)*a/sqrt(pi)

    >>> simplify(variance(X))
    a**2*(-8 + 3*pi)/pi

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Maxwell_distribution
    .. [2] http://mathworld.wolfram.com/MaxwellDistribution.html

    """

    return rv(name, MaxwellDistribution, (a, ))

#-------------------------------------------------------------------------------
# Nakagami distribution --------------------------------------------------------


class NakagamiDistribution(SingleContinuousDistribution):
    _argnames = ('mu', 'omega')

    set = Interval(0, oo)

    def pdf(self, x):
        mu, omega = self.mu, self.omega
        return 2*mu**mu/(gamma(mu)*omega**mu)*x**(2*mu - 1)*exp(-mu/omega*x**2)

    def _cdf(self, x):
        mu, omega = self.mu, self.omega
        return Piecewise(
                    (lowergamma(mu, (mu/omega)*x**2)/gamma(mu), x > 0),
                    (S.Zero, True))

def Nakagami(name, mu, omega):
    r"""
    Create a continuous random variable with a Nakagami distribution.

    The density of the Nakagami distribution is given by

    .. math::
        f(x) := \frac{2\mu^\mu}{\Gamma(\mu)\omega^\mu} x^{2\mu-1}
                \exp\left(-\frac{\mu}{\omega}x^2 \right)

    with :math:`x > 0`.

    Parameters
    ==========

    mu : Real number, `\mu \geq \frac{1}{2}` a shape
    omega : Real number, `\omega > 0`, the spread

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Nakagami, density, E, variance, cdf
    >>> from sympy import Symbol, simplify, pprint

    >>> mu = Symbol("mu", positive=True)
    >>> omega = Symbol("omega", positive=True)
    >>> z = Symbol("z")

    >>> X = Nakagami("x", mu, omega)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
                                    2
                               -mu*z
                               -------
        mu      -mu  2*mu - 1  omega
    2*mu  *omega   *z        *e
    ----------------------------------
                Gamma(mu)

    >>> simplify(E(X))
    sqrt(mu)*sqrt(omega)*gamma(mu + 1/2)/gamma(mu + 1)

    >>> V = simplify(variance(X))
    >>> pprint(V, use_unicode=False)
                        2
             omega*Gamma (mu + 1/2)
    omega - -----------------------
            Gamma(mu)*Gamma(mu + 1)

    >>> cdf(X)(z)
    Piecewise((lowergamma(mu, mu*z**2/omega)/gamma(mu), z > 0),
            (0, True))


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Nakagami_distribution

    """

    return rv(name, NakagamiDistribution, (mu, omega))

#-------------------------------------------------------------------------------
# Normal distribution ----------------------------------------------------------


class NormalDistribution(SingleContinuousDistribution):
    _argnames = ('mean', 'std')

    @staticmethod
    def check(mean, std):
        _value_check(std > 0, "Standard deviation must be positive")

    def pdf(self, x):
        return exp(-(x - self.mean)**2 / (2*self.std**2)) / (sqrt(2*pi)*self.std)

    def sample(self):
        return random.normalvariate(self.mean, self.std)

    def _cdf(self, x):
        mean, std = self.mean, self.std
        return erf(sqrt(2)*(-mean + x)/(2*std))/2 + S.Half

    def _characteristic_function(self, t):
        mean, std = self.mean, self.std
        return exp(I*mean*t - std**2*t**2/2)

    def _moment_generating_function(self, t):
        mean, std = self.mean, self.std
        return exp(mean*t + std**2*t**2/2)

def Normal(name, mean, std):
    r"""
    Create a continuous random variable with a Normal distribution.

    The density of the Normal distribution is given by

    .. math::
        f(x) := \frac{1}{\sigma\sqrt{2\pi}} e^{ -\frac{(x-\mu)^2}{2\sigma^2} }

    Parameters
    ==========

    mu : Real number or a list representing the mean or the mean vector
    sigma : Real number or a positive definite sqaure matrix,
         :math:`\sigma^2 > 0` the variance

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Normal, density, E, std, cdf, skewness
    >>> from sympy import Symbol, simplify, pprint, factor, together, factor_terms

    >>> mu = Symbol("mu")
    >>> sigma = Symbol("sigma", positive=True)
    >>> z = Symbol("z")
    >>> y = Symbol("y")
    >>> X = Normal("x", mu, sigma)

    >>> density(X)(z)
    sqrt(2)*exp(-(-mu + z)**2/(2*sigma**2))/(2*sqrt(pi)*sigma)

    >>> C = simplify(cdf(X))(z) # it needs a little more help...
    >>> pprint(C, use_unicode=False)
       /  ___          \
       |\/ 2 *(-mu + z)|
    erf|---------------|
       \    2*sigma    /   1
    -------------------- + -
             2             2

    >>> simplify(skewness(X))
    0

    >>> X = Normal("x", 0, 1) # Mean 0, standard deviation 1
    >>> density(X)(z)
    sqrt(2)*exp(-z**2/2)/(2*sqrt(pi))

    >>> E(2*X + 1)
    1

    >>> simplify(std(2*X + 1))
    2

    >>> m = Normal('X', [1, 2], [[2, 1], [1, 2]])
    >>> from sympy.stats.joint_rv import marginal_distribution
    >>> pprint(density(m)(y, z))
           /1   y\ /2*y   z\   /    z\ /  y   2*z    \
           |- - -|*|--- - -| + |1 - -|*|- - + --- - 1|
      ___  \2   2/ \ 3    3/   \    2/ \  3    3     /
    \/ 3 *e
    --------------------------------------------------
                           6*pi

    >>> marginal_distribution(m, m[0])(1)
     1/(2*sqrt(pi))


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Normal_distribution
    .. [2] http://mathworld.wolfram.com/NormalDistributionFunction.html

    """

    if isinstance(mean, (list, MatrixBase)) and\
        isinstance(std, (list, MatrixBase)):
        from sympy.stats.joint_rv_types import MultivariateNormalDistribution
        return multivariate_rv(
            MultivariateNormalDistribution, name, mean, std)
    return rv(name, NormalDistribution, (mean, std))

#-------------------------------------------------------------------------------
# Pareto distribution ----------------------------------------------------------


class ParetoDistribution(SingleContinuousDistribution):
    _argnames = ('xm', 'alpha')

    @property
    def set(self):
        return Interval(self.xm, oo)

    @staticmethod
    def check(xm, alpha):
        _value_check(xm > 0, "Xm must be positive")
        _value_check(alpha > 0, "Alpha must be positive")

    def pdf(self, x):
        xm, alpha = self.xm, self.alpha
        return alpha * xm**alpha / x**(alpha + 1)

    def sample(self):
        return random.paretovariate(self.alpha)

    def _cdf(self, x):
        xm, alpha = self.xm, self.alpha
        return Piecewise(
                (S.One - xm**alpha/x**alpha, x>=xm),
                (0, True),
        )

    def _moment_generating_function(self, t):
        xm, alpha = self.xm, self.alpha
        return alpha * (-xm*t)**alpha * uppergamma(-alpha, -xm*t)

    def _characteristic_function(self, t):
        xm, alpha = self.xm, self.alpha
        return alpha * (-I * xm * t) ** alpha * uppergamma(-alpha, -I * xm * t)


def Pareto(name, xm, alpha):
    r"""
    Create a continuous random variable with the Pareto distribution.

    The density of the Pareto distribution is given by

    .. math::
        f(x) := \frac{\alpha\,x_m^\alpha}{x^{\alpha+1}}

    with :math:`x \in [x_m,\infty]`.

    Parameters
    ==========

    xm : Real number, `x_m > 0`, a scale
    alpha : Real number, `\alpha > 0`, a shape

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Pareto, density
    >>> from sympy import Symbol

    >>> xm = Symbol("xm", positive=True)
    >>> beta = Symbol("beta", positive=True)
    >>> z = Symbol("z")

    >>> X = Pareto("x", xm, beta)

    >>> density(X)(z)
    beta*xm**beta*z**(-beta - 1)

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Pareto_distribution
    .. [2] http://mathworld.wolfram.com/ParetoDistribution.html

    """

    return rv(name, ParetoDistribution, (xm, alpha))

#-------------------------------------------------------------------------------
# QuadraticU distribution ------------------------------------------------------


class QuadraticUDistribution(SingleContinuousDistribution):
    _argnames = ('a', 'b')

    @property
    def set(self):
        return Interval(self.a, self.b)

    def pdf(self, x):
        a, b = self.a, self.b
        alpha = 12 / (b-a)**3
        beta = (a+b) / 2
        return Piecewise(
                  (alpha * (x-beta)**2, And(a<=x, x<=b)),
                  (S.Zero, True))

    def _moment_generating_function(self, t):
        a, b = self.a, self.b

        return -3 * (exp(a*t) * (4  + (a**2 + 2*a*(-2 + b) + b**2) * t) - exp(b*t) * (4 + (-4*b + (a + b)**2) * t)) / ((a-b)**3 * t**2)

    def _characteristic_function(self, t):
        def _moment_generating_function(self, t):
            a, b = self.a, self.b

            return -3*I*(exp(I*a*t*exp(I*b*t)) * (4*I - (-4*b + (a+b)**2)*t)) / ((a-b)**3 * t**2)


def QuadraticU(name, a, b):
    r"""
    Create a Continuous Random Variable with a U-quadratic distribution.

    The density of the U-quadratic distribution is given by

    .. math::
        f(x) := \alpha (x-\beta)^2

    with :math:`x \in [a,b]`.

    Parameters
    ==========

    a : Real number
    b : Real number, :math:`a < b`

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import QuadraticU, density, E, variance
    >>> from sympy import Symbol, simplify, factor, pprint

    >>> a = Symbol("a", real=True)
    >>> b = Symbol("b", real=True)
    >>> z = Symbol("z")

    >>> X = QuadraticU("x", a, b)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
    /                2
    |   /  a   b    \
    |12*|- - - - + z|
    |   \  2   2    /
    <-----------------  for And(b >= z, a <= z)
    |            3
    |    (-a + b)
    |
    \        0                 otherwise

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/U-quadratic_distribution

    """

    return rv(name, QuadraticUDistribution, (a, b))

#-------------------------------------------------------------------------------
# RaisedCosine distribution ----------------------------------------------------


class RaisedCosineDistribution(SingleContinuousDistribution):
    _argnames = ('mu', 's')

    @property
    def set(self):
        return Interval(self.mu - self.s, self.mu + self.s)

    @staticmethod
    def check(mu, s):
        _value_check(s > 0, "s must be positive")

    def pdf(self, x):
        mu, s = self.mu, self.s
        return Piecewise(
                ((1+cos(pi*(x-mu)/s)) / (2*s), And(mu-s<=x, x<=mu+s)),
                (S.Zero, True))

    def _characteristic_function(self, t):
        mu, s = self.mu, self.s
        return Piecewise((exp(-I*pi*mu/s)/2, Eq(t, -pi/s)),
                         (exp(I*pi*mu/s)/2, Eq(t, pi/s)),
                         (pi**2*sin(s*t)*exp(I*mu*t) / (s*t*(pi**2 - s**2*t**2)), True))

    def _moment_generating_function(self, t):
        mu, s = self.mu, self.s
        return pi**2 * sinh(s*t) * exp(mu*t) /  (s*t*(pi**2 + s**2*t**2))

def RaisedCosine(name, mu, s):
    r"""
    Create a Continuous Random Variable with a raised cosine distribution.

    The density of the raised cosine distribution is given by

    .. math::
        f(x) := \frac{1}{2s}\left(1+\cos\left(\frac{x-\mu}{s}\pi\right)\right)

    with :math:`x \in [\mu-s,\mu+s]`.

    Parameters
    ==========

    mu : Real number
    s : Real number, `s > 0`

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import RaisedCosine, density, E, variance
    >>> from sympy import Symbol, simplify, pprint

    >>> mu = Symbol("mu", real=True)
    >>> s = Symbol("s", positive=True)
    >>> z = Symbol("z")

    >>> X = RaisedCosine("x", mu, s)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
    /   /pi*(-mu + z)\
    |cos|------------| + 1
    |   \     s      /
    <---------------------  for And(z >= mu - s, z <= mu + s)
    |         2*s
    |
    \          0                        otherwise

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Raised_cosine_distribution

    """

    return rv(name, RaisedCosineDistribution, (mu, s))

#-------------------------------------------------------------------------------
# Rayleigh distribution --------------------------------------------------------


class RayleighDistribution(SingleContinuousDistribution):
    _argnames = ('sigma',)

    set = Interval(0, oo)

    def pdf(self, x):
        sigma = self.sigma
        return x/sigma**2*exp(-x**2/(2*sigma**2))

    def _characteristic_function(self, t):
        sigma = self.sigma
        return 1 - sigma*t*exp(-sigma**2*t**2/2) * sqrt(pi/2) * (erfi(sigma*t/sqrt(2)) - I)

    def _moment_generating_function(self, t):
        sigma = self.sigma
        return 1 + sigma*t*exp(sigma**2*t**2/2) * sqrt(pi/2) * (erf(sigma*t/sqrt(2)) + 1)


def Rayleigh(name, sigma):
    r"""
    Create a continuous random variable with a Rayleigh distribution.

    The density of the Rayleigh distribution is given by

    .. math ::
        f(x) := \frac{x}{\sigma^2} e^{-x^2/2\sigma^2}

    with :math:`x > 0`.

    Parameters
    ==========

    sigma : Real number, `\sigma > 0`

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Rayleigh, density, E, variance
    >>> from sympy import Symbol, simplify

    >>> sigma = Symbol("sigma", positive=True)
    >>> z = Symbol("z")

    >>> X = Rayleigh("x", sigma)

    >>> density(X)(z)
    z*exp(-z**2/(2*sigma**2))/sigma**2

    >>> E(X)
    sqrt(2)*sqrt(pi)*sigma/2

    >>> variance(X)
    -pi*sigma**2/2 + 2*sigma**2

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Rayleigh_distribution
    .. [2] http://mathworld.wolfram.com/RayleighDistribution.html

    """

    return rv(name, RayleighDistribution, (sigma, ))

#-------------------------------------------------------------------------------
# Shifted Gompertz distribution ------------------------------------------------


class ShiftedGompertzDistribution(SingleContinuousDistribution):
    _argnames = ('b', 'eta')

    set = Interval(0, oo)

    @staticmethod
    def check(b, eta):
        _value_check(b > 0, "b must be positive")
        _value_check(eta > 0, "eta must be positive")

    def pdf(self, x):
        b, eta = self.b, self.eta
        return b*exp(-b*x)*exp(-eta*exp(-b*x))*(1+eta*(1-exp(-b*x)))

def ShiftedGompertz(name, b, eta):
    r"""
    Create a continuous random variable with a Shifted Gompertz distribution.

    The density of the Shifted Gompertz distribution is given by

    .. math::
        f(x) := b e^{-b x} e^{-\eta \exp(-b x)} \left[1 + \eta(1 - e^(-bx)) \right]

    with :math: 'x \in [0, \inf)'.

    Parameters
    ==========

    b: Real number, 'b > 0' a scale
    eta: Real number, 'eta > 0' a shape

    Returns
    =======

    A RandomSymbol.

    Examples
    ========
    >>> from sympy.stats import ShiftedGompertz, density, E, variance
    >>> from sympy import Symbol

    >>> b = Symbol("b", positive=True)
    >>> eta = Symbol("eta", positive=True)
    >>> x = Symbol("x")

    >>> X = ShiftedGompertz("x", b, eta)

    >>> density(X)(x)
    b*(eta*(1 - exp(-b*x)) + 1)*exp(-b*x)*exp(-eta*exp(-b*x))

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Shifted_Gompertz_distribution

    """
    return rv(name, ShiftedGompertzDistribution, (b, eta))

#-------------------------------------------------------------------------------
# StudentT distribution --------------------------------------------------------


class StudentTDistribution(SingleContinuousDistribution):
    _argnames = ('nu',)

    def pdf(self, x):
        nu = self.nu
        return 1/(sqrt(nu)*beta_fn(S(1)/2, nu/2))*(1 + x**2/nu)**(-(nu + 1)/2)

    def _cdf(self, x):
        nu = self.nu
        return S.Half + x*gamma((nu+1)/2)*hyper((S.Half, (nu+1)/2),
                                (S(3)/2,), -x**2/nu)/(sqrt(pi*nu)*gamma(nu/2))

    def _moment_generating_function(self, t):
        raise NotImplementedError('The moment generating function for the Student-T distribution is undefined.')

def StudentT(name, nu):
    r"""
    Create a continuous random variable with a student's t distribution.

    The density of the student's t distribution is given by

    .. math::
        f(x) := \frac{\Gamma \left(\frac{\nu+1}{2} \right)}
                {\sqrt{\nu\pi}\Gamma \left(\frac{\nu}{2} \right)}
                \left(1+\frac{x^2}{\nu} \right)^{-\frac{\nu+1}{2}}

    Parameters
    ==========

    nu : Real number, `\nu > 0`, the degrees of freedom

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import StudentT, density, E, variance, cdf
    >>> from sympy import Symbol, simplify, pprint

    >>> nu = Symbol("nu", positive=True)
    >>> z = Symbol("z")

    >>> X = StudentT("x", nu)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
               nu   1
             - -- - -
               2    2
     /     2\
     |    z |
     |1 + --|
     \    nu/
    -----------------
      ____  /     nu\
    \/ nu *B|1/2, --|
            \     2 /

    >>> cdf(X)(z)
    1/2 + z*gamma(nu/2 + 1/2)*hyper((1/2, nu/2 + 1/2), (3/2,),
                                -z**2/nu)/(sqrt(pi)*sqrt(nu)*gamma(nu/2))


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Student_t-distribution
    .. [2] http://mathworld.wolfram.com/Studentst-Distribution.html

    """

    return rv(name, StudentTDistribution, (nu, ))

#-------------------------------------------------------------------------------
# Trapezoidal distribution ------------------------------------------------------


class TrapezoidalDistribution(SingleContinuousDistribution):
    _argnames = ('a', 'b', 'c', 'd')

    def pdf(self, x):
        a, b, c, d = self.a, self.b, self.c, self.d
        return Piecewise(
            (2*(x-a) / ((b-a)*(d+c-a-b)), And(a <= x, x < b)),
            (2 / (d+c-a-b), And(b <= x, x < c)),
            (2*(d-x) / ((d-c)*(d+c-a-b)), And(c <= x, x <= d)),
            (S.Zero, True))

def Trapezoidal(name, a, b, c, d):
    r"""
    Create a continuous random variable with a trapezoidal distribution.

    The density of the trapezoidal distribution is given by

    .. math::
        f(x) := \begin{cases}
                  0 & \mathrm{for\ } x < a, \\
                  \frac{2(x-a)}{(b-a)(d+c-a-b)} & \mathrm{for\ } a \le x < b, \\
                  \frac{2}{d+c-a-b} & \mathrm{for\ } b \le x < c, \\
                  \frac{2(d-x)}{(d-c)(d+c-a-b)} & \mathrm{for\ } c \le x < d, \\
                  0 & \mathrm{for\ } d < x.
                \end{cases}

    Parameters
    ==========

    a : Real number, :math:`a < d`
    b : Real number, :math:`a <= b < c`
    c : Real number, :math:`b < c <= d`
    d : Real number

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Trapezoidal, density, E
    >>> from sympy import Symbol, pprint

    >>> a = Symbol("a")
    >>> b = Symbol("b")
    >>> c = Symbol("c")
    >>> d = Symbol("d")
    >>> z = Symbol("z")

    >>> X = Trapezoidal("x", a,b,c,d)

    >>> pprint(density(X)(z), use_unicode=False)
    /        -2*a + 2*z
    |-------------------------  for And(a <= z, b > z)
    |(-a + b)*(-a - b + c + d)
    |
    |           2
    |     --------------        for And(b <= z, c > z)
    <     -a - b + c + d
    |
    |        2*d - 2*z
    |-------------------------  for And(d >= z, c <= z)
    |(-c + d)*(-a - b + c + d)
    |
    \            0                     otherwise

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Trapezoidal_distribution

    """
    return rv(name, TrapezoidalDistribution, (a, b, c, d))

#-------------------------------------------------------------------------------
# Triangular distribution ------------------------------------------------------


class TriangularDistribution(SingleContinuousDistribution):
    _argnames = ('a', 'b', 'c')

    def pdf(self, x):
        a, b, c = self.a, self.b, self.c
        return Piecewise(
            (2*(x - a)/((b - a)*(c - a)), And(a <= x, x < c)),
            (2/(b - a), Eq(x, c)),
            (2*(b - x)/((b - a)*(b - c)), And(c < x, x <= b)),
            (S.Zero, True))

    def _characteristic_function(self, t):
        a, b, c = self.a, self.b, self.c
        return -2 *((b-c) * exp(I*a*t) - (b-a) * exp(I*c*t) + (c-a) * exp(I*b*t)) / ((b-a)*(c-a)*(b-c)*t**2)

    def _moment_generating_function(self, t):
        a, b, c = self.a, self.b, self.c
        return 2 * ((b - c) * exp(a * t) - (b - a) * exp(c * t) + (c + a) * exp(b * t)) / (
        (b - a) * (c - a) * (b - c) * t ** 2)


def Triangular(name, a, b, c):
    r"""
    Create a continuous random variable with a triangular distribution.

    The density of the triangular distribution is given by

    .. math::
        f(x) := \begin{cases}
                  0 & \mathrm{for\ } x < a, \\
                  \frac{2(x-a)}{(b-a)(c-a)} & \mathrm{for\ } a \le x < c, \\
                  \frac{2}{b-a} & \mathrm{for\ } x = c, \\
                  \frac{2(b-x)}{(b-a)(b-c)} & \mathrm{for\ } c < x \le b, \\
                  0 & \mathrm{for\ } b < x.
                \end{cases}

    Parameters
    ==========

    a : Real number, :math:`a \in \left(-\infty, \infty\right)`
    b : Real number, :math:`a < b`
    c : Real number, :math:`a \leq c \leq b`

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Triangular, density, E
    >>> from sympy import Symbol, pprint

    >>> a = Symbol("a")
    >>> b = Symbol("b")
    >>> c = Symbol("c")
    >>> z = Symbol("z")

    >>> X = Triangular("x", a,b,c)

    >>> pprint(density(X)(z), use_unicode=False)
    /    -2*a + 2*z
    |-----------------  for And(a <= z, c > z)
    |(-a + b)*(-a + c)
    |
    |       2
    |     ------              for c = z
    <     -a + b
    |
    |   2*b - 2*z
    |----------------   for And(b >= z, c < z)
    |(-a + b)*(b - c)
    |
    \        0                otherwise

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Triangular_distribution
    .. [2] http://mathworld.wolfram.com/TriangularDistribution.html

    """

    return rv(name, TriangularDistribution, (a, b, c))

#-------------------------------------------------------------------------------
# Uniform distribution ---------------------------------------------------------


class UniformDistribution(SingleContinuousDistribution):
    _argnames = ('left', 'right')

    def pdf(self, x):
        left, right = self.left, self.right
        return Piecewise(
            (S.One/(right - left), And(left <= x, x <= right)),
            (S.Zero, True)
        )

    def _cdf(self, x):
        left, right = self.left, self.right
        return Piecewise(
            (S.Zero, x < left),
            ((x - left)/(right - left), x <= right),
            (S.One, True)
        )

    def _characteristic_function(self, t):
        left, right = self.left, self.right
        return Piecewise(((exp(I*t*right) - exp(I*t*left)) / (I*t*(right - left)), Ne(t, 0)),
                         (S.One, True))

    def _moment_generating_function(self, t):
        left, right = self.left, self.right
        return Piecewise(((exp(t*right) - exp(t*left)) / (t * (right - left)), Ne(t, 0)),
                         (S.One, True))

    def expectation(self, expr, var, **kwargs):
        from sympy import Max, Min
        kwargs['evaluate'] = True
        result = SingleContinuousDistribution.expectation(self, expr, var, **kwargs)
        result = result.subs({Max(self.left, self.right): self.right,
                              Min(self.left, self.right): self.left})
        return result

    def sample(self):
        return random.uniform(self.left, self.right)


def Uniform(name, left, right):
    r"""
    Create a continuous random variable with a uniform distribution.

    The density of the uniform distribution is given by

    .. math::
        f(x) := \begin{cases}
                  \frac{1}{b - a} & \text{for } x \in [a,b]  \\
                  0               & \text{otherwise}
                \end{cases}

    with :math:`x \in [a,b]`.

    Parameters
    ==========

    a : Real number, :math:`-\infty < a` the left boundary
    b : Real number, :math:`a < b < \infty` the right boundary

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Uniform, density, cdf, E, variance, skewness
    >>> from sympy import Symbol, simplify

    >>> a = Symbol("a", negative=True)
    >>> b = Symbol("b", positive=True)
    >>> z = Symbol("z")

    >>> X = Uniform("x", a, b)

    >>> density(X)(z)
    Piecewise((1/(-a + b), (b >= z) & (a <= z)), (0, True))

    >>> cdf(X)(z)  # doctest: +SKIP
    -a/(-a + b) + z/(-a + b)

    >>> simplify(E(X))
    a/2 + b/2

    >>> simplify(variance(X))
    a**2/12 - a*b/6 + b**2/12

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Uniform_distribution_%28continuous%29
    .. [2] http://mathworld.wolfram.com/UniformDistribution.html

    """

    return rv(name, UniformDistribution, (left, right))

#-------------------------------------------------------------------------------
# UniformSum distribution ------------------------------------------------------


class UniformSumDistribution(SingleContinuousDistribution):
    _argnames = ('n',)

    @property
    def set(self):
        return Interval(0, self.n)

    def pdf(self, x):
        n = self.n
        k = Dummy("k")
        return 1/factorial(
            n - 1)*Sum((-1)**k*binomial(n, k)*(x - k)**(n - 1), (k, 0, floor(x)))

    def _cdf(self, x):
        n = self.n
        k = Dummy("k")
        return Piecewise((S.Zero, x < 0),
                        (1/factorial(n)*Sum((-1)**k*binomial(n, k)*(x - k)**(n),
                        (k, 0, floor(x))), x <= n),
                        (S.One, True))

    def _characteristic_function(self, t):
        return ((exp(I*t) - 1) / (I*t))**self.n

    def _moment_generating_function(self, t):
        return ((exp(t) - 1) / t)**self.n

def UniformSum(name, n):
    r"""
    Create a continuous random variable with an Irwin-Hall distribution.

    The probability distribution function depends on a single parameter
    `n` which is an integer.

    The density of the Irwin-Hall distribution is given by

    .. math ::
        f(x) := \frac{1}{(n-1)!}\sum_{k=0}^{\left\lfloor x\right\rfloor}(-1)^k
                \binom{n}{k}(x-k)^{n-1}

    Parameters
    ==========

    n : A positive Integer, `n > 0`

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import UniformSum, density, cdf
    >>> from sympy import Symbol, pprint

    >>> n = Symbol("n", integer=True)
    >>> z = Symbol("z")

    >>> X = UniformSum("x", n)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
    floor(z)
      ___
      \  `
       \         k         n - 1 /n\
        )    (-1) *(-k + z)     *| |
       /                         \k/
      /__,
     k = 0
    --------------------------------
                (n - 1)!

    >>> cdf(X)(z)
    Piecewise((0, z < 0), (Sum((-1)**_k*(-_k + z)**n*binomial(n, _k),
                    (_k, 0, floor(z)))/factorial(n), n >= z), (1, True))


    Compute cdf with specific 'x' and 'n' values as follows :
    >>> cdf(UniformSum("x", 5), evaluate=False)(2).doit()
    9/40

    The argument evaluate=False prevents an attempt at evaluation
    of the sum for general n, before the argument 2 is passed.

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Uniform_sum_distribution
    .. [2] http://mathworld.wolfram.com/UniformSumDistribution.html

    """

    return rv(name, UniformSumDistribution, (n, ))

#-------------------------------------------------------------------------------
# VonMises distribution --------------------------------------------------------


class VonMisesDistribution(SingleContinuousDistribution):
    _argnames = ('mu', 'k')

    set = Interval(0, 2*pi)

    @staticmethod
    def check(mu, k):
        _value_check(k > 0, "k must be positive")

    def pdf(self, x):
        mu, k = self.mu, self.k
        return exp(k*cos(x-mu)) / (2*pi*besseli(0, k))

def VonMises(name, mu, k):
    r"""
    Create a Continuous Random Variable with a von Mises distribution.

    The density of the von Mises distribution is given by

    .. math::
        f(x) := \frac{e^{\kappa\cos(x-\mu)}}{2\pi I_0(\kappa)}

    with :math:`x \in [0,2\pi]`.

    Parameters
    ==========

    mu : Real number, measure of location
    k : Real number, measure of concentration

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import VonMises, density, E, variance
    >>> from sympy import Symbol, simplify, pprint

    >>> mu = Symbol("mu")
    >>> k = Symbol("k", positive=True)
    >>> z = Symbol("z")

    >>> X = VonMises("x", mu, k)

    >>> D = density(X)(z)
    >>> pprint(D, use_unicode=False)
         k*cos(mu - z)
        e
    ------------------
    2*pi*besseli(0, k)


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Von_Mises_distribution
    .. [2] http://mathworld.wolfram.com/vonMisesDistribution.html

    """

    return rv(name, VonMisesDistribution, (mu, k))

#-------------------------------------------------------------------------------
# Weibull distribution ---------------------------------------------------------


class WeibullDistribution(SingleContinuousDistribution):
    _argnames = ('alpha', 'beta')

    set = Interval(0, oo)

    @staticmethod
    def check(alpha, beta):
        _value_check(alpha > 0, "Alpha must be positive")
        _value_check(beta > 0, "Beta must be positive")

    def pdf(self, x):
        alpha, beta = self.alpha, self.beta
        return beta * (x/alpha)**(beta - 1) * exp(-(x/alpha)**beta) / alpha

    def sample(self):
        return random.weibullvariate(self.alpha, self.beta)

def Weibull(name, alpha, beta):
    r"""
    Create a continuous random variable with a Weibull distribution.

    The density of the Weibull distribution is given by

    .. math::
        f(x) := \begin{cases}
                  \frac{k}{\lambda}\left(\frac{x}{\lambda}\right)^{k-1}
                  e^{-(x/\lambda)^{k}} & x\geq0\\
                  0 & x<0
                \end{cases}

    Parameters
    ==========

    lambda : Real number, :math:`\lambda > 0` a scale
    k : Real number, `k > 0` a shape

    Returns
    =======

    A RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Weibull, density, E, variance
    >>> from sympy import Symbol, simplify

    >>> l = Symbol("lambda", positive=True)
    >>> k = Symbol("k", positive=True)
    >>> z = Symbol("z")

    >>> X = Weibull("x", l, k)

    >>> density(X)(z)
    k*(z/lambda)**(k - 1)*exp(-(z/lambda)**k)/lambda

    >>> simplify(E(X))
    lambda*gamma(1 + 1/k)

    >>> simplify(variance(X))
    lambda**2*(-gamma(1 + 1/k)**2 + gamma(1 + 2/k))

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Weibull_distribution
    .. [2] http://mathworld.wolfram.com/WeibullDistribution.html

    """

    return rv(name, WeibullDistribution, (alpha, beta))

#-------------------------------------------------------------------------------
# Wigner semicircle distribution -----------------------------------------------


class WignerSemicircleDistribution(SingleContinuousDistribution):
    _argnames = ('R',)

    @property
    def set(self):
        return Interval(-self.R, self.R)

    def pdf(self, x):
        R = self.R
        return 2/(pi*R**2)*sqrt(R**2 - x**2)

    def _characteristic_function(self, t):
        return Piecewise((2 * besselj(1, self.R*t) / (self.R*t), Ne(t, 0)),
                         (S.One, True))

    def _moment_generating_function(self, t):
        return Piecewise((2 * besseli(1, self.R*t) / (self.R*t), Ne(t, 0)),
                         (S.One, True))

def WignerSemicircle(name, R):
    r"""
    Create a continuous random variable with a Wigner semicircle distribution.

    The density of the Wigner semicircle distribution is given by

    .. math::
        f(x) := \frac2{\pi R^2}\,\sqrt{R^2-x^2}

    with :math:`x \in [-R,R]`.

    Parameters
    ==========

    R : Real number, `R > 0`, the radius

    Returns
    =======

    A `RandomSymbol`.

    Examples
    ========

    >>> from sympy.stats import WignerSemicircle, density, E
    >>> from sympy import Symbol, simplify

    >>> R = Symbol("R", positive=True)
    >>> z = Symbol("z")

    >>> X = WignerSemicircle("x", R)

    >>> density(X)(z)
    2*sqrt(R**2 - z**2)/(pi*R**2)

    >>> E(X)
    0

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Wigner_semicircle_distribution
    .. [2] http://mathworld.wolfram.com/WignersSemicircleLaw.html

    """

    return rv(name, WignerSemicircleDistribution, (R,))
