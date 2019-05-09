from __future__ import print_function, division

from sympy.calculus.singularities import is_decreasing
from sympy.calculus.util import AccumulationBounds
from sympy.concrete.expr_with_limits import AddWithLimits
from sympy.concrete.expr_with_intlimits import ExprWithIntLimits
from sympy.concrete.gosper import gosper_sum
from sympy.core.add import Add
from sympy.core.compatibility import range
from sympy.core.function import Derivative
from sympy.core.mul import Mul
from sympy.core.relational import Eq
from sympy.core.singleton import S
from sympy.core.symbol import Dummy, Wild, Symbol
from sympy.functions.special.zeta_functions import zeta
from sympy.functions.elementary.piecewise import Piecewise
from sympy.logic.boolalg import And
from sympy.polys import apart, PolynomialError, together
from sympy.series.limitseq import limit_seq
from sympy.series.order import O
from sympy.sets.sets import FiniteSet
from sympy.simplify import denom
from sympy.simplify.combsimp import combsimp
from sympy.simplify.powsimp import powsimp
from sympy.solvers import solve
from sympy.solvers.solveset import solveset
import itertools

class Sum(AddWithLimits, ExprWithIntLimits):
    r"""Represents unevaluated summation.

    ``Sum`` represents a finite or infinite series, with the first argument
    being the general form of terms in the series, and the second argument
    being ``(dummy_variable, start, end)``, with ``dummy_variable`` taking
    all integer values from ``start`` through ``end``. In accordance with
    long-standing mathematical convention, the end term is included in the
    summation.

    Finite sums
    ===========

    For finite sums (and sums with symbolic limits assumed to be finite) we
    follow the summation convention described by Karr [1], especially
    definition 3 of section 1.4. The sum:

    .. math::

        \sum_{m \leq i < n} f(i)

    has *the obvious meaning* for `m < n`, namely:

    .. math::

        \sum_{m \leq i < n} f(i) = f(m) + f(m+1) + \ldots + f(n-2) + f(n-1)

    with the upper limit value `f(n)` excluded. The sum over an empty set is
    zero if and only if `m = n`:

    .. math::

        \sum_{m \leq i < n} f(i) = 0  \quad \mathrm{for} \quad  m = n

    Finally, for all other sums over empty sets we assume the following
    definition:

    .. math::

        \sum_{m \leq i < n} f(i) = - \sum_{n \leq i < m} f(i)  \quad \mathrm{for} \quad  m > n

    It is important to note that Karr defines all sums with the upper
    limit being exclusive. This is in contrast to the usual mathematical notation,
    but does not affect the summation convention. Indeed we have:

    .. math::

        \sum_{m \leq i < n} f(i) = \sum_{i = m}^{n - 1} f(i)

    where the difference in notation is intentional to emphasize the meaning,
    with limits typeset on the top being inclusive.

    Examples
    ========

    >>> from sympy.abc import i, k, m, n, x
    >>> from sympy import Sum, factorial, oo, IndexedBase, Function
    >>> Sum(k, (k, 1, m))
    Sum(k, (k, 1, m))
    >>> Sum(k, (k, 1, m)).doit()
    m**2/2 + m/2
    >>> Sum(k**2, (k, 1, m))
    Sum(k**2, (k, 1, m))
    >>> Sum(k**2, (k, 1, m)).doit()
    m**3/3 + m**2/2 + m/6
    >>> Sum(x**k, (k, 0, oo))
    Sum(x**k, (k, 0, oo))
    >>> Sum(x**k, (k, 0, oo)).doit()
    Piecewise((1/(1 - x), Abs(x) < 1), (Sum(x**k, (k, 0, oo)), True))
    >>> Sum(x**k/factorial(k), (k, 0, oo)).doit()
    exp(x)

    Here are examples to do summation with symbolic indices.  You
    can use either Function of IndexedBase classes:

    >>> f = Function('f')
    >>> Sum(f(n), (n, 0, 3)).doit()
    f(0) + f(1) + f(2) + f(3)
    >>> Sum(f(n), (n, 0, oo)).doit()
    Sum(f(n), (n, 0, oo))
    >>> f = IndexedBase('f')
    >>> Sum(f[n]**2, (n, 0, 3)).doit()
    f[0]**2 + f[1]**2 + f[2]**2 + f[3]**2

    An example showing that the symbolic result of a summation is still
    valid for seemingly nonsensical values of the limits. Then the Karr
    convention allows us to give a perfectly valid interpretation to
    those sums by interchanging the limits according to the above rules:

    >>> S = Sum(i, (i, 1, n)).doit()
    >>> S
    n**2/2 + n/2
    >>> S.subs(n, -4)
    6
    >>> Sum(i, (i, 1, -4)).doit()
    6
    >>> Sum(-i, (i, -3, 0)).doit()
    6

    An explicit example of the Karr summation convention:

    >>> S1 = Sum(i**2, (i, m, m+n-1)).doit()
    >>> S1
    m**2*n + m*n**2 - m*n + n**3/3 - n**2/2 + n/6
    >>> S2 = Sum(i**2, (i, m+n, m-1)).doit()
    >>> S2
    -m**2*n - m*n**2 + m*n - n**3/3 + n**2/2 - n/6
    >>> S1 + S2
    0
    >>> S3 = Sum(i, (i, m, m-1)).doit()
    >>> S3
    0

    See Also
    ========

    summation
    Product, product

    References
    ==========

    .. [1] Michael Karr, "Summation in Finite Terms", Journal of the ACM,
           Volume 28 Issue 2, April 1981, Pages 305-350
           http://dl.acm.org/citation.cfm?doid=322248.322255
    .. [2] https://en.wikipedia.org/wiki/Summation#Capital-sigma_notation
    .. [3] https://en.wikipedia.org/wiki/Empty_sum
    """

    __slots__ = ['is_commutative']

    def __new__(cls, function, *symbols, **assumptions):
        obj = AddWithLimits.__new__(cls, function, *symbols, **assumptions)
        if not hasattr(obj, 'limits'):
            return obj
        if any(len(l) != 3 or None in l for l in obj.limits):
            raise ValueError('Sum requires values for lower and upper bounds.')

        return obj

    def _eval_is_zero(self):
        # a Sum is only zero if its function is zero or if all terms
        # cancel out. This only answers whether the summand is zero; if
        # not then None is returned since we don't analyze whether all
        # terms cancel out.
        if self.function.is_zero:
            return True

    def doit(self, **hints):
        if hints.get('deep', True):
            f = self.function.doit(**hints)
        else:
            f = self.function

        if self.function.is_Matrix:
            return self.expand().doit()

        for n, limit in enumerate(self.limits):
            i, a, b = limit
            dif = b - a
            if dif.is_integer and (dif < 0) == True:
                a, b = b + 1, a - 1
                f = -f

            newf = eval_sum(f, (i, a, b))
            if newf is None:
                if f == self.function:
                    zeta_function = self.eval_zeta_function(f, (i, a, b))
                    if zeta_function is not None:
                        return zeta_function
                    return self
                else:
                    return self.func(f, *self.limits[n:])
            f = newf

        if hints.get('deep', True):
            # eval_sum could return partially unevaluated
            # result with Piecewise.  In this case we won't
            # doit() recursively.
            if not isinstance(f, Piecewise):
                return f.doit(**hints)

        return f

    def eval_zeta_function(self, f, limits):
        """
        Check whether the function matches with the zeta function.
        If it matches, then return a `Piecewise` expression because
        zeta function does not converge unless `s > 1` and `q > 0`
        """
        i, a, b = limits
        w, y, z = Wild('w', exclude=[i]), Wild('y', exclude=[i]), Wild('z', exclude=[i])
        result = f.match((w * i + y) ** (-z))
        if result is not None and b == S.Infinity:
            coeff = 1 / result[w] ** result[z]
            s = result[z]
            q = result[y] / result[w] + a
            return Piecewise((coeff * zeta(s, q), And(q > 0, s > 1)), (self, True))

    def _eval_derivative(self, x):
        """
        Differentiate wrt x as long as x is not in the free symbols of any of
        the upper or lower limits.

        Sum(a*b*x, (x, 1, a)) can be differentiated wrt x or b but not `a`
        since the value of the sum is discontinuous in `a`. In a case
        involving a limit variable, the unevaluated derivative is returned.
        """

        # diff already confirmed that x is in the free symbols of self, but we
        # don't want to differentiate wrt any free symbol in the upper or lower
        # limits
        # XXX remove this test for free_symbols when the default _eval_derivative is in
        if isinstance(x, Symbol) and x not in self.free_symbols:
            return S.Zero

        # get limits and the function
        f, limits = self.function, list(self.limits)

        limit = limits.pop(-1)

        if limits:  # f is the argument to a Sum
            f = self.func(f, *limits)

        if len(limit) == 3:
            _, a, b = limit
            if x in a.free_symbols or x in b.free_symbols:
                return None
            df = Derivative(f, x, evaluate=True)
            rv = self.func(df, limit)
            return rv
        else:
            return NotImplementedError('Lower and upper bound expected.')

    def _eval_difference_delta(self, n, step):
        k, _, upper = self.args[-1]
        new_upper = upper.subs(n, n + step)

        if len(self.args) == 2:
            f = self.args[0]
        else:
            f = self.func(*self.args[:-1])

        return Sum(f, (k, upper + 1, new_upper)).doit()

    def _eval_simplify(self, ratio=1.7, measure=None, rational=False, inverse=False):
        from sympy.simplify.simplify import factor_sum, sum_combine
        from sympy.core.function import expand
        from sympy.core.mul import Mul

        # split the function into adds
        terms = Add.make_args(expand(self.function))
        s_t = [] # Sum Terms
        o_t = [] # Other Terms

        for term in terms:
            if term.has(Sum):
                # if there is an embedded sum here
                # it is of the form x * (Sum(whatever))
                # hence we make a Mul out of it, and simplify all interior sum terms
                subterms = Mul.make_args(expand(term))
                out_terms = []
                for subterm in subterms:
                    # go through each term
                    if isinstance(subterm, Sum):
                        # if it's a sum, simplify it
                        out_terms.append(subterm._eval_simplify())
                    else:
                        # otherwise, add it as is
                        out_terms.append(subterm)

                # turn it back into a Mul
                s_t.append(Mul(*out_terms))
            else:
                o_t.append(term)

        # next try to combine any interior sums for further simplification
        result = Add(sum_combine(s_t), *o_t)

        return factor_sum(result, limits=self.limits)

    def _eval_summation(self, f, x):
        return None

    def is_convergent(self):
        r"""Checks for the convergence of a Sum.

        We divide the study of convergence of infinite sums and products in
        two parts.

        First Part:
        One part is the question whether all the terms are well defined, i.e.,
        they are finite in a sum and also non-zero in a product. Zero
        is the analogy of (minus) infinity in products as
        :math:`e^{-\infty} = 0`.

        Second Part:
        The second part is the question of convergence after infinities,
        and zeros in products, have been omitted assuming that their number
        is finite. This means that we only consider the tail of the sum or
        product, starting from some point after which all terms are well
        defined.

        For example, in a sum of the form:

        .. math::

            \sum_{1 \leq i < \infty} \frac{1}{n^2 + an + b}

        where a and b are numbers. The routine will return true, even if there
        are infinities in the term sequence (at most two). An analogous
        product would be:

        .. math::

            \prod_{1 \leq i < \infty} e^{\frac{1}{n^2 + an + b}}

        This is how convergence is interpreted. It is concerned with what
        happens at the limit. Finding the bad terms is another independent
        matter.

        Note: It is responsibility of user to see that the sum or product
        is well defined.

        There are various tests employed to check the convergence like
        divergence test, root test, integral test, alternating series test,
        comparison tests, Dirichlet tests. It returns true if Sum is convergent
        and false if divergent and NotImplementedError if it can not be checked.

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Convergence_tests

        Examples
        ========

        >>> from sympy import factorial, S, Sum, Symbol, oo
        >>> n = Symbol('n', integer=True)
        >>> Sum(n/(n - 1), (n, 4, 7)).is_convergent()
        True
        >>> Sum(n/(2*n + 1), (n, 1, oo)).is_convergent()
        False
        >>> Sum(factorial(n)/5**n, (n, 1, oo)).is_convergent()
        False
        >>> Sum(1/n**(S(6)/5), (n, 1, oo)).is_convergent()
        True

        See Also
        ========

        Sum.is_absolutely_convergent()
        Product.is_convergent()
        """
        from sympy import Interval, Integral, log, symbols, simplify
        p, q, r = symbols('p q r', cls=Wild)

        sym = self.limits[0][0]
        lower_limit = self.limits[0][1]
        upper_limit = self.limits[0][2]
        sequence_term = self.function

        if len(sequence_term.free_symbols) > 1:
            raise NotImplementedError("convergence checking for more than one symbol "
                                      "containing series is not handled")

        if lower_limit.is_finite and upper_limit.is_finite:
            return S.true

        # transform sym -> -sym and swap the upper_limit = S.Infinity
        # and lower_limit = - upper_limit
        if lower_limit is S.NegativeInfinity:
            if upper_limit is S.Infinity:
                return Sum(sequence_term, (sym, 0, S.Infinity)).is_convergent() and \
                        Sum(sequence_term, (sym, S.NegativeInfinity, 0)).is_convergent()
            sequence_term = simplify(sequence_term.xreplace({sym: -sym}))
            lower_limit = -upper_limit
            upper_limit = S.Infinity

        sym_ = Dummy(sym.name, integer=True, positive=True)
        sequence_term = sequence_term.xreplace({sym: sym_})
        sym = sym_

        interval = Interval(lower_limit, upper_limit)

        # Piecewise function handle
        if sequence_term.is_Piecewise:
            for func, cond in sequence_term.args:
                # see if it represents something going to oo
                if cond == True or cond.as_set().sup is S.Infinity:
                    s = Sum(func, (sym, lower_limit, upper_limit))
                    return s.is_convergent()
            return S.true

        ###  -------- Divergence test ----------- ###
        try:
            lim_val = limit_seq(sequence_term, sym)
            if lim_val is not None and lim_val.is_zero is False:
                return S.false
        except NotImplementedError:
            pass

        try:
            lim_val_abs = limit_seq(abs(sequence_term), sym)
            if lim_val_abs is not None and lim_val_abs.is_zero is False:
                return S.false
        except NotImplementedError:
            pass

        order = O(sequence_term, (sym, S.Infinity))

        ### --------- p-series test (1/n**p) ---------- ###
        p1_series_test = order.expr.match(sym**p)
        if p1_series_test is not None:
            if p1_series_test[p] < -1:
                return S.true
            if p1_series_test[p] >= -1:
                return S.false

        p2_series_test = order.expr.match((1/sym)**p)
        if p2_series_test is not None:
            if p2_series_test[p] > 1:
                return S.true
            if p2_series_test[p] <= 1:
                return S.false

        ### ------------- comparison test ------------- ###
        # 1/(n**p*log(n)**q*log(log(n))**r) comparison
        n_log_test = order.expr.match(1/(sym**p*log(sym)**q*log(log(sym))**r))
        if n_log_test is not None:
            if (n_log_test[p] > 1 or
                (n_log_test[p] == 1 and n_log_test[q] > 1) or
                (n_log_test[p] == n_log_test[q] == 1 and n_log_test[r] > 1)):
                    return S.true
            return S.false

        ### ------------- Limit comparison test -----------###
        # (1/n) comparison
        try:
            lim_comp = limit_seq(sym*sequence_term, sym)
            if lim_comp is not None and lim_comp.is_number and lim_comp > 0:
                return S.false
        except NotImplementedError:
            pass

        ### ----------- ratio test ---------------- ###
        next_sequence_term = sequence_term.xreplace({sym: sym + 1})
        ratio = combsimp(powsimp(next_sequence_term/sequence_term))
        try:
            lim_ratio = limit_seq(ratio, sym)
            if lim_ratio is not None and lim_ratio.is_number:
                if abs(lim_ratio) > 1:
                    return S.false
                if abs(lim_ratio) < 1:
                    return S.true
        except NotImplementedError:
            pass

        ### ----------- root test ---------------- ###
        # lim = Limit(abs(sequence_term)**(1/sym), sym, S.Infinity)
        try:
            lim_evaluated = limit_seq(abs(sequence_term)**(1/sym), sym)
            if lim_evaluated is not None and lim_evaluated.is_number:
                if lim_evaluated < 1:
                    return S.true
                if lim_evaluated > 1:
                    return S.false
        except NotImplementedError:
            pass

        ### ------------- alternating series test ----------- ###
        dict_val = sequence_term.match((-1)**(sym + p)*q)
        if not dict_val[p].has(sym) and is_decreasing(dict_val[q], interval):
            return S.true


        ### ------------- integral test -------------- ###
        check_interval = None
        maxima = solveset(sequence_term.diff(sym), sym, interval)
        if not maxima:
            check_interval = interval
        elif isinstance(maxima, FiniteSet) and maxima.sup.is_number:
            check_interval = Interval(maxima.sup, interval.sup)
        if (check_interval is not None and
            (is_decreasing(sequence_term, check_interval) or
            is_decreasing(-sequence_term, check_interval))):
                integral_val = Integral(
                    sequence_term, (sym, lower_limit, upper_limit))
                try:
                    integral_val_evaluated = integral_val.doit()
                    if integral_val_evaluated.is_number:
                        return S(integral_val_evaluated.is_finite)
                except NotImplementedError:
                    pass

        ### ----- Dirichlet and bounded times convergent tests ----- ###
        # TODO
        #
        # Dirichlet_test
        # https://en.wikipedia.org/wiki/Dirichlet%27s_test
        #
        # Bounded times convergent test
        # It is based on comparison theorems for series.
        # In particular, if the general term of a series can
        # be written as a product of two terms a_n and b_n
        # and if a_n is bounded and if Sum(b_n) is absolutely
        # convergent, then the original series Sum(a_n * b_n)
        # is absolutely convergent and so convergent.
        #
        # The following code can grows like 2**n where n is the
        # number of args in order.expr
        # Possibly combined with the potentially slow checks
        # inside the loop, could make this test extremely slow
        # for larger summation expressions.

        if order.expr.is_Mul:
            args = order.expr.args
            argset = set(args)

            ### -------------- Dirichlet tests -------------- ###
            m = Dummy('m', integer=True)
            def _dirichlet_test(g_n):
                try:
                    ing_val = limit_seq(Sum(g_n, (sym, interval.inf, m)).doit(), m)
                    if ing_val is not None and ing_val.is_finite:
                        return S.true
                except NotImplementedError:
                    pass

            ### -------- bounded times convergent test ---------###
            def _bounded_convergent_test(g1_n, g2_n):
                try:
                    lim_val = limit_seq(g1_n, sym)
                    if lim_val is not None and (lim_val.is_finite or (
                        isinstance(lim_val, AccumulationBounds)
                        and (lim_val.max - lim_val.min).is_finite)):
                            if Sum(g2_n, (sym, lower_limit, upper_limit)).is_absolutely_convergent():
                                return S.true
                except NotImplementedError:
                    pass

            for n in range(1, len(argset)):
                for a_tuple in itertools.combinations(args, n):
                    b_set = argset - set(a_tuple)
                    a_n = Mul(*a_tuple)
                    b_n = Mul(*b_set)

                    if is_decreasing(a_n, interval):
                        dirich = _dirichlet_test(b_n)
                        if dirich is not None:
                            return dirich

                    bc_test = _bounded_convergent_test(a_n, b_n)
                    if bc_test is not None:
                        return bc_test

        _sym = self.limits[0][0]
        sequence_term = sequence_term.xreplace({sym: _sym})
        raise NotImplementedError("The algorithm to find the Sum convergence of %s "
                                  "is not yet implemented" % (sequence_term))

    def is_absolutely_convergent(self):
        """
        Checks for the absolute convergence of an infinite series.

        Same as checking convergence of absolute value of sequence_term of
        an infinite series.

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Absolute_convergence

        Examples
        ========

        >>> from sympy import Sum, Symbol, sin, oo
        >>> n = Symbol('n', integer=True)
        >>> Sum((-1)**n, (n, 1, oo)).is_absolutely_convergent()
        False
        >>> Sum((-1)**n/n**2, (n, 1, oo)).is_absolutely_convergent()
        True

        See Also
        ========

        Sum.is_convergent()
        """
        return Sum(abs(self.function), self.limits).is_convergent()

    def euler_maclaurin(self, m=0, n=0, eps=0, eval_integral=True):
        """
        Return an Euler-Maclaurin approximation of self, where m is the
        number of leading terms to sum directly and n is the number of
        terms in the tail.

        With m = n = 0, this is simply the corresponding integral
        plus a first-order endpoint correction.

        Returns (s, e) where s is the Euler-Maclaurin approximation
        and e is the estimated error (taken to be the magnitude of
        the first omitted term in the tail):

            >>> from sympy.abc import k, a, b
            >>> from sympy import Sum
            >>> Sum(1/k, (k, 2, 5)).doit().evalf()
            1.28333333333333
            >>> s, e = Sum(1/k, (k, 2, 5)).euler_maclaurin()
            >>> s
            -log(2) + 7/20 + log(5)
            >>> from sympy import sstr
            >>> print(sstr((s.evalf(), e.evalf()), full_prec=True))
            (1.26629073187415, 0.0175000000000000)

        The endpoints may be symbolic:

            >>> s, e = Sum(1/k, (k, a, b)).euler_maclaurin()
            >>> s
            -log(a) + log(b) + 1/(2*b) + 1/(2*a)
            >>> e
            Abs(1/(12*b**2) - 1/(12*a**2))

        If the function is a polynomial of degree at most 2n+1, the
        Euler-Maclaurin formula becomes exact (and e = 0 is returned):

            >>> Sum(k, (k, 2, b)).euler_maclaurin()
            (b**2/2 + b/2 - 1, 0)
            >>> Sum(k, (k, 2, b)).doit()
            b**2/2 + b/2 - 1

        With a nonzero eps specified, the summation is ended
        as soon as the remainder term is less than the epsilon.
        """
        from sympy.functions import bernoulli, factorial
        from sympy.integrals import Integral

        m = int(m)
        n = int(n)
        f = self.function
        if len(self.limits) != 1:
            raise ValueError("More than 1 limit")
        i, a, b = self.limits[0]
        if (a > b) == True:
            if a - b == 1:
                return S.Zero, S.Zero
            a, b = b + 1, a - 1
            f = -f
        s = S.Zero
        if m:
            if b.is_Integer and a.is_Integer:
                m = min(m, b - a + 1)
            if not eps or f.is_polynomial(i):
                for k in range(m):
                    s += f.subs(i, a + k)
            else:
                term = f.subs(i, a)
                if term:
                    test = abs(term.evalf(3)) < eps
                    if test == True:
                        return s, abs(term)
                    elif not (test == False):
                        # a symbolic Relational class, can't go further
                        return term, S.Zero
                s += term
                for k in range(1, m):
                    term = f.subs(i, a + k)
                    if abs(term.evalf(3)) < eps and term != 0:
                        return s, abs(term)
                    s += term
            if b - a + 1 == m:
                return s, S.Zero
            a += m
        x = Dummy('x')
        I = Integral(f.subs(i, x), (x, a, b))
        if eval_integral:
            I = I.doit()
        s += I

        def fpoint(expr):
            if b is S.Infinity:
                return expr.subs(i, a), 0
            return expr.subs(i, a), expr.subs(i, b)
        fa, fb = fpoint(f)
        iterm = (fa + fb)/2
        g = f.diff(i)
        for k in range(1, n + 2):
            ga, gb = fpoint(g)
            term = bernoulli(2*k)/factorial(2*k)*(gb - ga)
            if (eps and term and abs(term.evalf(3)) < eps) or (k > n):
                break
            s += term
            g = g.diff(i, 2, simplify=False)
        return s + iterm, abs(term)


    def reverse_order(self, *indices):
        """
        Reverse the order of a limit in a Sum.

        Usage
        =====

        ``reverse_order(self, *indices)`` reverses some limits in the expression
        ``self`` which can be either a ``Sum`` or a ``Product``. The selectors in
        the argument ``indices`` specify some indices whose limits get reversed.
        These selectors are either variable names or numerical indices counted
        starting from the inner-most limit tuple.

        Examples
        ========

        >>> from sympy import Sum
        >>> from sympy.abc import x, y, a, b, c, d

        >>> Sum(x, (x, 0, 3)).reverse_order(x)
        Sum(-x, (x, 4, -1))
        >>> Sum(x*y, (x, 1, 5), (y, 0, 6)).reverse_order(x, y)
        Sum(x*y, (x, 6, 0), (y, 7, -1))
        >>> Sum(x, (x, a, b)).reverse_order(x)
        Sum(-x, (x, b + 1, a - 1))
        >>> Sum(x, (x, a, b)).reverse_order(0)
        Sum(-x, (x, b + 1, a - 1))

        While one should prefer variable names when specifying which limits
        to reverse, the index counting notation comes in handy in case there
        are several symbols with the same name.

        >>> S = Sum(x**2, (x, a, b), (x, c, d))
        >>> S
        Sum(x**2, (x, a, b), (x, c, d))
        >>> S0 = S.reverse_order(0)
        >>> S0
        Sum(-x**2, (x, b + 1, a - 1), (x, c, d))
        >>> S1 = S0.reverse_order(1)
        >>> S1
        Sum(x**2, (x, b + 1, a - 1), (x, d + 1, c - 1))

        Of course we can mix both notations:

        >>> Sum(x*y, (x, a, b), (y, 2, 5)).reverse_order(x, 1)
        Sum(x*y, (x, b + 1, a - 1), (y, 6, 1))
        >>> Sum(x*y, (x, a, b), (y, 2, 5)).reverse_order(y, x)
        Sum(x*y, (x, b + 1, a - 1), (y, 6, 1))

        See Also
        ========

        index, reorder_limit, reorder

        References
        ==========

        .. [1] Michael Karr, "Summation in Finite Terms", Journal of the ACM,
               Volume 28 Issue 2, April 1981, Pages 305-350
               http://dl.acm.org/citation.cfm?doid=322248.322255
        """
        l_indices = list(indices)

        for i, indx in enumerate(l_indices):
            if not isinstance(indx, int):
                l_indices[i] = self.index(indx)

        e = 1
        limits = []
        for i, limit in enumerate(self.limits):
            l = limit
            if i in l_indices:
                e = -e
                l = (limit[0], limit[2] + 1, limit[1] - 1)
            limits.append(l)

        return Sum(e * self.function, *limits)


