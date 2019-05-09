from __future__ import print_function, division

from sympy.core import S, sympify
from sympy.core.compatibility import range
from sympy.functions import Piecewise, piecewise_fold
from sympy.sets.sets import Interval


def _add_splines(c, b1, d, b2):
    """Construct c*b1 + d*b2."""
    if b1 == S.Zero or c == S.Zero:
        rv = piecewise_fold(d*b2)
    elif b2 == S.Zero or d == S.Zero:
        rv = piecewise_fold(c*b1)
    else:
        new_args = []
        n_intervals = len(b1.args)
        if n_intervals != len(b2.args):
            # Args of b1 and b2 are not equal. Just combining the
            # Piecewise without any fancy optimization
            p1 = piecewise_fold(c*b1)
            p2 = piecewise_fold(d*b2)

            # Search all Piecewise arguments except (0, True)
            p2args = list(p2.args[:-1])

            # This merging algorithm assumes the conditions in
            # p1 and p2 are sorted
            for arg in p1.args[:-1]:
                # Conditional of Piecewise are And objects
                # the args of the And object is a tuple of two
                # Relational objects the numerical value is in the .rhs
                # of the Relational object
                expr = arg.expr
                cond = arg.cond

                lower = cond.args[0].rhs

                # Check p2 for matching conditions that can be merged
                for i, arg2 in enumerate(p2args):
                    expr2 = arg2.expr
                    cond2 = arg2.cond

                    lower_2 = cond2.args[0].rhs
                    upper_2 = cond2.args[1].rhs

                    if cond2 == cond:
                        # Conditions match, join expressions
                        expr += expr2
                        # Remove matching element
                        del p2args[i]
                        # No need to check the rest
                        break
                    elif lower_2 < lower and upper_2 <= lower:
                        # Check if arg2 condition smaller than arg1,
                        # add to new_args by itself (no match expected
                        # in p1)
                        new_args.append(arg2)
                        del p2args[i]
                        break

                # Checked all, add expr and cond
                new_args.append((expr, cond))

            # Add remaining items from p2args
            new_args.extend(p2args)

            # Add final (0, True)
            new_args.append((0, True))
        else:
            new_args.append((c*b1.args[0].expr, b1.args[0].cond))
            for i in range(1, n_intervals - 1):
                new_args.append((
                    c*b1.args[i].expr + d*b2.args[i - 1].expr,
                    b1.args[i].cond
                ))
            new_args.append((d*b2.args[-2].expr, b2.args[-2].cond))
            new_args.append(b2.args[-1])

        rv = Piecewise(*new_args)

    return rv.expand()


def bspline_basis(d, knots, n, x):
    """The `n`-th B-spline at `x` of degree `d` with knots.

    B-Splines are piecewise polynomials of degree `d` [1]_.  They are
    defined on a set of knots, which is a sequence of integers or
    floats.

    The 0th degree splines have a value of one on a single interval:

        >>> from sympy import bspline_basis
        >>> from sympy.abc import x
        >>> d = 0
        >>> knots = range(5)
        >>> bspline_basis(d, knots, 0, x)
        Piecewise((1, (x >= 0) & (x <= 1)), (0, True))

    For a given ``(d, knots)`` there are ``len(knots)-d-1`` B-splines
    defined, that are indexed by ``n`` (starting at 0).

    Here is an example of a cubic B-spline:

        >>> bspline_basis(3, range(5), 0, x)
        Piecewise((x**3/6, (x >= 0) & (x <= 1)),
                  (-x**3/2 + 2*x**2 - 2*x + 2/3,
                  (x >= 1) & (x <= 2)),
                  (x**3/2 - 4*x**2 + 10*x - 22/3,
                  (x >= 2) & (x <= 3)),
                  (-x**3/6 + 2*x**2 - 8*x + 32/3,
                  (x >= 3) & (x <= 4)),
                  (0, True))

    By repeating knot points, you can introduce discontinuities in the
    B-splines and their derivatives:

        >>> d = 1
        >>> knots = [0, 0, 2, 3, 4]
        >>> bspline_basis(d, knots, 0, x)
        Piecewise((1 - x/2, (x >= 0) & (x <= 2)), (0, True))

    It is quite time consuming to construct and evaluate B-splines. If
    you need to evaluate a B-splines many times, it is best to
    lambdify them first:

        >>> from sympy import lambdify
        >>> d = 3
        >>> knots = range(10)
        >>> b0 = bspline_basis(d, knots, 0, x)
        >>> f = lambdify(x, b0)
        >>> y = f(0.5)

    See Also
    ========

    bsplines_basis_set

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/B-spline

    """
    knots = [sympify(k) for k in knots]
    d = int(d)
    n = int(n)
    n_knots = len(knots)
    n_intervals = n_knots - 1
    if n + d + 1 > n_intervals:
        raise ValueError('n + d + 1 must not exceed len(knots) - 1')
    if d == 0:
        result = Piecewise(
            (S.One, Interval(knots[n], knots[n + 1]).contains(x)),
            (0, True)
        )
    elif d > 0:
        denom = knots[n + d + 1] - knots[n + 1]
        if denom != S.Zero:
            B = (knots[n + d + 1] - x)/denom
            b2 = bspline_basis(d - 1, knots, n + 1, x)
        else:
            b2 = B = S.Zero

        denom = knots[n + d] - knots[n]
        if denom != S.Zero:
            A = (x - knots[n])/denom
            b1 = bspline_basis(d - 1, knots, n, x)
        else:
            b1 = A = S.Zero

        result = _add_splines(A, b1, B, b2)
    else:
        raise ValueError('degree must be non-negative: %r' % n)
    return result


