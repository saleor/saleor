from __future__ import print_function, division

from sympy.core import Basic, S, Function, diff, Tuple, Dummy, Symbol
from sympy.core.basic import as_Basic
from sympy.core.compatibility import range
from sympy.core.numbers import Rational, NumberSymbol
from sympy.core.relational import (Equality, Unequality, Relational,
    _canonical)
from sympy.functions.elementary.miscellaneous import Max, Min
from sympy.logic.boolalg import (And, Boolean, distribute_and_over_or,
    true, false, Or, ITE, simplify_logic)
from sympy.utilities.iterables import uniq, ordered, product, sift
from sympy.utilities.misc import filldedent, func_name


Undefined = S.NaN  # Piecewise()

class ExprCondPair(Tuple):
    """Represents an expression, condition pair."""

    def __new__(cls, expr, cond):
        expr = as_Basic(expr)
        if cond == True:
            return Tuple.__new__(cls, expr, true)
        elif cond == False:
            return Tuple.__new__(cls, expr, false)
        elif isinstance(cond, Basic) and cond.has(Piecewise):
            cond = piecewise_fold(cond)
            if isinstance(cond, Piecewise):
                cond = cond.rewrite(ITE)

        if not isinstance(cond, Boolean):
            raise TypeError(filldedent('''
                Second argument must be a Boolean,
                not `%s`''' % func_name(cond)))
        return Tuple.__new__(cls, expr, cond)

    @property
    def expr(self):
        """
        Returns the expression of this pair.
        """
        return self.args[0]

    @property
    def cond(self):
        """
        Returns the condition of this pair.
        """
        return self.args[1]

    @property
    def is_commutative(self):
        return self.expr.is_commutative

    def __iter__(self):
        yield self.expr
        yield self.cond

    def _eval_simplify(self, ratio, measure, rational, inverse):
        return self.func(*[a.simplify(
            ratio=ratio,
            measure=measure,
            rational=rational,
            inverse=inverse) for a in self.args])

