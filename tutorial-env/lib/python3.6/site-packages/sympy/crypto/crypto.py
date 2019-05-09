# -*- coding: utf-8 -*-

"""
This file contains some classical ciphers and routines
implementing a linear-feedback shift register (LFSR)
and the Diffie-Hellman key exchange.

.. warning::

   This module is intended for educational purposes only. Do not use the
   functions in this module for real cryptographic applications. If you wish
   to encrypt real data, we recommend using something like the `cryptography
   <https://cryptography.io/en/latest/>`_ module.

"""

from __future__ import print_function

from string import whitespace, ascii_uppercase as uppercase, printable

from sympy import nextprime
from sympy.core import Rational, Symbol
from sympy.core.numbers import igcdex, mod_inverse
from sympy.core.compatibility import range
from sympy.matrices import Matrix
from sympy.ntheory import isprime, totient, primitive_root
from sympy.polys.domains import FF
from sympy.polys.polytools import gcd, Poly
from sympy.utilities.misc import filldedent, translate
from sympy.utilities.iterables import uniq
from sympy.utilities.randtest import _randrange, _randint
from sympy.utilities.exceptions import SymPyDeprecationWarning


def AZ(s=None):
    """Return the letters of ``s`` in uppercase. In case more than
    one string is passed, each of them will be processed and a list
    of upper case strings will be returned.

    Examples
    ========

    >>> from sympy.crypto.crypto import AZ
    >>> AZ('Hello, world!')
    'HELLOWORLD'
    >>> AZ('Hello, world!'.split())
    ['HELLO', 'WORLD']

    See Also
    ========
    check_and_join
    """
    if not s:
        return uppercase
    t = type(s) is str
    if t:
        s = [s]
    rv = [check_and_join(i.upper().split(), uppercase, filter=True)
        for i in s]
    if t:
        return rv[0]
    return rv

bifid5 = AZ().replace('J', '')
bifid6 = AZ() + '0123456789'
bifid10 = printable


def padded_key(key, symbols, filter=True):
    """Return a string of the distinct characters of ``symbols`` with
    those of ``key`` appearing first, omitting characters in ``key``
    that are not in ``symbols``. A ValueError is raised if a) there are
    duplicate characters in ``symbols`` or b) there are characters
    in ``key`` that are  not in ``symbols``.

    Examples
    ========

    >>> from sympy.crypto.crypto import padded_key
    >>> padded_key('PUPPY', 'OPQRSTUVWXY')
    'PUYOQRSTVWX'
    >>> padded_key('RSA', 'ARTIST')
    Traceback (most recent call last):
    ...
    ValueError: duplicate characters in symbols: T
    """
    syms = list(uniq(symbols))
    if len(syms) != len(symbols):
        extra = ''.join(sorted(set(
            [i for i in symbols if symbols.count(i) > 1])))
        raise ValueError('duplicate characters in symbols: %s' % extra)
    extra = set(key) - set(syms)
    if extra:
        raise ValueError(
            'characters in key but not symbols: %s' % ''.join(
            sorted(extra)))
    key0 = ''.join(list(uniq(key)))
    return key0 + ''.join([i for i in syms if i not in key0])


def check_and_join(phrase, symbols=None, filter=None):
    """
    Joins characters of `phrase` and if ``symbols`` is given, raises
    an error if any character in ``phrase`` is not in ``symbols``.

    Parameters
    ==========

    phrase:     string or list of strings to be returned as a string
    symbols:    iterable of characters allowed in ``phrase``;
                if ``symbols`` is None, no checking is performed

    Examples
    ========

    >>> from sympy.crypto.crypto import check_and_join
    >>> check_and_join('a phrase')
    'a phrase'
    >>> check_and_join('a phrase'.upper().split())
    'APHRASE'
    >>> check_and_join('a phrase!'.upper().split(), 'ARE', filter=True)
    'ARAE'
    >>> check_and_join('a phrase!'.upper().split(), 'ARE')
    Traceback (most recent call last):
    ...
    ValueError: characters in phrase but not symbols: "!HPS"

    """
    rv = ''.join(''.join(phrase))
    if symbols is not None:
        symbols = check_and_join(symbols)
        missing = ''.join(list(sorted(set(rv) - set(symbols))))
        if missing:
            if not filter:
                raise ValueError(
                    'characters in phrase but not symbols: "%s"' % missing)
            rv = translate(rv, None, missing)
    return rv


def _prep(msg, key, alp, default=None):
    if not alp:
        if not default:
            alp = AZ()
            msg = AZ(msg)
            key = AZ(key)
        else:
            alp = default
    else:
        alp = ''.join(alp)
    key = check_and_join(key, alp, filter=True)
    msg = check_and_join(msg, alp, filter=True)
    return msg, key, alp


def cycle_list(k, n):
    """
    Returns the elements of the list ``range(n)`` shifted to the
    left by ``k`` (so the list starts with ``k`` (mod ``n``)).

    Examples
    ========

    >>> from sympy.crypto.crypto import cycle_list
    >>> cycle_list(3, 10)
    [3, 4, 5, 6, 7, 8, 9, 0, 1, 2]

    """
    k = k % n
    return list(range(k, n)) + list(range(k))


######## shift cipher examples ############


def encipher_shift(msg, key, symbols=None):
    """
    Performs shift cipher encryption on plaintext msg, and returns the
    ciphertext.

    Notes
    =====

    The shift cipher is also called the Caesar cipher, after
    Julius Caesar, who, according to Suetonius, used it with a
    shift of three to protect messages of military significance.
    Caesar's nephew Augustus reportedly used a similar cipher, but
    with a right shift of 1.


    ALGORITHM:

        INPUT:

            ``key``: an integer (the secret key)

            ``msg``: plaintext of upper-case letters

        OUTPUT:

            ``ct``: ciphertext of upper-case letters

        STEPS:
            0. Number the letters of the alphabet from 0, ..., N
            1. Compute from the string ``msg`` a list ``L1`` of
               corresponding integers.
            2. Compute from the list ``L1`` a new list ``L2``, given by
               adding ``(k mod 26)`` to each element in ``L1``.
            3. Compute from the list ``L2`` a string ``ct`` of
               corresponding letters.

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_shift, decipher_shift
    >>> msg = "GONAVYBEATARMY"
    >>> ct = encipher_shift(msg, 1); ct
    'HPOBWZCFBUBSNZ'

    To decipher the shifted text, change the sign of the key:

    >>> encipher_shift(ct, -1)
    'GONAVYBEATARMY'

    There is also a convenience function that does this with the
    original key:

    >>> decipher_shift(ct, 1)
    'GONAVYBEATARMY'
    """
    msg, _, A = _prep(msg, '', symbols)
    shift = len(A) - key % len(A)
    key = A[shift:] + A[:shift]
    return translate(msg, key, A)


def decipher_shift(msg, key, symbols=None):
    """
    Return the text by shifting the characters of ``msg`` to the
    left by the amount given by ``key``.

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_shift, decipher_shift
    >>> msg = "GONAVYBEATARMY"
    >>> ct = encipher_shift(msg, 1); ct
    'HPOBWZCFBUBSNZ'

    To decipher the shifted text, change the sign of the key:

    >>> encipher_shift(ct, -1)
    'GONAVYBEATARMY'

    Or use this function with the original key:

    >>> decipher_shift(ct, 1)
    'GONAVYBEATARMY'
    """
    return encipher_shift(msg, -key, symbols)


######## affine cipher examples ############


def encipher_affine(msg, key, symbols=None, _inverse=False):
    r"""
    Performs the affine cipher encryption on plaintext ``msg``, and
    returns the ciphertext.

    Encryption is based on the map `x \rightarrow ax+b` (mod `N`)
    where ``N`` is the number of characters in the alphabet.
    Decryption is based on the map `x \rightarrow cx+d` (mod `N`),
    where `c = a^{-1}` (mod `N`) and `d = -a^{-1}b` (mod `N`).
    In particular, for the map to be invertible, we need
    `\mathrm{gcd}(a, N) = 1` and an error will be raised if this is
    not true.

    Notes
    =====

    This is a straightforward generalization of the shift cipher with
    the added complexity of requiring 2 characters to be deciphered in
    order to recover the key.

    ALGORITHM:

        INPUT:

            ``msg``: string of characters that appear in ``symbols``

            ``a, b``: a pair integers, with ``gcd(a, N) = 1``
            (the secret key)

            ``symbols``: string of characters (default = uppercase
            letters). When no symbols are given, ``msg`` is converted
            to upper case letters and all other charactes are ignored.

        OUTPUT:

            ``ct``: string of characters (the ciphertext message)

        STEPS:
            0. Number the letters of the alphabet from 0, ..., N
            1. Compute from the string ``msg`` a list ``L1`` of
               corresponding integers.
            2. Compute from the list ``L1`` a new list ``L2``, given by
               replacing ``x`` by ``a*x + b (mod N)``, for each element
               ``x`` in ``L1``.
            3. Compute from the list ``L2`` a string ``ct`` of
               corresponding letters.

    See Also
    ========
    decipher_affine

    """
    msg, _, A = _prep(msg, '', symbols)
    N = len(A)
    a, b = key
    assert gcd(a, N) == 1
    if _inverse:
        c = mod_inverse(a, N)
        d = -b*c
        a, b = c, d
    B = ''.join([A[(a*i + b) % N] for i in range(N)])
    return translate(msg, A, B)


