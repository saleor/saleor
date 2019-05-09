from __future__ import print_function, division

from sympy.utilities import dict_merge
from sympy.utilities.iterables import iterable
from sympy.physics.vector import (Dyadic, Vector, ReferenceFrame,
                                  Point, dynamicsymbols)
from sympy.physics.vector.printing import (vprint, vsprint, vpprint, vlatex,
                                           init_vprinting)
from sympy.physics.mechanics.particle import Particle
from sympy.physics.mechanics.rigidbody import RigidBody
from sympy import simplify
from sympy.core.backend import (Matrix, sympify, Mul, Derivative, sin, cos,
                                tan, AppliedUndef, S)

__all__ = ['inertia',
           'inertia_of_point_mass',
           'linear_momentum',
           'angular_momentum',
           'kinetic_energy',
           'potential_energy',
           'Lagrangian',
           'mechanics_printing',
           'mprint',
           'msprint',
           'mpprint',
           'mlatex',
           'msubs',
           'find_dynamicsymbols']

# These are functions that we've moved and renamed during extracting the
# basic vector calculus code from the mechanics packages.

mprint = vprint
msprint = vsprint
mpprint = vpprint
mlatex = vlatex


def mechanics_printing(**kwargs):
    """
    Initializes time derivative printing for all SymPy objects in
    mechanics module.
    """

    init_vprinting(**kwargs)

mechanics_printing.__doc__ = init_vprinting.__doc__


def inertia(frame, ixx, iyy, izz, ixy=0, iyz=0, izx=0):
    """Simple way to create inertia Dyadic object.

    If you don't know what a Dyadic is, just treat this like the inertia
    tensor. Then, do the easy thing and define it in a body-fixed frame.

    Parameters
    ==========

    frame : ReferenceFrame
        The frame the inertia is defined in
    ixx : Sympifyable
        the xx element in the inertia dyadic
    iyy : Sympifyable
        the yy element in the inertia dyadic
    izz : Sympifyable
        the zz element in the inertia dyadic
    ixy : Sympifyable
        the xy element in the inertia dyadic
    iyz : Sympifyable
        the yz element in the inertia dyadic
    izx : Sympifyable
        the zx element in the inertia dyadic

    Examples
    ========

    >>> from sympy.physics.mechanics import ReferenceFrame, inertia
    >>> N = ReferenceFrame('N')
    >>> inertia(N, 1, 2, 3)
    (N.x|N.x) + 2*(N.y|N.y) + 3*(N.z|N.z)

    """

    if not isinstance(frame, ReferenceFrame):
        raise TypeError('Need to define the inertia in a frame')
    ol = sympify(ixx) * (frame.x | frame.x)
    ol += sympify(ixy) * (frame.x | frame.y)
    ol += sympify(izx) * (frame.x | frame.z)
    ol += sympify(ixy) * (frame.y | frame.x)
    ol += sympify(iyy) * (frame.y | frame.y)
    ol += sympify(iyz) * (frame.y | frame.z)
    ol += sympify(izx) * (frame.z | frame.x)
    ol += sympify(iyz) * (frame.z | frame.y)
    ol += sympify(izz) * (frame.z | frame.z)
    return ol


def inertia_of_point_mass(mass, pos_vec, frame):
    """Inertia dyadic of a point mass relative to point O.

    Parameters
    ==========

    mass : Sympifyable
        Mass of the point mass
    pos_vec : Vector
        Position from point O to point mass
    frame : ReferenceFrame
        Reference frame to express the dyadic in

    Examples
    ========

    >>> from sympy import symbols
    >>> from sympy.physics.mechanics import ReferenceFrame, inertia_of_point_mass
    >>> N = ReferenceFrame('N')
    >>> r, m = symbols('r m')
    >>> px = r * N.x
    >>> inertia_of_point_mass(m, px, N)
    m*r**2*(N.y|N.y) + m*r**2*(N.z|N.z)

    """

    return mass * (((frame.x | frame.x) + (frame.y | frame.y) +
                   (frame.z | frame.z)) * (pos_vec & pos_vec) -
                   (pos_vec | pos_vec))


