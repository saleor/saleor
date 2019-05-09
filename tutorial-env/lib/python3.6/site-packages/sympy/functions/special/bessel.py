from __future__ import print_function, division

from functools import wraps

from sympy import S, pi, I, Rational, Wild, cacheit, sympify
from sympy.core.function import Function, ArgumentIndexError
from sympy.core.power import Pow
from sympy.core.compatibility import range
from sympy.functions.combinatorial.factorials import factorial
from sympy.functions.elementary.trigonometric import sin, cos, csc, cot
from sympy.functions.elementary.complexes import Abs
from sympy.functions.elementary.miscellaneous import sqrt, root
from sympy.functions.elementary.complexes import re, im
from sympy.functions.special.gamma_functions import gamma
from sympy.functions.special.hyper import hyper
from sympy.polys.orthopolys import spherical_bessel_fn as fn


# TODO
# o Scorer functions G1 and G2
# o Asymptotic expansions
#   These are possible, e.g. for fixed order, but since the bessel type
#   functions are oscillatory they are not actually tractable at
#   infinity, so this is not particularly useful right now.
# o Series Expansions for functions of the second kind about zero
# o Nicer series expansions.
# o More rewriting.
# o Add solvers to ode.py (or rather add solvers for the hypergeometric equation).


class BesselBase(Function):
    """
    Abstract base class for bessel-type functions.

    This class is meant to reduce code duplication.
    All Bessel type functions can 1) be differentiated, and the derivatives
    expressed in terms of similar functions and 2) be rewritten in terms
    of other bessel-type functions.

    Here "bessel-type functions" are assumed to have one complex parameter.

    To use this base class, define class attributes ``_a`` and ``_b`` such that
    ``2*F_n' = -_a*F_{n+1} + b*F_{n-1}``.
    """

    @property
    def order(self):
        """ The order of the bessel-type function. """
        return self.args[0]

    @property
    def argument(self):
        """ The argument of the bessel-type function. """
        return self.args[1]

    @classmethod
    def eval(cls, nu, z):
        return

    def fdiff(self, argindex=2):
        if argindex != 2:
            raise ArgumentIndexError(self, argindex)
        return (self._b/2 * self.__class__(self.order - 1, self.argument) -
                self._a/2 * self.__class__(self.order + 1, self.argument))

    def _eval_conjugate(self):
        z = self.argument
        if (z.is_real and z.is_negative) is False:
            return self.__class__(self.order.conjugate(), z.conjugate())

    def _eval_expand_func(self, **hints):
        nu, z, f = self.order, self.argument, self.__class__
        if nu.is_real:
            if (nu - 1).is_positive:
                return (-self._a*self._b*f(nu - 2, z)._eval_expand_func() +
                        2*self._a*(nu - 1)*f(nu - 1, z)._eval_expand_func()/z)
            elif (nu + 1).is_negative:
                return (2*self._b*(nu + 1)*f(nu + 1, z)._eval_expand_func()/z -
                        self._a*self._b*f(nu + 2, z)._eval_expand_func())
        return self

    def _eval_simplify(self, ratio, measure, rational, inverse):
        from sympy.simplify.simplify import besselsimp
        return besselsimp(self)


class besselj(BesselBase):
    r"""
    Bessel function of the first kind.

    The Bessel `J` function of order `\nu` is defined to be the function
    satisfying Bessel's differential equation

    .. math ::
        z^2 \frac{\mathrm{d}^2 w}{\mathrm{d}z^2}
        + z \frac{\mathrm{d}w}{\mathrm{d}z} + (z^2 - \nu^2) w = 0,

    with Laurent expansion

    .. math ::
        J_\nu(z) = z^\nu \left(\frac{1}{\Gamma(\nu + 1) 2^\nu} + O(z^2) \right),

    if :math:`\nu` is not a negative integer. If :math:`\nu=-n \in \mathbb{Z}_{<0}`
    *is* a negative integer, then the definition is

    .. math ::
        J_{-n}(z) = (-1)^n J_n(z).

    Examples
    ========

    Create a Bessel function object:

    >>> from sympy import besselj, jn
    >>> from sympy.abc import z, n
    >>> b = besselj(n, z)

    Differentiate it:

    >>> b.diff(z)
    besselj(n - 1, z)/2 - besselj(n + 1, z)/2

    Rewrite in terms of spherical Bessel functions:

    >>> b.rewrite(jn)
    sqrt(2)*sqrt(z)*jn(n - 1/2, z)/sqrt(pi)

    Access the parameter and argument:

    >>> b.order
    n
    >>> b.argument
    z

    See Also
    ========

    bessely, besseli, besselk

    References
    ==========

    .. [1] Abramowitz, Milton; Stegun, Irene A., eds. (1965), "Chapter 9",
           Handbook of Mathematical Functions with Formulas, Graphs, and
           Mathematical Tables
    .. [2] Luke, Y. L. (1969), The Special Functions and Their
           Approximations, Volume 1
    .. [3] https://en.wikipedia.org/wiki/Bessel_function
    .. [4] http://functions.wolfram.com/Bessel-TypeFunctions/BesselJ/
    """

    _a = S.One
    _b = S.One

    @classmethod
    def eval(cls, nu, z):
        if z.is_zero:
            if nu.is_zero:
                return S.One
            elif (nu.is_integer and nu.is_zero is False) or re(nu).is_positive:
                return S.Zero
            elif re(nu).is_negative and not (nu.is_integer is True):
                return S.ComplexInfinity
            elif nu.is_imaginary:
                return S.NaN
        if z is S.Infinity or (z is S.NegativeInfinity):
            return S.Zero

        if z.could_extract_minus_sign():
            return (z)**nu*(-z)**(-nu)*besselj(nu, -z)
        if nu.is_integer:
            if nu.could_extract_minus_sign():
                return S(-1)**(-nu)*besselj(-nu, z)
            newz = z.extract_multiplicatively(I)
            if newz:  # NOTE we don't want to change the function if z==0
                return I**(nu)*besseli(nu, newz)

        # branch handling:
        from sympy import unpolarify, exp
        if nu.is_integer:
            newz = unpolarify(z)
            if newz != z:
                return besselj(nu, newz)
        else:
            newz, n = z.extract_branch_factor()
            if n != 0:
                return exp(2*n*pi*nu*I)*besselj(nu, newz)
        nnu = unpolarify(nu)
        if nu != nnu:
            return besselj(nnu, z)

    def _eval_rewrite_as_besseli(self, nu, z, **kwargs):
        from sympy import polar_lift, exp
        return exp(I*pi*nu/2)*besseli(nu, polar_lift(-I)*z)

    def _eval_rewrite_as_bessely(self, nu, z, **kwargs):
        if nu.is_integer is False:
            return csc(pi*nu)*bessely(-nu, z) - cot(pi*nu)*bessely(nu, z)

    def _eval_rewrite_as_jn(self, nu, z, **kwargs):
        return sqrt(2*z/pi)*jn(nu - S.Half, self.argument)

    def _eval_is_real(self):
        nu, z = self.args
        if nu.is_integer and z.is_real:
            return True

    def _sage_(self):
        import sage.all as sage
        return sage.bessel_J(self.args[0]._sage_(), self.args[1]._sage_())


