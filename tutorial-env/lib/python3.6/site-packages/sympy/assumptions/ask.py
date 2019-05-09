"""Module for querying SymPy objects about assumptions."""
from __future__ import print_function, division

from sympy.assumptions.assume import (global_assumptions, Predicate,
        AppliedPredicate)
from sympy.core import sympify
from sympy.core.cache import cacheit
from sympy.core.decorators import deprecated
from sympy.core.relational import Relational
from sympy.logic.boolalg import (to_cnf, And, Not, Or, Implies, Equivalent,
    BooleanFunction, BooleanAtom)
from sympy.logic.inference import satisfiable
from sympy.utilities.decorator import memoize_property


# Deprecated predicates should be added to this list
deprecated_predicates = [
    'bounded',
    'infinity',
    'infinitesimal'
]

# Memoization storage for predicates
predicate_storage = {}
predicate_memo = memoize_property(predicate_storage)
# Memoization is necessary for the properties of AssumptionKeys to
# ensure that only one object of Predicate objects are created.
# This is because assumption handlers are registered on those objects.


class AssumptionKeys(object):
    """
    This class contains all the supported keys by ``ask``.
    """

    @predicate_memo
    def hermitian(self):
        """
        Hermitian predicate.

        ``ask(Q.hermitian(x))`` is true iff ``x`` belongs to the set of
        Hermitian operators.

        References
        ==========

        .. [1] http://mathworld.wolfram.com/HermitianOperator.html

        """
        # TODO: Add examples
        return Predicate('hermitian')

    @predicate_memo
    def antihermitian(self):
        """
        Antihermitian predicate.

        ``Q.antihermitian(x)`` is true iff ``x`` belongs to the field of
        antihermitian operators, i.e., operators in the form ``x*I``, where
        ``x`` is Hermitian.

        References
        ==========

        .. [1] http://mathworld.wolfram.com/HermitianOperator.html

        """
        # TODO: Add examples
        return Predicate('antihermitian')

    @predicate_memo
    def real(self):
        r"""
        Real number predicate.

        ``Q.real(x)`` is true iff ``x`` is a real number, i.e., it is in the
        interval `(-\infty, \infty)`.  Note that, in particular the infinities
        are not real. Use ``Q.extended_real`` if you want to consider those as
        well.

        A few important facts about reals:

        - Every real number is positive, negative, or zero.  Furthermore,
          because these sets are pairwise disjoint, each real number is exactly
          one of those three.

        - Every real number is also complex.

        - Every real number is finite.

        - Every real number is either rational or irrational.

        - Every real number is either algebraic or transcendental.

        - The facts ``Q.negative``, ``Q.zero``, ``Q.positive``,
          ``Q.nonnegative``, ``Q.nonpositive``, ``Q.nonzero``, ``Q.integer``,
          ``Q.rational``, and ``Q.irrational`` all imply ``Q.real``, as do all
          facts that imply those facts.

        - The facts ``Q.algebraic``, and ``Q.transcendental`` do not imply
          ``Q.real``; they imply ``Q.complex``. An algebraic or transcendental
          number may or may not be real.

        - The "non" facts (i.e., ``Q.nonnegative``, ``Q.nonzero``,
          ``Q.nonpositive`` and ``Q.noninteger``) are not equivalent to not the
          fact, but rather, not the fact *and* ``Q.real``.  For example,
          ``Q.nonnegative`` means ``~Q.negative & Q.real``. So for example,
          ``I`` is not nonnegative, nonzero, or nonpositive.

        Examples
        ========

        >>> from sympy import Q, ask, symbols
        >>> x = symbols('x')
        >>> ask(Q.real(x), Q.positive(x))
        True
        >>> ask(Q.real(0))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Real_number

        """
        return Predicate('real')

    @predicate_memo
    def extended_real(self):
        r"""
        Extended real predicate.

        ``Q.extended_real(x)`` is true iff ``x`` is a real number or
        `\{-\infty, \infty\}`.

        See documentation of ``Q.real`` for more information about related facts.

        Examples
        ========

        >>> from sympy import ask, Q, oo, I
        >>> ask(Q.extended_real(1))
        True
        >>> ask(Q.extended_real(I))
        False
        >>> ask(Q.extended_real(oo))
        True

        """
        return Predicate('extended_real')

    @predicate_memo
    def imaginary(self):
        """
        Imaginary number predicate.

        ``Q.imaginary(x)`` is true iff ``x`` can be written as a real
        number multiplied by the imaginary unit ``I``. Please note that ``0``
        is not considered to be an imaginary number.

        Examples
        ========

        >>> from sympy import Q, ask, I
        >>> ask(Q.imaginary(3*I))
        True
        >>> ask(Q.imaginary(2 + 3*I))
        False
        >>> ask(Q.imaginary(0))
        False

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Imaginary_number

        """
        return Predicate('imaginary')

    @predicate_memo
    def complex(self):
        """
        Complex number predicate.

        ``Q.complex(x)`` is true iff ``x`` belongs to the set of complex
        numbers. Note that every complex number is finite.

        Examples
        ========

        >>> from sympy import Q, Symbol, ask, I, oo
        >>> x = Symbol('x')
        >>> ask(Q.complex(0))
        True
        >>> ask(Q.complex(2 + 3*I))
        True
        >>> ask(Q.complex(oo))
        False

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Complex_number

        """
        return Predicate('complex')

    @predicate_memo
    def algebraic(self):
        r"""
        Algebraic number predicate.

        ``Q.algebraic(x)`` is true iff ``x`` belongs to the set of
        algebraic numbers. ``x`` is algebraic if there is some polynomial
        in ``p(x)\in \mathbb\{Q\}[x]`` such that ``p(x) = 0``.

        Examples
        ========

        >>> from sympy import ask, Q, sqrt, I, pi
        >>> ask(Q.algebraic(sqrt(2)))
        True
        >>> ask(Q.algebraic(I))
        True
        >>> ask(Q.algebraic(pi))
        False

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Algebraic_number
        """
        return Predicate('algebraic')

    @predicate_memo
    def transcendental(self):
        """
        Transcedental number predicate.

        ``Q.transcendental(x)`` is true iff ``x`` belongs to the set of
        transcendental numbers. A transcendental number is a real
        or complex number that is not algebraic.

        """
        # TODO: Add examples
        return Predicate('transcendental')

    @predicate_memo
    def integer(self):
        """
        Integer predicate.

        ``Q.integer(x)`` is true iff ``x`` belongs to the set of integer numbers.

        Examples
        ========

        >>> from sympy import Q, ask, S
        >>> ask(Q.integer(5))
        True
        >>> ask(Q.integer(S(1)/2))
        False

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Integer

        """
        return Predicate('integer')

    @predicate_memo
    def rational(self):
        """
        Rational number predicate.

        ``Q.rational(x)`` is true iff ``x`` belongs to the set of
        rational numbers.

        Examples
        ========

        >>> from sympy import ask, Q, pi, S
        >>> ask(Q.rational(0))
        True
        >>> ask(Q.rational(S(1)/2))
        True
        >>> ask(Q.rational(pi))
        False

        References
        ==========

        https://en.wikipedia.org/wiki/Rational_number

        """
        return Predicate('rational')

    @predicate_memo
    def irrational(self):
        """
        Irrational number predicate.

        ``Q.irrational(x)`` is true iff ``x``  is any real number that
        cannot be expressed as a ratio of integers.

        Examples
        ========

        >>> from sympy import ask, Q, pi, S, I
        >>> ask(Q.irrational(0))
        False
        >>> ask(Q.irrational(S(1)/2))
        False
        >>> ask(Q.irrational(pi))
        True
        >>> ask(Q.irrational(I))
        False

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Irrational_number

        """
        return Predicate('irrational')

    @predicate_memo
    def finite(self):
        """
        Finite predicate.

        ``Q.finite(x)`` is true if ``x`` is neither an infinity
        nor a ``NaN``. In other words, ``ask(Q.finite(x))`` is true for all ``x``
        having a bounded absolute value.

        Examples
        ========

        >>> from sympy import Q, ask, Symbol, S, oo, I
        >>> x = Symbol('x')
        >>> ask(Q.finite(S.NaN))
        False
        >>> ask(Q.finite(oo))
        False
        >>> ask(Q.finite(1))
        True
        >>> ask(Q.finite(2 + 3*I))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Finite

        """
        return Predicate('finite')

    @predicate_memo
    @deprecated(useinstead="finite", issue=9425, deprecated_since_version="1.0")
    def bounded(self):
        """
        See documentation of ``Q.finite``.
        """
        return Predicate('finite')

    @predicate_memo
    def infinite(self):
        """
        Infinite number predicate.

        ``Q.infinite(x)`` is true iff the absolute value of ``x`` is
        infinity.

        """
        # TODO: Add examples
        return Predicate('infinite')

    @predicate_memo
    @deprecated(useinstead="infinite", issue=9426, deprecated_since_version="1.0")
    def infinity(self):
        """
        See documentation of ``Q.infinite``.
        """
        return Predicate('infinite')

    @predicate_memo
    @deprecated(useinstead="zero", issue=9675, deprecated_since_version="1.0")
    def infinitesimal(self):
        """
        See documentation of ``Q.zero``.
        """
        return Predicate('zero')

    @predicate_memo
    def positive(self):
        r"""
        Positive real number predicate.

        ``Q.positive(x)`` is true iff ``x`` is real and `x > 0`, that is if ``x``
        is in the interval `(0, \infty)`.  In particular, infinity is not
        positive.

        A few important facts about positive numbers:

        - Note that ``Q.nonpositive`` and ``~Q.positive`` are *not* the same
          thing. ``~Q.positive(x)`` simply means that ``x`` is not positive,
          whereas ``Q.nonpositive(x)`` means that ``x`` is real and not
          positive, i.e., ``Q.nonpositive(x)`` is logically equivalent to
          `Q.negative(x) | Q.zero(x)``.  So for example, ``~Q.positive(I)`` is
          true, whereas ``Q.nonpositive(I)`` is false.

        - See the documentation of ``Q.real`` for more information about
          related facts.

        Examples
        ========

        >>> from sympy import Q, ask, symbols, I
        >>> x = symbols('x')
        >>> ask(Q.positive(x), Q.real(x) & ~Q.negative(x) & ~Q.zero(x))
        True
        >>> ask(Q.positive(1))
        True
        >>> ask(Q.nonpositive(I))
        False
        >>> ask(~Q.positive(I))
        True

        """
        return Predicate('positive')

    @predicate_memo
    def negative(self):
        r"""
        Negative number predicate.

        ``Q.negative(x)`` is true iff ``x`` is a real number and :math:`x < 0`, that is,
        it is in the interval :math:`(-\infty, 0)`.  Note in particular that negative
        infinity is not negative.

        A few important facts about negative numbers:

        - Note that ``Q.nonnegative`` and ``~Q.negative`` are *not* the same
          thing. ``~Q.negative(x)`` simply means that ``x`` is not negative,
          whereas ``Q.nonnegative(x)`` means that ``x`` is real and not
          negative, i.e., ``Q.nonnegative(x)`` is logically equivalent to
          ``Q.zero(x) | Q.positive(x)``.  So for example, ``~Q.negative(I)`` is
          true, whereas ``Q.nonnegative(I)`` is false.

        - See the documentation of ``Q.real`` for more information about
          related facts.

        Examples
        ========

        >>> from sympy import Q, ask, symbols, I
        >>> x = symbols('x')
        >>> ask(Q.negative(x), Q.real(x) & ~Q.positive(x) & ~Q.zero(x))
        True
        >>> ask(Q.negative(-1))
        True
        >>> ask(Q.nonnegative(I))
        False
        >>> ask(~Q.negative(I))
        True

        """
        return Predicate('negative')

    @predicate_memo
    def zero(self):
        """
        Zero number predicate.

        ``ask(Q.zero(x))`` is true iff the value of ``x`` is zero.

        Examples
        ========

        >>> from sympy import ask, Q, oo, symbols
        >>> x, y = symbols('x, y')
        >>> ask(Q.zero(0))
        True
        >>> ask(Q.zero(1/oo))
        True
        >>> ask(Q.zero(0*oo))
        False
        >>> ask(Q.zero(1))
        False
        >>> ask(Q.zero(x*y), Q.zero(x) | Q.zero(y))
        True

        """
        return Predicate('zero')

    @predicate_memo
    def nonzero(self):
        """
        Nonzero real number predicate.

        ``ask(Q.nonzero(x))`` is true iff ``x`` is real and ``x`` is not zero.  Note in
        particular that ``Q.nonzero(x)`` is false if ``x`` is not real.  Use
        ``~Q.zero(x)`` if you want the negation of being zero without any real
        assumptions.

        A few important facts about nonzero numbers:

        - ``Q.nonzero`` is logically equivalent to ``Q.positive | Q.negative``.

        - See the documentation of ``Q.real`` for more information about
          related facts.

        Examples
        ========

        >>> from sympy import Q, ask, symbols, I, oo
        >>> x = symbols('x')
        >>> print(ask(Q.nonzero(x), ~Q.zero(x)))
        None
        >>> ask(Q.nonzero(x), Q.positive(x))
        True
        >>> ask(Q.nonzero(x), Q.zero(x))
        False
        >>> ask(Q.nonzero(0))
        False
        >>> ask(Q.nonzero(I))
        False
        >>> ask(~Q.zero(I))
        True
        >>> ask(Q.nonzero(oo))  #doctest: +SKIP
        False

        """
        return Predicate('nonzero')

    @predicate_memo
    def nonpositive(self):
        """
        Nonpositive real number predicate.

        ``ask(Q.nonpositive(x))`` is true iff ``x`` belongs to the set of
        negative numbers including zero.

        - Note that ``Q.nonpositive`` and ``~Q.positive`` are *not* the same
          thing. ``~Q.positive(x)`` simply means that ``x`` is not positive,
          whereas ``Q.nonpositive(x)`` means that ``x`` is real and not
          positive, i.e., ``Q.nonpositive(x)`` is logically equivalent to
          `Q.negative(x) | Q.zero(x)``.  So for example, ``~Q.positive(I)`` is
          true, whereas ``Q.nonpositive(I)`` is false.

        Examples
        ========

        >>> from sympy import Q, ask, I
        >>> ask(Q.nonpositive(-1))
        True
        >>> ask(Q.nonpositive(0))
        True
        >>> ask(Q.nonpositive(1))
        False
        >>> ask(Q.nonpositive(I))
        False
        >>> ask(Q.nonpositive(-I))
        False

        """
        return Predicate('nonpositive')

    @predicate_memo
    def nonnegative(self):
        """
        Nonnegative real number predicate.

        ``ask(Q.nonnegative(x))`` is true iff ``x`` belongs to the set of
        positive numbers including zero.

        - Note that ``Q.nonnegative`` and ``~Q.negative`` are *not* the same
          thing. ``~Q.negative(x)`` simply means that ``x`` is not negative,
          whereas ``Q.nonnegative(x)`` means that ``x`` is real and not
          negative, i.e., ``Q.nonnegative(x)`` is logically equivalent to
          ``Q.zero(x) | Q.positive(x)``.  So for example, ``~Q.negative(I)`` is
          true, whereas ``Q.nonnegative(I)`` is false.

        Examples
        ========

        >>> from sympy import Q, ask, I
        >>> ask(Q.nonnegative(1))
        True
        >>> ask(Q.nonnegative(0))
        True
        >>> ask(Q.nonnegative(-1))
        False
        >>> ask(Q.nonnegative(I))
        False
        >>> ask(Q.nonnegative(-I))
        False

        """
        return Predicate('nonnegative')

    @predicate_memo
    def even(self):
        """
        Even number predicate.

        ``ask(Q.even(x))`` is true iff ``x`` belongs to the set of even
        integers.

        Examples
        ========

        >>> from sympy import Q, ask, pi
        >>> ask(Q.even(0))
        True
        >>> ask(Q.even(2))
        True
        >>> ask(Q.even(3))
        False
        >>> ask(Q.even(pi))
        False

        """
        return Predicate('even')

    @predicate_memo
    def odd(self):
        """
        Odd number predicate.

        ``ask(Q.odd(x))`` is true iff ``x`` belongs to the set of odd numbers.

        Examples
        ========

        >>> from sympy import Q, ask, pi
        >>> ask(Q.odd(0))
        False
        >>> ask(Q.odd(2))
        False
        >>> ask(Q.odd(3))
        True
        >>> ask(Q.odd(pi))
        False

        """
        return Predicate('odd')

    @predicate_memo
    def prime(self):
        """
        Prime number predicate.

        ``ask(Q.prime(x))`` is true iff ``x`` is a natural number greater
        than 1 that has no positive divisors other than ``1`` and the
        number itself.

        Examples
        ========

        >>> from sympy import Q, ask
        >>> ask(Q.prime(0))
        False
        >>> ask(Q.prime(1))
        False
        >>> ask(Q.prime(2))
        True
        >>> ask(Q.prime(20))
        False
        >>> ask(Q.prime(-3))
        False

        """
        return Predicate('prime')

    @predicate_memo
    def composite(self):
        """
        Composite number predicate.

        ``ask(Q.composite(x))`` is true iff ``x`` is a positive integer and has
        at least one positive divisor other than ``1`` and the number itself.

        Examples
        ========

        >>> from sympy import Q, ask
        >>> ask(Q.composite(0))
        False
        >>> ask(Q.composite(1))
        False
        >>> ask(Q.composite(2))
        False
        >>> ask(Q.composite(20))
        True

        """
        return Predicate('composite')

    @predicate_memo
    def commutative(self):
        """
        Commutative predicate.

        ``ask(Q.commutative(x))`` is true iff ``x`` commutes with any other
        object with respect to multiplication operation.

        """
        # TODO: Add examples
        return Predicate('commutative')

    @predicate_memo
    def is_true(self):
        """
        Generic predicate.

        ``ask(Q.is_true(x))`` is true iff ``x`` is true. This only makes
        sense if ``x`` is a predicate.

        Examples
        ========

        >>> from sympy import ask, Q, symbols
        >>> x = symbols('x')
        >>> ask(Q.is_true(True))
        True

        """
        return Predicate('is_true')

    @predicate_memo
    def symmetric(self):
        """
        Symmetric matrix predicate.

        ``Q.symmetric(x)`` is true iff ``x`` is a square matrix and is equal to
        its transpose. Every square diagonal matrix is a symmetric matrix.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 2, 2)
        >>> Y = MatrixSymbol('Y', 2, 3)
        >>> Z = MatrixSymbol('Z', 2, 2)
        >>> ask(Q.symmetric(X*Z), Q.symmetric(X) & Q.symmetric(Z))
        True
        >>> ask(Q.symmetric(X + Z), Q.symmetric(X) & Q.symmetric(Z))
        True
        >>> ask(Q.symmetric(Y))
        False


        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Symmetric_matrix

        """
        # TODO: Add handlers to make these keys work with
        # actual matrices and add more examples in the docstring.
        return Predicate('symmetric')

    @predicate_memo
    def invertible(self):
        """
        Invertible matrix predicate.

        ``Q.invertible(x)`` is true iff ``x`` is an invertible matrix.
        A square matrix is called invertible only if its determinant is 0.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 2, 2)
        >>> Y = MatrixSymbol('Y', 2, 3)
        >>> Z = MatrixSymbol('Z', 2, 2)
        >>> ask(Q.invertible(X*Y), Q.invertible(X))
        False
        >>> ask(Q.invertible(X*Z), Q.invertible(X) & Q.invertible(Z))
        True
        >>> ask(Q.invertible(X), Q.fullrank(X) & Q.square(X))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Invertible_matrix

        """
        return Predicate('invertible')

    @predicate_memo
    def orthogonal(self):
        """
        Orthogonal matrix predicate.

        ``Q.orthogonal(x)`` is true iff ``x`` is an orthogonal matrix.
        A square matrix ``M`` is an orthogonal matrix if it satisfies
        ``M^TM = MM^T = I`` where ``M^T`` is the transpose matrix of
        ``M`` and ``I`` is an identity matrix. Note that an orthogonal
        matrix is necessarily invertible.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol, Identity
        >>> X = MatrixSymbol('X', 2, 2)
        >>> Y = MatrixSymbol('Y', 2, 3)
        >>> Z = MatrixSymbol('Z', 2, 2)
        >>> ask(Q.orthogonal(Y))
        False
        >>> ask(Q.orthogonal(X*Z*X), Q.orthogonal(X) & Q.orthogonal(Z))
        True
        >>> ask(Q.orthogonal(Identity(3)))
        True
        >>> ask(Q.invertible(X), Q.orthogonal(X))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Orthogonal_matrix

        """
        return Predicate('orthogonal')

    @predicate_memo
    def unitary(self):
        """
        Unitary matrix predicate.

        ``Q.unitary(x)`` is true iff ``x`` is a unitary matrix.
        Unitary matrix is an analogue to orthogonal matrix. A square
        matrix ``M`` with complex elements is unitary if :math:``M^TM = MM^T= I``
        where :math:``M^T`` is the conjugate transpose matrix of ``M``.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol, Identity
        >>> X = MatrixSymbol('X', 2, 2)
        >>> Y = MatrixSymbol('Y', 2, 3)
        >>> Z = MatrixSymbol('Z', 2, 2)
        >>> ask(Q.unitary(Y))
        False
        >>> ask(Q.unitary(X*Z*X), Q.unitary(X) & Q.unitary(Z))
        True
        >>> ask(Q.unitary(Identity(3)))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Unitary_matrix

        """
        return Predicate('unitary')

    @predicate_memo
    def positive_definite(self):
        r"""
        Positive definite matrix predicate.

        If ``M`` is a :math:``n \times n`` symmetric real matrix, it is said
        to be positive definite if :math:`Z^TMZ` is positive for
        every non-zero column vector ``Z`` of ``n`` real numbers.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol, Identity
        >>> X = MatrixSymbol('X', 2, 2)
        >>> Y = MatrixSymbol('Y', 2, 3)
        >>> Z = MatrixSymbol('Z', 2, 2)
        >>> ask(Q.positive_definite(Y))
        False
        >>> ask(Q.positive_definite(Identity(3)))
        True
        >>> ask(Q.positive_definite(X + Z), Q.positive_definite(X) &
        ...     Q.positive_definite(Z))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Positive-definite_matrix

        """
        return Predicate('positive_definite')

    @predicate_memo
    def upper_triangular(self):
        """
        Upper triangular matrix predicate.

        A matrix ``M`` is called upper triangular matrix if :math:`M_{ij}=0`
        for :math:`i<j`.

        Examples
        ========

        >>> from sympy import Q, ask, ZeroMatrix, Identity
        >>> ask(Q.upper_triangular(Identity(3)))
        True
        >>> ask(Q.upper_triangular(ZeroMatrix(3, 3)))
        True

        References
        ==========

        .. [1] http://mathworld.wolfram.com/UpperTriangularMatrix.html

        """
        return Predicate('upper_triangular')

    @predicate_memo
    def lower_triangular(self):
        """
        Lower triangular matrix predicate.

        A matrix ``M`` is called lower triangular matrix if :math:`a_{ij}=0`
        for :math:`i>j`.

        Examples
        ========

        >>> from sympy import Q, ask, ZeroMatrix, Identity
        >>> ask(Q.lower_triangular(Identity(3)))
        True
        >>> ask(Q.lower_triangular(ZeroMatrix(3, 3)))
        True

        References
        ==========

        .. [1] http://mathworld.wolfram.com/LowerTriangularMatrix.html
        """
        return Predicate('lower_triangular')

    @predicate_memo
    def diagonal(self):
        """
        Diagonal matrix predicate.

        ``Q.diagonal(x)`` is true iff ``x`` is a diagonal matrix. A diagonal
        matrix is a matrix in which the entries outside the main diagonal
        are all zero.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol, ZeroMatrix
        >>> X = MatrixSymbol('X', 2, 2)
        >>> ask(Q.diagonal(ZeroMatrix(3, 3)))
        True
        >>> ask(Q.diagonal(X), Q.lower_triangular(X) &
        ...     Q.upper_triangular(X))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Diagonal_matrix

        """
        return Predicate('diagonal')

    @predicate_memo
    def fullrank(self):
        """
        Fullrank matrix predicate.

        ``Q.fullrank(x)`` is true iff ``x`` is a full rank matrix.
        A matrix is full rank if all rows and columns of the matrix
        are linearly independent. A square matrix is full rank iff
        its determinant is nonzero.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol, ZeroMatrix, Identity
        >>> X = MatrixSymbol('X', 2, 2)
        >>> ask(Q.fullrank(X.T), Q.fullrank(X))
        True
        >>> ask(Q.fullrank(ZeroMatrix(3, 3)))
        False
        >>> ask(Q.fullrank(Identity(3)))
        True

        """
        return Predicate('fullrank')

    @predicate_memo
    def square(self):
        """
        Square matrix predicate.

        ``Q.square(x)`` is true iff ``x`` is a square matrix. A square matrix
        is a matrix with the same number of rows and columns.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol, ZeroMatrix, Identity
        >>> X = MatrixSymbol('X', 2, 2)
        >>> Y = MatrixSymbol('X', 2, 3)
        >>> ask(Q.square(X))
        True
        >>> ask(Q.square(Y))
        False
        >>> ask(Q.square(ZeroMatrix(3, 3)))
        True
        >>> ask(Q.square(Identity(3)))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Square_matrix

        """
        return Predicate('square')

    @predicate_memo
    def integer_elements(self):
        """
        Integer elements matrix predicate.

        ``Q.integer_elements(x)`` is true iff all the elements of ``x``
        are integers.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 4, 4)
        >>> ask(Q.integer(X[1, 2]), Q.integer_elements(X))
        True

        """
        return Predicate('integer_elements')

    @predicate_memo
    def real_elements(self):
        """
        Real elements matrix predicate.

        ``Q.real_elements(x)`` is true iff all the elements of ``x``
        are real numbers.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 4, 4)
        >>> ask(Q.real(X[1, 2]), Q.real_elements(X))
        True

        """
        return Predicate('real_elements')

    @predicate_memo
    def complex_elements(self):
        """
        Complex elements matrix predicate.

        ``Q.complex_elements(x)`` is true iff all the elements of ``x``
        are complex numbers.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 4, 4)
        >>> ask(Q.complex(X[1, 2]), Q.complex_elements(X))
        True
        >>> ask(Q.complex_elements(X), Q.integer_elements(X))
        True

        """
        return Predicate('complex_elements')

    @predicate_memo
    def singular(self):
        """
        Singular matrix predicate.

        A matrix is singular iff the value of its determinant is 0.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 4, 4)
        >>> ask(Q.singular(X), Q.invertible(X))
        False
        >>> ask(Q.singular(X), ~Q.invertible(X))
        True

        References
        ==========

        .. [1] http://mathworld.wolfram.com/SingularMatrix.html

        """
        return Predicate('singular')

    @predicate_memo
    def normal(self):
        """
        Normal matrix predicate.

        A matrix is normal if it commutes with its conjugate transpose.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 4, 4)
        >>> ask(Q.normal(X), Q.unitary(X))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Normal_matrix

        """
        return Predicate('normal')

    @predicate_memo
    def triangular(self):
        """
        Triangular matrix predicate.

        ``Q.triangular(X)`` is true if ``X`` is one that is either lower
        triangular or upper triangular.

        Examples
        ========
        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 4, 4)
        >>> ask(Q.triangular(X), Q.upper_triangular(X))
        True
        >>> ask(Q.triangular(X), Q.lower_triangular(X))
        True

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Triangular_matrix

        """
        return Predicate('triangular')

    @predicate_memo
    def unit_triangular(self):
        """
        Unit triangular matrix predicate.

        A unit triangular matrix is a triangular matrix with 1s
        on the diagonal.

        Examples
        ========

        >>> from sympy import Q, ask, MatrixSymbol
        >>> X = MatrixSymbol('X', 4, 4)
        >>> ask(Q.triangular(X), Q.unit_triangular(X))
        True

        """
        return Predicate('unit_triangular')