class Piecewise(Function):
    """
    Represents a piecewise function.

    Usage:

      Piecewise( (expr,cond), (expr,cond), ... )
        - Each argument is a 2-tuple defining an expression and condition
        - The conds are evaluated in turn returning the first that is True.
          If any of the evaluated conds are not determined explicitly False,
          e.g. x < 1, the function is returned in symbolic form.
        - If the function is evaluated at a place where all conditions are False,
          nan will be returned.
        - Pairs where the cond is explicitly False, will be removed.

    Examples
    ========

    >>> from sympy import Piecewise, log, ITE, piecewise_fold
    >>> from sympy.abc import x, y
    >>> f = x**2
    >>> g = log(x)
    >>> p = Piecewise((0, x < -1), (f, x <= 1), (g, True))
    >>> p.subs(x,1)
    1
    >>> p.subs(x,5)
    log(5)

    Booleans can contain Piecewise elements:

    >>> cond = (x < y).subs(x, Piecewise((2, x < 0), (3, True))); cond
    Piecewise((2, x < 0), (3, True)) < y

    The folded version of this results in a Piecewise whose
    expressions are Booleans:

    >>> folded_cond = piecewise_fold(cond); folded_cond
    Piecewise((2 < y, x < 0), (3 < y, True))

    When a Boolean containing Piecewise (like cond) or a Piecewise
    with Boolean expressions (like folded_cond) is used as a condition,
    it is converted to an equivalent ITE object:

    >>> Piecewise((1, folded_cond))
    Piecewise((1, ITE(x < 0, y > 2, y > 3)))

    When a condition is an ITE, it will be converted to a simplified
    Boolean expression:

    >>> piecewise_fold(_)
    Piecewise((1, ((x >= 0) | (y > 2)) & ((y > 3) | (x < 0))))

    See Also
    ========
    piecewise_fold, ITE
    """

    nargs = None
    is_Piecewise = True

    def __new__(cls, *args, **options):
        if len(args) == 0:
            raise TypeError("At least one (expr, cond) pair expected.")
        # (Try to) sympify args first
        newargs = []
        for ec in args:
            # ec could be a ExprCondPair or a tuple
            pair = ExprCondPair(*getattr(ec, 'args', ec))
            cond = pair.cond
            if cond is false:
                continue
            newargs.append(pair)
            if cond is true:
                break

        if options.pop('evaluate', True):
            r = cls.eval(*newargs)
        else:
            r = None

        if r is None:
            return Basic.__new__(cls, *newargs, **options)
        else:
            return r

    @classmethod
    def eval(cls, *_args):
        """Either return a modified version of the args or, if no
        modifications were made, return None.

        Modifications that are made here:
        1) relationals are made canonical
        2) any False conditions are dropped
        3) any repeat of a previous condition is ignored
        3) any args past one with a true condition are dropped

        If there are no args left, nan will be returned.
        If there is a single arg with a True condition, its
        corresponding expression will be returned.
        """

        if not _args:
            return Undefined

        if len(_args) == 1 and _args[0][-1] == True:
            return _args[0][0]

        newargs = []  # the unevaluated conditions
        current_cond = set()  # the conditions up to a given e, c pair
        # make conditions canonical
        args = []
        for e, c in _args:
            if not c.is_Atom and not isinstance(c, Relational):
                free = c.free_symbols
                if len(free) == 1:
                    funcs = [i for i in c.atoms(Function)
                        if not isinstance(i, Boolean)]
                    if len(funcs) == 1 and len(
                            c.xreplace({list(funcs)[0]: Dummy()}
                            ).free_symbols) == 1:
                        # we can treat function like a symbol
                        free = funcs
                    _c = c
                    x = free.pop()
                    try:
                        c = c.as_set().as_relational(x)
                    except NotImplementedError:
                        pass
                    else:
                        reps = {}
                        for i in c.atoms(Relational):
                            ic = i.canonical
                            if ic.rhs in (S.Infinity, S.NegativeInfinity):
                                if not _c.has(ic.rhs):
                                    # don't accept introduction of
                                    # new Relationals with +/-oo
                                    reps[i] = S.true
                                elif ('=' not in ic.rel_op and
                                        c.xreplace({x: i.rhs}) !=
                                        _c.xreplace({x: i.rhs})):
                                    reps[i] = Relational(
                                        i.lhs, i.rhs, i.rel_op + '=')
                        c = c.xreplace(reps)
            args.append((e, _canonical(c)))

        for expr, cond in args:
            # Check here if expr is a Piecewise and collapse if one of
            # the conds in expr matches cond. This allows the collapsing
            # of Piecewise((Piecewise((x,x<0)),x<0)) to Piecewise((x,x<0)).
            # This is important when using piecewise_fold to simplify
            # multiple Piecewise instances having the same conds.
            # Eventually, this code should be able to collapse Piecewise's
            # having different intervals, but this will probably require
            # using the new assumptions.
            if isinstance(expr, Piecewise):
                unmatching = []
                for i, (e, c) in enumerate(expr.args):
                    if c in current_cond:
                        # this would already have triggered
                        continue
                    if c == cond:
                        if c != True:
                            # nothing past this condition will ever
                            # trigger and only those args before this
                            # that didn't match a previous condition
                            # could possibly trigger
                            if unmatching:
                                expr = Piecewise(*(
                                    unmatching + [(e, c)]))
                            else:
                                expr = e
                        break
                    else:
                        unmatching.append((e, c))

            # check for condition repeats
            got = False
            # -- if an And contains a condition that was
            #    already encountered, then the And will be
            #    False: if the previous condition was False
            #    then the And will be False and if the previous
            #    condition is True then then we wouldn't get to
            #    this point. In either case, we can skip this condition.
            for i in ([cond] +
                    (list(cond.args) if isinstance(cond, And) else
                    [])):
                if i in current_cond:
                    got = True
                    break
            if got:
                continue

            # -- if not(c) is already in current_cond then c is
            #    a redundant condition in an And. This does not
            #    apply to Or, however: (e1, c), (e2, Or(~c, d))
            #    is not (e1, c), (e2, d) because if c and d are
            #    both False this would give no results when the
            #    true answer should be (e2, True)
            if isinstance(cond, And):
                nonredundant = []
                for c in cond.args:
                    if (isinstance(c, Relational) and
                            c.negated.canonical in current_cond):
                        continue
                    nonredundant.append(c)
                cond = cond.func(*nonredundant)
            elif isinstance(cond, Relational):
                if cond.negated.canonical in current_cond:
                    cond = S.true

            current_cond.add(cond)

            # collect successive e,c pairs when exprs or cond match
            if newargs:
                if newargs[-1].expr == expr:
                    orcond = Or(cond, newargs[-1].cond)
                    if isinstance(orcond, (And, Or)):
                        orcond = distribute_and_over_or(orcond)
                    newargs[-1] = ExprCondPair(expr, orcond)
                    continue
                elif newargs[-1].cond == cond:
                    orexpr = Or(expr, newargs[-1].expr)
                    if isinstance(orexpr, (And, Or)):
                        orexpr = distribute_and_over_or(orexpr)
                    newargs[-1] == ExprCondPair(orexpr, cond)
                    continue

            newargs.append(ExprCondPair(expr, cond))

        # some conditions may have been redundant
        missing = len(newargs) != len(_args)
        # some conditions may have changed
        same = all(a == b for a, b in zip(newargs, _args))
        # if either change happened we return the expr with the
        # updated args
        if not newargs:
            raise ValueError(filldedent('''
                There are no conditions (or none that
                are not trivially false) to define an
                expression.'''))
        if missing or not same:
            return cls(*newargs)

    def doit(self, **hints):
        """
        Evaluate this piecewise function.
        """
        newargs = []
        for e, c in self.args:
            if hints.get('deep', True):
                if isinstance(e, Basic):
                    e = e.doit(**hints)
                if isinstance(c, Basic):
                    c = c.doit(**hints)
            newargs.append((e, c))
        return self.func(*newargs)

    def _eval_simplify(self, ratio, measure, rational, inverse):
        args = [a._eval_simplify(ratio, measure, rational, inverse)
            for a in self.args]
        _blessed = lambda e: getattr(e.lhs, '_diff_wrt', False) and (
            getattr(e.rhs, '_diff_wrt', None) or
            isinstance(e.rhs, (Rational, NumberSymbol)))
        for i, (expr, cond) in enumerate(args):
            # try to simplify conditions and the expression for
            # equalities that are part of the condition, e.g.
            # Piecewise((n, And(Eq(n,0), Eq(n + m, 0))), (1, True))
            # -> Piecewise((0, And(Eq(n, 0), Eq(m, 0))), (1, True))
            if isinstance(cond, And):
                eqs, other = sift(cond.args,
                    lambda i: isinstance(i, Equality), binary=True)
            elif isinstance(cond, Equality):
                eqs, other = [cond], []
            else:
                eqs = other = []
            if eqs:
                eqs = list(ordered(eqs))
                for j, e in enumerate(eqs):
                    # these blessed lhs objects behave like Symbols
                    # and the rhs are simple replacements for the "symbols"
                    if _blessed(e):
                        expr = expr.subs(*e.args)
                        eqs[j + 1:] = [ei.subs(*e.args) for ei in eqs[j + 1:]]
                        other = [ei.subs(*e.args) for ei in other]
                cond = And(*(eqs + other))
                args[i] = args[i].func(expr, cond)
        # See if expressions valid for an Equal expression happens to evaluate
        # to the same function as in the next piecewise segment, see:
        # https://github.com/sympy/sympy/issues/8458
        prevexpr = None
        for i, (expr, cond) in reversed(list(enumerate(args))):
            if prevexpr is not None:
                if isinstance(cond, And):
                    eqs, other = sift(cond.args,
                        lambda i: isinstance(i, Equality), binary=True)
                elif isinstance(cond, Equality):
                    eqs, other = [cond], []
                else:
                    eqs = other = []
                _prevexpr = prevexpr
                _expr = expr
                if eqs and not other:
                    eqs = list(ordered(eqs))
                    for e in eqs:
                        # these blessed lhs objects behave like Symbols
                        # and the rhs are simple replacements for the "symbols"
                        if _blessed(e):
                            _prevexpr = _prevexpr.subs(*e.args)
                            _expr = _expr.subs(*e.args)
                # Did it evaluate to the same?
                if _prevexpr == _expr:
                    # Set the expression for the Not equal section to the same
                    # as the next. These will be merged when creating the new
                    # Piecewise
                    args[i] = args[i].func(args[i+1][0], cond)
                else:
                    # Update the expression that we compare against
                    prevexpr = expr
            else:
                prevexpr = expr
        return self.func(*args)

    def _eval_as_leading_term(self, x):
        for e, c in self.args:
            if c == True or c.subs(x, 0) == True:
                return e.as_leading_term(x)

    def _eval_adjoint(self):
        return self.func(*[(e.adjoint(), c) for e, c in self.args])

    def _eval_conjugate(self):
        return self.func(*[(e.conjugate(), c) for e, c in self.args])

    def _eval_derivative(self, x):
        return self.func(*[(diff(e, x), c) for e, c in self.args])

    def _eval_evalf(self, prec):
        return self.func(*[(e._evalf(prec), c) for e, c in self.args])

    def piecewise_integrate(self, x, **kwargs):
        """Return the Piecewise with each expression being
        replaced with its antiderivative. To obtain a continuous
        antiderivative, use the `integrate` function or method.

        Examples
        ========

        >>> from sympy import Piecewise
        >>> from sympy.abc import x
        >>> p = Piecewise((0, x < 0), (1, x < 1), (2, True))
        >>> p.piecewise_integrate(x)
        Piecewise((0, x < 0), (x, x < 1), (2*x, True))

        Note that this does not give a continuous function, e.g.
        at x = 1 the 3rd condition applies and the antiderivative
        there is 2*x so the value of the antiderivative is 2:

        >>> anti = _
        >>> anti.subs(x, 1)
        2

        The continuous derivative accounts for the integral *up to*
        the point of interest, however:

        >>> p.integrate(x)
        Piecewise((0, x < 0), (x, x < 1), (2*x - 1, True))
        >>> _.subs(x, 1)
        1

        See Also
        ========
        Piecewise._eval_integral
        """
        from sympy.integrals import integrate
        return self.func(*[(integrate(e, x, **kwargs), c) for e, c in self.args])

    def _handle_irel(self, x, handler):
        """Return either None (if the conditions of self depend only on x) else
        a Piecewise expression whose expressions (handled by the handler that
        was passed) are paired with the governing x-independent relationals,
        e.g. Piecewise((A, a(x) & b(y)), (B, c(x) | c(y)) ->
        Piecewise(
            (handler(Piecewise((A, a(x) & True), (B, c(x) | True)), b(y) & c(y)),
            (handler(Piecewise((A, a(x) & True), (B, c(x) | False)), b(y)),
            (handler(Piecewise((A, a(x) & False), (B, c(x) | True)), c(y)),
            (handler(Piecewise((A, a(x) & False), (B, c(x) | False)), True))
        """
        # identify governing relationals
        rel = self.atoms(Relational)
        irel = list(ordered([r for r in rel if x not in r.free_symbols
            and r not in (S.true, S.false)]))
        if irel:
            args = {}
            exprinorder = []
            for truth in product((1, 0), repeat=len(irel)):
                reps = dict(zip(irel, truth))
                # only store the true conditions since the false are implied
                # when they appear lower in the Piecewise args
                if 1 not in truth:
                    cond = None  # flag this one so it doesn't get combined
                else:
                    andargs = Tuple(*[i for i in reps if reps[i]])
                    free = list(andargs.free_symbols)
                    if len(free) == 1:
                        from sympy.solvers.inequalities import (
                            reduce_inequalities, _solve_inequality)
                        try:
                            t = reduce_inequalities(andargs, free[0])
                            # ValueError when there are potentially
                            # nonvanishing imaginary parts
                        except (ValueError, NotImplementedError):
                            # at least isolate free symbol on left
                            t = And(*[_solve_inequality(
                                a, free[0], linear=True)
                                for a in andargs])
                    else:
                        t = And(*andargs)
                    if t is S.false:
                        continue  # an impossible combination
                    cond = t
                expr = handler(self.xreplace(reps))
                if isinstance(expr, self.func) and len(expr.args) == 1:
                    expr, econd = expr.args[0]
                    cond = And(econd, True if cond is None else cond)
                # the ec pairs are being collected since all possibilities
                # are being enumerated, but don't put the last one in since
                # its expr might match a previous expression and it
                # must appear last in the args
                if cond is not None:
                    args.setdefault(expr, []).append(cond)
                    # but since we only store the true conditions we must maintain
                    # the order so that the expression with the most true values
                    # comes first
                    exprinorder.append(expr)
            # convert collected conditions as args of Or
            for k in args:
                args[k] = Or(*args[k])
            # take them in the order obtained
            args = [(e, args[e]) for e in uniq(exprinorder)]
            # add in the last arg
            args.append((expr, True))
            # if any condition reduced to True, it needs to go last
            # and there should only be one of them or else the exprs
            # should agree
            trues = [i for i in range(len(args)) if args[i][1] is S.true]
            if not trues:
                # make the last one True since all cases were enumerated
                e, c = args[-1]
                args[-1] = (e, S.true)
            else:
                assert len(set([e for e, c in [args[i] for i in trues]])) == 1
                args.append(args.pop(trues.pop()))
                while trues:
                    args.pop(trues.pop())
            return Piecewise(*args)

    def _eval_integral(self, x, _first=True, **kwargs):
        """Return the indefinite integral of the
        Piecewise such that subsequent substitution of x with a
        value will give the value of the integral (not including
        the constant of integration) up to that point. To only
        integrate the individual parts of Piecewise, use the
        `piecewise_integrate` method.

        Examples
        ========

        >>> from sympy import Piecewise
        >>> from sympy.abc import x
        >>> p = Piecewise((0, x < 0), (1, x < 1), (2, True))
        >>> p.integrate(x)
        Piecewise((0, x < 0), (x, x < 1), (2*x - 1, True))
        >>> p.piecewise_integrate(x)
        Piecewise((0, x < 0), (x, x < 1), (2*x, True))

        See Also
        ========
        Piecewise.piecewise_integrate
        """
        from sympy.integrals.integrals import integrate

        if _first:
            def handler(ipw):
                if isinstance(ipw, self.func):
                    return ipw._eval_integral(x, _first=False, **kwargs)
                else:
                    return ipw.integrate(x, **kwargs)
            irv = self._handle_irel(x, handler)
            if irv is not None:
                return irv

        # handle a Piecewise from -oo to oo with and no x-independent relationals
        # -----------------------------------------------------------------------
        try:
            abei = self._intervals(x)
        except NotImplementedError:
            from sympy import Integral
            return Integral(self, x)  # unevaluated

        pieces = [(a, b) for a, b, _, _ in abei]
        oo = S.Infinity
        done = [(-oo, oo, -1)]
        for k, p in enumerate(pieces):
            if p == (-oo, oo):
                # all undone intervals will get this key
                for j, (a, b, i) in enumerate(done):
                    if i == -1:
                        done[j] = a, b, k
                break  # nothing else to consider
            N = len(done) - 1
            for j, (a, b, i) in enumerate(reversed(done)):
                if i == -1:
                    j = N - j
                    done[j: j + 1] = _clip(p, (a, b), k)
        done = [(a, b, i) for a, b, i in done if a != b]

        # append an arg if there is a hole so a reference to
        # argument -1 will give Undefined
        if any(i == -1 for (a, b, i) in done):
            abei.append((-oo, oo, Undefined, -1))

        # return the sum of the intervals
        args = []
        sum = None
        for a, b, i in done:
            anti = integrate(abei[i][-2], x, **kwargs)
            if sum is None:
                sum = anti
            else:
                sum = sum.subs(x, a)
                if sum == Undefined:
                    sum = 0
                sum += anti._eval_interval(x, a, x)
            # see if we know whether b is contained in original
            # condition
            if b is S.Infinity:
                cond = True
            elif self.args[abei[i][-1]].cond.subs(x, b) == False:
                cond = (x < b)
            else:
                cond = (x <= b)
            args.append((sum, cond))
        return Piecewise(*args)

    def _eval_interval(self, sym, a, b, _first=True):
        """Evaluates the function along the sym in a given interval [a, b]"""
        # FIXME: Currently complex intervals are not supported.  A possible
        # replacement algorithm, discussed in issue 5227, can be found in the
        # following papers;
        #     http://portal.acm.org/citation.cfm?id=281649
        #     http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.70.4127&rep=rep1&type=pdf
        from sympy.core.symbol import Dummy

        if a is None or b is None:
            # In this case, it is just simple substitution
            return super(Piecewise, self)._eval_interval(sym, a, b)
        else:
            x, lo, hi = map(as_Basic, (sym, a, b))

        if _first:  # get only x-dependent relationals
            def handler(ipw):
                if isinstance(ipw, self.func):
                    return ipw._eval_interval(x, lo, hi, _first=None)
                else:
                    return ipw._eval_interval(x, lo, hi)
            irv = self._handle_irel(x, handler)
            if irv is not None:
                return irv

            if (lo < hi) is S.false or (
                    lo is S.Infinity or hi is S.NegativeInfinity):
                rv = self._eval_interval(x, hi, lo, _first=False)
                if isinstance(rv, Piecewise):
                    rv = Piecewise(*[(-e, c) for e, c in rv.args])
                else:
                    rv = -rv
                return rv

            if (lo < hi) is S.true or (
                    hi is S.Infinity or lo is S.NegativeInfinity):
                pass
            else:
                _a = Dummy('lo')
                _b = Dummy('hi')
                a = lo if lo.is_comparable else _a
                b = hi if hi.is_comparable else _b
                pos = self._eval_interval(x, a, b, _first=False)
                if a == _a and b == _b:
                    # it's purely symbolic so just swap lo and hi and
                    # change the sign to get the value for when lo > hi
                    neg, pos = (-pos.xreplace({_a: hi, _b: lo}),
                        pos.xreplace({_a: lo, _b: hi}))
                else:
                    # at least one of the bounds was comparable, so allow
                    # _eval_interval to use that information when computing
                    # the interval with lo and hi reversed
                    neg, pos = (-self._eval_interval(x, hi, lo, _first=False),
                        pos.xreplace({_a: lo, _b: hi}))

                # allow simplification based on ordering of lo and hi
                p = Dummy('', positive=True)
                if lo.is_Symbol:
                    pos = pos.xreplace({lo: hi - p}).xreplace({p: hi - lo})
                    neg = neg.xreplace({lo: hi + p}).xreplace({p: lo - hi})
                elif hi.is_Symbol:
                    pos = pos.xreplace({hi: lo + p}).xreplace({p: hi - lo})
                    neg = neg.xreplace({hi: lo - p}).xreplace({p: lo - hi})

                # assemble return expression; make the first condition be Lt
                # b/c then the first expression will look the same whether
                # the lo or hi limit is symbolic
                if a == _a:  # the lower limit was symbolic
                    rv = Piecewise(
                        (pos,
                            lo < hi),
                        (neg,
                            True))
                else:
                    rv = Piecewise(
                        (neg,
                            hi < lo),
                        (pos,
                            True))

                if rv == Undefined:
                    raise ValueError("Can't integrate across undefined region.")
                if any(isinstance(i, Piecewise) for i in (pos, neg)):
                    rv = piecewise_fold(rv)
                return rv

        # handle a Piecewise with lo <= hi and no x-independent relationals
        # -----------------------------------------------------------------
        try:
            abei = self._intervals(x)
        except NotImplementedError:
            from sympy import Integral
            # not being able to do the interval of f(x) can
            # be stated as not being able to do the integral
            # of f'(x) over the same range
            return Integral(self.diff(x), (x, lo, hi))  # unevaluated

        pieces = [(a, b) for a, b, _, _ in abei]
        done = [(lo, hi, -1)]
        oo = S.Infinity
        for k, p in enumerate(pieces):
            if p[:2] == (-oo, oo):
                # all undone intervals will get this key
                for j, (a, b, i) in enumerate(done):
                    if i == -1:
                        done[j] = a, b, k
                break  # nothing else to consider
            N = len(done) - 1
            for j, (a, b, i) in enumerate(reversed(done)):
                if i == -1:
                    j = N - j
                    done[j: j + 1] = _clip(p, (a, b), k)
        done = [(a, b, i) for a, b, i in done if a != b]

        # return the sum of the intervals
        sum = S.Zero
        upto = None
        for a, b, i in done:
            if i == -1:
                if upto is None:
                    return Undefined
                # TODO simplify hi <= upto
                return Piecewise((sum, hi <= upto), (Undefined, True))
            sum += abei[i][-2]._eval_interval(x, a, b)
            upto = b
        return sum

    def _intervals(self, sym):
        """Return a list of unique tuples, (a, b, e, i), where a and b
        are the lower and upper bounds in which the expression e of
        argument i in self is defined and a < b (when involving
        numbers) or a <= b when involving symbols.

        If there are any relationals not involving sym, or any
        relational cannot be solved for sym, NotImplementedError is
        raised. The calling routine should have removed such
        relationals before calling this routine.

        The evaluated conditions will be returned as ranges.
        Discontinuous ranges will be returned separately with
        identical expressions. The first condition that evaluates to
        True will be returned as the last tuple with a, b = -oo, oo.
        """
        from sympy.solvers.inequalities import _solve_inequality
        from sympy.logic.boolalg import to_cnf, distribute_or_over_and

        assert isinstance(self, Piecewise)

        def _solve_relational(r):
            if sym not in r.free_symbols:
                nonsymfail(r)
            rv = _solve_inequality(r, sym)
            if isinstance(rv, Relational):
                free = rv.args[1].free_symbols
                if rv.args[0] != sym or sym in free:
                    raise NotImplementedError(filldedent('''
                        Unable to solve relational
                        %s for %s.''' % (r, sym)))
                if rv.rel_op == '==':
                    # this equality has been affirmed to have the form
                    # Eq(sym, rhs) where rhs is sym-free; it represents
                    # a zero-width interval which will be ignored
                    # whether it is an isolated condition or contained
                    # within an And or an Or
                    rv = S.false
                elif rv.rel_op == '!=':
                    try:
                        rv = Or(sym < rv.rhs, sym > rv.rhs)
                    except TypeError:
                        # e.g. x != I ==> all real x satisfy
                        rv = S.true
            elif rv == (S.NegativeInfinity < sym) & (sym < S.Infinity):
                rv = S.true
            return rv

        def nonsymfail(cond):
            raise NotImplementedError(filldedent('''
                A condition not involving
                %s appeared: %s''' % (sym, cond)))

        # make self canonical wrt Relationals
        reps = dict([
            (r, _solve_relational(r)) for r in self.atoms(Relational)])
        # process args individually so if any evaluate, their position
        # in the original Piecewise will be known
        args = [i.xreplace(reps) for i in self.args]

        # precondition args
        expr_cond = []
        default = idefault = None
        for i, (expr, cond) in enumerate(args):
            if cond is S.false:
                continue
            elif cond is S.true:
                default = expr
                idefault = i
                break

            cond = to_cnf(cond)
            if isinstance(cond, And):
                cond = distribute_or_over_and(cond)

            if isinstance(cond, Or):
                expr_cond.extend(
                    [(i, expr, o) for o in cond.args
                    if not isinstance(o, Equality)])
            elif cond is not S.false:
                expr_cond.append((i, expr, cond))

        # determine intervals represented by conditions
        int_expr = []
        for iarg, expr, cond in expr_cond:
            if isinstance(cond, And):
                lower = S.NegativeInfinity
                upper = S.Infinity
                for cond2 in cond.args:
                    if isinstance(cond2, Equality):
                        lower = upper  # ignore
                        break
                    elif cond2.lts == sym:
                        upper = Min(cond2.gts, upper)
                    elif cond2.gts == sym:
                        lower = Max(cond2.lts, lower)
                    else:
                        nonsymfail(cond2)  # should never get here
            elif isinstance(cond, Relational):
                lower, upper = cond.lts, cond.gts  # part 1: initialize with givens
                if cond.lts == sym:                # part 1a: expand the side ...
                    lower = S.NegativeInfinity   # e.g. x <= 0 ---> -oo <= 0
                elif cond.gts == sym:            # part 1a: ... that can be expanded
                    upper = S.Infinity           # e.g. x >= 0 --->  oo >= 0
                else:
                    nonsymfail(cond)
            else:
                raise NotImplementedError(
                    'unrecognized condition: %s' % cond)

            lower, upper = lower, Max(lower, upper)
            if (lower >= upper) is not S.true:
                int_expr.append((lower, upper, expr, iarg))

        if default is not None:
            int_expr.append(
                (S.NegativeInfinity, S.Infinity, default, idefault))

        return list(uniq(int_expr))

    def _eval_nseries(self, x, n, logx):
        args = [(ec.expr._eval_nseries(x, n, logx), ec.cond) for ec in self.args]
        return self.func(*args)

    def _eval_power(self, s):
        return self.func(*[(e**s, c) for e, c in self.args])

    def _eval_subs(self, old, new):
        # this is strictly not necessary, but we can keep track
        # of whether True or False conditions arise and be
        # somewhat more efficient by avoiding other substitutions
        # and avoiding invalid conditions that appear after a
        # True condition
        args = list(self.args)
        args_exist = False
        for i, (e, c) in enumerate(args):
            c = c._subs(old, new)
            if c != False:
                args_exist = True
                e = e._subs(old, new)
            args[i] = (e, c)
            if c == True:
                break
        if not args_exist:
            args = ((Undefined, True),)
        return self.func(*args)

    def _eval_transpose(self):
        return self.func(*[(e.transpose(), c) for e, c in self.args])

    def _eval_template_is_attr(self, is_attr):
        b = None
        for expr, _ in self.args:
            a = getattr(expr, is_attr)
            if a is None:
                return
            if b is None:
                b = a
            elif b is not a:
                return
        return b

    _eval_is_finite = lambda self: self._eval_template_is_attr(
        'is_finite')
    _eval_is_complex = lambda self: self._eval_template_is_attr('is_complex')
    _eval_is_even = lambda self: self._eval_template_is_attr('is_even')
    _eval_is_imaginary = lambda self: self._eval_template_is_attr(
        'is_imaginary')
    _eval_is_integer = lambda self: self._eval_template_is_attr('is_integer')
    _eval_is_irrational = lambda self: self._eval_template_is_attr(
        'is_irrational')
    _eval_is_negative = lambda self: self._eval_template_is_attr('is_negative')
    _eval_is_nonnegative = lambda self: self._eval_template_is_attr(
        'is_nonnegative')
    _eval_is_nonpositive = lambda self: self._eval_template_is_attr(
        'is_nonpositive')
    _eval_is_nonzero = lambda self: self._eval_template_is_attr(
        'is_nonzero')
    _eval_is_odd = lambda self: self._eval_template_is_attr('is_odd')
    _eval_is_polar = lambda self: self._eval_template_is_attr('is_polar')
    _eval_is_positive = lambda self: self._eval_template_is_attr('is_positive')
    _eval_is_real = lambda self: self._eval_template_is_attr('is_real')
    _eval_is_zero = lambda self: self._eval_template_is_attr(
        'is_zero')

    @classmethod
    def __eval_cond(cls, cond):
        """Return the truth value of the condition."""
        if cond == True:
            return True
        if isinstance(cond, Equality):
            try:
                diff = cond.lhs - cond.rhs
                if diff.is_commutative:
                    return diff.is_zero
            except TypeError:
                pass

    def as_expr_set_pairs(self, domain=S.Reals):
        """Return tuples for each argument of self that give
        the expression and the interval in which it is valid
        which is contained within the given domain.
        If a condition cannot be converted to a set, an error
        will be raised. The variable of the conditions is
        assumed to be real; sets of real values are returned.

        Examples
        ========

        >>> from sympy import Piecewise, Interval
        >>> from sympy.abc import x
        >>> p = Piecewise(
        ...     (1, x < 2),
        ...     (2,(x > 0) & (x < 4)),
        ...     (3, True))
        >>> p.as_expr_set_pairs()
        [(1, Interval.open(-oo, 2)),
         (2, Interval.Ropen(2, 4)),
         (3, Interval(4, oo))]
        >>> p.as_expr_set_pairs(Interval(0, 3))
        [(1, Interval.Ropen(0, 2)),
         (2, Interval(2, 3)), (3, EmptySet())]
        """
        exp_sets = []
        U = domain
        complex = not domain.is_subset(S.Reals)
        for expr, cond in self.args:
            if complex:
                for i in cond.atoms(Relational):
                    if not isinstance(i, (Equality, Unequality)):
                        raise ValueError(filldedent('''
                            Inequalities in the complex domain are
                            not supported. Try the real domain by
                            setting domain=S.Reals'''))
            cond_int = U.intersect(cond.as_set())
            U = U - cond_int
            exp_sets.append((expr, cond_int))
        return exp_sets

    def _eval_rewrite_as_ITE(self, *args, **kwargs):
        byfree = {}
        args = list(args)
        default = any(c == True for b, c in args)
        for i, (b, c) in enumerate(args):
            if not isinstance(b, Boolean) and b != True:
                raise TypeError(filldedent('''
                    Expecting Boolean or bool but got `%s`
                    ''' % func_name(b)))
            if c == True:
                break
            # loop over independent conditions for this b
            for c in c.args if isinstance(c, Or) else [c]:
                free = c.free_symbols
                x = free.pop()
                try:
                    byfree[x] = byfree.setdefault(
                        x, S.EmptySet).union(c.as_set())
                except NotImplementedError:
                    if not default:
                        raise NotImplementedError(filldedent('''
                            A method to determine whether a multivariate
                            conditional is consistent with a complete coverage
                            of all variables has not been implemented so the
                            rewrite is being stopped after encountering `%s`.
                            This error would not occur if a default expression
                            like `(foo, True)` were given.
                            ''' % c))
                if byfree[x] in (S.UniversalSet, S.Reals):
                    # collapse the ith condition to True and break
                    args[i] = list(args[i])
                    c = args[i][1] = True
                    break
            if c == True:
                break
        if c != True:
            raise ValueError(filldedent('''
                Conditions must cover all reals or a final default
                condition `(foo, True)` must be given.
                '''))
        last, _ = args[i]  # ignore all past ith arg
        for a, c in reversed(args[:i]):
            last = ITE(c, a, last)
        return _canonical(last)


