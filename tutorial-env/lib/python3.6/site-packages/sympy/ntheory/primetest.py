"""
Primality testing

"""

from __future__ import print_function, division

from sympy.core.compatibility import range, as_int

from mpmath.libmp import bitcount as _bitlength


def _int_tuple(*i):
    return tuple(int(_) for _ in i)


def is_euler_pseudoprime(n, b):
    """Returns True if n is prime or an Euler pseudoprime to base b, else False.

    Euler Pseudoprime : In arithmetic, an odd composite integer n is called an
    euler pseudoprime to base a, if a and n are coprime and satisfy the modular
    arithmetic congruence relation :

    a ^ (n-1)/2 = + 1(mod n) or
    a ^ (n-1)/2 = - 1(mod n)

    (where mod refers to the modulo operation).

    Examples
    ========

    >>> from sympy.ntheory.primetest import is_euler_pseudoprime
    >>> is_euler_pseudoprime(2, 5)
    True

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Euler_pseudoprime
    """
    from sympy.ntheory.factor_ import trailing

    if not mr(n, [b]):
        return False

    n = as_int(n)
    r = n - 1
    c = pow(b, r >> trailing(r), n)

    if c == 1:
        return True

    while True:
        if c == n - 1:
            return True
        c = pow(c, 2, n)
        if c == 1:
            return False


def is_square(n, prep=True):
    """Return True if n == a * a for some integer a, else False.
    If n is suspected of *not* being a square then this is a
    quick method of confirming that it is not.

    References
    ==========

    [1]  http://mersenneforum.org/showpost.php?p=110896

    See Also
    ========
    sympy.core.power.integer_nthroot
    """
    if prep:
        n = as_int(n)
        if n < 0:
            return False
        if n in [0, 1]:
            return True
    m = n & 127
    if not ((m*0x8bc40d7d) & (m*0xa1e2f5d1) & 0x14020a):
        m = n % 63
        if not ((m*0x3d491df7) & (m*0xc824a9f9) & 0x10f14008):
            from sympy.ntheory import perfect_power
            if perfect_power(n, [2]):
                return True
    return False


def _test(n, base, s, t):
    """Miller-Rabin strong pseudoprime test for one base.
    Return False if n is definitely composite, True if n is
    probably prime, with a probability greater than 3/4.

    """
    # do the Fermat test
    b = pow(base, t, n)
    if b == 1 or b == n - 1:
        return True
    else:
        for j in range(1, s):
            b = pow(b, 2, n)
            if b == n - 1:
                return True
            # see I. Niven et al. "An Introduction to Theory of Numbers", page 78
            if b == 1:
                return False
    return False


def mr(n, bases):
    """Perform a Miller-Rabin strong pseudoprime test on n using a
    given list of bases/witnesses.

    References
    ==========

    - Richard Crandall & Carl Pomerance (2005), "Prime Numbers:
      A Computational Perspective", Springer, 2nd edition, 135-138

    A list of thresholds and the bases they require are here:
    https://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test#Deterministic_variants_of_the_test

    Examples
    ========

    >>> from sympy.ntheory.primetest import mr
    >>> mr(1373651, [2, 3])
    False
    >>> mr(479001599, [31, 73])
    True

    """
    from sympy.ntheory.factor_ import trailing
    from sympy.polys.domains import ZZ

    n = as_int(n)
    if n < 2:
        return False
    # remove powers of 2 from n-1 (= t * 2**s)
    s = trailing(n - 1)
    t = n >> s
    for base in bases:
        # Bases >= n are wrapped, bases < 2 are invalid
        if base >= n:
            base %= n
        if base >= 2:
            base = ZZ(base)
            if not _test(n, base, s, t):
                return False
    return True


