from __future__ import print_function, division

from sympy.core.basic import Basic
from sympy.core.compatibility import as_int, with_metaclass, range, PY3
from sympy.core.expr import Expr
from sympy.core.function import Lambda
from sympy.core.singleton import Singleton, S
from sympy.core.symbol import Dummy, symbols
from sympy.core.sympify import _sympify, sympify, converter
from sympy.logic.boolalg import And
from sympy.sets.sets import Set, Interval, Union, FiniteSet
from sympy.utilities.misc import filldedent


class Naturals(with_metaclass(Singleton, Set)):
    """
    Represents the natural numbers (or counting numbers) which are all
    positive integers starting from 1. This set is also available as
    the Singleton, S.Naturals.

    Examples
    ========

    >>> from sympy import S, Interval, pprint
    >>> 5 in S.Naturals
    True
    >>> iterable = iter(S.Naturals)
    >>> next(iterable)
    1
    >>> next(iterable)
    2
    >>> next(iterable)
    3
    >>> pprint(S.Naturals.intersect(Interval(0, 10)))
    {1, 2, ..., 10}

    See Also
    ========

    Naturals0 : non-negative integers (i.e. includes 0, too)
    Integers : also includes negative integers
    """

    is_iterable = True
    _inf = S.One
    _sup = S.Infinity

    def _contains(self, other):
        if not isinstance(other, Expr):
            return S.false
        elif other.is_positive and other.is_integer:
            return S.true
        elif other.is_integer is False or other.is_positive is False:
            return S.false

    def __iter__(self):
        i = self._inf
        while True:
            yield i
            i = i + 1

    @property
    def _boundary(self):
        return self


class Naturals0(Naturals):
    """Represents the whole numbers which are all the non-negative integers,
    inclusive of zero.

    See Also
    ========

    Naturals : positive integers; does not include 0
    Integers : also includes the negative integers
    """
    _inf = S.Zero

    def _contains(self, other):
        if not isinstance(other, Expr):
            return S.false
        elif other.is_integer and other.is_nonnegative:
            return S.true
        elif other.is_integer is False or other.is_nonnegative is False:
            return S.false


class Integers(with_metaclass(Singleton, Set)):
    """
    Represents all integers: positive, negative and zero. This set is also
    available as the Singleton, S.Integers.

    Examples
    ========

    >>> from sympy import S, Interval, pprint
    >>> 5 in S.Naturals
    True
    >>> iterable = iter(S.Integers)
    >>> next(iterable)
    0
    >>> next(iterable)
    1
    >>> next(iterable)
    -1
    >>> next(iterable)
    2

    >>> pprint(S.Integers.intersect(Interval(-4, 4)))
    {-4, -3, ..., 4}

    See Also
    ========

    Naturals0 : non-negative integers
    Integers : positive and negative integers and zero
    """

    is_iterable = True

    def _contains(self, other):
        if not isinstance(other, Expr):
            return S.false
        elif other.is_integer:
            return S.true
        elif other.is_integer is False:
            return S.false

    def __iter__(self):
        yield S.Zero
        i = S.One
        while True:
            yield i
            yield -i
            i = i + 1

    @property
    def _inf(self):
        return -S.Infinity

    @property
    def _sup(self):
        return S.Infinity

    @property
    def _boundary(self):
        return self


class Reals(with_metaclass(Singleton, Interval)):

    def __new__(cls):
        return Interval.__new__(cls, -S.Infinity, S.Infinity)

    def __eq__(self, other):
        return other == Interval(-S.Infinity, S.Infinity)

    def __hash__(self):
        return hash(Interval(-S.Infinity, S.Infinity))


