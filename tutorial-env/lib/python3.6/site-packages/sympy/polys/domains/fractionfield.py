"""Implementation of :class:`FractionField` class. """

from __future__ import print_function, division

from sympy.polys.domains.compositedomain import CompositeDomain
from sympy.polys.domains.field import Field
from sympy.polys.polyerrors import CoercionFailed, GeneratorsError
from sympy.utilities import public

@public
class FractionField(Field, CompositeDomain):
    """A class for representing multivariate rational function fields. """

    is_FractionField = is_Frac = True

    has_assoc_Ring = True
    has_assoc_Field = True

    def __init__(self, domain_or_field, symbols=None, order=None):
        from sympy.polys.fields import FracField

        if isinstance(domain_or_field, FracField) and symbols is None and order is None:
            field = domain_or_field
        else:
            field = FracField(symbols, domain_or_field, order)

        self.field = field
        self.dtype = field.dtype

        self.gens = field.gens
        self.ngens = field.ngens
        self.symbols = field.symbols
        self.domain = field.domain

        # TODO: remove this
        self.dom = self.domain

    def new(self, element):
        return self.field.field_new(element)

    @property
    def zero(self):
        return self.field.zero

    @property
    def one(self):
        return self.field.one

    @property
    def order(self):
        return self.field.order

    def __str__(self):
        return str(self.domain) + '(' + ','.join(map(str, self.symbols)) + ')'

    def __hash__(self):
        return hash((self.__class__.__name__, self.dtype.field, self.domain, self.symbols))

    def __eq__(self, other):
        """Returns `True` if two domains are equivalent. """
        return isinstance(other, FractionField) and \
            (self.dtype.field, self.domain, self.symbols) ==\
            (other.dtype.field, other.domain, other.symbols)

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return a.as_expr()

    def from_sympy(self, a):
        """Convert SymPy's expression to `dtype`. """
        return self.field.from_expr(a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return K1(K1.domain.convert(a, K0))

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return K1(K1.domain.convert(a, K0))

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return K1(K1.domain.convert(a, K0))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return K1(K1.domain.convert(a, K0))

    def from_RealField(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return K1(K1.domain.convert(a, K0))

    def from_AlgebraicField(K1, a, K0):
        """Convert an algebraic number to ``dtype``. """
        if K1.domain == K0:
            return K1.new(a)

    def from_PolynomialRing(K1, a, K0):
        """Convert a polynomial to ``dtype``. """
        try:
            return K1.new(a)
        except (CoercionFailed, GeneratorsError):
            return None

    def from_FractionField(K1, a, K0):
        """Convert a rational function to ``dtype``. """
        try:
            return a.set_field(K1.field)
        except (CoercionFailed, GeneratorsError):
            return None

    def get_ring(self):
        """Returns a field associated with `self`. """
        return self.field.to_ring().to_domain()

    def is_positive(self, a):
        """Returns True if `LC(a)` is positive. """
        return self.domain.is_positive(a.numer.LC)

    def is_negative(self, a):
        """Returns True if `LC(a)` is negative. """
        return self.domain.is_negative(a.numer.LC)

    def is_nonpositive(self, a):
        """Returns True if `LC(a)` is non-positive. """
        return self.domain.is_nonpositive(a.numer.LC)

    def is_nonnegative(self, a):
        """Returns True if `LC(a)` is non-negative. """
        return self.domain.is_nonnegative(a.numer.LC)

    def numer(self, a):
        """Returns numerator of ``a``. """
        return a.numer

    def denom(self, a):
        """Returns denominator of ``a``. """
        return a.denom

    def factorial(self, a):
        """Returns factorial of `a`. """
        return self.dtype(self.domain.factorial(a))