def _lucas_sequence(n, P, Q, k):
    """Return the modular Lucas sequence (U_k, V_k, Q_k).

    Given a Lucas sequence defined by P, Q, returns the kth values for
    U and V, along with Q^k, all modulo n.  This is intended for use with
    possibly very large values of n and k, where the combinatorial functions
    would be completely unusable.

    The modular Lucas sequences are used in numerous places in number theory,
    especially in the Lucas compositeness tests and the various n + 1 proofs.

    Examples
    ========

    >>> from sympy.ntheory.primetest import _lucas_sequence
    >>> N = 10**2000 + 4561
    >>> sol = U, V, Qk = _lucas_sequence(N, 3, 1, N//2); sol
    (0, 2, 1)

    """
    D = P*P - 4*Q
    if n < 2:
        raise ValueError("n must be >= 2")
    if k < 0:
        raise ValueError("k must be >= 0")
    if D == 0:
        raise ValueError("D must not be zero")

    if k == 0:
        return _int_tuple(0, 2, Q)
    U = 1
    V = P
    Qk = Q
    b = _bitlength(k)
    if Q == 1:
        # Optimization for extra strong tests.
        while b > 1:
            U = (U*V) % n
            V = (V*V - 2) % n
            b -= 1
            if (k >> (b - 1)) & 1:
                U, V = U*P + V, V*P + U*D
                if U & 1:
                    U += n
                if V & 1:
                    V += n
                U, V = U >> 1, V >> 1
    elif P == 1 and Q == -1:
        # Small optimization for 50% of Selfridge parameters.
        while b > 1:
            U = (U*V) % n
            if Qk == 1:
                V = (V*V - 2) % n
            else:
                V = (V*V + 2) % n
                Qk = 1
            b -= 1
            if (k >> (b-1)) & 1:
                U, V = U + V, V + U*D
                if U & 1:
                    U += n
                if V & 1:
                    V += n
                U, V = U >> 1, V >> 1
                Qk = -1
    else:
        # The general case with any P and Q.
        while b > 1:
            U = (U*V) % n
            V = (V*V - 2*Qk) % n
            Qk *= Qk
            b -= 1
            if (k >> (b - 1)) & 1:
                U, V = U*P + V, V*P + U*D
                if U & 1:
                    U += n
                if V & 1:
                    V += n
                U, V = U >> 1, V >> 1
                Qk *= Q
            Qk %= n
    return _int_tuple(U % n, V % n, Qk)


def _lucas_selfridge_params(n):
    """Calculates the Selfridge parameters (D, P, Q) for n.  This is
       method A from page 1401 of Baillie and Wagstaff.

    References
    ==========
    - "Lucas Pseudoprimes", Baillie and Wagstaff, 1980.
      http://mpqs.free.fr/LucasPseudoprimes.pdf
    """
    from sympy.core import igcd
    from sympy.ntheory.residue_ntheory import jacobi_symbol
    D = 5
    while True:
        g = igcd(abs(D), n)
        if g > 1 and g != n:
            return (0, 0, 0)
        if jacobi_symbol(D, n) == -1:
            break
        if D > 0:
          D = -D - 2
        else:
          D = -D + 2
    return _int_tuple(D, 1, (1 - D)/4)


def _lucas_extrastrong_params(n):
    """Calculates the "extra strong" parameters (D, P, Q) for n.

    References
    ==========
    - OEIS A217719: Extra Strong Lucas Pseudoprimes
      https://oeis.org/A217719
    - https://en.wikipedia.org/wiki/Lucas_pseudoprime
    """
    from sympy.core import igcd
    from sympy.ntheory.residue_ntheory import jacobi_symbol
    P, Q, D = 3, 1, 5
    while True:
        g = igcd(D, n)
        if g > 1 and g != n:
            return (0, 0, 0)
        if jacobi_symbol(D, n) == -1:
            break
        P += 1
        D = P*P - 4
    return _int_tuple(D, P, Q)


