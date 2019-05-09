from sympy import (sympify, S, pi, sqrt, exp, Lambda, Indexed, Gt,
    IndexedBase)
from sympy.matrices import ImmutableMatrix
from sympy.matrices.expressions.determinant import det
from sympy.stats.joint_rv import (JointDistribution, JointPSpace,
    JointDistributionHandmade, MarginalDistribution)
from sympy.stats.rv import _value_check, random_symbols

# __all__ = ['MultivariateNormal',
# 'MultivariateLaplace',
# 'MultivariateT',
# 'NormalGamma'
# ]

def multivariate_rv(cls, sym, *args):
    args = list(map(sympify, args))
    dist = cls(*args)
    args = dist.args
    dist.check(*args)
    return JointPSpace(sym, dist).value

def JointRV(symbol, pdf, _set=None):
    """
    Create a Joint Random Variable where each of its component is conitinuous,
    given the following:

    -- a symbol
    -- a PDF in terms of indexed symbols of the symbol given
     as the first argument

    NOTE: As of now, the set for each component for a `JointRV` is
    equal to the set of all integers, which can not be changed.

    Returns a RandomSymbol.

    Examples
    ========

    >>> from sympy import symbols, exp, pi, Indexed, S
    >>> from sympy.stats import density
    >>> from sympy.stats.joint_rv_types import JointRV

    >>> x1, x2 = (Indexed('x', i) for i in (1, 2))
    >>> pdf = exp(-x1**2/2 + x1 - x2**2/2 - S(1)/2)/(2*pi)

    >>> N1 = JointRV('x', pdf) #Multivariate Normal distribution
    >>> density(N1)(1, 2)
    exp(-2)/(2*pi)
    """
    #TODO: Add support for sets provided by the user
    symbol = sympify(symbol)
    syms = list(i for i in pdf.free_symbols if isinstance(i, Indexed)
        and i.base == IndexedBase(symbol))
    syms.sort(key = lambda index: index.args[1])
    _set = S.Reals**len(syms)
    pdf = Lambda(syms, pdf)
    dist = JointDistributionHandmade(pdf, _set)
    jrv = JointPSpace(symbol, dist).value
    rvs = random_symbols(pdf)
    if len(rvs) != 0:
        dist = MarginalDistribution(dist, (jrv,))
        return JointPSpace(symbol, dist).value
    return jrv

#-------------------------------------------------------------------------------
# Multivariate Normal distribution ---------------------------------------------------------

class MultivariateNormalDistribution(JointDistribution):
    _argnames = ['mu', 'sigma']

    is_Continuous=True

    @property
    def set(self):
        k = len(self.mu)
        return S.Reals**k

    def check(self, mu, sigma):
        _value_check(len(mu) == len(sigma.col(0)),
            "Size of the mean vector and covariance matrix are incorrect.")
        #check if covariance matrix is positive definite or not.
        _value_check(all([Gt(i, 0) != False for i in sigma.eigenvals().keys()]),
            "The covariance matrix must be positive definite. ")

    def pdf(self, *args):
        mu, sigma = self.mu, self.sigma
        k = len(mu)
        args = ImmutableMatrix(args)
        x = args - mu
        return  S(1)/sqrt((2*pi)**(k)*det(sigma))*exp(
            -S(1)/2*x.transpose()*(sigma.inv()*\
                x))[0]

    def marginal_distribution(self, indices, sym):
        sym = ImmutableMatrix([Indexed(sym, i) for i in indices])
        _mu, _sigma = self.mu, self.sigma
        k = len(self.mu)
        for i in range(k):
            if i not in indices:
                _mu = _mu.row_del(i)
                _sigma = _sigma.col_del(i)
                _sigma = _sigma.row_del(i)
        return Lambda(sym, S(1)/sqrt((2*pi)**(len(_mu))*det(_sigma))*exp(
            -S(1)/2*(_mu - sym).transpose()*(_sigma.inv()*\
                (_mu - sym)))[0])

#-------------------------------------------------------------------------------
# Multivariate Laplace distribution ---------------------------------------------------------

class MultivariateLaplaceDistribution(JointDistribution):
    _argnames = ['mu', 'sigma']
    is_Continuous=True

    @property
    def set(self):
        k = len(self.mu)
        return S.Reals**k

    def check(self, mu, sigma):
        _value_check(len(mu) == len(sigma.col(0)),
            "Size of the mean vector and covariance matrix are incorrect.")
        #check if covariance matrix is positive definite or not.
        _value_check(all([Gt(i, 0) != False for i in sigma.eigenvals().keys()]),
            "The covariance matrix must be positive definite. ")

    def pdf(self, *args):
        from sympy.functions.special.bessel import besselk
        mu, sigma = self.mu, self.sigma
        mu_T = mu.transpose()
        k = S(len(mu))
        sigma_inv = sigma.inv()
        args = ImmutableMatrix(args)
        args_T = args.transpose()
        x = (mu_T*sigma_inv*mu)[0]
        y = (args_T*sigma_inv*args)[0]
        v = 1 - k/2
        return S(2)/((2*pi)**(S(k)/2)*sqrt(det(sigma)))\
        *(y/(2 + x))**(S(v)/2)*besselk(v, sqrt((2 + x)*(y)))\
        *exp((args_T*sigma_inv*mu)[0])


