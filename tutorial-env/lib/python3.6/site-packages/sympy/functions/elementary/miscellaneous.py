from __future__ import print_function, division

from sympy.core import Function, S, sympify
from sympy.core.add import Add
from sympy.core.containers import Tuple
from sympy.core.operations import LatticeOp, ShortCircuit
from sympy.core.function import (Application, Lambda,
    ArgumentIndexError)
from sympy.core.evaluate import global_evaluate
from sympy.core.expr import Expr
from sympy.core.mod import Mod
from sympy.core.mul import Mul
from sympy.core.numbers import Rational
from sympy.core.power import Pow
from sympy.core.relational import Eq, Relational
from sympy.core.singleton import Singleton
from sympy.core.symbol import Dummy
from sympy.core.rules import Transform
from sympy.core.compatibility import with_metaclass, range
from sympy.core.logic import fuzzy_and, fuzzy_or, _torf
from sympy.logic.boolalg import And, Or

def _minmax_as_Piecewise(op, *args):
    # helper for Min/Max rewrite as Piecewise
    from sympy.functions.elementary.piecewise import Piecewise
    ec = []
    for i, a in enumerate(args):
        c = []
        for j in range(i + 1, len(args)):
            c.append(Relational(a, args[j], op))
        ec.append((a, And(*c)))
    return Piecewise(*ec)


class IdentityFunction(with_metaclass(Singleton, Lambda)):
    """
    The identity function

    Examples
    ========

    >>> from sympy import Id, Symbol
    >>> x = Symbol('x')
    >>> Id(x)
    x

    """

    def __new__(cls):
        from sympy.sets.sets import FiniteSet
        x = Dummy('x')
        #construct "by hand" to avoid infinite loop
        obj = Expr.__new__(cls, Tuple(x), x)
        obj.nargs = FiniteSet(1)
        return obj

Id = S.IdentityFunction

###############################################################################
############################# ROOT and SQUARE ROOT FUNCTION ###################
###############################################################################


def sqrt(arg, evaluate=None):
    """The square root function

    sqrt(x) -> Returns the principal square root of x.

    The parameter evaluate determines if the expression should be evaluated.
    If None, its value is taken from global_evaluate

    Examples
    ========

    >>> from sympy import sqrt, Symbol
    >>> x = Symbol('x')

    >>> sqrt(x)
    sqrt(x)

    >>> sqrt(x)**2
    x

    Note that sqrt(x**2) does not simplify to x.

    >>> sqrt(x**2)
    sqrt(x**2)

    This is because the two are not equal to each other in general.
    For example, consider x == -1:

    >>> from sympy import Eq
    >>> Eq(sqrt(x**2), x).subs(x, -1)
    False

    This is because sqrt computes the principal square root, so the square may
    put the argument in a different branch.  This identity does hold if x is
    positive:

    >>> y = Symbol('y', positive=True)
    >>> sqrt(y**2)
    y

    You can force this simplification by using the powdenest() function with
    the force option set to True:

    >>> from sympy import powdenest
    >>> sqrt(x**2)
    sqrt(x**2)
    >>> powdenest(sqrt(x**2), force=True)
    x

    To get both branches of the square root you can use the rootof function:

    >>> from sympy import rootof

    >>> [rootof(x**2-3,i) for i in (0,1)]
    [-sqrt(3), sqrt(3)]

    See Also
    ========

    sympy.polys.rootoftools.rootof, root, real_root

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Square_root
    .. [2] https://en.wikipedia.org/wiki/Principal_value
    """
    # arg = sympify(arg) is handled by Pow
    return Pow(arg, S.Half, evaluate=evaluate)


