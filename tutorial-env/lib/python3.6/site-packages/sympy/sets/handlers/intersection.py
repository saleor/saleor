from sympy import (Interval, Intersection, Set, EmptySet,
        FiniteSet, Union, ComplexRegion, ProductSet)
from sympy.sets.fancysets import Integers, Naturals, Reals, Range, ImageSet
from sympy.sets.sets import UniversalSet, imageset
from sympy.sets.conditionset import ConditionSet
from sympy import S, sympify, Dummy, Lambda, symbols
from sympy.multipledispatch import dispatch


@dispatch(ConditionSet, ConditionSet)
def intersection_sets(a, b):
    return None

@dispatch(ConditionSet, Set)
def intersection_sets(a, b):
    return ConditionSet(a.sym, a.condition, Intersection(a.base_set, b))

@dispatch(Naturals, Interval)
def intersection_sets(a, b):
    return Intersection(S.Integers, b, Interval(a._inf, S.Infinity))

@dispatch(Interval, Naturals)
def intersection_sets(a, b):
    return intersection_sets(b, a)

@dispatch(Integers, Interval)
def intersection_sets(a, b):
    from sympy.functions.elementary.integers import floor, ceiling
    if b._inf == S.NegativeInfinity and b._sup == S.Infinity:
        return a
    s = Range(ceiling(b.left), floor(b.right) + 1)
    return intersection_sets(s, b)  # take out endpoints if open interval

@dispatch(ComplexRegion, Set)
def intersection_sets(self, other):
    if other.is_ComplexRegion:
        # self in rectangular form
        if (not self.polar) and (not other.polar):
            return ComplexRegion(Intersection(self.sets, other.sets))

        # self in polar form
        elif self.polar and other.polar:
            r1, theta1 = self.a_interval, self.b_interval
            r2, theta2 = other.a_interval, other.b_interval
            new_r_interval = Intersection(r1, r2)
            new_theta_interval = Intersection(theta1, theta2)

            # 0 and 2*Pi means the same
            if ((2*S.Pi in theta1 and S.Zero in theta2) or
               (2*S.Pi in theta2 and S.Zero in theta1)):
                new_theta_interval = Union(new_theta_interval,
                                           FiniteSet(0))
            return ComplexRegion(new_r_interval*new_theta_interval,
                                polar=True)


    if other.is_subset(S.Reals):
        new_interval = []
        x = symbols("x", cls=Dummy, real=True)

        # self in rectangular form
        if not self.polar:
            for element in self.psets:
                if S.Zero in element.args[1]:
                    new_interval.append(element.args[0])
            new_interval = Union(*new_interval)
            return Intersection(new_interval, other)

        # self in polar form
        elif self.polar:
            for element in self.psets:
                if S.Zero in element.args[1]:
                    new_interval.append(element.args[0])
                if S.Pi in element.args[1]:
                    new_interval.append(ImageSet(Lambda(x, -x), element.args[0]))
                if S.Zero in element.args[0]:
                    new_interval.append(FiniteSet(0))
            new_interval = Union(*new_interval)
            return Intersection(new_interval, other)

@dispatch(Integers, Reals)
def intersection_sets(a, b):
    return a

@dispatch(Range, Interval)
def intersection_sets(a, b):
    from sympy.functions.elementary.integers import floor, ceiling
    from sympy.functions.elementary.miscellaneous import Min, Max
    if not all(i.is_number for i in b.args[:2]):
        return

    # In case of null Range, return an EmptySet.
    if a.size == 0:
        return S.EmptySet

    # trim down to self's size, and represent
    # as a Range with step 1.
    start = ceiling(max(b.inf, a.inf))
    if start not in b:
        start += 1
    end = floor(min(b.sup, a.sup))
    if end not in b:
        end -= 1
    return intersection_sets(a, Range(start, end + 1))

@dispatch(Range, Naturals)
def intersection_sets(a, b):
    return intersection_sets(a, Interval(1, S.Infinity))

@dispatch(Naturals, Range)
def intersection_sets(a, b):
    return intersection_sets(b, a)

