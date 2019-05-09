from __future__ import print_function, division

from sympy.core import S, sympify, diff
from sympy.core.decorators import deprecated
from sympy.core.function import Function, ArgumentIndexError
from sympy.core.logic import fuzzy_not
from sympy.core.relational import Eq
from sympy.functions.elementary.complexes import im, sign
from sympy.functions.elementary.piecewise import Piecewise
from sympy.polys.polyerrors import PolynomialError
from sympy.utilities import filldedent


###############################################################################
################################ DELTA FUNCTION ###############################
###############################################################################


class DiracDelta(Function):
    """
    The DiracDelta function and its derivatives.

    DiracDelta is not an ordinary function. It can be rigorously defined either
    as a distribution or as a measure.

    DiracDelta only makes sense in definite integrals, and in particular, integrals
    of the form ``Integral(f(x)*DiracDelta(x - x0), (x, a, b))``, where it equals
    ``f(x0)`` if ``a <= x0 <= b`` and ``0`` otherwise. Formally, DiracDelta acts
    in some ways like a function that is ``0`` everywhere except at ``0``,
    but in many ways it also does not. It can often be useful to treat DiracDelta
    in formal ways, building up and manipulating expressions with delta functions
    (which may eventually be integrated), but care must be taken to not treat it
    as a real function.
    SymPy's ``oo`` is similar. It only truly makes sense formally in certain contexts
    (such as integration limits), but SymPy allows its use everywhere, and it tries to be
    consistent with operations on it (like ``1/oo``), but it is easy to get into trouble
    and get wrong results if ``oo`` is treated too much like a number.
    Similarly, if DiracDelta is treated too much like a function, it is easy to get wrong
    or nonsensical results.

    DiracDelta function has the following properties:

    1) ``diff(Heaviside(x), x) = DiracDelta(x)``
    2) ``integrate(DiracDelta(x - a)*f(x),(x, -oo, oo)) = f(a)`` and
       ``integrate(DiracDelta(x - a)*f(x),(x, a - e, a + e)) = f(a)``
    3) ``DiracDelta(x) = 0`` for all ``x != 0``
    4) ``DiracDelta(g(x)) = Sum_i(DiracDelta(x - x_i)/abs(g'(x_i)))``
       Where ``x_i``-s are the roots of ``g``
    5) ``DiracDelta(-x) = DiracDelta(x)``

    Derivatives of ``k``-th order of DiracDelta have the following property:

    6) ``DiracDelta(x, k) = 0``, for all ``x != 0``
    7) ``DiracDelta(-x, k) = -DiracDelta(x, k)`` for odd ``k``
    8) ``DiracDelta(-x, k) = DiracDelta(x, k)`` for even ``k``

    Examples
    ========

    >>> from sympy import DiracDelta, diff, pi, Piecewise
    >>> from sympy.abc import x, y

    >>> DiracDelta(x)
    DiracDelta(x)
    >>> DiracDelta(1)
    0
    >>> DiracDelta(-1)
    0
    >>> DiracDelta(pi)
    0
    >>> DiracDelta(x - 4).subs(x, 4)
    DiracDelta(0)
    >>> diff(DiracDelta(x))
    DiracDelta(x, 1)
    >>> diff(DiracDelta(x - 1),x,2)
    DiracDelta(x - 1, 2)
    >>> diff(DiracDelta(x**2 - 1),x,2)
    2*(2*x**2*DiracDelta(x**2 - 1, 2) + DiracDelta(x**2 - 1, 1))
    >>> DiracDelta(3*x).is_simple(x)
    True
    >>> DiracDelta(x**2).is_simple(x)
    False
    >>> DiracDelta((x**2 - 1)*y).expand(diracdelta=True, wrt=x)
    DiracDelta(x - 1)/(2*Abs(y)) + DiracDelta(x + 1)/(2*Abs(y))


    See Also
    ========

    Heaviside
    simplify, is_simple
    sympy.functions.special.tensor_functions.KroneckerDelta

    References
    ==========

    .. [1] http://mathworld.wolfram.com/DeltaFunction.html
    """

    is_real = True

    def fdiff(self, argindex=1):
        """
        Returns the first derivative of a DiracDelta Function.

        The difference between ``diff()`` and ``fdiff()`` is:-
        ``diff()`` is the user-level function and ``fdiff()`` is an object method.
        ``fdiff()`` is just a convenience method available in the ``Function`` class.
        It returns the derivative of the function without considering the chain rule.
        ``diff(function, x)`` calls ``Function._eval_derivative`` which in turn calls
        ``fdiff()`` internally to compute the derivative of the function.

        Examples
        ========

        >>> from sympy import DiracDelta, diff
        >>> from sympy.abc import x

        >>> DiracDelta(x).fdiff()
        DiracDelta(x, 1)

        >>> DiracDelta(x, 1).fdiff()
        DiracDelta(x, 2)

        >>> DiracDelta(x**2 - 1).fdiff()
        DiracDelta(x**2 - 1, 1)

        >>> diff(DiracDelta(x, 1)).fdiff()
        DiracDelta(x, 3)

        """
        if argindex == 1:
            #I didn't know if there is a better way to handle default arguments
            k = 0
            if len(self.args) > 1:
                k = self.args[1]
            return self.func(self.args[0], k + 1)
        else:
            raise ArgumentIndexError(self, argindex)

    @classmethod
    def eval(cls, arg, k=0):
        """
        Returns a simplified form or a value of DiracDelta depending on the
        argument passed by the DiracDelta object.

        The ``eval()`` method is automatically called when the ``DiracDelta`` class
        is about to be instantiated and it returns either some simplified instance
        or the unevaluated instance depending on the argument passed. In other words,
        ``eval()`` method is not needed to be called explicitly, it is being called
        and evaluated once the object is called.

        Examples
        ========

        >>> from sympy import DiracDelta, S, Subs
        >>> from sympy.abc import x

        >>> DiracDelta(x)
        DiracDelta(x)

        >>> DiracDelta(-x, 1)
        -DiracDelta(x, 1)

        >>> DiracDelta(1)
        0

        >>> DiracDelta(5, 1)
        0

        >>> DiracDelta(0)
        DiracDelta(0)

        >>> DiracDelta(-1)
        0

        >>> DiracDelta(S.NaN)
        nan

        >>> DiracDelta(x).eval(1)
        0

        >>> DiracDelta(x - 100).subs(x, 5)
        0

        >>> DiracDelta(x - 100).subs(x, 100)
        DiracDelta(0)

        """
        k = sympify(k)
        if not k.is_Integer or k.is_negative:
            raise ValueError("Error: the second argument of DiracDelta must be \
            a non-negative integer, %s given instead." % (k,))
        arg = sympify(arg)
        if arg is S.NaN:
            return S.NaN
        if arg.is_nonzero:
            return S.Zero
        if fuzzy_not(im(arg).is_zero):
            raise ValueError(filldedent('''
                Function defined only for Real Values.
                Complex part: %s  found in %s .''' % (
                repr(im(arg)), repr(arg))))
        c, nc = arg.args_cnc()
        if c and c[0] == -1:
            # keep this fast and simple instead of using
            # could_extract_minus_sign
            if k % 2 == 1:
                return -cls(-arg, k)
            elif k % 2 == 0:
                return cls(-arg, k) if k else cls(-arg)

    @deprecated(useinstead="expand(diracdelta=True, wrt=x)", issue=12859, deprecated_since_version="1.1")
    def simplify(self, x):
        return self.expand(diracdelta=True, wrt=x)

    def _eval_expand_diracdelta(self, **hints):
        """Compute a simplified representation of the function using
           property number 4. Pass wrt as a hint to expand the expression
           with respect to a particular variable.

           wrt is:

           - a variable with respect to which a DiracDelta expression will
           get expanded.

           Examples
           ========

           >>> from sympy import DiracDelta
           >>> from sympy.abc import x, y

           >>> DiracDelta(x*y).expand(diracdelta=True, wrt=x)
           DiracDelta(x)/Abs(y)
           >>> DiracDelta(x*y).expand(diracdelta=True, wrt=y)
           DiracDelta(y)/Abs(x)

           >>> DiracDelta(x**2 + x - 2).expand(diracdelta=True, wrt=x)
           DiracDelta(x - 1)/3 + DiracDelta(x + 2)/3

           See Also
           ========

           is_simple, Diracdelta

        """
        from sympy.polys.polyroots import roots

        wrt = hints.get('wrt', None)
        if wrt is None:
            free = self.free_symbols
            if len(free) == 1:
                wrt = free.pop()
            else:
                raise TypeError(filldedent('''
            When there is more than 1 free symbol or variable in the expression,
            the 'wrt' keyword is required as a hint to expand when using the
            DiracDelta hint.'''))

        if not self.args[0].has(wrt) or (len(self.args) > 1 and self.args[1] != 0 ):
            return self
        try:
            argroots = roots(self.args[0], wrt)
            result = 0
            valid = True
            darg = abs(diff(self.args[0], wrt))
            for r, m in argroots.items():
                if r.is_real is not False and m == 1:
                    result += self.func(wrt - r)/darg.subs(wrt, r)
                else:
                    # don't handle non-real and if m != 1 then
                    # a polynomial will have a zero in the derivative (darg)
                    # at r
                    valid = False
                    break
            if valid:
                return result
        except PolynomialError:
            pass
        return self

    def is_simple(self, x):
        """is_simple(self, x)

           Tells whether the argument(args[0]) of DiracDelta is a linear
           expression in x.

           x can be:

           - a symbol

           Examples
           ========

           >>> from sympy import DiracDelta, cos
           >>> from sympy.abc import x, y

           >>> DiracDelta(x*y).is_simple(x)
           True
           >>> DiracDelta(x*y).is_simple(y)
           True

           >>> DiracDelta(x**2 + x - 2).is_simple(x)
           False

           >>> DiracDelta(cos(x)).is_simple(x)
           False

           See Also
           ========

           simplify, Diracdelta

        """
        p = self.args[0].as_poly(x)
        if p:
            return p.degree() == 1
        return False

    def _eval_rewrite_as_Piecewise(self, *args, **kwargs):
        """Represents DiracDelta in a Piecewise form

           Examples
           ========

           >>> from sympy import DiracDelta, Piecewise, Symbol, SingularityFunction
           >>> x = Symbol('x')

           >>> DiracDelta(x).rewrite(Piecewise)
           Piecewise((DiracDelta(0), Eq(x, 0)), (0, True))

           >>> DiracDelta(x - 5).rewrite(Piecewise)
           Piecewise((DiracDelta(0), Eq(x - 5, 0)), (0, True))

           >>> DiracDelta(x**2 - 5).rewrite(Piecewise)
           Piecewise((DiracDelta(0), Eq(x**2 - 5, 0)), (0, True))

           >>> DiracDelta(x - 5, 4).rewrite(Piecewise)
           DiracDelta(x - 5, 4)

        """
        if len(args) == 1:
            return Piecewise((DiracDelta(0), Eq(args[0], 0)), (0, True))

    def _eval_rewrite_as_SingularityFunction(self, *args, **kwargs):
        """
        Returns the DiracDelta expression written in the form of Singularity Functions.

        """
        from sympy.solvers import solve
        from sympy.functions import SingularityFunction
        if self == DiracDelta(0):
            return SingularityFunction(0, 0, -1)
        if self == DiracDelta(0, 1):
            return SingularityFunction(0, 0, -2)
        free = self.free_symbols
        if len(free) == 1:
            x = (free.pop())
            if len(args) == 1:
                return SingularityFunction(x, solve(args[0], x)[0], -1)
            return SingularityFunction(x, solve(args[0], x)[0], -args[1] - 1)
        else:
            # I don't know how to handle the case for DiracDelta expressions
            # having arguments with more than one variable.
            raise TypeError(filldedent('''
                rewrite(SingularityFunction) doesn't support
                arguments with more that 1 variable.'''))

    def _sage_(self):
        import sage.all as sage
        return sage.dirac_delta(self.args[0]._sage_())