Q = AssumptionKeys()

def _extract_facts(expr, symbol, check_reversed_rel=True):
    """
    Helper for ask().

    Extracts the facts relevant to the symbol from an assumption.
    Returns None if there is nothing to extract.
    """
    if isinstance(symbol, Relational):
        if check_reversed_rel:
            rev = _extract_facts(expr, symbol.reversed, False)
            if rev is not None:
                return rev
    if isinstance(expr, bool):
        return
    if not expr.has(symbol):
        return
    if isinstance(expr, AppliedPredicate):
        if expr.arg == symbol:
            return expr.func
        else:
            return
    if isinstance(expr, Not) and expr.args[0].func in (And, Or):
        cls = Or if expr.args[0] == And else And
        expr = cls(*[~arg for arg in expr.args[0].args])
    args = [_extract_facts(arg, symbol) for arg in expr.args]
    if isinstance(expr, And):
        args = [x for x in args if x is not None]
        if args:
            return expr.func(*args)
    if args and all(x is not None for x in args):
        return expr.func(*args)


def ask(proposition, assumptions=True, context=global_assumptions):
    """
    Method for inferring properties about objects.

    **Syntax**

        * ask(proposition)

        * ask(proposition, assumptions)

            where ``proposition`` is any boolean expression

    Examples
    ========

    >>> from sympy import ask, Q, pi
    >>> from sympy.abc import x, y
    >>> ask(Q.rational(pi))
    False
    >>> ask(Q.even(x*y), Q.even(x) & Q.integer(y))
    True
    >>> ask(Q.prime(4*x), Q.integer(x))
    False

    **Remarks**
        Relations in assumptions are not implemented (yet), so the following
        will not give a meaningful result.

        >>> ask(Q.positive(x), Q.is_true(x > 0)) # doctest: +SKIP

        It is however a work in progress.

    """
    from sympy.assumptions.satask import satask

    if not isinstance(proposition, (BooleanFunction, AppliedPredicate, bool, BooleanAtom)):
        raise TypeError("proposition must be a valid logical expression")

    if not isinstance(assumptions, (BooleanFunction, AppliedPredicate, bool, BooleanAtom)):
        raise TypeError("assumptions must be a valid logical expression")

    if isinstance(proposition, AppliedPredicate):
        key, expr = proposition.func, sympify(proposition.arg)
    else:
        key, expr = Q.is_true, sympify(proposition)

    assumptions = And(assumptions, And(*context))
    assumptions = to_cnf(assumptions)

    local_facts = _extract_facts(assumptions, expr)

    known_facts_cnf = get_known_facts_cnf()
    known_facts_dict = get_known_facts_dict()

    if local_facts and satisfiable(And(local_facts, known_facts_cnf)) is False:
        raise ValueError("inconsistent assumptions %s" % assumptions)

    # direct resolution method, no logic
    res = key(expr)._eval_ask(assumptions)
    if res is not None:
        return bool(res)

    if local_facts is None:
        return satask(proposition, assumptions=assumptions, context=context)


    # See if there's a straight-forward conclusion we can make for the inference
    if local_facts.is_Atom:
        if key in known_facts_dict[local_facts]:
            return True
        if Not(key) in known_facts_dict[local_facts]:
            return False
    elif (isinstance(local_facts, And) and
            all(k in known_facts_dict for k in local_facts.args)):
        for assum in local_facts.args:
            if assum.is_Atom:
                if key in known_facts_dict[assum]:
                    return True
                if Not(key) in known_facts_dict[assum]:
                    return False
            elif isinstance(assum, Not) and assum.args[0].is_Atom:
                if key in known_facts_dict[assum]:
                    return False
                if Not(key) in known_facts_dict[assum]:
                    return True
    elif (isinstance(key, Predicate) and
            isinstance(local_facts, Not) and local_facts.args[0].is_Atom):
        if local_facts.args[0] in known_facts_dict[key]:
            return False

    # Failing all else, we do a full logical inference
    res = ask_full_inference(key, local_facts, known_facts_cnf)
    if res is None:
        return satask(proposition, assumptions=assumptions, context=context)
    return res