class bessely(BesselBase):
    r"""
    Bessel function of the second kind.

    The Bessel `Y` function of order `\nu` is defined as

    .. math ::
        Y_\nu(z) = \lim_{\mu \to \nu} \frac{J_\mu(z) \cos(\pi \mu)
                                            - J_{-\mu}(z)}{\sin(\pi \mu)},

    where :math:`J_\mu(z)` is the Bessel function of the first kind.

    It is a solution to Bessel's equation, and linearly independent from
    :math:`J_\nu`.

    Examples
    ========

    >>> from sympy import bessely, yn
    >>> from sympy.abc import z, n
    >>> b = bessely(n, z)
    >>> b.diff(z)
    bessely(n - 1, z)/2 - bessely(n + 1, z)/2
    >>> b.rewrite(yn)
    sqrt(2)*sqrt(z)*yn(n - 1/2, z)/sqrt(pi)

    See Also
    ========

    besselj, besseli, besselk

    References
    ==========

    .. [1] http://functions.wolfram.com/Bessel-TypeFunctions/BesselY/

    """

    _a = S.One
    _b = S.One

    @classmethod
    def eval(cls, nu, z):
        if z.is_zero:
            if nu.is_zero:
                return S.NegativeInfinity
            elif re(nu).is_zero is False:
                return S.ComplexInfinity
            elif re(nu).is_zero:
                return S.NaN
        if z is S.Infinity or z is S.NegativeInfinity:
            return S.Zero

        if nu.is_integer:
            if nu.could_extract_minus_sign():
                return S(-1)**(-nu)*bessely(-nu, z)

    def _eval_rewrite_as_besselj(self, nu, z, **kwargs):
        if nu.is_integer is False:
            return csc(pi*nu)*(cos(pi*nu)*besselj(nu, z) - besselj(-nu, z))

    def _eval_rewrite_as_besseli(self, nu, z, **kwargs):
        aj = self._eval_rewrite_as_besselj(*self.args)
        if aj:
            return aj.rewrite(besseli)

    def _eval_rewrite_as_yn(self, nu, z, **kwargs):
        return sqrt(2*z/pi) * yn(nu - S.Half, self.argument)

    def _eval_is_real(self):
        nu, z = self.args
        if nu.is_integer and z.is_positive:
            return True

    def _sage_(self):
        import sage.all as sage
        return sage.bessel_Y(self.args[0]._sage_(), self.args[1]._sage_())


class besseli(BesselBase):
    r"""
    Modified Bessel function of the first kind.

    The Bessel I function is a solution to the modified Bessel equation

    .. math ::
        z^2 \frac{\mathrm{d}^2 w}{\mathrm{d}z^2}
        + z \frac{\mathrm{d}w}{\mathrm{d}z} + (z^2 + \nu^2)^2 w = 0.

    It can be defined as

    .. math ::
        I_\nu(z) = i^{-\nu} J_\nu(iz),

    where :math:`J_\nu(z)` is the Bessel function of the first kind.

    Examples
    ========

    >>> from sympy import besseli
    >>> from sympy.abc import z, n
    >>> besseli(n, z).diff(z)
    besseli(n - 1, z)/2 + besseli(n + 1, z)/2

    See Also
    ========

    besselj, bessely, besselk

    References
    ==========

    .. [1] http://functions.wolfram.com/Bessel-TypeFunctions/BesselI/

    """

    _a = -S.One
    _b = S.One

    @classmethod
    def eval(cls, nu, z):
        if z.is_zero:
            if nu.is_zero:
                return S.One
            elif (nu.is_integer and nu.is_zero is False) or re(nu).is_positive:
                return S.Zero
            elif re(nu).is_negative and not (nu.is_integer is True):
                return S.ComplexInfinity
            elif nu.is_imaginary:
                return S.NaN
        if z.is_imaginary:
            if im(z) is S.Infinity or im(z) is S.NegativeInfinity:
                return S.Zero

        if z.could_extract_minus_sign():
            return (z)**nu*(-z)**(-nu)*besseli(nu, -z)
        if nu.is_integer:
            if nu.could_extract_minus_sign():
                return besseli(-nu, z)
            newz = z.extract_multiplicatively(I)
            if newz:  # NOTE we don't want to change the function if z==0
                return I**(-nu)*besselj(nu, -newz)

        # branch handling:
        from sympy import unpolarify, exp
        if nu.is_integer:
            newz = unpolarify(z)
            if newz != z:
                return besseli(nu, newz)
        else:
            newz, n = z.extract_branch_factor()
            if n != 0:
                return exp(2*n*pi*nu*I)*besseli(nu, newz)
        nnu = unpolarify(nu)
        if nu != nnu:
            return besseli(nnu, z)

    def _eval_rewrite_as_besselj(self, nu, z, **kwargs):
        from sympy import polar_lift, exp
        return exp(-I*pi*nu/2)*besselj(nu, polar_lift(I)*z)

    def _eval_rewrite_as_bessely(self, nu, z, **kwargs):
        aj = self._eval_rewrite_as_besselj(*self.args)
        if aj:
            return aj.rewrite(bessely)

    def _eval_rewrite_as_jn(self, nu, z, **kwargs):
        return self._eval_rewrite_as_besselj(*self.args).rewrite(jn)

    def _eval_is_real(self):
        nu, z = self.args
        if nu.is_integer and z.is_real:
            return True

    def _sage_(self):
        import sage.all as sage
        return sage.bessel_I(self.args[0]._sage_(), self.args[1]._sage_())


class besselk(BesselBase):
    r"""
    Modified Bessel function of the second kind.

    The Bessel K function of order :math:`\nu` is defined as

    .. math ::
        K_\nu(z) = \lim_{\mu \to \nu} \frac{\pi}{2}
                   \frac{I_{-\mu}(z) -I_\mu(z)}{\sin(\pi \mu)},

    where :math:`I_\mu(z)` is the modified Bessel function of the first kind.

    It is a solution of the modified Bessel equation, and linearly independent
    from :math:`Y_\nu`.

    Examples
    ========

    >>> from sympy import besselk
    >>> from sympy.abc import z, n
    >>> besselk(n, z).diff(z)
    -besselk(n - 1, z)/2 - besselk(n + 1, z)/2

    See Also
    ========

    besselj, besseli, bessely

    References
    ==========

    .. [1] http://functions.wolfram.com/Bessel-TypeFunctions/BesselK/

    """

    _a = S.One
    _b = -S.One

    @classmethod
    def eval(cls, nu, z):
        if z.is_zero:
            if nu.is_zero:
                return S.Infinity
            elif re(nu).is_zero is False:
                return S.ComplexInfinity
            elif re(nu).is_zero:
                return S.NaN
        if z.is_imaginary:
            if im(z) is S.Infinity or im(z) is S.NegativeInfinity:
                return S.Zero

        if nu.is_integer:
            if nu.could_extract_minus_sign():
                return besselk(-nu, z)

    def _eval_rewrite_as_besseli(self, nu, z, **kwargs):
        if nu.is_integer is False:
            return pi*csc(pi*nu)*(besseli(-nu, z) - besseli(nu, z))/2

    def _eval_rewrite_as_besselj(self, nu, z, **kwargs):
        ai = self._eval_rewrite_as_besseli(*self.args)
        if ai:
            return ai.rewrite(besselj)

    def _eval_rewrite_as_bessely(self, nu, z, **kwargs):
        aj = self._eval_rewrite_as_besselj(*self.args)
        if aj:
            return aj.rewrite(bessely)

    def _eval_rewrite_as_yn(self, nu, z, **kwargs):
        ay = self._eval_rewrite_as_bessely(*self.args)
        if ay:
            return ay.rewrite(yn)

    def _eval_is_real(self):
        nu, z = self.args
        if nu.is_integer and z.is_positive:
            return True

    def _sage_(self):
        import sage.all as sage
        return sage.bessel_K(self.args[0]._sage_(), self.args[1]._sage_())


