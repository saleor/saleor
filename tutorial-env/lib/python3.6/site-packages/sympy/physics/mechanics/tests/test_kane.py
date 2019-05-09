from sympy.utilities.pytest import warns_deprecated_sympy

from sympy.core.backend import (cos, expand, Matrix, sin, symbols, tan, sqrt, S,
                                zeros)
from sympy import simplify
from sympy.physics.mechanics import (dynamicsymbols, ReferenceFrame, Point,
                                     RigidBody, KanesMethod, inertia, Particle,
                                     dot)


def test_one_dof():
    # This is for a 1 dof spring-mass-damper case.
    # It is described in more detail in the KanesMethod docstring.
    q, u = dynamicsymbols('q u')
    qd, ud = dynamicsymbols('q u', 1)
    m, c, k = symbols('m c k')
    N = ReferenceFrame('N')
    P = Point('P')
    P.set_vel(N, u * N.x)

    kd = [qd - u]
    FL = [(P, (-k * q - c * u) * N.x)]
    pa = Particle('pa', P, m)
    BL = [pa]

    KM = KanesMethod(N, [q], [u], kd)
    # The old input format raises a deprecation warning, so catch it here so
    # it doesn't cause py.test to fail.
    with warns_deprecated_sympy():
        KM.kanes_equations(FL, BL)

    MM = KM.mass_matrix
    forcing = KM.forcing
    rhs = MM.inv() * forcing
    assert expand(rhs[0]) == expand(-(q * k + u * c) / m)

    assert simplify(KM.rhs() -
                    KM.mass_matrix_full.LUsolve(KM.forcing_full)) == zeros(2, 1)

    assert (KM.linearize(A_and_B=True, )[0] == Matrix([[0, 1], [-k/m, -c/m]]))


def test_two_dof():
    # This is for a 2 d.o.f., 2 particle spring-mass-damper.
    # The first coordinate is the displacement of the first particle, and the
    # second is the relative displacement between the first and second
    # particles. Speeds are defined as the time derivatives of the particles.
    q1, q2, u1, u2 = dynamicsymbols('q1 q2 u1 u2')
    q1d, q2d, u1d, u2d = dynamicsymbols('q1 q2 u1 u2', 1)
    m, c1, c2, k1, k2 = symbols('m c1 c2 k1 k2')
    N = ReferenceFrame('N')
    P1 = Point('P1')
    P2 = Point('P2')
    P1.set_vel(N, u1 * N.x)
    P2.set_vel(N, (u1 + u2) * N.x)
    kd = [q1d - u1, q2d - u2]

    # Now we create the list of forces, then assign properties to each
    # particle, then create a list of all particles.
    FL = [(P1, (-k1 * q1 - c1 * u1 + k2 * q2 + c2 * u2) * N.x), (P2, (-k2 *
        q2 - c2 * u2) * N.x)]
    pa1 = Particle('pa1', P1, m)
    pa2 = Particle('pa2', P2, m)
    BL = [pa1, pa2]

    # Finally we create the KanesMethod object, specify the inertial frame,
    # pass relevant information, and form Fr & Fr*. Then we calculate the mass
    # matrix and forcing terms, and finally solve for the udots.
    KM = KanesMethod(N, q_ind=[q1, q2], u_ind=[u1, u2], kd_eqs=kd)
    # The old input format raises a deprecation warning, so catch it here so
    # it doesn't cause py.test to fail.
    with warns_deprecated_sympy():
        KM.kanes_equations(FL, BL)
    MM = KM.mass_matrix
    forcing = KM.forcing
    rhs = MM.inv() * forcing
    assert expand(rhs[0]) == expand((-k1 * q1 - c1 * u1 + k2 * q2 + c2 * u2)/m)
    assert expand(rhs[1]) == expand((k1 * q1 + c1 * u1 - 2 * k2 * q2 - 2 *
                                    c2 * u2) / m)

    assert simplify(KM.rhs() -
                    KM.mass_matrix_full.LUsolve(KM.forcing_full)) == zeros(4, 1)