def ask_full_inference(proposition, assumptions, known_facts_cnf):
    """
    Method for inferring properties about objects.

    """
    if not satisfiable(And(known_facts_cnf, assumptions, proposition)):
        return False
    if not satisfiable(And(known_facts_cnf, assumptions, Not(proposition))):
        return True
    return None


def register_handler(key, handler):
    """
    Register a handler in the ask system. key must be a string and handler a
    class inheriting from AskHandler::

        >>> from sympy.assumptions import register_handler, ask, Q
        >>> from sympy.assumptions.handlers import AskHandler
        >>> class MersenneHandler(AskHandler):
        ...     # Mersenne numbers are in the form 2**n - 1, n integer
        ...     @staticmethod
        ...     def Integer(expr, assumptions):
        ...         from sympy import log
        ...         return ask(Q.integer(log(expr + 1, 2)))
        >>> register_handler('mersenne', MersenneHandler)
        >>> ask(Q.mersenne(7))
        True

    """
    if type(key) is Predicate:
        key = key.name
    Qkey = getattr(Q, key, None)
    if Qkey is not None:
        Qkey.add_handler(handler)
    else:
        setattr(Q, key, Predicate(key, handlers=[handler]))


def remove_handler(key, handler):
    """Removes a handler from the ask system. Same syntax as register_handler"""
    if type(key) is Predicate:
        key = key.name
    getattr(Q, key).remove_handler(handler)