class hankel1(BesselBase):
    r"""
    Hankel function of the first kind.

    This function is defined as

    .. math ::
        H_\nu^{(1)} = J_\nu(z) + iY_\nu(z),

    where :math:`J_\nu(z)` is the Bessel function of the first kind, and
    :math:`Y_\nu(z)` is the Bessel function of the second kind.

    It is a solution to Bessel's equation.

    Examples
    ========

    >>> from sympy import hankel1
    >>> from sympy.abc import z, n
    >>> hankel1(n, z).diff(z)
    hankel1(n - 1, z)/2 - hankel1(n + 1, z)/2

    See Also
    ========

    hankel2, besselj, bessely

    References
    ==========

    .. [1] http://functions.wolfram.com/Bessel-TypeFunctions/HankelH1/

    """

    _a = S.One
    _b = S.One

    def _eval_conjugate(self):
        z = self.argument
        if (z.is_real and z.is_negative) is False:
            return hankel2(self.order.conjugate(), z.conjugate())


class hankel2(BesselBase):
    r"""
    Hankel function of the second kind.

    This function is defined as

    .. math ::
        H_\nu^{(2)} = J_\nu(z) - iY_\nu(z),

    where :math:`J_\nu(z)` is the Bessel function of the first kind, and
    :math:`Y_\nu(z)` is the Bessel function of the second kind.

    It is a solution to Bessel's equation, and linearly independent from
    :math:`H_\nu^{(1)}`.

    Examples
    ========

    >>> from sympy import hankel2
    >>> from sympy.abc import z, n
    >>> hankel2(n, z).diff(z)
    hankel2(n - 1, z)/2 - hankel2(n + 1, z)/2

    See Also
    ========

    hankel1, besselj, bessely

    References
    ==========

    .. [1] http://functions.wolfram.com/Bessel-TypeFunctions/HankelH2/

    """

    _a = S.One
    _b = S.One

    def _eval_conjugate(self):
        z = self.argument
        if (z.is_real and z.is_negative) is False:
            return hankel1(self.order.conjugate(), z.conjugate())


def assume_integer_order(fn):
    @wraps(fn)
    def g(self, nu, z):
        if nu.is_integer:
            return fn(self, nu, z)
    return g


class SphericalBesselBase(BesselBase):
    """
    Base class for spherical Bessel functions.

    These are thin wrappers around ordinary Bessel functions,
    since spherical Bessel functions differ from the ordinary
    ones just by a slight change in order.

    To use this class, define the ``_rewrite`` and ``_expand`` methods.
    """

    def _expand(self, **hints):
        """ Expand self into a polynomial. Nu is guaranteed to be Integer. """
        raise NotImplementedError('expansion')

    def _rewrite(self):
        """ Rewrite self in terms of ordinary Bessel functions. """
        raise NotImplementedError('rewriting')

    def _eval_expand_func(self, **hints):
        if self.order.is_Integer:
            return self._expand(**hints)
        return self

    def _eval_evalf(self, prec):
        if self.order.is_Integer:
            return self._rewrite()._eval_evalf(prec)

    def fdiff(self, argindex=2):
        if argindex != 2:
            raise ArgumentIndexError(self, argindex)
        return self.__class__(self.order - 1, self.argument) - \
            self * (self.order + 1)/self.argument


def _jn(n, z):
    return fn(n, z)*sin(z) + (-1)**(n + 1)*fn(-n - 1, z)*cos(z)


def _yn(n, z):
    # (-1)**(n + 1) * _jn(-n - 1, z)
    return (-1)**(n + 1) * fn(-n - 1, z)*sin(z) - fn(n, z)*cos(z)


class jn(SphericalBesselBase):
    r"""
    Spherical Bessel function of the first kind.

    This function is a solution to the spherical Bessel equation

    .. math ::
        z^2 \frac{\mathrm{d}^2 w}{\mathrm{d}z^2}
          + 2z \frac{\mathrm{d}w}{\mathrm{d}z} + (z^2 - \nu(\nu + 1)) w = 0.

    It can be defined as

    .. math ::
        j_\nu(z) = \sqrt{\frac{\pi}{2z}} J_{\nu + \frac{1}{2}}(z),

    where :math:`J_\nu(z)` is the Bessel function of the first kind.

    The spherical Bessel functions of integral order are
    calculated using the formula:

    .. math:: j_n(z) = f_n(z) \sin{z} + (-1)^{n+1} f_{-n-1}(z) \cos{z},

    where the coefficients :math:`f_n(z)` are available as
    :func:`polys.orthopolys.spherical_bessel_fn`.

    Examples
    ========

    >>> from sympy import Symbol, jn, sin, cos, expand_func, besselj, bessely
    >>> from sympy import simplify
    >>> z = Symbol("z")
    >>> nu = Symbol("nu", integer=True)
    >>> print(expand_func(jn(0, z)))
    sin(z)/z
    >>> expand_func(jn(1, z)) == sin(z)/z**2 - cos(z)/z
    True
    >>> expand_func(jn(3, z))
    (-6/z**2 + 15/z**4)*sin(z) + (1/z - 15/z**3)*cos(z)
    >>> jn(nu, z).rewrite(besselj)
    sqrt(2)*sqrt(pi)*sqrt(1/z)*besselj(nu + 1/2, z)/2
    >>> jn(nu, z).rewrite(bessely)
    (-1)**nu*sqrt(2)*sqrt(pi)*sqrt(1/z)*bessely(-nu - 1/2, z)/2
    >>> jn(2, 5.2+0.3j).evalf(20)
    0.099419756723640344491 - 0.054525080242173562897*I

    See Also
    ========

    besselj, bessely, besselk, yn

    References
    ==========

    .. [1] http://dlmf.nist.gov/10.47

    """

    def _rewrite(self):
        return self._eval_rewrite_as_besselj(self.order, self.argument)

    def _eval_rewrite_as_besselj(self, nu, z, **kwargs):
        return sqrt(pi/(2*z)) * besselj(nu + S.Half, z)

    def _eval_rewrite_as_bessely(self, nu, z, **kwargs):
        return (-1)**nu * sqrt(pi/(2*z)) * bessely(-nu - S.Half, z)

    def _eval_rewrite_as_yn(self, nu, z, **kwargs):
        return (-1)**(nu) * yn(-nu - 1, z)

    def _expand(self, **hints):
        return _jn(self.order, self.argument)