def decipher_affine(msg, key, symbols=None):
    r"""
    Return the deciphered text that was made from the mapping,
    `x \rightarrow ax+b` (mod `N`), where ``N`` is the
    number of characters in the alphabet. Deciphering is done by
    reciphering with a new key: `x \rightarrow cx+d` (mod `N`),
    where `c = a^{-1}` (mod `N`) and `d = -a^{-1}b` (mod `N`).

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_affine, decipher_affine
    >>> msg = "GO NAVY BEAT ARMY"
    >>> key = (3, 1)
    >>> encipher_affine(msg, key)
    'TROBMVENBGBALV'
    >>> decipher_affine(_, key)
    'GONAVYBEATARMY'

    """
    return encipher_affine(msg, key, symbols, _inverse=True)


#################### substitution cipher ###########################


def encipher_substitution(msg, old, new=None):
    r"""
    Returns the ciphertext obtained by replacing each character that
    appears in ``old`` with the corresponding character in ``new``.
    If ``old`` is a mapping, then new is ignored and the replacements
    defined by ``old`` are used.

    Notes
    =====

    This is a more general than the affine cipher in that the key can
    only be recovered by determining the mapping for each symbol.
    Though in practice, once a few symbols are recognized the mappings
    for other characters can be quickly guessed.

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_substitution, AZ
    >>> old = 'OEYAG'
    >>> new = '034^6'
    >>> msg = AZ("go navy! beat army!")
    >>> ct = encipher_substitution(msg, old, new); ct
    '60N^V4B3^T^RM4'

    To decrypt a substitution, reverse the last two arguments:

    >>> encipher_substitution(ct, new, old)
    'GONAVYBEATARMY'

    In the special case where ``old`` and ``new`` are a permutation of
    order 2 (representing a transposition of characters) their order
    is immaterial:

    >>> old = 'NAVY'
    >>> new = 'ANYV'
    >>> encipher = lambda x: encipher_substitution(x, old, new)
    >>> encipher('NAVY')
    'ANYV'
    >>> encipher(_)
    'NAVY'

    The substitution cipher, in general, is a method
    whereby "units" (not necessarily single characters) of plaintext
    are replaced with ciphertext according to a regular system.

    >>> ords = dict(zip('abc', ['\\%i' % ord(i) for i in 'abc']))
    >>> print(encipher_substitution('abc', ords))
    \97\98\99
    """
    return translate(msg, old, new)


######################################################################
#################### Vigenère cipher examples ########################
######################################################################

def encipher_vigenere(msg, key, symbols=None):
    """
    Performs the Vigenère cipher encryption on plaintext ``msg``, and
    returns the ciphertext.

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_vigenere, AZ
    >>> key = "encrypt"
    >>> msg = "meet me on monday"
    >>> encipher_vigenere(msg, key)
    'QRGKKTHRZQEBPR'

    Section 1 of the Kryptos sculpture at the CIA headquarters
    uses this cipher and also changes the order of the the
    alphabet [2]_. Here is the first line of that section of
    the sculpture:

    >>> from sympy.crypto.crypto import decipher_vigenere, padded_key
    >>> alp = padded_key('KRYPTOS', AZ())
    >>> key = 'PALIMPSEST'
    >>> msg = 'EMUFPHZLRFAXYUSDJKZLDKRNSHGNFIVJ'
    >>> decipher_vigenere(msg, key, alp)
    'BETWEENSUBTLESHADINGANDTHEABSENC'

    Notes
    =====

    The Vigenère cipher is named after Blaise de Vigenère, a sixteenth
    century diplomat and cryptographer, by a historical accident.
    Vigenère actually invented a different and more complicated cipher.
    The so-called *Vigenère cipher* was actually invented
    by Giovan Batista Belaso in 1553.

    This cipher was used in the 1800's, for example, during the American
    Civil War. The Confederacy used a brass cipher disk to implement the
    Vigenère cipher (now on display in the NSA Museum in Fort
    Meade) [1]_.

    The Vigenère cipher is a generalization of the shift cipher.
    Whereas the shift cipher shifts each letter by the same amount
    (that amount being the key of the shift cipher) the Vigenère
    cipher shifts a letter by an amount determined by the key (which is
    a word or phrase known only to the sender and receiver).

    For example, if the key was a single letter, such as "C", then the
    so-called Vigenere cipher is actually a shift cipher with a
    shift of `2` (since "C" is the 2nd letter of the alphabet, if
    you start counting at `0`). If the key was a word with two
    letters, such as "CA", then the so-called Vigenère cipher will
    shift letters in even positions by `2` and letters in odd positions
    are left alone (shifted by `0`, since "A" is the 0th letter, if
    you start counting at `0`).


    ALGORITHM:

        INPUT:

            ``msg``: string of characters that appear in ``symbols``
            (the plaintext)

            ``key``: a string of characters that appear in ``symbols``
            (the secret key)

            ``symbols``: a string of letters defining the alphabet


        OUTPUT:

            ``ct``: string of characters (the ciphertext message)

        STEPS:
            0. Number the letters of the alphabet from 0, ..., N
            1. Compute from the string ``key`` a list ``L1`` of
               corresponding integers. Let ``n1 = len(L1)``.
            2. Compute from the string ``msg`` a list ``L2`` of
               corresponding integers. Let ``n2 = len(L2)``.
            3. Break ``L2`` up sequentially into sublists of size
               ``n1``; the last sublist may be smaller than ``n1``
            4. For each of these sublists ``L`` of ``L2``, compute a
               new list ``C`` given by ``C[i] = L[i] + L1[i] (mod N)``
               to the ``i``-th element in the sublist, for each ``i``.
            5. Assemble these lists ``C`` by concatenation into a new
               list of length ``n2``.
            6. Compute from the new list a string ``ct`` of
               corresponding letters.

    Once it is known that the key is, say, `n` characters long,
    frequency analysis can be applied to every `n`-th letter of
    the ciphertext to determine the plaintext. This method is
    called *Kasiski examination* (although it was first discovered
    by Babbage). If they key is as long as the message and is
    comprised of randomly selected characters -- a one-time pad -- the
    message is theoretically unbreakable.

    The cipher Vigenère actually discovered is an "auto-key" cipher
    described as follows.

    ALGORITHM:

        INPUT:

          ``key``: a string of letters (the secret key)

          ``msg``: string of letters (the plaintext message)

        OUTPUT:

          ``ct``: string of upper-case letters (the ciphertext message)

        STEPS:
            0. Number the letters of the alphabet from 0, ..., N
            1. Compute from the string ``msg`` a list ``L2`` of
               corresponding integers. Let ``n2 = len(L2)``.
            2. Let ``n1`` be the length of the key. Append to the
               string ``key`` the first ``n2 - n1`` characters of
               the plaintext message. Compute from this string (also of
               length ``n2``) a list ``L1`` of integers corresponding
               to the letter numbers in the first step.
            3. Compute a new list ``C`` given by
               ``C[i] = L1[i] + L2[i] (mod N)``.
            4. Compute from the new list a string ``ct`` of letters
               corresponding to the new integers.

    To decipher the auto-key ciphertext, the key is used to decipher
    the first ``n1`` characters and then those characters become the
    key to  decipher the next ``n1`` characters, etc...:

    >>> m = AZ('go navy, beat army! yes you can'); m
    'GONAVYBEATARMYYESYOUCAN'
    >>> key = AZ('gold bug'); n1 = len(key); n2 = len(m)
    >>> auto_key = key + m[:n2 - n1]; auto_key
    'GOLDBUGGONAVYBEATARMYYE'
    >>> ct = encipher_vigenere(m, auto_key); ct
    'MCYDWSHKOGAMKZCELYFGAYR'
    >>> n1 = len(key)
    >>> pt = []
    >>> while ct:
    ...     part, ct = ct[:n1], ct[n1:]
    ...     pt.append(decipher_vigenere(part, key))
    ...     key = pt[-1]
    ...
    >>> ''.join(pt) == m
    True

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Vigenere_cipher
    .. [2] http://web.archive.org/web/20071116100808/
       http://filebox.vt.edu/users/batman/kryptos.html
       (short URL: https://goo.gl/ijr22d)

    """
    msg, key, A = _prep(msg, key, symbols)
    map = {c: i for i, c in enumerate(A)}
    key = [map[c] for c in key]
    N = len(map)
    k = len(key)
    rv = []
    for i, m in enumerate(msg):
        rv.append(A[(map[m] + key[i % k]) % N])
    rv = ''.join(rv)
    return rv


