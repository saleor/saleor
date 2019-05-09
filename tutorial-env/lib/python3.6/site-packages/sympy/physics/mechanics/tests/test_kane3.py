from sympy.core.compatibility import range
from sympy import evalf, symbols, pi, sin, cos, sqrt, acos, Matrix
from sympy.physics.mechanics import (ReferenceFrame, dynamicsymbols, inertia,
                                     KanesMethod, RigidBody, Point, dot, msubs)
from sympy.utilities.pytest import slow, ON_TRAVIS, skip, warns_deprecated_sympy


@slow
def test_bicycle():
    if ON_TRAVIS:
        skip("Too slow for travis.")
    # Code to get equations of motion for a bicycle modeled as in:
    # J.P Meijaard, Jim M Papadopoulos, Andy Ruina and A.L Schwab. Linearized
    # dynamics equations for the balance and steer of a bicycle: a benchmark
    # and review. Proceedings of The Royal Society (2007) 463, 1955-1982
    # doi: 10.1098/rspa.2007.1857

    # Note that this code has been crudely ported from Autolev, which is the
    # reason for some of the unusual naming conventions. It was purposefully as
    # similar as possible in order to aide debugging.

    # Declare Coordinates & Speeds
    # Simple definitions for qdots - qd = u
    # Speeds are: yaw frame ang. rate, roll frame ang. rate, rear wheel frame
    # ang.  rate (spinning motion), frame ang. rate (pitching motion), steering
    # frame ang. rate, and front wheel ang. rate (spinning motion).
    # Wheel positions are ignorable coordinates, so they are not introduced.
    q1, q2, q4, q5 = dynamicsymbols('q1 q2 q4 q5')
    q1d, q2d, q4d, q5d = dynamicsymbols('q1 q2 q4 q5', 1)
    u1, u2, u3, u4, u5, u6 = dynamicsymbols('u1 u2 u3 u4 u5 u6')
    u1d, u2d, u3d, u4d, u5d, u6d = dynamicsymbols('u1 u2 u3 u4 u5 u6', 1)

    # Declare System's Parameters
    WFrad, WRrad, htangle, forkoffset = symbols('WFrad WRrad htangle forkoffset')
    forklength, framelength, forkcg1 = symbols('forklength framelength forkcg1')
    forkcg3, framecg1, framecg3, Iwr11 = symbols('forkcg3 framecg1 framecg3 Iwr11')
    Iwr22, Iwf11, Iwf22, Iframe11 = symbols('Iwr22 Iwf11 Iwf22 Iframe11')
    Iframe22, Iframe33, Iframe31, Ifork11 = symbols('Iframe22 Iframe33 Iframe31 Ifork11')
    Ifork22, Ifork33, Ifork31, g = symbols('Ifork22 Ifork33 Ifork31 g')
    mframe, mfork, mwf, mwr = symbols('mframe mfork mwf mwr')

    # Set up reference frames for the system
    # N - inertial
    # Y - yaw
    # R - roll
    # WR - rear wheel, rotation angle is ignorable coordinate so not oriented
    # Frame - bicycle frame
    # TempFrame - statically rotated frame for easier reference inertia definition
    # Fork - bicycle fork
    # TempFork - statically rotated frame for easier reference inertia definition
    # WF - front wheel, again posses a ignorable coordinate
    N = ReferenceFrame('N')
    Y = N.orientnew('Y', 'Axis', [q1, N.z])
    R = Y.orientnew('R', 'Axis', [q2, Y.x])
    Frame = R.orientnew('Frame', 'Axis', [q4 + htangle, R.y])
    WR = ReferenceFrame('WR')
    TempFrame = Frame.orientnew('TempFrame', 'Axis', [-htangle, Frame.y])
    Fork = Frame.orientnew('Fork', 'Axis', [q5, Frame.x])
    TempFork = Fork.orientnew('TempFork', 'Axis', [-htangle, Fork.y])
    WF = ReferenceFrame('WF')

    # Kinematics of the Bicycle First block of code is forming the positions of
    # the relevant points
    # rear wheel contact -> rear wheel mass center -> frame mass center +
    # frame/fork connection -> fork mass center + front wheel mass center ->
    # front wheel contact point
    WR_cont = Point('WR_cont')
    WR_mc = WR_cont.locatenew('WR_mc', WRrad * R.z)
    Steer = WR_mc.locatenew('Steer', framelength * Frame.z)
    Frame_mc = WR_mc.locatenew('Frame_mc', - framecg1 * Frame.x
                                           + framecg3 * Frame.z)
    Fork_mc = Steer.locatenew('Fork_mc', - forkcg1 * Fork.x
                                         + forkcg3 * Fork.z)
    WF_mc = Steer.locatenew('WF_mc', forklength * Fork.x + forkoffset * Fork.z)
    WF_cont = WF_mc.locatenew('WF_cont', WFrad * (dot(Fork.y, Y.z) * Fork.y -
                                                  Y.z).normalize())

    # Set the angular velocity of each frame.
    # Angular accelerations end up being calculated automatically by
    # differentiating the angular velocities when first needed.
    # u1 is yaw rate
    # u2 is roll rate
    # u3 is rear wheel rate
    # u4 is frame pitch rate
    # u5 is fork steer rate
    # u6 is front wheel rate
    Y.set_ang_vel(N, u1 * Y.z)
    R.set_ang_vel(Y, u2 * R.x)
    WR.set_ang_vel(Frame, u3 * Frame.y)
    Frame.set_ang_vel(R, u4 * Frame.y)
    Fork.set_ang_vel(Frame, u5 * Fork.x)
    WF.set_ang_vel(Fork, u6 * Fork.y)

    # Form the velocities of the previously defined points, using the 2 - point
    # theorem (written out by hand here).  Accelerations again are calculated
    # automatically when first needed.
    WR_cont.set_vel(N, 0)
    WR_mc.v2pt_theory(WR_cont, N, WR)
    Steer.v2pt_theory(WR_mc, N, Frame)
    Frame_mc.v2pt_theory(WR_mc, N, Frame)
    Fork_mc.v2pt_theory(Steer, N, Fork)
    WF_mc.v2pt_theory(Steer, N, Fork)
    WF_cont.v2pt_theory(WF_mc, N, WF)

    # Sets the inertias of each body. Uses the inertia frame to construct the
    # inertia dyadics. Wheel inertias are only defined by principle moments of
    # inertia, and are in fact constant in the frame and fork reference frames;
    # it is for this reason that the orientations of the wheels does not need
    # to be defined. The frame and fork inertias are defined in the 'Temp'
    # frames which are fixed to the appropriate body frames; this is to allow
    # easier input of the reference values of the benchmark paper. Note that
    # due to slightly different orientations, the products of inertia need to
    # have their signs flipped; this is done later when entering the numerical
    # value.

    Frame_I = (inertia(TempFrame, Iframe11, Iframe22, Iframe33, 0, 0, Iframe31), Frame_mc)
    Fork_I = (inertia(TempFork, Ifork11, Ifork22, Ifork33, 0, 0, Ifork31), Fork_mc)
    WR_I = (inertia(Frame, Iwr11, Iwr22, Iwr11), WR_mc)
    WF_I = (inertia(Fork, Iwf11, Iwf22, Iwf11), WF_mc)

    # Declaration of the RigidBody containers. ::

    BodyFrame = RigidBody('BodyFrame', Frame_mc, Frame, mframe, Frame_I)
    BodyFork = RigidBody('BodyFork', Fork_mc, Fork, mfork, Fork_I)
    BodyWR = RigidBody('BodyWR', WR_mc, WR, mwr, WR_I)
    BodyWF = RigidBody('BodyWF', WF_mc, WF, mwf, WF_I)

    # The kinematic differential equations; they are defined quite simply. Each
    # entry in this list is equal to zero.
    kd = [q1d - u1, q2d - u2, q4d - u4, q5d - u5]

    # The nonholonomic constraints are the velocity of the front wheel contact
    # point dotted into the X, Y, and Z directions; the yaw frame is used as it
    # is "closer" to the front wheel (1 less DCM connecting them). These
    # constraints force the velocity of the front wheel contact point to be 0
    # in the inertial frame; the X and Y direction constraints enforce a
    # "no-slip" condition, and the Z direction constraint forces the front
    # wheel contact point to not move away from the ground frame, essentially
    # replicating the holonomic constraint which does not allow the frame pitch
    # to change in an invalid fashion.

    conlist_speed = [WF_cont.vel(N) & Y.x, WF_cont.vel(N) & Y.y, WF_cont.vel(N) & Y.z]

    # The holonomic constraint is that the position from the rear wheel contact
    # point to the front wheel contact point when dotted into the
    # normal-to-ground plane direction must be zero; effectively that the front
    # and rear wheel contact points are always touching the ground plane. This
    # is actually not part of the dynamic equations, but instead is necessary
    # for the lineraization process.

    conlist_coord = [WF_cont.pos_from(WR_cont) & Y.z]

    # The force list; each body has the appropriate gravitational force applied
    # at its mass center.
    FL = [(Frame_mc, -mframe * g * Y.z),
        (Fork_mc, -mfork * g * Y.z),
        (WF_mc, -mwf * g * Y.z),
        (WR_mc, -mwr * g * Y.z)]
    BL = [BodyFrame, BodyFork, BodyWR, BodyWF]


    # The N frame is the inertial frame, coordinates are supplied in the order
    # of independent, dependent coordinates, as are the speeds. The kinematic
    # differential equation are also entered here.  Here the dependent speeds
    # are specified, in the same order they were provided in earlier, along
    # with the non-holonomic constraints.  The dependent coordinate is also
    # provided, with the holonomic constraint.  Again, this is only provided
    # for the linearization process.

    KM = KanesMethod(N, q_ind=[q1, q2, q5],
            q_dependent=[q4], configuration_constraints=conlist_coord,
            u_ind=[u2, u3, u5],
            u_dependent=[u1, u4, u6], velocity_constraints=conlist_speed,
            kd_eqs=kd)
    with warns_deprecated_sympy():
        (fr, frstar) = KM.kanes_equations(FL, BL)

    # This is the start of entering in the numerical values from the benchmark
    # paper to validate the eigen values of the linearized equations from this
    # model to the reference eigen values. Look at the aforementioned paper for
    # more information. Some of these are intermediate values, used to
    # transform values from the paper into the coordinate systems used in this
    # model.
    PaperRadRear                    =  0.3
    PaperRadFront                   =  0.35
    HTA                             =  evalf.N(pi / 2 - pi / 10)
    TrailPaper                      =  0.08
    rake                            =  evalf.N(-(TrailPaper*sin(HTA)-(PaperRadFront*cos(HTA))))
    PaperWb                         =  1.02
    PaperFrameCgX                   =  0.3
    PaperFrameCgZ                   =  0.9
    PaperForkCgX                    =  0.9
    PaperForkCgZ                    =  0.7
    FrameLength                     =  evalf.N(PaperWb*sin(HTA)-(rake-(PaperRadFront-PaperRadRear)*cos(HTA)))
    FrameCGNorm                     =  evalf.N((PaperFrameCgZ - PaperRadRear-(PaperFrameCgX/sin(HTA))*cos(HTA))*sin(HTA))
    FrameCGPar                      =  evalf.N((PaperFrameCgX / sin(HTA) + (PaperFrameCgZ - PaperRadRear - PaperFrameCgX / sin(HTA) * cos(HTA)) * cos(HTA)))
    tempa                           =  evalf.N((PaperForkCgZ - PaperRadFront))
    tempb                           =  evalf.N((PaperWb-PaperForkCgX))
    tempc                           =  evalf.N(sqrt(tempa**2+tempb**2))
    PaperForkL                      =  evalf.N((PaperWb*cos(HTA)-(PaperRadFront-PaperRadRear)*sin(HTA)))
    ForkCGNorm                      =  evalf.N(rake+(tempc * sin(pi/2-HTA-acos(tempa/tempc))))
    ForkCGPar                       =  evalf.N(tempc * cos((pi/2-HTA)-acos(tempa/tempc))-PaperForkL)

    # Here is the final assembly of the numerical values. The symbol 'v' is the
    # forward speed of the bicycle (a concept which only makes sense in the
    # upright, static equilibrium case?). These are in a dictionary which will
    # later be substituted in. Again the sign on the *product* of inertia
    # values is flipped here, due to different orientations of coordinate
    # systems.
    v = symbols('v')
    val_dict = {WFrad: PaperRadFront,
                WRrad: PaperRadRear,
                htangle: HTA,
                forkoffset: rake,
                forklength: PaperForkL,
                framelength: FrameLength,
                forkcg1: ForkCGPar,
                forkcg3: ForkCGNorm,
                framecg1: FrameCGNorm,
                framecg3: FrameCGPar,
                Iwr11: 0.0603,
                Iwr22: 0.12,
                Iwf11: 0.1405,
                Iwf22: 0.28,
                Ifork11: 0.05892,
                Ifork22: 0.06,
                Ifork33: 0.00708,
                Ifork31: 0.00756,
                Iframe11: 9.2,
                Iframe22: 11,
                Iframe33: 2.8,
                Iframe31: -2.4,
                mfork: 4,
                mframe: 85,
                mwf: 3,
                mwr: 2,
                g: 9.81,
                q1: 0,
                q2: 0,
                q4: 0,
                q5: 0,
                u1: 0,
                u2: 0,
                u3: v / PaperRadRear,
                u4: 0,
                u5: 0,
                u6: v / PaperRadFront}

    # Linearizes the forcing vector; the equations are set up as MM udot =
    # forcing, where MM is the mass matrix, udot is the vector representing the
    # time derivatives of the generalized speeds, and forcing is a vector which
    # contains both external forcing terms and internal forcing terms, such as
    # centripital or coriolis forces.  This actually returns a matrix with as
    # many rows as *total* coordinates and speeds, but only as many columns as
    # independent coordinates and speeds.

    forcing_lin = KM.linearize()[0]

    # As mentioned above, the size of the linearized forcing terms is expanded
    # to include both q's and u's, so the mass matrix must have this done as
    # well.  This will likely be changed to be part of the linearized process,
    # for future reference.
    MM_full = KM.mass_matrix_full

    MM_full_s = msubs(MM_full, val_dict)
    forcing_lin_s = msubs(forcing_lin, KM.kindiffdict(), val_dict)

    MM_full_s = MM_full_s.evalf()
    forcing_lin_s = forcing_lin_s.evalf()

    # Finally, we construct an "A" matrix for the form xdot = A x (x being the
    # state vector, although in this case, the sizes are a little off). The
    # following line extracts only the minimum entries required for eigenvalue
    # analysis, which correspond to rows and columns for lean, steer, lean
    # rate, and steer rate.
    Amat = MM_full_s.inv() * forcing_lin_s
    A = Amat.extract([1, 2, 4, 6], [1, 2, 3, 5])

    # Precomputed for comparison
    Res = Matrix([[               0,                                           0,                  1.0,                    0],
                  [               0,                                           0,                    0,                  1.0],
                  [9.48977444677355, -0.891197738059089*v**2 - 0.571523173729245, -0.105522449805691*v, -0.330515398992311*v],
                  [11.7194768719633,   -1.97171508499972*v**2 + 30.9087533932407,   3.67680523332152*v,  -3.08486552743311*v]])


    # Actual eigenvalue comparison
    eps = 1.e-12
    for i in range(6):
        error = Res.subs(v, i) - A.subs(v, i)
        assert all(abs(x) < eps for x in error)
