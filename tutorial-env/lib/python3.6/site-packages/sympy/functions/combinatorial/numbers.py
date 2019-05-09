"""
This module implements some special functions that commonly appear in
combinatorial contexts (e.g. in power series); in particular,
sequences of rational numbers such as Bernoulli and Fibonacci numbers.

Factorials, binomial coefficients and related functions are located in
the separate 'factorials' module.
"""

from __future__ import print_function, division

from sympy.core import S, Symbol, Rational, Integer, Add, Dummy
from sympy.core.cache import cacheit
from sympy.core.compatibility import as_int, SYMPY_INTS, range
from sympy.core.function import Function, expand_mul
from sympy.core.logic import fuzzy_not
from sympy.core.numbers import E, pi
from sympy.core.relational import LessThan, StrictGreaterThan
from sympy.functions.combinatorial.factorials import binomial, factorial
from sympy.functions.elementary.exponential import log
from sympy.functions.elementary.integers import floor
from sympy.functions.elementary.miscellaneous import sqrt, cbrt
from sympy.functions.elementary.trigonometric import sin, cos, cot
from sympy.ntheory import isprime
from sympy.ntheory.primetest import is_square
from sympy.utilities.memoization import recurrence_memo

from mpmath import bernfrac, workprec
from mpmath.libmp import ifib as _ifib


def _product(a, b):
    p = 1
    for k in range(a, b + 1):
        p *= k
    return p



# Dummy symbol used for computing polynomial sequences
_sym = Symbol('x')
_symbols = Function('x')


#----------------------------------------------------------------------------#
#                                                                            #
#                           Carmichael numbers                               #
#                                                                            #
#----------------------------------------------------------------------------#