def summation(f, *symbols, **kwargs):
    r"""
    Compute the summation of f with respect to symbols.

    The notation for symbols is similar to the notation used in Integral.
    summation(f, (i, a, b)) computes the sum of f with respect to i from a to b,
    i.e.,

    ::

                                    b
                                  ____
                                  \   `
        summation(f, (i, a, b)) =  )    f
                                  /___,
                                  i = a

    If it cannot compute the sum, it returns an unevaluated Sum object.
    Repeated sums can be computed by introducing additional symbols tuples::

    >>> from sympy import summation, oo, symbols, log
    >>> i, n, m = symbols('i n m', integer=True)

    >>> summation(2*i - 1, (i, 1, n))
    n**2
    >>> summation(1/2**i, (i, 0, oo))
    2
    >>> summation(1/log(n)**n, (n, 2, oo))
    Sum(log(n)**(-n), (n, 2, oo))
    >>> summation(i, (i, 0, n), (n, 0, m))
    m**3/6 + m**2/2 + m/3

    >>> from sympy.abc import x
    >>> from sympy import factorial
    >>> summation(x**n/factorial(n), (n, 0, oo))
    exp(x)

    See Also
    ========

    Sum
    Product, product

    """
    return Sum(f, *symbols, **kwargs).doit(deep=False)