class ImageSet(Set):
    """
    Image of a set under a mathematical function. The transformation
    must be given as a Lambda function which has as many arguments
    as the elements of the set upon which it operates, e.g. 1 argument
    when acting on the set of integers or 2 arguments when acting on
    a complex region.

    This function is not normally called directly, but is called
    from `imageset`.


    Examples
    ========

    >>> from sympy import Symbol, S, pi, Dummy, Lambda
    >>> from sympy.sets.sets import FiniteSet, Interval
    >>> from sympy.sets.fancysets import ImageSet

    >>> x = Symbol('x')
    >>> N = S.Naturals
    >>> squares = ImageSet(Lambda(x, x**2), N) # {x**2 for x in N}
    >>> 4 in squares
    True
    >>> 5 in squares
    False

    >>> FiniteSet(0, 1, 2, 3, 4, 5, 6, 7, 9, 10).intersect(squares)
    {1, 4, 9}

    >>> square_iterable = iter(squares)
    >>> for i in range(4):
    ...     next(square_iterable)
    1
    4
    9
    16

    If you want to get value for `x` = 2, 1/2 etc. (Please check whether the
    `x` value is in `base_set` or not before passing it as args)

    >>> squares.lamda(2)
    4
    >>> squares.lamda(S(1)/2)
    1/4

    >>> n = Dummy('n')
    >>> solutions = ImageSet(Lambda(n, n*pi), S.Integers) # solutions of sin(x) = 0
    >>> dom = Interval(-1, 1)
    >>> dom.intersect(solutions)
    {0}

    See Also
    ========

    sympy.sets.sets.imageset
    """
    def __new__(cls, flambda, *sets):
        if not isinstance(flambda, Lambda):
            raise ValueError('first argument must be a Lambda')
        if flambda is S.IdentityFunction and len(sets) == 1:
            return sets[0]
        if not flambda.expr.free_symbols or not flambda.expr.args:
            return FiniteSet(flambda.expr)

        return Basic.__new__(cls, flambda, *sets)

    lamda = property(lambda self: self.args[0])
    base_set = property(lambda self: self.args[1])

    def __iter__(self):
        already_seen = set()
        for i in self.base_set:
            val = self.lamda(i)
            if val in already_seen:
                continue
            else:
                already_seen.add(val)
                yield val

    def _is_multivariate(self):
        return len(self.lamda.variables) > 1

    def _contains(self, other):
        from sympy.matrices import Matrix
        from sympy.solvers.solveset import solveset, linsolve
        from sympy.utilities.iterables import is_sequence, iterable, cartes
        L = self.lamda
        if is_sequence(other):
            if not is_sequence(L.expr):
                return S.false
            if len(L.expr) != len(other):
                raise ValueError(filldedent('''
    Dimensions of other and output of Lambda are different.'''))
        elif iterable(other):
                raise ValueError(filldedent('''
    `other` should be an ordered object like a Tuple.'''))

        solns = None
        if self._is_multivariate():
            if not is_sequence(L.expr):
                # exprs -> (numer, denom) and check again
                # XXX this is a bad idea -- make the user
                # remap self to desired form
                return other.as_numer_denom() in self.func(
                    Lambda(L.variables, L.expr.as_numer_denom()), self.base_set)
            eqs = [expr - val for val, expr in zip(other, L.expr)]
            variables = L.variables
            free = set(variables)
            if all(i.is_number for i in list(Matrix(eqs).jacobian(variables))):
                solns = list(linsolve([e - val for e, val in
                zip(L.expr, other)], variables))
            else:
                syms = [e.free_symbols & free for e in eqs]
                solns = {}
                for i, (e, s, v) in enumerate(zip(eqs, syms, other)):
                    if not s:
                        if e != v:
                            return S.false
                        solns[vars[i]] = [v]
                        continue
                    elif len(s) == 1:
                        sy = s.pop()
                        sol = solveset(e, sy)
                        if sol is S.EmptySet:
                            return S.false
                        elif isinstance(sol, FiniteSet):
                            solns[sy] = list(sol)
                        else:
                            raise NotImplementedError
                    else:
                        raise NotImplementedError
                solns = cartes(*[solns[s] for s in variables])
        else:
            x = L.variables[0]
            if isinstance(L.expr, Expr):
                # scalar -> scalar mapping
                solnsSet = solveset(L.expr - other, x)
                if solnsSet.is_FiniteSet:
                    solns = list(solnsSet)
                else:
                    msgset = solnsSet
            else:
                # scalar -> vector
                for e, o in zip(L.expr, other):
                    solns = solveset(e - o, x)
                    if solns is S.EmptySet:
                        return S.false
                    for soln in solns:
                        try:
                            if soln in self.base_set:
                                break  # check next pair
                        except TypeError:
                            if self.base_set.contains(soln.evalf()):
                                break
                    else:
                        return S.false  # never broke so there was no True
                return S.true

        if solns is None:
            raise NotImplementedError(filldedent('''
            Determining whether %s contains %s has not
            been implemented.''' % (msgset, other)))
        for soln in solns:
            try:
                if soln in self.base_set:
                    return S.true
            except TypeError:
                return self.base_set.contains(soln.evalf())
        return S.false

    @property
    def is_iterable(self):
        return self.base_set.is_iterable

    def doit(self, **kwargs):
        from sympy.sets.setexpr import SetExpr
        f = self.lamda
        base_set = self.base_set
        return SetExpr(base_set)._eval_func(f).set


