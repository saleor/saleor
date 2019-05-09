"""Implementation of :class:`Domain` class. """

from __future__ import print_function, division


from sympy.core import Basic, sympify
from sympy.core.compatibility import HAS_GMPY, integer_types, is_sequence
from sympy.core.decorators import deprecated
from sympy.polys.domains.domainelement import DomainElement
from sympy.polys.orderings import lex
from sympy.polys.polyerrors import UnificationFailed, CoercionFailed, DomainError
from sympy.polys.polyutils import _unify_gens
from sympy.utilities import default_sort_key, public

@public
class Domain(object):
    """Represents an abstract domain. """

    dtype = None
    zero = None
    one = None

    is_Ring = False
    is_Field = False

    has_assoc_Ring = False
    has_assoc_Field = False

    is_FiniteField = is_FF = False
    is_IntegerRing = is_ZZ = False
    is_RationalField = is_QQ = False
    is_RealField = is_RR = False
    is_ComplexField = is_CC = False
    is_AlgebraicField = is_Algebraic = False
    is_PolynomialRing = is_Poly = False
    is_FractionField = is_Frac = False
    is_SymbolicDomain = is_EX = False

    is_Exact = True
    is_Numerical = False

    is_Simple = False
    is_Composite = False
    is_PID = False

    has_CharacteristicZero = False

    rep = None
    alias = None

    @property
    @deprecated(useinstead="is_Field", issue=12723, deprecated_since_version="1.1")
    def has_Field(self):
        return self.is_Field

    @property
    @deprecated(useinstead="is_Ring", issue=12723, deprecated_since_version="1.1")
    def has_Ring(self):
        return self.is_Ring

    def __init__(self):
        raise NotImplementedError

    def __str__(self):
        return self.rep

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.__class__.__name__, self.dtype))

    def new(self, *args):
        return self.dtype(*args)

    @property
    def tp(self):
        return self.dtype

    def __call__(self, *args):
        """Construct an element of ``self`` domain from ``args``. """
        return self.new(*args)

    def normal(self, *args):
        return self.dtype(*args)

    def convert_from(self, element, base):
        """Convert ``element`` to ``self.dtype`` given the base domain. """
        if base.alias is not None:
            method = "from_" + base.alias
        else:
            method = "from_" + base.__class__.__name__

        _convert = getattr(self, method)

        if _convert is not None:
            result = _convert(element, base)

            if result is not None:
                return result

        raise CoercionFailed("can't convert %s of type %s from %s to %s" % (element, type(element), base, self))

    def convert(self, element, base=None):
        """Convert ``element`` to ``self.dtype``. """
        if base is not None:
            return self.convert_from(element, base)

        if self.of_type(element):
            return element

        from sympy.polys.domains import PythonIntegerRing, GMPYIntegerRing, GMPYRationalField, RealField, ComplexField

        if isinstance(element, integer_types):
            return self.convert_from(element, PythonIntegerRing())

        if HAS_GMPY:
            integers = GMPYIntegerRing()
            if isinstance(element, integers.tp):
                return self.convert_from(element, integers)

            rationals = GMPYRationalField()
            if isinstance(element, rationals.tp):
                return self.convert_from(element, rationals)

        if isinstance(element, float):
            parent = RealField(tol=False)
            return self.convert_from(parent(element), parent)

        if isinstance(element, complex):
            parent = ComplexField(tol=False)
            return self.convert_from(parent(element), parent)

        if isinstance(element, DomainElement):
            return self.convert_from(element, element.parent())

        # TODO: implement this in from_ methods
        if self.is_Numerical and getattr(element, 'is_ground', False):
            return self.convert(element.LC())

        if isinstance(element, Basic):
            try:
                return self.from_sympy(element)
            except (TypeError, ValueError):
                pass
        else: # TODO: remove this branch
            if not is_sequence(element):
                try:
                    element = sympify(element)

                    if isinstance(element, Basic):
                        return self.from_sympy(element)
                except (TypeError, ValueError):
                    pass

        raise CoercionFailed("can't convert %s of type %s to %s" % (element, type(element), self))

    def of_type(self, element):
        """Check if ``a`` is of type ``dtype``. """
        return isinstance(element, self.tp) # XXX: this isn't correct, e.g. PolyElement

    def __contains__(self, a):
        """Check if ``a`` belongs to this domain. """
        try:
            self.convert(a)
        except CoercionFailed:
            return False

        return True

    def to_sympy(self, a):
        """Convert ``a`` to a SymPy object. """
        raise NotImplementedError

    def from_sympy(self, a):
        """Convert a SymPy object to ``dtype``. """
        raise NotImplementedError

    def from_FF_python(K1, a, K0):
        """Convert ``ModularInteger(int)`` to ``dtype``. """
        return None

    def from_ZZ_python(K1, a, K0):
        """Convert a Python ``int`` object to ``dtype``. """
        return None

    def from_QQ_python(K1, a, K0):
        """Convert a Python ``Fraction`` object to ``dtype``. """
        return None

    def from_FF_gmpy(K1, a, K0):
        """Convert ``ModularInteger(mpz)`` to ``dtype``. """
        return None

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY ``mpz`` object to ``dtype``. """
        return None

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY ``mpq`` object to ``dtype``. """
        return None

    def from_RealField(K1, a, K0):
        """Convert a real element object to ``dtype``. """
        return None

    def from_ComplexField(K1, a, K0):
        """Convert a complex element to ``dtype``. """
        return None

    def from_AlgebraicField(K1, a, K0):
        """Convert an algebraic number to ``dtype``. """
        return None

    def from_PolynomialRing(K1, a, K0):
        """Convert a polynomial to ``dtype``. """
        if a.is_ground:
            return K1.convert(a.LC, K0.dom)

    def from_FractionField(K1, a, K0):
        """Convert a rational function to ``dtype``. """
        return None

    def from_ExpressionDomain(K1, a, K0):
        """Convert a ``EX`` object to ``dtype``. """
        return K1.from_sympy(a.ex)

    def from_GlobalPolynomialRing(K1, a, K0):
        """Convert a polynomial to ``dtype``. """
        if a.degree() <= 0:
            return K1.convert(a.LC(), K0.dom)

    def from_GeneralizedPolynomialRing(K1, a, K0):
        return K1.from_FractionField(a, K0)

    def unify_with_symbols(K0, K1, symbols):
        if (K0.is_Composite and (set(K0.symbols) & set(symbols))) or (K1.is_Composite and (set(K1.symbols) & set(symbols))):
            raise UnificationFailed("can't unify %s with %s, given %s generators" % (K0, K1, tuple(symbols)))

        return K0.unify(K1)

    def unify(K0, K1, symbols=None):
        """
        Construct a minimal domain that contains elements of ``K0`` and ``K1``.

        Known domains (from smallest to largest):

        - ``GF(p)``
        - ``ZZ``
        - ``QQ``
        - ``RR(prec, tol)``
        - ``CC(prec, tol)``
        - ``ALG(a, b, c)``
        - ``K[x, y, z]``
        - ``K(x, y, z)``
        - ``EX``

        """
        if symbols is not None:
            return K0.unify_with_symbols(K1, symbols)

        if K0 == K1:
            return K0

        if K0.is_EX:
            return K0
        if K1.is_EX:
            return K1

        if K0.is_Composite or K1.is_Composite:
            K0_ground = K0.dom if K0.is_Composite else K0
            K1_ground = K1.dom if K1.is_Composite else K1

            K0_symbols = K0.symbols if K0.is_Composite else ()
            K1_symbols = K1.symbols if K1.is_Composite else ()

            domain = K0_ground.unify(K1_ground)
            symbols = _unify_gens(K0_symbols, K1_symbols)
            order = K0.order if K0.is_Composite else K1.order

            if ((K0.is_FractionField and K1.is_PolynomialRing or
                 K1.is_FractionField and K0.is_PolynomialRing) and
                 (not K0_ground.is_Field or not K1_ground.is_Field) and domain.is_Field):
                domain = domain.get_ring()

            if K0.is_Composite and (not K1.is_Composite or K0.is_FractionField or K1.is_PolynomialRing):
                cls = K0.__class__
            else:
                cls = K1.__class__

            from sympy.polys.domains.old_polynomialring import GlobalPolynomialRing
            if cls == GlobalPolynomialRing:
                return cls(domain, symbols)

            return cls(domain, symbols, order)

        def mkinexact(cls, K0, K1):
            prec = max(K0.precision, K1.precision)
            tol = max(K0.tolerance, K1.tolerance)
            return cls(prec=prec, tol=tol)

        if K0.is_ComplexField and K1.is_ComplexField:
            return mkinexact(K0.__class__, K0, K1)
        if K0.is_ComplexField and K1.is_RealField:
            return mkinexact(K0.__class__, K0, K1)
        if K0.is_RealField and K1.is_ComplexField:
            return mkinexact(K1.__class__, K1, K0)
        if K0.is_RealField and K1.is_RealField:
            return mkinexact(K0.__class__, K0, K1)
        if K0.is_ComplexField or K0.is_RealField:
            return K0
        if K1.is_ComplexField or K1.is_RealField:
            return K1

        if K0.is_AlgebraicField and K1.is_AlgebraicField:
            return K0.__class__(K0.dom.unify(K1.dom), *_unify_gens(K0.orig_ext, K1.orig_ext))
        elif K0.is_AlgebraicField:
            return K0
        elif K1.is_AlgebraicField:
            return K1

        if K0.is_RationalField:
            return K0
        if K1.is_RationalField:
            return K1

        if K0.is_IntegerRing:
            return K0
        if K1.is_IntegerRing:
            return K1

        if K0.is_FiniteField and K1.is_FiniteField:
            return K0.__class__(max(K0.mod, K1.mod, key=default_sort_key))

        from sympy.polys.domains import EX
        return EX

    def __eq__(self, other):
        """Returns ``True`` if two domains are equivalent. """
        return isinstance(other, Domain) and self.dtype == other.dtype

    def __ne__(self, other):
        """Returns ``False`` if two domains are equivalent. """
        return not self == other

    def map(self, seq):
        """Rersively apply ``self`` to all elements of ``seq``. """
        result = []

        for elt in seq:
            if isinstance(elt, list):
                result.append(self.map(elt))
            else:
                result.append(self(elt))

        return result

    def get_ring(self):
        """Returns a ring associated with ``self``. """
        raise DomainError('there is no ring associated with %s' % self)

    def get_field(self):
        """Returns a field associated with ``self``. """
        raise DomainError('there is no field associated with %s' % self)

    def get_exact(self):
        """Returns an exact domain associated with ``self``. """
        return self

    def __getitem__(self, symbols):
        """The mathematical way to make a polynomial ring. """
        if hasattr(symbols, '__iter__'):
            return self.poly_ring(*symbols)
        else:
            return self.poly_ring(symbols)

    def poly_ring(self, *symbols, **kwargs):
        """Returns a polynomial ring, i.e. `K[X]`. """
        from sympy.polys.domains.polynomialring import PolynomialRing
        return PolynomialRing(self, symbols, kwargs.get("order", lex))

    def frac_field(self, *symbols, **kwargs):
        """Returns a fraction field, i.e. `K(X)`. """
        from sympy.polys.domains.fractionfield import FractionField
        return FractionField(self, symbols, kwargs.get("order", lex))

    def old_poly_ring(self, *symbols, **kwargs):
        """Returns a polynomial ring, i.e. `K[X]`. """
        from sympy.polys.domains.old_polynomialring import PolynomialRing
        return PolynomialRing(self, *symbols, **kwargs)

    def old_frac_field(self, *symbols, **kwargs):
        """Returns a fraction field, i.e. `K(X)`. """
        from sympy.polys.domains.old_fractionfield import FractionField
        return FractionField(self, *symbols, **kwargs)

    def algebraic_field(self, *extension):
        r"""Returns an algebraic field, i.e. `K(\alpha, \ldots)`. """
        raise DomainError("can't create algebraic field over %s" % self)

    def inject(self, *symbols):
        """Inject generators into this domain. """
        raise NotImplementedError

    def is_zero(self, a):
        """Returns True if ``a`` is zero. """
        return not a

    def is_one(self, a):
        """Returns True if ``a`` is one. """
        return a == self.one

    def is_positive(self, a):
        """Returns True if ``a`` is positive. """
        return a > 0

    def is_negative(self, a):
        """Returns True if ``a`` is negative. """
        return a < 0

    def is_nonpositive(self, a):
        """Returns True if ``a`` is non-positive. """
        return a <= 0

    def is_nonnegative(self, a):
        """Returns True if ``a`` is non-negative. """
        return a >= 0

    def abs(self, a):
        """Absolute value of ``a``, implies ``__abs__``. """
        return abs(a)

    def neg(self, a):
        """Returns ``a`` negated, implies ``__neg__``. """
        return -a

    def pos(self, a):
        """Returns ``a`` positive, implies ``__pos__``. """
        return +a

    def add(self, a, b):
        """Sum of ``a`` and ``b``, implies ``__add__``.  """
        return a + b

    def sub(self, a, b):
        """Difference of ``a`` and ``b``, implies ``__sub__``.  """
        return a - b

    def mul(self, a, b):
        """Product of ``a`` and ``b``, implies ``__mul__``.  """
        return a * b

    def pow(self, a, b):
        """Raise ``a`` to power ``b``, implies ``__pow__``.  """
        return a ** b

    def exquo(self, a, b):
        """Exact quotient of ``a`` and ``b``, implies something. """
        raise NotImplementedError

    def quo(self, a, b):
        """Quotient of ``a`` and ``b``, implies something.  """
        raise NotImplementedError

    def rem(self, a, b):
        """Remainder of ``a`` and ``b``, implies ``__mod__``.  """
        raise NotImplementedError

    def div(self, a, b):
        """Division of ``a`` and ``b``, implies something. """
        raise NotImplementedError

    def invert(self, a, b):
        """Returns inversion of ``a mod b``, implies something. """
        raise NotImplementedError

    def revert(self, a):
        """Returns ``a**(-1)`` if possible. """
        raise NotImplementedError

    def numer(self, a):
        """Returns numerator of ``a``. """
        raise NotImplementedError

    def denom(self, a):
        """Returns denominator of ``a``. """
        raise NotImplementedError

    def half_gcdex(self, a, b):
        """Half extended GCD of ``a`` and ``b``. """
        s, t, h = self.gcdex(a, b)
        return s, h

    def gcdex(self, a, b):
        """Extended GCD of ``a`` and ``b``. """
        raise NotImplementedError

    def cofactors(self, a, b):
        """Returns GCD and cofactors of ``a`` and ``b``. """
        gcd = self.gcd(a, b)
        cfa = self.quo(a, gcd)
        cfb = self.quo(b, gcd)
        return gcd, cfa, cfb

    def gcd(self, a, b):
        """Returns GCD of ``a`` and ``b``. """
        raise NotImplementedError

    def lcm(self, a, b):
        """Returns LCM of ``a`` and ``b``. """
        raise NotImplementedError

    def log(self, a, b):
        """Returns b-base logarithm of ``a``. """
        raise NotImplementedError

    def sqrt(self, a):
        """Returns square root of ``a``. """
        raise NotImplementedError

    def evalf(self, a, prec=None, **options):
        """Returns numerical approximation of ``a``. """
        return self.to_sympy(a).evalf(prec, **options)

    n = evalf

    def real(self, a):
        return a

    def imag(self, a):
        return self.zero

    def almosteq(self, a, b, tolerance=None):
        """Check if ``a`` and ``b`` are almost equal. """
        return a == b

    def characteristic(self):
        """Return the characteristic of this domain. """
        raise NotImplementedError('characteristic()')