def decipher_vigenere(msg, key, symbols=None):
    """
    Decode using the Vigenère cipher.

    Examples
    ========

    >>> from sympy.crypto.crypto import decipher_vigenere
    >>> key = "encrypt"
    >>> ct = "QRGK kt HRZQE BPR"
    >>> decipher_vigenere(ct, key)
    'MEETMEONMONDAY'
    """
    msg, key, A = _prep(msg, key, symbols)
    map = {c: i for i, c in enumerate(A)}
    N = len(A)   # normally, 26
    K = [map[c] for c in key]
    n = len(K)
    C = [map[c] for c in msg]
    rv = ''.join([A[(-K[i % n] + c) % N] for i, c in enumerate(C)])
    return rv


#################### Hill cipher  ########################


def encipher_hill(msg, key, symbols=None, pad="Q"):
    r"""
    Return the Hill cipher encryption of ``msg``.

    Notes
    =====

    The Hill cipher [1]_, invented by Lester S. Hill in the 1920's [2]_,
    was the first polygraphic cipher in which it was practical
    (though barely) to operate on more than three symbols at once.
    The following discussion assumes an elementary knowledge of
    matrices.

    First, each letter is first encoded as a number starting with 0.
    Suppose your message `msg` consists of `n` capital letters, with no
    spaces. This may be regarded an `n`-tuple M of elements of
    `Z_{26}` (if the letters are those of the English alphabet). A key
    in the Hill cipher is a `k x k` matrix `K`, all of whose entries
    are in `Z_{26}`, such that the matrix `K` is invertible (i.e., the
    linear transformation `K: Z_{N}^k \rightarrow Z_{N}^k`
    is one-to-one).

    ALGORITHM:

        INPUT:

            ``msg``: plaintext message of `n` upper-case letters

            ``key``: a `k x k` invertible matrix `K`, all of whose
            entries are in `Z_{26}` (or whatever number of symbols
            are being used).

            ``pad``: character (default "Q") to use to make length
            of text be a multiple of ``k``

        OUTPUT:

            ``ct``: ciphertext of upper-case letters

        STEPS:
            0. Number the letters of the alphabet from 0, ..., N
            1. Compute from the string ``msg`` a list ``L`` of
               corresponding integers. Let ``n = len(L)``.
            2. Break the list ``L`` up into ``t = ceiling(n/k)``
               sublists ``L_1``, ..., ``L_t`` of size ``k`` (with
               the last list "padded" to ensure its size is
               ``k``).
            3. Compute new list ``C_1``, ..., ``C_t`` given by
               ``C[i] = K*L_i`` (arithmetic is done mod N), for each
               ``i``.
            4. Concatenate these into a list ``C = C_1 + ... + C_t``.
            5. Compute from ``C`` a string ``ct`` of corresponding
               letters. This has length ``k*t``.

    References
    ==========

    .. [1] en.wikipedia.org/wiki/Hill_cipher
    .. [2] Lester S. Hill, Cryptography in an Algebraic Alphabet,
       The American Mathematical Monthly Vol.36, June-July 1929,
       pp.306-312.

    See Also
    ========
    decipher_hill

    """
    assert key.is_square
    assert len(pad) == 1
    msg, pad, A = _prep(msg, pad, symbols)
    map = {c: i for i, c in enumerate(A)}
    P = [map[c] for c in msg]
    N = len(A)
    k = key.cols
    n = len(P)
    m, r = divmod(n, k)
    if r:
        P = P + [map[pad]]*(k - r)
        m += 1
    rv = ''.join([A[c % N] for j in range(m) for c in
        list(key*Matrix(k, 1, [P[i]
        for i in range(k*j, k*(j + 1))]))])
    return rv


def decipher_hill(msg, key, symbols=None):
    """
    Deciphering is the same as enciphering but using the inverse of the
    key matrix.

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_hill, decipher_hill
    >>> from sympy import Matrix

    >>> key = Matrix([[1, 2], [3, 5]])
    >>> encipher_hill("meet me on monday", key)
    'UEQDUEODOCTCWQ'
    >>> decipher_hill(_, key)
    'MEETMEONMONDAY'

    When the length of the plaintext (stripped of invalid characters)
    is not a multiple of the key dimension, extra characters will
    appear at the end of the enciphered and deciphered text. In order to
    decipher the text, those characters must be included in the text to
    be deciphered. In the following, the key has a dimension of 4 but
    the text is 2 short of being a multiple of 4 so two characters will
    be added.

    >>> key = Matrix([[1, 1, 1, 2], [0, 1, 1, 0],
    ...               [2, 2, 3, 4], [1, 1, 0, 1]])
    >>> msg = "ST"
    >>> encipher_hill(msg, key)
    'HJEB'
    >>> decipher_hill(_, key)
    'STQQ'
    >>> encipher_hill(msg, key, pad="Z")
    'ISPK'
    >>> decipher_hill(_, key)
    'STZZ'

    If the last two characters of the ciphertext were ignored in
    either case, the wrong plaintext would be recovered:

    >>> decipher_hill("HD", key)
    'ORMV'
    >>> decipher_hill("IS", key)
    'UIKY'

    """
    assert key.is_square
    msg, _, A = _prep(msg, '', symbols)
    map = {c: i for i, c in enumerate(A)}
    C = [map[c] for c in msg]
    N = len(A)
    k = key.cols
    n = len(C)
    m, r = divmod(n, k)
    if r:
        C = C + [0]*(k - r)
        m += 1
    key_inv = key.inv_mod(N)
    rv = ''.join([A[p % N] for j in range(m) for p in
        list(key_inv*Matrix(
        k, 1, [C[i] for i in range(k*j, k*(j + 1))]))])
    return rv


#################### Bifid cipher  ########################


def encipher_bifid(msg, key, symbols=None):
    r"""
    Performs the Bifid cipher encryption on plaintext ``msg``, and
    returns the ciphertext.

    This is the version of the Bifid cipher that uses an `n \times n`
    Polybius square.

        INPUT:

            ``msg``: plaintext string

            ``key``: short string for key; duplicate characters are
            ignored and then it is padded with the characters in
            ``symbols`` that were not in the short key

            ``symbols``: `n \times n` characters defining the alphabet
            (default is string.printable)

        OUTPUT:

            ciphertext (using Bifid5 cipher without spaces)

    See Also
    ========
    decipher_bifid, encipher_bifid5, encipher_bifid6

    """
    msg, key, A = _prep(msg, key, symbols, bifid10)
    long_key = ''.join(uniq(key)) or A

    n = len(A)**.5
    if n != int(n):
        raise ValueError(
            'Length of alphabet (%s) is not a square number.' % len(A))
    N = int(n)
    if len(long_key) < N**2:
      long_key = list(long_key) + [x for x in A if x not in long_key]

    # the fractionalization
    row_col = {ch: divmod(i, N) for i, ch in enumerate(long_key)}
    r, c = zip(*[row_col[x] for x in msg])
    rc = r + c
    ch = {i: ch for ch, i in row_col.items()}
    rv = ''.join((ch[i] for i in zip(rc[::2], rc[1::2])))
    return rv


