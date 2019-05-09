from sympy import (Sieve, binomial_coefficients, binomial_coefficients_list,
    Mul, S, Pow, sieve, Symbol, summation, Dummy,
    factorial as fac)
from sympy.core.evalf import bitcount
from sympy.core.numbers import Integer, Rational
from sympy.core.compatibility import long, range

from sympy.ntheory import (isprime, n_order, is_primitive_root,
    is_quad_residue, legendre_symbol, jacobi_symbol, npartitions, totient,
    factorint, primefactors, divisors, randprime, nextprime, prevprime,
    primerange, primepi, prime, pollard_rho, perfect_power, multiplicity,
    trailing, divisor_count, primorial, pollard_pm1, divisor_sigma,
    factorrat, reduced_totient)
from sympy.ntheory.factor_ import (smoothness, smoothness_p,
    antidivisors, antidivisor_count, core, digits, udivisors, udivisor_sigma,
    udivisor_count, primenu, primeomega, small_trailing, mersenne_prime_exponent,
    is_perfect, is_mersenne_prime, is_abundant, is_deficient, is_amicable)
from sympy.ntheory.generate import cycle_length
from sympy.ntheory.multinomial import (
    multinomial_coefficients, multinomial_coefficients_iterator)
from sympy.ntheory.bbp_pi import pi_hex_digits
from sympy.ntheory.modular import crt, crt1, crt2, solve_congruence

from sympy.utilities.pytest import raises, slow

from sympy.utilities.iterables import capture


def fac_multiplicity(n, p):
    """Return the power of the prime number p in the
    factorization of n!"""
    if p > n:
        return 0
    if p > n//2:
        return 1
    q, m = n, 0
    while q >= p:
        q //= p
        m += q
    return m