def linear_momentum(frame, *body):
    """Linear momentum of the system.

    This function returns the linear momentum of a system of Particle's and/or
    RigidBody's. The linear momentum of a system is equal to the vector sum of
    the linear momentum of its constituents. Consider a system, S, comprised of
    a rigid body, A, and a particle, P. The linear momentum of the system, L,
    is equal to the vector sum of the linear momentum of the particle, L1, and
    the linear momentum of the rigid body, L2, i.e.

    L = L1 + L2

    Parameters
    ==========

    frame : ReferenceFrame
        The frame in which linear momentum is desired.
    body1, body2, body3... : Particle and/or RigidBody
        The body (or bodies) whose linear momentum is required.

    Examples
    ========

    >>> from sympy.physics.mechanics import Point, Particle, ReferenceFrame
    >>> from sympy.physics.mechanics import RigidBody, outer, linear_momentum
    >>> N = ReferenceFrame('N')
    >>> P = Point('P')
    >>> P.set_vel(N, 10 * N.x)
    >>> Pa = Particle('Pa', P, 1)
    >>> Ac = Point('Ac')
    >>> Ac.set_vel(N, 25 * N.y)
    >>> I = outer(N.x, N.x)
    >>> A = RigidBody('A', Ac, N, 20, (I, Ac))
    >>> linear_momentum(N, A, Pa)
    10*N.x + 500*N.y

    """

    if not isinstance(frame, ReferenceFrame):
        raise TypeError('Please specify a valid ReferenceFrame')
    else:
        linear_momentum_sys = Vector(0)
        for e in body:
            if isinstance(e, (RigidBody, Particle)):
                linear_momentum_sys += e.linear_momentum(frame)
            else:
                raise TypeError('*body must have only Particle or RigidBody')
    return linear_momentum_sys


def angular_momentum(point, frame, *body):
    """Angular momentum of a system

    This function returns the angular momentum of a system of Particle's and/or
    RigidBody's. The angular momentum of such a system is equal to the vector
    sum of the angular momentum of its constituents. Consider a system, S,
    comprised of a rigid body, A, and a particle, P. The angular momentum of
    the system, H, is equal to the vector sum of the angular momentum of the
    particle, H1, and the angular momentum of the rigid body, H2, i.e.

    H = H1 + H2

    Parameters
    ==========

    point : Point
        The point about which angular momentum of the system is desired.
    frame : ReferenceFrame
        The frame in which angular momentum is desired.
    body1, body2, body3... : Particle and/or RigidBody
        The body (or bodies) whose angular momentum is required.

    Examples
    ========

    >>> from sympy.physics.mechanics import Point, Particle, ReferenceFrame
    >>> from sympy.physics.mechanics import RigidBody, outer, angular_momentum
    >>> N = ReferenceFrame('N')
    >>> O = Point('O')
    >>> O.set_vel(N, 0 * N.x)
    >>> P = O.locatenew('P', 1 * N.x)
    >>> P.set_vel(N, 10 * N.x)
    >>> Pa = Particle('Pa', P, 1)
    >>> Ac = O.locatenew('Ac', 2 * N.y)
    >>> Ac.set_vel(N, 5 * N.y)
    >>> a = ReferenceFrame('a')
    >>> a.set_ang_vel(N, 10 * N.z)
    >>> I = outer(N.z, N.z)
    >>> A = RigidBody('A', Ac, a, 20, (I, Ac))
    >>> angular_momentum(O, N, Pa, A)
    10*N.z

    """

    if not isinstance(frame, ReferenceFrame):
        raise TypeError('Please enter a valid ReferenceFrame')
    if not isinstance(point, Point):
        raise TypeError('Please specify a valid Point')
    else:
        angular_momentum_sys = Vector(0)
        for e in body:
            if isinstance(e, (RigidBody, Particle)):
                angular_momentum_sys += e.angular_momentum(point, frame)
            else:
                raise TypeError('*body must have only Particle or RigidBody')
    return angular_momentum_sys