def decipher_bifid(msg, key, symbols=None):
    r"""
    Performs the Bifid cipher decryption on ciphertext ``msg``, and
    returns the plaintext.

    This is the version of the Bifid cipher that uses the `n \times n`
    Polybius square.

        INPUT:

            ``msg``: ciphertext string

            ``key``: short string for key; duplicate characters are
            ignored and then it is padded with the characters in
            ``symbols`` that were not in the short key

            ``symbols``: `n \times n` characters defining the alphabet
            (default=string.printable, a `10 \times 10` matrix)

        OUTPUT:

            deciphered text

    Examples
    ========

    >>> from sympy.crypto.crypto import (
    ...     encipher_bifid, decipher_bifid, AZ)

    Do an encryption using the bifid5 alphabet:

    >>> alp = AZ().replace('J', '')
    >>> ct = AZ("meet me on monday!")
    >>> key = AZ("gold bug")
    >>> encipher_bifid(ct, key, alp)
    'IEILHHFSTSFQYE'

    When entering the text or ciphertext, spaces are ignored so it
    can be formatted as desired. Re-entering the ciphertext from the
    preceding, putting 4 characters per line and padding with an extra
    J, does not cause problems for the deciphering:

    >>> decipher_bifid('''
    ... IEILH
    ... HFSTS
    ... FQYEJ''', key, alp)
    'MEETMEONMONDAY'

    When no alphabet is given, all 100 printable characters will be
    used:

    >>> key = ''
    >>> encipher_bifid('hello world!', key)
    'bmtwmg-bIo*w'
    >>> decipher_bifid(_, key)
    'hello world!'

    If the key is changed, a different encryption is obtained:

    >>> key = 'gold bug'
    >>> encipher_bifid('hello world!', 'gold_bug')
    'hg2sfuei7t}w'

    And if the key used to decrypt the message is not exact, the
    original text will not be perfectly obtained:

    >>> decipher_bifid(_, 'gold pug')
    'heldo~wor6d!'

    """
    msg, _, A = _prep(msg, '', symbols, bifid10)
    long_key = ''.join(uniq(key)) or A

    n = len(A)**.5
    if n != int(n):
        raise ValueError(
            'Length of alphabet (%s) is not a square number.' % len(A))
    N = int(n)
    if len(long_key) < N**2:
        long_key = list(long_key) + [x for x in A if x not in long_key]

    # the reverse fractionalization
    row_col = dict(
        [(ch, divmod(i, N)) for i, ch in enumerate(long_key)])
    rc = [i for c in msg for i in row_col[c]]
    n = len(msg)
    rc = zip(*(rc[:n], rc[n:]))
    ch = {i: ch for ch, i in row_col.items()}
    rv = ''.join((ch[i] for i in rc))
    return rv


def bifid_square(key):
    """Return characters of ``key`` arranged in a square.

    Examples
    ========

    >>> from sympy.crypto.crypto import (
    ...    bifid_square, AZ, padded_key, bifid5)
    >>> bifid_square(AZ().replace('J', ''))
    Matrix([
    [A, B, C, D, E],
    [F, G, H, I, K],
    [L, M, N, O, P],
    [Q, R, S, T, U],
    [V, W, X, Y, Z]])

    >>> bifid_square(padded_key(AZ('gold bug!'), bifid5))
    Matrix([
    [G, O, L, D, B],
    [U, A, C, E, F],
    [H, I, K, M, N],
    [P, Q, R, S, T],
    [V, W, X, Y, Z]])

    See Also
    ========
    padded_key
    """
    A = ''.join(uniq(''.join(key)))
    n = len(A)**.5
    if n != int(n):
        raise ValueError(
            'Length of alphabet (%s) is not a square number.' % len(A))
    n = int(n)
    f = lambda i, j: Symbol(A[n*i + j])
    rv = Matrix(n, n, f)
    return rv


def encipher_bifid5(msg, key):
    r"""
    Performs the Bifid cipher encryption on plaintext ``msg``, and
    returns the ciphertext.

    This is the version of the Bifid cipher that uses the `5 \times 5`
    Polybius square. The letter "J" is ignored so it must be replaced
    with something else (traditionally an "I") before encryption.

    Notes
    =====

    The Bifid cipher was invented around 1901 by Felix Delastelle.
    It is a *fractional substitution* cipher, where letters are
    replaced by pairs of symbols from a smaller alphabet. The
    cipher uses a `5 \times 5` square filled with some ordering of the
    alphabet, except that "J" is replaced with "I" (this is a so-called
    Polybius square; there is a `6 \times 6` analog if you add back in
    "J" and also append onto the usual 26 letter alphabet, the digits
    0, 1, ..., 9).
    According to Helen Gaines' book *Cryptanalysis*, this type of cipher
    was used in the field by the German Army during World War I.

    ALGORITHM: (5x5 case)

        INPUT:

            ``msg``: plaintext string; converted to upper case and
            filtered of anything but all letters except J.

            ``key``: short string for key; non-alphabetic letters, J
            and duplicated characters are ignored and then, if the
            length is less than 25 characters, it is padded with other
            letters of the alphabet (in alphabetical order).

        OUTPUT:

            ciphertext (all caps, no spaces)

        STEPS:
            0. Create the `5 \times 5` Polybius square ``S`` associated
               to ``key`` as follows:

                a) moving from left-to-right, top-to-bottom,
                   place the letters of the key into a `5 \times 5`
                   matrix,
                b) if the key has less than 25 letters, add the
                   letters of the alphabet not in the key until the
                   `5 \times 5` square is filled.

            1. Create a list ``P`` of pairs of numbers which are the
               coordinates in the Polybius square of the letters in
               ``msg``.
            2. Let ``L1`` be the list of all first coordinates of ``P``
               (length of ``L1 = n``), let ``L2`` be the list of all
               second coordinates of ``P`` (so the length of ``L2``
               is also ``n``).
            3. Let ``L`` be the concatenation of ``L1`` and ``L2``
               (length ``L = 2*n``), except that consecutive numbers
               are paired ``(L[2*i], L[2*i + 1])``. You can regard
               ``L`` as a list of pairs of length ``n``.
            4. Let ``C`` be the list of all letters which are of the
               form ``S[i, j]``, for all ``(i, j)`` in ``L``. As a
               string, this is the ciphertext of ``msg``.

    Examples
    ========

    >>> from sympy.crypto.crypto import (
    ...     encipher_bifid5, decipher_bifid5)

    "J" will be omitted unless it is replaced with something else:

    >>> round_trip = lambda m, k: \
    ...     decipher_bifid5(encipher_bifid5(m, k), k)
    >>> key = 'a'
    >>> msg = "JOSIE"
    >>> round_trip(msg, key)
    'OSIE'
    >>> round_trip(msg.replace("J", "I"), key)
    'IOSIE'
    >>> j = "QIQ"
    >>> round_trip(msg.replace("J", j), key).replace(j, "J")
    'JOSIE'

    See Also
    ========
    decipher_bifid5, encipher_bifid

    """
    msg, key, _ = _prep(msg.upper(), key.upper(), None, bifid5)
    key = padded_key(key, bifid5)
    return encipher_bifid(msg, '', key)


def decipher_bifid5(msg, key):
    r"""
    Return the Bifid cipher decryption of ``msg``.

    This is the version of the Bifid cipher that uses the `5 \times 5`
    Polybius square; the letter "J" is ignored unless a ``key`` of
    length 25 is used.

    INPUT:

        ``msg``: ciphertext string

        ``key``: short string for key; duplicated characters are
        ignored and if the length is less then 25 characters, it
        will be padded with other letters from the alphabet omitting
        "J". Non-alphabetic characters are ignored.

    OUTPUT:

        plaintext from Bifid5 cipher (all caps, no spaces)

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_bifid5, decipher_bifid5
    >>> key = "gold bug"
    >>> encipher_bifid5('meet me on friday', key)
    'IEILEHFSTSFXEE'
    >>> encipher_bifid5('meet me on monday', key)
    'IEILHHFSTSFQYE'
    >>> decipher_bifid5(_, key)
    'MEETMEONMONDAY'

    """
    msg, key, _ = _prep(msg.upper(), key.upper(), None, bifid5)
    key = padded_key(key, bifid5)
    return decipher_bifid(msg, '', key)


def bifid5_square(key=None):
    r"""
    5x5 Polybius square.

    Produce the Polybius square for the `5 \times 5` Bifid cipher.

    Examples
    ========

    >>> from sympy.crypto.crypto import bifid5_square
    >>> bifid5_square("gold bug")
    Matrix([
    [G, O, L, D, B],
    [U, A, C, E, F],
    [H, I, K, M, N],
    [P, Q, R, S, T],
    [V, W, X, Y, Z]])

    """
    if not key:
        key = bifid5
    else:
        _, key, _ = _prep('', key.upper(), None, bifid5)
        key = padded_key(key, bifid5)
    return bifid_square(key)


def encipher_bifid6(msg, key):
    r"""
    Performs the Bifid cipher encryption on plaintext ``msg``, and
    returns the ciphertext.

    This is the version of the Bifid cipher that uses the `6 \times 6`
    Polybius square.

    INPUT:

        ``msg``: plaintext string (digits okay)

        ``key``: short string for key (digits okay). If ``key`` is
        less than 36 characters long, the square will be filled with
        letters A through Z and digits 0 through 9.

    OUTPUT:

        ciphertext from Bifid cipher (all caps, no spaces)

    See Also
    ========
    decipher_bifid6, encipher_bifid

    """
    msg, key, _ = _prep(msg.upper(), key.upper(), None, bifid6)
    key = padded_key(key, bifid6)
    return encipher_bifid(msg, '', key)


