from sympy.core import symbols
from sympy.core.compatibility import range
from sympy.crypto.crypto import (cycle_list,
      encipher_shift, encipher_affine, encipher_substitution,
      check_and_join, encipher_vigenere, decipher_vigenere,
      encipher_hill, decipher_hill, encipher_bifid5, encipher_bifid6,
      bifid5_square, bifid6_square, bifid5, bifid6, bifid10,
      decipher_bifid5, decipher_bifid6, encipher_kid_rsa,
      decipher_kid_rsa, kid_rsa_private_key, kid_rsa_public_key,
      decipher_rsa, rsa_private_key, rsa_public_key, encipher_rsa,
      lfsr_connection_polynomial, lfsr_autocorrelation, lfsr_sequence,
      encode_morse, decode_morse, elgamal_private_key, elgamal_public_key,
      encipher_elgamal, decipher_elgamal, dh_private_key, dh_public_key,
      dh_shared_key, decipher_shift, decipher_affine, encipher_bifid,
      decipher_bifid, bifid_square, padded_key, uniq, decipher_gm,
      encipher_gm, gm_public_key, gm_private_key, encipher_bg, decipher_bg,
      bg_private_key, bg_public_key)
from sympy.matrices import Matrix
from sympy.ntheory import isprime, is_primitive_root
from sympy.polys.domains import FF

from sympy.utilities.pytest import raises, slow, warns_deprecated_sympy

from random import randrange


def test_cycle_list():
    assert cycle_list(3, 4) == [3, 0, 1, 2]
    assert cycle_list(-1, 4) == [3, 0, 1, 2]
    assert cycle_list(1, 4) == [1, 2, 3, 0]


def test_encipher_shift():
    assert encipher_shift("ABC", 0) == "ABC"
    assert encipher_shift("ABC", 1) == "BCD"
    assert encipher_shift("ABC", -1) == "ZAB"
    assert decipher_shift("ZAB", -1) == "ABC"


def test_encipher_affine():
    assert encipher_affine("ABC", (1, 0)) == "ABC"
    assert encipher_affine("ABC", (1, 1)) == "BCD"
    assert encipher_affine("ABC", (-1, 0)) == "AZY"
    assert encipher_affine("ABC", (-1, 1), symbols="ABCD") == "BAD"
    assert encipher_affine("123", (-1, 1), symbols="1234") == "214"
    assert encipher_affine("ABC", (3, 16)) == "QTW"
    assert decipher_affine("QTW", (3, 16)) == "ABC"


def test_encipher_substitution():
    assert encipher_substitution("ABC", "BAC", "ABC") == "BAC"
    assert encipher_substitution("123", "1243", "1234") == "124"


def test_check_and_join():
    assert check_and_join("abc") == "abc"
    assert check_and_join(uniq("aaabc")) == "abc"
    assert check_and_join("ab c".split()) == "abc"
    assert check_and_join("abc", "a", filter=True) == "a"
    raises(ValueError, lambda: check_and_join('ab', 'a'))


def test_encipher_vigenere():
    assert encipher_vigenere("ABC", "ABC") == "ACE"
    assert encipher_vigenere("ABC", "ABC", symbols="ABCD") == "ACA"
    assert encipher_vigenere("ABC", "AB", symbols="ABCD") == "ACC"
    assert encipher_vigenere("AB", "ABC", symbols="ABCD") == "AC"
    assert encipher_vigenere("A", "ABC", symbols="ABCD") == "A"


def test_decipher_vigenere():
    assert decipher_vigenere("ABC", "ABC") == "AAA"
    assert decipher_vigenere("ABC", "ABC", symbols="ABCD") == "AAA"
    assert decipher_vigenere("ABC", "AB", symbols="ABCD") == "AAC"
    assert decipher_vigenere("AB", "ABC", symbols="ABCD") == "AA"
    assert decipher_vigenere("A", "ABC", symbols="ABCD") == "A"