def kinetic_energy(frame, *body):
    """Kinetic energy of a multibody system.

    This function returns the kinetic energy of a system of Particle's and/or
    RigidBody's. The kinetic energy of such a system is equal to the sum of
    the kinetic energies of its constituents. Consider a system, S, comprising
    a rigid body, A, and a particle, P. The kinetic energy of the system, T,
    is equal to the vector sum of the kinetic energy of the particle, T1, and
    the kinetic energy of the rigid body, T2, i.e.

    T = T1 + T2

    Kinetic energy is a scalar.

    Parameters
    ==========

    frame : ReferenceFrame
        The frame in which the velocity or angular velocity of the body is
        defined.
    body1, body2, body3... : Particle and/or RigidBody
        The body (or bodies) whose kinetic energy is required.

    Examples
    ========

    >>> from sympy.physics.mechanics import Point, Particle, ReferenceFrame
    >>> from sympy.physics.mechanics import RigidBody, outer, kinetic_energy
    >>> N = ReferenceFrame('N')
    >>> O = Point('O')
    >>> O.set_vel(N, 0 * N.x)
    >>> P = O.locatenew('P', 1 * N.x)
    >>> P.set_vel(N, 10 * N.x)
    >>> Pa = Particle('Pa', P, 1)
    >>> Ac = O.locatenew('Ac', 2 * N.y)
    >>> Ac.set_vel(N, 5 * N.y)
    >>> a = ReferenceFrame('a')
    >>> a.set_ang_vel(N, 10 * N.z)
    >>> I = outer(N.z, N.z)
    >>> A = RigidBody('A', Ac, a, 20, (I, Ac))
    >>> kinetic_energy(N, Pa, A)
    350

    """

    if not isinstance(frame, ReferenceFrame):
        raise TypeError('Please enter a valid ReferenceFrame')
    ke_sys = S(0)
    for e in body:
        if isinstance(e, (RigidBody, Particle)):
            ke_sys += e.kinetic_energy(frame)
        else:
            raise TypeError('*body must have only Particle or RigidBody')
    return ke_sys


def potential_energy(*body):
    """Potential energy of a multibody system.

    This function returns the potential energy of a system of Particle's and/or
    RigidBody's. The potential energy of such a system is equal to the sum of
    the potential energy of its constituents. Consider a system, S, comprising
    a rigid body, A, and a particle, P. The potential energy of the system, V,
    is equal to the vector sum of the potential energy of the particle, V1, and
    the potential energy of the rigid body, V2, i.e.

    V = V1 + V2

    Potential energy is a scalar.

    Parameters
    ==========

    body1, body2, body3... : Particle and/or RigidBody
        The body (or bodies) whose potential energy is required.

    Examples
    ========

    >>> from sympy.physics.mechanics import Point, Particle, ReferenceFrame
    >>> from sympy.physics.mechanics import RigidBody, outer, potential_energy
    >>> from sympy import symbols
    >>> M, m, g, h = symbols('M m g h')
    >>> N = ReferenceFrame('N')
    >>> O = Point('O')
    >>> O.set_vel(N, 0 * N.x)
    >>> P = O.locatenew('P', 1 * N.x)
    >>> Pa = Particle('Pa', P, m)
    >>> Ac = O.locatenew('Ac', 2 * N.y)
    >>> a = ReferenceFrame('a')
    >>> I = outer(N.z, N.z)
    >>> A = RigidBody('A', Ac, a, M, (I, Ac))
    >>> Pa.potential_energy = m * g * h
    >>> A.potential_energy = M * g * h
    >>> potential_energy(Pa, A)
    M*g*h + g*h*m

    """

    pe_sys = S(0)
    for e in body:
        if isinstance(e, (RigidBody, Particle)):
            pe_sys += e.potential_energy
        else:
            raise TypeError('*body must have only Particle or RigidBody')
    return pe_sys