def cbrt(arg, evaluate=None):
    """This function computes the principal cube root of `arg`, so
    it's just a shortcut for `arg**Rational(1, 3)`.

    The parameter evaluate determines if the expression should be evaluated.
    If None, its value is taken from global_evaluate.

    Examples
    ========

    >>> from sympy import cbrt, Symbol
    >>> x = Symbol('x')

    >>> cbrt(x)
    x**(1/3)

    >>> cbrt(x)**3
    x

    Note that cbrt(x**3) does not simplify to x.

    >>> cbrt(x**3)
    (x**3)**(1/3)

    This is because the two are not equal to each other in general.
    For example, consider `x == -1`:

    >>> from sympy import Eq
    >>> Eq(cbrt(x**3), x).subs(x, -1)
    False

    This is because cbrt computes the principal cube root, this
    identity does hold if `x` is positive:

    >>> y = Symbol('y', positive=True)
    >>> cbrt(y**3)
    y

    See Also
    ========

    sympy.polys.rootoftools.rootof, root, real_root

    References
    ==========

    * https://en.wikipedia.org/wiki/Cube_root
    * https://en.wikipedia.org/wiki/Principal_value

    """
    return Pow(arg, Rational(1, 3), evaluate=evaluate)


def root(arg, n, k=0, evaluate=None):
    """root(x, n, k) -> Returns the k-th n-th root of x, defaulting to the
    principal root (k=0).

    The parameter evaluate determines if the expression should be evaluated.
    If None, its value is taken from global_evaluate.

    Examples
    ========

    >>> from sympy import root, Rational
    >>> from sympy.abc import x, n

    >>> root(x, 2)
    sqrt(x)

    >>> root(x, 3)
    x**(1/3)

    >>> root(x, n)
    x**(1/n)

    >>> root(x, -Rational(2, 3))
    x**(-3/2)

    To get the k-th n-th root, specify k:

    >>> root(-2, 3, 2)
    -(-1)**(2/3)*2**(1/3)

    To get all n n-th roots you can use the rootof function.
    The following examples show the roots of unity for n
    equal 2, 3 and 4:

    >>> from sympy import rootof, I

    >>> [rootof(x**2 - 1, i) for i in range(2)]
    [-1, 1]

    >>> [rootof(x**3 - 1,i) for i in range(3)]
    [1, -1/2 - sqrt(3)*I/2, -1/2 + sqrt(3)*I/2]

    >>> [rootof(x**4 - 1,i) for i in range(4)]
    [-1, 1, -I, I]

    SymPy, like other symbolic algebra systems, returns the
    complex root of negative numbers. This is the principal
    root and differs from the text-book result that one might
    be expecting. For example, the cube root of -8 does not
    come back as -2:

    >>> root(-8, 3)
    2*(-1)**(1/3)

    The real_root function can be used to either make the principal
    result real (or simply to return the real root directly):

    >>> from sympy import real_root
    >>> real_root(_)
    -2
    >>> real_root(-32, 5)
    -2

    Alternatively, the n//2-th n-th root of a negative number can be
    computed with root:

    >>> root(-32, 5, 5//2)
    -2

    See Also
    ========

    sympy.polys.rootoftools.rootof
    sympy.core.power.integer_nthroot
    sqrt, real_root

    References
    ==========

    * https://en.wikipedia.org/wiki/Square_root
    * https://en.wikipedia.org/wiki/Real_root
    * https://en.wikipedia.org/wiki/Root_of_unity
    * https://en.wikipedia.org/wiki/Principal_value
    * http://mathworld.wolfram.com/CubeRoot.html

    """
    n = sympify(n)
    if k:
        return Mul(Pow(arg, S.One/n, evaluate=evaluate), S.NegativeOne**(2*k/n), evaluate=evaluate)
    return Pow(arg, 1/n, evaluate=evaluate)