def test_encipher_hill():
    A = Matrix(2, 2, [1, 2, 3, 5])
    assert encipher_hill("ABCD", A) == "CFIV"
    A = Matrix(2, 2, [1, 0, 0, 1])
    assert encipher_hill("ABCD", A) == "ABCD"
    assert encipher_hill("ABCD", A, symbols="ABCD") == "ABCD"
    A = Matrix(2, 2, [1, 2, 3, 5])
    assert encipher_hill("ABCD", A, symbols="ABCD") == "CBAB"
    assert encipher_hill("AB", A, symbols="ABCD") == "CB"
    # message length, n, does not need to be a multiple of k;
    # it is padded
    assert encipher_hill("ABA", A) == "CFGC"
    assert encipher_hill("ABA", A, pad="Z") == "CFYV"


def test_decipher_hill():
    A = Matrix(2, 2, [1, 2, 3, 5])
    assert decipher_hill("CFIV", A) == "ABCD"
    A = Matrix(2, 2, [1, 0, 0, 1])
    assert decipher_hill("ABCD", A) == "ABCD"
    assert decipher_hill("ABCD", A, symbols="ABCD") == "ABCD"
    A = Matrix(2, 2, [1, 2, 3, 5])
    assert decipher_hill("CBAB", A, symbols="ABCD") == "ABCD"
    assert decipher_hill("CB", A, symbols="ABCD") == "AB"
    # n does not need to be a multiple of k
    assert decipher_hill("CFA", A) == "ABAA"


def test_encipher_bifid5():
    assert encipher_bifid5("AB", "AB") == "AB"
    assert encipher_bifid5("AB", "CD") == "CO"
    assert encipher_bifid5("ab", "c") == "CH"
    assert encipher_bifid5("a bc", "b") == "BAC"


def test_bifid5_square():
    A = bifid5
    f = lambda i, j: symbols(A[5*i + j])
    M = Matrix(5, 5, f)
    assert bifid5_square("") == M


def test_decipher_bifid5():
    assert decipher_bifid5("AB", "AB") == "AB"
    assert decipher_bifid5("CO", "CD") == "AB"
    assert decipher_bifid5("ch", "c") == "AB"
    assert decipher_bifid5("b ac", "b") == "ABC"


def test_encipher_bifid6():
    assert encipher_bifid6("AB", "AB") == "AB"
    assert encipher_bifid6("AB", "CD") == "CP"
    assert encipher_bifid6("ab", "c") == "CI"
    assert encipher_bifid6("a bc", "b") == "BAC"


def test_decipher_bifid6():
    assert decipher_bifid6("AB", "AB") == "AB"
    assert decipher_bifid6("CP", "CD") == "AB"
    assert decipher_bifid6("ci", "c") == "AB"
    assert decipher_bifid6("b ac", "b") == "ABC"


def test_bifid6_square():
    A = bifid6
    f = lambda i, j: symbols(A[6*i + j])
    M = Matrix(6, 6, f)
    assert bifid6_square("") == M


def test_rsa_public_key():
    assert rsa_public_key(2, 3, 1) == (6, 1)
    assert rsa_public_key(5, 3, 3) == (15, 3)
    assert rsa_public_key(8, 8, 8) is False

    with warns_deprecated_sympy():
        assert rsa_public_key(2, 2, 1) == (4, 1)


def test_rsa_private_key():
    assert rsa_private_key(2, 3, 1) == (6, 1)
    assert rsa_private_key(5, 3, 3) == (15, 3)
    assert rsa_private_key(23,29,5) == (667,493)
    assert rsa_private_key(8, 8, 8) is False

    with warns_deprecated_sympy():
        assert rsa_private_key(2, 2, 1) == (4, 1)


def test_rsa_large_key():
    # Sample from
    # http://www.herongyang.com/Cryptography/JCE-Public-Key-RSA-Private-Public-Key-Pair-Sample.html
    p = int('101565610013301240713207239558950144682174355406589305284428666'\
        '903702505233009')
    q = int('894687191887545488935455605955948413812376003053143521429242133'\
        '12069293984003')
    e = int('65537')
    d = int('893650581832704239530398858744759129594796235440844479456143566'\
        '6999402846577625762582824202269399672579058991442587406384754958587'\
        '400493169361356902030209')
    assert rsa_public_key(p, q, e) == (p*q, e)
    assert rsa_private_key(p, q, e) == (p*q, d)


def test_encipher_rsa():
    puk = rsa_public_key(2, 3, 1)
    assert encipher_rsa(2, puk) == 2
    puk = rsa_public_key(5, 3, 3)
    assert encipher_rsa(2, puk) == 8

    with warns_deprecated_sympy():
        puk = rsa_public_key(2, 2, 1)
        assert encipher_rsa(2, puk) == 2


