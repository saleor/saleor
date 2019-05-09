"""Curves in 2-dimensional Euclidean space.

Contains
========
Curve

"""

from __future__ import division, print_function

from sympy import sqrt
from sympy.core import sympify, diff
from sympy.core.compatibility import is_sequence
from sympy.core.containers import Tuple
from sympy.core.symbol import _symbol
from sympy.geometry.entity import GeometryEntity, GeometrySet
from sympy.geometry.point import Point
from sympy.integrals import integrate


class Curve(GeometrySet):
    """A curve in space.

    A curve is defined by parametric functions for the coordinates, a
    parameter and the lower and upper bounds for the parameter value.

    Parameters
    ==========

    function : list of functions
    limits : 3-tuple
        Function parameter and lower and upper bounds.

    Attributes
    ==========

    functions
    parameter
    limits

    Raises
    ======

    ValueError
        When `functions` are specified incorrectly.
        When `limits` are specified incorrectly.

    See Also
    ========

    sympy.core.function.Function
    sympy.polys.polyfuncs.interpolate

    Examples
    ========

    >>> from sympy import sin, cos, Symbol, interpolate
    >>> from sympy.abc import t, a
    >>> from sympy.geometry import Curve
    >>> C = Curve((sin(t), cos(t)), (t, 0, 2))
    >>> C.functions
    (sin(t), cos(t))
    >>> C.limits
    (t, 0, 2)
    >>> C.parameter
    t
    >>> C = Curve((t, interpolate([1, 4, 9, 16], t)), (t, 0, 1)); C
    Curve((t, t**2), (t, 0, 1))
    >>> C.subs(t, 4)
    Point2D(4, 16)
    >>> C.arbitrary_point(a)
    Point2D(a, a**2)
    """

    def __new__(cls, function, limits):
        fun = sympify(function)
        if not is_sequence(fun) or len(fun) != 2:
            raise ValueError("Function argument should be (x(t), y(t)) "
                "but got %s" % str(function))
        if not is_sequence(limits) or len(limits) != 3:
            raise ValueError("Limit argument should be (t, tmin, tmax) "
                "but got %s" % str(limits))

        return GeometryEntity.__new__(cls, Tuple(*fun), Tuple(*limits))

    def _eval_subs(self, old, new):
        if old == self.parameter:
            return Point(*[f.subs(old, new) for f in self.functions])

    def arbitrary_point(self, parameter='t'):
        """
        A parameterized point on the curve.

        Parameters
        ==========

        parameter : str or Symbol, optional
            Default value is 't';
            the Curve's parameter is selected with None or self.parameter
            otherwise the provided symbol is used.

        Returns
        =======

        arbitrary_point : Point

        Raises
        ======

        ValueError
            When `parameter` already appears in the functions.

        See Also
        ========

        sympy.geometry.point.Point

        Examples
        ========

        >>> from sympy import Symbol
        >>> from sympy.abc import s
        >>> from sympy.geometry import Curve
        >>> C = Curve([2*s, s**2], (s, 0, 2))
        >>> C.arbitrary_point()
        Point2D(2*t, t**2)
        >>> C.arbitrary_point(C.parameter)
        Point2D(2*s, s**2)
        >>> C.arbitrary_point(None)
        Point2D(2*s, s**2)
        >>> C.arbitrary_point(Symbol('a'))
        Point2D(2*a, a**2)

        """
        if parameter is None:
            return Point(*self.functions)

        tnew = _symbol(parameter, self.parameter, real=True)
        t = self.parameter
        if (tnew.name != t.name and
                tnew.name in (f.name for f in self.free_symbols)):
            raise ValueError('Symbol %s already appears in object '
                'and cannot be used as a parameter.' % tnew.name)
        return Point(*[w.subs(t, tnew) for w in self.functions])

    @property
    def free_symbols(self):
        """
        Return a set of symbols other than the bound symbols used to
        parametrically define the Curve.

        Examples
        ========

        >>> from sympy.abc import t, a
        >>> from sympy.geometry import Curve
        >>> Curve((t, t**2), (t, 0, 2)).free_symbols
        set()
        >>> Curve((t, t**2), (t, a, 2)).free_symbols
        {a}
        """
        free = set()
        for a in self.functions + self.limits[1:]:
            free |= a.free_symbols
        free = free.difference({self.parameter})
        return free

    @property
    def ambient_dimension(self):
        return len(self.args[0])

    @property
    def functions(self):
        """The functions specifying the curve.

        Returns
        =======

        functions : list of parameterized coordinate functions.

        See Also
        ========

        parameter

        Examples
        ========

        >>> from sympy.abc import t
        >>> from sympy.geometry import Curve
        >>> C = Curve((t, t**2), (t, 0, 2))
        >>> C.functions
        (t, t**2)

        """
        return self.args[0]

    @property
    def limits(self):
        """The limits for the curve.

        Returns
        =======

        limits : tuple
            Contains parameter and lower and upper limits.

        See Also
        ========

        plot_interval

        Examples
        ========

        >>> from sympy.abc import t
        >>> from sympy.geometry import Curve
        >>> C = Curve([t, t**3], (t, -2, 2))
        >>> C.limits
        (t, -2, 2)

        """
        return self.args[1]

    @property
    def parameter(self):
        """The curve function variable.

        Returns
        =======

        parameter : SymPy symbol

        See Also
        ========

        functions

        Examples
        ========

        >>> from sympy.abc import t
        >>> from sympy.geometry import Curve
        >>> C = Curve([t, t**2], (t, 0, 2))
        >>> C.parameter
        t

        """
        return self.args[1][0]

    @property
    def length(self):
        """The curve length.

        Examples
        ========

        >>> from sympy.geometry.curve import Curve
        >>> from sympy import cos, sin
        >>> from sympy.abc import t
        >>> Curve((t, t), (t, 0, 1)).length
        sqrt(2)
        """
        integrand = sqrt(sum(diff(func, self.limits[0])**2 for func in self.functions))
        return integrate(integrand, self.limits)

    def plot_interval(self, parameter='t'):
        """The plot interval for the default geometric plot of the curve.

        Parameters
        ==========

        parameter : str or Symbol, optional
            Default value is 't';
            otherwise the provided symbol is used.

        Returns
        =======

        plot_interval : list (plot interval)
            [parameter, lower_bound, upper_bound]

        See Also
        ========

        limits : Returns limits of the parameter interval

        Examples
        ========

        >>> from sympy import Curve, sin
        >>> from sympy.abc import x, t, s
        >>> Curve((x, sin(x)), (x, 1, 2)).plot_interval()
        [t, 1, 2]
        >>> Curve((x, sin(x)), (x, 1, 2)).plot_interval(s)
        [s, 1, 2]

        """
        t = _symbol(parameter, self.parameter, real=True)
        return [t] + list(self.limits[1:])

    def rotate(self, angle=0, pt=None):
        """Rotate ``angle`` radians counterclockwise about Point ``pt``.

        The default pt is the origin, Point(0, 0).

        Examples
        ========

        >>> from sympy.geometry.curve import Curve
        >>> from sympy.abc import x
        >>> from sympy import pi
        >>> Curve((x, x), (x, 0, 1)).rotate(pi/2)
        Curve((-x, x), (x, 0, 1))
        """
        from sympy.matrices import Matrix, rot_axis3
        if pt:
            pt = -Point(pt, dim=2)
        else:
            pt = Point(0,0)
        rv = self.translate(*pt.args)
        f = list(rv.functions)
        f.append(0)
        f = Matrix(1, 3, f)
        f *= rot_axis3(angle)
        rv = self.func(f[0, :2].tolist()[0], self.limits)
        if pt is not None:
            pt = -pt
            return rv.translate(*pt.args)
        return rv

    def scale(self, x=1, y=1, pt=None):
        """Override GeometryEntity.scale since Curve is not made up of Points.

        Examples
        ========

        >>> from sympy.geometry.curve import Curve
        >>> from sympy import pi
        >>> from sympy.abc import x
        >>> Curve((x, x), (x, 0, 1)).scale(2)
        Curve((2*x, x), (x, 0, 1))
        """
        if pt:
            pt = Point(pt, dim=2)
            return self.translate(*(-pt).args).scale(x, y).translate(*pt.args)
        fx, fy = self.functions
        return self.func((fx*x, fy*y), self.limits)

    def translate(self, x=0, y=0):
        """Translate the Curve by (x, y).

        Examples
        ========

        >>> from sympy.geometry.curve import Curve
        >>> from sympy import pi
        >>> from sympy.abc import x
        >>> Curve((x, x), (x, 0, 1)).translate(1, 2)
        Curve((x + 1, x + 2), (x, 0, 1))
        """
        fx, fy = self.functions
        return self.func((fx + x, fy + y), self.limits)