###############################################################################
############################## HEAVISIDE FUNCTION #############################
###############################################################################


class Heaviside(Function):
    """Heaviside Piecewise function

    Heaviside function has the following properties [1]_:

    1) ``diff(Heaviside(x),x) = DiracDelta(x)``
                        ``( 0, if x < 0``
    2) ``Heaviside(x) = < ( undefined if x==0 [1]``
                        ``( 1, if x > 0``
    3) ``Max(0,x).diff(x) = Heaviside(x)``

    .. [1] Regarding to the value at 0, Mathematica defines ``H(0) = 1``,
           but Maple uses ``H(0) = undefined``.  Different application areas
           may have specific conventions.  For example, in control theory, it
           is common practice to assume ``H(0) == 0`` to match the Laplace
           transform of a DiracDelta distribution.

    To specify the value of Heaviside at x=0, a second argument can be given.
    Omit this 2nd argument or pass ``None`` to recover the default behavior.

    >>> from sympy import Heaviside, S
    >>> from sympy.abc import x
    >>> Heaviside(9)
    1
    >>> Heaviside(-9)
    0
    >>> Heaviside(0)
    Heaviside(0)
    >>> Heaviside(0, S.Half)
    1/2
    >>> (Heaviside(x) + 1).replace(Heaviside(x), Heaviside(x, 1))
    Heaviside(x, 1) + 1

    See Also
    ========

    DiracDelta

    References
    ==========

    .. [2] http://mathworld.wolfram.com/HeavisideStepFunction.html
    .. [3] http://dlmf.nist.gov/1.16#iv

    """

    is_real = True

    def fdiff(self, argindex=1):
        """
        Returns the first derivative of a Heaviside Function.

        Examples
        ========

        >>> from sympy import Heaviside, diff
        >>> from sympy.abc import x

        >>> Heaviside(x).fdiff()
        DiracDelta(x)

        >>> Heaviside(x**2 - 1).fdiff()
        DiracDelta(x**2 - 1)

        >>> diff(Heaviside(x)).fdiff()
        DiracDelta(x, 1)

        """
        if argindex == 1:
            # property number 1
            return DiracDelta(self.args[0])
        else:
            raise ArgumentIndexError(self, argindex)

    def __new__(cls, arg, H0=None, **options):
        if H0 is None:
            return super(cls, cls).__new__(cls, arg, **options)
        else:
            return super(cls, cls).__new__(cls, arg, H0, **options)

    @classmethod
    def eval(cls, arg, H0=None):
        """
        Returns a simplified form or a value of Heaviside depending on the
        argument passed by the Heaviside object.

        The ``eval()`` method is automatically called when the ``Heaviside`` class
        is about to be instantiated and it returns either some simplified instance
        or the unevaluated instance depending on the argument passed. In other words,
        ``eval()`` method is not needed to be called explicitly, it is being called
        and evaluated once the object is called.

        Examples
        ========

        >>> from sympy import Heaviside, S
        >>> from sympy.abc import x

        >>> Heaviside(x)
        Heaviside(x)

        >>> Heaviside(19)
        1

        >>> Heaviside(0)
        Heaviside(0)

        >>> Heaviside(0, 1)
        1

        >>> Heaviside(-5)
        0

        >>> Heaviside(S.NaN)
        nan

        >>> Heaviside(x).eval(100)
        1

        >>> Heaviside(x - 100).subs(x, 5)
        0

        >>> Heaviside(x - 100).subs(x, 105)
        1

        """
        H0 = sympify(H0)
        arg = sympify(arg)
        if arg.is_negative:
            return S.Zero
        elif arg.is_positive:
            return S.One
        elif arg.is_zero:
            return H0
        elif arg is S.NaN:
            return S.NaN
        elif fuzzy_not(im(arg).is_zero):
            raise ValueError("Function defined only for Real Values. Complex part: %s  found in %s ." % (repr(im(arg)), repr(arg)) )

    def _eval_rewrite_as_Piecewise(self, arg, H0=None, **kwargs):
        """Represents Heaviside in a Piecewise form

           Examples
           ========

           >>> from sympy import Heaviside, Piecewise, Symbol, pprint
           >>> x = Symbol('x')

           >>> Heaviside(x).rewrite(Piecewise)
           Piecewise((0, x < 0), (Heaviside(0), Eq(x, 0)), (1, x > 0))

           >>> Heaviside(x - 5).rewrite(Piecewise)
           Piecewise((0, x - 5 < 0), (Heaviside(0), Eq(x - 5, 0)), (1, x - 5 > 0))

           >>> Heaviside(x**2 - 1).rewrite(Piecewise)
           Piecewise((0, x**2 - 1 < 0), (Heaviside(0), Eq(x**2 - 1, 0)), (1, x**2 - 1 > 0))

        """
        if H0 is None:
            return Piecewise((0, arg < 0), (Heaviside(0), Eq(arg, 0)), (1, arg > 0))
        if H0 == 0:
            return Piecewise((0, arg <= 0), (1, arg > 0))
        if H0 == 1:
            return Piecewise((0, arg < 0), (1, arg >= 0))
        return Piecewise((0, arg < 0), (H0, Eq(arg, 0)), (1, arg > 0))

    def _eval_rewrite_as_sign(self, arg, H0=None, **kwargs):
        """Represents the Heaviside function in the form of sign function.
        The value of the second argument of Heaviside must specify Heaviside(0)
        = 1/2 for rewritting as sign to be strictly equivalent.  For easier
        usage, we also allow this rewriting when Heaviside(0) is undefined.

        Examples
        ========

        >>> from sympy import Heaviside, Symbol, sign
        >>> x = Symbol('x', real=True)

        >>> Heaviside(x).rewrite(sign)
        sign(x)/2 + 1/2

        >>> Heaviside(x, 0).rewrite(sign)
        Heaviside(x, 0)

        >>> Heaviside(x - 2).rewrite(sign)
        sign(x - 2)/2 + 1/2

        >>> Heaviside(x**2 - 2*x + 1).rewrite(sign)
        sign(x**2 - 2*x + 1)/2 + 1/2

        >>> y = Symbol('y')

        >>> Heaviside(y).rewrite(sign)
        Heaviside(y)

        >>> Heaviside(y**2 - 2*y + 1).rewrite(sign)
        Heaviside(y**2 - 2*y + 1)

        See Also
        ========

        sign

        """
        if arg.is_real:
            if H0 is None or H0 == S.Half:
                return (sign(arg)+1)/2

    def _eval_rewrite_as_SingularityFunction(self, args, **kwargs):
        """
        Returns the Heaviside expression written in the form of Singularity Functions.

        """
        from sympy.solvers import solve
        from sympy.functions import SingularityFunction
        if self == Heaviside(0):
            return SingularityFunction(0, 0, 0)
        free = self.free_symbols
        if len(free) == 1:
            x = (free.pop())
            return SingularityFunction(x, solve(args, x)[0], 0)
            # TODO
            # ((x - 5)**3*Heaviside(x - 5)).rewrite(SingularityFunction) should output
            # SingularityFunction(x, 5, 0) instead of (x - 5)**3*SingularityFunction(x, 5, 0)
        else:
            # I don't know how to handle the case for Heaviside expressions
            # having arguments with more than one variable.
            raise TypeError(filldedent('''
                rewrite(SingularityFunction) doesn't
                support arguments with more that 1 variable.'''))

    def _sage_(self):
        import sage.all as sage
        return sage.heaviside(self.args[0]._sage_())
