"""
This module has all the classes and functions related to waves in optics.

**Contains**

* TWave
"""

from __future__ import print_function, division

__all__ = ['TWave']

from sympy import (sympify, pi, sin, cos, sqrt, Symbol, S,
    symbols, Derivative, atan2)
from sympy.core.expr import Expr
from sympy.physics.units import speed_of_light, meter, second


c = speed_of_light.convert_to(meter/second)


class TWave(Expr):

    r"""
    This is a simple transverse sine wave travelling in a one-dimensional space.
    Basic properties are required at the time of creation of the object,
    but they can be changed later with respective methods provided.

    It is represented as :math:`A \times cos(k*x - \omega \times t + \phi )`,
    where :math:`A` is the amplitude, :math:`\omega` is the angular velocity,
    :math:`k` is the wavenumber (spatial frequency), :math:`x` is a spatial variable
    to represent the position on the dimension on which the wave propagates,
    and :math:`\phi` is the phase angle of the wave.


    Arguments
    =========

    amplitude : Sympifyable
        Amplitude of the wave.
    frequency : Sympifyable
        Frequency of the wave.
    phase : Sympifyable
        Phase angle of the wave.
    time_period : Sympifyable
        Time period of the wave.
    n : Sympifyable
        Refractive index of the medium.

    Raises
    =======

    ValueError : When neither frequency nor time period is provided
        or they are not consistent.
    TypeError : When anything other than TWave objects is added.


    Examples
    ========

    >>> from sympy import symbols
    >>> from sympy.physics.optics import TWave
    >>> A1, phi1, A2, phi2, f = symbols('A1, phi1, A2, phi2, f')
    >>> w1 = TWave(A1, f, phi1)
    >>> w2 = TWave(A2, f, phi2)
    >>> w3 = w1 + w2  # Superposition of two waves
    >>> w3
    TWave(sqrt(A1**2 + 2*A1*A2*cos(phi1 - phi2) + A2**2), f,
        atan2(A1*cos(phi1) + A2*cos(phi2), A1*sin(phi1) + A2*sin(phi2)))
    >>> w3.amplitude
    sqrt(A1**2 + 2*A1*A2*cos(phi1 - phi2) + A2**2)
    >>> w3.phase
    atan2(A1*cos(phi1) + A2*cos(phi2), A1*sin(phi1) + A2*sin(phi2))
    >>> w3.speed
    299792458*meter/(second*n)
    >>> w3.angular_velocity
    2*pi*f

    """

    def __init__(
            self,
            amplitude,
            frequency=None,
            phase=S.Zero,
            time_period=None,
            n=Symbol('n')):
        frequency = sympify(frequency)
        amplitude = sympify(amplitude)
        phase = sympify(phase)
        time_period = sympify(time_period)
        n = sympify(n)
        self._frequency = frequency
        self._amplitude = amplitude
        self._phase = phase
        self._time_period = time_period
        self._n = n
        if time_period is not None:
            self._frequency = 1/self._time_period
        if frequency is not None:
            self._time_period = 1/self._frequency
            if time_period is not None:
                if frequency != 1/time_period:
                    raise ValueError("frequency and time_period should be consistent.")
        if frequency is None and time_period is None:
            raise ValueError("Either frequency or time period is needed.")

    @property
    def frequency(self):
        """
        Returns the frequency of the wave,
        in cycles per second.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.optics import TWave
        >>> A, phi, f = symbols('A, phi, f')
        >>> w = TWave(A, f, phi)
        >>> w.frequency
        f
        """
        return self._frequency

    @property
    def time_period(self):
        """
        Returns the temporal period of the wave,
        in seconds per cycle.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.optics import TWave
        >>> A, phi, f = symbols('A, phi, f')
        >>> w = TWave(A, f, phi)
        >>> w.time_period
        1/f
        """
        return self._time_period

    @property
    def wavelength(self):
        """
        Returns the wavelength (spatial period) of the wave,
        in meters per cycle.
        It depends on the medium of the wave.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.optics import TWave
        >>> A, phi, f = symbols('A, phi, f')
        >>> w = TWave(A, f, phi)
        >>> w.wavelength
        299792458*meter/(second*f*n)
        """
        return c/(self._frequency*self._n)

    @property
    def amplitude(self):
        """
        Returns the amplitude of the wave.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.optics import TWave
        >>> A, phi, f = symbols('A, phi, f')
        >>> w = TWave(A, f, phi)
        >>> w.amplitude
        A
        """
        return self._amplitude

    @property
    def phase(self):
        """
        Returns the phase angle of the wave,
        in radians.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.optics import TWave
        >>> A, phi, f = symbols('A, phi, f')
        >>> w = TWave(A, f, phi)
        >>> w.phase
        phi
        """
        return self._phase

    @property
    def speed(self):
        """
        Returns the propagation speed of the wave,
        in meters per second.
        It is dependent on the propagation medium.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.optics import TWave
        >>> A, phi, f = symbols('A, phi, f')
        >>> w = TWave(A, f, phi)
        >>> w.speed
        299792458*meter/(second*n)
        """
        return self.wavelength*self._frequency

    @property
    def angular_velocity(self):
        """
        Returns the angular velocity of the wave,
        in radians per second.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.optics import TWave
        >>> A, phi, f = symbols('A, phi, f')
        >>> w = TWave(A, f, phi)
        >>> w.angular_velocity
        2*pi*f
        """
        return 2*pi*self._frequency

    @property
    def wavenumber(self):
        """
        Returns the wavenumber of the wave,
        in radians per meter.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.optics import TWave
        >>> A, phi, f = symbols('A, phi, f')
        >>> w = TWave(A, f, phi)
        >>> w.wavenumber
        pi*second*f*n/(149896229*meter)
        """
        return 2*pi/self.wavelength

    def __str__(self):
        """String representation of a TWave."""
        from sympy.printing import sstr
        return type(self).__name__ + sstr(self.args)

    __repr__ = __str__

    def __add__(self, other):
        """
        Addition of two waves will result in their superposition.
        The type of interference will depend on their phase angles.
        """
        if isinstance(other, TWave):
            if self._frequency == other._frequency and self.wavelength == other.wavelength:
                return TWave(sqrt(self._amplitude**2 + other._amplitude**2 + 2 *
                                  self.amplitude*other.amplitude*cos(
                                      self._phase - other.phase)),
                             self.frequency,
                             atan2(self._amplitude*cos(self._phase)
                             +other._amplitude*cos(other._phase),
                             self._amplitude*sin(self._phase)
                             +other._amplitude*sin(other._phase))
                             )
            else:
                raise NotImplementedError("Interference of waves with different frequencies"
                    " has not been implemented.")
        else:
            raise TypeError(type(other).__name__ + " and TWave objects can't be added.")

    def _eval_rewrite_as_sin(self, *args, **kwargs):
        return self._amplitude*sin(self.wavenumber*Symbol('x')
            - self.angular_velocity*Symbol('t') + self._phase + pi/2, evaluate=False)

    def _eval_rewrite_as_cos(self, *args, **kwargs):
        return self._amplitude*cos(self.wavenumber*Symbol('x')
            - self.angular_velocity*Symbol('t') + self._phase)

    def _eval_rewrite_as_pde(self, *args, **kwargs):
        from sympy import Function
        mu, epsilon, x, t = symbols('mu, epsilon, x, t')
        E = Function('E')
        return Derivative(E(x, t), x, 2) + mu*epsilon*Derivative(E(x, t), t, 2)

    def _eval_rewrite_as_exp(self, *args, **kwargs):
        from sympy import exp, I
        return self._amplitude*exp(I*(self.wavenumber*Symbol('x')
            - self.angular_velocity*Symbol('t') + self._phase))
