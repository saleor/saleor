from __future__ import print_function, division

from sympy.core.sympify import _sympify, sympify
from sympy.core.basic import Basic
from sympy.core.cache import cacheit
from sympy.core.compatibility import ordered, range
from sympy.core.logic import fuzzy_and
from sympy.core.evaluate import global_evaluate
from sympy.utilities.iterables import sift


class AssocOp(Basic):
    """ Associative operations, can separate noncommutative and
    commutative parts.

    (a op b) op c == a op (b op c) == a op b op c.

    Base class for Add and Mul.

    This is an abstract base class, concrete derived classes must define
    the attribute `identity`.
    """

    # for performance reason, we don't let is_commutative go to assumptions,
    # and keep it right here
    __slots__ = ['is_commutative']

    @cacheit
    def __new__(cls, *args, **options):
        from sympy import Order
        args = list(map(_sympify, args))
        args = [a for a in args if a is not cls.identity]

        evaluate = options.get('evaluate')
        if evaluate is None:
            evaluate = global_evaluate[0]
        if not evaluate:
            obj = cls._from_args(args)
            obj = cls._exec_constructor_postprocessors(obj)
            return obj

        if len(args) == 0:
            return cls.identity
        if len(args) == 1:
            return args[0]

        c_part, nc_part, order_symbols = cls.flatten(args)
        is_commutative = not nc_part
        obj = cls._from_args(c_part + nc_part, is_commutative)
        obj = cls._exec_constructor_postprocessors(obj)

        if order_symbols is not None:
            return Order(obj, *order_symbols)
        return obj

    @classmethod
    def _from_args(cls, args, is_commutative=None):
        """Create new instance with already-processed args"""
        if len(args) == 0:
            return cls.identity
        elif len(args) == 1:
            return args[0]

        obj = super(AssocOp, cls).__new__(cls, *args)
        if is_commutative is None:
            is_commutative = fuzzy_and(a.is_commutative for a in args)
        obj.is_commutative = is_commutative
        return obj

    def _new_rawargs(self, *args, **kwargs):
        """Create new instance of own class with args exactly as provided by
        caller but returning the self class identity if args is empty.

           This is handy when we want to optimize things, e.g.

               >>> from sympy import Mul, S
               >>> from sympy.abc import x, y
               >>> e = Mul(3, x, y)
               >>> e.args
               (3, x, y)
               >>> Mul(*e.args[1:])
               x*y
               >>> e._new_rawargs(*e.args[1:])  # the same as above, but faster
               x*y

           Note: use this with caution. There is no checking of arguments at
           all. This is best used when you are rebuilding an Add or Mul after
           simply removing one or more args. If, for example, modifications,
           result in extra 1s being inserted (as when collecting an
           expression's numerators and denominators) they will not show up in
           the result but a Mul will be returned nonetheless:

               >>> m = (x*y)._new_rawargs(S.One, x); m
               x
               >>> m == x
               False
               >>> m.is_Mul
               True

           Another issue to be aware of is that the commutativity of the result
           is based on the commutativity of self. If you are rebuilding the
           terms that came from a commutative object then there will be no
           problem, but if self was non-commutative then what you are
           rebuilding may now be commutative.

           Although this routine tries to do as little as possible with the
           input, getting the commutativity right is important, so this level
           of safety is enforced: commutativity will always be recomputed if
           self is non-commutative and kwarg `reeval=False` has not been
           passed.
        """
        if kwargs.pop('reeval', True) and self.is_commutative is False:
            is_commutative = None
        else:
            is_commutative = self.is_commutative
        return self._from_args(args, is_commutative)

    @classmethod
    def flatten(cls, seq):
        """Return seq so that none of the elements are of type `cls`. This is
        the vanilla routine that will be used if a class derived from AssocOp
        does not define its own flatten routine."""
        # apply associativity, no commutativity property is used
        new_seq = []
        while seq:
            o = seq.pop()
            if o.__class__ is cls:  # classes must match exactly
                seq.extend(o.args)
            else:
                new_seq.append(o)
        # c_part, nc_part, order_symbols
        return [], new_seq, None

    def _matches_commutative(self, expr, repl_dict={}, old=False):
        """
        Matches Add/Mul "pattern" to an expression "expr".

        repl_dict ... a dictionary of (wild: expression) pairs, that get
                      returned with the results

        This function is the main workhorse for Add/Mul.

        For instance:

        >>> from sympy import symbols, Wild, sin
        >>> a = Wild("a")
        >>> b = Wild("b")
        >>> c = Wild("c")
        >>> x, y, z = symbols("x y z")
        >>> (a+sin(b)*c)._matches_commutative(x+sin(y)*z)
        {a_: x, b_: y, c_: z}

        In the example above, "a+sin(b)*c" is the pattern, and "x+sin(y)*z" is
        the expression.

        The repl_dict contains parts that were already matched. For example
        here:

        >>> (x+sin(b)*c)._matches_commutative(x+sin(y)*z, repl_dict={a: x})
        {a_: x, b_: y, c_: z}

        the only function of the repl_dict is to return it in the
        result, e.g. if you omit it:

        >>> (x+sin(b)*c)._matches_commutative(x+sin(y)*z)
        {b_: y, c_: z}

        the "a: x" is not returned in the result, but otherwise it is
        equivalent.

        """
        # make sure expr is Expr if pattern is Expr
        from .expr import Add, Expr
        from sympy import Mul
        if isinstance(self, Expr) and not isinstance(expr, Expr):
            return None

        # handle simple patterns
        if self == expr:
            return repl_dict

        d = self._matches_simple(expr, repl_dict)
        if d is not None:
            return d

        # eliminate exact part from pattern: (2+a+w1+w2).matches(expr) -> (w1+w2).matches(expr-a-2)
        from .function import WildFunction
        from .symbol import Wild
        wild_part, exact_part = sift(self.args, lambda p:
            p.has(Wild, WildFunction) and not expr.has(p),
            binary=True)
        if not exact_part:
            wild_part = list(ordered(wild_part))
        else:
            exact = self._new_rawargs(*exact_part)
            free = expr.free_symbols
            if free and (exact.free_symbols - free):
                # there are symbols in the exact part that are not
                # in the expr; but if there are no free symbols, let
                # the matching continue
                return None
            newexpr = self._combine_inverse(expr, exact)
            if not old and (expr.is_Add or expr.is_Mul):
                if newexpr.count_ops() > expr.count_ops():
                    return None
            newpattern = self._new_rawargs(*wild_part)
            return newpattern.matches(newexpr, repl_dict)

        # now to real work ;)
        i = 0
        saw = set()
        while expr not in saw:
            saw.add(expr)
            expr_list = (self.identity,) + tuple(ordered(self.make_args(expr)))
            for last_op in reversed(expr_list):
                for w in reversed(wild_part):
                    d1 = w.matches(last_op, repl_dict)
                    if d1 is not None:
                        d2 = self.xreplace(d1).matches(expr, d1)
                        if d2 is not None:
                            return d2

            if i == 0:
                if self.is_Mul:
                    # make e**i look like Mul
                    if expr.is_Pow and expr.exp.is_Integer:
                        if expr.exp > 0:
                            expr = Mul(*[expr.base, expr.base**(expr.exp - 1)], evaluate=False)
                        else:
                            expr = Mul(*[1/expr.base, expr.base**(expr.exp + 1)], evaluate=False)
                        i += 1
                        continue

                elif self.is_Add:
                    # make i*e look like Add
                    c, e = expr.as_coeff_Mul()
                    if abs(c) > 1:
                        if c > 0:
                            expr = Add(*[e, (c - 1)*e], evaluate=False)
                        else:
                            expr = Add(*[-e, (c + 1)*e], evaluate=False)
                        i += 1
                        continue

                    # try collection on non-Wild symbols
                    from sympy.simplify.radsimp import collect
                    was = expr
                    did = set()
                    for w in reversed(wild_part):
                        c, w = w.as_coeff_mul(Wild)
                        free = c.free_symbols - did
                        if free:
                            did.update(free)
                            expr = collect(expr, free)
                    if expr != was:
                        i += 0
                        continue

                break  # if we didn't continue, there is nothing more to do

        return

    def _has_matcher(self):
        """Helper for .has()"""
        def _ncsplit(expr):
            # this is not the same as args_cnc because here
            # we don't assume expr is a Mul -- hence deal with args --
            # and always return a set.
            cpart, ncpart = sift(expr.args,
                lambda arg: arg.is_commutative is True, binary=True)
            return set(cpart), ncpart

        c, nc = _ncsplit(self)
        cls = self.__class__

        def is_in(expr):
            if expr == self:
                return True
            elif not isinstance(expr, Basic):
                return False
            elif isinstance(expr, cls):
                _c, _nc = _ncsplit(expr)
                if (c & _c) == c:
                    if not nc:
                        return True
                    elif len(nc) <= len(_nc):
                        for i in range(len(_nc) - len(nc) + 1):
                            if _nc[i:i + len(nc)] == nc:
                                return True
            return False
        return is_in

    def _eval_evalf(self, prec):
        """
        Evaluate the parts of self that are numbers; if the whole thing
        was a number with no functions it would have been evaluated, but
        it wasn't so we must judiciously extract the numbers and reconstruct
        the object. This is *not* simply replacing numbers with evaluated
        numbers. Nunmbers should be handled in the largest pure-number
        expression as possible. So the code below separates ``self`` into
        number and non-number parts and evaluates the number parts and
        walks the args of the non-number part recursively (doing the same
        thing).
        """
        from .add import Add
        from .mul import Mul
        from .symbol import Symbol
        from .function import AppliedUndef
        if isinstance(self, (Mul, Add)):
            x, tail = self.as_independent(Symbol, AppliedUndef)
            # if x is an AssocOp Function then the _evalf below will
            # call _eval_evalf (here) so we must break the recursion
            if not (tail is self.identity or
                    isinstance(x, AssocOp) and x.is_Function or
                    x is self.identity and isinstance(tail, AssocOp)):
                # here, we have a number so we just call to _evalf with prec;
                # prec is not the same as n, it is the binary precision so
                # that's why we don't call to evalf.
                x = x._evalf(prec) if x is not self.identity else self.identity
                args = []
                tail_args = tuple(self.func.make_args(tail))
                for a in tail_args:
                    # here we call to _eval_evalf since we don't know what we
                    # are dealing with and all other _eval_evalf routines should
                    # be doing the same thing (i.e. taking binary prec and
                    # finding the evalf-able args)
                    newa = a._eval_evalf(prec)
                    if newa is None:
                        args.append(a)
                    else:
                        args.append(newa)
                return self.func(x, *args)

        # this is the same as above, but there were no pure-number args to
        # deal with
        args = []
        for a in self.args:
            newa = a._eval_evalf(prec)
            if newa is None:
                args.append(a)
            else:
                args.append(newa)
        return self.func(*args)

    @classmethod
    def make_args(cls, expr):
        """
        Return a sequence of elements `args` such that cls(*args) == expr

        >>> from sympy import Symbol, Mul, Add
        >>> x, y = map(Symbol, 'xy')

        >>> Mul.make_args(x*y)
        (x, y)
        >>> Add.make_args(x*y)
        (x*y,)
        >>> set(Add.make_args(x*y + y)) == set([y, x*y])
        True

        """
        if isinstance(expr, cls):
            return expr.args
        else:
            return (sympify(expr),)