def telescopic_direct(L, R, n, limits):
    """Returns the direct summation of the terms of a telescopic sum

    L is the term with lower index
    R is the term with higher index
    n difference between the indexes of L and R

    For example:

    >>> from sympy.concrete.summations import telescopic_direct
    >>> from sympy.abc import k, a, b
    >>> telescopic_direct(1/k, -1/(k+2), 2, (k, a, b))
    -1/(b + 2) - 1/(b + 1) + 1/(a + 1) + 1/a

    """
    (i, a, b) = limits
    s = 0
    for m in range(n):
        s += L.subs(i, a + m) + R.subs(i, b - m)
    return s


def telescopic(L, R, limits):
    '''Tries to perform the summation using the telescopic property

    return None if not possible
    '''
    (i, a, b) = limits
    if L.is_Add or R.is_Add:
        return None

    # We want to solve(L.subs(i, i + m) + R, m)
    # First we try a simple match since this does things that
    # solve doesn't do, e.g. solve(f(k+m)-f(k), m) fails

    k = Wild("k")
    sol = (-R).match(L.subs(i, i + k))
    s = None
    if sol and k in sol:
        s = sol[k]
        if not (s.is_Integer and L.subs(i, i + s) == -R):
            # sometimes match fail(f(x+2).match(-f(x+k))->{k: -2 - 2x}))
            s = None

    # But there are things that match doesn't do that solve
    # can do, e.g. determine that 1/(x + m) = 1/(1 - x) when m = 1

    if s is None:
        m = Dummy('m')
        try:
            sol = solve(L.subs(i, i + m) + R, m) or []
        except NotImplementedError:
            return None
        sol = [si for si in sol if si.is_Integer and
               (L.subs(i, i + si) + R).expand().is_zero]
        if len(sol) != 1:
            return None
        s = sol[0]

    if s < 0:
        return telescopic_direct(R, L, abs(s), (i, a, b))
    elif s > 0:
        return telescopic_direct(L, R, s, (i, a, b))