class yn(SphericalBesselBase):
    r"""
    Spherical Bessel function of the second kind.

    This function is another solution to the spherical Bessel equation, and
    linearly independent from :math:`j_n`. It can be defined as

    .. math ::
        y_\nu(z) = \sqrt{\frac{\pi}{2z}} Y_{\nu + \frac{1}{2}}(z),

    where :math:`Y_\nu(z)` is the Bessel function of the second kind.

    For integral orders :math:`n`, :math:`y_n` is calculated using the formula:

    .. math:: y_n(z) = (-1)^{n+1} j_{-n-1}(z)

    Examples
    ========

    >>> from sympy import Symbol, yn, sin, cos, expand_func, besselj, bessely
    >>> z = Symbol("z")
    >>> nu = Symbol("nu", integer=True)
    >>> print(expand_func(yn(0, z)))
    -cos(z)/z
    >>> expand_func(yn(1, z)) == -cos(z)/z**2-sin(z)/z
    True
    >>> yn(nu, z).rewrite(besselj)
    (-1)**(nu + 1)*sqrt(2)*sqrt(pi)*sqrt(1/z)*besselj(-nu - 1/2, z)/2
    >>> yn(nu, z).rewrite(bessely)
    sqrt(2)*sqrt(pi)*sqrt(1/z)*bessely(nu + 1/2, z)/2
    >>> yn(2, 5.2+0.3j).evalf(20)
    0.18525034196069722536 + 0.014895573969924817587*I

    See Also
    ========

    besselj, bessely, besselk, jn

    References
    ==========

    .. [1] http://dlmf.nist.gov/10.47

    """

    def _rewrite(self):
        return self._eval_rewrite_as_bessely(self.order, self.argument)

    @assume_integer_order
    def _eval_rewrite_as_besselj(self, nu, z, **kwargs):
        return (-1)**(nu+1) * sqrt(pi/(2*z)) * besselj(-nu - S.Half, z)

    @assume_integer_order
    def _eval_rewrite_as_bessely(self, nu, z, **kwargs):
        return sqrt(pi/(2*z)) * bessely(nu + S.Half, z)

    def _eval_rewrite_as_jn(self, nu, z, **kwargs):
        return (-1)**(nu + 1) * jn(-nu - 1, z)

    def _expand(self, **hints):
        return _yn(self.order, self.argument)


class SphericalHankelBase(SphericalBesselBase):

    def _rewrite(self):
        return self._eval_rewrite_as_besselj(self.order, self.argument)

    @assume_integer_order
    def _eval_rewrite_as_besselj(self, nu, z, **kwargs):
        # jn +- I*yn
        # jn as beeselj: sqrt(pi/(2*z)) * besselj(nu + S.Half, z)
        # yn as besselj: (-1)**(nu+1) * sqrt(pi/(2*z)) * besselj(-nu - S.Half, z)
        hks = self._hankel_kind_sign
        return sqrt(pi/(2*z))*(besselj(nu + S.Half, z) +
                               hks*I*(-1)**(nu+1)*besselj(-nu - S.Half, z))

    @assume_integer_order
    def _eval_rewrite_as_bessely(self, nu, z, **kwargs):
        # jn +- I*yn
        # jn as bessely: (-1)**nu * sqrt(pi/(2*z)) * bessely(-nu - S.Half, z)
        # yn as bessely: sqrt(pi/(2*z)) * bessely(nu + S.Half, z)
        hks = self._hankel_kind_sign
        return sqrt(pi/(2*z))*((-1)**nu*bessely(-nu - S.Half, z) +
                               hks*I*bessely(nu + S.Half, z))

    def _eval_rewrite_as_yn(self, nu, z, **kwargs):
        hks = self._hankel_kind_sign
        return jn(nu, z).rewrite(yn) + hks*I*yn(nu, z)

    def _eval_rewrite_as_jn(self, nu, z, **kwargs):
        hks = self._hankel_kind_sign
        return jn(nu, z) + hks*I*yn(nu, z).rewrite(jn)

    def _eval_expand_func(self, **hints):
        if self.order.is_Integer:
            return self._expand(**hints)
        else:
            nu = self.order
            z = self.argument
            hks = self._hankel_kind_sign
            return jn(nu, z) + hks*I*yn(nu, z)

    def _expand(self, **hints):
        n = self.order
        z = self.argument
        hks = self._hankel_kind_sign

        # fully expanded version
        # return ((fn(n, z) * sin(z) +
        #          (-1)**(n + 1) * fn(-n - 1, z) * cos(z)) +  # jn
        #         (hks * I * (-1)**(n + 1) *
        #          (fn(-n - 1, z) * hk * I * sin(z) +
        #           (-1)**(-n) * fn(n, z) * I * cos(z)))  # +-I*yn
        #         )

        return (_jn(n, z) + hks*I*_yn(n, z)).expand()


class hn1(SphericalHankelBase):
    r"""
    Spherical Hankel function of the first kind.

    This function is defined as

    .. math:: h_\nu^(1)(z) = j_\nu(z) + i y_\nu(z),

    where :math:`j_\nu(z)` and :math:`y_\nu(z)` are the spherical
    Bessel function of the first and second kinds.

    For integral orders :math:`n`, :math:`h_n^(1)` is calculated using the formula:

    .. math:: h_n^(1)(z) = j_{n}(z) + i (-1)^{n+1} j_{-n-1}(z)

    Examples
    ========

    >>> from sympy import Symbol, hn1, hankel1, expand_func, yn, jn
    >>> z = Symbol("z")
    >>> nu = Symbol("nu", integer=True)
    >>> print(expand_func(hn1(nu, z)))
    jn(nu, z) + I*yn(nu, z)
    >>> print(expand_func(hn1(0, z)))
    sin(z)/z - I*cos(z)/z
    >>> print(expand_func(hn1(1, z)))
    -I*sin(z)/z - cos(z)/z + sin(z)/z**2 - I*cos(z)/z**2
    >>> hn1(nu, z).rewrite(jn)
    (-1)**(nu + 1)*I*jn(-nu - 1, z) + jn(nu, z)
    >>> hn1(nu, z).rewrite(yn)
    (-1)**nu*yn(-nu - 1, z) + I*yn(nu, z)
    >>> hn1(nu, z).rewrite(hankel1)
    sqrt(2)*sqrt(pi)*sqrt(1/z)*hankel1(nu, z)/2

    See Also
    ========

    hn2, jn, yn, hankel1, hankel2

    References
    ==========

    .. [1] http://dlmf.nist.gov/10.47

    """

    _hankel_kind_sign = S.One

    @assume_integer_order
    def _eval_rewrite_as_hankel1(self, nu, z, **kwargs):
        return sqrt(pi/(2*z))*hankel1(nu, z)