def multiproduct(seq=(), start=1):
    """
    Return the product of a sequence of factors with multiplicities,
    times the value of the parameter ``start``. The input may be a
    sequence of (factor, exponent) pairs or a dict of such pairs.

        >>> multiproduct({3:7, 2:5}, 4) # = 3**7 * 2**5 * 4
        279936

    """
    if not seq:
        return start
    if isinstance(seq, dict):
        seq = iter(seq.items())
    units = start
    multi = []
    for base, exp in seq:
        if not exp:
            continue
        elif exp == 1:
            units *= base
        else:
            if exp % 2:
                units *= base
            multi.append((base, exp//2))
    return units * multiproduct(multi)**2


def test_trailing_bitcount():
    assert trailing(0) == 0
    assert trailing(1) == 0
    assert trailing(-1) == 0
    assert trailing(2) == 1
    assert trailing(7) == 0
    assert trailing(-7) == 0
    for i in range(100):
        assert trailing((1 << i)) == i
        assert trailing((1 << i) * 31337) == i
    assert trailing((1 << 1000001)) == 1000001
    assert trailing((1 << 273956)*7**37) == 273956
    # issue 12709
    big = small_trailing[-1]*2
    assert trailing(-big) == trailing(big)
    assert bitcount(-big) == bitcount(big)


def test_multiplicity():
    for b in range(2, 20):
        for i in range(100):
            assert multiplicity(b, b**i) == i
            assert multiplicity(b, (b**i) * 23) == i
            assert multiplicity(b, (b**i) * 1000249) == i
    # Should be fast
    assert multiplicity(10, 10**10023) == 10023
    # Should exit quickly
    assert multiplicity(10**10, 10**10) == 1
    # Should raise errors for bad input
    raises(ValueError, lambda: multiplicity(1, 1))
    raises(ValueError, lambda: multiplicity(1, 2))
    raises(ValueError, lambda: multiplicity(1.3, 2))
    raises(ValueError, lambda: multiplicity(2, 0))
    raises(ValueError, lambda: multiplicity(1.3, 0))

    # handles Rationals
    assert multiplicity(10, Rational(30, 7)) == 1
    assert multiplicity(Rational(2, 7), Rational(4, 7)) == 1
    assert multiplicity(Rational(1, 7), Rational(3, 49)) == 2
    assert multiplicity(Rational(2, 7), Rational(7, 2)) == -1
    assert multiplicity(3, Rational(1, 9)) == -2


def test_perfect_power():
    assert perfect_power(0) is False
    assert perfect_power(1) is False
    assert perfect_power(2) is False
    assert perfect_power(3) is False
    assert perfect_power(4) == (2, 2)
    assert perfect_power(14) is False
    assert perfect_power(25) == (5, 2)
    assert perfect_power(22) is False
    assert perfect_power(22, [2]) is False
    assert perfect_power(137**(3*5*13)) == (137, 3*5*13)
    assert perfect_power(137**(3*5*13) + 1) is False
    assert perfect_power(137**(3*5*13) - 1) is False
    assert perfect_power(103005006004**7) == (103005006004, 7)
    assert perfect_power(103005006004**7 + 1) is False
    assert perfect_power(103005006004**7 - 1) is False
    assert perfect_power(103005006004**12) == (103005006004, 12)
    assert perfect_power(103005006004**12 + 1) is False
    assert perfect_power(103005006004**12 - 1) is False
    assert perfect_power(2**10007) == (2, 10007)
    assert perfect_power(2**10007 + 1) is False
    assert perfect_power(2**10007 - 1) is False
    assert perfect_power((9**99 + 1)**60) == (9**99 + 1, 60)
    assert perfect_power((9**99 + 1)**60 + 1) is False
    assert perfect_power((9**99 + 1)**60 - 1) is False
    assert perfect_power((10**40000)**2, big=False) == (10**40000, 2)
    assert perfect_power(10**100000) == (10, 100000)
    assert perfect_power(10**100001) == (10, 100001)
    assert perfect_power(13**4, [3, 5]) is False
    assert perfect_power(3**4, [3, 10], factor=0) is False
    assert perfect_power(3**3*5**3) == (15, 3)
    assert perfect_power(2**3*5**5) is False
    assert perfect_power(2*13**4) is False
    assert perfect_power(2**5*3**3) is False


def test_factorint():
    assert primefactors(123456) == [2, 3, 643]
    assert factorint(0) == {0: 1}
    assert factorint(1) == {}
    assert factorint(-1) == {-1: 1}
    assert factorint(-2) == {-1: 1, 2: 1}
    assert factorint(-16) == {-1: 1, 2: 4}
    assert factorint(2) == {2: 1}
    assert factorint(126) == {2: 1, 3: 2, 7: 1}
    assert factorint(123456) == {2: 6, 3: 1, 643: 1}
    assert factorint(5951757) == {3: 1, 7: 1, 29: 2, 337: 1}
    assert factorint(64015937) == {7993: 1, 8009: 1}
    assert factorint(2**(2**6) + 1) == {274177: 1, 67280421310721: 1}

    assert factorint(0, multiple=True) == [0]
    assert factorint(1, multiple=True) == []
    assert factorint(-1, multiple=True) == [-1]
    assert factorint(-2, multiple=True) == [-1, 2]
    assert factorint(-16, multiple=True) == [-1, 2, 2, 2, 2]
    assert factorint(2, multiple=True) == [2]
    assert factorint(24, multiple=True) == [2, 2, 2, 3]
    assert factorint(126, multiple=True) == [2, 3, 3, 7]
    assert factorint(123456, multiple=True) == [2, 2, 2, 2, 2, 2, 3, 643]
    assert factorint(5951757, multiple=True) == [3, 7, 29, 29, 337]
    assert factorint(64015937, multiple=True) == [7993, 8009]
    assert factorint(2**(2**6) + 1, multiple=True) == [274177, 67280421310721]

    assert factorint(fac(1, evaluate=False)) == {}
    assert factorint(fac(7, evaluate=False)) == {2: 4, 3: 2, 5: 1, 7: 1}
    assert factorint(fac(15, evaluate=False)) == \
        {2: 11, 3: 6, 5: 3, 7: 2, 11: 1, 13: 1}
    assert factorint(fac(20, evaluate=False)) == \
        {2: 18, 3: 8, 5: 4, 7: 2, 11: 1, 13: 1, 17: 1, 19: 1}
    assert factorint(fac(23, evaluate=False)) == \
        {2: 19, 3: 9, 5: 4, 7: 3, 11: 2, 13: 1, 17: 1, 19: 1, 23: 1}

    assert multiproduct(factorint(fac(200))) == fac(200)
    assert multiproduct(factorint(fac(200, evaluate=False))) == fac(200)
    for b, e in factorint(fac(150)).items():
        assert e == fac_multiplicity(150, b)
    for b, e in factorint(fac(150, evaluate=False)).items():
        assert e == fac_multiplicity(150, b)
    assert factorint(103005006059**7) == {103005006059: 7}
    assert factorint(31337**191) == {31337: 191}
    assert factorint(2**1000 * 3**500 * 257**127 * 383**60) == \
        {2: 1000, 3: 500, 257: 127, 383: 60}
    assert len(factorint(fac(10000))) == 1229
    assert len(factorint(fac(10000, evaluate=False))) == 1229
    assert factorint(12932983746293756928584532764589230) == \
        {2: 1, 5: 1, 73: 1, 727719592270351: 1, 63564265087747: 1, 383: 1}
    assert factorint(727719592270351) == {727719592270351: 1}
    assert factorint(2**64 + 1, use_trial=False) == factorint(2**64 + 1)
    for n in range(60000):
        assert multiproduct(factorint(n)) == n
    assert pollard_rho(2**64 + 1, seed=1) == 274177
    assert pollard_rho(19, seed=1) is None
    assert factorint(3, limit=2) == {3: 1}
    assert factorint(12345) == {3: 1, 5: 1, 823: 1}
    assert factorint(
        12345, limit=3) == {4115: 1, 3: 1}  # the 5 is greater than the limit
    assert factorint(1, limit=1) == {}
    assert factorint(0, 3) == {0: 1}
    assert factorint(12, limit=1) == {12: 1}
    assert factorint(30, limit=2) == {2: 1, 15: 1}
    assert factorint(16, limit=2) == {2: 4}
    assert factorint(124, limit=3) == {2: 2, 31: 1}
    assert factorint(4*31**2, limit=3) == {2: 2, 31: 2}
    p1 = nextprime(2**32)
    p2 = nextprime(2**16)
    p3 = nextprime(p2)
    assert factorint(p1*p2*p3) == {p1: 1, p2: 1, p3: 1}
    assert factorint(13*17*19, limit=15) == {13: 1, 17*19: 1}
    assert factorint(1951*15013*15053, limit=2000) == {225990689: 1, 1951: 1}
    assert factorint(primorial(17) + 1, use_pm1=0) == \
        {long(19026377261): 1, 3467: 1, 277: 1, 105229: 1}
    # when prime b is closer than approx sqrt(8*p) to prime p then they are
    # "close" and have a trivial factorization
    a = nextprime(2**2**8)  # 78 digits
    b = nextprime(a + 2**2**4)
    assert 'Fermat' in capture(lambda: factorint(a*b, verbose=1))

    raises(ValueError, lambda: pollard_rho(4))
    raises(ValueError, lambda: pollard_pm1(3))
    raises(ValueError, lambda: pollard_pm1(10, B=2))
    # verbose coverage
    n = nextprime(2**16)*nextprime(2**17)*nextprime(1901)
    assert 'with primes' in capture(lambda: factorint(n, verbose=1))
    capture(lambda: factorint(nextprime(2**16)*1012, verbose=1))

    n = nextprime(2**17)
    capture(lambda: factorint(n**3, verbose=1))  # perfect power termination
    capture(lambda: factorint(2*n, verbose=1))  # factoring complete msg

    # exceed 1st
    n = nextprime(2**17)
    n *= nextprime(n)
    assert '1000' in capture(lambda: factorint(n, limit=1000, verbose=1))
    n *= nextprime(n)
    assert len(factorint(n)) == 3
    assert len(factorint(n, limit=p1)) == 3
    n *= nextprime(2*n)
    # exceed 2nd
    assert '2001' in capture(lambda: factorint(n, limit=2000, verbose=1))
    assert capture(
        lambda: factorint(n, limit=4000, verbose=1)).count('Pollard') == 2
    # non-prime pm1 result
    n = nextprime(8069)
    n *= nextprime(2*n)*nextprime(2*n, 2)
    capture(lambda: factorint(n, verbose=1))  # non-prime pm1 result
    # factor fermat composite
    p1 = nextprime(2**17)
    p2 = nextprime(2*p1)
    assert factorint((p1*p2**2)**3) == {p1: 3, p2: 6}
    # Test for non integer input
    raises(ValueError, lambda: factorint(4.5))


def test_divisors_and_divisor_count():
    assert divisors(-1) == [1]
    assert divisors(0) == []
    assert divisors(1) == [1]
    assert divisors(2) == [1, 2]
    assert divisors(3) == [1, 3]
    assert divisors(17) == [1, 17]
    assert divisors(10) == [1, 2, 5, 10]
    assert divisors(100) == [1, 2, 4, 5, 10, 20, 25, 50, 100]
    assert divisors(101) == [1, 101]

    assert divisor_count(0) == 0
    assert divisor_count(-1) == 1
    assert divisor_count(1) == 1
    assert divisor_count(6) == 4
    assert divisor_count(12) == 6

    assert divisor_count(180, 3) == divisor_count(180//3)
    assert divisor_count(2*3*5, 7) == 0


def test_udivisors_and_udivisor_count():
    assert udivisors(-1) == [1]
    assert udivisors(0) == []
    assert udivisors(1) == [1]
    assert udivisors(2) == [1, 2]
    assert udivisors(3) == [1, 3]
    assert udivisors(17) == [1, 17]
    assert udivisors(10) == [1, 2, 5, 10]
    assert udivisors(100) == [1, 4, 25, 100]
    assert udivisors(101) == [1, 101]
    assert udivisors(1000) == [1, 8, 125, 1000]

    assert udivisor_count(0) == 0
    assert udivisor_count(-1) == 1
    assert udivisor_count(1) == 1
    assert udivisor_count(6) == 4
    assert udivisor_count(12) == 4

    assert udivisor_count(180) == 8
    assert udivisor_count(2*3*5*7) == 16


def test_issue_6981():
    S = set(divisors(4)).union(set(divisors(Integer(2))))
    assert S == {1,2,4}


def test_totient():
    assert [totient(k) for k in range(1, 12)] == \
        [1, 1, 2, 2, 4, 2, 6, 4, 6, 4, 10]
    assert totient(5005) == 2880
    assert totient(5006) == 2502
    assert totient(5009) == 5008
    assert totient(2**100) == 2**99

    raises(ValueError, lambda: totient(30.1))
    raises(ValueError, lambda: totient(20.001))

    m = Symbol("m", integer=True)
    assert totient(m)
    assert totient(m).subs(m, 3**10) == 3**10 - 3**9
    assert summation(totient(m), (m, 1, 11)) == 42

    n = Symbol("n", integer=True, positive=True)
    assert totient(n).is_integer

    x=Symbol("x", integer=False)
    raises(ValueError, lambda: totient(x))

    y=Symbol("y", positive=False)
    raises(ValueError, lambda: totient(y))

    z=Symbol("z", positive=True, integer=True)
    raises(ValueError, lambda: totient(2**(-z)))


def test_reduced_totient():
    assert [reduced_totient(k) for k in range(1, 16)] == \
        [1, 1, 2, 2, 4, 2, 6, 2, 6, 4, 10, 2, 12, 6, 4]
    assert reduced_totient(5005) == 60
    assert reduced_totient(5006) == 2502
    assert reduced_totient(5009) == 5008
    assert reduced_totient(2**100) == 2**98

    m = Symbol("m", integer=True)
    assert reduced_totient(m)
    assert reduced_totient(m).subs(m, 2**3*3**10) == 3**10 - 3**9
    assert summation(reduced_totient(m), (m, 1, 16)) == 68

    n = Symbol("n", integer=True, positive=True)
    assert reduced_totient(n).is_integer


def test_divisor_sigma():
    assert [divisor_sigma(k) for k in range(1, 12)] == \
        [1, 3, 4, 7, 6, 12, 8, 15, 13, 18, 12]
    assert [divisor_sigma(k, 2) for k in range(1, 12)] == \
        [1, 5, 10, 21, 26, 50, 50, 85, 91, 130, 122]
    assert divisor_sigma(23450) == 50592
    assert divisor_sigma(23450, 0) == 24
    assert divisor_sigma(23450, 1) == 50592
    assert divisor_sigma(23450, 2) == 730747500
    assert divisor_sigma(23450, 3) == 14666785333344

    m = Symbol("m", integer=True)
    k = Symbol("k", integer=True)
    assert divisor_sigma(m)
    assert divisor_sigma(m, k)
    assert divisor_sigma(m).subs(m, 3**10) == 88573
    assert divisor_sigma(m, k).subs([(m, 3**10), (k, 3)]) == 213810021790597
    assert summation(divisor_sigma(m), (m, 1, 11)) == 99


def test_udivisor_sigma():
    assert [udivisor_sigma(k) for k in range(1, 12)] == \
        [1, 3, 4, 5, 6, 12, 8, 9, 10, 18, 12]
    assert [udivisor_sigma(k, 3) for k in range(1, 12)] == \
        [1, 9, 28, 65, 126, 252, 344, 513, 730, 1134, 1332]
    assert udivisor_sigma(23450) == 42432
    assert udivisor_sigma(23450, 0) == 16
    assert udivisor_sigma(23450, 1) == 42432
    assert udivisor_sigma(23450, 2) == 702685000
    assert udivisor_sigma(23450, 4) == 321426961814978248

    m = Symbol("m", integer=True)
    k = Symbol("k", integer=True)
    assert udivisor_sigma(m)
    assert udivisor_sigma(m, k)
    assert udivisor_sigma(m).subs(m, 4**9) == 262145
    assert udivisor_sigma(m, k).subs([(m, 4**9), (k, 2)]) == 68719476737
    assert summation(udivisor_sigma(m), (m, 2, 15)) == 169


def test_issue_4356():
    assert factorint(1030903) == {53: 2, 367: 1}


def test_divisors():
    assert divisors(28) == [1, 2, 4, 7, 14, 28]
    assert [x for x in divisors(3*5*7, 1)] == [1, 3, 5, 15, 7, 21, 35, 105]
    assert divisors(0) == []


def test_divisor_count():
    assert divisor_count(0) == 0
    assert divisor_count(6) == 4


def test_antidivisors():
    assert antidivisors(-1) == []
    assert antidivisors(-3) == [2]
    assert antidivisors(14) == [3, 4, 9]
    assert antidivisors(237) == [2, 5, 6, 11, 19, 25, 43, 95, 158]
    assert antidivisors(12345) == [2, 6, 7, 10, 30, 1646, 3527, 4938, 8230]
    assert antidivisors(393216) == [262144]
    assert sorted(x for x in antidivisors(3*5*7, 1)) == \
        [2, 6, 10, 11, 14, 19, 30, 42, 70]
    assert antidivisors(1) == []


def test_antidivisor_count():
    assert antidivisor_count(0) == 0
    assert antidivisor_count(-1) == 0
    assert antidivisor_count(-4) == 1
    assert antidivisor_count(20) == 3
    assert antidivisor_count(25) == 5
    assert antidivisor_count(38) == 7
    assert antidivisor_count(180) == 6
    assert antidivisor_count(2*3*5) == 3


def test_smoothness_and_smoothness_p():
    assert smoothness(1) == (1, 1)
    assert smoothness(2**4*3**2) == (3, 16)

    assert smoothness_p(10431, m=1) == \
        (1, [(3, (2, 2, 4)), (19, (1, 5, 5)), (61, (1, 31, 31))])
    assert smoothness_p(10431) == \
        (-1, [(3, (2, 2, 2)), (19, (1, 3, 9)), (61, (1, 5, 5))])
    assert smoothness_p(10431, power=1) == \
        (-1, [(3, (2, 2, 2)), (61, (1, 5, 5)), (19, (1, 3, 9))])
    assert smoothness_p(21477639576571, visual=1) == \
        'p**i=4410317**1 has p-1 B=1787, B-pow=1787\n' + \
        'p**i=4869863**1 has p-1 B=2434931, B-pow=2434931'


def test_visual_factorint():
    assert factorint(1, visual=1) == 1
    forty2 = factorint(42, visual=True)
    assert type(forty2) == Mul
    assert str(forty2) == '2**1*3**1*7**1'
    assert factorint(1, visual=True) is S.One
    no = dict(evaluate=False)
    assert factorint(42**2, visual=True) == Mul(Pow(2, 2, **no),
                                                Pow(3, 2, **no),
                                                Pow(7, 2, **no), **no)
    assert -1 in factorint(-42, visual=True).args


def test_factorrat():
    assert str(factorrat(S(12)/1, visual=True)) == '2**2*3**1'
    assert str(factorrat(S(1)/1, visual=True)) == '1'
    assert str(factorrat(S(25)/14, visual=True)) == '5**2/(2*7)'
    assert str(factorrat(S(-25)/14/9, visual=True)) == '-5**2/(2*3**2*7)'

    assert factorrat(S(12)/1, multiple=True) == [2, 2, 3]
    assert factorrat(S(1)/1, multiple=True) == []
    assert factorrat(S(25)/14, multiple=True) == [S(1)/7, S(1)/2, 5, 5]
    assert factorrat(S(12)/1, multiple=True) == [2, 2, 3]
    assert factorrat(S(-25)/14/9, multiple=True) == \
        [-1, S(1)/7, S(1)/3, S(1)/3, S(1)/2, 5, 5]


def test_visual_io():
    sm = smoothness_p
    fi = factorint
    # with smoothness_p
    n = 124
    d = fi(n)
    m = fi(d, visual=True)
    t = sm(n)
    s = sm(t)
    for th in [d, s, t, n, m]:
        assert sm(th, visual=True) == s
        assert sm(th, visual=1) == s
    for th in [d, s, t, n, m]:
        assert sm(th, visual=False) == t
    assert [sm(th, visual=None) for th in [d, s, t, n, m]] == [s, d, s, t, t]
    assert [sm(th, visual=2) for th in [d, s, t, n, m]] == [s, d, s, t, t]

    # with factorint
    for th in [d, m, n]:
        assert fi(th, visual=True) == m
        assert fi(th, visual=1) == m
    for th in [d, m, n]:
        assert fi(th, visual=False) == d
    assert [fi(th, visual=None) for th in [d, m, n]] == [m, d, d]
    assert [fi(th, visual=0) for th in [d, m, n]] == [m, d, d]

    # test reevaluation
    no = dict(evaluate=False)
    assert sm({4: 2}, visual=False) == sm(16)
    assert sm(Mul(*[Pow(k, v, **no) for k, v in {4: 2, 2: 6}.items()], **no),
              visual=False) == sm(2**10)

    assert fi({4: 2}, visual=False) == fi(16)
    assert fi(Mul(*[Pow(k, v, **no) for k, v in {4: 2, 2: 6}.items()], **no),
              visual=False) == fi(2**10)


def test_core():
    assert core(35**13, 10) == 42875
    assert core(210**2) == 1
    assert core(7776, 3) == 36
    assert core(10**27, 22) == 10**5
    assert core(537824) == 14
    assert core(1, 6) == 1


def test_digits():
    assert all([digits(n, 2)[1:] == [int(d) for d in format(n, 'b')]
                for n in range(20)])
    assert all([digits(n, 8)[1:] == [int(d) for d in format(n, 'o')]
                for n in range(20)])
    assert all([digits(n, 16)[1:] == [int(d, 16) for d in format(n, 'x')]
                for n in range(20)])
    assert digits(2345, 34) == [34, 2, 0, 33]
    assert digits(384753, 71) == [71, 1, 5, 23, 4]
    assert digits(93409) == [10, 9, 3, 4, 0, 9]
    assert digits(-92838, 11) == [-11, 6, 3, 8, 2, 9]


def test_primenu():
    assert primenu(2) == 1
    assert primenu(2 * 3) == 2
    assert primenu(2 * 3 * 5) == 3
    assert primenu(3 * 25) == primenu(3) + primenu(25)
    assert [primenu(p) for p in primerange(1, 10)] == [1, 1, 1, 1]
    assert primenu(fac(50)) == 15
    assert primenu(2 ** 9941 - 1) == 1
    n = Symbol('n', integer=True)
    assert primenu(n)
    assert primenu(n).subs(n, 2 ** 31 - 1) == 1
    assert summation(primenu(n), (n, 2, 30)) == 43


def test_primeomega():
    assert primeomega(2) == 1
    assert primeomega(2 * 2) == 2
    assert primeomega(2 * 2 * 3) == 3
    assert primeomega(3 * 25) == primeomega(3) + primeomega(25)
    assert [primeomega(p) for p in primerange(1, 10)] == [1, 1, 1, 1]
    assert primeomega(fac(50)) == 108
    assert primeomega(2 ** 9941 - 1) == 1
    n = Symbol('n', integer=True)
    assert primeomega(n)
    assert primeomega(n).subs(n, 2 ** 31 - 1) == 1
    assert summation(primeomega(n), (n, 2, 30)) == 59


def test_mersenne_prime_exponent():
    assert mersenne_prime_exponent(1) == 2
    assert mersenne_prime_exponent(4) == 7
    assert mersenne_prime_exponent(10) == 89
    assert mersenne_prime_exponent(25) == 21701
    raises(ValueError, lambda: mersenne_prime_exponent(52))
    raises(ValueError, lambda: mersenne_prime_exponent(0))


def test_is_perfect():
    assert is_perfect(6) is True
    assert is_perfect(15) is False
    assert is_perfect(28) is True
    assert is_perfect(400) is False
    assert is_perfect(496) is True
    assert is_perfect(8128) is True
    assert is_perfect(10000) is False


def test_is_mersenne_prime():
    assert is_mersenne_prime(10) is False
    assert is_mersenne_prime(127) is True
    assert is_mersenne_prime(511) is False
    assert is_mersenne_prime(131071) is True
    assert is_mersenne_prime(2147483647) is True


def test_is_abundant():
    assert is_abundant(10) is False
    assert is_abundant(12) is True
    assert is_abundant(18) is True
    assert is_abundant(21) is False
    assert is_abundant(945) is True


def test_is_deficient():
    assert is_deficient(10) is True
    assert is_deficient(22) is True
    assert is_deficient(56) is False
    assert is_deficient(20) is False
    assert is_deficient(36) is False


def test_is_amicable():
    assert is_amicable(173, 129) is False
    assert is_amicable(220, 284) is True
    assert is_amicable(8756, 8756) is False
