"""Implementaton of :class:`PythonIntegerRing` class. """

from __future__ import print_function, division

from sympy.polys.domains.groundtypes import (
    PythonInteger, SymPyInteger, python_sqrt,
    python_factorial, python_gcdex, python_gcd, python_lcm,
)
from sympy.polys.domains.integerring import IntegerRing
from sympy.polys.polyerrors import CoercionFailed
from sympy.utilities import public

@public
class PythonIntegerRing(IntegerRing):
    """Integer ring based on Python's ``int`` type. """

    dtype = PythonInteger
    zero = dtype(0)
    one = dtype(1)
    alias = 'ZZ_python'

    def __init__(self):
        """Allow instantiation of this domain. """

    def to_sympy(self, a):
        """Convert ``a`` to a SymPy object. """
        return SymPyInteger(a)

    def from_sympy(self, a):
        """Convert SymPy's Integer to ``dtype``. """
        if a.is_Integer:
            return PythonInteger(a.p)
        elif a.is_Float and int(a) == a:
            return PythonInteger(int(a))
        else:
            raise CoercionFailed("expected an integer, got %s" % a)

    def from_FF_python(K1, a, K0):
        """Convert ``ModularInteger(int)`` to Python's ``int``. """
        return a.to_int()

    def from_ZZ_python(K1, a, K0):
        """Convert Python's ``int`` to Python's ``int``. """
        return a

    def from_QQ_python(K1, a, K0):
        """Convert Python's ``Fraction`` to Python's ``int``. """
        if a.denominator == 1:
            return a.numerator

    def from_FF_gmpy(K1, a, K0):
        """Convert ``ModularInteger(mpz)`` to Python's ``int``. """
        return PythonInteger(a.to_int())

    def from_ZZ_gmpy(K1, a, K0):
        """Convert GMPY's ``mpz`` to Python's ``int``. """
        return PythonInteger(a)

    def from_QQ_gmpy(K1, a, K0):
        """Convert GMPY's ``mpq`` to Python's ``int``. """
        if a.denom() == 1:
            return PythonInteger(a.numer())

    def from_RealField(K1, a, K0):
        """Convert mpmath's ``mpf`` to Python's ``int``. """
        p, q = K0.to_rational(a)

        if q == 1:
            return PythonInteger(p)

    def gcdex(self, a, b):
        """Compute extended GCD of ``a`` and ``b``. """
        return python_gcdex(a, b)

    def gcd(self, a, b):
        """Compute GCD of ``a`` and ``b``. """
        return python_gcd(a, b)

    def lcm(self, a, b):
        """Compute LCM of ``a`` and ``b``. """
        return python_lcm(a, b)

    def sqrt(self, a):
        """Compute square root of ``a``. """
        return python_sqrt(a)

    def factorial(self, a):
        """Compute factorial of ``a``. """
        return python_factorial(a)
