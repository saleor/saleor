from sympy import (Interval, Intersection, Set, EmptySet,
        FiniteSet, Union, ComplexRegion, ProductSet)
from sympy.sets.fancysets import Integers, Naturals, Reals
from sympy.sets.sets import UniversalSet
from sympy import S, sympify
from sympy.multipledispatch import dispatch


@dispatch(Integers, Set)
def union_sets(a, b):
    intersect = Intersection(a, b)
    if intersect == a:
        return b
    elif intersect == b:
        return a

@dispatch(ComplexRegion, Set)
def union_sets(a, b):
    if b.is_subset(S.Reals):
        # treat a subset of reals as a complex region
        b = ComplexRegion.from_real(b)

    if b.is_ComplexRegion:
        # a in rectangular form
        if (not a.polar) and (not b.polar):
            return ComplexRegion(Union(a.sets, b.sets))
        # a in polar form
        elif a.polar and b.polar:
            return ComplexRegion(Union(a.sets, b.sets), polar=True)
    return None

@dispatch(EmptySet, Set)
def union_sets(a, b):
    return b


@dispatch(UniversalSet, Set)
def union_sets(a, b):
    return a

@dispatch(ProductSet, ProductSet)
def union_sets(a, b):
    if b.is_subset(a):
        return a
    if len(b.args) != len(a.args):
        return None
    if a.args[0] == b.args[0]:
        return a.args[0] * Union(ProductSet(a.args[1:]),
                                    ProductSet(b.args[1:]))
    if a.args[-1] == b.args[-1]:
        return Union(ProductSet(a.args[:-1]),
                     ProductSet(b.args[:-1])) * a.args[-1]
    return None

@dispatch(ProductSet, Set)
def union_sets(a, b):
    if b.is_subset(a):
        return a
    return None

@dispatch(Interval, Interval)
def union_sets(a, b):
    if a._is_comparable(b):
        from sympy.functions.elementary.miscellaneous import Min, Max
        # Non-overlapping intervals
        end = Min(a.end, b.end)
        start = Max(a.start, b.start)
        if (end < start or
           (end == start and (end not in a and end not in b))):
            return None
        else:
            start = Min(a.start, b.start)
            end = Max(a.end, b.end)

            left_open = ((a.start != start or a.left_open) and
                         (b.start != start or b.left_open))
            right_open = ((a.end != end or a.right_open) and
                          (b.end != end or b.right_open))
            return Interval(start, end, left_open, right_open)

@dispatch(Interval, UniversalSet)
def union_sets(a, b):
    return S.UniversalSet

@dispatch(Interval, Set)
def union_sets(a, b):
    # If I have open end points and these endpoints are contained in b
    # But only in case, when endpoints are finite. Because
    # interval does not contain oo or -oo.
    open_left_in_b_and_finite = (a.left_open and
                                     sympify(b.contains(a.start)) is S.true and
                                     a.start.is_finite)
    open_right_in_b_and_finite = (a.right_open and
                                      sympify(b.contains(a.end)) is S.true and
                                      a.end.is_finite)
    if open_left_in_b_and_finite or open_right_in_b_and_finite:
        # Fill in my end points and return
        open_left = a.left_open and a.start not in b
        open_right = a.right_open and a.end not in b
        new_a = Interval(a.start, a.end, open_left, open_right)
        return set((new_a, b))
    return None

@dispatch(FiniteSet, FiniteSet)
def union_sets(a, b):
    return FiniteSet(*(a._elements | b._elements))

@dispatch(FiniteSet, Set)
def union_sets(a, b):
    # If `b` set contains one of my elements, remove it from `a`
    if any(b.contains(x) == True for x in a):
        return set((
            FiniteSet(*[x for x in a if not b.contains(x)]), b))
    return None

@dispatch(Set, Set)
def union_sets(a, b):
    return None
