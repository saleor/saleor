from sympy.core.backend import Symbol
from sympy.physics.mechanics import (RigidBody, Particle, ReferenceFrame,
                                     inertia)
from sympy.physics.vector import Point, Vector

__all__ = ['Body']


class Body(RigidBody, Particle):
    """
    Body is a common representation of either a RigidBody or a Particle SymPy
    object depending on what is passed in during initialization. If a mass is
    passed in and central_inertia is left as None, the Particle object is
    created. Otherwise a RigidBody object will be created.

    The attributes that Body possesses will be the same as a Particle instance
    or a Rigid Body instance depending on which was created. Additional
    attributes are listed below.

    Attributes
    ==========

    name : string
        The body's name
    masscenter : Point
        The point which represents the center of mass of the rigid body
    frame : ReferenceFrame
        The reference frame which the body is fixed in
    mass : Sympifyable
        The body's mass
    inertia : (Dyadic, Point)
        The body's inertia around its center of mass. This attribute is specific
        to the rigid body form of Body and is left undefined for the Particle
        form
    loads : iterable
        This list contains information on the different loads acting on the
        Body. Forces are listed as a (point, vector) tuple and torques are
        listed as (reference frame, vector) tuples.

    Parameters
    ==========

    name : String
        Defines the name of the body. It is used as the base for defining
        body specific properties.
    masscenter : Point, optional
        A point that represents the center of mass of the body or particle.
        If no point is given, a point is generated.
    mass : Sympifyable, optional
        A Sympifyable object which represents the mass of the body. If no
        mass is passed, one is generated.
    frame : ReferenceFrame, optional
        The ReferenceFrame that represents the reference frame of the body.
        If no frame is given, a frame is generated.
    central_inertia : Dyadic, optional
        Central inertia dyadic of the body. If none is passed while creating
        RigidBody, a default inertia is generated.

    Examples
    ========

    Default behaviour. This results in the creation of a RigidBody object for
    which the mass, mass center, frame and inertia attributes are given default
    values. ::

        >>> from sympy.physics.mechanics import Body
        >>> body = Body('name_of_body')

    This next example demonstrates the code required to specify all of the
    values of the Body object. Note this will also create a RigidBody version of
    the Body object. ::

        >>> from sympy import Symbol
        >>> from sympy.physics.mechanics import ReferenceFrame, Point, inertia
        >>> from sympy.physics.mechanics import Body
        >>> mass = Symbol('mass')
        >>> masscenter = Point('masscenter')
        >>> frame = ReferenceFrame('frame')
        >>> ixx = Symbol('ixx')
        >>> body_inertia = inertia(frame, ixx, 0, 0)
        >>> body = Body('name_of_body', masscenter, mass, frame, body_inertia)

    The minimal code required to create a Particle version of the Body object
    involves simply passing in a name and a mass. ::

        >>> from sympy import Symbol
        >>> from sympy.physics.mechanics import Body
        >>> mass = Symbol('mass')
        >>> body = Body('name_of_body', mass=mass)

    The Particle version of the Body object can also receive a masscenter point
    and a reference frame, just not an inertia.
    """

    def __init__(self, name, masscenter=None, mass=None, frame=None,
                 central_inertia=None):

        self.name = name
        self.loads = []

        if frame is None:
            frame = ReferenceFrame(name + '_frame')

        if masscenter is None:
            masscenter = Point(name + '_masscenter')

        if central_inertia is None and mass is None:
            ixx = Symbol(name + '_ixx')
            iyy = Symbol(name + '_iyy')
            izz = Symbol(name + '_izz')
            izx = Symbol(name + '_izx')
            ixy = Symbol(name + '_ixy')
            iyz = Symbol(name + '_iyz')
            _inertia = (inertia(frame, ixx, iyy, izz, ixy, iyz, izx),
                        masscenter)
        else:
            _inertia = (central_inertia, masscenter)

        if mass is None:
            _mass = Symbol(name + '_mass')
        else:
            _mass = mass

        masscenter.set_vel(frame, 0)

        # If user passes masscenter and mass then a particle is created
        # otherwise a rigidbody. As a result a body may or may not have inertia.
        if central_inertia is None and mass is not None:
            self.frame = frame
            self.masscenter = masscenter
            Particle.__init__(self, name, masscenter, _mass)
        else:
            RigidBody.__init__(self, name, masscenter, frame, _mass, _inertia)

    def apply_force(self, vec, point=None):
        """
        Adds a force to a point (center of mass by default) on the body.

        Parameters
        ==========

        vec: Vector
            Defines the force vector. Can be any vector w.r.t any frame or
            combinations of frames.
        point: Point, optional
            Defines the point on which the force is applied. Default is the
            Body's center of mass.

        Example
        =======

        The first example applies a gravitational force in the x direction of
        Body's frame to the body's center of mass. ::

            >>> from sympy import Symbol
            >>> from sympy.physics.mechanics import Body
            >>> body = Body('body')
            >>> g = Symbol('g')
            >>> body.apply_force(body.mass * g * body.frame.x)

        To apply force to any other point than center of mass, pass that point
        as well. This example applies a gravitational force to a point a
        distance l from the body's center of mass in the y direction. The
        force is again applied in the x direction. ::

            >>> from sympy import Symbol
            >>> from sympy.physics.mechanics import Body
            >>> body = Body('body')
            >>> g = Symbol('g')
            >>> l = Symbol('l')
            >>> point = body.masscenter.locatenew('force_point', l *
            ...                                   body.frame.y)
            >>> body.apply_force(body.mass * g * body.frame.x, point)

        """

        if not isinstance(point, Point):
            if point is None:
                point = self.masscenter  # masscenter
            else:
                raise TypeError("A Point must be supplied to apply force to.")
        if not isinstance(vec, Vector):
            raise TypeError("A Vector must be supplied to apply force.")

        self.loads.append((point, vec))

    def apply_torque(self, vec):
        """
        Adds a torque to the body.

        Parameters
        ==========

        vec: Vector
            Defines the torque vector. Can be any vector w.r.t any frame or
            combinations of frame.

        Example
        =======

        This example adds a simple torque around the body's z axis. ::

            >>> from sympy import Symbol
            >>> from sympy.physics.mechanics import Body
            >>> body = Body('body')
            >>> T = Symbol('T')
            >>> body.apply_torque(T * body.frame.z)
        """

        if not isinstance(vec, Vector):
            raise TypeError("A Vector must be supplied to add torque.")
        self.loads.append((self.frame, vec))