class hn2(SphericalHankelBase):
    r"""
    Spherical Hankel function of the second kind.

    This function is defined as

    .. math:: h_\nu^(2)(z) = j_\nu(z) - i y_\nu(z),

    where :math:`j_\nu(z)` and :math:`y_\nu(z)` are the spherical
    Bessel function of the first and second kinds.

    For integral orders :math:`n`, :math:`h_n^(2)` is calculated using the formula:

    .. math:: h_n^(2)(z) = j_{n} - i (-1)^{n+1} j_{-n-1}(z)

    Examples
    ========

    >>> from sympy import Symbol, hn2, hankel2, expand_func, jn, yn
    >>> z = Symbol("z")
    >>> nu = Symbol("nu", integer=True)
    >>> print(expand_func(hn2(nu, z)))
    jn(nu, z) - I*yn(nu, z)
    >>> print(expand_func(hn2(0, z)))
    sin(z)/z + I*cos(z)/z
    >>> print(expand_func(hn2(1, z)))
    I*sin(z)/z - cos(z)/z + sin(z)/z**2 + I*cos(z)/z**2
    >>> hn2(nu, z).rewrite(hankel2)
    sqrt(2)*sqrt(pi)*sqrt(1/z)*hankel2(nu, z)/2
    >>> hn2(nu, z).rewrite(jn)
    -(-1)**(nu + 1)*I*jn(-nu - 1, z) + jn(nu, z)
    >>> hn2(nu, z).rewrite(yn)
    (-1)**nu*yn(-nu - 1, z) - I*yn(nu, z)

    See Also
    ========

    hn1, jn, yn, hankel1, hankel2

    References
    ==========

    .. [1] http://dlmf.nist.gov/10.47

    """

    _hankel_kind_sign = -S.One

    @assume_integer_order
    def _eval_rewrite_as_hankel2(self, nu, z, **kwargs):
        return sqrt(pi/(2*z))*hankel2(nu, z)


def jn_zeros(n, k, method="sympy", dps=15):
    """
    Zeros of the spherical Bessel function of the first kind.

    This returns an array of zeros of jn up to the k-th zero.

    * method = "sympy": uses :func:`mpmath.besseljzero`
    * method = "scipy": uses the
      `SciPy's sph_jn <http://docs.scipy.org/doc/scipy/reference/generated/scipy.special.jn_zeros.html>`_
      and
      `newton <http://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.newton.html>`_
      to find all
      roots, which is faster than computing the zeros using a general
      numerical solver, but it requires SciPy and only works with low
      precision floating point numbers.  [The function used with
      method="sympy" is a recent addition to mpmath, before that a general
      solver was used.]

    Examples
    ========

    >>> from sympy import jn_zeros
    >>> jn_zeros(2, 4, dps=5)
    [5.7635, 9.095, 12.323, 15.515]

    See Also
    ========

    jn, yn, besselj, besselk, bessely
    """
    from math import pi

    if method == "sympy":
        from mpmath import besseljzero
        from mpmath.libmp.libmpf import dps_to_prec
        from sympy import Expr
        prec = dps_to_prec(dps)
        return [Expr._from_mpmath(besseljzero(S(n + 0.5)._to_mpmath(prec),
                                              int(l)), prec)
                for l in range(1, k + 1)]
    elif method == "scipy":
        from scipy.optimize import newton
        try:
            from scipy.special import spherical_jn
            f = lambda x: spherical_jn(n, x)
        except ImportError:
            from scipy.special import sph_jn
            f = lambda x: sph_jn(n, x)[0][-1]
    else:
        raise NotImplementedError("Unknown method.")

    def solver(f, x):
        if method == "scipy":
            root = newton(f, x)
        else:
            raise NotImplementedError("Unknown method.")
        return root

    # we need to approximate the position of the first root:
    root = n + pi
    # determine the first root exactly:
    root = solver(f, root)
    roots = [root]
    for i in range(k - 1):
        # estimate the position of the next root using the last root + pi:
        root = solver(f, root + pi)
        roots.append(root)
    return roots


class AiryBase(Function):
    """
    Abstract base class for Airy functions.

    This class is meant to reduce code duplication.
    """

    def _eval_conjugate(self):
        return self.func(self.args[0].conjugate())

    def _eval_is_real(self):
        return self.args[0].is_real

    def _as_real_imag(self, deep=True, **hints):
        if self.args[0].is_real:
            if deep:
                hints['complex'] = False
                return (self.expand(deep, **hints), S.Zero)
            else:
                return (self, S.Zero)
        if deep:
            re, im = self.args[0].expand(deep, **hints).as_real_imag()
        else:
            re, im = self.args[0].as_real_imag()
        return (re, im)

    def as_real_imag(self, deep=True, **hints):
        x, y = self._as_real_imag(deep=deep, **hints)
        sq = -y**2/x**2
        re = S.Half*(self.func(x+x*sqrt(sq))+self.func(x-x*sqrt(sq)))
        im = x/(2*y) * sqrt(sq) * (self.func(x-x*sqrt(sq)) - self.func(x+x*sqrt(sq)))
        return (re, im)

    def _eval_expand_complex(self, deep=True, **hints):
        re_part, im_part = self.as_real_imag(deep=deep, **hints)
        return re_part + im_part*S.ImaginaryUnit