def decipher_bifid6(msg, key):
    r"""
    Performs the Bifid cipher decryption on ciphertext ``msg``, and
    returns the plaintext.

    This is the version of the Bifid cipher that uses the `6 \times 6`
    Polybius square.

    INPUT:

        ``msg``: ciphertext string (digits okay); converted to upper case

        ``key``: short string for key (digits okay). If ``key`` is
        less than 36 characters long, the square will be filled with
        letters A through Z and digits 0 through 9. All letters are
        converted to uppercase.

    OUTPUT:

        plaintext from Bifid cipher (all caps, no spaces)

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_bifid6, decipher_bifid6
    >>> key = "gold bug"
    >>> encipher_bifid6('meet me on monday at 8am', key)
    'KFKLJJHF5MMMKTFRGPL'
    >>> decipher_bifid6(_, key)
    'MEETMEONMONDAYAT8AM'

    """
    msg, key, _ = _prep(msg.upper(), key.upper(), None, bifid6)
    key = padded_key(key, bifid6)
    return decipher_bifid(msg, '', key)


def bifid6_square(key=None):
    r"""
    6x6 Polybius square.

    Produces the Polybius square for the `6 \times 6` Bifid cipher.
    Assumes alphabet of symbols is "A", ..., "Z", "0", ..., "9".

    Examples
    ========

    >>> from sympy.crypto.crypto import bifid6_square
    >>> key = "gold bug"
    >>> bifid6_square(key)
    Matrix([
    [G, O, L, D, B, U],
    [A, C, E, F, H, I],
    [J, K, M, N, P, Q],
    [R, S, T, V, W, X],
    [Y, Z, 0, 1, 2, 3],
    [4, 5, 6, 7, 8, 9]])
    """
    if not key:
        key = bifid6
    else:
        _, key, _ = _prep('', key.upper(), None, bifid6)
        key = padded_key(key, bifid6)
    return bifid_square(key)


#################### RSA  #############################


def rsa_public_key(p, q, e):
    r"""
    Return the RSA *public key* pair, `(n, e)`, where `n`
    is a product of two primes and `e` is relatively
    prime (coprime) to the Euler totient `\phi(n)`. False
    is returned if any assumption is violated.

    Examples
    ========

    >>> from sympy.crypto.crypto import rsa_public_key
    >>> p, q, e = 3, 5, 7
    >>> rsa_public_key(p, q, e)
    (15, 7)
    >>> rsa_public_key(p, q, 30)
    False

    """
    n = p*q
    if isprime(p) and isprime(q):
        if p == q:
            SymPyDeprecationWarning(
                feature="Using non-distinct primes for rsa_public_key",
                useinstead="distinct primes",
                issue=16162,
                deprecated_since_version="1.4").warn()
            phi = p * (p - 1)
        else:
            phi = (p - 1) * (q - 1)
        if gcd(e, phi) == 1:
            return n, e
    return False


def rsa_private_key(p, q, e):
    r"""
    Return the RSA *private key*, `(n,d)`, where `n`
    is a product of two primes and `d` is the inverse of
    `e` (mod `\phi(n)`). False is returned if any assumption
    is violated.

    Examples
    ========

    >>> from sympy.crypto.crypto import rsa_private_key
    >>> p, q, e = 3, 5, 7
    >>> rsa_private_key(p, q, e)
    (15, 7)
    >>> rsa_private_key(p, q, 30)
    False
    """
    n = p*q
    if isprime(p) and isprime(q):
        if p == q:
            SymPyDeprecationWarning(
                feature="Using non-distinct primes for rsa_public_key",
                useinstead="distinct primes",
                issue=16162,
                deprecated_since_version="1.4").warn()
            phi = p * (p - 1)
        else:
            phi = (p - 1) * (q - 1)
        if gcd(e, phi) == 1:
            d = mod_inverse(e, phi)
            return n, d
    return False


def encipher_rsa(i, key):
    """
    Return encryption of ``i`` by computing `i^e` (mod `n`),
    where ``key`` is the public key `(n, e)`.

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_rsa, rsa_public_key
    >>> p, q, e = 3, 5, 7
    >>> puk = rsa_public_key(p, q, e)
    >>> msg = 12
    >>> encipher_rsa(msg, puk)
    3

    """
    n, e = key
    return pow(i, e, n)


def decipher_rsa(i, key):
    """
    Return decyption of ``i`` by computing `i^d` (mod `n`),
    where ``key`` is the private key `(n, d)`.

    Examples
    ========

    >>> from sympy.crypto.crypto import decipher_rsa, rsa_private_key
    >>> p, q, e = 3, 5, 7
    >>> prk = rsa_private_key(p, q, e)
    >>> msg = 3
    >>> decipher_rsa(msg, prk)
    12

    """
    n, d = key
    return pow(i, d, n)


#################### kid krypto (kid RSA) #############################


def kid_rsa_public_key(a, b, A, B):
    r"""
    Kid RSA is a version of RSA useful to teach grade school children
    since it does not involve exponentiation.

    Alice wants to talk to Bob. Bob generates keys as follows.
    Key generation:

    * Select positive integers `a, b, A, B` at random.
    * Compute `M = a b - 1`, `e = A M + a`, `d = B M + b`,
      `n = (e d - 1)//M`.
    * The *public key* is `(n, e)`. Bob sends these to Alice.
    * The *private key* is `(n, d)`, which Bob keeps secret.

    Encryption: If `p` is the plaintext message then the
    ciphertext is `c = p e \pmod n`.

    Decryption: If `c` is the ciphertext message then the
    plaintext is `p = c d \pmod n`.

    Examples
    ========

    >>> from sympy.crypto.crypto import kid_rsa_public_key
    >>> a, b, A, B = 3, 4, 5, 6
    >>> kid_rsa_public_key(a, b, A, B)
    (369, 58)

    """
    M = a*b - 1
    e = A*M + a
    d = B*M + b
    n = (e*d - 1)//M
    return n, e


def kid_rsa_private_key(a, b, A, B):
    """
    Compute `M = a b - 1`, `e = A M + a`, `d = B M + b`,
    `n = (e d - 1) / M`. The *private key* is `d`, which Bob
    keeps secret.

    Examples
    ========

    >>> from sympy.crypto.crypto import kid_rsa_private_key
    >>> a, b, A, B = 3, 4, 5, 6
    >>> kid_rsa_private_key(a, b, A, B)
    (369, 70)

    """
    M = a*b - 1
    e = A*M + a
    d = B*M + b
    n = (e*d - 1)//M
    return n, d


def encipher_kid_rsa(msg, key):
    """
    Here ``msg`` is the plaintext and ``key`` is the public key.

    Examples
    ========

    >>> from sympy.crypto.crypto import (
    ...     encipher_kid_rsa, kid_rsa_public_key)
    >>> msg = 200
    >>> a, b, A, B = 3, 4, 5, 6
    >>> key = kid_rsa_public_key(a, b, A, B)
    >>> encipher_kid_rsa(msg, key)
    161

    """
    n, e = key
    return (msg*e) % n


def decipher_kid_rsa(msg, key):
    """
    Here ``msg`` is the plaintext and ``key`` is the private key.

    Examples
    ========

    >>> from sympy.crypto.crypto import (
    ...     kid_rsa_public_key, kid_rsa_private_key,
    ...     decipher_kid_rsa, encipher_kid_rsa)
    >>> a, b, A, B = 3, 4, 5, 6
    >>> d = kid_rsa_private_key(a, b, A, B)
    >>> msg = 200
    >>> pub = kid_rsa_public_key(a, b, A, B)
    >>> pri = kid_rsa_private_key(a, b, A, B)
    >>> ct = encipher_kid_rsa(msg, pub)
    >>> decipher_kid_rsa(ct, pri)
    200

    """
    n, d = key
    return (msg*d) % n


#################### Morse Code ######################################

morse_char = {
    ".-": "A", "-...": "B",
    "-.-.": "C", "-..": "D",
    ".": "E", "..-.": "F",
    "--.": "G", "....": "H",
    "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N",
    "---": "O", ".--.": "P",
    "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T",
    "..-": "U", "...-": "V",
    ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",
    "-----": "0", "----": "1",
    "..---": "2", "...--": "3",
    "....-": "4", ".....": "5",
    "-....": "6", "--...": "7",
    "---..": "8", "----.": "9",
    ".-.-.-": ".", "--..--": ",",
    "---...": ":", "-.-.-.": ";",
    "..--..": "?", "-....-": "-",
    "..--.-": "_", "-.--.": "(",
    "-.--.-": ")", ".----.": "'",
    "-...-": "=", ".-.-.": "+",
    "-..-.": "/", ".--.-.": "@",
    "...-..-": "$", "-.-.--": "!"}