def real_root(arg, n=None, evaluate=None):
    """Return the real nth-root of arg if possible. If n is omitted then
    all instances of (-n)**(1/odd) will be changed to -n**(1/odd); this
    will only create a real root of a principal root -- the presence of
    other factors may cause the result to not be real.

    The parameter evaluate determines if the expression should be evaluated.
    If None, its value is taken from global_evaluate.

    Examples
    ========

    >>> from sympy import root, real_root, Rational
    >>> from sympy.abc import x, n

    >>> real_root(-8, 3)
    -2
    >>> root(-8, 3)
    2*(-1)**(1/3)
    >>> real_root(_)
    -2

    If one creates a non-principal root and applies real_root, the
    result will not be real (so use with caution):

    >>> root(-8, 3, 2)
    -2*(-1)**(2/3)
    >>> real_root(_)
    -2*(-1)**(2/3)


    See Also
    ========

    sympy.polys.rootoftools.rootof
    sympy.core.power.integer_nthroot
    root, sqrt
    """
    from sympy.functions.elementary.complexes import Abs, im, sign
    from sympy.functions.elementary.piecewise import Piecewise
    if n is not None:
        return Piecewise(
            (root(arg, n, evaluate=evaluate), Or(Eq(n, S.One), Eq(n, S.NegativeOne))),
            (Mul(sign(arg), root(Abs(arg), n, evaluate=evaluate), evaluate=evaluate),
            And(Eq(im(arg), S.Zero), Eq(Mod(n, 2), S.One))),
            (root(arg, n, evaluate=evaluate), True))
    rv = sympify(arg)
    n1pow = Transform(lambda x: -(-x.base)**x.exp,
                      lambda x:
                      x.is_Pow and
                      x.base.is_negative and
                      x.exp.is_Rational and
                      x.exp.p == 1 and x.exp.q % 2)
    return rv.xreplace(n1pow)

###############################################################################
############################# MINIMUM and MAXIMUM #############################
###############################################################################