def test_decipher_rsa():
    prk = rsa_private_key(2, 3, 1)
    assert decipher_rsa(2, prk) == 2
    prk = rsa_private_key(5, 3, 3)
    assert decipher_rsa(8, prk) == 2

    with warns_deprecated_sympy():
        prk = rsa_private_key(2, 2, 1)
        assert decipher_rsa(2, prk) == 2


def test_kid_rsa_public_key():
    assert kid_rsa_public_key(1, 2, 1, 1) == (5, 2)
    assert kid_rsa_public_key(1, 2, 2, 1) == (8, 3)
    assert kid_rsa_public_key(1, 2, 1, 2) == (7, 2)


def test_kid_rsa_private_key():
    assert kid_rsa_private_key(1, 2, 1, 1) == (5, 3)
    assert kid_rsa_private_key(1, 2, 2, 1) == (8, 3)
    assert kid_rsa_private_key(1, 2, 1, 2) == (7, 4)


def test_encipher_kid_rsa():
    assert encipher_kid_rsa(1, (5, 2)) == 2
    assert encipher_kid_rsa(1, (8, 3)) == 3
    assert encipher_kid_rsa(1, (7, 2)) == 2


def test_decipher_kid_rsa():
    assert decipher_kid_rsa(2, (5, 3)) == 1
    assert decipher_kid_rsa(3, (8, 3)) == 1
    assert decipher_kid_rsa(2, (7, 4)) == 1


def test_encode_morse():
    assert encode_morse('ABC') == '.-|-...|-.-.'
    assert encode_morse('SMS ') == '...|--|...||'
    assert encode_morse('SMS\n') == '...|--|...||'
    assert encode_morse('') == ''
    assert encode_morse(' ') == '||'
    assert encode_morse(' ', sep='`') == '``'
    assert encode_morse(' ', sep='``') == '````'
    assert encode_morse('!@#$%^&*()_+') == '-.-.--|.--.-.|...-..-|-.--.|-.--.-|..--.-|.-.-.'


def test_decode_morse():
    assert decode_morse('-.-|.|-.--') == 'KEY'
    assert decode_morse('.-.|..-|-.||') == 'RUN'
    raises(KeyError, lambda: decode_morse('.....----'))


def test_lfsr_sequence():
    raises(TypeError, lambda: lfsr_sequence(1, [1], 1))
    raises(TypeError, lambda: lfsr_sequence([1], 1, 1))
    F = FF(2)
    assert lfsr_sequence([F(1)], [F(1)], 2) == [F(1), F(1)]
    assert lfsr_sequence([F(0)], [F(1)], 2) == [F(1), F(0)]
    F = FF(3)
    assert lfsr_sequence([F(1)], [F(1)], 2) == [F(1), F(1)]
    assert lfsr_sequence([F(0)], [F(2)], 2) == [F(2), F(0)]
    assert lfsr_sequence([F(1)], [F(2)], 2) == [F(2), F(2)]


def test_lfsr_autocorrelation():
    raises(TypeError, lambda: lfsr_autocorrelation(1, 2, 3))
    F = FF(2)
    s = lfsr_sequence([F(1), F(0)], [F(0), F(1)], 5)
    assert lfsr_autocorrelation(s, 2, 0) == 1
    assert lfsr_autocorrelation(s, 2, 1) == -1


def test_lfsr_connection_polynomial():
    F = FF(2)
    x = symbols("x")
    s = lfsr_sequence([F(1), F(0)], [F(0), F(1)], 5)
    assert lfsr_connection_polynomial(s) == x**2 + 1
    s = lfsr_sequence([F(1), F(1)], [F(0), F(1)], 5)
    assert lfsr_connection_polynomial(s) == x**2 + x + 1


def test_elgamal_private_key():
    a, b, _ = elgamal_private_key(digit=100)
    assert isprime(a)
    assert is_primitive_root(b, a)
    assert len(bin(a)) >= 102