def single_fact_lookup(known_facts_keys, known_facts_cnf):
    # Compute the quick lookup for single facts
    mapping = {}
    for key in known_facts_keys:
        mapping[key] = {key}
        for other_key in known_facts_keys:
            if other_key != key:
                if ask_full_inference(other_key, key, known_facts_cnf):
                    mapping[key].add(other_key)
    return mapping


def compute_known_facts(known_facts, known_facts_keys):
    """Compute the various forms of knowledge compilation used by the
    assumptions system.

    This function is typically applied to the results of the ``get_known_facts``
    and ``get_known_facts_keys`` functions defined at the bottom of
    this file.
    """
    from textwrap import dedent, wrap

    fact_string = dedent('''\
    """
    The contents of this file are the return value of
    ``sympy.assumptions.ask.compute_known_facts``.

    Do NOT manually edit this file.
    Instead, run ./bin/ask_update.py.
    """

    from sympy.core.cache import cacheit
    from sympy.logic.boolalg import And, Not, Or
    from sympy.assumptions.ask import Q

    # -{ Known facts in Conjunctive Normal Form }-
    @cacheit
    def get_known_facts_cnf():
        return And(
            %s
        )

    # -{ Known facts in compressed sets }-
    @cacheit
    def get_known_facts_dict():
        return {
            %s
        }
    ''')
    # Compute the known facts in CNF form for logical inference
    LINE = ",\n        "
    HANG = ' '*8
    cnf = to_cnf(known_facts)
    c = LINE.join([str(a) for a in cnf.args])
    mapping = single_fact_lookup(known_facts_keys, cnf)
    items = sorted(mapping.items(), key=str)
    keys = [str(i[0]) for i in items]
    values = ['set(%s)' % sorted(i[1], key=str) for i in items]
    m = LINE.join(['\n'.join(
        wrap("%s: %s" % (k, v),
            subsequent_indent=HANG,
            break_long_words=False))
        for k, v in zip(keys, values)]) + ','
    return fact_string % (c, m)