def piecewise_fold(expr):
    """
    Takes an expression containing a piecewise function and returns the
    expression in piecewise form. In addition, any ITE conditions are
    rewritten in negation normal form and simplified.

    Examples
    ========

    >>> from sympy import Piecewise, piecewise_fold, sympify as S
    >>> from sympy.abc import x
    >>> p = Piecewise((x, x < 1), (1, S(1) <= x))
    >>> piecewise_fold(x*p)
    Piecewise((x**2, x < 1), (x, True))

    See Also
    ========

    Piecewise
    """
    if not isinstance(expr, Basic) or not expr.has(Piecewise):
        return expr

    new_args = []
    if isinstance(expr, (ExprCondPair, Piecewise)):
        for e, c in expr.args:
            if not isinstance(e, Piecewise):
                e = piecewise_fold(e)
            # we don't keep Piecewise in condition because
            # it has to be checked to see that it's complete
            # and we convert it to ITE at that time
            assert not c.has(Piecewise)  # pragma: no cover
            if isinstance(c, ITE):
                c = c.to_nnf()
                c = simplify_logic(c, form='cnf')
            if isinstance(e, Piecewise):
                new_args.extend([(piecewise_fold(ei), And(ci, c))
                    for ei, ci in e.args])
            else:
                new_args.append((e, c))
    else:
        from sympy.utilities.iterables import cartes, sift, common_prefix
        # Given
        #     P1 = Piecewise((e11, c1), (e12, c2), A)
        #     P2 = Piecewise((e21, c1), (e22, c2), B)
        #     ...
        # the folding of f(P1, P2) is trivially
        # Piecewise(
        #   (f(e11, e21), c1),
        #   (f(e12, e22), c2),
        #   (f(Piecewise(A), Piecewise(B)), True))
        # Certain objects end up rewriting themselves as thus, so
        # we do that grouping before the more generic folding.
        # The following applies this idea when f = Add or f = Mul
        # (and the expression is commutative).
        if expr.is_Add or expr.is_Mul and expr.is_commutative:
            p, args = sift(expr.args, lambda x: x.is_Piecewise, binary=True)
            pc = sift(p, lambda x: tuple([c for e,c in x.args]))
            for c in list(ordered(pc)):
                if len(pc[c]) > 1:
                    pargs = [list(i.args) for i in pc[c]]
                    # the first one is the same; there may be more
                    com = common_prefix(*[
                        [i.cond for i in j] for j in pargs])
                    n = len(com)
                    collected = []
                    for i in range(n):
                        collected.append((
                            expr.func(*[ai[i].expr for ai in pargs]),
                            com[i]))
                    remains = []
                    for a in pargs:
                        if n == len(a):  # no more args
                            continue
                        if a[n].cond == True:  # no longer Piecewise
                            remains.append(a[n].expr)
                        else:  # restore the remaining Piecewise
                            remains.append(
                                Piecewise(*a[n:], evaluate=False))
                    if remains:
                        collected.append((expr.func(*remains), True))
                    args.append(Piecewise(*collected, evaluate=False))
                    continue
                args.extend(pc[c])
        else:
            args = expr.args
        # fold
        folded = list(map(piecewise_fold, args))
        for ec in cartes(*[
                (i.args if isinstance(i, Piecewise) else
                 [(i, true)]) for i in folded]):
            e, c = zip(*ec)
            new_args.append((expr.func(*e), And(*c)))

    return Piecewise(*new_args)