@dispatch(Range, Range)
def intersection_sets(a, b):
    from sympy.solvers.diophantine import diop_linear
    from sympy.core.numbers import ilcm
    from sympy import sign

    # non-overlap quick exits
    if not b:
        return S.EmptySet
    if not a:
        return S.EmptySet
    if b.sup < a.inf:
        return S.EmptySet
    if b.inf > a.sup:
        return S.EmptySet

    # work with finite end at the start
    r1 = a
    if r1.start.is_infinite:
        r1 = r1.reversed
    r2 = b
    if r2.start.is_infinite:
        r2 = r2.reversed

    # this equation represents the values of the Range;
    # it's a linear equation
    eq = lambda r, i: r.start + i*r.step

    # we want to know when the two equations might
    # have integer solutions so we use the diophantine
    # solver
    va, vb = diop_linear(eq(r1, Dummy()) - eq(r2, Dummy()))

    # check for no solution
    no_solution = va is None and vb is None
    if no_solution:
        return S.EmptySet

    # there is a solution
    # -------------------

    # find the coincident point, c
    a0 = va.as_coeff_Add()[0]
    c = eq(r1, a0)

    # find the first point, if possible, in each range
    # since c may not be that point
    def _first_finite_point(r1, c):
        if c == r1.start:
            return c
        # st is the signed step we need to take to
        # get from c to r1.start
        st = sign(r1.start - c)*step
        # use Range to calculate the first point:
        # we want to get as close as possible to
        # r1.start; the Range will not be null since
        # it will at least contain c
        s1 = Range(c, r1.start + st, st)[-1]
        if s1 == r1.start:
            pass
        else:
            # if we didn't hit r1.start then, if the
            # sign of st didn't match the sign of r1.step
            # we are off by one and s1 is not in r1
            if sign(r1.step) != sign(st):
                s1 -= st
        if s1 not in r1:
            return
        return s1

    # calculate the step size of the new Range
    step = abs(ilcm(r1.step, r2.step))
    s1 = _first_finite_point(r1, c)
    if s1 is None:
        return S.EmptySet
    s2 = _first_finite_point(r2, c)
    if s2 is None:
        return S.EmptySet

    # replace the corresponding start or stop in
    # the original Ranges with these points; the
    # result must have at least one point since
    # we know that s1 and s2 are in the Ranges
    def _updated_range(r, first):
        st = sign(r.step)*step
        if r.start.is_finite:
            rv = Range(first, r.stop, st)
        else:
            rv = Range(r.start, first + st, st)
        return rv
    r1 = _updated_range(a, s1)
    r2 = _updated_range(b, s2)

    # work with them both in the increasing direction
    if sign(r1.step) < 0:
        r1 = r1.reversed
    if sign(r2.step) < 0:
        r2 = r2.reversed

    # return clipped Range with positive step; it
    # can't be empty at this point
    start = max(r1.start, r2.start)
    stop = min(r1.stop, r2.stop)
    return Range(start, stop, step)


@dispatch(Range, Integers)
def intersection_sets(a, b):
    return a


