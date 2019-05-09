from sympy.core.backend import (diff, expand, sin, cos, sympify,
                   eye, symbols, ImmutableMatrix as Matrix, MatrixBase)
from sympy import (trigsimp, solve, Symbol, Dummy)
from sympy.core.compatibility import string_types, range
from sympy.physics.vector.vector import Vector, _check_vector
from sympy.utilities.misc import translate

__all__ = ['CoordinateSym', 'ReferenceFrame']


class CoordinateSym(Symbol):
    """
    A coordinate symbol/base scalar associated wrt a Reference Frame.

    Ideally, users should not instantiate this class. Instances of
    this class must only be accessed through the corresponding frame
    as 'frame[index]'.

    CoordinateSyms having the same frame and index parameters are equal
    (even though they may be instantiated separately).

    Parameters
    ==========

    name : string
        The display name of the CoordinateSym

    frame : ReferenceFrame
        The reference frame this base scalar belongs to

    index : 0, 1 or 2
        The index of the dimension denoted by this coordinate variable

    Examples
    ========

    >>> from sympy.physics.vector import ReferenceFrame, CoordinateSym
    >>> A = ReferenceFrame('A')
    >>> A[1]
    A_y
    >>> type(A[0])
    <class 'sympy.physics.vector.frame.CoordinateSym'>
    >>> a_y = CoordinateSym('a_y', A, 1)
    >>> a_y == A[1]
    True

    """

    def __new__(cls, name, frame, index):
        # We can't use the cached Symbol.__new__ because this class depends on
        # frame and index, which are not passed to Symbol.__xnew__.
        assumptions = {}
        super(CoordinateSym, cls)._sanitize(assumptions, cls)
        obj = super(CoordinateSym, cls).__xnew__(cls, name, **assumptions)
        _check_frame(frame)
        if index not in range(0, 3):
            raise ValueError("Invalid index specified")
        obj._id = (frame, index)
        return obj

    @property
    def frame(self):
        return self._id[0]

    def __eq__(self, other):
        #Check if the other object is a CoordinateSym of the same frame
        #and same index
        if isinstance(other, CoordinateSym):
            if other._id == self._id:
                return True
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return tuple((self._id[0].__hash__(), self._id[1])).__hash__()