class ShortCircuit(Exception):
    pass


class LatticeOp(AssocOp):
    """
    Join/meet operations of an algebraic lattice[1].

    These binary operations are associative (op(op(a, b), c) = op(a, op(b, c))),
    commutative (op(a, b) = op(b, a)) and idempotent (op(a, a) = op(a) = a).
    Common examples are AND, OR, Union, Intersection, max or min. They have an
    identity element (op(identity, a) = a) and an absorbing element
    conventionally called zero (op(zero, a) = zero).

    This is an abstract base class, concrete derived classes must declare
    attributes zero and identity. All defining properties are then respected.

    >>> from sympy import Integer
    >>> from sympy.core.operations import LatticeOp
    >>> class my_join(LatticeOp):
    ...     zero = Integer(0)
    ...     identity = Integer(1)
    >>> my_join(2, 3) == my_join(3, 2)
    True
    >>> my_join(2, my_join(3, 4)) == my_join(2, 3, 4)
    True
    >>> my_join(0, 1, 4, 2, 3, 4)
    0
    >>> my_join(1, 2)
    2

    References:

    [1] - https://en.wikipedia.org/wiki/Lattice_%28order%29
    """

    is_commutative = True

    def __new__(cls, *args, **options):
        args = (_sympify(arg) for arg in args)

        try:
            # /!\ args is a generator and _new_args_filter
            # must be careful to handle as such; this
            # is done so short-circuiting can be done
            # without having to sympify all values
            _args = frozenset(cls._new_args_filter(args))
        except ShortCircuit:
            return sympify(cls.zero)
        if not _args:
            return sympify(cls.identity)
        elif len(_args) == 1:
            return set(_args).pop()
        else:
            # XXX in almost every other case for __new__, *_args is
            # passed along, but the expectation here is for _args
            obj = super(AssocOp, cls).__new__(cls, _args)
            obj._argset = _args
            return obj

    @classmethod
    def _new_args_filter(cls, arg_sequence, call_cls=None):
        """Generator filtering args"""
        ncls = call_cls or cls
        for arg in arg_sequence:
            if arg == ncls.zero:
                raise ShortCircuit(arg)
            elif arg == ncls.identity:
                continue
            elif arg.func == ncls:
                for x in arg.args:
                    yield x
            else:
                yield arg

    @classmethod
    def make_args(cls, expr):
        """
        Return a set of args such that cls(*arg_set) == expr.
        """
        if isinstance(expr, cls):
            return expr._argset
        else:
            return frozenset([sympify(expr)])

    @property
    @cacheit
    def args(self):
        return tuple(ordered(self._argset))

    @staticmethod
    def _compare_pretty(a, b):
        return (str(a) > str(b)) - (str(a) < str(b))
