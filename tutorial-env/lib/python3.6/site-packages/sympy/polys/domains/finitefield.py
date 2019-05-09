"""Implementation of :class:`FiniteField` class. """

from __future__ import print_function, division

from sympy.polys.domains.field import Field
from sympy.polys.domains.groundtypes import SymPyInteger
from sympy.polys.domains.modularinteger import ModularIntegerFactory
from sympy.polys.domains.simpledomain import SimpleDomain
from sympy.polys.polyerrors import CoercionFailed
from sympy.utilities import public

@public
class FiniteField(Field, SimpleDomain):
    """General class for finite fields. """

    rep = 'FF'

    is_FiniteField = is_FF = True
    is_Numerical = True

    has_assoc_Ring = False
    has_assoc_Field = True

    dom = None
    mod = None

    def __init__(self, mod, dom=None, symmetric=True):
        if mod <= 0:
            raise ValueError('modulus must be a positive integer, got %s' % mod)
        if dom is None:
            from sympy.polys.domains import ZZ
            dom = ZZ

        self.dtype = ModularIntegerFactory(mod, dom, symmetric, self)
        self.zero = self.dtype(0)
        self.one = self.dtype(1)
        self.dom = dom
        self.mod = mod

    def __str__(self):
        return 'GF(%s)' % self.mod

    def __hash__(self):
        return hash((self.__class__.__name__, self.dtype, self.mod, self.dom))

    def __eq__(self, other):
        """Returns ``True`` if two domains are equivalent. """
        return isinstance(other, FiniteField) and \
            self.mod == other.mod and self.dom == other.dom

    def characteristic(self):
        """Return the characteristic of this domain. """
        return self.mod

    def get_field(self):
        """Returns a field associated with ``self``. """
        return self

    def to_sympy(self, a):
        """Convert ``a`` to a SymPy object. """
        return SymPyInteger(int(a))

    def from_sympy(self, a):
        """Convert SymPy's Integer to SymPy's ``Integer``. """
        if a.is_Integer:
            return self.dtype(self.dom.dtype(int(a)))
        elif a.is_Float and int(a) == a:
            return self.dtype(self.dom.dtype(int(a)))
        else:
            raise CoercionFailed("expected an integer, got %s" % a)

    def from_FF_python(K1, a, K0=None):
        """Convert ``ModularInteger(int)`` to ``dtype``. """
        return K1.dtype(K1.dom.from_ZZ_python(a.val, K0.dom))

    def from_ZZ_python(K1, a, K0=None):
        """Convert Python's ``int`` to ``dtype``. """
        return K1.dtype(K1.dom.from_ZZ_python(a, K0))

    def from_QQ_python(K1, a, K0=None):
        """Convert Python's ``Fraction`` to ``dtype``. """
        if a.denominator == 1:
            return K1.from_ZZ_python(a.numerator)

    def from_FF_gmpy(K1, a, K0=None):
        """Convert ``ModularInteger(mpz)`` to ``dtype``. """
        return K1.dtype(K1.dom.from_ZZ_gmpy(a.val, K0.dom))

    def from_ZZ_gmpy(K1, a, K0=None):
        """Convert GMPY's ``mpz`` to ``dtype``. """
        return K1.dtype(K1.dom.from_ZZ_gmpy(a, K0))

    def from_QQ_gmpy(K1, a, K0=None):
        """Convert GMPY's ``mpq`` to ``dtype``. """
        if a.denominator == 1:
            return K1.from_ZZ_gmpy(a.numerator)

    def from_RealField(K1, a, K0):
        """Convert mpmath's ``mpf`` to ``dtype``. """
        p, q = K0.to_rational(a)

        if q == 1:
            return K1.dtype(self.dom.dtype(p))
