""" Elliptic integrals. """

from __future__ import print_function, division

from sympy.core import S, pi, I
from sympy.core.function import Function, ArgumentIndexError
from sympy.functions.elementary.complexes import sign
from sympy.functions.elementary.hyperbolic import atanh
from sympy.functions.elementary.miscellaneous import sqrt
from sympy.functions.elementary.trigonometric import sin, tan
from sympy.functions.special.gamma_functions import gamma
from sympy.functions.special.hyper import hyper, meijerg

class elliptic_k(Function):
    r"""
    The complete elliptic integral of the first kind, defined by

    .. math:: K(m) = F\left(\tfrac{\pi}{2}\middle| m\right)

    where `F\left(z\middle| m\right)` is the Legendre incomplete
    elliptic integral of the first kind.

    The function `K(m)` is a single-valued function on the complex
    plane with branch cut along the interval `(1, \infty)`.

    Note that our notation defines the incomplete elliptic integral
    in terms of the parameter `m` instead of the elliptic modulus
    (eccentricity) `k`.
    In this case, the parameter `m` is defined as `m=k^2`.

    Examples
    ========

    >>> from sympy import elliptic_k, I, pi
    >>> from sympy.abc import m
    >>> elliptic_k(0)
    pi/2
    >>> elliptic_k(1.0 + I)
    1.50923695405127 + 0.625146415202697*I
    >>> elliptic_k(m).series(n=3)
    pi/2 + pi*m/8 + 9*pi*m**2/128 + O(m**3)

    See Also
    ========

    elliptic_f

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Elliptic_integrals
    .. [2] http://functions.wolfram.com/EllipticIntegrals/EllipticK

    """

    @classmethod
    def eval(cls, m):
        if m is S.Zero:
            return pi/2
        elif m is S.Half:
            return 8*pi**(S(3)/2)/gamma(-S(1)/4)**2
        elif m is S.One:
            return S.ComplexInfinity
        elif m is S.NegativeOne:
            return gamma(S(1)/4)**2/(4*sqrt(2*pi))
        elif m in (S.Infinity, S.NegativeInfinity, I*S.Infinity,
                   I*S.NegativeInfinity, S.ComplexInfinity):
            return S.Zero

    def fdiff(self, argindex=1):
        m = self.args[0]
        return (elliptic_e(m) - (1 - m)*elliptic_k(m))/(2*m*(1 - m))

    def _eval_conjugate(self):
        m = self.args[0]
        if (m.is_real and (m - 1).is_positive) is False:
            return self.func(m.conjugate())

    def _eval_nseries(self, x, n, logx):
        from sympy.simplify import hyperexpand
        return hyperexpand(self.rewrite(hyper)._eval_nseries(x, n=n, logx=logx))

    def _eval_rewrite_as_hyper(self, m, **kwargs):
        return (pi/2)*hyper((S.Half, S.Half), (S.One,), m)

    def _eval_rewrite_as_meijerg(self, m, **kwargs):
        return meijerg(((S.Half, S.Half), []), ((S.Zero,), (S.Zero,)), -m)/2

    def _sage_(self):
        import sage.all as sage
        return sage.elliptic_kc(self.args[0]._sage_())


class elliptic_f(Function):
    r"""
    The Legendre incomplete elliptic integral of the first
    kind, defined by

    .. math:: F\left(z\middle| m\right) =
              \int_0^z \frac{dt}{\sqrt{1 - m \sin^2 t}}

    This function reduces to a complete elliptic integral of
    the first kind, `K(m)`, when `z = \pi/2`.

    Note that our notation defines the incomplete elliptic integral
    in terms of the parameter `m` instead of the elliptic modulus
    (eccentricity) `k`.
    In this case, the parameter `m` is defined as `m=k^2`.

    Examples
    ========

    >>> from sympy import elliptic_f, I, O
    >>> from sympy.abc import z, m
    >>> elliptic_f(z, m).series(z)
    z + z**5*(3*m**2/40 - m/30) + m*z**3/6 + O(z**6)
    >>> elliptic_f(3.0 + I/2, 1.0 + I)
    2.909449841483 + 1.74720545502474*I

    See Also
    ========

    elliptic_k

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Elliptic_integrals
    .. [2] http://functions.wolfram.com/EllipticIntegrals/EllipticF

    """

    @classmethod
    def eval(cls, z, m):
        k = 2*z/pi
        if m.is_zero:
            return z
        elif z.is_zero:
            return S.Zero
        elif k.is_integer:
            return k*elliptic_k(m)
        elif m in (S.Infinity, S.NegativeInfinity):
            return S.Zero
        elif z.could_extract_minus_sign():
            return -elliptic_f(-z, m)

    def fdiff(self, argindex=1):
        z, m = self.args
        fm = sqrt(1 - m*sin(z)**2)
        if argindex == 1:
            return 1/fm
        elif argindex == 2:
            return (elliptic_e(z, m)/(2*m*(1 - m)) - elliptic_f(z, m)/(2*m) -
                    sin(2*z)/(4*(1 - m)*fm))
        raise ArgumentIndexError(self, argindex)

    def _eval_conjugate(self):
        z, m = self.args
        if (m.is_real and (m - 1).is_positive) is False:
            return self.func(z.conjugate(), m.conjugate())


