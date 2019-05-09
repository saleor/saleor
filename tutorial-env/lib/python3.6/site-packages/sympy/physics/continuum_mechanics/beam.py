"""
This module can be used to solve 2D beam bending problems with
singularity functions in mechanics.
"""

from __future__ import print_function, division

from sympy.core import S, Symbol, diff, symbols
from sympy.solvers import linsolve
from sympy.printing import sstr
from sympy.functions import SingularityFunction, Piecewise, factorial
from sympy.core import sympify
from sympy.integrals import integrate
from sympy.series import limit
from sympy.plotting import plot
from sympy.external import import_module
from sympy.utilities.decorator import doctest_depends_on
from sympy import lambdify

matplotlib = import_module('matplotlib', __import__kwargs={'fromlist':['pyplot']})
numpy = import_module('numpy', __import__kwargs={'fromlist':['linspace']})


__doctest_requires__ = {('Beam.plot_loading_results',): ['matplotlib']}


class Beam(object):
    """
    A Beam is a structural element that is capable of withstanding load
    primarily by resisting against bending. Beams are characterized by
    their cross sectional profile(Second moment of area), their length
    and their material.

    .. note::
       While solving a beam bending problem, a user should choose its
       own sign convention and should stick to it. The results will
       automatically follow the chosen sign convention.

    Examples
    ========
    There is a beam of length 4 meters. A constant distributed load of 6 N/m
    is applied from half of the beam till the end. There are two simple supports
    below the beam, one at the starting point and another at the ending point
    of the beam. The deflection of the beam at the end is restricted.

    Using the sign convention of downwards forces being positive.

    >>> from sympy.physics.continuum_mechanics.beam import Beam
    >>> from sympy import symbols, Piecewise
    >>> E, I = symbols('E, I')
    >>> R1, R2 = symbols('R1, R2')
    >>> b = Beam(4, E, I)
    >>> b.apply_load(R1, 0, -1)
    >>> b.apply_load(6, 2, 0)
    >>> b.apply_load(R2, 4, -1)
    >>> b.bc_deflection = [(0, 0), (4, 0)]
    >>> b.boundary_conditions
    {'deflection': [(0, 0), (4, 0)], 'slope': []}
    >>> b.load
    R1*SingularityFunction(x, 0, -1) + R2*SingularityFunction(x, 4, -1) + 6*SingularityFunction(x, 2, 0)
    >>> b.solve_for_reaction_loads(R1, R2)
    >>> b.load
    -3*SingularityFunction(x, 0, -1) + 6*SingularityFunction(x, 2, 0) - 9*SingularityFunction(x, 4, -1)
    >>> b.shear_force()
    -3*SingularityFunction(x, 0, 0) + 6*SingularityFunction(x, 2, 1) - 9*SingularityFunction(x, 4, 0)
    >>> b.bending_moment()
    -3*SingularityFunction(x, 0, 1) + 3*SingularityFunction(x, 2, 2) - 9*SingularityFunction(x, 4, 1)
    >>> b.slope()
    (-3*SingularityFunction(x, 0, 2)/2 + SingularityFunction(x, 2, 3) - 9*SingularityFunction(x, 4, 2)/2 + 7)/(E*I)
    >>> b.deflection()
    (7*x - SingularityFunction(x, 0, 3)/2 + SingularityFunction(x, 2, 4)/4 - 3*SingularityFunction(x, 4, 3)/2)/(E*I)
    >>> b.deflection().rewrite(Piecewise)
    (7*x - Piecewise((x**3, x > 0), (0, True))/2
         - 3*Piecewise(((x - 4)**3, x - 4 > 0), (0, True))/2
         + Piecewise(((x - 2)**4, x - 2 > 0), (0, True))/4)/(E*I)
    """

    def __init__(self, length, elastic_modulus, second_moment, variable=Symbol('x'), base_char='C'):
        """Initializes the class.

        Parameters
        ==========
        length : Sympifyable
            A Symbol or value representing the Beam's length.
        elastic_modulus : Sympifyable
            A SymPy expression representing the Beam's Modulus of Elasticity.
            It is a measure of the stiffness of the Beam material. It can
            also be a continuous function of position along the beam.
        second_moment : Sympifyable
            A SymPy expression representing the Beam's Second moment of area.
            It is a geometrical property of an area which reflects how its
            points are distributed with respect to its neutral axis. It can
            also be a continuous function of position along the beam.
        variable : Symbol, optional
            A Symbol object that will be used as the variable along the beam
            while representing the load, shear, moment, slope and deflection
            curve. By default, it is set to ``Symbol('x')``.
        base_char : String, optional
            A String that will be used as base character to generate sequential
            symbols for integration constants in cases where boundary conditions
            are not sufficient to solve them.
        """
        self.length = length
        self.elastic_modulus = elastic_modulus
        self.second_moment = second_moment
        self.variable = variable
        self._base_char = base_char
        self._boundary_conditions = {'deflection': [], 'slope': []}
        self._load = 0
        self._applied_loads = []
        self._reaction_loads = {}
        self._composite_type = None
        self._hinge_position = None

    def __str__(self):
        str_sol = 'Beam({}, {}, {})'.format(sstr(self._length), sstr(self._elastic_modulus), sstr(self._second_moment))
        return str_sol

    @property
    def reaction_loads(self):
        """ Returns the reaction forces in a dictionary."""
        return self._reaction_loads

    @property
    def length(self):
        """Length of the Beam."""
        return self._length

    @length.setter
    def length(self, l):
        self._length = sympify(l)

    @property
    def variable(self):
        """
        A symbol that can be used as a variable along the length of the beam
        while representing load distribution, shear force curve, bending
        moment, slope curve and the deflection curve. By default, it is set
        to ``Symbol('x')``, but this property is mutable.

        Examples
        ========

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> x, y, z = symbols('x, y, z')
        >>> b = Beam(4, E, I)
        >>> b.variable
        x
        >>> b.variable = y
        >>> b.variable
        y
        >>> b = Beam(4, E, I, z)
        >>> b.variable
        z
        """
        return self._variable

    @variable.setter
    def variable(self, v):
        if isinstance(v, Symbol):
            self._variable = v
        else:
            raise TypeError("""The variable should be a Symbol object.""")

    @property
    def elastic_modulus(self):
        """Young's Modulus of the Beam. """
        return self._elastic_modulus

    @elastic_modulus.setter
    def elastic_modulus(self, e):
        self._elastic_modulus = sympify(e)

    @property
    def second_moment(self):
        """Second moment of area of the Beam. """
        return self._second_moment

    @second_moment.setter
    def second_moment(self, i):
        self._second_moment = sympify(i)

    @property
    def boundary_conditions(self):
        """
        Returns a dictionary of boundary conditions applied on the beam.
        The dictionary has three kewwords namely moment, slope and deflection.
        The value of each keyword is a list of tuple, where each tuple
        contains loaction and value of a boundary condition in the format
        (location, value).

        Examples
        ========
        There is a beam of length 4 meters. The bending moment at 0 should be 4
        and at 4 it should be 0. The slope of the beam should be 1 at 0. The
        deflection should be 2 at 0.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> b = Beam(4, E, I)
        >>> b.bc_deflection = [(0, 2)]
        >>> b.bc_slope = [(0, 1)]
        >>> b.boundary_conditions
        {'deflection': [(0, 2)], 'slope': [(0, 1)]}

        Here the deflection of the beam should be ``2`` at ``0``.
        Similarly, the slope of the beam should be ``1`` at ``0``.
        """
        return self._boundary_conditions

    @property
    def bc_slope(self):
        return self._boundary_conditions['slope']

    @bc_slope.setter
    def bc_slope(self, s_bcs):
        self._boundary_conditions['slope'] = s_bcs

    @property
    def bc_deflection(self):
        return self._boundary_conditions['deflection']

    @bc_deflection.setter
    def bc_deflection(self, d_bcs):
        self._boundary_conditions['deflection'] = d_bcs

    def join(self, beam, via="fixed"):
        """
        This method joins two beams to make a new composite beam system.
        Passed Beam class instance is attached to the right end of calling
        object. This method can be used to form beams having Discontinuous
        values of Elastic modulus or Second moment.

        Parameters
        ==========
        beam : Beam class object
            The Beam object which would be connected to the right of calling
            object.
        via : String
            States the way two Beam object would get connected
            - For axially fixed Beams, via="fixed"
            - For Beams connected via hinge, via="hinge"

        Examples
        ========
        There is a cantilever beam of length 4 meters. For first 2 meters
        its moment of inertia is `1.5*I` and `I` for the other end.
        A pointload of magnitude 4 N is applied from the top at its free end.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> R1, R2 = symbols('R1, R2')
        >>> b1 = Beam(2, E, 1.5*I)
        >>> b2 = Beam(2, E, I)
        >>> b = b1.join(b2, "fixed")
        >>> b.apply_load(20, 4, -1)
        >>> b.apply_load(R1, 0, -1)
        >>> b.apply_load(R2, 0, -2)
        >>> b.bc_slope = [(0, 0)]
        >>> b.bc_deflection = [(0, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.load
        80*SingularityFunction(x, 0, -2) - 20*SingularityFunction(x, 0, -1) + 20*SingularityFunction(x, 4, -1)
        >>> b.slope()
        (((80*SingularityFunction(x, 0, 1) - 10*SingularityFunction(x, 0, 2) + 10*SingularityFunction(x, 4, 2))/I - 120/I)/E + 80.0/(E*I))*SingularityFunction(x, 2, 0)
        + 0.666666666666667*(80*SingularityFunction(x, 0, 1) - 10*SingularityFunction(x, 0, 2) + 10*SingularityFunction(x, 4, 2))*SingularityFunction(x, 0, 0)/(E*I)
        - 0.666666666666667*(80*SingularityFunction(x, 0, 1) - 10*SingularityFunction(x, 0, 2) + 10*SingularityFunction(x, 4, 2))*SingularityFunction(x, 2, 0)/(E*I)
        """
        x = self.variable
        E = self.elastic_modulus
        new_length = self.length + beam.length
        if self.second_moment != beam.second_moment:
            new_second_moment = Piecewise((self.second_moment, x<=self.length),
                                    (beam.second_moment, x<=new_length))
        else:
            new_second_moment = self.second_moment

        if via == "fixed":
            new_beam = Beam(new_length, E, new_second_moment, x)
            new_beam._composite_type = "fixed"
            return new_beam

        if via == "hinge":
            new_beam = Beam(new_length, E, new_second_moment, x)
            new_beam._composite_type = "hinge"
            new_beam._hinge_position = self.length
            return new_beam

    def apply_support(self, loc, type="fixed"):
        """
        This method applies support to a particular beam object.

        Parameters
        ==========
        loc : Sympifyable
            Location of point at which support is applied.
        type : String
            Determines type of Beam support applied. To apply support structure
            with
            - zero degree of freedom, type = "fixed"
            - one degree of freedom, type = "pin"
            - two degrees of freedom, type = "roller"

        Examples
        ========
        There is a beam of length 30 meters. A moment of magnitude 120 Nm is
        applied in the clockwise direction at the end of the beam. A pointload
        of magnitude 8 N is applied from the top of the beam at the starting
        point. There are two simple supports below the beam. One at the end
        and another one at a distance of 10 meters from the start. The
        deflection is restricted at both the supports.

        Using the sign convention of upward forces and clockwise moment
        being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> b = Beam(30, E, I)
        >>> b.apply_support(10, 'roller')
        >>> b.apply_support(30, 'roller')
        >>> b.apply_load(-8, 0, -1)
        >>> b.apply_load(120, 30, -2)
        >>> R_10, R_30 = symbols('R_10, R_30')
        >>> b.solve_for_reaction_loads(R_10, R_30)
        >>> b.load
        -8*SingularityFunction(x, 0, -1) + 6*SingularityFunction(x, 10, -1)
        + 120*SingularityFunction(x, 30, -2) + 2*SingularityFunction(x, 30, -1)
        >>> b.slope()
        (-4*SingularityFunction(x, 0, 2) + 3*SingularityFunction(x, 10, 2)
            + 120*SingularityFunction(x, 30, 1) + SingularityFunction(x, 30, 2) + 4000/3)/(E*I)
        """
        if type == "pin" or type == "roller":
            reaction_load = Symbol('R_'+str(loc))
            self.apply_load(reaction_load, loc, -1)
            self.bc_deflection.append((loc, 0))
        else:
            reaction_load = Symbol('R_'+str(loc))
            reaction_moment = Symbol('M_'+str(loc))
            self.apply_load(reaction_load, loc, -1)
            self.apply_load(reaction_moment, loc, -2)
            self.bc_deflection.append((loc, 0))
            self.bc_slope.append((loc, 0))

    def apply_load(self, value, start, order, end=None):
        """
        This method adds up the loads given to a particular beam object.

        Parameters
        ==========
        value : Sympifyable
            The magnitude of an applied load.
        start : Sympifyable
            The starting point of the applied load. For point moments and
            point forces this is the location of application.
        order : Integer
            The order of the applied load.

               - For moments, order = -2
               - For point loads, order =-1
               - For constant distributed load, order = 0
               - For ramp loads, order = 1
               - For parabolic ramp loads, order = 2
               - ... so on.

        end : Sympifyable, optional
            An optional argument that can be used if the load has an end point
            within the length of the beam.

        Examples
        ========
        There is a beam of length 4 meters. A moment of magnitude 3 Nm is
        applied in the clockwise direction at the starting point of the beam.
        A point load of magnitude 4 N is applied from the top of the beam at
        2 meters from the starting point and a parabolic ramp load of magnitude
        2 N/m is applied below the beam starting from 2 meters to 3 meters
        away from the starting point of the beam.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> b = Beam(4, E, I)
        >>> b.apply_load(-3, 0, -2)
        >>> b.apply_load(4, 2, -1)
        >>> b.apply_load(-2, 2, 2, end=3)
        >>> b.load
        -3*SingularityFunction(x, 0, -2) + 4*SingularityFunction(x, 2, -1) - 2*SingularityFunction(x, 2, 2) + 2*SingularityFunction(x, 3, 0) + 4*SingularityFunction(x, 3, 1) + 2*SingularityFunction(x, 3, 2)

        """
        x = self.variable
        value = sympify(value)
        start = sympify(start)
        order = sympify(order)

        self._applied_loads.append((value, start, order, end))
        self._load += value*SingularityFunction(x, start, order)

        if end:
            if order.is_negative:
                msg = ("If 'end' is provided the 'order' of the load cannot "
                       "be negative, i.e. 'end' is only valid for distributed "
                       "loads.")
                raise ValueError(msg)
            # NOTE : A Taylor series can be used to define the summation of
            # singularity functions that subtract from the load past the end
            # point such that it evaluates to zero past 'end'.
            f = value * x**order
            for i in range(0, order + 1):
                self._load -= (f.diff(x, i).subs(x, end - start) *
                               SingularityFunction(x, end, i) / factorial(i))

    def remove_load(self, value, start, order, end=None):
        """
        This method removes a particular load present on the beam object.
        Returns a ValueError if the load passed as an argument is not
        present on the beam.

        Parameters
        ==========
        value : Sympifyable
            The magnitude of an applied load.
        start : Sympifyable
            The starting point of the applied load. For point moments and
            point forces this is the location of application.
        order : Integer
            The order of the applied load.
            - For moments, order= -2
            - For point loads, order=-1
            - For constant distributed load, order=0
            - For ramp loads, order=1
            - For parabolic ramp loads, order=2
            - ... so on.
        end : Sympifyable, optional
            An optional argument that can be used if the load has an end point
            within the length of the beam.

        Examples
        ========
        There is a beam of length 4 meters. A moment of magnitude 3 Nm is
        applied in the clockwise direction at the starting point of the beam.
        A pointload of magnitude 4 N is applied from the top of the beam at
        2 meters from the starting point and a parabolic ramp load of magnitude
        2 N/m is applied below the beam starting from 2 meters to 3 meters
        away from the starting point of the beam.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> b = Beam(4, E, I)
        >>> b.apply_load(-3, 0, -2)
        >>> b.apply_load(4, 2, -1)
        >>> b.apply_load(-2, 2, 2, end=3)
        >>> b.load
        -3*SingularityFunction(x, 0, -2) + 4*SingularityFunction(x, 2, -1) - 2*SingularityFunction(x, 2, 2) + 2*SingularityFunction(x, 3, 0) + 4*SingularityFunction(x, 3, 1) + 2*SingularityFunction(x, 3, 2)
        >>> b.remove_load(-2, 2, 2, end = 3)
        >>> b.load
        -3*SingularityFunction(x, 0, -2) + 4*SingularityFunction(x, 2, -1)
        """
        x = self.variable
        value = sympify(value)
        start = sympify(start)
        order = sympify(order)

        if (value, start, order, end) in self._applied_loads:
            self._load -= value*SingularityFunction(x, start, order)
            self._applied_loads.remove((value, start, order, end))
        else:
            msg = "No such load distribution exists on the beam object."
            raise ValueError(msg)

        if end:
            # TODO : This is essentially duplicate code wrt to apply_load,
            # would be better to move it to one location and both methods use
            # it.
            if order.is_negative:
                msg = ("If 'end' is provided the 'order' of the load cannot "
                       "be negative, i.e. 'end' is only valid for distributed "
                       "loads.")
                raise ValueError(msg)
            # NOTE : A Taylor series can be used to define the summation of
            # singularity functions that subtract from the load past the end
            # point such that it evaluates to zero past 'end'.
            f = value * x**order
            for i in range(0, order + 1):
                self._load += (f.diff(x, i).subs(x, end - start) *
                               SingularityFunction(x, end, i) / factorial(i))

    @property
    def load(self):
        """
        Returns a Singularity Function expression which represents
        the load distribution curve of the Beam object.

        Examples
        ========
        There is a beam of length 4 meters. A moment of magnitude 3 Nm is
        applied in the clockwise direction at the starting point of the beam.
        A point load of magnitude 4 N is applied from the top of the beam at
        2 meters from the starting point and a parabolic ramp load of magnitude
        2 N/m is applied below the beam starting from 3 meters away from the
        starting point of the beam.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> b = Beam(4, E, I)
        >>> b.apply_load(-3, 0, -2)
        >>> b.apply_load(4, 2, -1)
        >>> b.apply_load(-2, 3, 2)
        >>> b.load
        -3*SingularityFunction(x, 0, -2) + 4*SingularityFunction(x, 2, -1) - 2*SingularityFunction(x, 3, 2)
        """
        return self._load

    @property
    def applied_loads(self):
        """
        Returns a list of all loads applied on the beam object.
        Each load in the list is a tuple of form (value, start, order, end).

        Examples
        ========
        There is a beam of length 4 meters. A moment of magnitude 3 Nm is
        applied in the clockwise direction at the starting point of the beam.
        A pointload of magnitude 4 N is applied from the top of the beam at
        2 meters from the starting point. Another pointload of magnitude 5 N
        is applied at same position.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> b = Beam(4, E, I)
        >>> b.apply_load(-3, 0, -2)
        >>> b.apply_load(4, 2, -1)
        >>> b.apply_load(5, 2, -1)
        >>> b.load
        -3*SingularityFunction(x, 0, -2) + 9*SingularityFunction(x, 2, -1)
        >>> b.applied_loads
        [(-3, 0, -2, None), (4, 2, -1, None), (5, 2, -1, None)]
        """
        return self._applied_loads

    def _solve_hinge_beams(self, *reactions):
        """Method to find integration constants and reactional variables in a
        composite beam connected via hinge.
        This method resolves the composite Beam into its sub-beams and then
        equations of shear force, bending moment, slope and deflection are
        evaluated for both of them separately. These equations are then solved
        for unknown reactions and integration constants using the boundary
        conditions applied on the Beam. Equal deflection of both sub-beams
        at the hinge joint gives us another equation to solve the system.

        Examples
        ========
        A combined beam, with constant fkexural rigidity E*I, is formed by joining
        a Beam of length 2*l to the right of another Beam of length l. The whole beam
        is fixed at both of its both end. A point load of magnitude P is also applied
        from the top at a distance of 2*l from starting point.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> l=symbols('l', positive=True)
        >>> b1=Beam(l ,E,I)
        >>> b2=Beam(2*l ,E,I)
        >>> b=b1.join(b2,"hinge")
        >>> M1, A1, M2, A2, P = symbols('M1 A1 M2 A2 P')
        >>> b.apply_load(A1,0,-1)
        >>> b.apply_load(M1,0,-2)
        >>> b.apply_load(P,2*l,-1)
        >>> b.apply_load(A2,3*l,-1)
        >>> b.apply_load(M2,3*l,-2)
        >>> b.bc_slope=[(0,0), (3*l, 0)]
        >>> b.bc_deflection=[(0,0), (3*l, 0)]
        >>> b.solve_for_reaction_loads(M1, A1, M2, A2)
        >>> b.reaction_loads
        {A1: -5*P/18, A2: -13*P/18, M1: 5*P*l/18, M2: -4*P*l/9}
        >>> b.slope()
        (5*P*l*SingularityFunction(x, 0, 1)/18 - 5*P*SingularityFunction(x, 0, 2)/36 + 5*P*SingularityFunction(x, l, 2)/36)*SingularityFunction(x, 0, 0)/(E*I)
        - (5*P*l*SingularityFunction(x, 0, 1)/18 - 5*P*SingularityFunction(x, 0, 2)/36 + 5*P*SingularityFunction(x, l, 2)/36)*SingularityFunction(x, l, 0)/(E*I)
        + (P*l**2/18 - 4*P*l*SingularityFunction(-l + x, 2*l, 1)/9 - 5*P*SingularityFunction(-l + x, 0, 2)/36 + P*SingularityFunction(-l + x, l, 2)/2
        - 13*P*SingularityFunction(-l + x, 2*l, 2)/36)*SingularityFunction(x, l, 0)/(E*I)
        >>> b.deflection()
        (5*P*l*SingularityFunction(x, 0, 2)/36 - 5*P*SingularityFunction(x, 0, 3)/108 + 5*P*SingularityFunction(x, l, 3)/108)*SingularityFunction(x, 0, 0)/(E*I)
        - (5*P*l*SingularityFunction(x, 0, 2)/36 - 5*P*SingularityFunction(x, 0, 3)/108 + 5*P*SingularityFunction(x, l, 3)/108)*SingularityFunction(x, l, 0)/(E*I)
        + (5*P*l**3/54 + P*l**2*(-l + x)/18 - 2*P*l*SingularityFunction(-l + x, 2*l, 2)/9 - 5*P*SingularityFunction(-l + x, 0, 3)/108 + P*SingularityFunction(-l + x, l, 3)/6
        - 13*P*SingularityFunction(-l + x, 2*l, 3)/108)*SingularityFunction(x, l, 0)/(E*I)
        """
        x = self.variable
        l = self._hinge_position
        E = self._elastic_modulus
        I = self._second_moment

        if isinstance(I, Piecewise):
            I1 = I.args[0][0]
            I2 = I.args[1][0]
        else:
            I1 = I2 = I

        load_1 = 0       # Load equation on first segment of composite beam
        load_2 = 0       # Load equation on second segment of composite beam

        # Distributing load on both segments
        for load in self.applied_loads:
            if load[1] < l:
                load_1 += load[0]*SingularityFunction(x, load[1], load[2])
                if load[2] == 0:
                    load_1 -= load[0]*SingularityFunction(x, load[3], load[2])
                elif load[2] > 0:
                    load_1 -= load[0]*SingularityFunction(x, load[3], load[2]) + load[0]*SingularityFunction(x, load[3], 0)
            elif load[1] == l:
                load_1 += load[0]*SingularityFunction(x, load[1], load[2])
                load_2 += load[0]*SingularityFunction(x, load[1] - l, load[2])
            elif load[1] > l:
                load_2 += load[0]*SingularityFunction(x, load[1] - l, load[2])
                if load[2] == 0:
                    load_2 -= load[0]*SingularityFunction(x, load[3] - l, load[2])
                elif load[2] > 0:
                    load_2 -= load[0]*SingularityFunction(x, load[3] - l, load[2]) + load[0]*SingularityFunction(x, load[3] - l, 0)

        h = Symbol('h')     # Force due to hinge
        load_1 += h*SingularityFunction(x, l, -1)
        load_2 -= h*SingularityFunction(x, 0, -1)

        eq = []
        shear_1 = integrate(load_1, x)
        shear_curve_1 = limit(shear_1, x, l)
        eq.append(shear_curve_1)
        bending_1 = integrate(shear_1, x)
        moment_curve_1 = limit(bending_1, x, l)
        eq.append(moment_curve_1)

        shear_2 = integrate(load_2, x)
        shear_curve_2 = limit(shear_2, x, self.length - l)
        eq.append(shear_curve_2)
        bending_2 = integrate(shear_2, x)
        moment_curve_2 = limit(bending_2, x, self.length - l)
        eq.append(moment_curve_2)

        C1 = Symbol('C1')
        C2 = Symbol('C2')
        C3 = Symbol('C3')
        C4 = Symbol('C4')
        slope_1 = S(1)/(E*I1)*(integrate(bending_1, x) + C1)
        def_1 = S(1)/(E*I1)*(integrate((E*I)*slope_1, x) + C1*x + C2)
        slope_2 = S(1)/(E*I2)*(integrate(integrate(integrate(load_2, x), x), x) + C3)
        def_2 = S(1)/(E*I2)*(integrate((E*I)*slope_2, x) + C4)

        for position, value in self.bc_slope:
            if position<l:
                eq.append(slope_1.subs(x, position) - value)
            else:
                eq.append(slope_2.subs(x, position - l) - value)

        for position, value in self.bc_deflection:
            if position<l:
                eq.append(def_1.subs(x, position) - value)
            else:
                eq.append(def_2.subs(x, position - l) - value)

        eq.append(def_1.subs(x, l) - def_2.subs(x, 0)) # Deflection of both the segments at hinge would be equal

        constants = list(linsolve(eq, C1, C2, C3, C4, h, *reactions))
        reaction_values = list(constants[0])[5:]

        self._reaction_loads = dict(zip(reactions, reaction_values))
        self._load = self._load.subs(self._reaction_loads)

        # Substituting constants and reactional load and moments with their corresponding values
        slope_1 = slope_1.subs({C1: constants[0][0], h:constants[0][4]}).subs(self._reaction_loads)
        def_1 = def_1.subs({C1: constants[0][0], C2: constants[0][1], h:constants[0][4]}).subs(self._reaction_loads)
        slope_2 = slope_2.subs({x: x-l, C3: constants[0][2], h:constants[0][4]}).subs(self._reaction_loads)
        def_2 = def_2.subs({x: x-l,C3: constants[0][2], C4: constants[0][3], h:constants[0][4]}).subs(self._reaction_loads)

        self._hinge_beam_slope = slope_1*SingularityFunction(x, 0, 0) - slope_1*SingularityFunction(x, l, 0) + slope_2*SingularityFunction(x, l, 0)
        self._hinge_beam_deflection = def_1*SingularityFunction(x, 0, 0) - def_1*SingularityFunction(x, l, 0) + def_2*SingularityFunction(x, l, 0)

    def solve_for_reaction_loads(self, *reactions):
        """
        Solves for the reaction forces.

        Examples
        ========
        There is a beam of length 30 meters. A moment of magnitude 120 Nm is
        applied in the clockwise direction at the end of the beam. A pointload
        of magnitude 8 N is applied from the top of the beam at the starting
        point. There are two simple supports below the beam. One at the end
        and another one at a distance of 10 meters from the start. The
        deflection is restricted at both the supports.

        Using the sign convention of upward forces and clockwise moment
        being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols, linsolve, limit
        >>> E, I = symbols('E, I')
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(30, E, I)
        >>> b.apply_load(-8, 0, -1)
        >>> b.apply_load(R1, 10, -1)  # Reaction force at x = 10
        >>> b.apply_load(R2, 30, -1)  # Reaction force at x = 30
        >>> b.apply_load(120, 30, -2)
        >>> b.bc_deflection = [(10, 0), (30, 0)]
        >>> b.load
        R1*SingularityFunction(x, 10, -1) + R2*SingularityFunction(x, 30, -1)
            - 8*SingularityFunction(x, 0, -1) + 120*SingularityFunction(x, 30, -2)
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.reaction_loads
        {R1: 6, R2: 2}
        >>> b.load
        -8*SingularityFunction(x, 0, -1) + 6*SingularityFunction(x, 10, -1)
            + 120*SingularityFunction(x, 30, -2) + 2*SingularityFunction(x, 30, -1)
        """
        if self._composite_type == "hinge":
            return self._solve_hinge_beams(*reactions)

        x = self.variable
        l = self.length
        C3 = Symbol('C3')
        C4 = Symbol('C4')

        shear_curve = limit(self.shear_force(), x, l)
        moment_curve = limit(self.bending_moment(), x, l)

        slope_eqs = []
        deflection_eqs = []

        slope_curve = integrate(self.bending_moment(), x) + C3
        for position, value in self._boundary_conditions['slope']:
            eqs = slope_curve.subs(x, position) - value
            slope_eqs.append(eqs)

        deflection_curve = integrate(slope_curve, x) + C4
        for position, value in self._boundary_conditions['deflection']:
            eqs = deflection_curve.subs(x, position) - value
            deflection_eqs.append(eqs)

        solution = list((linsolve([shear_curve, moment_curve] + slope_eqs
                            + deflection_eqs, (C3, C4) + reactions).args)[0])
        solution = solution[2:]

        self._reaction_loads = dict(zip(reactions, solution))
        self._load = self._load.subs(self._reaction_loads)

    def shear_force(self):
        """
        Returns a Singularity Function expression which represents
        the shear force curve of the Beam object.

        Examples
        ========
        There is a beam of length 30 meters. A moment of magnitude 120 Nm is
        applied in the clockwise direction at the end of the beam. A pointload
        of magnitude 8 N is applied from the top of the beam at the starting
        point. There are two simple supports below the beam. One at the end
        and another one at a distance of 10 meters from the start. The
        deflection is restricted at both the supports.

        Using the sign convention of upward forces and clockwise moment
        being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(30, E, I)
        >>> b.apply_load(-8, 0, -1)
        >>> b.apply_load(R1, 10, -1)
        >>> b.apply_load(R2, 30, -1)
        >>> b.apply_load(120, 30, -2)
        >>> b.bc_deflection = [(10, 0), (30, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.shear_force()
        -8*SingularityFunction(x, 0, 0) + 6*SingularityFunction(x, 10, 0) + 120*SingularityFunction(x, 30, -1) + 2*SingularityFunction(x, 30, 0)
        """
        x = self.variable
        return integrate(self.load, x)

    def max_shear_force(self):
        """Returns maximum Shear force and its coordinate
        in the Beam object."""
        from sympy import solve, Mul, Interval
        shear_curve = self.shear_force()
        x = self.variable

        terms = shear_curve.args
        singularity = []        # Points at which shear function changes
        for term in terms:
            if isinstance(term, Mul):
                term = term.args[-1]    # SingularityFunction in the term
            singularity.append(term.args[1])
        singularity.sort()
        singularity = list(set(singularity))

        intervals = []    # List of Intervals with discrete value of shear force
        shear_values = []   # List of values of shear force in each interval
        for i, s in enumerate(singularity):
            if s == 0:
                continue
            try:
                shear_slope = Piecewise((float("nan"), x<=singularity[i-1]),(self._load.rewrite(Piecewise), x<s), (float("nan"), True))
                points = solve(shear_slope, x)
                val = []
                for point in points:
                    val.append(shear_curve.subs(x, point))
                points.extend([singularity[i-1], s])
                val.extend([limit(shear_curve, x, singularity[i-1], '+'), limit(shear_curve, x, s, '-')])
                val = list(map(abs, val))
                max_shear = max(val)
                shear_values.append(max_shear)
                intervals.append(points[val.index(max_shear)])
            # If shear force in a particular Interval has zero or constant
            # slope, then above block gives NotImplementedError as
            # solve can't represent Interval solutions.
            except NotImplementedError:
                initial_shear = limit(shear_curve, x, singularity[i-1], '+')
                final_shear = limit(shear_curve, x, s, '-')
                # If shear_curve has a constant slope(it is a line).
                if shear_curve.subs(x, (singularity[i-1] + s)/2) == (initial_shear + final_shear)/2 and initial_shear != final_shear:
                    shear_values.extend([initial_shear, final_shear])
                    intervals.extend([singularity[i-1], s])
                else:    # shear_curve has same value in whole Interval
                    shear_values.append(final_shear)
                    intervals.append(Interval(singularity[i-1], s))

        shear_values = list(map(abs, shear_values))
        maximum_shear = max(shear_values)
        point = intervals[shear_values.index(maximum_shear)]
        return (point, maximum_shear)

    def bending_moment(self):
        """
        Returns a Singularity Function expression which represents
        the bending moment curve of the Beam object.

        Examples
        ========
        There is a beam of length 30 meters. A moment of magnitude 120 Nm is
        applied in the clockwise direction at the end of the beam. A pointload
        of magnitude 8 N is applied from the top of the beam at the starting
        point. There are two simple supports below the beam. One at the end
        and another one at a distance of 10 meters from the start. The
        deflection is restricted at both the supports.

        Using the sign convention of upward forces and clockwise moment
        being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(30, E, I)
        >>> b.apply_load(-8, 0, -1)
        >>> b.apply_load(R1, 10, -1)
        >>> b.apply_load(R2, 30, -1)
        >>> b.apply_load(120, 30, -2)
        >>> b.bc_deflection = [(10, 0), (30, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.bending_moment()
        -8*SingularityFunction(x, 0, 1) + 6*SingularityFunction(x, 10, 1) + 120*SingularityFunction(x, 30, 0) + 2*SingularityFunction(x, 30, 1)
        """
        x = self.variable
        return integrate(self.shear_force(), x)

    def max_bmoment(self):
        """Returns maximum Shear force and its coordinate
        in the Beam object."""
        from sympy import solve, Mul, Interval
        bending_curve = self.bending_moment()
        x = self.variable

        terms = bending_curve.args
        singularity = []        # Points at which bending moment changes
        for term in terms:
            if isinstance(term, Mul):
                term = term.args[-1]    # SingularityFunction in the term
            singularity.append(term.args[1])
        singularity.sort()
        singularity = list(set(singularity))

        intervals = []    # List of Intervals with discrete value of bending moment
        moment_values = []   # List of values of bending moment in each interval
        for i, s in enumerate(singularity):
            if s == 0:
                continue
            try:
                moment_slope = Piecewise((float("nan"), x<=singularity[i-1]),(self.shear_force().rewrite(Piecewise), x<s), (float("nan"), True))
                points = solve(moment_slope, x)
                val = []
                for point in points:
                    val.append(bending_curve.subs(x, point))
                points.extend([singularity[i-1], s])
                val.extend([limit(bending_curve, x, singularity[i-1], '+'), limit(bending_curve, x, s, '-')])
                val = list(map(abs, val))
                max_moment = max(val)
                moment_values.append(max_moment)
                intervals.append(points[val.index(max_moment)])
            # If bending moment in a particular Interval has zero or constant
            # slope, then above block gives NotImplementedError as solve
            # can't represent Interval solutions.
            except NotImplementedError:
                initial_moment = limit(bending_curve, x, singularity[i-1], '+')
                final_moment = limit(bending_curve, x, s, '-')
                # If bending_curve has a constant slope(it is a line).
                if bending_curve.subs(x, (singularity[i-1] + s)/2) == (initial_moment + final_moment)/2 and initial_moment != final_moment:
                    moment_values.extend([initial_moment, final_moment])
                    intervals.extend([singularity[i-1], s])
                else:    # bending_curve has same value in whole Interval
                    moment_values.append(final_moment)
                    intervals.append(Interval(singularity[i-1], s))

        moment_values = list(map(abs, moment_values))
        maximum_moment = max(moment_values)
        point = intervals[moment_values.index(maximum_moment)]
        return (point, maximum_moment)

    def point_cflexure(self):
        """
        Returns a Set of point(s) with zero bending moment and
        where bending moment curve of the beam object changes
        its sign from negative to positive or vice versa.

        Examples
        ========
        There is is 10 meter long overhanging beam. There are
        two simple supports below the beam. One at the start
        and another one at a distance of 6 meters from the start.
        Point loads of magnitude 10KN and 20KN are applied at
        2 meters and 4 meters from start respectively. A Uniformly
        distribute load of magnitude of magnitude 3KN/m is also
        applied on top starting from 6 meters away from starting
        point till end.
        Using the sign convention of upward forces and clockwise moment
        being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> b = Beam(10, E, I)
        >>> b.apply_load(-4, 0, -1)
        >>> b.apply_load(-46, 6, -1)
        >>> b.apply_load(10, 2, -1)
        >>> b.apply_load(20, 4, -1)
        >>> b.apply_load(3, 6, 0)
        >>> b.point_cflexure()
        [10/3]
        """
        from sympy import solve, Piecewise

        # To restrict the range within length of the Beam
        moment_curve = Piecewise((float("nan"), self.variable<=0),
                (self.bending_moment(), self.variable<self.length),
                (float("nan"), True))

        points = solve(moment_curve.rewrite(Piecewise), self.variable,
                        domain=S.Reals)
        return points

    def slope(self):
        """
        Returns a Singularity Function expression which represents
        the slope the elastic curve of the Beam object.

        Examples
        ========
        There is a beam of length 30 meters. A moment of magnitude 120 Nm is
        applied in the clockwise direction at the end of the beam. A pointload
        of magnitude 8 N is applied from the top of the beam at the starting
        point. There are two simple supports below the beam. One at the end
        and another one at a distance of 10 meters from the start. The
        deflection is restricted at both the supports.

        Using the sign convention of upward forces and clockwise moment
        being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(30, E, I)
        >>> b.apply_load(-8, 0, -1)
        >>> b.apply_load(R1, 10, -1)
        >>> b.apply_load(R2, 30, -1)
        >>> b.apply_load(120, 30, -2)
        >>> b.bc_deflection = [(10, 0), (30, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.slope()
        (-4*SingularityFunction(x, 0, 2) + 3*SingularityFunction(x, 10, 2)
            + 120*SingularityFunction(x, 30, 1) + SingularityFunction(x, 30, 2) + 4000/3)/(E*I)
        """
        x = self.variable
        E = self.elastic_modulus
        I = self.second_moment

        if self._composite_type == "hinge":
            return self._hinge_beam_slope
        if not self._boundary_conditions['slope']:
            return diff(self.deflection(), x)
        if isinstance(I, Piecewise) and self._composite_type == "fixed":
            args = I.args
            slope = 0
            prev_slope = 0
            prev_end = 0
            for i in range(len(args)):
                if i != 0:
                    prev_end = args[i-1][1].args[1]
                slope_value = S(1)/E*integrate(self.bending_moment()/args[i][0], (x, prev_end, x))
                if i != len(args) - 1:
                    slope += (prev_slope + slope_value)*SingularityFunction(x, prev_end, 0) - \
                        (prev_slope + slope_value)*SingularityFunction(x, args[i][1].args[1], 0)
                else:
                    slope += (prev_slope + slope_value)*SingularityFunction(x, prev_end, 0)
                prev_slope = slope_value.subs(x, args[i][1].args[1])
            return slope

        C3 = Symbol('C3')
        slope_curve = integrate(S(1)/(E*I)*self.bending_moment(), x) + C3

        bc_eqs = []
        for position, value in self._boundary_conditions['slope']:
            eqs = slope_curve.subs(x, position) - value
            bc_eqs.append(eqs)
        constants = list(linsolve(bc_eqs, C3))
        slope_curve = slope_curve.subs({C3: constants[0][0]})
        return slope_curve

    def deflection(self):
        """
        Returns a Singularity Function expression which represents
        the elastic curve or deflection of the Beam object.

        Examples
        ========
        There is a beam of length 30 meters. A moment of magnitude 120 Nm is
        applied in the clockwise direction at the end of the beam. A pointload
        of magnitude 8 N is applied from the top of the beam at the starting
        point. There are two simple supports below the beam. One at the end
        and another one at a distance of 10 meters from the start. The
        deflection is restricted at both the supports.

        Using the sign convention of upward forces and clockwise moment
        being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> E, I = symbols('E, I')
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(30, E, I)
        >>> b.apply_load(-8, 0, -1)
        >>> b.apply_load(R1, 10, -1)
        >>> b.apply_load(R2, 30, -1)
        >>> b.apply_load(120, 30, -2)
        >>> b.bc_deflection = [(10, 0), (30, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.deflection()
        (4000*x/3 - 4*SingularityFunction(x, 0, 3)/3 + SingularityFunction(x, 10, 3)
            + 60*SingularityFunction(x, 30, 2) + SingularityFunction(x, 30, 3)/3 - 12000)/(E*I)
        """
        x = self.variable
        E = self.elastic_modulus
        I = self.second_moment
        if self._composite_type == "hinge":
            return self._hinge_beam_deflection
        if not self._boundary_conditions['deflection'] and not self._boundary_conditions['slope']:
            if isinstance(I, Piecewise) and self._composite_type == "fixed":
                args = I.args
                prev_slope = 0
                prev_def = 0
                prev_end = 0
                deflection = 0
                for i in range(len(args)):
                    if i != 0:
                        prev_end = args[i-1][1].args[1]
                    slope_value = S(1)/E*integrate(self.bending_moment()/args[i][0], (x, prev_end, x))
                    recent_segment_slope = prev_slope + slope_value
                    deflection_value = integrate(recent_segment_slope, (x, prev_end, x))
                    if i != len(args) - 1:
                        deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0) \
                            - (prev_def + deflection_value)*SingularityFunction(x, args[i][1].args[1], 0)
                    else:
                        deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0)
                    prev_slope = slope_value.subs(x, args[i][1].args[1])
                    prev_def = deflection_value.subs(x, args[i][1].args[1])
                return deflection
            base_char = self._base_char
            constants = symbols(base_char + '3:5')
            return S(1)/(E*I)*integrate(integrate(self.bending_moment(), x), x) + constants[0]*x + constants[1]
        elif not self._boundary_conditions['deflection']:
            base_char = self._base_char
            constant = symbols(base_char + '4')
            return integrate(self.slope(), x) + constant
        elif not self._boundary_conditions['slope'] and self._boundary_conditions['deflection']:
            if isinstance(I, Piecewise) and self._composite_type == "fixed":
                args = I.args
                prev_slope = 0
                prev_def = 0
                prev_end = 0
                deflection = 0
                for i in range(len(args)):
                    if i != 0:
                        prev_end = args[i-1][1].args[1]
                    slope_value = S(1)/E*integrate(self.bending_moment()/args[i][0], (x, prev_end, x))
                    recent_segment_slope = prev_slope + slope_value
                    deflection_value = integrate(recent_segment_slope, (x, prev_end, x))
                    if i != len(args) - 1:
                        deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0) \
                            - (prev_def + deflection_value)*SingularityFunction(x, args[i][1].args[1], 0)
                    else:
                        deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0)
                    prev_slope = slope_value.subs(x, args[i][1].args[1])
                    prev_def = deflection_value.subs(x, args[i][1].args[1])
                return deflection
            base_char = self._base_char
            C3, C4 = symbols(base_char + '3:5')    # Integration constants
            slope_curve = integrate(self.bending_moment(), x) + C3
            deflection_curve = integrate(slope_curve, x) + C4
            bc_eqs = []
            for position, value in self._boundary_conditions['deflection']:
                eqs = deflection_curve.subs(x, position) - value
                bc_eqs.append(eqs)
            constants = list(linsolve(bc_eqs, (C3, C4)))
            deflection_curve = deflection_curve.subs({C3: constants[0][0], C4: constants[0][1]})
            return S(1)/(E*I)*deflection_curve

        if isinstance(I, Piecewise) and self._composite_type == "fixed":
            args = I.args
            prev_slope = 0
            prev_def = 0
            prev_end = 0
            deflection = 0
            for i in range(len(args)):
                if i != 0:
                    prev_end = args[i-1][1].args[1]
                slope_value = S(1)/E*integrate(self.bending_moment()/args[i][0], (x, prev_end, x))
                recent_segment_slope = prev_slope + slope_value
                deflection_value = integrate(recent_segment_slope, (x, prev_end, x))
                if i != len(args) - 1:
                    deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0) \
                        - (prev_def + deflection_value)*SingularityFunction(x, args[i][1].args[1], 0)
                else:
                    deflection += (prev_def + deflection_value)*SingularityFunction(x, prev_end, 0)
                prev_slope = slope_value.subs(x, args[i][1].args[1])
                prev_def = deflection_value.subs(x, args[i][1].args[1])
            return deflection

        C4 = Symbol('C4')
        deflection_curve = integrate(self.slope(), x) + C4

        bc_eqs = []
        for position, value in self._boundary_conditions['deflection']:
            eqs = deflection_curve.subs(x, position) - value
            bc_eqs.append(eqs)

        constants = list(linsolve(bc_eqs, C4))
        deflection_curve = deflection_curve.subs({C4: constants[0][0]})
        return deflection_curve

    def max_deflection(self):
        """
        Returns point of max deflection and its coresponding deflection value
        in a Beam object.
        """
        from sympy import solve, Piecewise

        # To restrict the range within length of the Beam
        slope_curve = Piecewise((float("nan"), self.variable<=0),
                (self.slope(), self.variable<self.length),
                (float("nan"), True))

        points = solve(slope_curve.rewrite(Piecewise), self.variable,
                        domain=S.Reals)
        deflection_curve = self.deflection()
        deflections = [deflection_curve.subs(self.variable, x) for x in points]
        deflections = list(map(abs, deflections))
        if len(deflections) != 0:
            max_def = max(deflections)
            return (points[deflections.index(max_def)], max_def)
        else:
            return None

    def plot_shear_force(self, subs=None):
        """
        Returns a plot for Shear force present in the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.

        Examples
        ========
        There is a beam of length 8 meters. A constant distributed load of 10 KN/m
        is applied from half of the beam till the end. There are two simple supports
        below the beam, one at the starting point and another at the ending point
        of the beam. A pointload of magnitude 5 KN is also applied from top of the
        beam, at a distance of 4 meters from the starting point.
        Take E = 200 GPa and I = 400*(10**-6) meter**4.

        Using the sign convention of downwards forces being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(8, 200*(10**9), 400*(10**-6))
        >>> b.apply_load(5000, 2, -1)
        >>> b.apply_load(R1, 0, -1)
        >>> b.apply_load(R2, 8, -1)
        >>> b.apply_load(10000, 4, 0, end=8)
        >>> b.bc_deflection = [(0, 0), (8, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.plot_shear_force()
        Plot object containing:
        [0]: cartesian line: -13750*SingularityFunction(x, 0, 0) + 5000*SingularityFunction(x, 2, 0)
        + 10000*SingularityFunction(x, 4, 1) - 31250*SingularityFunction(x, 8, 0)
        - 10000*SingularityFunction(x, 8, 1) for x over (0.0, 8.0)
        """
        shear_force = self.shear_force()
        if subs is None:
            subs = {}
        for sym in shear_force.atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length
        return plot(shear_force.subs(subs), (self.variable, 0, length), title='Shear Force',
                xlabel='position', ylabel='Value', line_color='g')

    def plot_bending_moment(self, subs=None):
        """
        Returns a plot for Bending moment present in the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.

        Examples
        ========
        There is a beam of length 8 meters. A constant distributed load of 10 KN/m
        is applied from half of the beam till the end. There are two simple supports
        below the beam, one at the starting point and another at the ending point
        of the beam. A pointload of magnitude 5 KN is also applied from top of the
        beam, at a distance of 4 meters from the starting point.
        Take E = 200 GPa and I = 400*(10**-6) meter**4.

        Using the sign convention of downwards forces being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(8, 200*(10**9), 400*(10**-6))
        >>> b.apply_load(5000, 2, -1)
        >>> b.apply_load(R1, 0, -1)
        >>> b.apply_load(R2, 8, -1)
        >>> b.apply_load(10000, 4, 0, end=8)
        >>> b.bc_deflection = [(0, 0), (8, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.plot_bending_moment()
        Plot object containing:
        [0]: cartesian line: -13750*SingularityFunction(x, 0, 1) + 5000*SingularityFunction(x, 2, 1)
        + 5000*SingularityFunction(x, 4, 2) - 31250*SingularityFunction(x, 8, 1)
        - 5000*SingularityFunction(x, 8, 2) for x over (0.0, 8.0)
        """
        bending_moment = self.bending_moment()
        if subs is None:
            subs = {}
        for sym in bending_moment.atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length
        return plot(bending_moment.subs(subs), (self.variable, 0, length), title='Bending Moment',
                xlabel='position', ylabel='Value', line_color='b')

    def plot_slope(self, subs=None):
        """
        Returns a plot for slope of deflection curve of the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.

        Examples
        ========
        There is a beam of length 8 meters. A constant distributed load of 10 KN/m
        is applied from half of the beam till the end. There are two simple supports
        below the beam, one at the starting point and another at the ending point
        of the beam. A pointload of magnitude 5 KN is also applied from top of the
        beam, at a distance of 4 meters from the starting point.
        Take E = 200 GPa and I = 400*(10**-6) meter**4.

        Using the sign convention of downwards forces being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(8, 200*(10**9), 400*(10**-6))
        >>> b.apply_load(5000, 2, -1)
        >>> b.apply_load(R1, 0, -1)
        >>> b.apply_load(R2, 8, -1)
        >>> b.apply_load(10000, 4, 0, end=8)
        >>> b.bc_deflection = [(0, 0), (8, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.plot_slope()
        Plot object containing:
        [0]: cartesian line: -8.59375e-5*SingularityFunction(x, 0, 2) + 3.125e-5*SingularityFunction(x, 2, 2)
        + 2.08333333333333e-5*SingularityFunction(x, 4, 3) - 0.0001953125*SingularityFunction(x, 8, 2)
        - 2.08333333333333e-5*SingularityFunction(x, 8, 3) + 0.00138541666666667 for x over (0.0, 8.0)
        """
        slope = self.slope()
        if subs is None:
            subs = {}
        for sym in slope.atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length
        return plot(slope.subs(subs), (self.variable, 0, length), title='Slope',
                xlabel='position', ylabel='Value', line_color='m')

    def plot_deflection(self, subs=None):
        """
        Returns a plot for deflection curve of the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.

        Examples
        ========
        There is a beam of length 8 meters. A constant distributed load of 10 KN/m
        is applied from half of the beam till the end. There are two simple supports
        below the beam, one at the starting point and another at the ending point
        of the beam. A pointload of magnitude 5 KN is also applied from top of the
        beam, at a distance of 4 meters from the starting point.
        Take E = 200 GPa and I = 400*(10**-6) meter**4.

        Using the sign convention of downwards forces being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(8, 200*(10**9), 400*(10**-6))
        >>> b.apply_load(5000, 2, -1)
        >>> b.apply_load(R1, 0, -1)
        >>> b.apply_load(R2, 8, -1)
        >>> b.apply_load(10000, 4, 0, end=8)
        >>> b.bc_deflection = [(0, 0), (8, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> b.plot_deflection()
        Plot object containing:
        [0]: cartesian line: 0.00138541666666667*x - 2.86458333333333e-5*SingularityFunction(x, 0, 3)
        + 1.04166666666667e-5*SingularityFunction(x, 2, 3) + 5.20833333333333e-6*SingularityFunction(x, 4, 4)
        - 6.51041666666667e-5*SingularityFunction(x, 8, 3) - 5.20833333333333e-6*SingularityFunction(x, 8, 4)
        for x over (0.0, 8.0)
        """
        deflection = self.deflection()
        if subs is None:
            subs = {}
        for sym in deflection.atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' %sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length
        return plot(deflection.subs(subs), (self.variable, 0, length),
                    title='Deflection', xlabel='position', ylabel='Value',
                    line_color='r')

    @doctest_depends_on(modules=('numpy', 'matplotlib',))
    def plot_loading_results(self, subs=None):
        """
        Returns Axes object containing subplots of Shear Force, Bending Moment,
        Slope and Deflection of the Beam object.

        Parameters
        ==========
        subs : dictionary
            Python dictionary containing Symbols as key and their
            corresponding values.

        .. note::
           This method only works if numpy and matplotlib libraries
           are installed on the system.

        Examples
        ========
        There is a beam of length 8 meters. A constant distributed load of 10
        KN/m is applied from half of the beam till the end. There are two
        simple supports below the beam, one at the starting point and another
        at the ending point of the beam. A pointload of magnitude 5 KN is also
        applied from top of the beam, at a distance of 4 meters from the
        starting point.  Take E = 200 GPa and I = 400*(10**-6) meter**4.

        Using the sign convention of downwards forces being positive.

        >>> from sympy.physics.continuum_mechanics.beam import Beam
        >>> from sympy import symbols
        >>> R1, R2 = symbols('R1, R2')
        >>> b = Beam(8, 200*(10**9), 400*(10**-6))
        >>> b.apply_load(5000, 2, -1)
        >>> b.apply_load(R1, 0, -1)
        >>> b.apply_load(R2, 8, -1)
        >>> b.apply_load(10000, 4, 0, end=8)
        >>> b.bc_deflection = [(0, 0), (8, 0)]
        >>> b.solve_for_reaction_loads(R1, R2)
        >>> axes = b.plot_loading_results()
        """
        if matplotlib is None:
            raise ImportError('Install matplotlib to use this method.')
        else:
            plt = matplotlib.pyplot
        if numpy is None:
            raise ImportError('Install numpy to use this method.')
        else:
            linspace = numpy.linspace

        variable = self.variable
        if subs is None:
            subs = {}
        for sym in self.deflection().atoms(Symbol):
            if sym == self.variable:
                continue
            if sym not in subs:
                raise ValueError('Value of %s was not passed.' % sym)
        if self.length in subs:
            length = subs[self.length]
        else:
            length = self.length

        # As we are using matplotlib directly in this method, we need to change
        # SymPy methods to numpy functions.
        shear = lambdify(variable,
                         self.shear_force().subs(subs).rewrite(Piecewise),
                         'numpy')
        moment = lambdify(variable,
                          self.bending_moment().subs(subs).rewrite(Piecewise),
                          'numpy')
        slope = lambdify(variable, self.slope().subs(subs).rewrite(Piecewise),
                         'numpy')
        deflection = lambdify(variable,
                              self.deflection().subs(subs).rewrite(Piecewise),
                              'numpy')

        points = linspace(0, float(length), num=100*length)

        # Creating a grid for subplots with 2 rows and 2 columns
        fig, axs = plt.subplots(4, 1)
        # axs is a 2D-numpy array containing axes
        axs[0].plot(points, shear(points))
        axs[0].set_title("Shear Force")
        axs[1].plot(points, moment(points))
        axs[1].set_title("Bending Moment")
        axs[2].plot(points, slope(points))
        axs[2].set_title("Slope")
        axs[3].plot(points, deflection(points))
        axs[3].set_title("Deflection")

        fig.tight_layout()    # For better spacing between subplots
        return axs