def gravity(acceleration, *bodies):
    """
    Returns a list of gravity forces given the acceleration
    due to gravity and any number of particles or rigidbodies.

    Example
    =======

    >>> from sympy.physics.mechanics import ReferenceFrame, Point, Particle, outer, RigidBody
    >>> from sympy.physics.mechanics.functions import gravity
    >>> from sympy import symbols
    >>> N = ReferenceFrame('N')
    >>> m, M, g = symbols('m M g')
    >>> F1, F2 = symbols('F1 F2')
    >>> po = Point('po')
    >>> pa = Particle('pa', po, m)
    >>> A = ReferenceFrame('A')
    >>> P = Point('P')
    >>> I = outer(A.x, A.x)
    >>> B = RigidBody('B', P, A, M, (I, P))
    >>> forceList = [(po, F1), (P, F2)]
    >>> forceList.extend(gravity(g*N.y, pa, B))
    >>> forceList
    [(po, F1), (P, F2), (po, g*m*N.y), (P, M*g*N.y)]
    """

    gravity_force = []
    if not bodies:
        raise TypeError("No bodies(instances of Particle or Rigidbody) were passed.")

    for e in bodies:
        point = getattr(e, 'masscenter', None)
        if point is None:
            point = e.point

        gravity_force.append((point, e.mass*acceleration))

    return gravity_force


def center_of_mass(point, *bodies):
    """
    Returns the position vector from the given point to the center of mass
    of the given bodies(particles or rigidbodies).

    Example
    =======

    >>> from sympy import symbols, S
    >>> from sympy.physics.vector import Point
    >>> from sympy.physics.mechanics import Particle, ReferenceFrame, RigidBody, outer
    >>> from sympy.physics.mechanics.functions import center_of_mass
    >>> a = ReferenceFrame('a')
    >>> m = symbols('m', real=True)
    >>> p1 = Particle('p1', Point('p1_pt'), S(1))
    >>> p2 = Particle('p2', Point('p2_pt'), S(2))
    >>> p3 = Particle('p3', Point('p3_pt'), S(3))
    >>> p4 = Particle('p4', Point('p4_pt'), m)
    >>> b_f = ReferenceFrame('b_f')
    >>> b_cm = Point('b_cm')
    >>> mb = symbols('mb')
    >>> b = RigidBody('b', b_cm, b_f, mb, (outer(b_f.x, b_f.x), b_cm))
    >>> p2.point.set_pos(p1.point, a.x)
    >>> p3.point.set_pos(p1.point, a.x + a.y)
    >>> p4.point.set_pos(p1.point, a.y)
    >>> b.masscenter.set_pos(p1.point, a.y + a.z)
    >>> point_o=Point('o')
    >>> point_o.set_pos(p1.point, center_of_mass(p1.point, p1, p2, p3, p4, b))
    >>> expr = 5/(m + mb + 6)*a.x + (m + mb + 3)/(m + mb + 6)*a.y + mb/(m + mb + 6)*a.z
    >>> point_o.pos_from(p1.point)
    5/(m + mb + 6)*a.x + (m + mb + 3)/(m + mb + 6)*a.y + mb/(m + mb + 6)*a.z
    """
    if not bodies:
        raise TypeError("No bodies(instances of Particle or Rigidbody) were passed.")

    total_mass = 0
    vec = Vector(0)
    for i in bodies:
        total_mass += i.mass

        masscenter = getattr(i, 'masscenter', None)
        if masscenter is None:
            masscenter = i.point
        vec += i.mass*masscenter.pos_from(point)

    return vec/total_mass


def Lagrangian(frame, *body):
    """Lagrangian of a multibody system.

    This function returns the Lagrangian of a system of Particle's and/or
    RigidBody's. The Lagrangian of such a system is equal to the difference
    between the kinetic energies and potential energies of its constituents. If
    T and V are the kinetic and potential energies of a system then it's
    Lagrangian, L, is defined as

    L = T - V

    The Lagrangian is a scalar.

    Parameters
    ==========

    frame : ReferenceFrame
        The frame in which the velocity or angular velocity of the body is
        defined to determine the kinetic energy.

    body1, body2, body3... : Particle and/or RigidBody
        The body (or bodies) whose Lagrangian is required.

    Examples
    ========

    >>> from sympy.physics.mechanics import Point, Particle, ReferenceFrame
    >>> from sympy.physics.mechanics import RigidBody, outer, Lagrangian
    >>> from sympy import symbols
    >>> M, m, g, h = symbols('M m g h')
    >>> N = ReferenceFrame('N')
    >>> O = Point('O')
    >>> O.set_vel(N, 0 * N.x)
    >>> P = O.locatenew('P', 1 * N.x)
    >>> P.set_vel(N, 10 * N.x)
    >>> Pa = Particle('Pa', P, 1)
    >>> Ac = O.locatenew('Ac', 2 * N.y)
    >>> Ac.set_vel(N, 5 * N.y)
    >>> a = ReferenceFrame('a')
    >>> a.set_ang_vel(N, 10 * N.z)
    >>> I = outer(N.z, N.z)
    >>> A = RigidBody('A', Ac, a, 20, (I, Ac))
    >>> Pa.potential_energy = m * g * h
    >>> A.potential_energy = M * g * h
    >>> Lagrangian(N, Pa, A)
    -M*g*h - g*h*m + 350

    """

    if not isinstance(frame, ReferenceFrame):
        raise TypeError('Please supply a valid ReferenceFrame')
    for e in body:
        if not isinstance(e, (RigidBody, Particle)):
            raise TypeError('*body must have only Particle or RigidBody')
    return kinetic_energy(frame, *body) - potential_energy(*body)


