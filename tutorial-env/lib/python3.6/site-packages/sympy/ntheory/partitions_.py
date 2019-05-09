from __future__ import print_function, division
from mpmath.libmp import (fzero,
    from_man_exp, from_int, from_rational,
    fone, fhalf, bitcount, to_int, to_str, mpf_mul, mpf_div, mpf_sub,
    mpf_add, mpf_sqrt, mpf_pi, mpf_cosh_sinh, pi_fixed, mpf_cos,
    mpf_sin)
from sympy.core.numbers import igcd
from sympy.core.compatibility import range
from .residue_ntheory import (_sqrt_mod_prime_power,
    legendre_symbol, jacobi_symbol, is_quad_residue)

import math

def _pre():
    maxn = 10**5
    global _factor
    global _totient
    _factor = [0]*maxn
    _totient = [1]*maxn
    lim = int(maxn**0.5) + 5
    for i in range(2, lim):
        if _factor[i] == 0:
            for j in range(i*i, maxn, i):
                if _factor[j] == 0:
                    _factor[j] = i
    for i in range(2, maxn):
        if _factor[i] == 0:
            _factor[i] = i
            _totient[i] = i-1
            continue
        x = _factor[i]
        y = i//x
        if y % x == 0:
            _totient[i] = _totient[y]*x
        else:
            _totient[i] = _totient[y]*(x - 1)

def _a(n, k, prec):
    """ Compute the inner sum in HRR formula [1]_

    References
    ==========

    .. [1] http://msp.org/pjm/1956/6-1/pjm-v6-n1-p18-p.pdf

    """
    if k == 1:
        return fone

    k1 = k
    e = 0
    p = _factor[k]
    while k1 % p == 0:
        k1 //= p
        e += 1
    k2 = k//k1 # k2 = p^e
    v = 1 - 24*n
    pi = mpf_pi(prec)

    if k1 == 1:
        # k  = p^e
        if p == 2:
            mod = 8*k
            v = mod + v % mod
            v = (v*pow(9, k - 1, mod)) % mod
            m = _sqrt_mod_prime_power(v, 2, e + 3)[0]
            arg = mpf_div(mpf_mul(
                from_int(4*m), pi, prec), from_int(mod), prec)
            return mpf_mul(mpf_mul(
                from_int((-1)**e*jacobi_symbol(m - 1, m)),
                mpf_sqrt(from_int(k), prec), prec),
                mpf_sin(arg, prec), prec)
        if p == 3:
            mod = 3*k
            v = mod + v % mod
            if e > 1:
                v = (v*pow(64, k//3 - 1, mod)) % mod
            m = _sqrt_mod_prime_power(v, 3, e + 1)[0]
            arg = mpf_div(mpf_mul(from_int(4*m), pi, prec),
                from_int(mod), prec)
            return mpf_mul(mpf_mul(
                from_int(2*(-1)**(e + 1)*legendre_symbol(m, 3)),
                mpf_sqrt(from_int(k//3), prec), prec),
                mpf_sin(arg, prec), prec)
        v = k + v % k
        if v % p == 0:
            if e == 1:
                return mpf_mul(
                    from_int(jacobi_symbol(3, k)),
                    mpf_sqrt(from_int(k), prec), prec)
            return fzero
        if not is_quad_residue(v, p):
            return fzero
        _phi = p**(e - 1)*(p - 1)
        v = (v*pow(576, _phi - 1, k))
        m = _sqrt_mod_prime_power(v, p, e)[0]
        arg = mpf_div(
            mpf_mul(from_int(4*m), pi, prec),
            from_int(k), prec)
        return mpf_mul(mpf_mul(
            from_int(2*jacobi_symbol(3, k)),
            mpf_sqrt(from_int(k), prec), prec),
            mpf_cos(arg, prec), prec)

    if p != 2 or e >= 3:
        d1, d2 = igcd(k1, 24), igcd(k2, 24)
        e = 24//(d1*d2)
        n1 = ((d2*e*n + (k2**2 - 1)//d1)*
            pow(e*k2*k2*d2, _totient[k1] - 1, k1)) % k1
        n2 = ((d1*e*n + (k1**2 - 1)//d2)*
            pow(e*k1*k1*d1, _totient[k2] - 1, k2)) % k2
        return mpf_mul(_a(n1, k1, prec), _a(n2, k2, prec), prec)
    if e == 2:
        n1 = ((8*n + 5)*pow(128, _totient[k1] - 1, k1)) % k1
        n2 = (4 + ((n - 2 - (k1**2 - 1)//8)*(k1**2)) % 4) % 4
        return mpf_mul(mpf_mul(
            from_int(-1),
            _a(n1, k1, prec), prec),
            _a(n2, k2, prec))
    n1 = ((8*n + 1)*pow(32, _totient[k1] - 1, k1)) % k1
    n2 = (2 + (n - (k1**2 - 1)//8) % 2) % 2
    return mpf_mul(_a(n1, k1, prec), _a(n2, k2, prec), prec)

def _d(n, j, prec, sq23pi, sqrt8):
    """
    Compute the sinh term in the outer sum of the HRR formula.
    The constants sqrt(2/3*pi) and sqrt(8) must be precomputed.
    """
    j = from_int(j)
    pi = mpf_pi(prec)
    a = mpf_div(sq23pi, j, prec)
    b = mpf_sub(from_int(n), from_rational(1, 24, prec), prec)
    c = mpf_sqrt(b, prec)
    ch, sh = mpf_cosh_sinh(mpf_mul(a, c), prec)
    D = mpf_div(
        mpf_sqrt(j, prec),
        mpf_mul(mpf_mul(sqrt8, b), pi), prec)
    E = mpf_sub(mpf_mul(a, ch), mpf_div(sh, c, prec), prec)
    return mpf_mul(D, E)


def npartitions(n, verbose=False):
    """
    Calculate the partition function P(n), i.e. the number of ways that
    n can be written as a sum of positive integers.

    P(n) is computed using the Hardy-Ramanujan-Rademacher formula [1]_.


    The correctness of this implementation has been tested through 10**10.

    Examples
    ========

    >>> from sympy.ntheory import npartitions
    >>> npartitions(25)
    1958

    References
    ==========

    .. [1] http://mathworld.wolfram.com/PartitionFunctionP.html

    """
    n = int(n)
    if n < 0:
        return 0
    if n <= 5:
        return [1, 1, 2, 3, 5, 7][n]
    if '_factor' not in globals():
        _pre()
    # Estimate number of bits in p(n). This formula could be tidied
    pbits = int((
        math.pi*(2*n/3.)**0.5 -
        math.log(4*n))/math.log(10) + 1) * \
        math.log(10, 2)
    prec = p = int(pbits*1.1 + 100)
    s = fzero
    M = max(6, int(0.24*n**0.5 + 4))
    if M > 10**5:
        raise ValueError("Input too big") # Corresponds to n > 1.7e11
    sq23pi = mpf_mul(mpf_sqrt(from_rational(2, 3, p), p), mpf_pi(p), p)
    sqrt8 = mpf_sqrt(from_int(8), p)
    for q in range(1, M):
        a = _a(n, q, p)
        d = _d(n, q, p, sq23pi, sqrt8)
        s = mpf_add(s, mpf_mul(a, d), prec)
        if verbose:
            print("step", q, "of", M, to_str(a, 10), to_str(d, 10))
        # On average, the terms decrease rapidly in magnitude.
        # Dynamically reducing the precision greatly improves
        # performance.
        p = bitcount(abs(to_int(d))) + 50
    return int(to_int(mpf_add(s, fhalf, prec)))

__all__ = ['npartitions']