def is_lucas_prp(n):
    """Standard Lucas compositeness test with Selfridge parameters.  Returns
    False if n is definitely composite, and True if n is a Lucas probable
    prime.

    This is typically used in combination with the Miller-Rabin test.

    References
    ==========
    - "Lucas Pseudoprimes", Baillie and Wagstaff, 1980.
      http://mpqs.free.fr/LucasPseudoprimes.pdf
    - OEIS A217120: Lucas Pseudoprimes
      https://oeis.org/A217120
    - https://en.wikipedia.org/wiki/Lucas_pseudoprime

    Examples
    ========

    >>> from sympy.ntheory.primetest import isprime, is_lucas_prp
    >>> for i in range(10000):
    ...     if is_lucas_prp(i) and not isprime(i):
    ...        print(i)
    323
    377
    1159
    1829
    3827
    5459
    5777
    9071
    9179
    """
    n = as_int(n)
    if n == 2:
        return True
    if n < 2 or (n % 2) == 0:
        return False
    if is_square(n, False):
        return False

    D, P, Q = _lucas_selfridge_params(n)
    if D == 0:
        return False
    U, V, Qk = _lucas_sequence(n, P, Q, n+1)
    return U == 0


def is_strong_lucas_prp(n):
    """Strong Lucas compositeness test with Selfridge parameters.  Returns
    False if n is definitely composite, and True if n is a strong Lucas
    probable prime.

    This is often used in combination with the Miller-Rabin test, and
    in particular, when combined with M-R base 2 creates the strong BPSW test.

    References
    ==========
    - "Lucas Pseudoprimes", Baillie and Wagstaff, 1980.
      http://mpqs.free.fr/LucasPseudoprimes.pdf
    - OEIS A217255: Strong Lucas Pseudoprimes
      https://oeis.org/A217255
    - https://en.wikipedia.org/wiki/Lucas_pseudoprime
    - https://en.wikipedia.org/wiki/Baillie-PSW_primality_test

    Examples
    ========

    >>> from sympy.ntheory.primetest import isprime, is_strong_lucas_prp
    >>> for i in range(20000):
    ...     if is_strong_lucas_prp(i) and not isprime(i):
    ...        print(i)
    5459
    5777
    10877
    16109
    18971
    """
    from sympy.ntheory.factor_ import trailing
    n = as_int(n)
    if n == 2:
        return True
    if n < 2 or (n % 2) == 0:
        return False
    if is_square(n, False):
        return False

    D, P, Q = _lucas_selfridge_params(n)
    if D == 0:
        return False

    # remove powers of 2 from n+1 (= k * 2**s)
    s = trailing(n + 1)
    k = (n+1) >> s

    U, V, Qk = _lucas_sequence(n, P, Q, k)

    if U == 0 or V == 0:
        return True
    for r in range(1, s):
        V = (V*V - 2*Qk) % n
        if V == 0:
            return True
        Qk = pow(Qk, 2, n)
    return False


def is_extra_strong_lucas_prp(n):
    """Extra Strong Lucas compositeness test.  Returns False if n is
    definitely composite, and True if n is a "extra strong" Lucas probable
    prime.

    The parameters are selected using P = 3, Q = 1, then incrementing P until
    (D|n) == -1.  The test itself is as defined in Grantham 2000, from the
    Mo and Jones preprint.  The parameter selection and test are the same as
    used in OEIS A217719, Perl's Math::Prime::Util, and the Lucas pseudoprime
    page on Wikipedia.

    With these parameters, there are no counterexamples below 2^64 nor any
    known above that range.  It is 20-50% faster than the strong test.

    Because of the different parameters selected, there is no relationship
    between the strong Lucas pseudoprimes and extra strong Lucas pseudoprimes.
    In particular, one is not a subset of the other.

    References
    ==========
    - "Frobenius Pseudoprimes", Jon Grantham, 2000.
      http://www.ams.org/journals/mcom/2001-70-234/S0025-5718-00-01197-2/
    - OEIS A217719: Extra Strong Lucas Pseudoprimes
      https://oeis.org/A217719
    - https://en.wikipedia.org/wiki/Lucas_pseudoprime

    Examples
    ========

    >>> from sympy.ntheory.primetest import isprime, is_extra_strong_lucas_prp
    >>> for i in range(20000):
    ...     if is_extra_strong_lucas_prp(i) and not isprime(i):
    ...        print(i)
    989
    3239
    5777
    10877
    """
    # Implementation notes:
    #   1) the parameters differ from Thomas R. Nicely's.  His parameter
    #      selection leads to pseudoprimes that overlap M-R tests, and
    #      contradict Baillie and Wagstaff's suggestion of (D|n) = -1.
    #   2) The MathWorld page as of June 2013 specifies Q=-1.  The Lucas
    #      sequence must have Q=1.  See Grantham theorem 2.3, any of the
    #      references on the MathWorld page, or run it and see Q=-1 is wrong.
    from sympy.ntheory.factor_ import trailing
    n = as_int(n)
    if n == 2:
        return True
    if n < 2 or (n % 2) == 0:
        return False
    if is_square(n, False):
        return False

    D, P, Q = _lucas_extrastrong_params(n)
    if D == 0:
        return False

    # remove powers of 2 from n+1 (= k * 2**s)
    s = trailing(n + 1)
    k = (n+1) >> s

    U, V, Qk = _lucas_sequence(n, P, Q, k)

    if U == 0 and (V == 2 or V == n - 2):
        return True
    if V == 0:
        return True
    for r in range(1, s):
        V = (V*V - 2) % n
        if V == 0:
            return True
    return False