def eval_sum(f, limits):
    from sympy.concrete.delta import deltasummation, _has_simple_delta
    from sympy.functions import KroneckerDelta

    (i, a, b) = limits
    if f is S.Zero:
        return S.Zero
    if i not in f.free_symbols:
        return f*(b - a + 1)
    if a == b:
        return f.subs(i, a)
    if isinstance(f, Piecewise):
        if not any(i in arg.args[1].free_symbols for arg in f.args):
            # Piecewise conditions do not depend on the dummy summation variable,
            # therefore we can fold:     Sum(Piecewise((e, c), ...), limits)
            #                        --> Piecewise((Sum(e, limits), c), ...)
            newargs = []
            for arg in f.args:
                newexpr = eval_sum(arg.expr, limits)
                if newexpr is None:
                    return None
                newargs.append((newexpr, arg.cond))
            return f.func(*newargs)

    if f.has(KroneckerDelta) and _has_simple_delta(f, limits[0]):
        return deltasummation(f, limits)

    dif = b - a
    definite = dif.is_Integer
    # Doing it directly may be faster if there are very few terms.
    if definite and (dif < 100):
        return eval_sum_direct(f, (i, a, b))
    if isinstance(f, Piecewise):
        return None
    # Try to do it symbolically. Even when the number of terms is known,
    # this can save time when b-a is big.
    # We should try to transform to partial fractions
    value = eval_sum_symbolic(f.expand(), (i, a, b))
    if value is not None:
        return value
    # Do it directly
    if definite:
        return eval_sum_direct(f, (i, a, b))


