"""
Finite Discrete Random Variables - Prebuilt variable types

Contains
========
FiniteRV
DiscreteUniform
Die
Bernoulli
Coin
Binomial
Hypergeometric
Rademacher
"""

from __future__ import print_function, division

from sympy import (S, sympify, Rational, binomial, cacheit, Integer,
        Dict, Basic, KroneckerDelta, Dummy)
from sympy.concrete.summations import Sum
from sympy.core.compatibility import as_int, range
from sympy.core.logic import fuzzy_not, fuzzy_and
from sympy.stats.frv import (SingleFinitePSpace, SingleFiniteDistribution)

__all__ = ['FiniteRV', 'DiscreteUniform', 'Die', 'Bernoulli', 'Coin',
        'Binomial', 'Hypergeometric']

def rv(name, cls, *args):
    density = cls(*args)
    return SingleFinitePSpace(name, density).value

class FiniteDistributionHandmade(SingleFiniteDistribution):
    @property
    def dict(self):
        return self.args[0]

    def __new__(cls, density):
        density = Dict(density)
        for k in density.values():
            k_sym = sympify(k)
            if fuzzy_not(fuzzy_and((k_sym.is_nonnegative, (k_sym - 1).is_nonpositive))):
                raise ValueError("Probability at a point must be between 0 and 1.")
        sum_sym = sum(density.values())
        if sum_sym != 1:
            raise ValueError("Total Probability must be equal to 1.")
        return Basic.__new__(cls, density)

def FiniteRV(name, density):
    """
    Create a Finite Random Variable given a dict representing the density.

    Returns a RandomSymbol.

    >>> from sympy.stats import FiniteRV, P, E

    >>> density = {0: .1, 1: .2, 2: .3, 3: .4}
    >>> X = FiniteRV('X', density)

    >>> E(X)
    2.00000000000000
    >>> P(X >= 2)
    0.700000000000000
    """
    return rv(name, FiniteDistributionHandmade, density)

class DiscreteUniformDistribution(SingleFiniteDistribution):
    @property
    def p(self):
        return Rational(1, len(self.args))

    @property
    @cacheit
    def dict(self):
        return dict((k, self.p) for k in self.set)

    @property
    def set(self):
        return self.args

    def pdf(self, x):
        if x in self.args:
            return self.p
        else:
            return S.Zero


def DiscreteUniform(name, items):
    """
    Create a Finite Random Variable representing a uniform distribution over
    the input set.

    Returns a RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import DiscreteUniform, density
    >>> from sympy import symbols

    >>> X = DiscreteUniform('X', symbols('a b c')) # equally likely over a, b, c
    >>> density(X).dict
    {a: 1/3, b: 1/3, c: 1/3}

    >>> Y = DiscreteUniform('Y', list(range(5))) # distribution over a range
    >>> density(Y).dict
    {0: 1/5, 1: 1/5, 2: 1/5, 3: 1/5, 4: 1/5}

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Discrete_uniform_distribution
    .. [2] http://mathworld.wolfram.com/DiscreteUniformDistribution.html

    """
    return rv(name, DiscreteUniformDistribution, *items)


class DieDistribution(SingleFiniteDistribution):
    _argnames = ('sides',)

    def __new__(cls, sides):
        sides_sym = sympify(sides)
        if fuzzy_not(fuzzy_and((sides_sym.is_integer, sides_sym.is_positive))):
            raise ValueError("'sides' must be a positive integer.")
        else:
            return super(DieDistribution, cls).__new__(cls, sides)

    @property
    @cacheit
    def dict(self):
        as_int(self.sides) # Check that self.sides can be converted to an integer
        return super(DieDistribution, self).dict

    @property
    def set(self):
        return list(map(Integer, list(range(1, self.sides + 1))))

    def pdf(self, x):
        x = sympify(x)
        if x.is_number:
            if x.is_Integer and x >= 1 and x <= self.sides:
                return Rational(1, self.sides)
            return S.Zero
        if x.is_Symbol:
            i = Dummy('i', integer=True, positive=True)
            return Sum(KroneckerDelta(x, i)/self.sides, (i, 1, self.sides))
        raise ValueError("'x' expected as an argument of type 'number' or 'symbol', "
                        "not %s" % (type(x)))


def Die(name, sides=6):
    """
    Create a Finite Random Variable representing a fair die.

    Returns a RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Die, density

    >>> D6 = Die('D6', 6) # Six sided Die
    >>> density(D6).dict
    {1: 1/6, 2: 1/6, 3: 1/6, 4: 1/6, 5: 1/6, 6: 1/6}

    >>> D4 = Die('D4', 4) # Four sided Die
    >>> density(D4).dict
    {1: 1/4, 2: 1/4, 3: 1/4, 4: 1/4}
    """

    return rv(name, DieDistribution, sides)


class BernoulliDistribution(SingleFiniteDistribution):
    _argnames = ('p', 'succ', 'fail')

    def __new__(cls, *args):
        p = args[BernoulliDistribution._argnames.index('p')]
        p_sym = sympify(p)

        if fuzzy_not(fuzzy_and((p_sym.is_nonnegative, (p_sym - 1).is_nonpositive))):
            raise ValueError("p = %s is not in range [0, 1]." % str(p))
        else:
            return super(BernoulliDistribution, cls).__new__(cls, *args)

    @property
    @cacheit
    def dict(self):
        return {self.succ: self.p, self.fail: 1 - self.p}