class MinMaxBase(Expr, LatticeOp):
    def __new__(cls, *args, **assumptions):
        evaluate = assumptions.pop('evaluate', True)
        args = (sympify(arg) for arg in args)

        # first standard filter, for cls.zero and cls.identity
        # also reshape Max(a, Max(b, c)) to Max(a, b, c)

        if evaluate:
            try:
                args = frozenset(cls._new_args_filter(args))
            except ShortCircuit:
                return cls.zero
        else:
            args = frozenset(args)

        if evaluate:
            # remove redundant args that are easily identified
            args = cls._collapse_arguments(args, **assumptions)
            # find local zeros
            args = cls._find_localzeros(args, **assumptions)

        if not args:
            return cls.identity

        if len(args) == 1:
            return list(args).pop()

        # base creation
        _args = frozenset(args)
        obj = Expr.__new__(cls, _args, **assumptions)
        obj._argset = _args
        return obj

    @classmethod
    def _collapse_arguments(cls, args, **assumptions):
        """Remove redundant args.

        Examples
        ========

        >>> from sympy import Min, Max
        >>> from sympy.abc import a, b, c, d, e

        Any arg in parent that appears in any
        parent-like function in any of the flat args
        of parent can be removed from that sub-arg:

        >>> Min(a, Max(b, Min(a, c, d)))
        Min(a, Max(b, Min(c, d)))

        If the arg of parent appears in an opposite-than parent
        function in any of the flat args of parent that function
        can be replaced with the arg:

        >>> Min(a, Max(b, Min(c, d, Max(a, e))))
        Min(a, Max(b, Min(a, c, d)))

        """
        from sympy.utilities.iterables import ordered
        from sympy.simplify.simplify import walk

        if not args:
            return args
        args = list(ordered(args))
        if cls == Min:
            other = Max
        else:
            other = Min

        # find global comparable max of Max and min of Min if a new
        # value is being introduced in these args at position 0 of
        # the ordered args
        if args[0].is_number:
            sifted = mins, maxs = [], []
            for i in args:
                for v in walk(i, Min, Max):
                    if v.args[0].is_comparable:
                        sifted[isinstance(v, Max)].append(v)
            small = Min.identity
            for i in mins:
                v = i.args[0]
                if v.is_number and (v < small) == True:
                    small = v
            big = Max.identity
            for i in maxs:
                v = i.args[0]
                if v.is_number and (v > big) == True:
                    big = v
            # at the point when this function is called from __new__,
            # there may be more than one numeric arg present since
            # local zeros have not been handled yet, so look through
            # more than the first arg
            if cls == Min:
                for i in range(len(args)):
                    if not args[i].is_number:
                        break
                    if (args[i] < small) == True:
                        small = args[i]
            elif cls == Max:
                for i in range(len(args)):
                    if not args[i].is_number:
                        break
                    if (args[i] > big) == True:
                        big = args[i]
            T = None
            if cls == Min:
                if small != Min.identity:
                    other = Max
                    T = small
            elif big != Max.identity:
                other = Min
                T = big
            if T is not None:
                # remove numerical redundancy
                for i in range(len(args)):
                    a = args[i]
                    if isinstance(a, other):
                        a0 = a.args[0]
                        if ((a0 > T) if other == Max else (a0 < T)) == True:
                            args[i] = cls.identity

        # remove redundant symbolic args
        def do(ai, a):
            if not isinstance(ai, (Min, Max)):
                return ai
            cond = a in ai.args
            if not cond:
                return ai.func(*[do(i, a) for i in ai.args],
                    evaluate=False)
            if isinstance(ai, cls):
                return ai.func(*[do(i, a) for i in ai.args if i != a],
                    evaluate=False)
            return a
        for i, a in enumerate(args):
            args[i + 1:] = [do(ai, a) for ai in args[i + 1:]]

        # factor out common elements as for
        # Min(Max(x, y), Max(x, z)) -> Max(x, Min(y, z))
        # and vice versa when swapping Min/Max -- do this only for the
        # easy case where all functions contain something in common;
        # trying to find some optimal subset of args to modify takes
        # too long
        if len(args) > 1:
            common = None
            remove = []
            sets = []
            for i in range(len(args)):
                a = args[i]
                if not isinstance(a, other):
                    continue
                s = set(a.args)
                common = s if common is None else (common & s)
                if not common:
                    break
                sets.append(s)
                remove.append(i)
            if common:
                sets = filter(None, [s - common for s in sets])
                sets = [other(*s, evaluate=False) for s in sets]
                for i in reversed(remove):
                    args.pop(i)
                oargs = [cls(*sets)] if sets else []
                oargs.extend(common)
                args.append(other(*oargs, evaluate=False))

        return args

    @classmethod
    def _new_args_filter(cls, arg_sequence):
        """
        Generator filtering args.

        first standard filter, for cls.zero and cls.identity.
        Also reshape Max(a, Max(b, c)) to Max(a, b, c),
        and check arguments for comparability
        """
        for arg in arg_sequence:

            # pre-filter, checking comparability of arguments
            if not isinstance(arg, Expr) or arg.is_real is False or (
                    arg.is_number and
                    not arg.is_comparable):
                raise ValueError("The argument '%s' is not comparable." % arg)

            if arg == cls.zero:
                raise ShortCircuit(arg)
            elif arg == cls.identity:
                continue
            elif arg.func == cls:
                for x in arg.args:
                    yield x
            else:
                yield arg

    @classmethod
    def _find_localzeros(cls, values, **options):
        """
        Sequentially allocate values to localzeros.

        When a value is identified as being more extreme than another member it
        replaces that member; if this is never true, then the value is simply
        appended to the localzeros.
        """
        localzeros = set()
        for v in values:
            is_newzero = True
            localzeros_ = list(localzeros)
            for z in localzeros_:
                if id(v) == id(z):
                    is_newzero = False
                else:
                    con = cls._is_connected(v, z)
                    if con:
                        is_newzero = False
                        if con is True or con == cls:
                            localzeros.remove(z)
                            localzeros.update([v])
            if is_newzero:
                localzeros.update([v])
        return localzeros

    @classmethod
    def _is_connected(cls, x, y):
        """
        Check if x and y are connected somehow.
        """
        from sympy.core.exprtools import factor_terms
        def hit(v, t, f):
            if not v.is_Relational:
                return t if v else f
        for i in range(2):
            if x == y:
                return True
            r = hit(x >= y, Max, Min)
            if r is not None:
                return r
            r = hit(y <= x, Max, Min)
            if r is not None:
                return r
            r = hit(x <= y, Min, Max)
            if r is not None:
                return r
            r = hit(y >= x, Min, Max)
            if r is not None:
                return r
            # simplification can be expensive, so be conservative
            # in what is attempted
            x = factor_terms(x - y)
            y = S.Zero

        return False

    def _eval_derivative(self, s):
        # f(x).diff(s) -> x.diff(s) * f.fdiff(1)(s)
        i = 0
        l = []
        for a in self.args:
            i += 1
            da = a.diff(s)
            if da is S.Zero:
                continue
            try:
                df = self.fdiff(i)
            except ArgumentIndexError:
                df = Function.fdiff(self, i)
            l.append(df * da)
        return Add(*l)

    def _eval_rewrite_as_Abs(self, *args, **kwargs):
        from sympy.functions.elementary.complexes import Abs
        s = (args[0] + self.func(*args[1:]))/2
        d = abs(args[0] - self.func(*args[1:]))/2
        return (s + d if isinstance(self, Max) else s - d).rewrite(Abs)

    def evalf(self, prec=None, **options):
        return self.func(*[a.evalf(prec, **options) for a in self.args])
    n = evalf

    _eval_is_algebraic = lambda s: _torf(i.is_algebraic for i in s.args)
    _eval_is_antihermitian = lambda s: _torf(i.is_antihermitian for i in s.args)
    _eval_is_commutative = lambda s: _torf(i.is_commutative for i in s.args)
    _eval_is_complex = lambda s: _torf(i.is_complex for i in s.args)
    _eval_is_composite = lambda s: _torf(i.is_composite for i in s.args)
    _eval_is_even = lambda s: _torf(i.is_even for i in s.args)
    _eval_is_finite = lambda s: _torf(i.is_finite for i in s.args)
    _eval_is_hermitian = lambda s: _torf(i.is_hermitian for i in s.args)
    _eval_is_imaginary = lambda s: _torf(i.is_imaginary for i in s.args)
    _eval_is_infinite = lambda s: _torf(i.is_infinite for i in s.args)
    _eval_is_integer = lambda s: _torf(i.is_integer for i in s.args)
    _eval_is_irrational = lambda s: _torf(i.is_irrational for i in s.args)
    _eval_is_negative = lambda s: _torf(i.is_negative for i in s.args)
    _eval_is_noninteger = lambda s: _torf(i.is_noninteger for i in s.args)
    _eval_is_nonnegative = lambda s: _torf(i.is_nonnegative for i in s.args)
    _eval_is_nonpositive = lambda s: _torf(i.is_nonpositive for i in s.args)
    _eval_is_nonzero = lambda s: _torf(i.is_nonzero for i in s.args)
    _eval_is_odd = lambda s: _torf(i.is_odd for i in s.args)
    _eval_is_polar = lambda s: _torf(i.is_polar for i in s.args)
    _eval_is_positive = lambda s: _torf(i.is_positive for i in s.args)
    _eval_is_prime = lambda s: _torf(i.is_prime for i in s.args)
    _eval_is_rational = lambda s: _torf(i.is_rational for i in s.args)
    _eval_is_real = lambda s: _torf(i.is_real for i in s.args)
    _eval_is_transcendental = lambda s: _torf(i.is_transcendental for i in s.args)
    _eval_is_zero = lambda s: _torf(i.is_zero for i in s.args)