def eval_sum_direct(expr, limits):
    from sympy.core import Add
    (i, a, b) = limits

    dif = b - a
    return Add(*[expr.subs(i, a + j) for j in range(dif + 1)])


def eval_sum_symbolic(f, limits):
    from sympy.functions import harmonic, bernoulli

    f_orig = f
    (i, a, b) = limits
    if not f.has(i):
        return f*(b - a + 1)

    # Linearity
    if f.is_Mul:
        L, R = f.as_two_terms()

        if not L.has(i):
            sR = eval_sum_symbolic(R, (i, a, b))
            if sR:
                return L*sR

        if not R.has(i):
            sL = eval_sum_symbolic(L, (i, a, b))
            if sL:
                return R*sL

        try:
            f = apart(f, i)  # see if it becomes an Add
        except PolynomialError:
            pass

    if f.is_Add:
        L, R = f.as_two_terms()
        lrsum = telescopic(L, R, (i, a, b))

        if lrsum:
            return lrsum

        lsum = eval_sum_symbolic(L, (i, a, b))
        rsum = eval_sum_symbolic(R, (i, a, b))

        if None not in (lsum, rsum):
            r = lsum + rsum
            if not r is S.NaN:
                return r

    # Polynomial terms with Faulhaber's formula
    n = Wild('n')
    result = f.match(i**n)

    if result is not None:
        n = result[n]

        if n.is_Integer:
            if n >= 0:
                if (b is S.Infinity and not a is S.NegativeInfinity) or \
                   (a is S.NegativeInfinity and not b is S.Infinity):
                    return S.Infinity
                return ((bernoulli(n + 1, b + 1) - bernoulli(n + 1, a))/(n + 1)).expand()
            elif a.is_Integer and a >= 1:
                if n == -1:
                    return harmonic(b) - harmonic(a - 1)
                else:
                    return harmonic(b, abs(n)) - harmonic(a - 1, abs(n))

    if not (a.has(S.Infinity, S.NegativeInfinity) or
            b.has(S.Infinity, S.NegativeInfinity)):
        # Geometric terms
        c1 = Wild('c1', exclude=[i])
        c2 = Wild('c2', exclude=[i])
        c3 = Wild('c3', exclude=[i])
        wexp = Wild('wexp')

        # Here we first attempt powsimp on f for easier matching with the
        # exponential pattern, and attempt expansion on the exponent for easier
        # matching with the linear pattern.
        e = f.powsimp().match(c1 ** wexp)
        if e is not None:
            e_exp = e.pop(wexp).expand().match(c2*i + c3)
            if e_exp is not None:
                e.update(e_exp)

        if e is not None:
            p = (c1**c3).subs(e)
            q = (c1**c2).subs(e)

            r = p*(q**a - q**(b + 1))/(1 - q)
            l = p*(b - a + 1)

            return Piecewise((l, Eq(q, S.One)), (r, True))

        r = gosper_sum(f, (i, a, b))

        if isinstance(r, (Mul,Add)):
            from sympy import ordered, Tuple
            non_limit = r.free_symbols - Tuple(*limits[1:]).free_symbols
            den = denom(together(r))
            den_sym = non_limit & den.free_symbols
            args = []
            for v in ordered(den_sym):
                try:
                    s = solve(den, v)
                    m = Eq(v, s[0]) if s else S.false
                    if m != False:
                        args.append((Sum(f_orig.subs(*m.args), limits).doit(), m))
                    break
                except NotImplementedError:
                    continue

            args.append((r, True))
            return Piecewise(*args)

        if not r in (None, S.NaN):
            return r

    h = eval_sum_hyper(f_orig, (i, a, b))
    if h is not None:
        return h

    factored = f_orig.factor()
    if factored != f_orig:
        return eval_sum_symbolic(factored, (i, a, b))