class Beam3D(Beam):
    """
    This class handles loads applied in any direction of a 3D space along
    with unequal values of Second moment along different axes.

    .. note::
       While solving a beam bending problem, a user should choose its
       own sign convention and should stick to it. The results will
       automatically follow the chosen sign convention.
       This class assumes that any kind of distributed load/moment is
       applied through out the span of a beam.

    Examples
    ========
    There is a beam of l meters long. A constant distributed load of magnitude q
    is applied along y-axis from start till the end of beam. A constant distributed
    moment of magnitude m is also applied along z-axis from start till the end of beam.
    Beam is fixed at both of its end. So, deflection of the beam at the both ends
    is restricted.

    >>> from sympy.physics.continuum_mechanics.beam import Beam3D
    >>> from sympy import symbols, simplify
    >>> l, E, G, I, A = symbols('l, E, G, I, A')
    >>> b = Beam3D(l, E, G, I, A)
    >>> x, q, m = symbols('x, q, m')
    >>> b.apply_load(q, 0, 0, dir="y")
    >>> b.apply_moment_load(m, 0, -1, dir="z")
    >>> b.shear_force()
    [0, -q*x, 0]
    >>> b.bending_moment()
    [0, 0, -m*x + q*x**2/2]
    >>> b.bc_slope = [(0, [0, 0, 0]), (l, [0, 0, 0])]
    >>> b.bc_deflection = [(0, [0, 0, 0]), (l, [0, 0, 0])]
    >>> b.solve_slope_deflection()
    >>> b.slope()
    [0, 0, l*x*(-l*q + 3*l*(A*G*l*(l*q - 2*m) + 12*E*I*q)/(2*(A*G*l**2 + 12*E*I)) + 3*m)/(6*E*I)
    + q*x**3/(6*E*I) + x**2*(-l*(A*G*l*(l*q - 2*m) + 12*E*I*q)/(2*(A*G*l**2 + 12*E*I))
    - m)/(2*E*I)]
    >>> dx, dy, dz = b.deflection()
    >>> dx
    0
    >>> dz
    0
    >>> expectedy = (
    ... -l**2*q*x**2/(12*E*I) + l**2*x**2*(A*G*l*(l*q - 2*m) + 12*E*I*q)/(8*E*I*(A*G*l**2 + 12*E*I))
    ... + l*m*x**2/(4*E*I) - l*x**3*(A*G*l*(l*q - 2*m) + 12*E*I*q)/(12*E*I*(A*G*l**2 + 12*E*I)) - m*x**3/(6*E*I)
    ... + q*x**4/(24*E*I) + l*x*(A*G*l*(l*q - 2*m) + 12*E*I*q)/(2*A*G*(A*G*l**2 + 12*E*I)) - q*x**2/(2*A*G)
    ... )
    >>> simplify(dy - expectedy)
    0

    References
    ==========

    .. [1] http://homes.civil.aau.dk/jc/FemteSemester/Beams3D.pdf

    """

    def __init__(self, length, elastic_modulus, shear_modulus , second_moment, area, variable=Symbol('x')):
        """Initializes the class.

        Parameters
        ==========
        length : Sympifyable
            A Symbol or value representing the Beam's length.
        elastic_modulus : Sympifyable
            A SymPy expression representing the Beam's Modulus of Elasticity.
            It is a measure of the stiffness of the Beam material.
        shear_modulus : Sympifyable
            A SymPy expression representing the Beam's Modulus of rigidity.
            It is a measure of rigidity of the Beam material.
        second_moment : Sympifyable or list
            A list of two elements having SymPy expression representing the
            Beam's Second moment of area. First value represent Second moment
            across y-axis and second across z-axis.
            Single SymPy expression can be passed if both values are same
        area : Sympifyable
            A SymPy expression representing the Beam's cross-sectional area
            in a plane prependicular to length of the Beam.
        variable : Symbol, optional
            A Symbol object that will be used as the variable along the beam
            while representing the load, shear, moment, slope and deflection
            curve. By default, it is set to ``Symbol('x')``.
        """
        super(Beam3D, self).__init__(length, elastic_modulus, second_moment, variable)
        self.shear_modulus = shear_modulus
        self.area = area
        self._load_vector = [0, 0, 0]
        self._moment_load_vector = [0, 0, 0]
        self._load_Singularity = [0, 0, 0]
        self._slope = [0, 0, 0]
        self._deflection = [0, 0, 0]

    @property
    def shear_modulus(self):
        """Young's Modulus of the Beam. """
        return self._shear_modulus

    @shear_modulus.setter
    def shear_modulus(self, e):
        self._shear_modulus = sympify(e)

    @property
    def second_moment(self):
        """Second moment of area of the Beam. """
        return self._second_moment

    @second_moment.setter
    def second_moment(self, i):
        if isinstance(i, list):
            i = [sympify(x) for x in i]
            self._second_moment = i
        else:
            self._second_moment = sympify(i)

    @property
    def area(self):
        """Cross-sectional area of the Beam. """
        return self._area

    @area.setter
    def area(self, a):
        self._area = sympify(a)

    @property
    def load_vector(self):
        """
        Returns a three element list representing the load vector.
        """
        return self._load_vector

    @property
    def moment_load_vector(self):
        """
        Returns a three element list representing moment loads on Beam.
        """
        return self._moment_load_vector

    @property
    def boundary_conditions(self):
        """
        Returns a dictionary of boundary conditions applied on the beam.
        The dictionary has two keywords namely slope and deflection.
        The value of each keyword is a list of tuple, where each tuple
        contains loaction and value of a boundary condition in the format
        (location, value). Further each value is a list corresponding to
        slope or deflection(s) values along three axes at that location.

        Examples
        ========
        There is a beam of length 4 meters. The slope at 0 should be 4 along
        the x-axis and 0 along others. At the other end of beam, deflection
        along all the three axes should be zero.

        >>> from sympy.physics.continuum_mechanics.beam import Beam3D
        >>> from sympy import symbols
        >>> l, E, G, I, A, x = symbols('l, E, G, I, A, x')
        >>> b = Beam3D(30, E, G, I, A, x)
        >>> b.bc_slope = [(0, (4, 0, 0))]
        >>> b.bc_deflection = [(4, [0, 0, 0])]
        >>> b.boundary_conditions
        {'deflection': [(4, [0, 0, 0])], 'slope': [(0, (4, 0, 0))]}

        Here the deflection of the beam should be ``0`` along all the three axes at ``4``.
        Similarly, the slope of the beam should be ``4`` along x-axis and ``0``
        along y and z axis at ``0``.
        """
        return self._boundary_conditions

    def apply_load(self, value, start, order, dir="y"):
        """
        This method adds up the force load to a particular beam object.

        Parameters
        ==========
        value : Sympifyable
            The magnitude of an applied load.
        dir : String
            Axis along which load is applied.
        order : Integer
            The order of the applied load.
            - For point loads, order=-1
            - For constant distributed load, order=0
            - For ramp loads, order=1
            - For parabolic ramp loads, order=2
            - ... so on.
        """
        x = self.variable
        value = sympify(value)
        start = sympify(start)
        order = sympify(order)

        if dir == "x":
            if not order == -1:
                self._load_vector[0] += value
            self._load_Singularity[0] += value*SingularityFunction(x, start, order)

        elif dir == "y":
            if not order == -1:
                self._load_vector[1] += value
            self._load_Singularity[1] += value*SingularityFunction(x, start, order)

        else:
            if not order == -1:
                self._load_vector[2] += value
            self._load_Singularity[2] += value*SingularityFunction(x, start, order)

    def apply_moment_load(self, value, start, order, dir="y"):
        """
        This method adds up the moment loads to a particular beam object.

        Parameters
        ==========
        value : Sympifyable
            The magnitude of an applied moment.
        dir : String
            Axis along which moment is applied.
        order : Integer
            The order of the applied load.
            - For point moments, order=-2
            - For constant distributed moment, order=-1
            - For ramp moments, order=0
            - For parabolic ramp moments, order=1
            - ... so on.
        """
        x = self.variable
        value = sympify(value)
        start = sympify(start)
        order = sympify(order)

        if dir == "x":
            if not order == -2:
                self._moment_load_vector[0] += value
            self._load_Singularity[0] += value*SingularityFunction(x, start, order)
        elif dir == "y":
            if not order == -2:
                self._moment_load_vector[1] += value
            self._load_Singularity[0] += value*SingularityFunction(x, start, order)
        else:
            if not order == -2:
                self._moment_load_vector[2] += value
            self._load_Singularity[0] += value*SingularityFunction(x, start, order)

    def apply_support(self, loc, type="fixed"):
        if type == "pin" or type == "roller":
            reaction_load = Symbol('R_'+str(loc))
            self._reaction_loads[reaction_load] = reaction_load
            self.bc_deflection.append((loc, [0, 0, 0]))
        else:
            reaction_load = Symbol('R_'+str(loc))
            reaction_moment = Symbol('M_'+str(loc))
            self._reaction_loads[reaction_load] = [reaction_load, reaction_moment]
            self.bc_deflection.append((loc, [0, 0, 0]))
            self.bc_slope.append((loc, [0, 0, 0]))

    def solve_for_reaction_loads(self, *reaction):
        """
        Solves for the reaction forces.

        Examples
        ========
        There is a beam of length 30 meters. It it supported by rollers at
        of its end. A constant distributed load of magnitude 8 N is applied
        from start till its end along y-axis. Another linear load having
        slope equal to 9 is applied along z-axis.

        >>> from sympy.physics.continuum_mechanics.beam import Beam3D
        >>> from sympy import symbols
        >>> l, E, G, I, A, x = symbols('l, E, G, I, A, x')
        >>> b = Beam3D(30, E, G, I, A, x)
        >>> b.apply_load(8, start=0, order=0, dir="y")
        >>> b.apply_load(9*x, start=0, order=0, dir="z")
        >>> b.bc_deflection = [(0, [0, 0, 0]), (30, [0, 0, 0])]
        >>> R1, R2, R3, R4 = symbols('R1, R2, R3, R4')
        >>> b.apply_load(R1, start=0, order=-1, dir="y")
        >>> b.apply_load(R2, start=30, order=-1, dir="y")
        >>> b.apply_load(R3, start=0, order=-1, dir="z")
        >>> b.apply_load(R4, start=30, order=-1, dir="z")
        >>> b.solve_for_reaction_loads(R1, R2, R3, R4)
        >>> b.reaction_loads
        {R1: -120, R2: -120, R3: -1350, R4: -2700}
        """
        x = self.variable
        l = self.length
        q = self._load_Singularity
        shear_curves = [integrate(load, x) for load in q]
        moment_curves = [integrate(shear, x) for shear in shear_curves]
        for i in range(3):
            react = [r for r in reaction if (shear_curves[i].has(r) or moment_curves[i].has(r))]
            if len(react) == 0:
                continue
            shear_curve = limit(shear_curves[i], x, l)
            moment_curve = limit(moment_curves[i], x, l)
            sol = list((linsolve([shear_curve, moment_curve], react).args)[0])
            sol_dict = dict(zip(react, sol))
            reaction_loads = self._reaction_loads
            # Check if any of the evaluated rection exists in another direction
            # and if it exists then it should have same value.
            for key in sol_dict:
                if key in reaction_loads and sol_dict[key] != reaction_loads[key]:
                    raise ValueError("Ambiguous solution for %s in different directions." % key)
            self._reaction_loads.update(sol_dict)

    def shear_force(self):
        """
        Returns a list of three expressions which represents the shear force
        curve of the Beam object along all three axes.
        """
        x = self.variable
        q = self._load_vector
        return [integrate(-q[0], x), integrate(-q[1], x), integrate(-q[2], x)]

    def axial_force(self):
        """
        Returns expression of Axial shear force present inside the Beam object.
        """
        return self.shear_force()[0]

    def bending_moment(self):
        """
        Returns a list of three expressions which represents the bending moment
        curve of the Beam object along all three axes.
        """
        x = self.variable
        m = self._moment_load_vector
        shear = self.shear_force()

        return [integrate(-m[0], x), integrate(-m[1] + shear[2], x),
                integrate(-m[2] - shear[1], x) ]

    def torsional_moment(self):
        """
        Returns expression of Torsional moment present inside the Beam object.
        """
        return self.bending_moment()[0]

    def solve_slope_deflection(self):
        from sympy import dsolve, Function, Derivative, Eq
        x = self.variable
        l = self.length
        E = self.elastic_modulus
        G = self.shear_modulus
        I = self.second_moment
        if isinstance(I, list):
            I_y, I_z = I[0], I[1]
        else:
            I_y = I_z = I
        A = self.area
        load = self._load_vector
        moment = self._moment_load_vector
        defl = Function('defl')
        theta = Function('theta')

        # Finding deflection along x-axis(and corresponding slope value by differentiating it)
        # Equation used: Derivative(E*A*Derivative(def_x(x), x), x) + load_x = 0
        eq = Derivative(E*A*Derivative(defl(x), x), x) + load[0]
        def_x = dsolve(Eq(eq, 0), defl(x)).args[1]
        # Solving constants originated from dsolve
        C1 = Symbol('C1')
        C2 = Symbol('C2')
        constants = list((linsolve([def_x.subs(x, 0), def_x.subs(x, l)], C1, C2).args)[0])
        def_x = def_x.subs({C1:constants[0], C2:constants[1]})
        slope_x = def_x.diff(x)
        self._deflection[0] = def_x
        self._slope[0] = slope_x

        # Finding deflection along y-axis and slope across z-axis. System of equation involved:
        # 1: Derivative(E*I_z*Derivative(theta_z(x), x), x) + G*A*(Derivative(defl_y(x), x) - theta_z(x)) + moment_z = 0
        # 2: Derivative(G*A*(Derivative(defl_y(x), x) - theta_z(x)), x) + load_y = 0
        C_i = Symbol('C_i')
        # Substitute value of `G*A*(Derivative(defl_y(x), x) - theta_z(x))` from (2) in (1)
        eq1 = Derivative(E*I_z*Derivative(theta(x), x), x) + (integrate(-load[1], x) + C_i) + moment[2]
        slope_z = dsolve(Eq(eq1, 0)).args[1]

        # Solve for constants originated from using dsolve on eq1
        constants = list((linsolve([slope_z.subs(x, 0), slope_z.subs(x, l)], C1, C2).args)[0])
        slope_z = slope_z.subs({C1:constants[0], C2:constants[1]})

        # Put value of slope obtained back in (2) to solve for `C_i` and find deflection across y-axis
        eq2 = G*A*(Derivative(defl(x), x)) + load[1]*x - C_i - G*A*slope_z
        def_y = dsolve(Eq(eq2, 0), defl(x)).args[1]
        # Solve for constants originated from using dsolve on eq2
        constants = list((linsolve([def_y.subs(x, 0), def_y.subs(x, l)], C1, C_i).args)[0])
        self._deflection[1] = def_y.subs({C1:constants[0], C_i:constants[1]})
        self._slope[2] = slope_z.subs(C_i, constants[1])

        # Finding deflection along z-axis and slope across y-axis. System of equation involved:
        # 1: Derivative(E*I_y*Derivative(theta_y(x), x), x) - G*A*(Derivative(defl_z(x), x) + theta_y(x)) + moment_y = 0
        # 2: Derivative(G*A*(Derivative(defl_z(x), x) + theta_y(x)), x) + load_z = 0

        # Substitute value of `G*A*(Derivative(defl_y(x), x) + theta_z(x))` from (2) in (1)
        eq1 = Derivative(E*I_y*Derivative(theta(x), x), x) + (integrate(load[2], x) - C_i) + moment[1]
        slope_y = dsolve(Eq(eq1, 0)).args[1]
        # Solve for constants originated from using dsolve on eq1
        constants = list((linsolve([slope_y.subs(x, 0), slope_y.subs(x, l)], C1, C2).args)[0])
        slope_y = slope_y.subs({C1:constants[0], C2:constants[1]})

        # Put value of slope obtained back in (2) to solve for `C_i` and find deflection across z-axis
        eq2 = G*A*(Derivative(defl(x), x)) + load[2]*x - C_i + G*A*slope_y
        def_z = dsolve(Eq(eq2,0)).args[1]
        # Solve for constants originated from using dsolve on eq2
        constants = list((linsolve([def_z.subs(x, 0), def_z.subs(x, l)], C1, C_i).args)[0])
        self._deflection[2] = def_z.subs({C1:constants[0], C_i:constants[1]})
        self._slope[1] = slope_y.subs(C_i, constants[1])

    def slope(self):
        """
        Returns a three element list representing slope of deflection curve
        along all the three axes.
        """
        return self._slope

    def deflection(self):
        """
        Returns a three element list representing deflection curve along all
        the three axes.
        """
        return self._deflection