class Max(MinMaxBase, Application):
    """
    Return, if possible, the maximum value of the list.

    When number of arguments is equal one, then
    return this argument.

    When number of arguments is equal two, then
    return, if possible, the value from (a, b) that is >= the other.

    In common case, when the length of list greater than 2, the task
    is more complicated. Return only the arguments, which are greater
    than others, if it is possible to determine directional relation.

    If is not possible to determine such a relation, return a partially
    evaluated result.

    Assumptions are used to make the decision too.

    Also, only comparable arguments are permitted.

    It is named ``Max`` and not ``max`` to avoid conflicts
    with the built-in function ``max``.


    Examples
    ========

    >>> from sympy import Max, Symbol, oo
    >>> from sympy.abc import x, y
    >>> p = Symbol('p', positive=True)
    >>> n = Symbol('n', negative=True)

    >>> Max(x, -2)                  #doctest: +SKIP
    Max(x, -2)
    >>> Max(x, -2).subs(x, 3)
    3
    >>> Max(p, -2)
    p
    >>> Max(x, y)
    Max(x, y)
    >>> Max(x, y) == Max(y, x)
    True
    >>> Max(x, Max(y, z))           #doctest: +SKIP
    Max(x, y, z)
    >>> Max(n, 8, p, 7, -oo)        #doctest: +SKIP
    Max(8, p)
    >>> Max (1, x, oo)
    oo

    * Algorithm

    The task can be considered as searching of supremums in the
    directed complete partial orders [1]_.

    The source values are sequentially allocated by the isolated subsets
    in which supremums are searched and result as Max arguments.

    If the resulted supremum is single, then it is returned.

    The isolated subsets are the sets of values which are only the comparable
    with each other in the current set. E.g. natural numbers are comparable with
    each other, but not comparable with the `x` symbol. Another example: the
    symbol `x` with negative assumption is comparable with a natural number.

    Also there are "least" elements, which are comparable with all others,
    and have a zero property (maximum or minimum for all elements). E.g. `oo`.
    In case of it the allocation operation is terminated and only this value is
    returned.

    Assumption:
       - if A > B > C then A > C
       - if A == B then B can be removed

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Directed_complete_partial_order
    .. [2] https://en.wikipedia.org/wiki/Lattice_%28order%29

    See Also
    ========

    Min : find minimum values
    """
    zero = S.Infinity
    identity = S.NegativeInfinity

    def fdiff( self, argindex ):
        from sympy import Heaviside
        n = len(self.args)
        if 0 < argindex and argindex <= n:
            argindex -= 1
            if n == 2:
                return Heaviside(self.args[argindex] - self.args[1 - argindex])
            newargs = tuple([self.args[i] for i in range(n) if i != argindex])
            return Heaviside(self.args[argindex] - Max(*newargs))
        else:
            raise ArgumentIndexError(self, argindex)

    def _eval_rewrite_as_Heaviside(self, *args, **kwargs):
        from sympy import Heaviside
        return Add(*[j*Mul(*[Heaviside(j - i) for i in args if i!=j]) \
                for j in args])

    def _eval_rewrite_as_Piecewise(self, *args, **kwargs):
        return _minmax_as_Piecewise('>=', *args)

    def _eval_is_positive(self):
        return fuzzy_or(a.is_positive for a in self.args)

    def _eval_is_nonnegative(self):
        return fuzzy_or(a.is_nonnegative for a in self.args)

    def _eval_is_negative(self):
        return fuzzy_and(a.is_negative for a in self.args)