char_morse = {v: k for k, v in morse_char.items()}


def encode_morse(msg, sep='|', mapping=None):
    """
    Encodes a plaintext into popular Morse Code with letters
    separated by `sep` and words by a double `sep`.

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Morse_code

    Examples
    ========

    >>> from sympy.crypto.crypto import encode_morse
    >>> msg = 'ATTACK RIGHT FLANK'
    >>> encode_morse(msg)
    '.-|-|-|.-|-.-.|-.-||.-.|..|--.|....|-||..-.|.-..|.-|-.|-.-'

    """

    mapping = mapping or char_morse
    assert sep not in mapping
    word_sep = 2*sep
    mapping[" "] = word_sep
    suffix = msg and msg[-1] in whitespace

    # normalize whitespace
    msg = (' ' if word_sep else '').join(msg.split())
    # omit unmapped chars
    chars = set(''.join(msg.split()))
    ok = set(mapping.keys())
    msg = translate(msg, None, ''.join(chars - ok))

    morsestring = []
    words = msg.split()
    for word in words:
        morseword = []
        for letter in word:
            morseletter = mapping[letter]
            morseword.append(morseletter)

        word = sep.join(morseword)
        morsestring.append(word)

    return word_sep.join(morsestring) + (word_sep if suffix else '')


def decode_morse(msg, sep='|', mapping=None):
    """
    Decodes a Morse Code with letters separated by `sep`
    (default is '|') and words by `word_sep` (default is '||)
    into plaintext.

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Morse_code

    Examples
    ========

    >>> from sympy.crypto.crypto import decode_morse
    >>> mc = '--|---|...-|.||.|.-|...|-'
    >>> decode_morse(mc)
    'MOVE EAST'

    """

    mapping = mapping or morse_char
    word_sep = 2*sep
    characterstring = []
    words = msg.strip(word_sep).split(word_sep)
    for word in words:
        letters = word.split(sep)
        chars = [mapping[c] for c in letters]
        word = ''.join(chars)
        characterstring.append(word)
    rv = " ".join(characterstring)
    return rv


#################### LFSRs  ##########################################


def lfsr_sequence(key, fill, n):
    r"""
    This function creates an lfsr sequence.

    INPUT:

        ``key``: a list of finite field elements,
            `[c_0, c_1, \ldots, c_k].`

        ``fill``: the list of the initial terms of the lfsr
            sequence, `[x_0, x_1, \ldots, x_k].`

        ``n``: number of terms of the sequence that the
            function returns.

    OUTPUT:

        The lfsr sequence defined by
        `x_{n+1} = c_k x_n + \ldots + c_0 x_{n-k}`, for
        `n \leq k`.

    Notes
    =====

    S. Golomb [G]_ gives a list of three statistical properties a
    sequence of numbers `a = \{a_n\}_{n=1}^\infty`,
    `a_n \in \{0,1\}`, should display to be considered
    "random". Define the autocorrelation of `a` to be

    .. math::

        C(k) = C(k,a) = \lim_{N\rightarrow \infty} {1\over N}\sum_{n=1}^N (-1)^{a_n + a_{n+k}}.

    In the case where `a` is periodic with period
    `P` then this reduces to

    .. math::

        C(k) = {1\over P}\sum_{n=1}^P (-1)^{a_n + a_{n+k}}.

    Assume `a` is periodic with period `P`.

    - balance:

      .. math::

        \left|\sum_{n=1}^P(-1)^{a_n}\right| \leq 1.

    - low autocorrelation:

       .. math::

         C(k) = \left\{ \begin{array}{cc} 1,& k = 0,\\ \epsilon, & k \ne 0. \end{array} \right.

      (For sequences satisfying these first two properties, it is known
      that `\epsilon = -1/P` must hold.)

    - proportional runs property: In each period, half the runs have
      length `1`, one-fourth have length `2`, etc.
      Moreover, there are as many runs of `1`'s as there are of
      `0`'s.

    References
    ==========

    .. [G] Solomon Golomb, Shift register sequences, Aegean Park Press,
       Laguna Hills, Ca, 1967

    Examples
    ========

    >>> from sympy.crypto.crypto import lfsr_sequence
    >>> from sympy.polys.domains import FF
    >>> F = FF(2)
    >>> fill = [F(1), F(1), F(0), F(1)]
    >>> key = [F(1), F(0), F(0), F(1)]
    >>> lfsr_sequence(key, fill, 10)
    [1 mod 2, 1 mod 2, 0 mod 2, 1 mod 2, 0 mod 2,
    1 mod 2, 1 mod 2, 0 mod 2, 0 mod 2, 1 mod 2]

    """
    if not isinstance(key, list):
        raise TypeError("key must be a list")
    if not isinstance(fill, list):
        raise TypeError("fill must be a list")
    p = key[0].mod
    F = FF(p)
    s = fill
    k = len(fill)
    L = []
    for i in range(n):
        s0 = s[:]
        L.append(s[0])
        s = s[1:k]
        x = sum([int(key[i]*s0[i]) for i in range(k)])
        s.append(F(x))
    return L       # use [x.to_int() for x in L] for int version


def lfsr_autocorrelation(L, P, k):
    """
    This function computes the LFSR autocorrelation function.

    INPUT:

        ``L``: is a periodic sequence of elements of `GF(2)`.
        ``L`` must have length larger than ``P``.

        ``P``: the period of ``L``

        ``k``: an integer (`0 < k < p`)

    OUTPUT:

        the ``k``-th value of the autocorrelation of the LFSR ``L``

    Examples
    ========

    >>> from sympy.crypto.crypto import (
    ...     lfsr_sequence, lfsr_autocorrelation)
    >>> from sympy.polys.domains import FF
    >>> F = FF(2)
    >>> fill = [F(1), F(1), F(0), F(1)]
    >>> key = [F(1), F(0), F(0), F(1)]
    >>> s = lfsr_sequence(key, fill, 20)
    >>> lfsr_autocorrelation(s, 15, 7)
    -1/15
    >>> lfsr_autocorrelation(s, 15, 0)
    1

    """
    if not isinstance(L, list):
        raise TypeError("L (=%s) must be a list" % L)
    P = int(P)
    k = int(k)
    L0 = L[:P]     # slices makes a copy
    L1 = L0 + L0[:k]
    L2 = [(-1)**(L1[i].to_int() + L1[i + k].to_int()) for i in range(P)]
    tot = sum(L2)
    return Rational(tot, P)


def lfsr_connection_polynomial(s):
    """
    This function computes the LFSR connection polynomial.

    INPUT:

        ``s``: a sequence of elements of even length, with entries in
        a finite field

    OUTPUT:

        ``C(x)``: the connection polynomial of a minimal LFSR yielding
        ``s``.

    This implements the algorithm in section 3 of J. L. Massey's
    article [M]_.

    References
    ==========

    .. [M] James L. Massey, "Shift-Register Synthesis and BCH Decoding."
        IEEE Trans. on Information Theory, vol. 15(1), pp. 122-127,
        Jan 1969.

    Examples
    ========

    >>> from sympy.crypto.crypto import (
    ...     lfsr_sequence, lfsr_connection_polynomial)
    >>> from sympy.polys.domains import FF
    >>> F = FF(2)
    >>> fill = [F(1), F(1), F(0), F(1)]
    >>> key = [F(1), F(0), F(0), F(1)]
    >>> s = lfsr_sequence(key, fill, 20)
    >>> lfsr_connection_polynomial(s)
    x**4 + x + 1
    >>> fill = [F(1), F(0), F(0), F(1)]
    >>> key = [F(1), F(1), F(0), F(1)]
    >>> s = lfsr_sequence(key, fill, 20)
    >>> lfsr_connection_polynomial(s)
    x**3 + 1
    >>> fill = [F(1), F(0), F(1)]
    >>> key = [F(1), F(1), F(0)]
    >>> s = lfsr_sequence(key, fill, 20)
    >>> lfsr_connection_polynomial(s)
    x**3 + x**2 + 1
    >>> fill = [F(1), F(0), F(1)]
    >>> key = [F(1), F(0), F(1)]
    >>> s = lfsr_sequence(key, fill, 20)
    >>> lfsr_connection_polynomial(s)
    x**3 + x + 1

    """
    # Initialization:
    p = s[0].mod
    x = Symbol("x")
    C = 1*x**0
    B = 1*x**0
    m = 1
    b = 1*x**0
    L = 0
    N = 0
    while N < len(s):
        if L > 0:
            dC = Poly(C).degree()
            r = min(L + 1, dC + 1)
            coeffsC = [C.subs(x, 0)] + [C.coeff(x**i)
                for i in range(1, dC + 1)]
            d = (s[N].to_int() + sum([coeffsC[i]*s[N - i].to_int()
                for i in range(1, r)])) % p
        if L == 0:
            d = s[N].to_int()*x**0
        if d == 0:
            m += 1
            N += 1
        if d > 0:
            if 2*L > N:
                C = (C - d*((b**(p - 2)) % p)*x**m*B).expand()
                m += 1
                N += 1
            else:
                T = C
                C = (C - d*((b**(p - 2)) % p)*x**m*B).expand()
                L = N + 1 - L
                m = 1
                b = d
                B = T
                N += 1
    dC = Poly(C).degree()
    coeffsC = [C.subs(x, 0)] + [C.coeff(x**i) for i in range(1, dC + 1)]
    return sum([coeffsC[i] % p*x**i for i in range(dC + 1)
        if coeffsC[i] is not None])