def test_pend():
    q, u = dynamicsymbols('q u')
    qd, ud = dynamicsymbols('q u', 1)
    m, l, g = symbols('m l g')
    N = ReferenceFrame('N')
    P = Point('P')
    P.set_vel(N, -l * u * sin(q) * N.x + l * u * cos(q) * N.y)
    kd = [qd - u]

    FL = [(P, m * g * N.x)]
    pa = Particle('pa', P, m)
    BL = [pa]

    KM = KanesMethod(N, [q], [u], kd)
    with warns_deprecated_sympy():
        KM.kanes_equations(FL, BL)
    MM = KM.mass_matrix
    forcing = KM.forcing
    rhs = MM.inv() * forcing
    rhs.simplify()
    assert expand(rhs[0]) == expand(-g / l * sin(q))
    assert simplify(KM.rhs() -
                    KM.mass_matrix_full.LUsolve(KM.forcing_full)) == zeros(2, 1)


def test_rolling_disc():
    # Rolling Disc Example
    # Here the rolling disc is formed from the contact point up, removing the
    # need to introduce generalized speeds. Only 3 configuration and three
    # speed variables are need to describe this system, along with the disc's
    # mass and radius, and the local gravity (note that mass will drop out).
    q1, q2, q3, u1, u2, u3 = dynamicsymbols('q1 q2 q3 u1 u2 u3')
    q1d, q2d, q3d, u1d, u2d, u3d = dynamicsymbols('q1 q2 q3 u1 u2 u3', 1)
    r, m, g = symbols('r m g')

    # The kinematics are formed by a series of simple rotations. Each simple
    # rotation creates a new frame, and the next rotation is defined by the new
    # frame's basis vectors. This example uses a 3-1-2 series of rotations, or
    # Z, X, Y series of rotations. Angular velocity for this is defined using
    # the second frame's basis (the lean frame).
    N = ReferenceFrame('N')
    Y = N.orientnew('Y', 'Axis', [q1, N.z])
    L = Y.orientnew('L', 'Axis', [q2, Y.x])
    R = L.orientnew('R', 'Axis', [q3, L.y])
    w_R_N_qd = R.ang_vel_in(N)
    R.set_ang_vel(N, u1 * L.x + u2 * L.y + u3 * L.z)

    # This is the translational kinematics. We create a point with no velocity
    # in N; this is the contact point between the disc and ground. Next we form
    # the position vector from the contact point to the disc's center of mass.
    # Finally we form the velocity and acceleration of the disc.
    C = Point('C')
    C.set_vel(N, 0)
    Dmc = C.locatenew('Dmc', r * L.z)
    Dmc.v2pt_theory(C, N, R)

    # This is a simple way to form the inertia dyadic.
    I = inertia(L, m / 4 * r**2, m / 2 * r**2, m / 4 * r**2)

    # Kinematic differential equations; how the generalized coordinate time
    # derivatives relate to generalized speeds.
    kd = [dot(R.ang_vel_in(N) - w_R_N_qd, uv) for uv in L]

    # Creation of the force list; it is the gravitational force at the mass
    # center of the disc. Then we create the disc by assigning a Point to the
    # center of mass attribute, a ReferenceFrame to the frame attribute, and mass
    # and inertia. Then we form the body list.
    ForceList = [(Dmc, - m * g * Y.z)]
    BodyD = RigidBody('BodyD', Dmc, R, m, (I, Dmc))
    BodyList = [BodyD]

    # Finally we form the equations of motion, using the same steps we did
    # before. Specify inertial frame, supply generalized speeds, supply
    # kinematic differential equation dictionary, compute Fr from the force
    # list and Fr* from the body list, compute the mass matrix and forcing
    # terms, then solve for the u dots (time derivatives of the generalized
    # speeds).
    KM = KanesMethod(N, q_ind=[q1, q2, q3], u_ind=[u1, u2, u3], kd_eqs=kd)
    with warns_deprecated_sympy():
        KM.kanes_equations(ForceList, BodyList)
    MM = KM.mass_matrix
    forcing = KM.forcing
    rhs = MM.inv() * forcing
    kdd = KM.kindiffdict()
    rhs = rhs.subs(kdd)
    rhs.simplify()
    assert rhs.expand() == Matrix([(6*u2*u3*r - u3**2*r*tan(q2) +
        4*g*sin(q2))/(5*r), -2*u1*u3/3, u1*(-2*u2 + u3*tan(q2))]).expand()
    assert simplify(KM.rhs() -
                    KM.mass_matrix_full.LUsolve(KM.forcing_full)) == zeros(6, 1)

    # This code tests our output vs. benchmark values. When r=g=m=1, the
    # critical speed (where all eigenvalues of the linearized equations are 0)
    # is 1 / sqrt(3) for the upright case.
    A = KM.linearize(A_and_B=True)[0]
    A_upright = A.subs({r: 1, g: 1, m: 1}).subs({q1: 0, q2: 0, q3: 0, u1: 0, u3: 0})
    import sympy
    assert sympy.sympify(A_upright.subs({u2: 1 / sqrt(3)})).eigenvals() == {S(0): 6}