class airyai(AiryBase):
    r"""
    The Airy function `\operatorname{Ai}` of the first kind.

    The Airy function `\operatorname{Ai}(z)` is defined to be the function
    satisfying Airy's differential equation

    .. math::
        \frac{\mathrm{d}^2 w(z)}{\mathrm{d}z^2} - z w(z) = 0.

    Equivalently, for real `z`

    .. math::
        \operatorname{Ai}(z) := \frac{1}{\pi}
        \int_0^\infty \cos\left(\frac{t^3}{3} + z t\right) \mathrm{d}t.

    Examples
    ========

    Create an Airy function object:

    >>> from sympy import airyai
    >>> from sympy.abc import z

    >>> airyai(z)
    airyai(z)

    Several special values are known:

    >>> airyai(0)
    3**(1/3)/(3*gamma(2/3))
    >>> from sympy import oo
    >>> airyai(oo)
    0
    >>> airyai(-oo)
    0

    The Airy function obeys the mirror symmetry:

    >>> from sympy import conjugate
    >>> conjugate(airyai(z))
    airyai(conjugate(z))

    Differentiation with respect to z is supported:

    >>> from sympy import diff
    >>> diff(airyai(z), z)
    airyaiprime(z)
    >>> diff(airyai(z), z, 2)
    z*airyai(z)

    Series expansion is also supported:

    >>> from sympy import series
    >>> series(airyai(z), z, 0, 3)
    3**(5/6)*gamma(1/3)/(6*pi) - 3**(1/6)*z*gamma(2/3)/(2*pi) + O(z**3)

    We can numerically evaluate the Airy function to arbitrary precision
    on the whole complex plane:

    >>> airyai(-2).evalf(50)
    0.22740742820168557599192443603787379946077222541710

    Rewrite Ai(z) in terms of hypergeometric functions:

    >>> from sympy import hyper
    >>> airyai(z).rewrite(hyper)
    -3**(2/3)*z*hyper((), (4/3,), z**3/9)/(3*gamma(1/3)) + 3**(1/3)*hyper((), (2/3,), z**3/9)/(3*gamma(2/3))

    See Also
    ========

    airybi: Airy function of the second kind.
    airyaiprime: Derivative of the Airy function of the first kind.
    airybiprime: Derivative of the Airy function of the second kind.

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Airy_function
    .. [2] http://dlmf.nist.gov/9
    .. [3] http://www.encyclopediaofmath.org/index.php/Airy_functions
    .. [4] http://mathworld.wolfram.com/AiryFunctions.html
    """

    nargs = 1
    unbranched = True

    @classmethod
    def eval(cls, arg):
        if arg.is_Number:
            if arg is S.NaN:
                return S.NaN
            elif arg is S.Infinity:
                return S.Zero
            elif arg is S.NegativeInfinity:
                return S.Zero
            elif arg is S.Zero:
                return S.One / (3**Rational(2, 3) * gamma(Rational(2, 3)))

    def fdiff(self, argindex=1):
        if argindex == 1:
            return airyaiprime(self.args[0])
        else:
            raise ArgumentIndexError(self, argindex)

    @staticmethod
    @cacheit
    def taylor_term(n, x, *previous_terms):
        if n < 0:
            return S.Zero
        else:
            x = sympify(x)
            if len(previous_terms) > 1:
                p = previous_terms[-1]
                return ((3**(S(1)/3)*x)**(-n)*(3**(S(1)/3)*x)**(n + 1)*sin(pi*(2*n/3 + S(4)/3))*factorial(n) *
                        gamma(n/3 + S(2)/3)/(sin(pi*(2*n/3 + S(2)/3))*factorial(n + 1)*gamma(n/3 + S(1)/3)) * p)
            else:
                return (S.One/(3**(S(2)/3)*pi) * gamma((n+S.One)/S(3)) * sin(2*pi*(n+S.One)/S(3)) /
                        factorial(n) * (root(3, 3)*x)**n)

    def _eval_rewrite_as_besselj(self, z, **kwargs):
        ot = Rational(1, 3)
        tt = Rational(2, 3)
        a = Pow(-z, Rational(3, 2))
        if re(z).is_negative:
            return ot*sqrt(-z) * (besselj(-ot, tt*a) + besselj(ot, tt*a))

    def _eval_rewrite_as_besseli(self, z, **kwargs):
        ot = Rational(1, 3)
        tt = Rational(2, 3)
        a = Pow(z, Rational(3, 2))
        if re(z).is_positive:
            return ot*sqrt(z) * (besseli(-ot, tt*a) - besseli(ot, tt*a))
        else:
            return ot*(Pow(a, ot)*besseli(-ot, tt*a) - z*Pow(a, -ot)*besseli(ot, tt*a))

    def _eval_rewrite_as_hyper(self, z, **kwargs):
        pf1 = S.One / (3**(S(2)/3)*gamma(S(2)/3))
        pf2 = z / (root(3, 3)*gamma(S(1)/3))
        return pf1 * hyper([], [S(2)/3], z**3/9) - pf2 * hyper([], [S(4)/3], z**3/9)

    def _eval_expand_func(self, **hints):
        arg = self.args[0]
        symbs = arg.free_symbols

        if len(symbs) == 1:
            z = symbs.pop()
            c = Wild("c", exclude=[z])
            d = Wild("d", exclude=[z])
            m = Wild("m", exclude=[z])
            n = Wild("n", exclude=[z])
            M = arg.match(c*(d*z**n)**m)
            if M is not None:
                m = M[m]
                # The transformation is given by 03.05.16.0001.01
                # http://functions.wolfram.com/Bessel-TypeFunctions/AiryAi/16/01/01/0001/
                if (3*m).is_integer:
                    c = M[c]
                    d = M[d]
                    n = M[n]
                    pf = (d * z**n)**m / (d**m * z**(m*n))
                    newarg = c * d**m * z**(m*n)
                    return S.Half * ((pf + S.One)*airyai(newarg) - (pf - S.One)/sqrt(3)*airybi(newarg))