def _eval_sum_hyper(f, i, a):
    """ Returns (res, cond). Sums from a to oo. """
    from sympy.functions import hyper
    from sympy.simplify import hyperexpand, hypersimp, fraction, simplify
    from sympy.polys.polytools import Poly, factor
    from sympy.core.numbers import Float

    if a != 0:
        return _eval_sum_hyper(f.subs(i, i + a), i, 0)

    if f.subs(i, 0) == 0:
        if simplify(f.subs(i, Dummy('i', integer=True, positive=True))) == 0:
            return S(0), True
        return _eval_sum_hyper(f.subs(i, i + 1), i, 0)

    hs = hypersimp(f, i)
    if hs is None:
        return None

    if isinstance(hs, Float):
        from sympy.simplify.simplify import nsimplify
        hs = nsimplify(hs)

    numer, denom = fraction(factor(hs))
    top, topl = numer.as_coeff_mul(i)
    bot, botl = denom.as_coeff_mul(i)
    ab = [top, bot]
    factors = [topl, botl]
    params = [[], []]
    for k in range(2):
        for fac in factors[k]:
            mul = 1
            if fac.is_Pow:
                mul = fac.exp
                fac = fac.base
                if not mul.is_Integer:
                    return None
            p = Poly(fac, i)
            if p.degree() != 1:
                return None
            m, n = p.all_coeffs()
            ab[k] *= m**mul
            params[k] += [n/m]*mul

    # Add "1" to numerator parameters, to account for implicit n! in
    # hypergeometric series.
    ap = params[0] + [1]
    bq = params[1]
    x = ab[0]/ab[1]
    h = hyper(ap, bq, x)
    f = combsimp(f)
    return f.subs(i, 0)*hyperexpand(h), h.convergence_statement