# handlers tells us what ask handler we should use
# for a particular key
_val_template = 'sympy.assumptions.handlers.%s'
_handlers = [
    ("antihermitian",     "sets.AskAntiHermitianHandler"),
    ("finite",           "calculus.AskFiniteHandler"),
    ("commutative",       "AskCommutativeHandler"),
    ("complex",           "sets.AskComplexHandler"),
    ("composite",         "ntheory.AskCompositeHandler"),
    ("even",              "ntheory.AskEvenHandler"),
    ("extended_real",     "sets.AskExtendedRealHandler"),
    ("hermitian",         "sets.AskHermitianHandler"),
    ("imaginary",         "sets.AskImaginaryHandler"),
    ("integer",           "sets.AskIntegerHandler"),
    ("irrational",        "sets.AskIrrationalHandler"),
    ("rational",          "sets.AskRationalHandler"),
    ("negative",          "order.AskNegativeHandler"),
    ("nonzero",           "order.AskNonZeroHandler"),
    ("nonpositive",       "order.AskNonPositiveHandler"),
    ("nonnegative",       "order.AskNonNegativeHandler"),
    ("zero",              "order.AskZeroHandler"),
    ("positive",          "order.AskPositiveHandler"),
    ("prime",             "ntheory.AskPrimeHandler"),
    ("real",              "sets.AskRealHandler"),
    ("odd",               "ntheory.AskOddHandler"),
    ("algebraic",         "sets.AskAlgebraicHandler"),
    ("is_true",           "common.TautologicalHandler"),
    ("symmetric",         "matrices.AskSymmetricHandler"),
    ("invertible",        "matrices.AskInvertibleHandler"),
    ("orthogonal",        "matrices.AskOrthogonalHandler"),
    ("unitary",           "matrices.AskUnitaryHandler"),
    ("positive_definite", "matrices.AskPositiveDefiniteHandler"),
    ("upper_triangular",  "matrices.AskUpperTriangularHandler"),
    ("lower_triangular",  "matrices.AskLowerTriangularHandler"),
    ("diagonal",          "matrices.AskDiagonalHandler"),
    ("fullrank",          "matrices.AskFullRankHandler"),
    ("square",            "matrices.AskSquareHandler"),
    ("integer_elements",  "matrices.AskIntegerElementsHandler"),
    ("real_elements",     "matrices.AskRealElementsHandler"),
    ("complex_elements",  "matrices.AskComplexElementsHandler"),
]