def Bernoulli(name, p, succ=1, fail=0):
    """
    Create a Finite Random Variable representing a Bernoulli process.

    Returns a RandomSymbol

    Examples
    ========

    >>> from sympy.stats import Bernoulli, density
    >>> from sympy import S

    >>> X = Bernoulli('X', S(3)/4) # 1-0 Bernoulli variable, probability = 3/4
    >>> density(X).dict
    {0: 1/4, 1: 3/4}

    >>> X = Bernoulli('X', S.Half, 'Heads', 'Tails') # A fair coin toss
    >>> density(X).dict
    {Heads: 1/2, Tails: 1/2}

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Bernoulli_distribution
    .. [2] http://mathworld.wolfram.com/BernoulliDistribution.html

    """

    return rv(name, BernoulliDistribution, p, succ, fail)


def Coin(name, p=S.Half):
    """
    Create a Finite Random Variable representing a Coin toss.

    Probability p is the chance of gettings "Heads." Half by default

    Returns a RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Coin, density
    >>> from sympy import Rational

    >>> C = Coin('C') # A fair coin toss
    >>> density(C).dict
    {H: 1/2, T: 1/2}

    >>> C2 = Coin('C2', Rational(3, 5)) # An unfair coin
    >>> density(C2).dict
    {H: 3/5, T: 2/5}

    See Also
    ========

    sympy.stats.Binomial

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Coin_flipping

    """
    return rv(name, BernoulliDistribution, p, 'H', 'T')


class BinomialDistribution(SingleFiniteDistribution):
    _argnames = ('n', 'p', 'succ', 'fail')

    def __new__(cls, *args):
        n = args[BinomialDistribution._argnames.index('n')]
        p = args[BinomialDistribution._argnames.index('p')]
        n_sym = sympify(n)
        p_sym = sympify(p)

        if fuzzy_not(fuzzy_and((n_sym.is_integer, n_sym.is_nonnegative))):
            raise ValueError("'n' must be positive integer. n = %s." % str(n))
        elif fuzzy_not(fuzzy_and((p_sym.is_nonnegative, (p_sym - 1).is_nonpositive))):
            raise ValueError("'p' must be: 0 <= p <= 1 . p = %s" % str(p))
        else:
            return super(BinomialDistribution, cls).__new__(cls, *args)

    @property
    @cacheit
    def dict(self):
        n, p, succ, fail = self.n, self.p, self.succ, self.fail
        n = as_int(n)
        return dict((k*succ + (n - k)*fail,
                binomial(n, k) * p**k * (1 - p)**(n - k)) for k in range(0, n + 1))


def Binomial(name, n, p, succ=1, fail=0):
    """
    Create a Finite Random Variable representing a binomial distribution.

    Returns a RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Binomial, density
    >>> from sympy import S

    >>> X = Binomial('X', 4, S.Half) # Four "coin flips"
    >>> density(X).dict
    {0: 1/16, 1: 1/4, 2: 3/8, 3: 1/4, 4: 1/16}

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Binomial_distribution
    .. [2] http://mathworld.wolfram.com/BinomialDistribution.html

    """

    return rv(name, BinomialDistribution, n, p, succ, fail)


class HypergeometricDistribution(SingleFiniteDistribution):
    _argnames = ('N', 'm', 'n')

    @property
    @cacheit
    def dict(self):
        N, m, n = self.N, self.m, self.n
        N, m, n = list(map(sympify, (N, m, n)))
        density = dict((sympify(k),
                        Rational(binomial(m, k) * binomial(N - m, n - k),
                                 binomial(N, n)))
                        for k in range(max(0, n + m - N), min(m, n) + 1))
        return density


def Hypergeometric(name, N, m, n):
    """
    Create a Finite Random Variable representing a hypergeometric distribution.

    Returns a RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Hypergeometric, density
    >>> from sympy import S

    >>> X = Hypergeometric('X', 10, 5, 3) # 10 marbles, 5 white (success), 3 draws
    >>> density(X).dict
    {0: 1/12, 1: 5/12, 2: 5/12, 3: 1/12}

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Hypergeometric_distribution
    .. [2] http://mathworld.wolfram.com/HypergeometricDistribution.html

    """
    return rv(name, HypergeometricDistribution, N, m, n)


class RademacherDistribution(SingleFiniteDistribution):
    @property
    @cacheit
    def dict(self):
        return {-1: S.Half, 1: S.Half}


def Rademacher(name):
    """
    Create a Finite Random Variable representing a Rademacher distribution.

    Return a RandomSymbol.

    Examples
    ========

    >>> from sympy.stats import Rademacher, density

    >>> X = Rademacher('X')
    >>> density(X).dict
    {-1: 1/2, 1: 1/2}

    See Also
    ========

    sympy.stats.Bernoulli

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Rademacher_distribution

    """
    return rv(name, RademacherDistribution)