class airybi(AiryBase):
    r"""
    The Airy function `\operatorname{Bi}` of the second kind.

    The Airy function `\operatorname{Bi}(z)` is defined to be the function
    satisfying Airy's differential equation

    .. math::
        \frac{\mathrm{d}^2 w(z)}{\mathrm{d}z^2} - z w(z) = 0.

    Equivalently, for real `z`

    .. math::
        \operatorname{Bi}(z) := \frac{1}{\pi}
                 \int_0^\infty
                   \exp\left(-\frac{t^3}{3} + z t\right)
                   + \sin\left(\frac{t^3}{3} + z t\right) \mathrm{d}t.

    Examples
    ========

    Create an Airy function object:

    >>> from sympy import airybi
    >>> from sympy.abc import z

    >>> airybi(z)
    airybi(z)

    Several special values are known:

    >>> airybi(0)
    3**(5/6)/(3*gamma(2/3))
    >>> from sympy import oo
    >>> airybi(oo)
    oo
    >>> airybi(-oo)
    0

    The Airy function obeys the mirror symmetry:

    >>> from sympy import conjugate
    >>> conjugate(airybi(z))
    airybi(conjugate(z))

    Differentiation with respect to z is supported:

    >>> from sympy import diff
    >>> diff(airybi(z), z)
    airybiprime(z)
    >>> diff(airybi(z), z, 2)
    z*airybi(z)

    Series expansion is also supported:

    >>> from sympy import series
    >>> series(airybi(z), z, 0, 3)
    3**(1/3)*gamma(1/3)/(2*pi) + 3**(2/3)*z*gamma(2/3)/(2*pi) + O(z**3)

    We can numerically evaluate the Airy function to arbitrary precision
    on the whole complex plane:

    >>> airybi(-2).evalf(50)
    -0.41230258795639848808323405461146104203453483447240

    Rewrite Bi(z) in terms of hypergeometric functions:

    >>> from sympy import hyper
    >>> airybi(z).rewrite(hyper)
    3**(1/6)*z*hyper((), (4/3,), z**3/9)/gamma(1/3) + 3**(5/6)*hyper((), (2/3,), z**3/9)/(3*gamma(2/3))

    See Also
    ========

    airyai: Airy function of the first kind.
    airyaiprime: Derivative of the Airy function of the first kind.
    airybiprime: Derivative of the Airy function of the second kind.

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Airy_function
    .. [2] http://dlmf.nist.gov/9
    .. [3] http://www.encyclopediaofmath.org/index.php/Airy_functions
    .. [4] http://mathworld.wolfram.com/AiryFunctions.html
    """

    nargs = 1
    unbranched = True

    @classmethod
    def eval(cls, arg):
        if arg.is_Number:
            if arg is S.NaN:
                return S.NaN
            elif arg is S.Infinity:
                return S.Infinity
            elif arg is S.NegativeInfinity:
                return S.Zero
            elif arg is S.Zero:
                return S.One / (3**Rational(1, 6) * gamma(Rational(2, 3)))

    def fdiff(self, argindex=1):
        if argindex == 1:
            return airybiprime(self.args[0])
        else:
            raise ArgumentIndexError(self, argindex)

    @staticmethod
    @cacheit
    def taylor_term(n, x, *previous_terms):
        if n < 0:
            return S.Zero
        else:
            x = sympify(x)
            if len(previous_terms) > 1:
                p = previous_terms[-1]
                return (3**(S(1)/3)*x * Abs(sin(2*pi*(n + S.One)/S(3))) * factorial((n - S.One)/S(3)) /
                        ((n + S.One) * Abs(cos(2*pi*(n + S.Half)/S(3))) * factorial((n - 2)/S(3))) * p)
            else:
                return (S.One/(root(3, 6)*pi) * gamma((n + S.One)/S(3)) * Abs(sin(2*pi*(n + S.One)/S(3))) /
                        factorial(n) * (root(3, 3)*x)**n)

    def _eval_rewrite_as_besselj(self, z, **kwargs):
        ot = Rational(1, 3)
        tt = Rational(2, 3)
        a = Pow(-z, Rational(3, 2))
        if re(z).is_negative:
            return sqrt(-z/3) * (besselj(-ot, tt*a) - besselj(ot, tt*a))

    def _eval_rewrite_as_besseli(self, z, **kwargs):
        ot = Rational(1, 3)
        tt = Rational(2, 3)
        a = Pow(z, Rational(3, 2))
        if re(z).is_positive:
            return sqrt(z)/sqrt(3) * (besseli(-ot, tt*a) + besseli(ot, tt*a))
        else:
            b = Pow(a, ot)
            c = Pow(a, -ot)
            return sqrt(ot)*(b*besseli(-ot, tt*a) + z*c*besseli(ot, tt*a))

    def _eval_rewrite_as_hyper(self, z, **kwargs):
        pf1 = S.One / (root(3, 6)*gamma(S(2)/3))
        pf2 = z*root(3, 6) / gamma(S(1)/3)
        return pf1 * hyper([], [S(2)/3], z**3/9) + pf2 * hyper([], [S(4)/3], z**3/9)

    def _eval_expand_func(self, **hints):
        arg = self.args[0]
        symbs = arg.free_symbols

        if len(symbs) == 1:
            z = symbs.pop()
            c = Wild("c", exclude=[z])
            d = Wild("d", exclude=[z])
            m = Wild("m", exclude=[z])
            n = Wild("n", exclude=[z])
            M = arg.match(c*(d*z**n)**m)
            if M is not None:
                m = M[m]
                # The transformation is given by 03.06.16.0001.01
                # http://functions.wolfram.com/Bessel-TypeFunctions/AiryBi/16/01/01/0001/
                if (3*m).is_integer:
                    c = M[c]
                    d = M[d]
                    n = M[n]
                    pf = (d * z**n)**m / (d**m * z**(m*n))
                    newarg = c * d**m * z**(m*n)
                    return S.Half * (sqrt(3)*(S.One - pf)*airyai(newarg) + (S.One + pf)*airybi(newarg))


class airyaiprime(AiryBase):
    r"""
    The derivative `\operatorname{Ai}^\prime` of the Airy function of the first kind.

    The Airy function `\operatorname{Ai}^\prime(z)` is defined to be the function

    .. math::
        \operatorname{Ai}^\prime(z) := \frac{\mathrm{d} \operatorname{Ai}(z)}{\mathrm{d} z}.

    Examples
    ========

    Create an Airy function object:

    >>> from sympy import airyaiprime
    >>> from sympy.abc import z

    >>> airyaiprime(z)
    airyaiprime(z)

    Several special values are known:

    >>> airyaiprime(0)
    -3**(2/3)/(3*gamma(1/3))
    >>> from sympy import oo
    >>> airyaiprime(oo)
    0

    The Airy function obeys the mirror symmetry:

    >>> from sympy import conjugate
    >>> conjugate(airyaiprime(z))
    airyaiprime(conjugate(z))

    Differentiation with respect to z is supported:

    >>> from sympy import diff
    >>> diff(airyaiprime(z), z)
    z*airyai(z)
    >>> diff(airyaiprime(z), z, 2)
    z*airyaiprime(z) + airyai(z)

    Series expansion is also supported:

    >>> from sympy import series
    >>> series(airyaiprime(z), z, 0, 3)
    -3**(2/3)/(3*gamma(1/3)) + 3**(1/3)*z**2/(6*gamma(2/3)) + O(z**3)

    We can numerically evaluate the Airy function to arbitrary precision
    on the whole complex plane:

    >>> airyaiprime(-2).evalf(50)
    0.61825902074169104140626429133247528291577794512415

    Rewrite Ai'(z) in terms of hypergeometric functions:

    >>> from sympy import hyper
    >>> airyaiprime(z).rewrite(hyper)
    3**(1/3)*z**2*hyper((), (5/3,), z**3/9)/(6*gamma(2/3)) - 3**(2/3)*hyper((), (1/3,), z**3/9)/(3*gamma(1/3))

    See Also
    ========

    airyai: Airy function of the first kind.
    airybi: Airy function of the second kind.
    airybiprime: Derivative of the Airy function of the second kind.

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Airy_function
    .. [2] http://dlmf.nist.gov/9
    .. [3] http://www.encyclopediaofmath.org/index.php/Airy_functions
    .. [4] http://mathworld.wolfram.com/AiryFunctions.html
    """

    nargs = 1
    unbranched = True

    @classmethod
    def eval(cls, arg):
        if arg.is_Number:
            if arg is S.NaN:
                return S.NaN
            elif arg is S.Infinity:
                return S.Zero
            elif arg is S.Zero:
                return -S.One / (3**Rational(1, 3) * gamma(Rational(1, 3)))

    def fdiff(self, argindex=1):
        if argindex == 1:
            return self.args[0]*airyai(self.args[0])
        else:
            raise ArgumentIndexError(self, argindex)

    def _eval_evalf(self, prec):
        from mpmath import mp, workprec
        from sympy import Expr
        z = self.args[0]._to_mpmath(prec)
        with workprec(prec):
            res = mp.airyai(z, derivative=1)
        return Expr._from_mpmath(res, prec)

    def _eval_rewrite_as_besselj(self, z, **kwargs):
        tt = Rational(2, 3)
        a = Pow(-z, Rational(3, 2))
        if re(z).is_negative:
            return z/3 * (besselj(-tt, tt*a) - besselj(tt, tt*a))

    def _eval_rewrite_as_besseli(self, z, **kwargs):
        ot = Rational(1, 3)
        tt = Rational(2, 3)
        a = tt * Pow(z, Rational(3, 2))
        if re(z).is_positive:
            return z/3 * (besseli(tt, a) - besseli(-tt, a))
        else:
            a = Pow(z, Rational(3, 2))
            b = Pow(a, tt)
            c = Pow(a, -tt)
            return ot * (z**2*c*besseli(tt, tt*a) - b*besseli(-ot, tt*a))

    def _eval_rewrite_as_hyper(self, z, **kwargs):
        pf1 = z**2 / (2*3**(S(2)/3)*gamma(S(2)/3))
        pf2 = 1 / (root(3, 3)*gamma(S(1)/3))
        return pf1 * hyper([], [S(5)/3], z**3/9) - pf2 * hyper([], [S(1)/3], z**3/9)

    def _eval_expand_func(self, **hints):
        arg = self.args[0]
        symbs = arg.free_symbols

        if len(symbs) == 1:
            z = symbs.pop()
            c = Wild("c", exclude=[z])
            d = Wild("d", exclude=[z])
            m = Wild("m", exclude=[z])
            n = Wild("n", exclude=[z])
            M = arg.match(c*(d*z**n)**m)
            if M is not None:
                m = M[m]
                # The transformation is in principle
                # given by 03.07.16.0001.01 but note
                # that there is an error in this formula.
                # http://functions.wolfram.com/Bessel-TypeFunctions/AiryAiPrime/16/01/01/0001/
                if (3*m).is_integer:
                    c = M[c]
                    d = M[d]
                    n = M[n]
                    pf = (d**m * z**(n*m)) / (d * z**n)**m
                    newarg = c * d**m * z**(n*m)
                    return S.Half * ((pf + S.One)*airyaiprime(newarg) + (pf - S.One)/sqrt(3)*airybiprime(newarg))