#################### ElGamal  #############################


def elgamal_private_key(digit=10, seed=None):
    r"""
    Return three number tuple as private key.

    Elgamal encryption is based on the mathmatical problem
    called the Discrete Logarithm Problem (DLP). For example,

    `a^{b} \equiv c \pmod p`

    In general, if ``a`` and ``b`` are known, ``ct`` is easily
    calculated. If ``b`` is unknown, it is hard to use
    ``a`` and ``ct`` to get ``b``.

    Parameters
    ==========

    digit : minimum number of binary digits for key

    Returns
    =======

    (p, r, d) : p = prime number, r = primitive root, d = random number

    Notes
    =====

    For testing purposes, the ``seed`` parameter may be set to control
    the output of this routine. See sympy.utilities.randtest._randrange.

    Examples
    ========

    >>> from sympy.crypto.crypto import elgamal_private_key
    >>> from sympy.ntheory import is_primitive_root, isprime
    >>> a, b, _ = elgamal_private_key()
    >>> isprime(a)
    True
    >>> is_primitive_root(b, a)
    True

    """
    randrange = _randrange(seed)
    p = nextprime(2**digit)
    return p, primitive_root(p), randrange(2, p)


def elgamal_public_key(key):
    """
    Return three number tuple as public key.

    Parameters
    ==========

    key : Tuple (p, r, e)  generated by ``elgamal_private_key``

    Returns
    =======
    (p, r, e = r**d mod p) : d is a random number in private key.

    Examples
    ========

    >>> from sympy.crypto.crypto import elgamal_public_key
    >>> elgamal_public_key((1031, 14, 636))
    (1031, 14, 212)

    """
    p, r, e = key
    return p, r, pow(r, e, p)


def encipher_elgamal(i, key, seed=None):
    r"""
    Encrypt message with public key

    ``i`` is a plaintext message expressed as an integer.
    ``key`` is public key (p, r, e). In order to encrypt
    a message, a random number ``a`` in ``range(2, p)``
    is generated and the encryped message is returned as
    `c_{1}` and `c_{2}` where:

    `c_{1} \equiv r^{a} \pmod p`

    `c_{2} \equiv m e^{a} \pmod p`

    Parameters
    ==========

    msg : int of encoded message
    key : public key

    Returns
    =======

    (c1, c2) : Encipher into two number

    Notes
    =====

    For testing purposes, the ``seed`` parameter may be set to control
    the output of this routine. See sympy.utilities.randtest._randrange.

    Examples
    ========

    >>> from sympy.crypto.crypto import encipher_elgamal, elgamal_private_key, elgamal_public_key
    >>> pri = elgamal_private_key(5, seed=[3]); pri
    (37, 2, 3)
    >>> pub = elgamal_public_key(pri); pub
    (37, 2, 8)
    >>> msg = 36
    >>> encipher_elgamal(msg, pub, seed=[3])
    (8, 6)

    """
    p, r, e = key
    if i < 0 or i >= p:
        raise ValueError(
            'Message (%s) should be in range(%s)' % (i, p))
    randrange = _randrange(seed)
    a = randrange(2, p)
    return pow(r, a, p), i*pow(e, a, p) % p


def decipher_elgamal(msg, key):
    r"""
    Decrypt message with private key

    `msg = (c_{1}, c_{2})`

    `key = (p, r, d)`

    According to extended Eucliden theorem,
    `u c_{1}^{d} + p n = 1`

    `u \equiv 1/{{c_{1}}^d} \pmod p`

    `u c_{2} \equiv \frac{1}{c_{1}^d} c_{2} \equiv \frac{1}{r^{ad}} c_{2} \pmod p`

    `\frac{1}{r^{ad}} m e^a \equiv \frac{1}{r^{ad}} m {r^{d a}} \equiv m \pmod p`

    Examples
    ========

    >>> from sympy.crypto.crypto import decipher_elgamal
    >>> from sympy.crypto.crypto import encipher_elgamal
    >>> from sympy.crypto.crypto import elgamal_private_key
    >>> from sympy.crypto.crypto import elgamal_public_key

    >>> pri = elgamal_private_key(5, seed=[3])
    >>> pub = elgamal_public_key(pri); pub
    (37, 2, 8)
    >>> msg = 17
    >>> decipher_elgamal(encipher_elgamal(msg, pub), pri) == msg
    True

    """
    p, r, d = key
    c1, c2 = msg
    u = igcdex(c1**d, p)[0]
    return u * c2 % p


################ Diffie-Hellman Key Exchange  #########################

def dh_private_key(digit=10, seed=None):
    r"""
    Return three integer tuple as private key.

    Diffie-Hellman key exchange is based on the mathematical problem
    called the Discrete Logarithm Problem (see ElGamal).

    Diffie-Hellman key exchange is divided into the following steps:

    *   Alice and Bob agree on a base that consist of a prime ``p``
        and a primitive root of ``p`` called ``g``
    *   Alice choses a number ``a`` and Bob choses a number ``b`` where
        ``a`` and ``b`` are random numbers in range `[2, p)`. These are
        their private keys.
    *   Alice then publicly sends Bob `g^{a} \pmod p` while Bob sends
        Alice `g^{b} \pmod p`
    *   They both raise the received value to their secretly chosen
        number (``a`` or ``b``) and now have both as their shared key
        `g^{ab} \pmod p`

    Parameters
    ==========

    digit: minimum number of binary digits required in key

    Returns
    =======

    (p, g, a) : p = prime number, g = primitive root of p,
                a = random number from 2 through p - 1

    Notes
    =====

    For testing purposes, the ``seed`` parameter may be set to control
    the output of this routine. See sympy.utilities.randtest._randrange.

    Examples
    ========

    >>> from sympy.crypto.crypto import dh_private_key
    >>> from sympy.ntheory import isprime, is_primitive_root
    >>> p, g, _ = dh_private_key()
    >>> isprime(p)
    True
    >>> is_primitive_root(g, p)
    True
    >>> p, g, _ = dh_private_key(5)
    >>> isprime(p)
    True
    >>> is_primitive_root(g, p)
    True

    """
    p = nextprime(2**digit)
    g = primitive_root(p)
    randrange = _randrange(seed)
    a = randrange(2, p)
    return p, g, a


def dh_public_key(key):
    """
    Return three number tuple as public key.

    This is the tuple that Alice sends to Bob.

    Parameters
    ==========

    key: Tuple (p, g, a) generated by ``dh_private_key``

    Returns
    =======

    (p, g, g^a mod p) : p, g and a as in Parameters

    Examples
    ========

    >>> from sympy.crypto.crypto import dh_private_key, dh_public_key
    >>> p, g, a = dh_private_key();
    >>> _p, _g, x = dh_public_key((p, g, a))
    >>> p == _p and g == _g
    True
    >>> x == pow(g, a, p)
    True

    """
    p, g, a = key
    return p, g, pow(g, a, p)


def dh_shared_key(key, b):
    """
    Return an integer that is the shared key.

    This is what Bob and Alice can both calculate using the public
    keys they received from each other and their private keys.

    Parameters
    ==========

    key: Tuple (p, g, x) generated by ``dh_public_key``
    b: Random number in the range of 2 to p - 1
       (Chosen by second key exchange member (Bob))

    Returns
    =======

    shared key (int)

    Examples
    ========

    >>> from sympy.crypto.crypto import (
    ...     dh_private_key, dh_public_key, dh_shared_key)
    >>> prk = dh_private_key();
    >>> p, g, x = dh_public_key(prk);
    >>> sk = dh_shared_key((p, g, x), 1000)
    >>> sk == pow(x, 1000, p)
    True

    """
    p, _, x = key
    if 1 >= b or b >= p:
        raise ValueError(filldedent('''
            Value of b should be greater 1 and less
            than prime %s.''' % p))

    return pow(x, b, p)


