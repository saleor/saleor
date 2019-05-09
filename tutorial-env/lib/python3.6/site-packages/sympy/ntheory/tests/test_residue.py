from collections import defaultdict
from sympy import S, Symbol, Tuple
from sympy.core.compatibility import range

from sympy.ntheory import n_order, is_primitive_root, is_quad_residue, \
    legendre_symbol, jacobi_symbol, totient, primerange, sqrt_mod, \
    primitive_root, quadratic_residues, is_nthpow_residue, nthroot_mod, \
    sqrt_mod_iter, mobius, discrete_log
from sympy.ntheory.residue_ntheory import _primitive_root_prime_iter, \
    _discrete_log_trial_mul, _discrete_log_shanks_steps, \
    _discrete_log_pollard_rho, _discrete_log_pohlig_hellman
from sympy.polys.domains import ZZ
from sympy.utilities.pytest import raises


def test_residue():
    assert n_order(2, 13) == 12
    assert [n_order(a, 7) for a in range(1, 7)] == \
           [1, 3, 6, 3, 6, 2]
    assert n_order(5, 17) == 16
    assert n_order(17, 11) == n_order(6, 11)
    assert n_order(101, 119) == 6
    assert n_order(11, (10**50 + 151)**2) == 10000000000000000000000000000000000000000000000030100000000000000000000000000000000000000000000022650
    raises(ValueError, lambda: n_order(6, 9))

    assert is_primitive_root(2, 7) is False
    assert is_primitive_root(3, 8) is False
    assert is_primitive_root(11, 14) is False
    assert is_primitive_root(12, 17) == is_primitive_root(29, 17)
    raises(ValueError, lambda: is_primitive_root(3, 6))

    assert [primitive_root(i) for i in range(2, 31)] == [1, 2, 3, 2, 5, 3, \
       None, 2, 3, 2, None, 2, 3, None, None, 3, 5, 2, None, None, 7, 5, \
       None, 2, 7, 2, None, 2, None]

    for p in primerange(3, 100):
        it = _primitive_root_prime_iter(p)
        assert len(list(it)) == totient(totient(p))
    assert primitive_root(97) == 5
    assert primitive_root(97**2) == 5
    assert primitive_root(40487) == 5
    # note that primitive_root(40487) + 40487 = 40492 is a primitive root
    # of 40487**2, but it is not the smallest
    assert primitive_root(40487**2) == 10
    assert primitive_root(82) == 7
    p = 10**50 + 151
    assert primitive_root(p) == 11
    assert primitive_root(2*p) == 11
    assert primitive_root(p**2) == 11
    raises(ValueError, lambda: primitive_root(-3))

    assert is_quad_residue(3, 7) is False
    assert is_quad_residue(10, 13) is True
    assert is_quad_residue(12364, 139) == is_quad_residue(12364 % 139, 139)
    assert is_quad_residue(207, 251) is True
    assert is_quad_residue(0, 1) is True
    assert is_quad_residue(1, 1) is True
    assert is_quad_residue(0, 2) == is_quad_residue(1, 2) is True
    assert is_quad_residue(1, 4) is True
    assert is_quad_residue(2, 27) is False
    assert is_quad_residue(13122380800, 13604889600) is True
    assert [j for j in range(14) if is_quad_residue(j, 14)] == \
           [0, 1, 2, 4, 7, 8, 9, 11]
    raises(ValueError, lambda: is_quad_residue(1.1, 2))
    raises(ValueError, lambda: is_quad_residue(2, 0))


    assert quadratic_residues(S.One) == [0]
    assert quadratic_residues(1) == [0]
    assert quadratic_residues(12) == [0, 1, 4, 9]
    assert quadratic_residues(12) == [0, 1, 4, 9]
    assert quadratic_residues(13) == [0, 1, 3, 4, 9, 10, 12]
    assert [len(quadratic_residues(i)) for i in range(1, 20)] == \
      [1, 2, 2, 2, 3, 4, 4, 3, 4, 6, 6, 4, 7, 8, 6, 4, 9, 8, 10]

    assert list(sqrt_mod_iter(6, 2)) == [0]
    assert sqrt_mod(3, 13) == 4
    assert sqrt_mod(3, -13) == 4
    assert sqrt_mod(6, 23) == 11
    assert sqrt_mod(345, 690) == 345

    for p in range(3, 100):
        d = defaultdict(list)
        for i in range(p):
            d[pow(i, 2, p)].append(i)
        for i in range(1, p):
            it = sqrt_mod_iter(i, p)
            v = sqrt_mod(i, p, True)
            if v:
                v = sorted(v)
                assert d[i] == v
            else:
                assert not d[i]

    assert sqrt_mod(9, 27, True) == [3, 6, 12, 15, 21, 24]
    assert sqrt_mod(9, 81, True) == [3, 24, 30, 51, 57, 78]
    assert sqrt_mod(9, 3**5, True) == [3, 78, 84, 159, 165, 240]
    assert sqrt_mod(81, 3**4, True) == [0, 9, 18, 27, 36, 45, 54, 63, 72]
    assert sqrt_mod(81, 3**5, True) == [9, 18, 36, 45, 63, 72, 90, 99, 117,\
            126, 144, 153, 171, 180, 198, 207, 225, 234]
    assert sqrt_mod(81, 3**6, True) == [9, 72, 90, 153, 171, 234, 252, 315,\
            333, 396, 414, 477, 495, 558, 576, 639, 657, 720]
    assert sqrt_mod(81, 3**7, True) == [9, 234, 252, 477, 495, 720, 738, 963,\
            981, 1206, 1224, 1449, 1467, 1692, 1710, 1935, 1953, 2178]

    for a, p in [(26214400, 32768000000), (26214400, 16384000000),
        (262144, 1048576), (87169610025, 163443018796875),
        (22315420166400, 167365651248000000)]:
        assert pow(sqrt_mod(a, p), 2, p) == a

    n = 70
    a, p = 5**2*3**n*2**n, 5**6*3**(n+1)*2**(n+2)
    it = sqrt_mod_iter(a, p)
    for i in range(10):
        assert pow(next(it), 2, p) == a
    a, p = 5**2*3**n*2**n, 5**6*3**(n+1)*2**(n+3)
    it = sqrt_mod_iter(a, p)
    for i in range(2):
        assert pow(next(it), 2, p) == a
    n = 100
    a, p = 5**2*3**n*2**n, 5**6*3**(n+1)*2**(n+1)
    it = sqrt_mod_iter(a, p)
    for i in range(2):
        assert pow(next(it), 2, p) == a

    assert type(next(sqrt_mod_iter(9, 27))) is int
    assert type(next(sqrt_mod_iter(9, 27, ZZ))) is type(ZZ(1))
    assert type(next(sqrt_mod_iter(1, 7, ZZ))) is type(ZZ(1))

    assert is_nthpow_residue(2, 1, 5)

    #issue 10816
    assert is_nthpow_residue(1, 0, 1) is False
    assert is_nthpow_residue(1, 0, 2) is True
    assert is_nthpow_residue(3, 0, 2) is False
    assert is_nthpow_residue(0, 1, 8) is True
    assert is_nthpow_residue(2, 3, 2) is False
    assert is_nthpow_residue(2, 3, 9) is False
    assert is_nthpow_residue(3, 5, 30) is True
    assert is_nthpow_residue(21, 11, 20) is True
    assert is_nthpow_residue(7, 10, 20) is False
    assert is_nthpow_residue(5, 10, 20) is True
    assert is_nthpow_residue(3, 10, 48) is False
    assert is_nthpow_residue(1, 10, 40) is True
    assert is_nthpow_residue(3, 10, 24) is False
    assert is_nthpow_residue(1, 10, 24) is True
    assert is_nthpow_residue(3, 10, 24) is False
    assert is_nthpow_residue(2, 10, 48) is False
    assert is_nthpow_residue(81, 3, 972) is False
    assert is_nthpow_residue(243, 5, 5103) is True
    assert is_nthpow_residue(243, 3, 1240029) is False
    x = set([pow(i, 56, 1024) for i in range(1024)])
    assert set([a for a in range(1024) if is_nthpow_residue(a, 56, 1024)]) == x
    x = set([ pow(i, 256, 2048) for i in range(2048)])
    assert set([a for a in range(2048) if is_nthpow_residue(a, 256, 2048)]) == x
    x = set([ pow(i, 11, 324000) for i in range(1000)])
    assert [ is_nthpow_residue(a, 11, 324000) for a in x]
    x = set([ pow(i, 17, 22217575536) for i in range(1000)])
    assert [ is_nthpow_residue(a, 17, 22217575536) for a in x]
    assert is_nthpow_residue(676, 3, 5364)
    assert is_nthpow_residue(9, 12, 36)
    assert is_nthpow_residue(32, 10, 41)
    assert is_nthpow_residue(4, 2, 64)
    assert is_nthpow_residue(31, 4, 41)
    assert not is_nthpow_residue(2, 2, 5)
    assert is_nthpow_residue(8547, 12, 10007)
    assert nthroot_mod(29, 31, 74) == 31
    assert nthroot_mod(*Tuple(29, 31, 74)) == 31
    assert nthroot_mod(1801, 11, 2663) == 44
    for a, q, p in [(51922, 2, 203017), (43, 3, 109), (1801, 11, 2663),
          (26118163, 1303, 33333347), (1499, 7, 2663), (595, 6, 2663),
          (1714, 12, 2663), (28477, 9, 33343)]:
        r = nthroot_mod(a, q, p)
        assert pow(r, q, p) == a
    assert nthroot_mod(11, 3, 109) is None
    raises(NotImplementedError, lambda: nthroot_mod(16, 5, 36))
    raises(NotImplementedError, lambda: nthroot_mod(9, 16, 36))

    for p in primerange(5, 100):
        qv = range(3, p, 4)
        for q in qv:
            d = defaultdict(list)
            for i in range(p):
                d[pow(i, q, p)].append(i)
            for a in range(1, p - 1):
                res = nthroot_mod(a, q, p, True)
                if d[a]:
                    assert d[a] == res
                else:
                    assert res is None

    assert legendre_symbol(5, 11) == 1
    assert legendre_symbol(25, 41) == 1
    assert legendre_symbol(67, 101) == -1
    assert legendre_symbol(0, 13) == 0
    assert legendre_symbol(9, 3) == 0
    raises(ValueError, lambda: legendre_symbol(2, 4))

    assert jacobi_symbol(25, 41) == 1
    assert jacobi_symbol(-23, 83) == -1
    assert jacobi_symbol(3, 9) == 0
    assert jacobi_symbol(42, 97) == -1
    assert jacobi_symbol(3, 5) == -1
    assert jacobi_symbol(7, 9) == 1
    assert jacobi_symbol(0, 3) == 0
    assert jacobi_symbol(0, 1) == 1
    assert jacobi_symbol(2, 1) == 1
    assert jacobi_symbol(1, 3) == 1
    raises(ValueError, lambda: jacobi_symbol(3, 8))

    assert mobius(13*7) == 1
    assert mobius(1) == 1
    assert mobius(13*7*5) == -1
    assert mobius(13**2) == 0
    raises(ValueError, lambda: mobius(-3))

    p = Symbol('p', integer=True, positive=True, prime=True)
    x = Symbol('x', positive=True)
    i = Symbol('i', integer=True)
    assert mobius(p) == -1
    raises(TypeError, lambda: mobius(x))
    raises(ValueError, lambda: mobius(i))

    assert _discrete_log_trial_mul(587, 2**7, 2) == 7
    assert _discrete_log_trial_mul(941, 7**18, 7) == 18
    assert _discrete_log_trial_mul(389, 3**81, 3) == 81
    assert _discrete_log_trial_mul(191, 19**123, 19) == 123
    assert _discrete_log_shanks_steps(442879, 7**2, 7) == 2
    assert _discrete_log_shanks_steps(874323, 5**19, 5) == 19
    assert _discrete_log_shanks_steps(6876342, 7**71, 7) == 71
    assert _discrete_log_shanks_steps(2456747, 3**321, 3) == 321
    assert _discrete_log_pollard_rho(6013199, 2**6, 2, rseed=0) == 6
    assert _discrete_log_pollard_rho(6138719, 2**19, 2, rseed=0) == 19
    assert _discrete_log_pollard_rho(36721943, 2**40, 2, rseed=0) == 40
    assert _discrete_log_pollard_rho(24567899, 3**333, 3, rseed=0) == 333
    raises(ValueError, lambda: _discrete_log_pollard_rho(11, 7, 31, rseed=0))
    raises(ValueError, lambda: _discrete_log_pollard_rho(227, 3**7, 5, rseed=0))

    assert _discrete_log_pohlig_hellman(98376431, 11**9, 11) == 9
    assert _discrete_log_pohlig_hellman(78723213, 11**31, 11) == 31
    assert _discrete_log_pohlig_hellman(32942478, 11**98, 11) == 98
    assert _discrete_log_pohlig_hellman(14789363, 11**444, 11) == 444
    assert discrete_log(587, 2**9, 2) == 9
    assert discrete_log(2456747, 3**51, 3) == 51
    assert discrete_log(32942478, 11**127, 11) == 127
    assert discrete_log(432751500361, 7**324, 7) == 324
    args = 5779, 3528, 6215
    assert discrete_log(*args) == 687
    assert discrete_log(*Tuple(*args)) == 687