def test_elgamal():
    dk = elgamal_private_key(5)
    ek = elgamal_public_key(dk)
    P = ek[0]
    assert P - 1 == decipher_elgamal(encipher_elgamal(P - 1, ek), dk)
    raises(ValueError, lambda: encipher_elgamal(P, dk))
    raises(ValueError, lambda: encipher_elgamal(-1, dk))


def test_dh_private_key():
    p, g, _ = dh_private_key(digit = 100)
    assert isprime(p)
    assert is_primitive_root(g, p)
    assert len(bin(p)) >= 102


def test_dh_public_key():
    p1, g1, a = dh_private_key(digit = 100)
    p2, g2, ga = dh_public_key((p1, g1, a))
    assert p1 == p2
    assert g1 == g2
    assert ga == pow(g1, a, p1)


def test_dh_shared_key():
    prk = dh_private_key(digit = 100)
    p, _, ga = dh_public_key(prk)
    b = randrange(2, p)
    sk = dh_shared_key((p, _, ga), b)
    assert sk == pow(ga, b, p)
    raises(ValueError, lambda: dh_shared_key((1031, 14, 565), 2000))


def test_padded_key():
    assert padded_key('b', 'ab') == 'ba'
    raises(ValueError, lambda: padded_key('ab', 'ace'))
    raises(ValueError, lambda: padded_key('ab', 'abba'))


def test_bifid():
    raises(ValueError, lambda: encipher_bifid('abc', 'b', 'abcde'))
    assert encipher_bifid('abc', 'b', 'abcd') == 'bdb'
    raises(ValueError, lambda: decipher_bifid('bdb', 'b', 'abcde'))
    assert encipher_bifid('bdb', 'b', 'abcd') == 'abc'
    raises(ValueError, lambda: bifid_square('abcde'))
    assert bifid5_square("B") == \
        bifid5_square('BACDEFGHIKLMNOPQRSTUVWXYZ')
    assert bifid6_square('B0') == \
        bifid6_square('B0ACDEFGHIJKLMNOPQRSTUVWXYZ123456789')


def test_encipher_decipher_gm():
    ps = [131, 137, 139, 149, 151, 157, 163, 167,
          173, 179, 181, 191, 193, 197, 199]
    qs = [89, 97, 101, 103, 107, 109, 113, 127,
          131, 137, 139, 149, 151, 157, 47]
    messages = [
        0, 32855, 34303, 14805, 1280, 75859, 38368,
        724, 60356, 51675, 76697, 61854, 18661,
    ]
    for p, q in zip(ps, qs):
        pri = gm_private_key(p, q)
        for msg in messages:
            pub = gm_public_key(p, q)
            enc = encipher_gm(msg, pub)
            dec = decipher_gm(enc, pri)
            assert dec == msg


def test_gm_private_key():
    raises(ValueError, lambda: gm_public_key(13, 15))
    raises(ValueError, lambda: gm_public_key(0, 0))
    raises(ValueError, lambda: gm_public_key(0, 5))
    assert 17, 19 == gm_public_key(17, 19)


def test_gm_public_key():
    assert 323 == gm_public_key(17, 19)[1]
    assert 15  == gm_public_key(3, 5)[1]
    raises(ValueError, lambda: gm_public_key(15, 19))

def test_encipher_decipher_bg():
    ps = [67, 7, 71, 103, 11, 43, 107, 47,
          79, 19, 83, 23, 59, 127, 31]
    qs = qs = [7, 71, 103, 11, 43, 107, 47,
               79, 19, 83, 23, 59, 127, 31, 67]
    messages = [
        0, 328, 343, 148, 1280, 758, 383,
        724, 603, 516, 766, 618, 186,
    ]

    for p, q in zip(ps, qs):
        pri = bg_private_key(p, q)
        for msg in messages:
            pub = bg_public_key(p, q)
            enc = encipher_bg(msg, pub)
            dec = decipher_bg(enc, pri)
            assert dec == msg

def test_bg_private_key():
    raises(ValueError, lambda: bg_private_key(8, 16))
    raises(ValueError, lambda: bg_private_key(8, 8))
    raises(ValueError, lambda: bg_private_key(13, 17))
    assert 23, 31 == bg_private_key(23, 31)

def test_bg_public_key():
    assert 5293 == bg_public_key(67, 79)
    assert 713 == bg_public_key(23, 31)
    raises(ValueError, lambda: bg_private_key(13, 17))