def test_aux():
    # Same as above, except we have 2 auxiliary speeds for the ground contact
    # point, which is known to be zero. In one case, we go through then
    # substitute the aux. speeds in at the end (they are zero, as well as their
    # derivative), in the other case, we use the built-in auxiliary speed part
    # of KanesMethod. The equations from each should be the same.
    q1, q2, q3, u1, u2, u3 = dynamicsymbols('q1 q2 q3 u1 u2 u3')
    q1d, q2d, q3d, u1d, u2d, u3d = dynamicsymbols('q1 q2 q3 u1 u2 u3', 1)
    u4, u5, f1, f2 = dynamicsymbols('u4, u5, f1, f2')
    u4d, u5d = dynamicsymbols('u4, u5', 1)
    r, m, g = symbols('r m g')

    N = ReferenceFrame('N')
    Y = N.orientnew('Y', 'Axis', [q1, N.z])
    L = Y.orientnew('L', 'Axis', [q2, Y.x])
    R = L.orientnew('R', 'Axis', [q3, L.y])
    w_R_N_qd = R.ang_vel_in(N)
    R.set_ang_vel(N, u1 * L.x + u2 * L.y + u3 * L.z)

    C = Point('C')
    C.set_vel(N, u4 * L.x + u5 * (Y.z ^ L.x))
    Dmc = C.locatenew('Dmc', r * L.z)
    Dmc.v2pt_theory(C, N, R)
    Dmc.a2pt_theory(C, N, R)

    I = inertia(L, m / 4 * r**2, m / 2 * r**2, m / 4 * r**2)

    kd = [dot(R.ang_vel_in(N) - w_R_N_qd, uv) for uv in L]

    ForceList = [(Dmc, - m * g * Y.z), (C, f1 * L.x + f2 * (Y.z ^ L.x))]
    BodyD = RigidBody('BodyD', Dmc, R, m, (I, Dmc))
    BodyList = [BodyD]

    KM = KanesMethod(N, q_ind=[q1, q2, q3], u_ind=[u1, u2, u3, u4, u5],
                     kd_eqs=kd)
    with warns_deprecated_sympy():
        (fr, frstar) = KM.kanes_equations(ForceList, BodyList)
    fr = fr.subs({u4d: 0, u5d: 0}).subs({u4: 0, u5: 0})
    frstar = frstar.subs({u4d: 0, u5d: 0}).subs({u4: 0, u5: 0})

    KM2 = KanesMethod(N, q_ind=[q1, q2, q3], u_ind=[u1, u2, u3], kd_eqs=kd,
                      u_auxiliary=[u4, u5])
    with warns_deprecated_sympy():
        (fr2, frstar2) = KM2.kanes_equations(ForceList, BodyList)
    fr2 = fr2.subs({u4d: 0, u5d: 0}).subs({u4: 0, u5: 0})
    frstar2 = frstar2.subs({u4d: 0, u5d: 0}).subs({u4: 0, u5: 0})

    frstar.simplify()
    frstar2.simplify()

    assert (fr - fr2).expand() == Matrix([0, 0, 0, 0, 0])
    assert (frstar - frstar2).expand() == Matrix([0, 0, 0, 0, 0])