#-------------------------------------------------------------------------------
# Multivariate StudentT distribution ---------------------------------------------------------

class MultivariateTDistribution(JointDistribution):
    _argnames = ['mu', 'shape_mat', 'dof']
    is_Continuous=True

    @property
    def set(self):
        k = len(self.mu)
        return S.Reals**k

    def check(self, mu, sigma, v):
        _value_check(len(mu) == len(sigma.col(0)),
            "Size of the location vector and shape matrix are incorrect.")
        #check if covariance matrix is positive definite or not.
        _value_check(all([Gt(i, 0) != False for i in sigma.eigenvals().keys()]),
            "The shape matrix must be positive definite. ")

    def pdf(self, *args):
        from sympy.functions.special.gamma_functions import gamma
        mu, sigma = self.mu, self.shape_mat
        v = S(self.dof)
        k = S(len(mu))
        sigma_inv = sigma.inv()
        args = ImmutableMatrix(args)
        x = args - mu
        return gamma((k + v)/2)/(gamma(v/2)*(v*pi)**(k/2)*sqrt(det(sigma)))\
        *(1 + 1/v*(x.transpose()*sigma_inv*x)[0])**((-v - k)/2)

def MultivariateT(syms, mu, sigma, v):
    """
    Creates a joint random variable with multivariate T-distribution.

    Parameters
    ==========

    syms: list/tuple/set of symbols for identifying each component
    mu: A list/tuple/set consisting of k means,represents a k
        dimensional location vector
    sigma: The shape matrix for the distribution

    Returns
    =======

    A random symbol
    """
    return multivariate_rv(MultivariateTDistribution, syms, mu, sigma, v)


#-------------------------------------------------------------------------------
# Multivariate Normal Gamma distribution ---------------------------------------------------------

class NormalGammaDistribution(JointDistribution):

    _argnames = ['mu', 'lamda', 'alpha', 'beta']
    is_Continuous=True

    def check(self, mu, lamda, alpha, beta):
        _value_check(mu.is_real, "Location must be real.")
        _value_check(lamda > 0, "Lambda must be positive")
        _value_check(alpha > 0, "alpha must be positive")
        _value_check(beta > 0, "beta must be positive")

    @property
    def set(self):
        from sympy.sets.sets import Interval
        return S.Reals*Interval(0, S.Infinity)

    def pdf(self, x, tau):
        from sympy.functions.special.gamma_functions import gamma
        beta, alpha, lamda = self.beta, self.alpha, self.lamda
        mu = self.mu

        return beta**alpha*sqrt(lamda)/(gamma(alpha)*sqrt(2*pi))*\
        tau**(alpha - S(1)/2)*exp(-1*beta*tau)*\
        exp(-1*(lamda*tau*(x - mu)**2)/S(2))

    def marginal_distribution(self, indices, *sym):
        from sympy.functions.special.gamma_functions import gamma
        if len(indices) == 2:
            return self.pdf(*sym)
        if indices[0] == 0:
            #For marginal over `x`, return non-standardized Student-T's
            #distribution
            x = sym[0]
            v, mu, sigma = self.alpha - S(1)/2, self.mu, \
                S(self.beta)/(self.lamda * self.alpha)
            return Lambda(sym, gamma((v + 1)/2)/(gamma(v/2)*sqrt(pi*v)*sigma)*\
                (1 + 1/v*((x - mu)/sigma)**2)**((-v -1)/2))
        #For marginal over `tau`, return Gamma distribution as per construction
        from sympy.stats.crv_types import GammaDistribution
        return Lambda(sym, GammaDistribution(self.alpha, self.beta)(sym[0]))

def NormalGamma(syms, mu, lamda, alpha, beta):
    """
    Creates a bivariate joint random variable with multivariate Normal gamma
    distribution.

    Parameters
    ==========

    syms: list/tuple/set of two symbols for identifying each component
    mu: A real number, as the mean of the normal distribution
    alpha: a positive integer
    beta: a positive integer
    lamda: a positive integer

    Returns
    =======

    A random symbol
    """
    return multivariate_rv(NormalGammaDistribution, syms, mu, lamda, alpha, beta)