class carmichael(Function):
    """
    Carmichael Numbers:

    Certain cryptographic algorithms make use of big prime numbers.
    However, checking whether a big number is prime is not so easy.
    Randomized prime number checking tests exist that offer a high degree of confidence of
    accurate determination at low cost, such as the Fermat test.

    Let 'a' be a random number between 2 and n - 1, where n is the number whose primality we are testing.
    Then, n is probably prime if it satisfies the modular arithmetic congruence relation :

    a^(n-1) = 1(mod n).
    (where mod refers to the modulo operation)

    If a number passes the Fermat test several times, then it is prime with a
    high probability.

    Unfortunately, certain composite numbers (non-primes) still pass the Fermat test
    with every number smaller than themselves.
    These numbers are called Carmichael numbers.

    A Carmichael number will pass a Fermat primality test to every base b relatively prime to the number,
    even though it is not actually prime. This makes tests based on Fermat's Little Theorem less effective than
    strong probable prime tests such as the Baillie-PSW primality test and the Miller-Rabin primality test.
    mr functions given in sympy/sympy/ntheory/primetest.py will produce wrong results for each and every
    carmichael number.

    Examples
    ========

    >>> from sympy import carmichael
    >>> carmichael.find_first_n_carmichaels(5)
    [561, 1105, 1729, 2465, 2821]
    >>> carmichael.is_prime(2465)
    False
    >>> carmichael.is_prime(1729)
    False
    >>> carmichael.find_carmichael_numbers_in_range(0, 562)
    [561]
    >>> carmichael.find_carmichael_numbers_in_range(0,1000)
    [561]
    >>> carmichael.find_carmichael_numbers_in_range(0,2000)
    [561, 1105, 1729]

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Carmichael_number
    .. [2] https://en.wikipedia.org/wiki/Fermat_primality_test
    .. [3] https://www.jstor.org/stable/23248683?seq=1#metadata_info_tab_contents
    """

    @staticmethod
    def is_perfect_square(n):
        return is_square(n)

    @staticmethod
    def divides(p, n):
        return n % p == 0

    @staticmethod
    def is_prime(n):
        return isprime(n)

    @staticmethod
    def is_carmichael(n):
        if n >= 0:
            if (n == 1) or (carmichael.is_prime(n)) or (n % 2 == 0):
                return False

            divisors = list([1, n])

            # get divisors
            for i in range(3, n // 2 + 1, 2):
                if n % i == 0:
                    divisors.append(i)

            for i in divisors:
                if carmichael.is_perfect_square(i) and i != 1:
                    return False
                if carmichael.is_prime(i):
                    if not carmichael.divides(i - 1, n - 1):
                        return False

            return True

        else:
            raise ValueError('The provided number must be greater than or equal to 0')

    @staticmethod
    def find_carmichael_numbers_in_range(x, y):
        if 0 <= x <= y:
            if x % 2 == 0:
                return list([i for i in range(x + 1, y, 2) if carmichael.is_carmichael(i)])
            else:
                return list([i for i in range(x, y, 2) if carmichael.is_carmichael(i)])

        else:
            raise ValueError('The provided range is not valid. x and y must be non-negative integers and x <= y')

    @staticmethod
    def find_first_n_carmichaels(n):
        i = 1
        carmichaels = list()

        while len(carmichaels) < n:
            if carmichael.is_carmichael(i):
                carmichaels.append(i)
            i += 2

        return carmichaels


#----------------------------------------------------------------------------#
#                                                                            #
#                           Fibonacci numbers                                #
#                                                                            #
#----------------------------------------------------------------------------#


class fibonacci(Function):
    r"""
    Fibonacci numbers / Fibonacci polynomials

    The Fibonacci numbers are the integer sequence defined by the
    initial terms `F_0 = 0`, `F_1 = 1` and the two-term recurrence
    relation `F_n = F_{n-1} + F_{n-2}`.  This definition
    extended to arbitrary real and complex arguments using
    the formula

    .. math :: F_z = \frac{\phi^z - \cos(\pi z) \phi^{-z}}{\sqrt 5}

    The Fibonacci polynomials are defined by `F_1(x) = 1`,
    `F_2(x) = x`, and `F_n(x) = x*F_{n-1}(x) + F_{n-2}(x)` for `n > 2`.
    For all positive integers `n`, `F_n(1) = F_n`.

    * ``fibonacci(n)`` gives the `n^{th}` Fibonacci number, `F_n`
    * ``fibonacci(n, x)`` gives the `n^{th}` Fibonacci polynomial in `x`, `F_n(x)`

    Examples
    ========

    >>> from sympy import fibonacci, Symbol

    >>> [fibonacci(x) for x in range(11)]
    [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    >>> fibonacci(5, Symbol('t'))
    t**4 + 3*t**2 + 1

    See Also
    ========

    bell, bernoulli, catalan, euler, harmonic, lucas, genocchi, partition, tribonacci

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Fibonacci_number
    .. [2] http://mathworld.wolfram.com/FibonacciNumber.html

    """

    @staticmethod
    def _fib(n):
        return _ifib(n)

    @staticmethod
    @recurrence_memo([None, S.One, _sym])
    def _fibpoly(n, prev):
        return (prev[-2] + _sym*prev[-1]).expand()

    @classmethod
    def eval(cls, n, sym=None):
        if n is S.Infinity:
            return S.Infinity

        if n.is_Integer:
            n = int(n)
            if n < 0:
                return S.NegativeOne**(n + 1) * fibonacci(-n)
            if sym is None:
                return Integer(cls._fib(n))
            else:
                if n < 1:
                    raise ValueError("Fibonacci polynomials are defined "
                       "only for positive integer indices.")
                return cls._fibpoly(n).subs(_sym, sym)

    def _eval_rewrite_as_sqrt(self, n, **kwargs):
        return 2**(-n)*sqrt(5)*((1 + sqrt(5))**n - (-sqrt(5) + 1)**n) / 5

    def _eval_rewrite_as_GoldenRatio(self,n, **kwargs):
        return (S.GoldenRatio**n - 1/(-S.GoldenRatio)**n)/(2*S.GoldenRatio-1)


#----------------------------------------------------------------------------#
#                                                                            #
#                               Lucas numbers                                #
#                                                                            #
#----------------------------------------------------------------------------#


class lucas(Function):
    """
    Lucas numbers

    Lucas numbers satisfy a recurrence relation similar to that of
    the Fibonacci sequence, in which each term is the sum of the
    preceding two. They are generated by choosing the initial
    values `L_0 = 2` and `L_1 = 1`.

    * ``lucas(n)`` gives the `n^{th}` Lucas number

    Examples
    ========

    >>> from sympy import lucas

    >>> [lucas(x) for x in range(11)]
    [2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123]

    See Also
    ========

    bell, bernoulli, catalan, euler, fibonacci, harmonic, genocchi, partition, tribonacci

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Lucas_number
    .. [2] http://mathworld.wolfram.com/LucasNumber.html

    """

    @classmethod
    def eval(cls, n):
        if n is S.Infinity:
            return S.Infinity

        if n.is_Integer:
            return fibonacci(n + 1) + fibonacci(n - 1)

    def _eval_rewrite_as_sqrt(self, n, **kwargs):
        return 2**(-n)*((1 + sqrt(5))**n + (-sqrt(5) + 1)**n)


#----------------------------------------------------------------------------#
#                                                                            #
#                             Tribonacci numbers                             #
#                                                                            #
#----------------------------------------------------------------------------#


class tribonacci(Function):
    r"""
    Tribonacci numbers / Tribonacci polynomials

    The Tribonacci numbers are the integer sequence defined by the
    initial terms `T_0 = 0`, `T_1 = 1`, `T_2 = 1` and the three-term
    recurrence relation `T_n = T_{n-1} + T_{n-2} + T_{n-3}`.

    The Tribonacci polynomials are defined by `T_0(x) = 0`, `T_1(x) = 1`,
    `T_2(x) = x^2`, and `T_n(x) = x^2 T_{n-1}(x) + x T_{n-2}(x) + T_{n-3}(x)`
    for `n > 2`.  For all positive integers `n`, `T_n(1) = T_n`.

    * ``tribonacci(n)`` gives the `n^{th}` Tribonacci number, `T_n`
    * ``tribonacci(n, x)`` gives the `n^{th}` Tribonacci polynomial in `x`, `T_n(x)`

    Examples
    ========

    >>> from sympy import tribonacci, Symbol

    >>> [tribonacci(x) for x in range(11)]
    [0, 1, 1, 2, 4, 7, 13, 24, 44, 81, 149]
    >>> tribonacci(5, Symbol('t'))
    t**8 + 3*t**5 + 3*t**2

    See Also
    ========

    bell, bernoulli, catalan, euler, fibonacci, harmonic, lucas, genocchi, partition

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Generalizations_of_Fibonacci_numbers#Tribonacci_numbers
    .. [2] http://mathworld.wolfram.com/TribonacciNumber.html
    .. [3] https://oeis.org/A000073

    """

    @staticmethod
    @recurrence_memo([S.Zero, S.One, S.One])
    def _trib(n, prev):
        return (prev[-3] + prev[-2] + prev[-1])

    @staticmethod
    @recurrence_memo([S.Zero, S.One, _sym**2])
    def _tribpoly(n, prev):
        return (prev[-3] + _sym*prev[-2] + _sym**2*prev[-1]).expand()

    @classmethod
    def eval(cls, n, sym=None):
        if n is S.Infinity:
            return S.Infinity

        if n.is_Integer:
            n = int(n)
            if n < 0:
                raise ValueError("Tribonacci polynomials are defined "
                       "only for non-negative integer indices.")
            if sym is None:
                return Integer(cls._trib(n))
            else:
                return cls._tribpoly(n).subs(_sym, sym)

    def _eval_rewrite_as_sqrt(self, n, **kwargs):
        w = (-1 + S.ImaginaryUnit * sqrt(3)) / 2
        a = (1 + cbrt(19 + 3*sqrt(33)) + cbrt(19 - 3*sqrt(33))) / 3
        b = (1 + w*cbrt(19 + 3*sqrt(33)) + w**2*cbrt(19 - 3*sqrt(33))) / 3
        c = (1 + w**2*cbrt(19 + 3*sqrt(33)) + w*cbrt(19 - 3*sqrt(33))) / 3
        Tn = (a**(n + 1)/((a - b)*(a - c))
            + b**(n + 1)/((b - a)*(b - c))
            + c**(n + 1)/((c - a)*(c - b)))
        return Tn

    def _eval_rewrite_as_TribonacciConstant(self, n, **kwargs):
        b = cbrt(586 + 102*sqrt(33))
        Tn = 3 * b * S.TribonacciConstant**n / (b**2 - 2*b + 4)
        return floor(Tn + S.Half)


#----------------------------------------------------------------------------#
#                                                                            #
#                           Bernoulli numbers                                #
#                                                                            #
#----------------------------------------------------------------------------#


class bernoulli(Function):
    r"""
    Bernoulli numbers / Bernoulli polynomials

    The Bernoulli numbers are a sequence of rational numbers
    defined by `B_0 = 1` and the recursive relation (`n > 0`):

    .. math :: 0 = \sum_{k=0}^n \binom{n+1}{k} B_k

    They are also commonly defined by their exponential generating
    function, which is `\frac{x}{e^x - 1}`. For odd indices > 1, the
    Bernoulli numbers are zero.

    The Bernoulli polynomials satisfy the analogous formula:

    .. math :: B_n(x) = \sum_{k=0}^n \binom{n}{k} B_k x^{n-k}

    Bernoulli numbers and Bernoulli polynomials are related as
    `B_n(0) = B_n`.

    We compute Bernoulli numbers using Ramanujan's formula:

    .. math :: B_n = \frac{A(n) - S(n)}{\binom{n+3}{n}}

    where:

    .. math :: A(n) = \begin{cases} \frac{n+3}{3} &
        n \equiv 0\ \text{or}\ 2 \pmod{6} \\
        -\frac{n+3}{6} & n \equiv 4 \pmod{6} \end{cases}

    and:

    .. math :: S(n) = \sum_{k=1}^{[n/6]} \binom{n+3}{n-6k} B_{n-6k}

    This formula is similar to the sum given in the definition, but
    cuts 2/3 of the terms. For Bernoulli polynomials, we use the
    formula in the definition.

    * ``bernoulli(n)`` gives the nth Bernoulli number, `B_n`
    * ``bernoulli(n, x)`` gives the nth Bernoulli polynomial in `x`, `B_n(x)`

    Examples
    ========

    >>> from sympy import bernoulli

    >>> [bernoulli(n) for n in range(11)]
    [1, -1/2, 1/6, 0, -1/30, 0, 1/42, 0, -1/30, 0, 5/66]
    >>> bernoulli(1000001)
    0

    See Also
    ========

    bell, catalan, euler, fibonacci, harmonic, lucas, genocchi, partition, tribonacci

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Bernoulli_number
    .. [2] https://en.wikipedia.org/wiki/Bernoulli_polynomial
    .. [3] http://mathworld.wolfram.com/BernoulliNumber.html
    .. [4] http://mathworld.wolfram.com/BernoulliPolynomial.html

    """

    # Calculates B_n for positive even n
    @staticmethod
    def _calc_bernoulli(n):
        s = 0
        a = int(binomial(n + 3, n - 6))
        for j in range(1, n//6 + 1):
            s += a * bernoulli(n - 6*j)
            # Avoid computing each binomial coefficient from scratch
            a *= _product(n - 6 - 6*j + 1, n - 6*j)
            a //= _product(6*j + 4, 6*j + 9)
        if n % 6 == 4:
            s = -Rational(n + 3, 6) - s
        else:
            s = Rational(n + 3, 3) - s
        return s / binomial(n + 3, n)

    # We implement a specialized memoization scheme to handle each
    # case modulo 6 separately
    _cache = {0: S.One, 2: Rational(1, 6), 4: Rational(-1, 30)}
    _highest = {0: 0, 2: 2, 4: 4}

    @classmethod
    def eval(cls, n, sym=None):
        if n.is_Number:
            if n.is_Integer and n.is_nonnegative:
                if n is S.Zero:
                    return S.One
                elif n is S.One:
                    if sym is None:
                        return -S.Half
                    else:
                        return sym - S.Half
                # Bernoulli numbers
                elif sym is None:
                    if n.is_odd:
                        return S.Zero
                    n = int(n)
                    # Use mpmath for enormous Bernoulli numbers
                    if n > 500:
                        p, q = bernfrac(n)
                        return Rational(int(p), int(q))
                    case = n % 6
                    highest_cached = cls._highest[case]
                    if n <= highest_cached:
                        return cls._cache[n]
                    # To avoid excessive recursion when, say, bernoulli(1000) is
                    # requested, calculate and cache the entire sequence ... B_988,
                    # B_994, B_1000 in increasing order
                    for i in range(highest_cached + 6, n + 6, 6):
                        b = cls._calc_bernoulli(i)
                        cls._cache[i] = b
                        cls._highest[case] = i
                    return b
                # Bernoulli polynomials
                else:
                    n, result = int(n), []
                    for k in range(n + 1):
                        result.append(binomial(n, k)*cls(k)*sym**(n - k))
                    return Add(*result)
            else:
                raise ValueError("Bernoulli numbers are defined only"
                                 " for nonnegative integer indices.")

        if sym is None:
            if n.is_odd and (n - 1).is_positive:
                return S.Zero


#----------------------------------------------------------------------------#
#                                                                            #
#                                Bell numbers                                #
#                                                                            #
#----------------------------------------------------------------------------#


class bell(Function):
    r"""
    Bell numbers / Bell polynomials

    The Bell numbers satisfy `B_0 = 1` and

    .. math:: B_n = \sum_{k=0}^{n-1} \binom{n-1}{k} B_k.

    They are also given by:

    .. math:: B_n = \frac{1}{e} \sum_{k=0}^{\infty} \frac{k^n}{k!}.

    The Bell polynomials are given by `B_0(x) = 1` and

    .. math:: B_n(x) = x \sum_{k=1}^{n-1} \binom{n-1}{k-1} B_{k-1}(x).

    The second kind of Bell polynomials (are sometimes called "partial" Bell
    polynomials or incomplete Bell polynomials) are defined as

    .. math:: B_{n,k}(x_1, x_2,\dotsc x_{n-k+1}) =
            \sum_{j_1+j_2+j_2+\dotsb=k \atop j_1+2j_2+3j_2+\dotsb=n}
                \frac{n!}{j_1!j_2!\dotsb j_{n-k+1}!}
                \left(\frac{x_1}{1!} \right)^{j_1}
                \left(\frac{x_2}{2!} \right)^{j_2} \dotsb
                \left(\frac{x_{n-k+1}}{(n-k+1)!} \right) ^{j_{n-k+1}}.

    * ``bell(n)`` gives the `n^{th}` Bell number, `B_n`.
    * ``bell(n, x)`` gives the `n^{th}` Bell polynomial, `B_n(x)`.
    * ``bell(n, k, (x1, x2, ...))`` gives Bell polynomials of the second kind,
      `B_{n,k}(x_1, x_2, \dotsc, x_{n-k+1})`.

    Notes
    =====

    Not to be confused with Bernoulli numbers and Bernoulli polynomials,
    which use the same notation.

    Examples
    ========

    >>> from sympy import bell, Symbol, symbols

    >>> [bell(n) for n in range(11)]
    [1, 1, 2, 5, 15, 52, 203, 877, 4140, 21147, 115975]
    >>> bell(30)
    846749014511809332450147
    >>> bell(4, Symbol('t'))
    t**4 + 6*t**3 + 7*t**2 + t
    >>> bell(6, 2, symbols('x:6')[1:])
    6*x1*x5 + 15*x2*x4 + 10*x3**2

    See Also
    ========

    bernoulli, catalan, euler, fibonacci, harmonic, lucas, genocchi, partition, tribonacci

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Bell_number
    .. [2] http://mathworld.wolfram.com/BellNumber.html
    .. [3] http://mathworld.wolfram.com/BellPolynomial.html

    """

    @staticmethod
    @recurrence_memo([1, 1])
    def _bell(n, prev):
        s = 1
        a = 1
        for k in range(1, n):
            a = a * (n - k) // k
            s += a * prev[k]
        return s

    @staticmethod
    @recurrence_memo([S.One, _sym])
    def _bell_poly(n, prev):
        s = 1
        a = 1
        for k in range(2, n + 1):
            a = a * (n - k + 1) // (k - 1)
            s += a * prev[k - 1]
        return expand_mul(_sym * s)

    @staticmethod
    def _bell_incomplete_poly(n, k, symbols):
        r"""
        The second kind of Bell polynomials (incomplete Bell polynomials).

        Calculated by recurrence formula:

        .. math:: B_{n,k}(x_1, x_2, \dotsc, x_{n-k+1}) =
                \sum_{m=1}^{n-k+1}
                \x_m \binom{n-1}{m-1} B_{n-m,k-1}(x_1, x_2, \dotsc, x_{n-m-k})

        where
            `B_{0,0} = 1;`
            `B_{n,0} = 0; for n \ge 1`
            `B_{0,k} = 0; for k \ge 1`

        """
        if (n == 0) and (k == 0):
            return S.One
        elif (n == 0) or (k == 0):
            return S.Zero
        s = S.Zero
        a = S.One
        for m in range(1, n - k + 2):
            s += a * bell._bell_incomplete_poly(
                n - m, k - 1, symbols) * symbols[m - 1]
            a = a * (n - m) / m
        return expand_mul(s)

    @classmethod
    def eval(cls, n, k_sym=None, symbols=None):
        if n is S.Infinity:
            if k_sym is None:
                return S.Infinity
            else:
                raise ValueError("Bell polynomial is not defined")

        if n.is_negative or n.is_integer is False:
            raise ValueError("a non-negative integer expected")

        if n.is_Integer and n.is_nonnegative:
            if k_sym is None:
                return Integer(cls._bell(int(n)))
            elif symbols is None:
                return cls._bell_poly(int(n)).subs(_sym, k_sym)
            else:
                r = cls._bell_incomplete_poly(int(n), int(k_sym), symbols)
                return r

    def _eval_rewrite_as_Sum(self, n, k_sym=None, symbols=None, **kwargs):
        from sympy import Sum
        if (k_sym is not None) or (symbols is not None):
            return self

        # Dobinski's formula
        if not n.is_nonnegative:
            return self
        k = Dummy('k', integer=True, nonnegative=True)
        return 1 / E * Sum(k**n / factorial(k), (k, 0, S.Infinity))


#----------------------------------------------------------------------------#
#                                                                            #
#                              Harmonic numbers                              #
#                                                                            #
#----------------------------------------------------------------------------#


class harmonic(Function):
    r"""
    Harmonic numbers

    The nth harmonic number is given by `\operatorname{H}_{n} =
    1 + \frac{1}{2} + \frac{1}{3} + \ldots + \frac{1}{n}`.

    More generally:

    .. math:: \operatorname{H}_{n,m} = \sum_{k=1}^{n} \frac{1}{k^m}

    As `n \rightarrow \infty`, `\operatorname{H}_{n,m} \rightarrow \zeta(m)`,
    the Riemann zeta function.

    * ``harmonic(n)`` gives the nth harmonic number, `\operatorname{H}_n`

    * ``harmonic(n, m)`` gives the nth generalized harmonic number
      of order `m`, `\operatorname{H}_{n,m}`, where
      ``harmonic(n) == harmonic(n, 1)``

    Examples
    ========

    >>> from sympy import harmonic, oo

    >>> [harmonic(n) for n in range(6)]
    [0, 1, 3/2, 11/6, 25/12, 137/60]
    >>> [harmonic(n, 2) for n in range(6)]
    [0, 1, 5/4, 49/36, 205/144, 5269/3600]
    >>> harmonic(oo, 2)
    pi**2/6

    >>> from sympy import Symbol, Sum
    >>> n = Symbol("n")

    >>> harmonic(n).rewrite(Sum)
    Sum(1/_k, (_k, 1, n))

    We can evaluate harmonic numbers for all integral and positive
    rational arguments:

    >>> from sympy import S, expand_func, simplify
    >>> harmonic(8)
    761/280
    >>> harmonic(11)
    83711/27720

    >>> H = harmonic(1/S(3))
    >>> H
    harmonic(1/3)
    >>> He = expand_func(H)
    >>> He
    -log(6) - sqrt(3)*pi/6 + 2*Sum(log(sin(_k*pi/3))*cos(2*_k*pi/3), (_k, 1, 1))
                           + 3*Sum(1/(3*_k + 1), (_k, 0, 0))
    >>> He.doit()
    -log(6) - sqrt(3)*pi/6 - log(sqrt(3)/2) + 3
    >>> H = harmonic(25/S(7))
    >>> He = simplify(expand_func(H).doit())
    >>> He
    log(sin(pi/7)**(-2*cos(pi/7))*sin(2*pi/7)**(2*cos(16*pi/7))*cos(pi/14)**(-2*sin(pi/14))/14)
    + pi*tan(pi/14)/2 + 30247/9900
    >>> He.n(40)
    1.983697455232980674869851942390639915940
    >>> harmonic(25/S(7)).n(40)
    1.983697455232980674869851942390639915940

    We can rewrite harmonic numbers in terms of polygamma functions:

    >>> from sympy import digamma, polygamma
    >>> m = Symbol("m")

    >>> harmonic(n).rewrite(digamma)
    polygamma(0, n + 1) + EulerGamma

    >>> harmonic(n).rewrite(polygamma)
    polygamma(0, n + 1) + EulerGamma

    >>> harmonic(n,3).rewrite(polygamma)
    polygamma(2, n + 1)/2 - polygamma(2, 1)/2

    >>> harmonic(n,m).rewrite(polygamma)
    (-1)**m*(polygamma(m - 1, 1) - polygamma(m - 1, n + 1))/factorial(m - 1)

    Integer offsets in the argument can be pulled out:

    >>> from sympy import expand_func

    >>> expand_func(harmonic(n+4))
    harmonic(n) + 1/(n + 4) + 1/(n + 3) + 1/(n + 2) + 1/(n + 1)

    >>> expand_func(harmonic(n-4))
    harmonic(n) - 1/(n - 1) - 1/(n - 2) - 1/(n - 3) - 1/n

    Some limits can be computed as well:

    >>> from sympy import limit, oo

    >>> limit(harmonic(n), n, oo)
    oo

    >>> limit(harmonic(n, 2), n, oo)
    pi**2/6

    >>> limit(harmonic(n, 3), n, oo)
    -polygamma(2, 1)/2

    However we can not compute the general relation yet:

    >>> limit(harmonic(n, m), n, oo)
    harmonic(oo, m)

    which equals ``zeta(m)`` for ``m > 1``.

    See Also
    ========

    bell, bernoulli, catalan, euler, fibonacci, lucas, genocchi, partition, tribonacci

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Harmonic_number
    .. [2] http://functions.wolfram.com/GammaBetaErf/HarmonicNumber/
    .. [3] http://functions.wolfram.com/GammaBetaErf/HarmonicNumber2/

    """

    # Generate one memoized Harmonic number-generating function for each
    # order and store it in a dictionary
    _functions = {}

    @classmethod
    def eval(cls, n, m=None):
        from sympy import zeta
        if m is S.One:
            return cls(n)
        if m is None:
            m = S.One

        if m.is_zero:
            return n

        if n is S.Infinity and m.is_Number:
            # TODO: Fix for symbolic values of m
            if m.is_negative:
                return S.NaN
            elif LessThan(m, S.One):
                return S.Infinity
            elif StrictGreaterThan(m, S.One):
                return zeta(m)
            else:
                return cls

        if n == 0:
            return S.Zero

        if n.is_Integer and n.is_nonnegative and m.is_Integer:
            if not m in cls._functions:
                @recurrence_memo([0])
                def f(n, prev):
                    return prev[-1] + S.One / n**m
                cls._functions[m] = f
            return cls._functions[m](int(n))

    def _eval_rewrite_as_polygamma(self, n, m=1, **kwargs):
        from sympy.functions.special.gamma_functions import polygamma
        return S.NegativeOne**m/factorial(m - 1) * (polygamma(m - 1, 1) - polygamma(m - 1, n + 1))

    def _eval_rewrite_as_digamma(self, n, m=1, **kwargs):
        from sympy.functions.special.gamma_functions import polygamma
        return self.rewrite(polygamma)

    def _eval_rewrite_as_trigamma(self, n, m=1, **kwargs):
        from sympy.functions.special.gamma_functions import polygamma
        return self.rewrite(polygamma)

    def _eval_rewrite_as_Sum(self, n, m=None, **kwargs):
        from sympy import Sum
        k = Dummy("k", integer=True)
        if m is None:
            m = S.One
        return Sum(k**(-m), (k, 1, n))

    def _eval_expand_func(self, **hints):
        from sympy import Sum
        n = self.args[0]
        m = self.args[1] if len(self.args) == 2 else 1

        if m == S.One:
            if n.is_Add:
                off = n.args[0]
                nnew = n - off
                if off.is_Integer and off.is_positive:
                    result = [S.One/(nnew + i) for i in range(off, 0, -1)] + [harmonic(nnew)]
                    return Add(*result)
                elif off.is_Integer and off.is_negative:
                    result = [-S.One/(nnew + i) for i in range(0, off, -1)] + [harmonic(nnew)]
                    return Add(*result)

            if n.is_Rational:
                # Expansions for harmonic numbers at general rational arguments (u + p/q)
                # Split n as u + p/q with p < q
                p, q = n.as_numer_denom()
                u = p // q
                p = p - u * q
                if u.is_nonnegative and p.is_positive and q.is_positive and p < q:
                    k = Dummy("k")
                    t1 = q * Sum(1 / (q * k + p), (k, 0, u))
                    t2 = 2 * Sum(cos((2 * pi * p * k) / S(q)) *
                                   log(sin((pi * k) / S(q))),
                                   (k, 1, floor((q - 1) / S(2))))
                    t3 = (pi / 2) * cot((pi * p) / q) + log(2 * q)
                    return t1 + t2 - t3

        return self

    def _eval_rewrite_as_tractable(self, n, m=1, **kwargs):
        from sympy import polygamma
        return self.rewrite(polygamma).rewrite("tractable", deep=True)

    def _eval_evalf(self, prec):
        from sympy import polygamma
        if all(i.is_number for i in self.args):
            return self.rewrite(polygamma)._eval_evalf(prec)


#----------------------------------------------------------------------------#
#                                                                            #
#                           Euler numbers                                    #
#                                                                            #
#----------------------------------------------------------------------------#


class euler(Function):
    r"""
    Euler numbers / Euler polynomials

    The Euler numbers are given by:

    .. math:: E_{2n} = I \sum_{k=1}^{2n+1} \sum_{j=0}^k \binom{k}{j}
        \frac{(-1)^j (k-2j)^{2n+1}}{2^k I^k k}

    .. math:: E_{2n+1} = 0

    Euler numbers and Euler polynomials are related by

    .. math:: E_n = 2^n E_n\left(\frac{1}{2}\right).

    We compute symbolic Euler polynomials using [5]_

    .. math:: E_n(x) = \sum_{k=0}^n \binom{n}{k} \frac{E_k}{2^k}
                       \left(x - \frac{1}{2}\right)^{n-k}.

    However, numerical evaluation of the Euler polynomial is computed
    more efficiently (and more accurately) using the mpmath library.

    * ``euler(n)`` gives the `n^{th}` Euler number, `E_n`.
    * ``euler(n, x)`` gives the `n^{th}` Euler polynomial, `E_n(x)`.

    Examples
    ========

    >>> from sympy import Symbol, S
    >>> from sympy.functions import euler
    >>> [euler(n) for n in range(10)]
    [1, 0, -1, 0, 5, 0, -61, 0, 1385, 0]
    >>> n = Symbol("n")
    >>> euler(n + 2*n)
    euler(3*n)

    >>> x = Symbol("x")
    >>> euler(n, x)
    euler(n, x)

    >>> euler(0, x)
    1
    >>> euler(1, x)
    x - 1/2
    >>> euler(2, x)
    x**2 - x
    >>> euler(3, x)
    x**3 - 3*x**2/2 + 1/4
    >>> euler(4, x)
    x**4 - 2*x**3 + x

    >>> euler(12, S.Half)
    2702765/4096
    >>> euler(12)
    2702765

    See Also
    ========

    bell, bernoulli, catalan, fibonacci, harmonic, lucas, genocchi, partition, tribonacci

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Euler_numbers
    .. [2] http://mathworld.wolfram.com/EulerNumber.html
    .. [3] https://en.wikipedia.org/wiki/Alternating_permutation
    .. [4] http://mathworld.wolfram.com/AlternatingPermutation.html
    .. [5] http://dlmf.nist.gov/24.2#ii

    """

    @classmethod
    def eval(cls, m, sym=None):
        if m.is_Number:
            if m.is_Integer and m.is_nonnegative:
                # Euler numbers
                if sym is None:
                    if m.is_odd:
                        return S.Zero
                    from mpmath import mp
                    m = m._to_mpmath(mp.prec)
                    res = mp.eulernum(m, exact=True)
                    return Integer(res)
                # Euler polynomial
                else:
                    from sympy.core.evalf import pure_complex
                    reim = pure_complex(sym, or_real=True)
                    # Evaluate polynomial numerically using mpmath
                    if reim and all(a.is_Float or a.is_Integer for a in reim) \
                            and any(a.is_Float for a in reim):
                        from mpmath import mp
                        from sympy import Expr
                        m = int(m)
                        # XXX ComplexFloat (#12192) would be nice here, above
                        prec = min([a._prec for a in reim if a.is_Float])
                        with workprec(prec):
                            res = mp.eulerpoly(m, sym)
                        return Expr._from_mpmath(res, prec)
                    # Construct polynomial symbolically from definition
                    m, result = int(m), []
                    for k in range(m + 1):
                        result.append(binomial(m, k)*cls(k)/(2**k)*(sym - S.Half)**(m - k))
                    return Add(*result).expand()
            else:
                raise ValueError("Euler numbers are defined only"
                                 " for nonnegative integer indices.")
        if sym is None:
            if m.is_odd and m.is_positive:
                return S.Zero

    def _eval_rewrite_as_Sum(self, n, x=None, **kwargs):
        from sympy import Sum
        if x is None and n.is_even:
            k = Dummy("k", integer=True)
            j = Dummy("j", integer=True)
            n = n / 2
            Em = (S.ImaginaryUnit * Sum(Sum(binomial(k, j) * ((-1)**j * (k - 2*j)**(2*n + 1)) /
                  (2**k*S.ImaginaryUnit**k * k), (j, 0, k)), (k, 1, 2*n + 1)))
            return Em
        if x:
            k = Dummy("k", integer=True)
            return Sum(binomial(n, k)*euler(k)/2**k*(x-S.Half)**(n-k), (k, 0, n))

    def _eval_evalf(self, prec):
        m, x = (self.args[0], None) if len(self.args) == 1 else self.args

        if x is None and m.is_Integer and m.is_nonnegative:
            from mpmath import mp
            from sympy import Expr
            m = m._to_mpmath(prec)
            with workprec(prec):
                res = mp.eulernum(m)
            return Expr._from_mpmath(res, prec)
        if x and x.is_number and m.is_Integer and m.is_nonnegative:
            from mpmath import mp
            from sympy import Expr
            m = int(m)
            x = x._to_mpmath(prec)
            with workprec(prec):
                res = mp.eulerpoly(m, x)
            return Expr._from_mpmath(res, prec)

#----------------------------------------------------------------------------#
#                                                                            #
#                              Catalan numbers                               #
#                                                                            #
#----------------------------------------------------------------------------#


class catalan(Function):
    r"""
    Catalan numbers

    The `n^{th}` catalan number is given by:

    .. math :: C_n = \frac{1}{n+1} \binom{2n}{n}

    * ``catalan(n)`` gives the `n^{th}` Catalan number, `C_n`

    Examples
    ========

    >>> from sympy import (Symbol, binomial, gamma, hyper, polygamma,
    ...             catalan, diff, combsimp, Rational, I)

    >>> [catalan(i) for i in range(1,10)]
    [1, 2, 5, 14, 42, 132, 429, 1430, 4862]

    >>> n = Symbol("n", integer=True)

    >>> catalan(n)
    catalan(n)

    Catalan numbers can be transformed into several other, identical
    expressions involving other mathematical functions

    >>> catalan(n).rewrite(binomial)
    binomial(2*n, n)/(n + 1)

    >>> catalan(n).rewrite(gamma)
    4**n*gamma(n + 1/2)/(sqrt(pi)*gamma(n + 2))

    >>> catalan(n).rewrite(hyper)
    hyper((1 - n, -n), (2,), 1)

    For some non-integer values of n we can get closed form
    expressions by rewriting in terms of gamma functions:

    >>> catalan(Rational(1,2)).rewrite(gamma)
    8/(3*pi)

    We can differentiate the Catalan numbers C(n) interpreted as a
    continuous real function in n:

    >>> diff(catalan(n), n)
    (polygamma(0, n + 1/2) - polygamma(0, n + 2) + log(4))*catalan(n)

    As a more advanced example consider the following ratio
    between consecutive numbers:

    >>> combsimp((catalan(n + 1)/catalan(n)).rewrite(binomial))
    2*(2*n + 1)/(n + 2)

    The Catalan numbers can be generalized to complex numbers:

    >>> catalan(I).rewrite(gamma)
    4**I*gamma(1/2 + I)/(sqrt(pi)*gamma(2 + I))

    and evaluated with arbitrary precision:

    >>> catalan(I).evalf(20)
    0.39764993382373624267 - 0.020884341620842555705*I

    See Also
    ========

    bell, bernoulli, euler, fibonacci, harmonic, lucas, genocchi, partition, tribonacci
    sympy.functions.combinatorial.factorials.binomial

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Catalan_number
    .. [2] http://mathworld.wolfram.com/CatalanNumber.html
    .. [3] http://functions.wolfram.com/GammaBetaErf/CatalanNumber/
    .. [4] http://geometer.org/mathcircles/catalan.pdf

    """

    @classmethod
    def eval(cls, n):
        from sympy import gamma
        if (n.is_Integer and n.is_nonnegative) or \
           (n.is_noninteger and n.is_negative):
            return 4**n*gamma(n + S.Half)/(gamma(S.Half)*gamma(n + 2))

        if (n.is_integer and n.is_negative):
            if (n + 1).is_negative:
                return S.Zero
            if (n + 1).is_zero:
                return -S.Half

    def fdiff(self, argindex=1):
        from sympy import polygamma, log
        n = self.args[0]
        return catalan(n)*(polygamma(0, n + Rational(1, 2)) - polygamma(0, n + 2) + log(4))

    def _eval_rewrite_as_binomial(self, n, **kwargs):
        return binomial(2*n, n)/(n + 1)

    def _eval_rewrite_as_factorial(self, n, **kwargs):
        return factorial(2*n) / (factorial(n+1) * factorial(n))

    def _eval_rewrite_as_gamma(self, n, **kwargs):
        from sympy import gamma
        # The gamma function allows to generalize Catalan numbers to complex n
        return 4**n*gamma(n + S.Half)/(gamma(S.Half)*gamma(n + 2))

    def _eval_rewrite_as_hyper(self, n, **kwargs):
        from sympy import hyper
        return hyper([1 - n, -n], [2], 1)

    def _eval_rewrite_as_Product(self, n, **kwargs):
        from sympy import Product
        if not (n.is_integer and n.is_nonnegative):
            return self
        k = Dummy('k', integer=True, positive=True)
        return Product((n + k) / k, (k, 2, n))

    def _eval_is_integer(self):
        if self.args[0].is_integer and self.args[0].is_nonnegative:
            return True

    def _eval_is_positive(self):
        if self.args[0].is_nonnegative:
            return True

    def _eval_is_composite(self):
        if self.args[0].is_integer and (self.args[0] - 3).is_positive:
            return True

    def _eval_evalf(self, prec):
        from sympy import gamma
        if self.args[0].is_number:
            return self.rewrite(gamma)._eval_evalf(prec)



#----------------------------------------------------------------------------#
#                                                                            #
#                           Genocchi numbers                                 #
#                                                                            #
#----------------------------------------------------------------------------#


class genocchi(Function):
    r"""
    Genocchi numbers

    The Genocchi numbers are a sequence of integers `G_n` that satisfy the
    relation:

    .. math:: \frac{2t}{e^t + 1} = \sum_{n=1}^\infty \frac{G_n t^n}{n!}

    Examples
    ========

    >>> from sympy import Symbol
    >>> from sympy.functions import genocchi
    >>> [genocchi(n) for n in range(1, 9)]
    [1, -1, 0, 1, 0, -3, 0, 17]
    >>> n = Symbol('n', integer=True, positive=True)
    >>> genocchi(2*n + 1)
    0

    See Also
    ========

    bell, bernoulli, catalan, euler, fibonacci, harmonic, lucas, partition, tribonacci

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Genocchi_number
    .. [2] http://mathworld.wolfram.com/GenocchiNumber.html

    """

    @classmethod
    def eval(cls, n):
        if n.is_Number:
            if (not n.is_Integer) or n.is_nonpositive:
                raise ValueError("Genocchi numbers are defined only for " +
                                 "positive integers")
            return 2 * (1 - S(2) ** n) * bernoulli(n)

        if n.is_odd and (n - 1).is_positive:
            return S.Zero

        if (n - 1).is_zero:
            return S.One

    def _eval_rewrite_as_bernoulli(self, n, **kwargs):
        if n.is_integer and n.is_nonnegative:
            return (1 - S(2) ** n) * bernoulli(n) * 2

    def _eval_is_integer(self):
        if self.args[0].is_integer and self.args[0].is_positive:
            return True

    def _eval_is_negative(self):
        n = self.args[0]
        if n.is_integer and n.is_positive:
            if n.is_odd:
                return False
            return (n / 2).is_odd

    def _eval_is_positive(self):
        n = self.args[0]
        if n.is_integer and n.is_positive:
            if n.is_odd:
                return fuzzy_not((n - 1).is_positive)
            return (n / 2).is_even

    def _eval_is_even(self):
        n = self.args[0]
        if n.is_integer and n.is_positive:
            if n.is_even:
                return False
            return (n - 1).is_positive

    def _eval_is_odd(self):
        n = self.args[0]
        if n.is_integer and n.is_positive:
            if n.is_even:
                return True
            return fuzzy_not((n - 1).is_positive)

    def _eval_is_prime(self):
        n = self.args[0]
        # only G_6 = -3 and G_8 = 17 are prime,
        # but SymPy does not consider negatives as prime
        # so only n=8 is tested
        return (n - 8).is_zero


#----------------------------------------------------------------------------#
#                                                                            #
#                           Partition numbers                                #
#                                                                            #
#----------------------------------------------------------------------------#


class partition(Function):
    r"""
    Partition numbers

    The Partition numbers are a sequence of integers `p_n` that represent the
    number of distinct ways of representing `n` as a sum of natural numbers
    (with order irrelevant). The generating function for `p_n` is given by:

    .. math:: \sum_{n=0}^\infty p_n x^n = \prod_{k=1}^\infty (1 - x^k)^{-1}

    Examples
    ========

    >>> from sympy import Symbol
    >>> from sympy.functions import partition
    >>> [partition(n) for n in range(9)]
    [1, 1, 2, 3, 5, 7, 11, 15, 22]
    >>> n = Symbol('n', integer=True, negative=True)
    >>> partition(n)
    0

    See Also
    ========

    bell, bernoulli, catalan, euler, fibonacci, harmonic, lucas, genocchi, tribonacci

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Partition_(number_theory%29
    .. [2] https://en.wikipedia.org/wiki/Pentagonal_number_theorem

    """

    @staticmethod
    @recurrence_memo([1, 1])
    def _partition(n, prev):
        v, g, i = 0, 0, 0
        while 1:
            s = 0
            i += 1
            g = i * (3*i - 1) // 2
            if n >= g:
                s += prev[n - g]
            g = i * (3*i + 1) // 2
            if n >= g:
                s += prev[n - g]
            if s == 0:
                break
            else:
                v += s if i%2 == 1 else -s
        return v

    @classmethod
    def eval(cls, n):
        is_int = n.is_integer
        if is_int == False:
            raise ValueError("Partition numbers are defined only for "
                             "integers")
        elif is_int:
            if n.is_negative:
                return S.Zero

            if n.is_zero or (n - 1).is_zero:
                return S.One

            if n.is_Integer:
                return Integer(cls._partition(n))


    def _eval_is_integer(self):
        if self.args[0].is_integer:
            return True

    def _eval_is_negative(self):
        if self.args[0].is_integer:
            return False

    def _eval_is_positive(self):
        n = self.args[0]
        if n.is_nonnegative and n.is_integer:
            return True


#######################################################################
###
### Functions for enumerating partitions, permutations and combinations
###
#######################################################################


class _MultisetHistogram(tuple):
    pass


_N = -1
_ITEMS = -2
_M = slice(None, _ITEMS)


def _multiset_histogram(n):
    """Return tuple used in permutation and combination counting. Input
    is a dictionary giving items with counts as values or a sequence of
    items (which need not be sorted).

    The data is stored in a class deriving from tuple so it is easily
    recognized and so it can be converted easily to a list.
    """
    if isinstance(n, dict):  # item: count
        if not all(isinstance(v, int) and v >= 0 for v in n.values()):
            raise ValueError
        tot = sum(n.values())
        items = sum(1 for k in n if n[k] > 0)
        return _MultisetHistogram([n[k] for k in n if n[k] > 0] + [items, tot])
    else:
        n = list(n)
        s = set(n)
        if len(s) == len(n):
            n = [1]*len(n)
            n.extend([len(n), len(n)])
            return _MultisetHistogram(n)
        m = dict(zip(s, range(len(s))))
        d = dict(zip(range(len(s)), [0]*len(s)))
        for i in n:
            d[m[i]] += 1
        return _multiset_histogram(d)


def nP(n, k=None, replacement=False):
    """Return the number of permutations of ``n`` items taken ``k`` at a time.

    Possible values for ``n``::
        integer - set of length ``n``
        sequence - converted to a multiset internally
        multiset - {element: multiplicity}

    If ``k`` is None then the total of all permutations of length 0
    through the number of items represented by ``n`` will be returned.

    If ``replacement`` is True then a given item can appear more than once
    in the ``k`` items. (For example, for 'ab' permutations of 2 would
    include 'aa', 'ab', 'ba' and 'bb'.) The multiplicity of elements in
    ``n`` is ignored when ``replacement`` is True but the total number
    of elements is considered since no element can appear more times than
    the number of elements in ``n``.

    Examples
    ========

    >>> from sympy.functions.combinatorial.numbers import nP
    >>> from sympy.utilities.iterables import multiset_permutations, multiset
    >>> nP(3, 2)
    6
    >>> nP('abc', 2) == nP(multiset('abc'), 2) == 6
    True
    >>> nP('aab', 2)
    3
    >>> nP([1, 2, 2], 2)
    3
    >>> [nP(3, i) for i in range(4)]
    [1, 3, 6, 6]
    >>> nP(3) == sum(_)
    True

    When ``replacement`` is True, each item can have multiplicity
    equal to the length represented by ``n``:

    >>> nP('aabc', replacement=True)
    121
    >>> [len(list(multiset_permutations('aaaabbbbcccc', i))) for i in range(5)]
    [1, 3, 9, 27, 81]
    >>> sum(_)
    121

    See Also
    ========
    sympy.utilities.iterables.multiset_permutations

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Permutation

    """
    try:
        n = as_int(n)
    except ValueError:
        return Integer(_nP(_multiset_histogram(n), k, replacement))
    return Integer(_nP(n, k, replacement))


@cacheit
def _nP(n, k=None, replacement=False):
    from sympy.functions.combinatorial.factorials import factorial
    from sympy.core.mul import prod

    if k == 0:
        return 1
    if isinstance(n, SYMPY_INTS):  # n different items
        # assert n >= 0
        if k is None:
            return sum(_nP(n, i, replacement) for i in range(n + 1))
        elif replacement:
            return n**k
        elif k > n:
            return 0
        elif k == n:
            return factorial(k)
        elif k == 1:
            return n
        else:
            # assert k >= 0
            return _product(n - k + 1, n)
    elif isinstance(n, _MultisetHistogram):
        if k is None:
            return sum(_nP(n, i, replacement) for i in range(n[_N] + 1))
        elif replacement:
            return n[_ITEMS]**k
        elif k == n[_N]:
            return factorial(k)/prod([factorial(i) for i in n[_M] if i > 1])
        elif k > n[_N]:
            return 0
        elif k == 1:
            return n[_ITEMS]
        else:
            # assert k >= 0
            tot = 0
            n = list(n)
            for i in range(len(n[_M])):
                if not n[i]:
                    continue
                n[_N] -= 1
                if n[i] == 1:
                    n[i] = 0
                    n[_ITEMS] -= 1
                    tot += _nP(_MultisetHistogram(n), k - 1)
                    n[_ITEMS] += 1
                    n[i] = 1
                else:
                    n[i] -= 1
                    tot += _nP(_MultisetHistogram(n), k - 1)
                    n[i] += 1
                n[_N] += 1
            return tot


@cacheit
def _AOP_product(n):
    """for n = (m1, m2, .., mk) return the coefficients of the polynomial,
    prod(sum(x**i for i in range(nj + 1)) for nj in n); i.e. the coefficients
    of the product of AOPs (all-one polynomials) or order given in n.  The
    resulting coefficient corresponding to x**r is the number of r-length
    combinations of sum(n) elements with multiplicities given in n.
    The coefficients are given as a default dictionary (so if a query is made
    for a key that is not present, 0 will be returned).

    Examples
    ========

    >>> from sympy.functions.combinatorial.numbers import _AOP_product
    >>> from sympy.abc import x
    >>> n = (2, 2, 3)  # e.g. aabbccc
    >>> prod = ((x**2 + x + 1)*(x**2 + x + 1)*(x**3 + x**2 + x + 1)).expand()
    >>> c = _AOP_product(n); dict(c)
    {0: 1, 1: 3, 2: 6, 3: 8, 4: 8, 5: 6, 6: 3, 7: 1}
    >>> [c[i] for i in range(8)] == [prod.coeff(x, i) for i in range(8)]
    True

    The generating poly used here is the same as that listed in
    http://tinyurl.com/cep849r, but in a refactored form.

    """
    from collections import defaultdict

    n = list(n)
    ord = sum(n)
    need = (ord + 2)//2
    rv = [1]*(n.pop() + 1)
    rv.extend([0]*(need - len(rv)))
    rv = rv[:need]
    while n:
        ni = n.pop()
        N = ni + 1
        was = rv[:]
        for i in range(1, min(N, len(rv))):
            rv[i] += rv[i - 1]
        for i in range(N, need):
            rv[i] += rv[i - 1] - was[i - N]
    rev = list(reversed(rv))
    if ord % 2:
        rv = rv + rev
    else:
        rv[-1:] = rev
    d = defaultdict(int)
    for i in range(len(rv)):
        d[i] = rv[i]
    return d


def nC(n, k=None, replacement=False):
    """Return the number of combinations of ``n`` items taken ``k`` at a time.

    Possible values for ``n``::
        integer - set of length ``n``
        sequence - converted to a multiset internally
        multiset - {element: multiplicity}

    If ``k`` is None then the total of all combinations of length 0
    through the number of items represented in ``n`` will be returned.

    If ``replacement`` is True then a given item can appear more than once
    in the ``k`` items. (For example, for 'ab' sets of 2 would include 'aa',
    'ab', and 'bb'.) The multiplicity of elements in ``n`` is ignored when
    ``replacement`` is True but the total number of elements is considered
    since no element can appear more times than the number of elements in
    ``n``.

    Examples
    ========

    >>> from sympy.functions.combinatorial.numbers import nC
    >>> from sympy.utilities.iterables import multiset_combinations
    >>> nC(3, 2)
    3
    >>> nC('abc', 2)
    3
    >>> nC('aab', 2)
    2

    When ``replacement`` is True, each item can have multiplicity
    equal to the length represented by ``n``:

    >>> nC('aabc', replacement=True)
    35
    >>> [len(list(multiset_combinations('aaaabbbbcccc', i))) for i in range(5)]
    [1, 3, 6, 10, 15]
    >>> sum(_)
    35

    If there are ``k`` items with multiplicities ``m_1, m_2, ..., m_k``
    then the total of all combinations of length 0 through ``k`` is the
    product, ``(m_1 + 1)*(m_2 + 1)*...*(m_k + 1)``. When the multiplicity
    of each item is 1 (i.e., k unique items) then there are 2**k
    combinations. For example, if there are 4 unique items, the total number
    of combinations is 16:

    >>> sum(nC(4, i) for i in range(5))
    16

    See Also
    ========

    sympy.utilities.iterables.multiset_combinations

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Combination
    .. [2] http://tinyurl.com/cep849r

    """
    from sympy.functions.combinatorial.factorials import binomial
    from sympy.core.mul import prod

    if isinstance(n, SYMPY_INTS):
        if k is None:
            if not replacement:
                return 2**n
            return sum(nC(n, i, replacement) for i in range(n + 1))
        if k < 0:
            raise ValueError("k cannot be negative")
        if replacement:
            return binomial(n + k - 1, k)
        return binomial(n, k)
    if isinstance(n, _MultisetHistogram):
        N = n[_N]
        if k is None:
            if not replacement:
                return prod(m + 1 for m in n[_M])
            return sum(nC(n, i, replacement) for i in range(N + 1))
        elif replacement:
            return nC(n[_ITEMS], k, replacement)
        # assert k >= 0
        elif k in (1, N - 1):
            return n[_ITEMS]
        elif k in (0, N):
            return 1
        return _AOP_product(tuple(n[_M]))[k]
    else:
        return nC(_multiset_histogram(n), k, replacement)


@cacheit
def _stirling1(n, k):
    if n == k == 0:
        return S.One
    if 0 in (n, k):
        return S.Zero
    n1 = n - 1

    # some special values
    if n == k:
        return S.One
    elif k == 1:
        return factorial(n1)
    elif k == n1:
        return binomial(n, 2)
    elif k == n - 2:
        return (3*n - 1)*binomial(n, 3)/4
    elif k == n - 3:
        return binomial(n, 2)*binomial(n, 4)

    # general recurrence
    return n1*_stirling1(n1, k) + _stirling1(n1, k - 1)


@cacheit
def _stirling2(n, k):
    if n == k == 0:
        return S.One
    if 0 in (n, k):
        return S.Zero
    n1 = n - 1

    # some special values
    if k == n1:
        return binomial(n, 2)
    elif k == 2:
        return 2**n1 - 1

    # general recurrence
    return k*_stirling2(n1, k) + _stirling2(n1, k - 1)


def stirling(n, k, d=None, kind=2, signed=False):
    r"""Return Stirling number `S(n, k)` of the first or second (default) kind.

    The sum of all Stirling numbers of the second kind for `k = 1`
    through `n` is ``bell(n)``. The recurrence relationship for these numbers
    is:

    .. math :: {0 \brace 0} = 1; {n \brace 0} = {0 \brace k} = 0;

    .. math :: {{n+1} \brace k} = j {n \brace k} + {n \brace {k-1}}

    where `j` is:
        `n` for Stirling numbers of the first kind
        `-n` for signed Stirling numbers of the first kind
        `k` for Stirling numbers of the second kind

    The first kind of Stirling number counts the number of permutations of
    ``n`` distinct items that have ``k`` cycles; the second kind counts the
    ways in which ``n`` distinct items can be partitioned into ``k`` parts.
    If ``d`` is given, the "reduced Stirling number of the second kind" is
    returned: ``S^{d}(n, k) = S(n - d + 1, k - d + 1)`` with ``n >= k >= d``.
    (This counts the ways to partition ``n`` consecutive integers into
    ``k`` groups with no pairwise difference less than ``d``. See example
    below.)

    To obtain the signed Stirling numbers of the first kind, use keyword
    ``signed=True``. Using this keyword automatically sets ``kind`` to 1.

    Examples
    ========

    >>> from sympy.functions.combinatorial.numbers import stirling, bell
    >>> from sympy.combinatorics import Permutation
    >>> from sympy.utilities.iterables import multiset_partitions, permutations

    First kind (unsigned by default):

    >>> [stirling(6, i, kind=1) for i in range(7)]
    [0, 120, 274, 225, 85, 15, 1]
    >>> perms = list(permutations(range(4)))
    >>> [sum(Permutation(p).cycles == i for p in perms) for i in range(5)]
    [0, 6, 11, 6, 1]
    >>> [stirling(4, i, kind=1) for i in range(5)]
    [0, 6, 11, 6, 1]

    First kind (signed):

    >>> [stirling(4, i, signed=True) for i in range(5)]
    [0, -6, 11, -6, 1]

    Second kind:

    >>> [stirling(10, i) for i in range(12)]
    [0, 1, 511, 9330, 34105, 42525, 22827, 5880, 750, 45, 1, 0]
    >>> sum(_) == bell(10)
    True
    >>> len(list(multiset_partitions(range(4), 2))) == stirling(4, 2)
    True

    Reduced second kind:

    >>> from sympy import subsets, oo
    >>> def delta(p):
    ...    if len(p) == 1:
    ...        return oo
    ...    return min(abs(i[0] - i[1]) for i in subsets(p, 2))
    >>> parts = multiset_partitions(range(5), 3)
    >>> d = 2
    >>> sum(1 for p in parts if all(delta(i) >= d for i in p))
    7
    >>> stirling(5, 3, 2)
    7

    See Also
    ========
    sympy.utilities.iterables.multiset_partitions


    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Stirling_numbers_of_the_first_kind
    .. [2] https://en.wikipedia.org/wiki/Stirling_numbers_of_the_second_kind

    """
    # TODO: make this a class like bell()

    n = as_int(n)
    k = as_int(k)
    if n < 0:
        raise ValueError('n must be nonnegative')
    if k > n:
        return S.Zero
    if d:
        # assert k >= d
        # kind is ignored -- only kind=2 is supported
        return _stirling2(n - d + 1, k - d + 1)
    elif signed:
        # kind is ignored -- only kind=1 is supported
        return (-1)**(n - k)*_stirling1(n, k)

    if kind == 1:
        return _stirling1(n, k)
    elif kind == 2:
        return _stirling2(n, k)
    else:
        raise ValueError('kind must be 1 or 2, not %s' % k)


@cacheit
def _nT(n, k):
    """Return the partitions of ``n`` items into ``k`` parts. This
    is used by ``nT`` for the case when ``n`` is an integer."""
    if k == 0:
        return 1 if k == n else 0
    return sum(_nT(n - k, j) for j in range(min(k, n - k) + 1))


def nT(n, k=None):
    """Return the number of ``k``-sized partitions of ``n`` items.

    Possible values for ``n``::
        integer - ``n`` identical items
        sequence - converted to a multiset internally
        multiset - {element: multiplicity}

    Note: the convention for ``nT`` is different than that of ``nC`` and
    ``nP`` in that
    here an integer indicates ``n`` *identical* items instead of a set of
    length ``n``; this is in keeping with the ``partitions`` function which
    treats its integer-``n`` input like a list of ``n`` 1s. One can use
    ``range(n)`` for ``n`` to indicate ``n`` distinct items.

    If ``k`` is None then the total number of ways to partition the elements
    represented in ``n`` will be returned.

    Examples
    ========

    >>> from sympy.functions.combinatorial.numbers import nT

    Partitions of the given multiset:

    >>> [nT('aabbc', i) for i in range(1, 7)]
    [1, 8, 11, 5, 1, 0]
    >>> nT('aabbc') == sum(_)
    True

    >>> [nT("mississippi", i) for i in range(1, 12)]
    [1, 74, 609, 1521, 1768, 1224, 579, 197, 50, 9, 1]

    Partitions when all items are identical:

    >>> [nT(5, i) for i in range(1, 6)]
    [1, 2, 2, 1, 1]
    >>> nT('1'*5) == sum(_)
    True

    When all items are different:

    >>> [nT(range(5), i) for i in range(1, 6)]
    [1, 15, 25, 10, 1]
    >>> nT(range(5)) == sum(_)
    True

    Partitions of an integer expressed as a sum of positive integers:

    >>> from sympy.functions.combinatorial.numbers import partition
    >>> partition(4)
    5
    >>> sum([nT(4, i) for i in range(4 + 1)])
    5
    >>> nT('1'*4)
    5

    See Also
    ========
    sympy.utilities.iterables.partitions
    sympy.utilities.iterables.multiset_partitions
    sympy.functions.combinatorial.numbers.partition

    References
    ==========

    .. [1] http://undergraduate.csse.uwa.edu.au/units/CITS7209/partition.pdf

    """
    from sympy.utilities.enumerative import MultisetPartitionTraverser

    if isinstance(n, SYMPY_INTS):
        # assert n >= 0
        # all the same
        if k is None:
            return partition(n)
        elif n == 0:
            return S.One if k == 0 else S.Zero
        return _nT(n, k)
    if not isinstance(n, _MultisetHistogram):
        try:
            # if n contains hashable items there is some
            # quick handling that can be done
            u = len(set(n))
            if u <= 1:
                return nT(len(n), k)
            elif u == len(n):
                n = range(u)
            raise TypeError
        except TypeError:
            n = _multiset_histogram(n)
    N = n[_N]
    if k is None and N == 1:
        return 1
    if k in (1, N):
        return 1
    if k == 2 or N == 2 and k is None:
        m, r = divmod(N, 2)
        rv = sum(nC(n, i) for i in range(1, m + 1))
        if not r:
            rv -= nC(n, m)//2
        if k is None:
            rv += 1  # for k == 1
        return rv
    if N == n[_ITEMS]:
        # all distinct
        if k is None:
            return bell(N)
        return stirling(N, k)
    m = MultisetPartitionTraverser()
    if k is None:
        return m.count_partitions(n[_M])
    # MultisetPartitionTraverser does not have a range-limited count
    # method, so need to enumerate and count
    tot = 0
    for discard in m.enum_range(n[_M], k-1, k):
        tot += 1
    return tot