def find_dynamicsymbols(expression, exclude=None, reference_frame=None):
    """Find all dynamicsymbols in expression.

    If the optional ``exclude`` kwarg is used, only dynamicsymbols
    not in the iterable ``exclude`` are returned.
    If we intend to apply this function on a vector, the optional
    ''reference_frame'' is also used to inform about the corresponding frame
    with respect to which the dynamic symbols of the given vector is to be
    determined.

    Parameters
    ==========

    expression : sympy expression

    exclude : iterable of dynamicsymbols, optional

    reference_frame : ReferenceFrame, optional
        The frame with respect to which the dynamic symbols of the
        given vector is to be determined.

    Examples
    ========

    >>> from sympy.physics.mechanics import dynamicsymbols, find_dynamicsymbols
    >>> from sympy.physics.mechanics import ReferenceFrame
    >>> x, y = dynamicsymbols('x, y')
    >>> expr = x + x.diff()*y
    >>> find_dynamicsymbols(expr)
    {x(t), y(t), Derivative(x(t), t)}
    >>> find_dynamicsymbols(expr, exclude=[x, y])
    {Derivative(x(t), t)}
    >>> a, b, c = dynamicsymbols('a, b, c')
    >>> A = ReferenceFrame('A')
    >>> v = a * A.x + b * A.y + c * A.z
    >>> find_dynamicsymbols(v, reference_frame=A)
    {a(t), b(t), c(t)}

    """
    t_set = {dynamicsymbols._t}
    if exclude:
        if iterable(exclude):
            exclude_set = set(exclude)
        else:
            raise TypeError("exclude kwarg must be iterable")
    else:
        exclude_set = set()
    if isinstance(expression, Vector):
        if reference_frame is None:
            raise ValueError("You must provide reference_frame when passing a "
                             "vector expression, got %s." % reference_frame)
        else:
            expression = expression.to_matrix(reference_frame)
    return set([i for i in expression.atoms(AppliedUndef, Derivative) if
            i.free_symbols == t_set]) - exclude_set


def msubs(expr, *sub_dicts, **kwargs):
    """A custom subs for use on expressions derived in physics.mechanics.

    Traverses the expression tree once, performing the subs found in sub_dicts.
    Terms inside ``Derivative`` expressions are ignored:

    >>> from sympy.physics.mechanics import dynamicsymbols, msubs
    >>> x = dynamicsymbols('x')
    >>> msubs(x.diff() + x, {x: 1})
    Derivative(x(t), t) + 1

    Note that sub_dicts can be a single dictionary, or several dictionaries:

    >>> x, y, z = dynamicsymbols('x, y, z')
    >>> sub1 = {x: 1, y: 2}
    >>> sub2 = {z: 3, x.diff(): 4}
    >>> msubs(x.diff() + x + y + z, sub1, sub2)
    10

    If smart=True (default False), also checks for conditions that may result
    in ``nan``, but if simplified would yield a valid expression. For example:

    >>> from sympy import sin, tan
    >>> (sin(x)/tan(x)).subs(x, 0)
    nan
    >>> msubs(sin(x)/tan(x), {x: 0}, smart=True)
    1

    It does this by first replacing all ``tan`` with ``sin/cos``. Then each
    node is traversed. If the node is a fraction, subs is first evaluated on
    the denominator. If this results in 0, simplification of the entire
    fraction is attempted. Using this selective simplification, only
    subexpressions that result in 1/0 are targeted, resulting in faster
    performance.

    """

    sub_dict = dict_merge(*sub_dicts)
    smart = kwargs.pop('smart', False)
    if smart:
        func = _smart_subs
    elif hasattr(expr, 'msubs'):
        return expr.msubs(sub_dict)
    else:
        func = lambda expr, sub_dict: _crawl(expr, _sub_func, sub_dict)
    if isinstance(expr, (Matrix, Vector, Dyadic)):
        return expr.applyfunc(lambda x: func(x, sub_dict))
    else:
        return func(expr, sub_dict)


