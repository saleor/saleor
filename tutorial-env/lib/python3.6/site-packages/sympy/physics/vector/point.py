from __future__ import print_function, division
from sympy.core.compatibility import range, string_types
from .vector import Vector, _check_vector
from .frame import _check_frame

__all__ = ['Point']


class Point(object):
    """This object represents a point in a dynamic system.

    It stores the: position, velocity, and acceleration of a point.
    The position is a vector defined as the vector distance from a parent
    point to this point.

    """

    def __init__(self, name):
        """Initialization of a Point object. """
        self.name = name
        self._pos_dict = {}
        self._vel_dict = {}
        self._acc_dict = {}
        self._pdlist = [self._pos_dict, self._vel_dict, self._acc_dict]

    def __str__(self):
        return self.name

    __repr__ = __str__

    def _check_point(self, other):
        if not isinstance(other, Point):
            raise TypeError('A Point must be supplied')

    def _pdict_list(self, other, num):
        """Creates a list from self to other using _dcm_dict. """
        outlist = [[self]]
        oldlist = [[]]
        while outlist != oldlist:
            oldlist = outlist[:]
            for i, v in enumerate(outlist):
                templist = v[-1]._pdlist[num].keys()
                for i2, v2 in enumerate(templist):
                    if not v.__contains__(v2):
                        littletemplist = v + [v2]
                        if not outlist.__contains__(littletemplist):
                            outlist.append(littletemplist)
        for i, v in enumerate(oldlist):
            if v[-1] != other:
                outlist.remove(v)
        outlist.sort(key=len)
        if len(outlist) != 0:
            return outlist[0]
        raise ValueError('No Connecting Path found between ' + other.name +
                         ' and ' + self.name)

    def a1pt_theory(self, otherpoint, outframe, interframe):
        """Sets the acceleration of this point with the 1-point theory.

        The 1-point theory for point acceleration looks like this:

        ^N a^P = ^B a^P + ^N a^O + ^N alpha^B x r^OP + ^N omega^B x (^N omega^B
        x r^OP) + 2 ^N omega^B x ^B v^P

        where O is a point fixed in B, P is a point moving in B, and B is
        rotating in frame N.

        Parameters
        ==========

        otherpoint : Point
            The first point of the 1-point theory (O)
        outframe : ReferenceFrame
            The frame we want this point's acceleration defined in (N)
        fixedframe : ReferenceFrame
            The intermediate frame in this calculation (B)

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame
        >>> from sympy.physics.vector import Vector, dynamicsymbols
        >>> q = dynamicsymbols('q')
        >>> q2 = dynamicsymbols('q2')
        >>> qd = dynamicsymbols('q', 1)
        >>> q2d = dynamicsymbols('q2', 1)
        >>> N = ReferenceFrame('N')
        >>> B = ReferenceFrame('B')
        >>> B.set_ang_vel(N, 5 * B.y)
        >>> O = Point('O')
        >>> P = O.locatenew('P', q * B.x)
        >>> P.set_vel(B, qd * B.x + q2d * B.y)
        >>> O.set_vel(N, 0)
        >>> P.a1pt_theory(O, N, B)
        (-25*q + q'')*B.x + q2''*B.y - 10*q'*B.z

        """

        _check_frame(outframe)
        _check_frame(interframe)
        self._check_point(otherpoint)
        dist = self.pos_from(otherpoint)
        v = self.vel(interframe)
        a1 = otherpoint.acc(outframe)
        a2 = self.acc(interframe)
        omega = interframe.ang_vel_in(outframe)
        alpha = interframe.ang_acc_in(outframe)
        self.set_acc(outframe, a2 + 2 * (omega ^ v) + a1 + (alpha ^ dist) +
                (omega ^ (omega ^ dist)))
        return self.acc(outframe)

    def a2pt_theory(self, otherpoint, outframe, fixedframe):
        """Sets the acceleration of this point with the 2-point theory.

        The 2-point theory for point acceleration looks like this:

        ^N a^P = ^N a^O + ^N alpha^B x r^OP + ^N omega^B x (^N omega^B x r^OP)

        where O and P are both points fixed in frame B, which is rotating in
        frame N.

        Parameters
        ==========

        otherpoint : Point
            The first point of the 2-point theory (O)
        outframe : ReferenceFrame
            The frame we want this point's acceleration defined in (N)
        fixedframe : ReferenceFrame
            The frame in which both points are fixed (B)

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame, dynamicsymbols
        >>> q = dynamicsymbols('q')
        >>> qd = dynamicsymbols('q', 1)
        >>> N = ReferenceFrame('N')
        >>> B = N.orientnew('B', 'Axis', [q, N.z])
        >>> O = Point('O')
        >>> P = O.locatenew('P', 10 * B.x)
        >>> O.set_vel(N, 5 * N.x)
        >>> P.a2pt_theory(O, N, B)
        - 10*q'**2*B.x + 10*q''*B.y

        """

        _check_frame(outframe)
        _check_frame(fixedframe)
        self._check_point(otherpoint)
        dist = self.pos_from(otherpoint)
        a = otherpoint.acc(outframe)
        omega = fixedframe.ang_vel_in(outframe)
        alpha = fixedframe.ang_acc_in(outframe)
        self.set_acc(outframe, a + (alpha ^ dist) + (omega ^ (omega ^ dist)))
        return self.acc(outframe)

    def acc(self, frame):
        """The acceleration Vector of this Point in a ReferenceFrame.

        Parameters
        ==========

        frame : ReferenceFrame
            The frame in which the returned acceleration vector will be defined in

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame
        >>> N = ReferenceFrame('N')
        >>> p1 = Point('p1')
        >>> p1.set_acc(N, 10 * N.x)
        >>> p1.acc(N)
        10*N.x

        """

        _check_frame(frame)
        if not (frame in self._acc_dict):
            if self._vel_dict[frame] != 0:
                return (self._vel_dict[frame]).dt(frame)
            else:
                return Vector(0)
        return self._acc_dict[frame]

    def locatenew(self, name, value):
        """Creates a new point with a position defined from this point.

        Parameters
        ==========

        name : str
            The name for the new point
        value : Vector
            The position of the new point relative to this point

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Point
        >>> N = ReferenceFrame('N')
        >>> P1 = Point('P1')
        >>> P2 = P1.locatenew('P2', 10 * N.x)

        """

        if not isinstance(name, string_types):
            raise TypeError('Must supply a valid name')
        if value == 0:
            value = Vector(0)
        value = _check_vector(value)
        p = Point(name)
        p.set_pos(self, value)
        self.set_pos(p, -value)
        return p

    def pos_from(self, otherpoint):
        """Returns a Vector distance between this Point and the other Point.

        Parameters
        ==========

        otherpoint : Point
            The otherpoint we are locating this one relative to

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame
        >>> N = ReferenceFrame('N')
        >>> p1 = Point('p1')
        >>> p2 = Point('p2')
        >>> p1.set_pos(p2, 10 * N.x)
        >>> p1.pos_from(p2)
        10*N.x

        """

        outvec = Vector(0)
        plist = self._pdict_list(otherpoint, 0)
        for i in range(len(plist) - 1):
            outvec += plist[i]._pos_dict[plist[i + 1]]
        return outvec

    def set_acc(self, frame, value):
        """Used to set the acceleration of this Point in a ReferenceFrame.

        Parameters
        ==========

        frame : ReferenceFrame
            The frame in which this point's acceleration is defined
        value : Vector
            The vector value of this point's acceleration in the frame

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame
        >>> N = ReferenceFrame('N')
        >>> p1 = Point('p1')
        >>> p1.set_acc(N, 10 * N.x)
        >>> p1.acc(N)
        10*N.x

        """

        if value == 0:
            value = Vector(0)
        value = _check_vector(value)
        _check_frame(frame)
        self._acc_dict.update({frame: value})

    def set_pos(self, otherpoint, value):
        """Used to set the position of this point w.r.t. another point.

        Parameters
        ==========

        otherpoint : Point
            The other point which this point's location is defined relative to
        value : Vector
            The vector which defines the location of this point

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame
        >>> N = ReferenceFrame('N')
        >>> p1 = Point('p1')
        >>> p2 = Point('p2')
        >>> p1.set_pos(p2, 10 * N.x)
        >>> p1.pos_from(p2)
        10*N.x

        """

        if value == 0:
            value = Vector(0)
        value = _check_vector(value)
        self._check_point(otherpoint)
        self._pos_dict.update({otherpoint: value})
        otherpoint._pos_dict.update({self: -value})

    def set_vel(self, frame, value):
        """Sets the velocity Vector of this Point in a ReferenceFrame.

        Parameters
        ==========

        frame : ReferenceFrame
            The frame in which this point's velocity is defined
        value : Vector
            The vector value of this point's velocity in the frame

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame
        >>> N = ReferenceFrame('N')
        >>> p1 = Point('p1')
        >>> p1.set_vel(N, 10 * N.x)
        >>> p1.vel(N)
        10*N.x

        """

        if value == 0:
            value = Vector(0)
        value = _check_vector(value)
        _check_frame(frame)
        self._vel_dict.update({frame: value})

    def v1pt_theory(self, otherpoint, outframe, interframe):
        """Sets the velocity of this point with the 1-point theory.

        The 1-point theory for point velocity looks like this:

        ^N v^P = ^B v^P + ^N v^O + ^N omega^B x r^OP

        where O is a point fixed in B, P is a point moving in B, and B is
        rotating in frame N.

        Parameters
        ==========

        otherpoint : Point
            The first point of the 2-point theory (O)
        outframe : ReferenceFrame
            The frame we want this point's velocity defined in (N)
        interframe : ReferenceFrame
            The intermediate frame in this calculation (B)

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame
        >>> from sympy.physics.vector import Vector, dynamicsymbols
        >>> q = dynamicsymbols('q')
        >>> q2 = dynamicsymbols('q2')
        >>> qd = dynamicsymbols('q', 1)
        >>> q2d = dynamicsymbols('q2', 1)
        >>> N = ReferenceFrame('N')
        >>> B = ReferenceFrame('B')
        >>> B.set_ang_vel(N, 5 * B.y)
        >>> O = Point('O')
        >>> P = O.locatenew('P', q * B.x)
        >>> P.set_vel(B, qd * B.x + q2d * B.y)
        >>> O.set_vel(N, 0)
        >>> P.v1pt_theory(O, N, B)
        q'*B.x + q2'*B.y - 5*q*B.z

        """

        _check_frame(outframe)
        _check_frame(interframe)
        self._check_point(otherpoint)
        dist = self.pos_from(otherpoint)
        v1 = self.vel(interframe)
        v2 = otherpoint.vel(outframe)
        omega = interframe.ang_vel_in(outframe)
        self.set_vel(outframe, v1 + v2 + (omega ^ dist))
        return self.vel(outframe)

    def v2pt_theory(self, otherpoint, outframe, fixedframe):
        """Sets the velocity of this point with the 2-point theory.

        The 2-point theory for point velocity looks like this:

        ^N v^P = ^N v^O + ^N omega^B x r^OP

        where O and P are both points fixed in frame B, which is rotating in
        frame N.

        Parameters
        ==========

        otherpoint : Point
            The first point of the 2-point theory (O)
        outframe : ReferenceFrame
            The frame we want this point's velocity defined in (N)
        fixedframe : ReferenceFrame
            The frame in which both points are fixed (B)

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame, dynamicsymbols
        >>> q = dynamicsymbols('q')
        >>> qd = dynamicsymbols('q', 1)
        >>> N = ReferenceFrame('N')
        >>> B = N.orientnew('B', 'Axis', [q, N.z])
        >>> O = Point('O')
        >>> P = O.locatenew('P', 10 * B.x)
        >>> O.set_vel(N, 5 * N.x)
        >>> P.v2pt_theory(O, N, B)
        5*N.x + 10*q'*B.y

        """

        _check_frame(outframe)
        _check_frame(fixedframe)
        self._check_point(otherpoint)
        dist = self.pos_from(otherpoint)
        v = otherpoint.vel(outframe)
        omega = fixedframe.ang_vel_in(outframe)
        self.set_vel(outframe, v + (omega ^ dist))
        return self.vel(outframe)

    def vel(self, frame):
        """The velocity Vector of this Point in the ReferenceFrame.

        Parameters
        ==========

        frame : ReferenceFrame
            The frame in which the returned velocity vector will be defined in

        Examples
        ========

        >>> from sympy.physics.vector import Point, ReferenceFrame
        >>> N = ReferenceFrame('N')
        >>> p1 = Point('p1')
        >>> p1.set_vel(N, 10 * N.x)
        >>> p1.vel(N)
        10*N.x

        """

        _check_frame(frame)
        if not (frame in self._vel_dict):
            raise ValueError('Velocity of point ' + self.name + ' has not been'
                             ' defined in ReferenceFrame ' + frame.name)
        return self._vel_dict[frame]

    def partial_velocity(self, frame, *gen_speeds):
        """Returns the partial velocities of the linear velocity vector of this
        point in the given frame with respect to one or more provided
        generalized speeds.

        Parameters
        ==========
        frame : ReferenceFrame
            The frame with which the velocity is defined in.
        gen_speeds : functions of time
            The generalized speeds.

        Returns
        =======
        partial_velocities : tuple of Vector
            The partial velocity vectors corresponding to the provided
            generalized speeds.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Point
        >>> from sympy.physics.vector import dynamicsymbols
        >>> N = ReferenceFrame('N')
        >>> A = ReferenceFrame('A')
        >>> p = Point('p')
        >>> u1, u2 = dynamicsymbols('u1, u2')
        >>> p.set_vel(N, u1 * N.x + u2 * A.y)
        >>> p.partial_velocity(N, u1)
        N.x
        >>> p.partial_velocity(N, u1, u2)
        (N.x, A.y)

        """
        partials = [self.vel(frame).diff(speed, frame, var_in_dcm=False) for
                    speed in gen_speeds]

        if len(partials) == 1:
            return partials[0]
        else:
            return tuple(partials)