for name, value in _handlers:
    register_handler(name, _val_template % value)

@cacheit
def get_known_facts_keys():
    return [
        getattr(Q, attr)
        for attr in Q.__class__.__dict__
        if not (attr.startswith('__') or
                attr in deprecated_predicates)]

@cacheit
def get_known_facts():
    return And(
        Implies(Q.infinite, ~Q.finite),
        Implies(Q.real, Q.complex),
        Implies(Q.real, Q.hermitian),
        Equivalent(Q.extended_real, Q.real | Q.infinite),
        Equivalent(Q.even | Q.odd, Q.integer),
        Implies(Q.even, ~Q.odd),
        Equivalent(Q.prime, Q.integer & Q.positive & ~Q.composite),
        Implies(Q.integer, Q.rational),
        Implies(Q.rational, Q.algebraic),
        Implies(Q.algebraic, Q.complex),
        Equivalent(Q.transcendental | Q.algebraic, Q.complex),
        Implies(Q.transcendental, ~Q.algebraic),
        Implies(Q.imaginary, Q.complex & ~Q.real),
        Implies(Q.imaginary, Q.antihermitian),
        Implies(Q.antihermitian, ~Q.hermitian),
        Equivalent(Q.irrational | Q.rational, Q.real),
        Implies(Q.irrational, ~Q.rational),
        Implies(Q.zero, Q.even),

        Equivalent(Q.real, Q.negative | Q.zero | Q.positive),
        Implies(Q.zero, ~Q.negative & ~Q.positive),
        Implies(Q.negative, ~Q.positive),
        Equivalent(Q.nonnegative, Q.zero | Q.positive),
        Equivalent(Q.nonpositive, Q.zero | Q.negative),
        Equivalent(Q.nonzero, Q.negative | Q.positive),

        Implies(Q.orthogonal, Q.positive_definite),
        Implies(Q.orthogonal, Q.unitary),
        Implies(Q.unitary & Q.real, Q.orthogonal),
        Implies(Q.unitary, Q.normal),
        Implies(Q.unitary, Q.invertible),
        Implies(Q.normal, Q.square),
        Implies(Q.diagonal, Q.normal),
        Implies(Q.positive_definite, Q.invertible),
        Implies(Q.diagonal, Q.upper_triangular),
        Implies(Q.diagonal, Q.lower_triangular),
        Implies(Q.lower_triangular, Q.triangular),
        Implies(Q.upper_triangular, Q.triangular),
        Implies(Q.triangular, Q.upper_triangular | Q.lower_triangular),
        Implies(Q.upper_triangular & Q.lower_triangular, Q.diagonal),
        Implies(Q.diagonal, Q.symmetric),
        Implies(Q.unit_triangular, Q.triangular),
        Implies(Q.invertible, Q.fullrank),
        Implies(Q.invertible, Q.square),
        Implies(Q.symmetric, Q.square),
        Implies(Q.fullrank & Q.square, Q.invertible),
        Equivalent(Q.invertible, ~Q.singular),
        Implies(Q.integer_elements, Q.real_elements),
        Implies(Q.real_elements, Q.complex_elements),
    )

from sympy.assumptions.ask_generated import (
    get_known_facts_dict, get_known_facts_cnf)
