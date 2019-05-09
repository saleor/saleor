from __future__ import print_function, division

from sympy.core.backend import sympify
from sympy.core.compatibility import string_types
from sympy.physics.vector import Point

__all__ = ['Particle']


class Particle(object):
    """A particle.

    Particles have a non-zero mass and lack spatial extension; they take up no
    space.

    Values need to be supplied on initialization, but can be changed later.

    Parameters
    ==========
    name : str
        Name of particle
    point : Point
        A physics/mechanics Point which represents the position, velocity, and
        acceleration of this Particle
    mass : sympifyable
        A SymPy expression representing the Particle's mass

    Examples
    ========

    >>> from sympy.physics.mechanics import Particle, Point
    >>> from sympy import Symbol
    >>> po = Point('po')
    >>> m = Symbol('m')
    >>> pa = Particle('pa', po, m)
    >>> # Or you could change these later
    >>> pa.mass = m
    >>> pa.point = po

    """

    def __init__(self, name, point, mass):
        if not isinstance(name, string_types):
            raise TypeError('Supply a valid name.')
        self._name = name
        self.mass = mass
        self.point = point
        self.potential_energy = 0

    def __str__(self):
        return self._name

    __repr__ = __str__

    @property
    def mass(self):
        """Mass of the particle."""
        return self._mass

    @mass.setter
    def mass(self, value):
        self._mass = sympify(value)

    @property
    def point(self):
        """Point of the particle."""
        return self._point

    @point.setter
    def point(self, p):
        if not isinstance(p, Point):
            raise TypeError("Particle point attribute must be a Point object.")
        self._point = p

    def linear_momentum(self, frame):
        """Linear momentum of the particle.

        The linear momentum L, of a particle P, with respect to frame N is
        given by

        L = m * v

        where m is the mass of the particle, and v is the velocity of the
        particle in the frame N.

        Parameters
        ==========

        frame : ReferenceFrame
            The frame in which linear momentum is desired.

        Examples
        ========

        >>> from sympy.physics.mechanics import Particle, Point, ReferenceFrame
        >>> from sympy.physics.mechanics import dynamicsymbols
        >>> m, v = dynamicsymbols('m v')
        >>> N = ReferenceFrame('N')
        >>> P = Point('P')
        >>> A = Particle('A', P, m)
        >>> P.set_vel(N, v * N.x)
        >>> A.linear_momentum(N)
        m*v*N.x

        """

        return self.mass * self.point.vel(frame)

    def angular_momentum(self, point, frame):
        """Angular momentum of the particle about the point.

        The angular momentum H, about some point O of a particle, P, is given
        by:

        H = r x m * v

        where r is the position vector from point O to the particle P, m is
        the mass of the particle, and v is the velocity of the particle in
        the inertial frame, N.

        Parameters
        ==========

        point : Point
            The point about which angular momentum of the particle is desired.

        frame : ReferenceFrame
            The frame in which angular momentum is desired.

        Examples
        ========

        >>> from sympy.physics.mechanics import Particle, Point, ReferenceFrame
        >>> from sympy.physics.mechanics import dynamicsymbols
        >>> m, v, r = dynamicsymbols('m v r')
        >>> N = ReferenceFrame('N')
        >>> O = Point('O')
        >>> A = O.locatenew('A', r * N.x)
        >>> P = Particle('P', A, m)
        >>> P.point.set_vel(N, v * N.y)
        >>> P.angular_momentum(O, N)
        m*r*v*N.z

        """

        return self.point.pos_from(point) ^ (self.mass * self.point.vel(frame))

    def kinetic_energy(self, frame):
        """Kinetic energy of the particle

        The kinetic energy, T, of a particle, P, is given by

        'T = 1/2 m v^2'

        where m is the mass of particle P, and v is the velocity of the
        particle in the supplied ReferenceFrame.

        Parameters
        ==========

        frame : ReferenceFrame
            The Particle's velocity is typically defined with respect to
            an inertial frame but any relevant frame in which the velocity is
            known can be supplied.

        Examples
        ========

        >>> from sympy.physics.mechanics import Particle, Point, ReferenceFrame
        >>> from sympy import symbols
        >>> m, v, r = symbols('m v r')
        >>> N = ReferenceFrame('N')
        >>> O = Point('O')
        >>> P = Particle('P', O, m)
        >>> P.point.set_vel(N, v * N.y)
        >>> P.kinetic_energy(N)
        m*v**2/2

        """

        return (self.mass / sympify(2) * self.point.vel(frame) &
                self.point.vel(frame))

    @property
    def potential_energy(self):
        """The potential energy of the Particle.

        Examples
        ========

        >>> from sympy.physics.mechanics import Particle, Point
        >>> from sympy import symbols
        >>> m, g, h = symbols('m g h')
        >>> O = Point('O')
        >>> P = Particle('P', O, m)
        >>> P.potential_energy = m * g * h
        >>> P.potential_energy
        g*h*m

        """

        return self._pe

    @potential_energy.setter
    def potential_energy(self, scalar):
        """Used to set the potential energy of the Particle.

        Parameters
        ==========

        scalar : Sympifyable
            The potential energy (a scalar) of the Particle.

        Examples
        ========

        >>> from sympy.physics.mechanics import Particle, Point
        >>> from sympy import symbols
        >>> m, g, h = symbols('m g h')
        >>> O = Point('O')
        >>> P = Particle('P', O, m)
        >>> P.potential_energy = m * g * h

        """

        self._pe = sympify(scalar)