def isprime(n):
    """
    Test if n is a prime number (True) or not (False). For n < 2^64 the
    answer is definitive; larger n values have a small probability of actually
    being pseudoprimes.

    Negative numbers (e.g. -2) are not considered prime.

    The first step is looking for trivial factors, which if found enables
    a quick return.  Next, if the sieve is large enough, use bisection search
    on the sieve.  For small numbers, a set of deterministic Miller-Rabin
    tests are performed with bases that are known to have no counterexamples
    in their range.  Finally if the number is larger than 2^64, a strong
    BPSW test is performed.  While this is a probable prime test and we
    believe counterexamples exist, there are no known counterexamples.

    Examples
    ========

    >>> from sympy.ntheory import isprime
    >>> isprime(13)
    True
    >>> isprime(13.0)  # limited precision
    False
    >>> isprime(15)
    False

    Notes
    =====

    This routine is intended only for integer input, not numerical
    expressions which may represent numbers. Floats are also
    rejected as input because they represent numbers of limited
    precision. While it is tempting to permit 7.0 to represent an
    integer there are errors that may "pass silently" if this is
    allowed:

    >>> from sympy import Float, S
    >>> int(1e3) == 1e3 == 10**3
    True
    >>> int(1e23) == 1e23
    True
    >>> int(1e23) == 10**23
    False

    >>> near_int = 1 + S(1)/10**19
    >>> near_int == int(near_int)
    False
    >>> n = Float(near_int, 10)  # truncated by precision
    >>> n == int(n)
    True
    >>> n = Float(near_int, 20)
    >>> n == int(n)
    False

    See Also
    ========

    sympy.ntheory.generate.primerange : Generates all primes in a given range
    sympy.ntheory.generate.primepi : Return the number of primes less than or equal to n
    sympy.ntheory.generate.prime : Return the nth prime

    References
    ==========
    - https://en.wikipedia.org/wiki/Strong_pseudoprime
    - "Lucas Pseudoprimes", Baillie and Wagstaff, 1980.
      http://mpqs.free.fr/LucasPseudoprimes.pdf
    - https://en.wikipedia.org/wiki/Baillie-PSW_primality_test
    """
    try:
        n = as_int(n)
    except ValueError:
        return False

    # Step 1, do quick composite testing via trial division.  The individual
    # modulo tests benchmark faster than one or two primorial igcds for me.
    # The point here is just to speedily handle small numbers and many
    # composites.  Step 2 only requires that n <= 2 get handled here.
    if n in [2, 3, 5]:
        return True
    if n < 2 or (n % 2) == 0 or (n % 3) == 0 or (n % 5) == 0:
        return False
    if n < 49:
        return True
    if (n %  7) == 0 or (n % 11) == 0 or (n % 13) == 0 or (n % 17) == 0 or \
       (n % 19) == 0 or (n % 23) == 0 or (n % 29) == 0 or (n % 31) == 0 or \
       (n % 37) == 0 or (n % 41) == 0 or (n % 43) == 0 or (n % 47) == 0:
        return False
    if n < 2809:
        return True
    if n <= 23001:
        return pow(2, n, n) == 2 and n not in [7957, 8321, 13747, 18721, 19951]

    # bisection search on the sieve if the sieve is large enough
    from sympy.ntheory.generate import sieve as s
    if n <= s._list[-1]:
        l, u = s.search(n)
        return l == u

    # If we have GMPY2, skip straight to step 3 and do a strong BPSW test.
    # This should be a bit faster than our step 2, and for large values will
    # be a lot faster than our step 3 (C+GMP vs. Python).
    from sympy.core.compatibility import HAS_GMPY
    if HAS_GMPY == 2:
        from gmpy2 import is_strong_prp, is_strong_selfridge_prp
        return is_strong_prp(n, 2) and is_strong_selfridge_prp(n)


    # Step 2: deterministic Miller-Rabin testing for numbers < 2^64.  See:
    #    https://miller-rabin.appspot.com/
    # for lists.  We have made sure the M-R routine will successfully handle
    # bases larger than n, so we can use the minimal set.
    if n < 341531:
        return mr(n, [9345883071009581737])
    if n < 885594169:
        return mr(n, [725270293939359937, 3569819667048198375])
    if n < 350269456337:
        return mr(n, [4230279247111683200, 14694767155120705706, 16641139526367750375])
    if n < 55245642489451:
        return mr(n, [2, 141889084524735, 1199124725622454117, 11096072698276303650])
    if n < 7999252175582851:
        return mr(n, [2, 4130806001517, 149795463772692060, 186635894390467037, 3967304179347715805])
    if n < 585226005592931977:
        return mr(n, [2, 123635709730000, 9233062284813009, 43835965440333360, 761179012939631437, 1263739024124850375])
    if n < 18446744073709551616:
        return mr(n, [2, 325, 9375, 28178, 450775, 9780504, 1795265022])

    # We could do this instead at any point:
    #if n < 18446744073709551616:
    #   return mr(n, [2]) and is_extra_strong_lucas_prp(n)

    # Here are tests that are safe for MR routines that don't understand
    # large bases.
    #if n < 9080191:
    #    return mr(n, [31, 73])
    #if n < 19471033:
    #    return mr(n, [2, 299417])
    #if n < 38010307:
    #    return mr(n, [2, 9332593])
    #if n < 316349281:
    #    return mr(n, [11000544, 31481107])
    #if n < 4759123141:
    #    return mr(n, [2, 7, 61])
    #if n < 105936894253:
    #    return mr(n, [2, 1005905886, 1340600841])
    #if n < 31858317218647:
    #    return mr(n, [2, 642735, 553174392, 3046413974])
    #if n < 3071837692357849:
    #    return mr(n, [2, 75088, 642735, 203659041, 3613982119])
    #if n < 18446744073709551616:
    #    return mr(n, [2, 325, 9375, 28178, 450775, 9780504, 1795265022])

    # Step 3: BPSW.
    #
    #  Time for isprime(10**2000 + 4561), no gmpy or gmpy2 installed
    #     44.0s   old isprime using 46 bases
    #      5.3s   strong BPSW + one random base
    #      4.3s   extra strong BPSW + one random base
    #      4.1s   strong BPSW
    #      3.2s   extra strong BPSW

    # Classic BPSW from page 1401 of the paper.  See alternate ideas below.
    return mr(n, [2]) and is_strong_lucas_prp(n)

    # Using extra strong test, which is somewhat faster
    #return mr(n, [2]) and is_extra_strong_lucas_prp(n)

    # Add a random M-R base
    #import random
    #return mr(n, [2, random.randint(3, n-1)]) and is_strong_lucas_prp(n)