def _crawl(expr, func, *args, **kwargs):
    """Crawl the expression tree, and apply func to every node."""
    val = func(expr, *args, **kwargs)
    if val is not None:
        return val
    new_args = (_crawl(arg, func, *args, **kwargs) for arg in expr.args)
    return expr.func(*new_args)


def _sub_func(expr, sub_dict):
    """Perform direct matching substitution, ignoring derivatives."""
    if expr in sub_dict:
        return sub_dict[expr]
    elif not expr.args or expr.is_Derivative:
        return expr


def _tan_repl_func(expr):
    """Replace tan with sin/cos."""
    if isinstance(expr, tan):
        return sin(*expr.args) / cos(*expr.args)
    elif not expr.args or expr.is_Derivative:
        return expr


def _smart_subs(expr, sub_dict):
    """Performs subs, checking for conditions that may result in `nan` or
    `oo`, and attempts to simplify them out.

    The expression tree is traversed twice, and the following steps are
    performed on each expression node:
    - First traverse:
        Replace all `tan` with `sin/cos`.
    - Second traverse:
        If node is a fraction, check if the denominator evaluates to 0.
        If so, attempt to simplify it out. Then if node is in sub_dict,
        sub in the corresponding value."""
    expr = _crawl(expr, _tan_repl_func)

    def _recurser(expr, sub_dict):
        # Decompose the expression into num, den
        num, den = _fraction_decomp(expr)
        if den != 1:
            # If there is a non trivial denominator, we need to handle it
            denom_subbed = _recurser(den, sub_dict)
            if denom_subbed.evalf() == 0:
                # If denom is 0 after this, attempt to simplify the bad expr
                expr = simplify(expr)
            else:
                # Expression won't result in nan, find numerator
                num_subbed = _recurser(num, sub_dict)
                return num_subbed / denom_subbed
        # We have to crawl the tree manually, because `expr` may have been
        # modified in the simplify step. First, perform subs as normal:
        val = _sub_func(expr, sub_dict)
        if val is not None:
            return val
        new_args = (_recurser(arg, sub_dict) for arg in expr.args)
        return expr.func(*new_args)
    return _recurser(expr, sub_dict)


def _fraction_decomp(expr):
    """Return num, den such that expr = num/den"""
    if not isinstance(expr, Mul):
        return expr, 1
    num = []
    den = []
    for a in expr.args:
        if a.is_Pow and a.args[1] < 0:
            den.append(1 / a)
        else:
            num.append(a)
    if not den:
        return expr, 1
    num = Mul(*num)
    den = Mul(*den)
    return num, den


def _f_list_parser(fl, ref_frame):
    """Parses the provided forcelist composed of items
    of the form (obj, force).
    Returns a tuple containing:
        vel_list: The velocity (ang_vel for Frames, vel for Points) in
                the provided reference frame.
        f_list: The forces.

    Used internally in the KanesMethod and LagrangesMethod classes.
    """
    def flist_iter():
        for pair in fl:
            obj, force = pair
            if isinstance(obj, ReferenceFrame):
                yield obj.ang_vel_in(ref_frame), force
            elif isinstance(obj, Point):
                yield obj.vel(ref_frame), force
            else:
                raise TypeError('First entry in each forcelist pair must '
                                'be a point or frame.')

    if not fl:
        vel_list, f_list = (), ()
    else:
        unzip = lambda l: list(zip(*l)) if l[0] else [(), ()]
        vel_list, f_list = unzip(list(flist_iter()))
    return vel_list, f_list