class ReferenceFrame(object):
    """A reference frame in classical mechanics.

    ReferenceFrame is a class used to represent a reference frame in classical
    mechanics. It has a standard basis of three unit vectors in the frame's
    x, y, and z directions.

    It also can have a rotation relative to a parent frame; this rotation is
    defined by a direction cosine matrix relating this frame's basis vectors to
    the parent frame's basis vectors.  It can also have an angular velocity
    vector, defined in another frame.

    """
    _count = 0

    def __init__(self, name, indices=None, latexs=None, variables=None):
        """ReferenceFrame initialization method.

        A ReferenceFrame has a set of orthonormal basis vectors, along with
        orientations relative to other ReferenceFrames and angular velocities
        relative to other ReferenceFrames.

        Parameters
        ==========

        indices : list (of strings)
            If custom indices are desired for console, pretty, and LaTeX
            printing, supply three as a list. The basis vectors can then be
            accessed with the get_item method.
        latexs : list (of strings)
            If custom names are desired for LaTeX printing of each basis
            vector, supply the names here in a list.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, vlatex
        >>> N = ReferenceFrame('N')
        >>> N.x
        N.x
        >>> O = ReferenceFrame('O', indices=('1', '2', '3'))
        >>> O.x
        O['1']
        >>> O['1']
        O['1']
        >>> P = ReferenceFrame('P', latexs=('A1', 'A2', 'A3'))
        >>> vlatex(P.x)
        'A1'

        """

        if not isinstance(name, string_types):
            raise TypeError('Need to supply a valid name')
        # The if statements below are for custom printing of basis-vectors for
        # each frame.
        # First case, when custom indices are supplied
        if indices is not None:
            if not isinstance(indices, (tuple, list)):
                raise TypeError('Supply the indices as a list')
            if len(indices) != 3:
                raise ValueError('Supply 3 indices')
            for i in indices:
                if not isinstance(i, string_types):
                    raise TypeError('Indices must be strings')
            self.str_vecs = [(name + '[\'' + indices[0] + '\']'),
                             (name + '[\'' + indices[1] + '\']'),
                             (name + '[\'' + indices[2] + '\']')]
            self.pretty_vecs = [(name.lower() + u"_" + indices[0]),
                                (name.lower() + u"_" + indices[1]),
                                (name.lower() + u"_" + indices[2])]
            self.latex_vecs = [(r"\mathbf{\hat{%s}_{%s}}" % (name.lower(),
                               indices[0])), (r"\mathbf{\hat{%s}_{%s}}" %
                               (name.lower(), indices[1])),
                               (r"\mathbf{\hat{%s}_{%s}}" % (name.lower(),
                               indices[2]))]
            self.indices = indices
        # Second case, when no custom indices are supplied
        else:
            self.str_vecs = [(name + '.x'), (name + '.y'), (name + '.z')]
            self.pretty_vecs = [name.lower() + u"_x",
                                name.lower() + u"_y",
                                name.lower() + u"_z"]
            self.latex_vecs = [(r"\mathbf{\hat{%s}_x}" % name.lower()),
                               (r"\mathbf{\hat{%s}_y}" % name.lower()),
                               (r"\mathbf{\hat{%s}_z}" % name.lower())]
            self.indices = ['x', 'y', 'z']
        # Different step, for custom latex basis vectors
        if latexs is not None:
            if not isinstance(latexs, (tuple, list)):
                raise TypeError('Supply the indices as a list')
            if len(latexs) != 3:
                raise ValueError('Supply 3 indices')
            for i in latexs:
                if not isinstance(i, string_types):
                    raise TypeError('Latex entries must be strings')
            self.latex_vecs = latexs
        self.name = name
        self._var_dict = {}
        #The _dcm_dict dictionary will only store the dcms of parent-child
        #relationships. The _dcm_cache dictionary will work as the dcm
        #cache.
        self._dcm_dict = {}
        self._dcm_cache = {}
        self._ang_vel_dict = {}
        self._ang_acc_dict = {}
        self._dlist = [self._dcm_dict, self._ang_vel_dict, self._ang_acc_dict]
        self._cur = 0
        self._x = Vector([(Matrix([1, 0, 0]), self)])
        self._y = Vector([(Matrix([0, 1, 0]), self)])
        self._z = Vector([(Matrix([0, 0, 1]), self)])
        #Associate coordinate symbols wrt this frame
        if variables is not None:
            if not isinstance(variables, (tuple, list)):
                raise TypeError('Supply the variable names as a list/tuple')
            if len(variables) != 3:
                raise ValueError('Supply 3 variable names')
            for i in variables:
                if not isinstance(i, string_types):
                    raise TypeError('Variable names must be strings')
        else:
            variables = [name + '_x', name + '_y', name + '_z']
        self.varlist = (CoordinateSym(variables[0], self, 0), \
                        CoordinateSym(variables[1], self, 1), \
                        CoordinateSym(variables[2], self, 2))
        ReferenceFrame._count += 1
        self.index = ReferenceFrame._count

    def __getitem__(self, ind):
        """
        Returns basis vector for the provided index, if the index is a string.

        If the index is a number, returns the coordinate variable correspon-
        -ding to that index.
        """
        if not isinstance(ind, string_types):
            if ind < 3:
                return self.varlist[ind]
            else:
                raise ValueError("Invalid index provided")
        if self.indices[0] == ind:
            return self.x
        if self.indices[1] == ind:
            return self.y
        if self.indices[2] == ind:
            return self.z
        else:
            raise ValueError('Not a defined index')

    def __iter__(self):
        return iter([self.x, self.y, self.z])

    def __str__(self):
        """Returns the name of the frame. """
        return self.name

    __repr__ = __str__

    def _dict_list(self, other, num):
        """Creates a list from self to other using _dcm_dict. """
        outlist = [[self]]
        oldlist = [[]]
        while outlist != oldlist:
            oldlist = outlist[:]
            for i, v in enumerate(outlist):
                templist = v[-1]._dlist[num].keys()
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
        raise ValueError('No Connecting Path found between ' + self.name +
                         ' and ' + other.name)

    def _w_diff_dcm(self, otherframe):
        """Angular velocity from time differentiating the DCM. """
        from sympy.physics.vector.functions import dynamicsymbols
        dcm2diff = self.dcm(otherframe)
        diffed = dcm2diff.diff(dynamicsymbols._t)
        # angvelmat = diffed * dcm2diff.T
        # This one seems to produce the correct result when I checked using Autolev.
        angvelmat = dcm2diff*diffed.T
        w1 = trigsimp(expand(angvelmat[7]), recursive=True)
        w2 = trigsimp(expand(angvelmat[2]), recursive=True)
        w3 = trigsimp(expand(angvelmat[3]), recursive=True)
        return -Vector([(Matrix([w1, w2, w3]), self)])

    def variable_map(self, otherframe):
        """
        Returns a dictionary which expresses the coordinate variables
        of this frame in terms of the variables of otherframe.

        If Vector.simp is True, returns a simplified version of the mapped
        values. Else, returns them without simplification.

        Simplification of the expressions may take time.

        Parameters
        ==========

        otherframe : ReferenceFrame
            The other frame to map the variables to

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, dynamicsymbols
        >>> A = ReferenceFrame('A')
        >>> q = dynamicsymbols('q')
        >>> B = A.orientnew('B', 'Axis', [q, A.z])
        >>> A.variable_map(B)
        {A_x: B_x*cos(q(t)) - B_y*sin(q(t)), A_y: B_x*sin(q(t)) + B_y*cos(q(t)), A_z: B_z}

        """

        _check_frame(otherframe)
        if (otherframe, Vector.simp) in self._var_dict:
            return self._var_dict[(otherframe, Vector.simp)]
        else:
            vars_matrix = self.dcm(otherframe) * Matrix(otherframe.varlist)
            mapping = {}
            for i, x in enumerate(self):
                if Vector.simp:
                    mapping[self.varlist[i]] = trigsimp(vars_matrix[i], method='fu')
                else:
                    mapping[self.varlist[i]] = vars_matrix[i]
            self._var_dict[(otherframe, Vector.simp)] = mapping
            return mapping

    def ang_acc_in(self, otherframe):
        """Returns the angular acceleration Vector of the ReferenceFrame.

        Effectively returns the Vector:
        ^N alpha ^B
        which represent the angular acceleration of B in N, where B is self, and
        N is otherframe.

        Parameters
        ==========

        otherframe : ReferenceFrame
            The ReferenceFrame which the angular acceleration is returned in.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Vector
        >>> N = ReferenceFrame('N')
        >>> A = ReferenceFrame('A')
        >>> V = 10 * N.x
        >>> A.set_ang_acc(N, V)
        >>> A.ang_acc_in(N)
        10*N.x

        """

        _check_frame(otherframe)
        if otherframe in self._ang_acc_dict:
            return self._ang_acc_dict[otherframe]
        else:
            return self.ang_vel_in(otherframe).dt(otherframe)

    def ang_vel_in(self, otherframe):
        """Returns the angular velocity Vector of the ReferenceFrame.

        Effectively returns the Vector:
        ^N omega ^B
        which represent the angular velocity of B in N, where B is self, and
        N is otherframe.

        Parameters
        ==========

        otherframe : ReferenceFrame
            The ReferenceFrame which the angular velocity is returned in.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Vector
        >>> N = ReferenceFrame('N')
        >>> A = ReferenceFrame('A')
        >>> V = 10 * N.x
        >>> A.set_ang_vel(N, V)
        >>> A.ang_vel_in(N)
        10*N.x

        """

        _check_frame(otherframe)
        flist = self._dict_list(otherframe, 1)
        outvec = Vector(0)
        for i in range(len(flist) - 1):
            outvec += flist[i]._ang_vel_dict[flist[i + 1]]
        return outvec

    def dcm(self, otherframe):
        """The direction cosine matrix between frames.

        This gives the DCM between this frame and the otherframe.
        The format is N.xyz = N.dcm(B) * B.xyz
        A SymPy Matrix is returned.

        Parameters
        ==========

        otherframe : ReferenceFrame
            The otherframe which the DCM is generated to.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Vector
        >>> from sympy import symbols
        >>> q1 = symbols('q1')
        >>> N = ReferenceFrame('N')
        >>> A = N.orientnew('A', 'Axis', [q1, N.x])
        >>> N.dcm(A)
        Matrix([
        [1,       0,        0],
        [0, cos(q1), -sin(q1)],
        [0, sin(q1),  cos(q1)]])

        """

        _check_frame(otherframe)
        #Check if the dcm wrt that frame has already been calculated
        if otherframe in self._dcm_cache:
            return self._dcm_cache[otherframe]
        flist = self._dict_list(otherframe, 0)
        outdcm = eye(3)
        for i in range(len(flist) - 1):
            outdcm = outdcm * flist[i]._dcm_dict[flist[i + 1]]
        #After calculation, store the dcm in dcm cache for faster
        #future retrieval
        self._dcm_cache[otherframe] = outdcm
        otherframe._dcm_cache[self] = outdcm.T
        return outdcm

    def orient(self, parent, rot_type, amounts, rot_order=''):
        """Defines the orientation of this frame relative to a parent frame.

        Parameters
        ==========

        parent : ReferenceFrame
            The frame that this ReferenceFrame will have its orientation matrix
            defined in relation to.
        rot_type : str
            The type of orientation matrix that is being created. Supported
            types are 'Body', 'Space', 'Quaternion', 'Axis', and 'DCM'.
            See examples for correct usage.
        amounts : list OR value
            The quantities that the orientation matrix will be defined by.
            In case of rot_type='DCM', value must be a
            sympy.matrices.MatrixBase object (or subclasses of it).
        rot_order : str or int
            If applicable, the order of a series of rotations.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Vector
        >>> from sympy import symbols, eye, ImmutableMatrix
        >>> q0, q1, q2, q3 = symbols('q0 q1 q2 q3')
        >>> N = ReferenceFrame('N')
        >>> B = ReferenceFrame('B')

        Now we have a choice of how to implement the orientation. First is
        Body. Body orientation takes this reference frame through three
        successive simple rotations. Acceptable rotation orders are of length
        3, expressed in XYZ or 123, and cannot have a rotation about about an
        axis twice in a row.

        >>> B.orient(N, 'Body', [q1, q2, q3], 123)
        >>> B.orient(N, 'Body', [q1, q2, 0], 'ZXZ')
        >>> B.orient(N, 'Body', [0, 0, 0], 'XYX')

        Next is Space. Space is like Body, but the rotations are applied in the
        opposite order.

        >>> B.orient(N, 'Space', [q1, q2, q3], '312')

        Next is Quaternion. This orients the new ReferenceFrame with
        Quaternions, defined as a finite rotation about lambda, a unit vector,
        by some amount theta.
        This orientation is described by four parameters:
        q0 = cos(theta/2)
        q1 = lambda_x sin(theta/2)
        q2 = lambda_y sin(theta/2)
        q3 = lambda_z sin(theta/2)
        Quaternion does not take in a rotation order.

        >>> B.orient(N, 'Quaternion', [q0, q1, q2, q3])

        Next is Axis. This is a rotation about an arbitrary, non-time-varying
        axis by some angle. The axis is supplied as a Vector. This is how
        simple rotations are defined.

        >>> B.orient(N, 'Axis', [q1, N.x + 2 * N.y])

        Last is DCM (Direction Cosine Matrix). This is a rotation matrix
        given manually.

        >>> B.orient(N, 'DCM', eye(3))
        >>> B.orient(N, 'DCM', ImmutableMatrix([[0, 1, 0], [0, 0, -1], [-1, 0, 0]]))

        """

        from sympy.physics.vector.functions import dynamicsymbols
        _check_frame(parent)

        # Allow passing a rotation matrix manually.
        if rot_type == 'DCM':
            # When rot_type == 'DCM', then amounts must be a Matrix type object
            # (e.g. sympy.matrices.dense.MutableDenseMatrix).
            if not isinstance(amounts, MatrixBase):
                raise TypeError("Amounts must be a sympy Matrix type object.")
        else:
            amounts = list(amounts)
            for i, v in enumerate(amounts):
                if not isinstance(v, Vector):
                    amounts[i] = sympify(v)

        def _rot(axis, angle):
            """DCM for simple axis 1,2,or 3 rotations. """
            if axis == 1:
                return Matrix([[1, 0, 0],
                    [0, cos(angle), -sin(angle)],
                    [0, sin(angle), cos(angle)]])
            elif axis == 2:
                return Matrix([[cos(angle), 0, sin(angle)],
                    [0, 1, 0],
                    [-sin(angle), 0, cos(angle)]])
            elif axis == 3:
                return Matrix([[cos(angle), -sin(angle), 0],
                    [sin(angle), cos(angle), 0],
                    [0, 0, 1]])

        approved_orders = ('123', '231', '312', '132', '213', '321', '121',
                           '131', '212', '232', '313', '323', '')
        # make sure XYZ => 123 and rot_type is in upper case
        rot_order = translate(str(rot_order), 'XYZxyz', '123123')
        rot_type = rot_type.upper()
        if not rot_order in approved_orders:
            raise TypeError('The supplied order is not an approved type')
        parent_orient = []
        if rot_type == 'AXIS':
            if not rot_order == '':
                raise TypeError('Axis orientation takes no rotation order')
            if not (isinstance(amounts, (list, tuple)) & (len(amounts) == 2)):
                raise TypeError('Amounts are a list or tuple of length 2')
            theta = amounts[0]
            axis = amounts[1]
            axis = _check_vector(axis)
            if not axis.dt(parent) == 0:
                raise ValueError('Axis cannot be time-varying')
            axis = axis.express(parent).normalize()
            axis = axis.args[0][0]
            parent_orient = ((eye(3) - axis * axis.T) * cos(theta) +
                    Matrix([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]],
                        [-axis[1], axis[0], 0]]) * sin(theta) + axis * axis.T)
        elif rot_type == 'QUATERNION':
            if not rot_order == '':
                raise TypeError(
                    'Quaternion orientation takes no rotation order')
            if not (isinstance(amounts, (list, tuple)) & (len(amounts) == 4)):
                raise TypeError('Amounts are a list or tuple of length 4')
            q0, q1, q2, q3 = amounts
            parent_orient = (Matrix([[q0 ** 2 + q1 ** 2 - q2 ** 2 - q3 **
                2, 2 * (q1 * q2 - q0 * q3), 2 * (q0 * q2 + q1 * q3)],
                [2 * (q1 * q2 + q0 * q3), q0 ** 2 - q1 ** 2 + q2 ** 2 - q3 ** 2,
                2 * (q2 * q3 - q0 * q1)], [2 * (q1 * q3 - q0 * q2), 2 * (q0 *
                q1 + q2 * q3), q0 ** 2 - q1 ** 2 - q2 ** 2 + q3 ** 2]]))
        elif rot_type == 'BODY':
            if not (len(amounts) == 3 & len(rot_order) == 3):
                raise TypeError('Body orientation takes 3 values & 3 orders')
            a1 = int(rot_order[0])
            a2 = int(rot_order[1])
            a3 = int(rot_order[2])
            parent_orient = (_rot(a1, amounts[0]) * _rot(a2, amounts[1])
                    * _rot(a3, amounts[2]))
        elif rot_type == 'SPACE':
            if not (len(amounts) == 3 & len(rot_order) == 3):
                raise TypeError('Space orientation takes 3 values & 3 orders')
            a1 = int(rot_order[0])
            a2 = int(rot_order[1])
            a3 = int(rot_order[2])
            parent_orient = (_rot(a3, amounts[2]) * _rot(a2, amounts[1])
                    * _rot(a1, amounts[0]))
        elif rot_type == 'DCM':
            parent_orient = amounts
        else:
            raise NotImplementedError('That is not an implemented rotation')
        #Reset the _dcm_cache of this frame, and remove it from the _dcm_caches
        #of the frames it is linked to. Also remove it from the _dcm_dict of
        #its parent
        frames = self._dcm_cache.keys()
        dcm_dict_del = []
        dcm_cache_del = []
        for frame in frames:
            if frame in self._dcm_dict:
                dcm_dict_del += [frame]
            dcm_cache_del += [frame]
        for frame in dcm_dict_del:
            del frame._dcm_dict[self]
        for frame in dcm_cache_del:
            del frame._dcm_cache[self]
        #Add the dcm relationship to _dcm_dict
        self._dcm_dict = self._dlist[0] = {}
        self._dcm_dict.update({parent: parent_orient.T})
        parent._dcm_dict.update({self: parent_orient})
        #Also update the dcm cache after resetting it
        self._dcm_cache = {}
        self._dcm_cache.update({parent: parent_orient.T})
        parent._dcm_cache.update({self: parent_orient})
        if rot_type == 'QUATERNION':
            t = dynamicsymbols._t
            q0, q1, q2, q3 = amounts
            q0d = diff(q0, t)
            q1d = diff(q1, t)
            q2d = diff(q2, t)
            q3d = diff(q3, t)
            w1 = 2 * (q1d * q0 + q2d * q3 - q3d * q2 - q0d * q1)
            w2 = 2 * (q2d * q0 + q3d * q1 - q1d * q3 - q0d * q2)
            w3 = 2 * (q3d * q0 + q1d * q2 - q2d * q1 - q0d * q3)
            wvec = Vector([(Matrix([w1, w2, w3]), self)])
        elif rot_type == 'AXIS':
            thetad = (amounts[0]).diff(dynamicsymbols._t)
            wvec = thetad * amounts[1].express(parent).normalize()
        elif rot_type == 'DCM':
            wvec = self._w_diff_dcm(parent)
        else:
            try:
                from sympy.polys.polyerrors import CoercionFailed
                from sympy.physics.vector.functions import kinematic_equations
                q1, q2, q3 = amounts
                u1, u2, u3 = symbols('u1, u2, u3', cls=Dummy)
                templist = kinematic_equations([u1, u2, u3], [q1, q2, q3],
                                               rot_type, rot_order)
                templist = [expand(i) for i in templist]
                td = solve(templist, [u1, u2, u3])
                u1 = expand(td[u1])
                u2 = expand(td[u2])
                u3 = expand(td[u3])
                wvec = u1 * self.x + u2 * self.y + u3 * self.z
            except (CoercionFailed, AssertionError):
                wvec = self._w_diff_dcm(parent)
        self._ang_vel_dict.update({parent: wvec})
        parent._ang_vel_dict.update({self: -wvec})
        self._var_dict = {}

    def orientnew(self, newname, rot_type, amounts, rot_order='',
                  variables=None, indices=None, latexs=None):
        """Creates a new ReferenceFrame oriented with respect to this Frame.

        See ReferenceFrame.orient() for acceptable rotation types, amounts,
        and orders. Parent is going to be self.

        Parameters
        ==========

        newname : str
            The name for the new ReferenceFrame
        rot_type : str
            The type of orientation matrix that is being created.
        amounts : list OR value
            The quantities that the orientation matrix will be defined by.
        rot_order : str
            If applicable, the order of a series of rotations.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Vector
        >>> from sympy import symbols
        >>> q0, q1, q2, q3 = symbols('q0 q1 q2 q3')
        >>> N = ReferenceFrame('N')

        Now we have a choice of how to implement the orientation. First is
        Body. Body orientation takes this reference frame through three
        successive simple rotations. Acceptable rotation orders are of length
        3, expressed in XYZ or 123, and cannot have a rotation about about an
        axis twice in a row.

        >>> A = N.orientnew('A', 'Body', [q1, q2, q3], '123')
        >>> A = N.orientnew('A', 'Body', [q1, q2, 0], 'ZXZ')
        >>> A = N.orientnew('A', 'Body', [0, 0, 0], 'XYX')

        Next is Space. Space is like Body, but the rotations are applied in the
        opposite order.

        >>> A = N.orientnew('A', 'Space', [q1, q2, q3], '312')

        Next is Quaternion. This orients the new ReferenceFrame with
        Quaternions, defined as a finite rotation about lambda, a unit vector,
        by some amount theta.
        This orientation is described by four parameters:
        q0 = cos(theta/2)
        q1 = lambda_x sin(theta/2)
        q2 = lambda_y sin(theta/2)
        q3 = lambda_z sin(theta/2)
        Quaternion does not take in a rotation order.

        >>> A = N.orientnew('A', 'Quaternion', [q0, q1, q2, q3])

        Last is Axis. This is a rotation about an arbitrary, non-time-varying
        axis by some angle. The axis is supplied as a Vector. This is how
        simple rotations are defined.

        >>> A = N.orientnew('A', 'Axis', [q1, N.x])

        """

        newframe = self.__class__(newname, variables=variables,
                                  indices=indices, latexs=latexs)
        newframe.orient(self, rot_type, amounts, rot_order)
        return newframe

    def set_ang_acc(self, otherframe, value):
        """Define the angular acceleration Vector in a ReferenceFrame.

        Defines the angular acceleration of this ReferenceFrame, in another.
        Angular acceleration can be defined with respect to multiple different
        ReferenceFrames. Care must be taken to not create loops which are
        inconsistent.

        Parameters
        ==========

        otherframe : ReferenceFrame
            A ReferenceFrame to define the angular acceleration in
        value : Vector
            The Vector representing angular acceleration

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Vector
        >>> N = ReferenceFrame('N')
        >>> A = ReferenceFrame('A')
        >>> V = 10 * N.x
        >>> A.set_ang_acc(N, V)
        >>> A.ang_acc_in(N)
        10*N.x

        """

        if value == 0:
            value = Vector(0)
        value = _check_vector(value)
        _check_frame(otherframe)
        self._ang_acc_dict.update({otherframe: value})
        otherframe._ang_acc_dict.update({self: -value})

    def set_ang_vel(self, otherframe, value):
        """Define the angular velocity vector in a ReferenceFrame.

        Defines the angular velocity of this ReferenceFrame, in another.
        Angular velocity can be defined with respect to multiple different
        ReferenceFrames. Care must be taken to not create loops which are
        inconsistent.

        Parameters
        ==========

        otherframe : ReferenceFrame
            A ReferenceFrame to define the angular velocity in
        value : Vector
            The Vector representing angular velocity

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, Vector
        >>> N = ReferenceFrame('N')
        >>> A = ReferenceFrame('A')
        >>> V = 10 * N.x
        >>> A.set_ang_vel(N, V)
        >>> A.ang_vel_in(N)
        10*N.x

        """

        if value == 0:
            value = Vector(0)
        value = _check_vector(value)
        _check_frame(otherframe)
        self._ang_vel_dict.update({otherframe: value})
        otherframe._ang_vel_dict.update({self: -value})

    @property
    def x(self):
        """The basis Vector for the ReferenceFrame, in the x direction. """
        return self._x

    @property
    def y(self):
        """The basis Vector for the ReferenceFrame, in the y direction. """
        return self._y

    @property
    def z(self):
        """The basis Vector for the ReferenceFrame, in the z direction. """
        return self._z

    def partial_velocity(self, frame, *gen_speeds):
        """Returns the partial angular velocities of this frame in the given
        frame with respect to one or more provided generalized speeds.

        Parameters
        ==========
        frame : ReferenceFrame
            The frame with which the angular velocity is defined in.
        gen_speeds : functions of time
            The generalized speeds.

        Returns
        =======
        partial_velocities : tuple of Vector
            The partial angular velocity vectors corresponding to the provided
            generalized speeds.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, dynamicsymbols
        >>> N = ReferenceFrame('N')
        >>> A = ReferenceFrame('A')
        >>> u1, u2 = dynamicsymbols('u1, u2')
        >>> A.set_ang_vel(N, u1 * A.x + u2 * N.y)
        >>> A.partial_velocity(N, u1)
        A.x
        >>> A.partial_velocity(N, u1, u2)
        (A.x, N.y)

        """

        partials = [self.ang_vel_in(frame).diff(speed, frame, var_in_dcm=False)
                    for speed in gen_speeds]

        if len(partials) == 1:
            return partials[0]
        else:
            return tuple(partials)


def _check_frame(other):
    from .vector import VectorTypeError
    if not isinstance(other, ReferenceFrame):
        raise VectorTypeError(other, ReferenceFrame('A'))
