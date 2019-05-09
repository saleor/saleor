"""Module containing a cryptographic-quality source of randomness and
other cryptographically useful functionality

Python 2.4 needs no external support for this module, nor does Python
2.3 on a system with /dev/urandom.

Other configurations will need a quality source of random bytes and
access to a function that will convert binary strings to long
integers. This module will work with the Python Cryptography Toolkit
(pycrypto) if it is present. pycrypto can be found with a search
engine, but is currently found at:

http://www.amk.ca/python/code/crypto
"""

__all__ = [
    'base64ToLong',
    'binaryToLong',
    'hmacSha1',
    'hmacSha256',
    'longToBase64',
    'longToBinary',
    'randomString',
    'randrange',
    'sha1',
    'sha256',
]

import hmac
import os
import random

from openid.oidutil import toBase64, fromBase64

import hashlib


class HashContainer(object):
    def __init__(self, hash_constructor):
        self.new = hash_constructor
        self.digest_size = hash_constructor().digest_size


sha1_module = HashContainer(hashlib.sha1)
sha256_module = HashContainer(hashlib.sha256)


def hmacSha1(key, text):
    if isinstance(key, str):
        key = bytes(key, encoding="utf-8")
    if isinstance(text, str):
        text = bytes(text, encoding="utf-8")
    return hmac.new(key, text, sha1_module).digest()


def sha1(s):
    if isinstance(s, str):
        s = bytes(s, encoding="utf-8")
    return sha1_module.new(s).digest()


def hmacSha256(key, text):
    if isinstance(key, str):
        key = bytes(key, encoding="utf-8")
    if isinstance(text, str):
        text = bytes(text, encoding="utf-8")
    return hmac.new(key, text, sha256_module).digest()


def sha256(s):
    if isinstance(s, str):
        s = bytes(s, encoding="utf-8")
    return sha256_module.new(s).digest()


SHA256_AVAILABLE = True

try:
    from Crypto.Util.number import long_to_bytes, bytes_to_long
except ImportError:
    # In the case where we don't have pycrypto installed, define substitute
    # functionality.

    import pickle

    def longToBinary(l):
        if l == 0:
            return b'\x00'
        b = bytearray(pickle.encode_long(l))
        b.reverse()
        return bytes(b)

    def binaryToLong(s):
        if isinstance(s, str):
            s = s.encode("utf-8")
        b = bytearray(s)
        b.reverse()
        return pickle.decode_long(bytes(b))
else:
    # We have pycrypto, so wrap its functions instead.

    def longToBinary(l):
        if l < 0:
            raise ValueError('This function only supports positive integers')

        bytestring = long_to_bytes(l)
        if bytestring[0] > 127:
            return b'\x00' + bytestring
        else:
            return bytestring

    def binaryToLong(bytestring):
        if not bytestring:
            raise ValueError('Empty string passed to strToLong')

        if bytestring[0] > 127:
            raise ValueError('This function only supports positive integers')

        return bytes_to_long(bytestring)


# A cryptographically safe source of random bytes
getBytes = os.urandom

# A randrange function that works for longs
randrange = random.randrange


def longToBase64(l):
    return toBase64(longToBinary(l))


def base64ToLong(s):
    return binaryToLong(fromBase64(s))


def randomString(length, chrs=None):
    """Produce a string of length random bytes, chosen from chrs."""
    if chrs is None:
        return getBytes(length)
    else:
        n = len(chrs)
        return ''.join([chrs[randrange(n)] for _ in range(length)])


def const_eq(s1, s2):
    if len(s1) != len(s2):
        return False

    result = True
    for i in range(len(s1)):
        result = result and (s1[i] == s2[i])

    return result