class airybiprime(AiryBase):
    r"""
    The derivative `\operatorname{Bi}^\prime` of the Airy function of the first kind.

    The Airy function `\operatorname{Bi}^\prime(z)` is defined to be the function

    .. math::
        \operatorname{Bi}^\prime(z) := \frac{\mathrm{d} \operatorname{Bi}(z)}{\mathrm{d} z}.

    Examples
    ========

    Create an Airy function object:

    >>> from sympy import airybiprime
    >>> from sympy.abc import z

    >>> airybiprime(z)
    airybiprime(z)

    Several special values are known:

    >>> airybiprime(0)
    3**(1/6)/gamma(1/3)
    >>> from sympy import oo
    >>> airybiprime(oo)
    oo
    >>> airybiprime(-oo)
    0

    The Airy function obeys the mirror symmetry:

    >>> from sympy import conjugate
    >>> conjugate(airybiprime(z))
    airybiprime(conjugate(z))

    Differentiation with respect to z is supported:

    >>> from sympy import diff
    >>> diff(airybiprime(z), z)
    z*airybi(z)
    >>> diff(airybiprime(z), z, 2)
    z*airybiprime(z) + airybi(z)

    Series expansion is also supported:

    >>> from sympy import series
    >>> series(airybiprime(z), z, 0, 3)
    3**(1/6)/gamma(1/3) + 3**(5/6)*z**2/(6*gamma(2/3)) + O(z**3)

    We can numerically evaluate the Airy function to arbitrary precision
    on the whole complex plane:

    >>> airybiprime(-2).evalf(50)
    0.27879516692116952268509756941098324140300059345163

    Rewrite Bi'(z) in terms of hypergeometric functions:

    >>> from sympy import hyper
    >>> airybiprime(z).rewrite(hyper)
    3**(5/6)*z**2*hyper((), (5/3,), z**3/9)/(6*gamma(2/3)) + 3**(1/6)*hyper((), (1/3,), z**3/9)/gamma(1/3)

    See Also
    ========

    airyai: Airy function of the first kind.
    airybi: Airy function of the second kind.
    airyaiprime: Derivative of the Airy function of the first kind.

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Airy_function
    .. [2] http://dlmf.nist.gov/9
    .. [3] http://www.encyclopediaofmath.org/index.php/Airy_functions
    .. [4] http://mathworld.wolfram.com/AiryFunctions.html
    """

    nargs = 1
    unbranched = True

    @classmethod
    def eval(cls, arg):
        if arg.is_Number:
            if arg is S.NaN:
                return S.NaN
            elif arg is S.Infinity:
                return S.Infinity
            elif arg is S.NegativeInfinity:
                return S.Zero
            elif arg is S.Zero:
                return 3**Rational(1, 6) / gamma(Rational(1, 3))

    def fdiff(self, argindex=1):
        if argindex == 1:
            return self.args[0]*airybi(self.args[0])
        else:
            raise ArgumentIndexError(self, argindex)

    def _eval_evalf(self, prec):
        from mpmath import mp, workprec
        from sympy import Expr
        z = self.args[0]._to_mpmath(prec)
        with workprec(prec):
            res = mp.airybi(z, derivative=1)
        return Expr._from_mpmath(res, prec)

    def _eval_rewrite_as_besselj(self, z, **kwargs):
        tt = Rational(2, 3)
        a = tt * Pow(-z, Rational(3, 2))
        if re(z).is_negative:
            return -z/sqrt(3) * (besselj(-tt, a) + besselj(tt, a))

    def _eval_rewrite_as_besseli(self, z, **kwargs):
        ot = Rational(1, 3)
        tt = Rational(2, 3)
        a = tt * Pow(z, Rational(3, 2))
        if re(z).is_positive:
            return z/sqrt(3) * (besseli(-tt, a) + besseli(tt, a))
        else:
            a = Pow(z, Rational(3, 2))
            b = Pow(a, tt)
            c = Pow(a, -tt)
            return sqrt(ot) * (b*besseli(-tt, tt*a) + z**2*c*besseli(tt, tt*a))

    def _eval_rewrite_as_hyper(self, z, **kwargs):
        pf1 = z**2 / (2*root(3, 6)*gamma(S(2)/3))
        pf2 = root(3, 6) / gamma(S(1)/3)
        return pf1 * hyper([], [S(5)/3], z**3/9) + pf2 * hyper([], [S(1)/3], z**3/9)

    def _eval_expand_func(self, **hints):
        arg = self.args[0]
        symbs = arg.free_symbols

        if len(symbs) == 1:
            z = symbs.pop()
            c = Wild("c", exclude=[z])
            d = Wild("d", exclude=[z])
            m = Wild("m", exclude=[z])
            n = Wild("n", exclude=[z])
            M = arg.match(c*(d*z**n)**m)
            if M is not None:
                m = M[m]
                # The transformation is in principle
                # given by 03.08.16.0001.01 but note
                # that there is an error in this formula.
                # http://functions.wolfram.com/Bessel-TypeFunctions/AiryBiPrime/16/01/01/0001/
                if (3*m).is_integer:
                    c = M[c]
                    d = M[d]
                    n = M[n]
                    pf = (d**m * z**(n*m)) / (d * z**n)**m
                    newarg = c * d**m * z**(n*m)
                    return S.Half * (sqrt(3)*(pf - S.One)*airyaiprime(newarg) + (pf + S.One)*airybiprime(newarg))