class Min(MinMaxBase, Application):
    """
    Return, if possible, the minimum value of the list.
    It is named ``Min`` and not ``min`` to avoid conflicts
    with the built-in function ``min``.

    Examples
    ========

    >>> from sympy import Min, Symbol, oo
    >>> from sympy.abc import x, y
    >>> p = Symbol('p', positive=True)
    >>> n = Symbol('n', negative=True)

    >>> Min(x, -2)                  #doctest: +SKIP
    Min(x, -2)
    >>> Min(x, -2).subs(x, 3)
    -2
    >>> Min(p, -3)
    -3
    >>> Min(x, y)                   #doctest: +SKIP
    Min(x, y)
    >>> Min(n, 8, p, -7, p, oo)     #doctest: +SKIP
    Min(n, -7)

    See Also
    ========

    Max : find maximum values
    """
    zero = S.NegativeInfinity
    identity = S.Infinity

    def fdiff( self, argindex ):
        from sympy import Heaviside
        n = len(self.args)
        if 0 < argindex and argindex <= n:
            argindex -= 1
            if n == 2:
                return Heaviside( self.args[1-argindex] - self.args[argindex] )
            newargs = tuple([ self.args[i] for i in range(n) if i != argindex])
            return Heaviside( Min(*newargs) - self.args[argindex] )
        else:
            raise ArgumentIndexError(self, argindex)

    def _eval_rewrite_as_Heaviside(self, *args, **kwargs):
        from sympy import Heaviside
        return Add(*[j*Mul(*[Heaviside(i-j) for i in args if i!=j]) \
                for j in args])

    def _eval_rewrite_as_Piecewise(self, *args, **kwargs):
        return _minmax_as_Piecewise('<=', *args)

    def _eval_is_positive(self):
        return fuzzy_and(a.is_positive for a in self.args)

    def _eval_is_nonnegative(self):
        return fuzzy_and(a.is_nonnegative for a in self.args)

    def _eval_is_negative(self):
        return fuzzy_or(a.is_negative for a in self.args)