class elliptic_e(Function):
    r"""
    Called with two arguments `z` and `m`, evaluates the
    incomplete elliptic integral of the second kind, defined by

    .. math:: E\left(z\middle| m\right) = \int_0^z \sqrt{1 - m \sin^2 t} dt

    Called with a single argument `m`, evaluates the Legendre complete
    elliptic integral of the second kind

    .. math:: E(m) = E\left(\tfrac{\pi}{2}\middle| m\right)

    The function `E(m)` is a single-valued function on the complex
    plane with branch cut along the interval `(1, \infty)`.

    Note that our notation defines the incomplete elliptic integral
    in terms of the parameter `m` instead of the elliptic modulus
    (eccentricity) `k`.
    In this case, the parameter `m` is defined as `m=k^2`.

    Examples
    ========

    >>> from sympy import elliptic_e, I, pi, O
    >>> from sympy.abc import z, m
    >>> elliptic_e(z, m).series(z)
    z + z**5*(-m**2/40 + m/30) - m*z**3/6 + O(z**6)
    >>> elliptic_e(m).series(n=4)
    pi/2 - pi*m/8 - 3*pi*m**2/128 - 5*pi*m**3/512 + O(m**4)
    >>> elliptic_e(1 + I, 2 - I/2).n()
    1.55203744279187 + 0.290764986058437*I
    >>> elliptic_e(0)
    pi/2
    >>> elliptic_e(2.0 - I)
    0.991052601328069 + 0.81879421395609*I

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Elliptic_integrals
    .. [2] http://functions.wolfram.com/EllipticIntegrals/EllipticE2
    .. [3] http://functions.wolfram.com/EllipticIntegrals/EllipticE

    """

    @classmethod
    def eval(cls, m, z=None):
        if z is not None:
            z, m = m, z
            k = 2*z/pi
            if m.is_zero:
                return z
            if z.is_zero:
                return S.Zero
            elif k.is_integer:
                return k*elliptic_e(m)
            elif m in (S.Infinity, S.NegativeInfinity):
                return S.ComplexInfinity
            elif z.could_extract_minus_sign():
                return -elliptic_e(-z, m)
        else:
            if m.is_zero:
                return pi/2
            elif m is S.One:
                return S.One
            elif m is S.Infinity:
                return I*S.Infinity
            elif m is S.NegativeInfinity:
                return S.Infinity
            elif m is S.ComplexInfinity:
                return S.ComplexInfinity

    def fdiff(self, argindex=1):
        if len(self.args) == 2:
            z, m = self.args
            if argindex == 1:
                return sqrt(1 - m*sin(z)**2)
            elif argindex == 2:
                return (elliptic_e(z, m) - elliptic_f(z, m))/(2*m)
        else:
            m = self.args[0]
            if argindex == 1:
                return (elliptic_e(m) - elliptic_k(m))/(2*m)
        raise ArgumentIndexError(self, argindex)

    def _eval_conjugate(self):
        if len(self.args) == 2:
            z, m = self.args
            if (m.is_real and (m - 1).is_positive) is False:
                return self.func(z.conjugate(), m.conjugate())
        else:
            m = self.args[0]
            if (m.is_real and (m - 1).is_positive) is False:
                return self.func(m.conjugate())

    def _eval_nseries(self, x, n, logx):
        from sympy.simplify import hyperexpand
        if len(self.args) == 1:
            return hyperexpand(self.rewrite(hyper)._eval_nseries(x, n=n, logx=logx))
        return super(elliptic_e, self)._eval_nseries(x, n=n, logx=logx)

    def _eval_rewrite_as_hyper(self, *args, **kwargs):
        if len(args) == 1:
            m = args[0]
            return (pi/2)*hyper((-S.Half, S.Half), (S.One,), m)

    def _eval_rewrite_as_meijerg(self, *args, **kwargs):
        if len(args) == 1:
            m = args[0]
            return -meijerg(((S.Half, S(3)/2), []), \
                            ((S.Zero,), (S.Zero,)), -m)/4