class Range(Set):
    """
    Represents a range of integers. Can be called as Range(stop),
    Range(start, stop), or Range(start, stop, step); when stop is
    not given it defaults to 1.

    `Range(stop)` is the same as `Range(0, stop, 1)` and the stop value
    (juse as for Python ranges) is not included in the Range values.

        >>> from sympy import Range
        >>> list(Range(3))
        [0, 1, 2]

    The step can also be negative:

        >>> list(Range(10, 0, -2))
        [10, 8, 6, 4, 2]

    The stop value is made canonical so equivalent ranges always
    have the same args:

        >>> Range(0, 10, 3)
        Range(0, 12, 3)

    Infinite ranges are allowed. ``oo`` and ``-oo`` are never included in the
    set (``Range`` is always a subset of ``Integers``). If the starting point
    is infinite, then the final value is ``stop - step``. To iterate such a
    range, it needs to be reversed:

        >>> from sympy import oo
        >>> r = Range(-oo, 1)
        >>> r[-1]
        0
        >>> next(iter(r))
        Traceback (most recent call last):
        ...
        ValueError: Cannot iterate over Range with infinite start
        >>> next(iter(r.reversed))
        0

    Although Range is a set (and supports the normal set
    operations) it maintains the order of the elements and can
    be used in contexts where `range` would be used.

        >>> from sympy import Interval
        >>> Range(0, 10, 2).intersect(Interval(3, 7))
        Range(4, 8, 2)
        >>> list(_)
        [4, 6]

    Although slicing of a Range will always return a Range -- possibly
    empty -- an empty set will be returned from any intersection that
    is empty:

        >>> Range(3)[:0]
        Range(0, 0, 1)
        >>> Range(3).intersect(Interval(4, oo))
        EmptySet()
        >>> Range(3).intersect(Range(4, oo))
        EmptySet()

    """

    is_iterable = True

    def __new__(cls, *args):
        from sympy.functions.elementary.integers import ceiling
        if len(args) == 1:
            if isinstance(args[0], range if PY3 else xrange):
                args = args[0].__reduce__()[1]  # use pickle method

        # expand range
        slc = slice(*args)

        if slc.step == 0:
            raise ValueError("step cannot be 0")

        start, stop, step = slc.start or 0, slc.stop, slc.step or 1
        try:
            start, stop, step = [
                w if w in [S.NegativeInfinity, S.Infinity]
                else sympify(as_int(w))
                for w in (start, stop, step)]
        except ValueError:
            raise ValueError(filldedent('''
    Finite arguments to Range must be integers; `imageset` can define
    other cases, e.g. use `imageset(i, i/10, Range(3))` to give
    [0, 1/10, 1/5].'''))

        if not step.is_Integer:
            raise ValueError(filldedent('''
    Ranges must have a literal integer step.'''))

        if all(i.is_infinite for i in  (start, stop)):
            if start == stop:
                # canonical null handled below
                start = stop = S.One
            else:
                raise ValueError(filldedent('''
    Either the start or end value of the Range must be finite.'''))

        if start.is_infinite:
            end = stop
        else:
            ref = start if start.is_finite else stop
            n = ceiling((stop - ref)/step)
            if n <= 0:
                # null Range
                start = end = 0
                step = 1
            else:
                end = ref + n*step
        return Basic.__new__(cls, start, end, step)

    start = property(lambda self: self.args[0])
    stop = property(lambda self: self.args[1])
    step = property(lambda self: self.args[2])

    @property
    def reversed(self):
        """Return an equivalent Range in the opposite order.

        Examples
        ========

        >>> from sympy import Range
        >>> Range(10).reversed
        Range(9, -1, -1)
        """
        if not self:
            return self
        return self.func(
            self.stop - self.step, self.start - self.step, -self.step)

    def _contains(self, other):
        if not self:
            return S.false
        if other.is_infinite:
            return S.false
        if not other.is_integer:
            return other.is_integer
        ref = self.start if self.start.is_finite else self.stop
        if (ref - other) % self.step:  # off sequence
            return S.false
        return _sympify(other >= self.inf and other <= self.sup)

    def __iter__(self):
        if self.start in [S.NegativeInfinity, S.Infinity]:
            raise ValueError("Cannot iterate over Range with infinite start")
        elif self:
            i = self.start
            step = self.step

            while True:
                if (step > 0 and not (self.start <= i < self.stop)) or \
                   (step < 0 and not (self.stop < i <= self.start)):
                    break
                yield i
                i += step

    def __len__(self):
        if not self:
            return 0
        dif = self.stop - self.start
        if dif.is_infinite:
            raise ValueError(
                "Use .size to get the length of an infinite Range")
        return abs(dif//self.step)

    @property
    def size(self):
        try:
            return _sympify(len(self))
        except ValueError:
            return S.Infinity

    def __nonzero__(self):
        return self.start != self.stop

    __bool__ = __nonzero__

    def __getitem__(self, i):
        from sympy.functions.elementary.integers import ceiling
        ooslice = "cannot slice from the end with an infinite value"
        zerostep = "slice step cannot be zero"
        # if we had to take every other element in the following
        # oo, ..., 6, 4, 2, 0
        # we might get oo, ..., 4, 0 or oo, ..., 6, 2
        ambiguous = "cannot unambiguously re-stride from the end " + \
            "with an infinite value"
        if isinstance(i, slice):
            if self.size.is_finite:
                start, stop, step = i.indices(self.size)
                n = ceiling((stop - start)/step)
                if n <= 0:
                    return Range(0)
                canonical_stop = start + n*step
                end = canonical_stop - step
                ss = step*self.step
                return Range(self[start], self[end] + ss, ss)
            else:  # infinite Range
                start = i.start
                stop = i.stop
                if i.step == 0:
                    raise ValueError(zerostep)
                step = i.step or 1
                ss = step*self.step
                #---------------------
                # handle infinite on right
                #   e.g. Range(0, oo) or Range(0, -oo, -1)
                # --------------------
                if self.stop.is_infinite:
                    # start and stop are not interdependent --
                    # they only depend on step --so we use the
                    # equivalent reversed values
                    return self.reversed[
                        stop if stop is None else -stop + 1:
                        start if start is None else -start:
                        step].reversed
                #---------------------
                # handle infinite on the left
                #   e.g. Range(oo, 0, -1) or Range(-oo, 0)
                # --------------------
                # consider combinations of
                # start/stop {== None, < 0, == 0, > 0} and
                # step {< 0, > 0}
                if start is None:
                    if stop is None:
                        if step < 0:
                            return Range(self[-1], self.start, ss)
                        elif step > 1:
                            raise ValueError(ambiguous)
                        else:  # == 1
                            return self
                    elif stop < 0:
                        if step < 0:
                            return Range(self[-1], self[stop], ss)
                        else:  # > 0
                            return Range(self.start, self[stop], ss)
                    elif stop == 0:
                        if step > 0:
                            return Range(0)
                        else:  # < 0
                            raise ValueError(ooslice)
                    elif stop == 1:
                        if step > 0:
                            raise ValueError(ooslice)  # infinite singleton
                        else:  # < 0
                            raise ValueError(ooslice)
                    else:  # > 1
                        raise ValueError(ooslice)
                elif start < 0:
                    if stop is None:
                        if step < 0:
                            return Range(self[start], self.start, ss)
                        else:  # > 0
                            return Range(self[start], self.stop, ss)
                    elif stop < 0:
                        return Range(self[start], self[stop], ss)
                    elif stop == 0:
                        if step < 0:
                            raise ValueError(ooslice)
                        else:  # > 0
                            return Range(0)
                    elif stop > 0:
                        raise ValueError(ooslice)
                elif start == 0:
                    if stop is None:
                        if step < 0:
                            raise ValueError(ooslice)  # infinite singleton
                        elif step > 1:
                            raise ValueError(ambiguous)
                        else:  # == 1
                            return self
                    elif stop < 0:
                        if step > 1:
                            raise ValueError(ambiguous)
                        elif step == 1:
                            return Range(self.start, self[stop], ss)
                        else:  # < 0
                            return Range(0)
                    else:  # >= 0
                        raise ValueError(ooslice)
                elif start > 0:
                    raise ValueError(ooslice)
        else:
            if not self:
                raise IndexError('Range index out of range')
            if i == 0:
                return self.start
            if i == -1 or i is S.Infinity:
                return self.stop - self.step
            rv = (self.stop if i < 0 else self.start) + i*self.step
            if rv.is_infinite:
                raise ValueError(ooslice)
            if rv < self.inf or rv > self.sup:
                raise IndexError("Range index out of range")
            return rv

    @property
    def _inf(self):
        if not self:
            raise NotImplementedError
        if self.step > 0:
            return self.start
        else:
            return self.stop - self.step

    @property
    def _sup(self):
        if not self:
            raise NotImplementedError
        if self.step > 0:
            return self.stop - self.step
        else:
            return self.start

    @property
    def _boundary(self):
        return self


if PY3:
    converter[range] = Range
else:
    converter[xrange] = Range

def normalize_theta_set(theta):
    """
    Normalize a Real Set `theta` in the Interval [0, 2*pi). It returns
    a normalized value of theta in the Set. For Interval, a maximum of
    one cycle [0, 2*pi], is returned i.e. for theta equal to [0, 10*pi],
    returned normalized value would be [0, 2*pi). As of now intervals
    with end points as non-multiples of `pi` is not supported.

    Raises
    ======

    NotImplementedError
        The algorithms for Normalizing theta Set are not yet
        implemented.
    ValueError
        The input is not valid, i.e. the input is not a real set.
    RuntimeError
        It is a bug, please report to the github issue tracker.

    Examples
    ========

    >>> from sympy.sets.fancysets import normalize_theta_set
    >>> from sympy import Interval, FiniteSet, pi
    >>> normalize_theta_set(Interval(9*pi/2, 5*pi))
    Interval(pi/2, pi)
    >>> normalize_theta_set(Interval(-3*pi/2, pi/2))
    Interval.Ropen(0, 2*pi)
    >>> normalize_theta_set(Interval(-pi/2, pi/2))
    Union(Interval(0, pi/2), Interval.Ropen(3*pi/2, 2*pi))
    >>> normalize_theta_set(Interval(-4*pi, 3*pi))
    Interval.Ropen(0, 2*pi)
    >>> normalize_theta_set(Interval(-3*pi/2, -pi/2))
    Interval(pi/2, 3*pi/2)
    >>> normalize_theta_set(FiniteSet(0, pi, 3*pi))
    {0, pi}

    """
    from sympy.functions.elementary.trigonometric import _pi_coeff as coeff

    if theta.is_Interval:
        interval_len = theta.measure
        # one complete circle
        if interval_len >= 2*S.Pi:
            if interval_len == 2*S.Pi and theta.left_open and theta.right_open:
                k = coeff(theta.start)
                return Union(Interval(0, k*S.Pi, False, True),
                        Interval(k*S.Pi, 2*S.Pi, True, True))
            return Interval(0, 2*S.Pi, False, True)

        k_start, k_end = coeff(theta.start), coeff(theta.end)

        if k_start is None or k_end is None:
            raise NotImplementedError("Normalizing theta without pi as coefficient is "
                                    "not yet implemented")
        new_start = k_start*S.Pi
        new_end = k_end*S.Pi

        if new_start > new_end:
            return Union(Interval(S.Zero, new_end, False, theta.right_open),
                         Interval(new_start, 2*S.Pi, theta.left_open, True))
        else:
            return Interval(new_start, new_end, theta.left_open, theta.right_open)

    elif theta.is_FiniteSet:
        new_theta = []
        for element in theta:
            k = coeff(element)
            if k is None:
                raise NotImplementedError('Normalizing theta without pi as '
                                          'coefficient, is not Implemented.')
            else:
                new_theta.append(k*S.Pi)
        return FiniteSet(*new_theta)

    elif theta.is_Union:
        return Union(*[normalize_theta_set(interval) for interval in theta.args])

    elif theta.is_subset(S.Reals):
        raise NotImplementedError("Normalizing theta when, it is of type %s is not "
                                  "implemented" % type(theta))
    else:
        raise ValueError(" %s is not a real set" % (theta))


class ComplexRegion(Set):
    """
    Represents the Set of all Complex Numbers. It can represent a
    region of Complex Plane in both the standard forms Polar and
    Rectangular coordinates.

    * Polar Form
      Input is in the form of the ProductSet or Union of ProductSets
      of the intervals of r and theta, & use the flag polar=True.

    Z = {z in C | z = r*[cos(theta) + I*sin(theta)], r in [r], theta in [theta]}

    * Rectangular Form
      Input is in the form of the ProductSet or Union of ProductSets
      of interval of x and y the of the Complex numbers in a Plane.
      Default input type is in rectangular form.

    Z = {z in C | z = x + I*y, x in [Re(z)], y in [Im(z)]}

    Examples
    ========

    >>> from sympy.sets.fancysets import ComplexRegion
    >>> from sympy.sets import Interval
    >>> from sympy import S, I, Union
    >>> a = Interval(2, 3)
    >>> b = Interval(4, 6)
    >>> c = Interval(1, 8)
    >>> c1 = ComplexRegion(a*b)  # Rectangular Form
    >>> c1
    ComplexRegion(Interval(2, 3) x Interval(4, 6), False)

    * c1 represents the rectangular region in complex plane
      surrounded by the coordinates (2, 4), (3, 4), (3, 6) and
      (2, 6), of the four vertices.

    >>> c2 = ComplexRegion(Union(a*b, b*c))
    >>> c2
    ComplexRegion(Union(Interval(2, 3) x Interval(4, 6), Interval(4, 6) x Interval(1, 8)), False)

    * c2 represents the Union of two rectangular regions in complex
      plane. One of them surrounded by the coordinates of c1 and
      other surrounded by the coordinates (4, 1), (6, 1), (6, 8) and
      (4, 8).

    >>> 2.5 + 4.5*I in c1
    True
    >>> 2.5 + 6.5*I in c1
    False

    >>> r = Interval(0, 1)
    >>> theta = Interval(0, 2*S.Pi)
    >>> c2 = ComplexRegion(r*theta, polar=True)  # Polar Form
    >>> c2  # unit Disk
    ComplexRegion(Interval(0, 1) x Interval.Ropen(0, 2*pi), True)

    * c2 represents the region in complex plane inside the
      Unit Disk centered at the origin.

    >>> 0.5 + 0.5*I in c2
    True
    >>> 1 + 2*I in c2
    False

    >>> unit_disk = ComplexRegion(Interval(0, 1)*Interval(0, 2*S.Pi), polar=True)
    >>> upper_half_unit_disk = ComplexRegion(Interval(0, 1)*Interval(0, S.Pi), polar=True)
    >>> intersection = unit_disk.intersect(upper_half_unit_disk)
    >>> intersection
    ComplexRegion(Interval(0, 1) x Interval(0, pi), True)
    >>> intersection == upper_half_unit_disk
    True

    See Also
    ========

    Reals

    """
    is_ComplexRegion = True

    def __new__(cls, sets, polar=False):
        from sympy import sin, cos

        x, y, r, theta = symbols('x, y, r, theta', cls=Dummy)
        I = S.ImaginaryUnit
        polar = sympify(polar)

        # Rectangular Form
        if polar == False:
            if all(_a.is_FiniteSet for _a in sets.args) and (len(sets.args) == 2):

                # ** ProductSet of FiniteSets in the Complex Plane. **
                # For Cases like ComplexRegion({2, 4}*{3}), It
                # would return {2 + 3*I, 4 + 3*I}
                complex_num = []
                for x in sets.args[0]:
                    for y in sets.args[1]:
                        complex_num.append(x + I*y)
                obj = FiniteSet(*complex_num)
            else:
                obj = ImageSet.__new__(cls, Lambda((x, y), x + I*y), sets)
            obj._variables = (x, y)
            obj._expr = x + I*y

        # Polar Form
        elif polar == True:
            new_sets = []
            # sets is Union of ProductSets
            if not sets.is_ProductSet:
                for k in sets.args:
                    new_sets.append(k)
            # sets is ProductSets
            else:
                new_sets.append(sets)
            # Normalize input theta
            for k, v in enumerate(new_sets):
                from sympy.sets import ProductSet
                new_sets[k] = ProductSet(v.args[0],
                                         normalize_theta_set(v.args[1]))
            sets = Union(*new_sets)
            obj = ImageSet.__new__(cls, Lambda((r, theta),
                                   r*(cos(theta) + I*sin(theta))),
                                   sets)
            obj._variables = (r, theta)
            obj._expr = r*(cos(theta) + I*sin(theta))

        else:
            raise ValueError("polar should be either True or False")

        obj._sets = sets
        obj._polar = polar
        return obj

    @property
    def sets(self):
        """
        Return raw input sets to the self.

        Examples
        ========

        >>> from sympy import Interval, ComplexRegion, Union
        >>> a = Interval(2, 3)
        >>> b = Interval(4, 5)
        >>> c = Interval(1, 7)
        >>> C1 = ComplexRegion(a*b)
        >>> C1.sets
        Interval(2, 3) x Interval(4, 5)
        >>> C2 = ComplexRegion(Union(a*b, b*c))
        >>> C2.sets
        Union(Interval(2, 3) x Interval(4, 5), Interval(4, 5) x Interval(1, 7))

        """
        return self._sets

    @property
    def args(self):
        return (self._sets, self._polar)

    @property
    def variables(self):
        return self._variables

    @property
    def expr(self):
        return self._expr

    @property
    def psets(self):
        """
        Return a tuple of sets (ProductSets) input of the self.

        Examples
        ========

        >>> from sympy import Interval, ComplexRegion, Union
        >>> a = Interval(2, 3)
        >>> b = Interval(4, 5)
        >>> c = Interval(1, 7)
        >>> C1 = ComplexRegion(a*b)
        >>> C1.psets
        (Interval(2, 3) x Interval(4, 5),)
        >>> C2 = ComplexRegion(Union(a*b, b*c))
        >>> C2.psets
        (Interval(2, 3) x Interval(4, 5), Interval(4, 5) x Interval(1, 7))

        """
        if self.sets.is_ProductSet:
            psets = ()
            psets = psets + (self.sets, )
        else:
            psets = self.sets.args
        return psets

    @property
    def a_interval(self):
        """
        Return the union of intervals of `x` when, self is in
        rectangular form, or the union of intervals of `r` when
        self is in polar form.

        Examples
        ========

        >>> from sympy import Interval, ComplexRegion, Union
        >>> a = Interval(2, 3)
        >>> b = Interval(4, 5)
        >>> c = Interval(1, 7)
        >>> C1 = ComplexRegion(a*b)
        >>> C1.a_interval
        Interval(2, 3)
        >>> C2 = ComplexRegion(Union(a*b, b*c))
        >>> C2.a_interval
        Union(Interval(2, 3), Interval(4, 5))

        """
        a_interval = []
        for element in self.psets:
            a_interval.append(element.args[0])

        a_interval = Union(*a_interval)
        return a_interval

    @property
    def b_interval(self):
        """
        Return the union of intervals of `y` when, self is in
        rectangular form, or the union of intervals of `theta`
        when self is in polar form.

        Examples
        ========

        >>> from sympy import Interval, ComplexRegion, Union
        >>> a = Interval(2, 3)
        >>> b = Interval(4, 5)
        >>> c = Interval(1, 7)
        >>> C1 = ComplexRegion(a*b)
        >>> C1.b_interval
        Interval(4, 5)
        >>> C2 = ComplexRegion(Union(a*b, b*c))
        >>> C2.b_interval
        Interval(1, 7)

        """
        b_interval = []
        for element in self.psets:
            b_interval.append(element.args[1])

        b_interval = Union(*b_interval)
        return b_interval

    @property
    def polar(self):
        """
        Returns True if self is in polar form.

        Examples
        ========

        >>> from sympy import Interval, ComplexRegion, Union, S
        >>> a = Interval(2, 3)
        >>> b = Interval(4, 5)
        >>> theta = Interval(0, 2*S.Pi)
        >>> C1 = ComplexRegion(a*b)
        >>> C1.polar
        False
        >>> C2 = ComplexRegion(a*theta, polar=True)
        >>> C2.polar
        True
        """
        return self._polar

    @property
    def _measure(self):
        """
        The measure of self.sets.

        Examples
        ========

        >>> from sympy import Interval, ComplexRegion, S
        >>> a, b = Interval(2, 5), Interval(4, 8)
        >>> c = Interval(0, 2*S.Pi)
        >>> c1 = ComplexRegion(a*b)
        >>> c1.measure
        12
        >>> c2 = ComplexRegion(a*c, polar=True)
        >>> c2.measure
        6*pi

        """
        return self.sets._measure

    @classmethod
    def from_real(cls, sets):
        """
        Converts given subset of real numbers to a complex region.

        Examples
        ========

        >>> from sympy import Interval, ComplexRegion
        >>> unit = Interval(0,1)
        >>> ComplexRegion.from_real(unit)
        ComplexRegion(Interval(0, 1) x {0}, False)

        """
        if not sets.is_subset(S.Reals):
            raise ValueError("sets must be a subset of the real line")

        return cls(sets * FiniteSet(0))

    def _contains(self, other):
        from sympy.functions import arg, Abs
        from sympy.core.containers import Tuple
        other = sympify(other)
        isTuple = isinstance(other, Tuple)
        if isTuple and len(other) != 2:
            raise ValueError('expecting Tuple of length 2')

        # If the other is not an Expression, and neither a Tuple
        if not isinstance(other, Expr) and not isinstance(other, Tuple):
            return S.false
        # self in rectangular form
        if not self.polar:
            re, im = other if isTuple else other.as_real_imag()
            for element in self.psets:
                if And(element.args[0]._contains(re),
                        element.args[1]._contains(im)):
                    return True
            return False

        # self in polar form
        elif self.polar:
            if isTuple:
                r, theta = other
            elif other.is_zero:
                r, theta = S.Zero, S.Zero
            else:
                r, theta = Abs(other), arg(other)
            for element in self.psets:
                if And(element.args[0]._contains(r),
                        element.args[1]._contains(theta)):
                    return True
            return False


class Complexes(with_metaclass(Singleton, ComplexRegion)):

    def __new__(cls):
        return ComplexRegion.__new__(cls, S.Reals*S.Reals)

    def __eq__(self, other):
        return other == ComplexRegion(S.Reals*S.Reals)

    def __hash__(self):
        return hash(ComplexRegion(S.Reals*S.Reals))

    def __str__(self):
        return "S.Complexes"

    def __repr__(self):
        return "S.Complexes"