def _clip(A, B, k):
    """Return interval B as intervals that are covered by A (keyed
    to k) and all other intervals of B not covered by A keyed to -1.

    The reference point of each interval is the rhs; if the lhs is
    greater than the rhs then an interval of zero width interval will
    result, e.g. (4, 1) is treated like (1, 1).

    Examples
    ========

    >>> from sympy.functions.elementary.piecewise import _clip
    >>> from sympy import Tuple
    >>> A = Tuple(1, 3)
    >>> B = Tuple(2, 4)
    >>> _clip(A, B, 0)
    [(2, 3, 0), (3, 4, -1)]

    Interpretation: interval portion (2, 3) of interval (2, 4) is
    covered by interval (1, 3) and is keyed to 0 as requested;
    interval (3, 4) was not covered by (1, 3) and is keyed to -1.
    """
    a, b = B
    c, d = A
    c, d = Min(Max(c, a), b), Min(Max(d, a), b)
    a, b = Min(a, b), b
    p = []
    if a != c:
        p.append((a, c, -1))
    else:
        pass
    if c != d:
        p.append((c, d, k))
    else:
        pass
    if b != d:
        if d == c and p and p[-1][-1] == -1:
            p[-1] = p[-1][0], b, -1
        else:
            p.append((d, b, -1))
    else:
        pass

    return p
