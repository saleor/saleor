from sympy.core.backend import eye, Matrix, zeros
from sympy.physics.mechanics import dynamicsymbols
from sympy.physics.mechanics.functions import find_dynamicsymbols

__all__ = ['SymbolicSystem']


class SymbolicSystem(object):
    """SymbolicSystem is a class that contains all the information about a
    system in a symbolic format such as the equations of motions and the bodies
    and loads in the system.

    There are three ways that the equations of motion can be described for
    Symbolic System:


        [1] Explicit form where the kinematics and dynamics are combined
            x' = F_1(x, t, r, p)

        [2] Implicit form where the kinematics and dynamics are combined
            M_2(x, p) x' = F_2(x, t, r, p)

        [3] Implicit form where the kinematics and dynamics are separate
            M_3(q, p) u' = F_3(q, u, t, r, p)
            q' = G(q, u, t, r, p)

    where

    x : states, e.g. [q, u]
    t : time
    r : specified (exogenous) inputs
    p : constants
    q : generalized coordinates
    u : generalized speeds
    F_1 : right hand side of the combined equations in explicit form
    F_2 : right hand side of the combined equations in implicit form
    F_3 : right hand side of the dynamical equations in implicit form
    M_2 : mass matrix of the combined equations in implicit form
    M_3 : mass matrix of the dynamical equations in implicit form
    G : right hand side of the kinematical differential equations

        Parameters
        ==========

        coord_states : ordered iterable of functions of time
            This input will either be a collection of the coordinates or states
            of the system depending on whether or not the speeds are also
            given. If speeds are specified this input will be assumed to
            be the coordinates otherwise this input will be assumed to
            be the states.

        right_hand_side : Matrix
            This variable is the right hand side of the equations of motion in
            any of the forms. The specific form will be assumed depending on
            whether a mass matrix or coordinate derivatives are given.

        speeds : ordered iterable of functions of time, optional
            This is a collection of the generalized speeds of the system. If
            given it will be assumed that the first argument (coord_states)
            will represent the generalized coordinates of the system.

        mass_matrix : Matrix, optional
            The matrix of the implicit forms of the equations of motion (forms
            [2] and [3]). The distinction between the forms is determined by
            whether or not the coordinate derivatives are passed in. If
            they are given form [3] will be assumed otherwise form [2] is
            assumed.

        coordinate_derivatives : Matrix, optional
            The right hand side of the kinematical equations in explicit form.
            If given it will be assumed that the equations of motion are being
            entered in form [3].

        alg_con : Iterable, optional
            The indexes of the rows in the equations of motion that contain
            algebraic constraints instead of differential equations. If the
            equations are input in form [3], it will be assumed the indexes are
            referencing the mass_matrix/right_hand_side combination and not the
            coordinate_derivatives.

        output_eqns : Dictionary, optional
            Any output equations that are desired to be tracked are stored in a
            dictionary where the key corresponds to the name given for the
            specific equation and the value is the equation itself in symbolic
            form

        coord_idxs : Iterable, optional
            If coord_states corresponds to the states rather than the
            coordinates this variable will tell SymbolicSystem which indexes of
            the states correspond to generalized coordinates.

        speed_idxs : Iterable, optional
            If coord_states corresponds to the states rather than the
            coordinates this variable will tell SymbolicSystem which indexes of
            the states correspond to generalized speeds.

        bodies : iterable of Body/Rigidbody objects, optional
            Iterable containing the bodies of the system

        loads : iterable of load instances (described below), optional
            Iterable containing the loads of the system where forces are given
            by (point of application, force vector) and torques are given by
            (reference frame acting upon, torque vector). Ex [(point, force),
            (ref_frame, torque)]

    Attributes
    ==========

    coordinates : Matrix, shape(n, 1)
        This is a matrix containing the generalized coordinates of the system

    speeds : Matrix, shape(m, 1)
        This is a matrix containing the generalized speeds of the system

    states : Matrix, shape(o, 1)
        This is a matrix containing the state variables of the system

    alg_con : List
        This list contains the indices of the algebraic constraints in the
        combined equations of motion. The presence of these constraints
        requires that a DAE solver be used instead of an ODE solver.
        If the system is given in form [3] the alg_con variable will be
        adjusted such that it is a representation of the combined kinematics
        and dynamics thus make sure it always matches the mass matrix
        entered.

    dyn_implicit_mat : Matrix, shape(m, m)
        This is the M matrix in form [3] of the equations of motion (the mass
        matrix or generalized inertia matrix of the dynamical equations of
        motion in implicit form).

    dyn_implicit_rhs : Matrix, shape(m, 1)
        This is the F vector in form [3] of the equations of motion (the right
        hand side of the dynamical equations of motion in implicit form).

    comb_implicit_mat : Matrix, shape(o, o)
        This is the M matrix in form [2] of the equations of motion.
        This matrix contains a block diagonal structure where the top
        left block (the first rows) represent the matrix in the
        implicit form of the kinematical equations and the bottom right
        block (the last rows) represent the matrix in the implicit form
        of the dynamical equations.

    comb_implicit_rhs : Matrix, shape(o, 1)
        This is the F vector in form [2] of the equations of motion. The top
        part of the vector represents the right hand side of the implicit form
        of the kinemaical equations and the bottom of the vector represents the
        right hand side of the implicit form of the dynamical equations of
        motion.

    comb_explicit_rhs : Matrix, shape(o, 1)
        This vector represents the right hand side of the combined equations of
        motion in explicit form (form [1] from above).

    kin_explicit_rhs : Matrix, shape(m, 1)
        This is the right hand side of the explicit form of the kinematical
        equations of motion as can be seen in form [3] (the G matrix).

    output_eqns : Dictionary
        If output equations were given they are stored in a dictionary where
        the key corresponds to the name given for the specific equation and
        the value is the equation itself in symbolic form

    bodies : Tuple
        If the bodies in the system were given they are stored in a tuple for
        future access

    loads : Tuple
        If the loads in the system were given they are stored in a tuple for
        future access. This includes forces and torques where forces are given
        by (point of application, force vector) and torques are given by
        (reference frame acted upon, torque vector).

    Example
    =======

    As a simple example, the dynamics of a simple pendulum will be input into a
    SymbolicSystem object manually. First some imports will be needed and then
    symbols will be set up for the length of the pendulum (l), mass at the end
    of the pendulum (m), and a constant for gravity (g). ::

        >>> from sympy import Matrix, sin, symbols
        >>> from sympy.physics.mechanics import dynamicsymbols, SymbolicSystem
        >>> l, m, g = symbols('l m g')

    The system will be defined by an angle of theta from the vertical and a
    generalized speed of omega will be used where omega = theta_dot. ::

        >>> theta, omega = dynamicsymbols('theta omega')

    Now the equations of motion are ready to be formed and passed to the
    SymbolicSystem object. ::

        >>> kin_explicit_rhs = Matrix([omega])
        >>> dyn_implicit_mat = Matrix([l**2 * m])
        >>> dyn_implicit_rhs = Matrix([-g * l * m * sin(theta)])
        >>> symsystem = SymbolicSystem([theta], dyn_implicit_rhs, [omega],
        ...                            dyn_implicit_mat)

    Notes
    =====

    m : number of generalized speeds
    n : number of generalized coordinates
    o : number of states

    """

    def __init__(self, coord_states, right_hand_side, speeds=None,
                 mass_matrix=None, coordinate_derivatives=None, alg_con=None,
                 output_eqns={}, coord_idxs=None, speed_idxs=None, bodies=None,
                 loads=None):
        """Initializes a SymbolicSystem object"""

        # Extract information on speeds, coordinates and states
        if speeds is None:
            self._states = Matrix(coord_states)

            if coord_idxs is None:
                self._coordinates = None
            else:
                coords = [coord_states[i] for i in coord_idxs]
                self._coordinates = Matrix(coords)

            if speed_idxs is None:
                self._speeds = None
            else:
                speeds_inter = [coord_states[i] for i in speed_idxs]
                self._speeds = Matrix(speeds_inter)
        else:
            self._coordinates = Matrix(coord_states)
            self._speeds = Matrix(speeds)
            self._states = self._coordinates.col_join(self._speeds)

        # Extract equations of motion form
        if coordinate_derivatives is not None:
            self._kin_explicit_rhs = coordinate_derivatives
            self._dyn_implicit_rhs = right_hand_side
            self._dyn_implicit_mat = mass_matrix
            self._comb_implicit_rhs = None
            self._comb_implicit_mat = None
            self._comb_explicit_rhs = None
        elif mass_matrix is not None:
            self._kin_explicit_rhs = None
            self._dyn_implicit_rhs = None
            self._dyn_implicit_mat = None
            self._comb_implicit_rhs = right_hand_side
            self._comb_implicit_mat = mass_matrix
            self._comb_explicit_rhs = None
        else:
            self._kin_explicit_rhs = None
            self._dyn_implicit_rhs = None
            self._dyn_implicit_mat = None
            self._comb_implicit_rhs = None
            self._comb_implicit_mat = None
            self._comb_explicit_rhs = right_hand_side

        # Set the remainder of the inputs as instance attributes
        if alg_con is not None and coordinate_derivatives is not None:
            alg_con = [i + len(coordinate_derivatives) for i in alg_con]
        self._alg_con = alg_con
        self.output_eqns = output_eqns

        # Change the body and loads iterables to tuples if they are not tuples
        # already
        if type(bodies) != tuple and bodies is not None:
            bodies = tuple(bodies)
        if type(loads) != tuple and loads is not None:
            loads = tuple(loads)
        self._bodies = bodies
        self._loads = loads

    @property
    def coordinates(self):
        """Returns the column matrix of the generalized coordinates"""
        if self._coordinates is None:
            raise AttributeError("The coordinates were not specified.")
        else:
            return self._coordinates

    @property
    def speeds(self):
        """Returns the column matrix of generalized speeds"""
        if self._speeds is None:
            raise AttributeError("The speeds were not specified.")
        else:
            return self._speeds

    @property
    def states(self):
        """Returns the column matrix of the state variables"""
        return self._states

    @property
    def alg_con(self):
        """Returns a list with the indices of the rows containing algebraic
        constraints in the combined form of the equations of motion"""
        return self._alg_con

    @property
    def dyn_implicit_mat(self):
        """Returns the matrix, M, corresponding to the dynamic equations in
        implicit form, M x' = F, where the kinematical equations are not
        included"""
        if self._dyn_implicit_mat is None:
            raise AttributeError("dyn_implicit_mat is not specified for "
                                 "equations of motion form [1] or [2].")
        else:
            return self._dyn_implicit_mat

    @property
    def dyn_implicit_rhs(self):
        """Returns the column matrix, F, corresponding to the dynamic equations
        in implicit form, M x' = F, where the kinematical equations are not
        included"""
        if self._dyn_implicit_rhs is None:
            raise AttributeError("dyn_implicit_rhs is not specified for "
                                 "equations of motion form [1] or [2].")
        else:
            return self._dyn_implicit_rhs

    @property
    def comb_implicit_mat(self):
        """Returns the matrix, M, corresponding to the equations of motion in
        implicit form (form [2]), M x' = F, where the kinematical equations are
        included"""
        if self._comb_implicit_mat is None:
            if self._dyn_implicit_mat is not None:
                num_kin_eqns = len(self._kin_explicit_rhs)
                num_dyn_eqns = len(self._dyn_implicit_rhs)
                zeros1 = zeros(num_kin_eqns, num_dyn_eqns)
                zeros2 = zeros(num_dyn_eqns, num_kin_eqns)
                inter1 = eye(num_kin_eqns).row_join(zeros1)
                inter2 = zeros2.row_join(self._dyn_implicit_mat)
                self._comb_implicit_mat = inter1.col_join(inter2)
                return self._comb_implicit_mat
            else:
                raise AttributeError("comb_implicit_mat is not specified for "
                                     "equations of motion form [1].")
        else:
            return self._comb_implicit_mat

    @property
    def comb_implicit_rhs(self):
        """Returns the column matrix, F, corresponding to the equations of
        motion in implicit form (form [2]), M x' = F, where the kinematical
        equations are included"""
        if self._comb_implicit_rhs is None:
            if self._dyn_implicit_rhs is not None:
                kin_inter = self._kin_explicit_rhs
                dyn_inter = self._dyn_implicit_rhs
                self._comb_implicit_rhs = kin_inter.col_join(dyn_inter)
                return self._comb_implicit_rhs
            else:
                raise AttributeError("comb_implicit_mat is not specified for "
                                     "equations of motion in form [1].")
        else:
            return self._comb_implicit_rhs

    def compute_explicit_form(self):
        """If the explicit right hand side of the combined equations of motion
        is to provided upon initialization, this method will calculate it. This
        calculation can potentially take awhile to compute."""
        if self._comb_explicit_rhs is not None:
            raise AttributeError("comb_explicit_rhs is already formed.")

        inter1 = getattr(self, 'kin_explicit_rhs', None)
        if inter1 is not None:
            inter2 = self._dyn_implicit_mat.LUsolve(self._dyn_implicit_rhs)
            out = inter1.col_join(inter2)
        else:
            out = self._comb_implicit_mat.LUsolve(self._comb_implicit_rhs)

        self._comb_explicit_rhs = out

    @property
    def comb_explicit_rhs(self):
        """Returns the right hand side of the equations of motion in explicit
        form, x' = F, where the kinematical equations are included"""
        if self._comb_explicit_rhs is None:
            raise AttributeError("Please run .combute_explicit_form before "
                                 "attempting to access comb_explicit_rhs.")
        else:
            return self._comb_explicit_rhs

    @property
    def kin_explicit_rhs(self):
        """Returns the right hand side of the kinematical equations in explicit
        form, q' = G"""
        if self._kin_explicit_rhs is None:
            raise AttributeError("kin_explicit_rhs is not specified for "
                                 "equations of motion form [1] or [2].")
        else:
            return self._kin_explicit_rhs

    def dynamic_symbols(self):
        """Returns a column matrix containing all of the symbols in the system
        that depend on time"""
        # Create a list of all of the expressions in the equations of motion
        if self._comb_explicit_rhs is None:
            eom_expressions = (self.comb_implicit_mat[:] +
                               self.comb_implicit_rhs[:])
        else:
            eom_expressions = (self._comb_explicit_rhs[:])

        functions_of_time = set()
        for expr in eom_expressions:
            functions_of_time = functions_of_time.union(
                find_dynamicsymbols(expr))
        functions_of_time = functions_of_time.union(self._states)

        return tuple(functions_of_time)

    def constant_symbols(self):
        """Returns a column matrix containing all of the symbols in the system
        that do not depend on time"""
        # Create a list of all of the expressions in the equations of motion
        if self._comb_explicit_rhs is None:
            eom_expressions = (self.comb_implicit_mat[:] +
                               self.comb_implicit_rhs[:])
        else:
            eom_expressions = (self._comb_explicit_rhs[:])

        constants = set()
        for expr in eom_expressions:
            constants = constants.union(expr.free_symbols)
        constants.remove(dynamicsymbols._t)

        return tuple(constants)

    @property
    def bodies(self):
        """Returns the bodies in the system"""
        if self._bodies is None:
            raise AttributeError("bodies were not specified for the system.")
        else:
            return self._bodies

    @property
    def loads(self):
        """Returns the loads in the system"""
        if self._loads is None:
            raise AttributeError("loads were not specified for the system.")
        else:
            return self._loads