def test_parallel_axis():
    # This is for a 2 dof inverted pendulum on a cart.
    # This tests the parallel axis code in KanesMethod. The inertia of the
    # pendulum is defined about the hinge, not about the center of mass.

    # Defining the constants and knowns of the system
    gravity = symbols('g')
    k, ls = symbols('k ls')
    a, mA, mC = symbols('a mA mC')
    F = dynamicsymbols('F')
    Ix, Iy, Iz = symbols('Ix Iy Iz')

    # Declaring the Generalized coordinates and speeds
    q1, q2 = dynamicsymbols('q1 q2')
    q1d, q2d = dynamicsymbols('q1 q2', 1)
    u1, u2 = dynamicsymbols('u1 u2')
    u1d, u2d = dynamicsymbols('u1 u2', 1)

    # Creating reference frames
    N = ReferenceFrame('N')
    A = ReferenceFrame('A')

    A.orient(N, 'Axis', [-q2, N.z])
    A.set_ang_vel(N, -u2 * N.z)

    # Origin of Newtonian reference frame
    O = Point('O')

    # Creating and Locating the positions of the cart, C, and the
    # center of mass of the pendulum, A
    C = O.locatenew('C', q1 * N.x)
    Ao = C.locatenew('Ao', a * A.y)

    # Defining velocities of the points
    O.set_vel(N, 0)
    C.set_vel(N, u1 * N.x)
    Ao.v2pt_theory(C, N, A)
    Cart = Particle('Cart', C, mC)
    Pendulum = RigidBody('Pendulum', Ao, A, mA, (inertia(A, Ix, Iy, Iz), C))

    # kinematical differential equations

    kindiffs = [q1d - u1, q2d - u2]

    bodyList = [Cart, Pendulum]

    forceList = [(Ao, -N.y * gravity * mA),
                 (C, -N.y * gravity * mC),
                 (C, -N.x * k * (q1 - ls)),
                 (C, N.x * F)]

    km = KanesMethod(N, [q1, q2], [u1, u2], kindiffs)
    with warns_deprecated_sympy():
        (fr, frstar) = km.kanes_equations(forceList, bodyList)
    mm = km.mass_matrix_full
    assert mm[3, 3] == Iz

def test_input_format():
    # 1 dof problem from test_one_dof
    q, u = dynamicsymbols('q u')
    qd, ud = dynamicsymbols('q u', 1)
    m, c, k = symbols('m c k')
    N = ReferenceFrame('N')
    P = Point('P')
    P.set_vel(N, u * N.x)

    kd = [qd - u]
    FL = [(P, (-k * q - c * u) * N.x)]
    pa = Particle('pa', P, m)
    BL = [pa]

    KM = KanesMethod(N, [q], [u], kd)
    # test for input format kane.kanes_equations((body1, body2, particle1))
    assert KM.kanes_equations(BL)[0] == Matrix([0])
    # test for input format kane.kanes_equations(bodies=(body1, body 2), loads=(load1,load2))
    assert KM.kanes_equations(bodies=BL, loads=None)[0] == Matrix([0])
    # test for input format kane.kanes_equations(bodies=(body1, body 2), loads=None)
    assert KM.kanes_equations(BL, loads=None)[0] == Matrix([0])
    # test for input format kane.kanes_equations(bodies=(body1, body 2))
    assert KM.kanes_equations(BL)[0] == Matrix([0])
    # test for error raised when a wrong force list (in this case a string) is provided
    from sympy.utilities.pytest import raises
    raises(ValueError, lambda: KM._form_fr('bad input'))

    # 2 dof problem from test_two_dof
    q1, q2, u1, u2 = dynamicsymbols('q1 q2 u1 u2')
    q1d, q2d, u1d, u2d = dynamicsymbols('q1 q2 u1 u2', 1)
    m, c1, c2, k1, k2 = symbols('m c1 c2 k1 k2')
    N = ReferenceFrame('N')
    P1 = Point('P1')
    P2 = Point('P2')
    P1.set_vel(N, u1 * N.x)
    P2.set_vel(N, (u1 + u2) * N.x)
    kd = [q1d - u1, q2d - u2]

    FL = ((P1, (-k1 * q1 - c1 * u1 + k2 * q2 + c2 * u2) * N.x), (P2, (-k2 *
        q2 - c2 * u2) * N.x))
    pa1 = Particle('pa1', P1, m)
    pa2 = Particle('pa2', P2, m)
    BL = (pa1, pa2)

    KM = KanesMethod(N, q_ind=[q1, q2], u_ind=[u1, u2], kd_eqs=kd)
    # test for input format
    # kane.kanes_equations((body1, body2), (load1, load2))
    KM.kanes_equations(BL, FL)
    MM = KM.mass_matrix
    forcing = KM.forcing
    rhs = MM.inv() * forcing
    assert expand(rhs[0]) == expand((-k1 * q1 - c1 * u1 + k2 * q2 + c2 * u2)/m)
    assert expand(rhs[1]) == expand((k1 * q1 + c1 * u1 - 2 * k2 * q2 - 2 *
                                    c2 * u2) / m)