class elliptic_pi(Function):
    r"""
    Called with three arguments `n`, `z` and `m`, evaluates the
    Legendre incomplete elliptic integral of the third kind, defined by

    .. math:: \Pi\left(n; z\middle| m\right) = \int_0^z \frac{dt}
              {\left(1 - n \sin^2 t\right) \sqrt{1 - m \sin^2 t}}

    Called with two arguments `n` and `m`, evaluates the complete
    elliptic integral of the third kind:

    .. math:: \Pi\left(n\middle| m\right) =
              \Pi\left(n; \tfrac{\pi}{2}\middle| m\right)

    Note that our notation defines the incomplete elliptic integral
    in terms of the parameter `m` instead of the elliptic modulus
    (eccentricity) `k`.
    In this case, the parameter `m` is defined as `m=k^2`.

    Examples
    ========

    >>> from sympy import elliptic_pi, I, pi, O, S
    >>> from sympy.abc import z, n, m
    >>> elliptic_pi(n, z, m).series(z, n=4)
    z + z**3*(m/6 + n/3) + O(z**4)
    >>> elliptic_pi(0.5 + I, 1.0 - I, 1.2)
    2.50232379629182 - 0.760939574180767*I
    >>> elliptic_pi(0, 0)
    pi/2
    >>> elliptic_pi(1.0 - I/3, 2.0 + I)
    3.29136443417283 + 0.32555634906645*I

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Elliptic_integrals
    .. [2] http://functions.wolfram.com/EllipticIntegrals/EllipticPi3
    .. [3] http://functions.wolfram.com/EllipticIntegrals/EllipticPi

    """

    @classmethod
    def eval(cls, n, m, z=None):
        if z is not None:
            n, z, m = n, m, z
            k = 2*z/pi
            if n == S.Zero:
                return elliptic_f(z, m)
            elif n == S.One:
                return (elliptic_f(z, m) +
                        (sqrt(1 - m*sin(z)**2)*tan(z) -
                         elliptic_e(z, m))/(1 - m))
            elif k.is_integer:
                return k*elliptic_pi(n, m)
            elif m == S.Zero:
                return atanh(sqrt(n - 1)*tan(z))/sqrt(n - 1)
            elif n == m:
                return (elliptic_f(z, n) - elliptic_pi(1, z, n) +
                        tan(z)/sqrt(1 - n*sin(z)**2))
            elif n in (S.Infinity, S.NegativeInfinity):
                return S.Zero
            elif m in (S.Infinity, S.NegativeInfinity):
                return S.Zero
            elif z.could_extract_minus_sign():
                return -elliptic_pi(n, -z, m)
        else:
            if n == S.Zero:
                return elliptic_k(m)
            elif n == S.One:
                return S.ComplexInfinity
            elif m == S.Zero:
                return pi/(2*sqrt(1 - n))
            elif m == S.One:
                return -S.Infinity/sign(n - 1)
            elif n == m:
                return elliptic_e(n)/(1 - n)
            elif n in (S.Infinity, S.NegativeInfinity):
                return S.Zero
            elif m in (S.Infinity, S.NegativeInfinity):
                return S.Zero

    def _eval_conjugate(self):
        if len(self.args) == 3:
            n, z, m = self.args
            if (n.is_real and (n - 1).is_positive) is False and \
               (m.is_real and (m - 1).is_positive) is False:
                return self.func(n.conjugate(), z.conjugate(), m.conjugate())
        else:
            n, m = self.args
            return self.func(n.conjugate(), m.conjugate())

    def fdiff(self, argindex=1):
        if len(self.args) == 3:
            n, z, m = self.args
            fm, fn = sqrt(1 - m*sin(z)**2), 1 - n*sin(z)**2
            if argindex == 1:
                return (elliptic_e(z, m) + (m - n)*elliptic_f(z, m)/n +
                        (n**2 - m)*elliptic_pi(n, z, m)/n -
                        n*fm*sin(2*z)/(2*fn))/(2*(m - n)*(n - 1))
            elif argindex == 2:
                return 1/(fm*fn)
            elif argindex == 3:
                return (elliptic_e(z, m)/(m - 1) +
                        elliptic_pi(n, z, m) -
                        m*sin(2*z)/(2*(m - 1)*fm))/(2*(n - m))
        else:
            n, m = self.args
            if argindex == 1:
                return (elliptic_e(m) + (m - n)*elliptic_k(m)/n +
                        (n**2 - m)*elliptic_pi(n, m)/n)/(2*(m - n)*(n - 1))
            elif argindex == 2:
                return (elliptic_e(m)/(m - 1) + elliptic_pi(n, m))/(2*(n - m))
        raise ArgumentIndexError(self, argindex)