def bspline_basis_set(d, knots, x):
    """Return the ``len(knots)-d-1`` B-splines at ``x`` of degree ``d``
    with ``knots``.

    This function returns a list of Piecewise polynomials that are the
    ``len(knots)-d-1`` B-splines of degree ``d`` for the given knots.
    This function calls ``bspline_basis(d, knots, n, x)`` for different
    values of ``n``.

    Examples
    ========

    >>> from sympy import bspline_basis_set
    >>> from sympy.abc import x
    >>> d = 2
    >>> knots = range(5)
    >>> splines = bspline_basis_set(d, knots, x)
    >>> splines
    [Piecewise((x**2/2, (x >= 0) & (x <= 1)),
               (-x**2 + 3*x - 3/2, (x >= 1) & (x <= 2)),
               (x**2/2 - 3*x + 9/2, (x >= 2) & (x <= 3)),
               (0, True)),
    Piecewise((x**2/2 - x + 1/2, (x >= 1) & (x <= 2)),
              (-x**2 + 5*x - 11/2, (x >= 2) & (x <= 3)),
              (x**2/2 - 4*x + 8, (x >= 3) & (x <= 4)),
              (0, True))]

    See Also
    ========

    bsplines_basis
    """
    n_splines = len(knots) - d - 1
    return [bspline_basis(d, knots, i, x) for i in range(n_splines)]


def interpolating_spline(d, x, X, Y):
    """Return spline of degree ``d``, passing through the given ``X``
    and ``Y`` values.

    This function returns a piecewise function such that each part is
    a polynomial of degree not greater than ``d``. The value of ``d``
    must be 1 or greater and the values of ``X`` must be strictly
    increasing.

    Examples
    ========

    >>> from sympy import interpolating_spline
    >>> from sympy.abc import x
    >>> interpolating_spline(1, x, [1, 2, 4, 7], [3, 6, 5, 7])
    Piecewise((3*x, (x >= 1) & (x <= 2)),
            (7 - x/2, (x >= 2) & (x <= 4)),
            (2*x/3 + 7/3, (x >= 4) & (x <= 7)))
    >>> interpolating_spline(3, x, [-2, 0, 1, 3, 4], [4, 2, 1, 1, 3])
    Piecewise((-x**3/36 - x**2/36 - 17*x/18 + 2, (x >= -2) & (x <= 1)),
            (5*x**3/36 - 13*x**2/36 - 11*x/18 + 7/3, (x >= 1) & (x <= 4)))

    See Also
    ========

    bsplines_basis_set, sympy.polys.specialpolys.interpolating_poly
    """
    from sympy import symbols, Number, Dummy, Rational
    from sympy.solvers.solveset import linsolve
    from sympy.matrices.dense import Matrix

    # Input sanitization
    d = sympify(d)
    if not(d.is_Integer and d.is_positive):
        raise ValueError(
            "Spline degree must be a positive integer, not %s." % d)
    if len(X) != len(Y):
        raise ValueError(
            "Number of X and Y coordinates must be the same.")
    if len(X) < d + 1:
        raise ValueError(
            "Degree must be less than the number of control points.")
    if not all(a < b for a, b in zip(X, X[1:])):
        raise ValueError(
            "The x-coordinates must be strictly increasing.")

    # Evaluating knots value
    if d.is_odd:
        j = (d + 1) // 2
        interior_knots = X[j:-j]
    else:
        j = d // 2
        interior_knots = [Rational(a + b, 2) for a, b in
            zip(X[j:-j - 1], X[j + 1:-j])]

    knots = [X[0]] * (d + 1) + list(interior_knots) + [X[-1]] * (d + 1)

    basis = bspline_basis_set(d, knots, x)

    A = [[b.subs(x, v) for b in basis] for v in X]

    coeff = linsolve((Matrix(A), Matrix(Y)), symbols('c0:{}'.format(
        len(X)), cls=Dummy))
    coeff = list(coeff)[0]
    intervals = set([c for b in basis for (e, c) in b.args
        if c != True])

    # Sorting the intervals
    #  ival contains the end-points of each interval
    ival = [e.atoms(Number) for e in intervals]
    ival = [list(sorted(e))[0] for e in ival]
    com = zip(ival, intervals)
    com = sorted(com, key=lambda x: x[0])
    intervals = [y for x, y in com]

    basis_dicts = [dict((c, e) for (e, c) in b.args) for b in basis]
    spline = []
    for i in intervals:
        piece = sum([c*d.get(i, S.Zero) for (c, d) in
            zip(coeff, basis_dicts)], S.Zero)
        spline.append((piece, i))
    return(Piecewise(*spline))