def eval_sum_hyper(f, i_a_b):
    from sympy.logic.boolalg import And

    i, a, b = i_a_b

    if (b - a).is_Integer:
        # We are never going to do better than doing the sum in the obvious way
        return None

    old_sum = Sum(f, (i, a, b))

    if b != S.Infinity:
        if a == S.NegativeInfinity:
            res = _eval_sum_hyper(f.subs(i, -i), i, -b)
            if res is not None:
                return Piecewise(res, (old_sum, True))
        else:
            res1 = _eval_sum_hyper(f, i, a)
            res2 = _eval_sum_hyper(f, i, b + 1)
            if res1 is None or res2 is None:
                return None
            (res1, cond1), (res2, cond2) = res1, res2
            cond = And(cond1, cond2)
            if cond == False:
                return None
            return Piecewise((res1 - res2, cond), (old_sum, True))

    if a == S.NegativeInfinity:
        res1 = _eval_sum_hyper(f.subs(i, -i), i, 1)
        res2 = _eval_sum_hyper(f, i, 0)
        if res1 is None or res2 is None:
            return None
        res1, cond1 = res1
        res2, cond2 = res2
        cond = And(cond1, cond2)
        if cond == False or cond.as_set() == S.EmptySet:
            return None
        return Piecewise((res1 + res2, cond), (old_sum, True))

    # Now b == oo, a != -oo
    res = _eval_sum_hyper(f, i, a)
    if res is not None:
        r, c = res
        if c == False:
            if r.is_number:
                f = f.subs(i, Dummy('i', integer=True, positive=True) + a)
                if f.is_positive or f.is_zero:
                    return S.Infinity
                elif f.is_negative:
                    return S.NegativeInfinity
            return None
        return Piecewise(res, (old_sum, True))