@dispatch(ImageSet, Set)
def intersection_sets(self, other):
    from sympy.solvers.diophantine import diophantine
    if self.base_set is S.Integers:
        g = None
        if isinstance(other, ImageSet) and other.base_set is S.Integers:
            g = other.lamda.expr
            m = other.lamda.variables[0]
        elif other is S.Integers:
            m = g = Dummy('x')
        if g is not None:
            f = self.lamda.expr
            n = self.lamda.variables[0]
            # Diophantine sorts the solutions according to the alphabetic
            # order of the variable names, since the result should not depend
            # on the variable name, they are replaced by the dummy variables
            # below
            a, b = Dummy('a'), Dummy('b')
            f, g = f.subs(n, a), g.subs(m, b)
            solns_set = diophantine(f - g)
            if solns_set == set():
                return EmptySet()
            solns = list(diophantine(f - g))

            if len(solns) != 1:
                return

            # since 'a' < 'b', select soln for n
            nsol = solns[0][0]
            t = nsol.free_symbols.pop()
            return imageset(Lambda(n, f.subs(a, nsol.subs(t, n))), S.Integers)

    if other == S.Reals:
        from sympy.solvers.solveset import solveset_real
        from sympy.core.function import expand_complex
        if len(self.lamda.variables) > 1:
            return None

        f = self.lamda.expr
        n = self.lamda.variables[0]

        n_ = Dummy(n.name, real=True)
        f_ = f.subs(n, n_)

        re, im = f_.as_real_imag()
        im = expand_complex(im)

        return imageset(Lambda(n_, re),
                        self.base_set.intersect(
                            solveset_real(im, n_)))

    elif isinstance(other, Interval):
        from sympy.solvers.solveset import (invert_real, invert_complex,
                                            solveset)

        f = self.lamda.expr
        n = self.lamda.variables[0]
        base_set = self.base_set
        new_inf, new_sup = None, None
        new_lopen, new_ropen = other.left_open, other.right_open

        if f.is_real:
            inverter = invert_real
        else:
            inverter = invert_complex

        g1, h1 = inverter(f, other.inf, n)
        g2, h2 = inverter(f, other.sup, n)

        if all(isinstance(i, FiniteSet) for i in (h1, h2)):
            if g1 == n:
                if len(h1) == 1:
                    new_inf = h1.args[0]
            if g2 == n:
                if len(h2) == 1:
                    new_sup = h2.args[0]
            # TODO: Design a technique to handle multiple-inverse
            # functions

            # Any of the new boundary values cannot be determined
            if any(i is None for i in (new_sup, new_inf)):
                return


            range_set = S.EmptySet

            if all(i.is_real for i in (new_sup, new_inf)):
                # this assumes continuity of underlying function
                # however fixes the case when it is decreasing
                if new_inf > new_sup:
                    new_inf, new_sup = new_sup, new_inf
                new_interval = Interval(new_inf, new_sup, new_lopen, new_ropen)
                range_set = base_set.intersect(new_interval)
            else:
                if other.is_subset(S.Reals):
                    solutions = solveset(f, n, S.Reals)
                    if not isinstance(range_set, (ImageSet, ConditionSet)):
                        range_set = solutions.intersect(other)
                    else:
                        return

            if range_set is S.EmptySet:
                return S.EmptySet
            elif isinstance(range_set, Range) and range_set.size is not S.Infinity:
                range_set = FiniteSet(*list(range_set))

            if range_set is not None:
                return imageset(Lambda(n, f), range_set)
            return
        else:
            return


@dispatch(ProductSet, ProductSet)
def intersection_sets(a, b):
    if len(b.args) != len(a.args):
        return S.EmptySet
    return ProductSet(i.intersect(j)
            for i, j in zip(a.sets, b.sets))

@dispatch(Interval, Interval)
def intersection_sets(a, b):
    # handle (-oo, oo)
    infty = S.NegativeInfinity, S.Infinity
    if a == Interval(*infty):
        l, r = a.left, a.right
        if l.is_real or l in infty or r.is_real or r in infty:
            return b

    # We can't intersect [0,3] with [x,6] -- we don't know if x>0 or x<0
    if not a._is_comparable(b):
        return None

    empty = False

    if a.start <= b.end and b.start <= a.end:
        # Get topology right.
        if a.start < b.start:
            start = b.start
            left_open = b.left_open
        elif a.start > b.start:
            start = a.start
            left_open = a.left_open
        else:
            start = a.start
            left_open = a.left_open or b.left_open

        if a.end < b.end:
            end = a.end
            right_open = a.right_open
        elif a.end > b.end:
            end = b.end
            right_open = b.right_open
        else:
            end = a.end
            right_open = a.right_open or b.right_open

        if end - start == 0 and (left_open or right_open):
            empty = True
    else:
        empty = True

    if empty:
        return S.EmptySet

    return Interval(start, end, left_open, right_open)

@dispatch(EmptySet, Set)
def intersection_sets(a, b):
    return S.EmptySet

@dispatch(UniversalSet, Set)
def intersection_sets(a, b):
    return b

@dispatch(FiniteSet, FiniteSet)
def intersection_sets(a, b):
    return FiniteSet(*(a._elements & b._elements))

@dispatch(FiniteSet, Set)
def intersection_sets(a, b):
    try:
        return FiniteSet(*[el for el in a if el in b])
    except TypeError:
        return None  # could not evaluate `el in b` due to symbolic ranges.

@dispatch(Set, Set)
def intersection_sets(a, b):
    return None