################ Goldwasser-Micali Encryption  #########################


def _legendre(a, p):
    """
    Returns the legendre symbol of a and p
    assuming that p is a prime

    i.e. 1 if a is a quadratic residue mod p
        -1 if a is not a quadratic residue mod p
         0 if a is divisible by p

    Parameters
    ==========

    a : int the number to test
    p : the prime to test a against

    Returns
    =======

    legendre symbol (a / p) (int)

    """
    sig = pow(a, (p - 1)//2, p)
    if sig == 1:
        return 1
    elif sig == 0:
        return 0
    else:
        return -1


def _random_coprime_stream(n, seed=None):
    randrange = _randrange(seed)
    while True:
        y = randrange(n)
        if gcd(y, n) == 1:
            yield y


def gm_private_key(p, q, a=None):
    """
    Check if p and q can be used as private keys for
    the Goldwasser-Micali encryption. The method works
    roughly as follows.

    Pick two large primes p ands q. Call their product N.
    Given a message as an integer i, write i in its
    bit representation b_0,...,b_n. For each k,

     if b_k = 0:
        let a_k be a random square
        (quadratic residue) modulo p * q
        such that jacobi_symbol(a, p * q) = 1
     if b_k = 1:
        let a_k be a random non-square
        (non-quadratic residue) modulo p * q
        such that jacobi_symbol(a, p * q) = 1

    return [a_1, a_2,...]

    b_k can be recovered by checking whether or not
    a_k is a residue. And from the b_k's, the message
    can be reconstructed.

    The idea is that, while jacobi_symbol(a, p * q)
    can be easily computed (and when it is equal to -1 will
    tell you that a is not a square mod p * q), quadratic
    residuosity modulo a composite number is hard to compute
    without knowing its factorization.

    Moreover, approximately half the numbers coprime to p * q have
    jacobi_symbol equal to 1. And among those, approximately half
    are residues and approximately half are not. This maximizes the
    entropy of the code.

    Parameters
    ==========

    p, q, a : initialization variables

    Returns
    =======

    p, q : the input value p and q

    Raises
    ======

    ValueError : if p and q are not distinct odd primes

    """
    if p == q:
        raise ValueError("expected distinct primes, "
                         "got two copies of %i" % p)
    elif not isprime(p) or not isprime(q):
        raise ValueError("first two arguments must be prime, "
                         "got %i of %i" % (p, q))
    elif p == 2 or q == 2:
        raise ValueError("first two arguments must not be even, "
                         "got %i of %i" % (p, q))
    return p, q


def gm_public_key(p, q, a=None, seed=None):
    """
    Compute public keys for p and q.
    Note that in Goldwasser-Micali Encrpytion,
    public keys are randomly selected.

    Parameters
    ==========

    p, q, a : (int) initialization variables

    Returns
    =======

    (a, N) : tuple[int]
        a is the input a if it is not None otherwise
        some random integer coprime to p and q.

        N is the product of p and q
    """

    p, q = gm_private_key(p, q)
    N = p * q

    if a is None:
        randrange = _randrange(seed)
        while True:
            a = randrange(N)
            if _legendre(a, p) == _legendre(a, q) == -1:
                break
    else:
        if _legendre(a, p) != -1 or _legendre(a, q) != -1:
            return False
    return (a, N)


def encipher_gm(i, key, seed=None):
    """
    Encrypt integer 'i' using public_key 'key'
    Note that gm uses random encrpytion.

    Parameters
    ==========

    i: (int) the message to encrypt
    key: Tuple (a, N) the public key

    Returns
    =======

    List[int] the randomized encrpyted message.

    """
    if i < 0:
        raise ValueError(
            "message must be a non-negative "
            "integer: got %d instead" % i)
    a, N = key
    bits = []
    while i > 0:
        bits.append(i % 2)
        i //= 2

    gen = _random_coprime_stream(N, seed)
    rev = reversed(bits)
    encode = lambda b: next(gen)**2*pow(a, b) % N
    return [ encode(b) for b in rev ]



def decipher_gm(message, key):
    """
    Decrypt message 'message' using public_key 'key'.

    Parameters
    ==========

    List[int]: the randomized encrpyted message.
    key: Tuple (p, q) the private key

    Returns
    =======

    i (int) the encrpyted message
    """
    p, q = key
    res = lambda m, p: _legendre(m, p) > 0
    bits = [res(m, p) * res(m, q) for m in message]
    m = 0
    for b in bits:
        m <<= 1
        m += not b
    return m

################ Blum–Goldwasser cryptosystem  #########################

def bg_private_key(p, q):
    """
    Check if p and q can be used as private keys for
    the Blum–Goldwasser cryptosystem.

    The three necessary checks for p and q to pass
    so that they can be used as private keys:

        1. p and q must both be prime
        2. p and q must be distinct
        3. p and q must be congruent to 3 mod 4

    Parameters
    ==========

    p, q : the keys to be checked

    Returns
    =======

    p, q : input values

    Raises
    ======

    ValueError : if p and q do not pass the above conditions

    """

    if not isprime(p) or not isprime(q):
        raise ValueError("the two arguments must be prime, "
                         "got %i and %i" %(p, q))
    elif p == q:
        raise ValueError("the two arguments must be distinct, "
                         "got two copies of %i. " %p)
    elif (p - 3) % 4 != 0 or (q - 3) % 4 != 0:
        raise ValueError("the two arguments must be congruent to 3 mod 4, "
                         "got %i and %i" %(p, q))
    return p, q

def bg_public_key(p, q):
    """
    Calculates public keys from private keys.

    The function first checks the validity of
    private keys passed as arguments and
    then returns their product.

    Parameters
    ==========

    p, q : the private keys

    Returns
    =======

    N : the public key
    """
    p, q = bg_private_key(p, q)
    N = p * q
    return N

def encipher_bg(i, key, seed=None):
    """
    Encrypts the message using public key and seed.

    ALGORITHM:
        1. Encodes i as a string of L bits, m.
        2. Select a random element r, where 1 < r < key, and computes
           x = r^2 mod key.
        3. Use BBS pseudo-random number generator to generate L random bits, b,
        using the initial seed as x.
        4. Encrypted message, c_i = m_i XOR b_i, 1 <= i <= L.
        5. x_L = x^(2^L) mod key.
        6. Return (c, x_L)

    Parameters
    ==========

    i : message, a non-negative integer
    key : the public key

    Returns
    =======

    (encrypted_message, x_L) : Tuple

    Raises
    ======

    ValueError : if i is negative
    """

    if i < 0:
        raise ValueError(
            "message must be a non-negative "
            "integer: got %d instead" % i)

    enc_msg = []
    while i > 0:
        enc_msg.append(i % 2)
        i //= 2
    enc_msg.reverse()
    L = len(enc_msg)

    r = _randint(seed)(2, key - 1)
    x = r**2 % key
    x_L = pow(int(x), int(2**L), int(key))

    rand_bits = []
    for k in range(L):
        rand_bits.append(x % 2)
        x = x**2 % key

    encrypt_msg = [m ^ b for (m, b) in zip(enc_msg, rand_bits)]

    return (encrypt_msg, x_L)

def decipher_bg(message, key):
    """
    Decrypts the message using private keys.

    ALGORITHM:
        1. Let, c be the encrypted message, y the second number received,
        and p and q be the private keys.
        2. Compute, r_p = y^((p+1)/4 ^ L) mod p and
        r_q = y^((q+1)/4 ^ L) mod q.
        3. Compute x_0 = (q(q^-1 mod p)r_p + p(p^-1 mod q)r_q) mod N.
        4. From, recompute the bits using the BBS generator, as in the
        encryption algorithm.
        5. Compute original message by XORing c and b.

    Parameters
    ==========

    message : Tuple of encrypted message and a non-negative integer.
    key : Tuple of private keys

    Returns
    =======

    orig_msg : The original message
    """

    p, q = key
    encrypt_msg, y = message
    public_key = p * q
    L = len(encrypt_msg)
    p_t = ((p + 1)/4)**L
    q_t = ((q + 1)/4)**L
    r_p = pow(int(y), int(p_t), int(p))
    r_q = pow(int(y), int(q_t), int(q))

    x = (q * mod_inverse(q, p) * r_p + p * mod_inverse(p, q) * r_q) % public_key

    orig_bits = []
    for k in range(L):
        orig_bits.append(x % 2)
        x = x**2 % public_key

    orig_msg = 0
    for (m, b) in zip(encrypt_msg, orig_bits):
        orig_msg = orig_msg * 2
        orig_msg += (m ^ b)

    return orig_msg
