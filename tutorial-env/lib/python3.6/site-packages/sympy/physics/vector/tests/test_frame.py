from sympy import symbols, sin, cos, pi, zeros, eye, ImmutableMatrix as Matrix
from sympy.physics.vector import (ReferenceFrame, Vector, CoordinateSym,
                                  dynamicsymbols, time_derivative, express,
                                  dot)
from sympy.physics.vector.frame import _check_frame
from sympy.physics.vector.vector import VectorTypeError
from sympy.utilities.pytest import raises

Vector.simp = True


def test_coordinate_vars():
    """Tests the coordinate variables functionality"""
    A = ReferenceFrame('A')
    assert CoordinateSym('Ax', A, 0) == A[0]
    assert CoordinateSym('Ax', A, 1) == A[1]
    assert CoordinateSym('Ax', A, 2) == A[2]
    raises(ValueError, lambda: CoordinateSym('Ax', A, 3))
    q = dynamicsymbols('q')
    qd = dynamicsymbols('q', 1)
    assert isinstance(A[0], CoordinateSym) and \
           isinstance(A[0], CoordinateSym) and \
           isinstance(A[0], CoordinateSym)
    assert A.variable_map(A) == {A[0]:A[0], A[1]:A[1], A[2]:A[2]}
    assert A[0].frame == A
    B = A.orientnew('B', 'Axis', [q, A.z])
    assert B.variable_map(A) == {B[2]: A[2], B[1]: -A[0]*sin(q) + A[1]*cos(q),
                                 B[0]: A[0]*cos(q) + A[1]*sin(q)}
    assert A.variable_map(B) == {A[0]: B[0]*cos(q) - B[1]*sin(q),
                                 A[1]: B[0]*sin(q) + B[1]*cos(q), A[2]: B[2]}
    assert time_derivative(B[0], A) == -A[0]*sin(q)*qd + A[1]*cos(q)*qd
    assert time_derivative(B[1], A) == -A[0]*cos(q)*qd - A[1]*sin(q)*qd
    assert time_derivative(B[2], A) == 0
    assert express(B[0], A, variables=True) == A[0]*cos(q) + A[1]*sin(q)
    assert express(B[1], A, variables=True) == -A[0]*sin(q) + A[1]*cos(q)
    assert express(B[2], A, variables=True) == A[2]
    assert time_derivative(A[0]*A.x + A[1]*A.y + A[2]*A.z, B) == A[1]*qd*A.x - A[0]*qd*A.y
    assert time_derivative(B[0]*B.x + B[1]*B.y + B[2]*B.z, A) == - B[1]*qd*B.x + B[0]*qd*B.y
    assert express(B[0]*B[1]*B[2], A, variables=True) == \
           A[2]*(-A[0]*sin(q) + A[1]*cos(q))*(A[0]*cos(q) + A[1]*sin(q))
    assert (time_derivative(B[0]*B[1]*B[2], A) -
            (A[2]*(-A[0]**2*cos(2*q) -
             2*A[0]*A[1]*sin(2*q) +
             A[1]**2*cos(2*q))*qd)).trigsimp() == 0
    assert express(B[0]*B.x + B[1]*B.y + B[2]*B.z, A) == \
           (B[0]*cos(q) - B[1]*sin(q))*A.x + (B[0]*sin(q) + \
           B[1]*cos(q))*A.y + B[2]*A.z
    assert express(B[0]*B.x + B[1]*B.y + B[2]*B.z, A, variables=True) == \
           A[0]*A.x + A[1]*A.y + A[2]*A.z
    assert express(A[0]*A.x + A[1]*A.y + A[2]*A.z, B) == \
           (A[0]*cos(q) + A[1]*sin(q))*B.x + \
           (-A[0]*sin(q) + A[1]*cos(q))*B.y + A[2]*B.z
    assert express(A[0]*A.x + A[1]*A.y + A[2]*A.z, B, variables=True) == \
           B[0]*B.x + B[1]*B.y + B[2]*B.z
    N = B.orientnew('N', 'Axis', [-q, B.z])
    assert N.variable_map(A) == {N[0]: A[0], N[2]: A[2], N[1]: A[1]}
    C = A.orientnew('C', 'Axis', [q, A.x + A.y + A.z])
    mapping = A.variable_map(C)
    assert mapping[A[0]] == 2*C[0]*cos(q)/3 + C[0]/3 - 2*C[1]*sin(q + pi/6)/3 +\
           C[1]/3 - 2*C[2]*cos(q + pi/3)/3 + C[2]/3
    assert mapping[A[1]] == -2*C[0]*cos(q + pi/3)/3 + \
           C[0]/3 + 2*C[1]*cos(q)/3 + C[1]/3 - 2*C[2]*sin(q + pi/6)/3 + C[2]/3
    assert mapping[A[2]] == -2*C[0]*sin(q + pi/6)/3 + C[0]/3 - \
           2*C[1]*cos(q + pi/3)/3 + C[1]/3 + 2*C[2]*cos(q)/3 + C[2]/3


def test_ang_vel():
    q1, q2, q3, q4 = dynamicsymbols('q1 q2 q3 q4')
    q1d, q2d, q3d, q4d = dynamicsymbols('q1 q2 q3 q4', 1)
    N = ReferenceFrame('N')
    A = N.orientnew('A', 'Axis', [q1, N.z])
    B = A.orientnew('B', 'Axis', [q2, A.x])
    C = B.orientnew('C', 'Axis', [q3, B.y])
    D = N.orientnew('D', 'Axis', [q4, N.y])
    u1, u2, u3 = dynamicsymbols('u1 u2 u3')
    assert A.ang_vel_in(N) == (q1d)*A.z
    assert B.ang_vel_in(N) == (q2d)*B.x + (q1d)*A.z
    assert C.ang_vel_in(N) == (q3d)*C.y + (q2d)*B.x + (q1d)*A.z

    A2 = N.orientnew('A2', 'Axis', [q4, N.y])
    assert N.ang_vel_in(N) == 0
    assert N.ang_vel_in(A) == -q1d*N.z
    assert N.ang_vel_in(B) == -q1d*A.z - q2d*B.x
    assert N.ang_vel_in(C) == -q1d*A.z - q2d*B.x - q3d*B.y
    assert N.ang_vel_in(A2) == -q4d*N.y

    assert A.ang_vel_in(N) == q1d*N.z
    assert A.ang_vel_in(A) == 0
    assert A.ang_vel_in(B) == - q2d*B.x
    assert A.ang_vel_in(C) == - q2d*B.x - q3d*B.y
    assert A.ang_vel_in(A2) == q1d*N.z - q4d*N.y

    assert B.ang_vel_in(N) == q1d*A.z + q2d*A.x
    assert B.ang_vel_in(A) == q2d*A.x
    assert B.ang_vel_in(B) == 0
    assert B.ang_vel_in(C) == -q3d*B.y
    assert B.ang_vel_in(A2) == q1d*A.z + q2d*A.x - q4d*N.y

    assert C.ang_vel_in(N) == q1d*A.z + q2d*A.x + q3d*B.y
    assert C.ang_vel_in(A) == q2d*A.x + q3d*C.y
    assert C.ang_vel_in(B) == q3d*B.y
    assert C.ang_vel_in(C) == 0
    assert C.ang_vel_in(A2) == q1d*A.z + q2d*A.x + q3d*B.y - q4d*N.y

    assert A2.ang_vel_in(N) == q4d*A2.y
    assert A2.ang_vel_in(A) == q4d*A2.y - q1d*N.z
    assert A2.ang_vel_in(B) == q4d*N.y - q1d*A.z - q2d*A.x
    assert A2.ang_vel_in(C) == q4d*N.y - q1d*A.z - q2d*A.x - q3d*B.y
    assert A2.ang_vel_in(A2) == 0

    C.set_ang_vel(N, u1*C.x + u2*C.y + u3*C.z)
    assert C.ang_vel_in(N) == (u1)*C.x + (u2)*C.y + (u3)*C.z
    assert N.ang_vel_in(C) == (-u1)*C.x + (-u2)*C.y + (-u3)*C.z
    assert C.ang_vel_in(D) == (u1)*C.x + (u2)*C.y + (u3)*C.z + (-q4d)*D.y
    assert D.ang_vel_in(C) == (-u1)*C.x + (-u2)*C.y + (-u3)*C.z + (q4d)*D.y

    q0 = dynamicsymbols('q0')
    q0d = dynamicsymbols('q0', 1)
    E = N.orientnew('E', 'Quaternion', (q0, q1, q2, q3))
    assert E.ang_vel_in(N) == (
        2 * (q1d * q0 + q2d * q3 - q3d * q2 - q0d * q1) * E.x +
        2 * (q2d * q0 + q3d * q1 - q1d * q3 - q0d * q2) * E.y +
        2 * (q3d * q0 + q1d * q2 - q2d * q1 - q0d * q3) * E.z)

    F = N.orientnew('F', 'Body', (q1, q2, q3), 313)
    assert F.ang_vel_in(N) == ((sin(q2)*sin(q3)*q1d + cos(q3)*q2d)*F.x +
        (sin(q2)*cos(q3)*q1d - sin(q3)*q2d)*F.y + (cos(q2)*q1d + q3d)*F.z)
    G = N.orientnew('G', 'Axis', (q1, N.x + N.y))
    assert G.ang_vel_in(N) == q1d * (N.x + N.y).normalize()
    assert N.ang_vel_in(G) == -q1d * (N.x + N.y).normalize()


def test_dcm():
    q1, q2, q3, q4 = dynamicsymbols('q1 q2 q3 q4')
    N = ReferenceFrame('N')
    A = N.orientnew('A', 'Axis', [q1, N.z])
    B = A.orientnew('B', 'Axis', [q2, A.x])
    C = B.orientnew('C', 'Axis', [q3, B.y])
    D = N.orientnew('D', 'Axis', [q4, N.y])
    E = N.orientnew('E', 'Space', [q1, q2, q3], '123')
    assert N.dcm(C) == Matrix([
        [- sin(q1) * sin(q2) * sin(q3) + cos(q1) * cos(q3), - sin(q1) *
        cos(q2), sin(q1) * sin(q2) * cos(q3) + sin(q3) * cos(q1)], [sin(q1) *
        cos(q3) + sin(q2) * sin(q3) * cos(q1), cos(q1) * cos(q2), sin(q1) *
            sin(q3) - sin(q2) * cos(q1) * cos(q3)], [- sin(q3) * cos(q2), sin(q2),
        cos(q2) * cos(q3)]])
    # This is a little touchy.  Is it ok to use simplify in assert?
    test_mat = D.dcm(C) - Matrix(
        [[cos(q1) * cos(q3) * cos(q4) - sin(q3) * (- sin(q4) * cos(q2) +
        sin(q1) * sin(q2) * cos(q4)), - sin(q2) * sin(q4) - sin(q1) *
            cos(q2) * cos(q4), sin(q3) * cos(q1) * cos(q4) + cos(q3) * (- sin(q4) *
        cos(q2) + sin(q1) * sin(q2) * cos(q4))], [sin(q1) * cos(q3) +
        sin(q2) * sin(q3) * cos(q1), cos(q1) * cos(q2), sin(q1) * sin(q3) -
            sin(q2) * cos(q1) * cos(q3)], [sin(q4) * cos(q1) * cos(q3) -
        sin(q3) * (cos(q2) * cos(q4) + sin(q1) * sin(q2) * sin(q4)), sin(q2) *
                cos(q4) - sin(q1) * sin(q4) * cos(q2), sin(q3) * sin(q4) * cos(q1) +
                cos(q3) * (cos(q2) * cos(q4) + sin(q1) * sin(q2) * sin(q4))]])
    assert test_mat.expand() == zeros(3, 3)
    assert E.dcm(N) == Matrix(
        [[cos(q2)*cos(q3), sin(q3)*cos(q2), -sin(q2)],
        [sin(q1)*sin(q2)*cos(q3) - sin(q3)*cos(q1), sin(q1)*sin(q2)*sin(q3) +
        cos(q1)*cos(q3), sin(q1)*cos(q2)], [sin(q1)*sin(q3) +
        sin(q2)*cos(q1)*cos(q3), - sin(q1)*cos(q3) + sin(q2)*sin(q3)*cos(q1),
         cos(q1)*cos(q2)]])


# This test has been added to test the _w_diff_dcm() function
# for which a test was previously not included.
# Also note that the _w_diff_dcm() function was changed as part of
# PR #14758 as it was observed to be giving incorrect results
# when compared with Autolev results.
def test_w_diff_dcm():
    a = ReferenceFrame('a')
    b = ReferenceFrame('b')
    c11, c12, c13, c21, c22, c23, c31, c32, c33 = dynamicsymbols('c11 c12 c13 c21 c22 c23 c31 c32 c33')
    c11d, c12d, c13d, c21d, c22d, c23d, c31d, c32d, c33d = dynamicsymbols('c11 c12 c13 c21 c22 c23 c31 c32 c33', 1)
    b.orient(a, 'DCM', Matrix([c11,c12,c13,c21,c22,c23,c31,c32,c33]).reshape(3, 3))
    b1a=(b.x).express(a)
    b2a=(b.y).express(a)
    b3a=(b.z).express(a)
    b.set_ang_vel(a, b.x*(dot((b3a).dt(a), b.y)) + b.y*(dot((b1a).dt(a), b.z)) +
                     b.z*(dot((b2a).dt(a), b.x)))
    expr = ((c12*c13d + c22*c23d + c32*c33d)*b.x + (c13*c11d + c23*c21d + c33*c31d)*b.y +
           (c11*c12d + c21*c22d + c31*c32d)*b.z)
    assert b.ang_vel_in(a) - expr == 0


def test_orientnew_respects_parent_class():
    class MyReferenceFrame(ReferenceFrame):
        pass
    B = MyReferenceFrame('B')
    C = B.orientnew('C', 'Axis', [0, B.x])
    assert isinstance(C, MyReferenceFrame)


def test_orientnew_respects_input_indices():
    N = ReferenceFrame('N')
    q1 = dynamicsymbols('q1')
    A = N.orientnew('a', 'Axis', [q1, N.z])
    #modify default indices:
    minds = [x+'1' for x in N.indices]
    B = N.orientnew('b', 'Axis', [q1, N.z], indices=minds)

    assert N.indices == A.indices
    assert B.indices == minds

def test_orientnew_respects_input_latexs():
    N = ReferenceFrame('N')
    q1 = dynamicsymbols('q1')
    A = N.orientnew('a', 'Axis', [q1, N.z])

    #build default and alternate latex_vecs:
    def_latex_vecs = [(r"\mathbf{\hat{%s}_%s}" % (A.name.lower(),
                      A.indices[0])), (r"\mathbf{\hat{%s}_%s}" %
                      (A.name.lower(), A.indices[1])),
                      (r"\mathbf{\hat{%s}_%s}" % (A.name.lower(),
                      A.indices[2]))]

    name = 'b'
    indices = [x+'1' for x in N.indices]
    new_latex_vecs = [(r"\mathbf{\hat{%s}_{%s}}" % (name.lower(),
                      indices[0])), (r"\mathbf{\hat{%s}_{%s}}" %
                      (name.lower(), indices[1])),
                      (r"\mathbf{\hat{%s}_{%s}}" % (name.lower(),
                      indices[2]))]

    B = N.orientnew(name, 'Axis', [q1, N.z], latexs=new_latex_vecs)

    assert A.latex_vecs == def_latex_vecs
    assert B.latex_vecs == new_latex_vecs
    assert B.indices != indices

def test_orientnew_respects_input_variables():
    N = ReferenceFrame('N')
    q1 = dynamicsymbols('q1')
    A = N.orientnew('a', 'Axis', [q1, N.z])

    #build non-standard variable names
    name = 'b'
    new_variables = ['notb_'+x+'1' for x in N.indices]
    B = N.orientnew(name, 'Axis', [q1, N.z], variables=new_variables)

    for j,var in enumerate(A.varlist):
        assert var.name == A.name + '_' + A.indices[j]

    for j,var in enumerate(B.varlist):
        assert var.name == new_variables[j]

def test_issue_10348():
    u = dynamicsymbols('u:3')
    I = ReferenceFrame('I')
    A = I.orientnew('A', 'space', u, 'XYZ')


def test_issue_11503():
    A = ReferenceFrame("A")
    B = A.orientnew("B", "Axis", [35, A.y])
    C = ReferenceFrame("C")
    A.orient(C, "Axis", [70, C.z])


def test_partial_velocity():

    N = ReferenceFrame('N')
    A = ReferenceFrame('A')

    u1, u2 = dynamicsymbols('u1, u2')

    A.set_ang_vel(N, u1 * A.x + u2 * N.y)

    assert N.partial_velocity(A, u1) == -A.x
    assert N.partial_velocity(A, u1, u2) == (-A.x, -N.y)

    assert A.partial_velocity(N, u1) == A.x
    assert A.partial_velocity(N, u1, u2) == (A.x, N.y)

    assert N.partial_velocity(N, u1) == 0
    assert A.partial_velocity(A, u1) == 0


def test_issue_11498():
    A = ReferenceFrame('A')
    B = ReferenceFrame('B')

    # Identity transformation
    A.orient(B, 'DCM', eye(3))
    assert A.dcm(B) == Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert B.dcm(A) == Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    # x -> y
    # y -> -z
    # z -> -x
    A.orient(B, 'DCM', Matrix([[0, 1, 0], [0, 0, -1], [-1, 0, 0]]))
    assert B.dcm(A) == Matrix([[0, 1, 0], [0, 0, -1], [-1, 0, 0]])
    assert A.dcm(B) == Matrix([[0, 0, -1], [1, 0, 0], [0, -1, 0]])
    assert B.dcm(A).T == A.dcm(B)


def test_reference_frame():
    raises(TypeError, lambda: ReferenceFrame(0))
    raises(TypeError, lambda: ReferenceFrame('N', 0))
    raises(ValueError, lambda: ReferenceFrame('N', [0, 1]))
    raises(TypeError, lambda: ReferenceFrame('N', [0, 1, 2]))
    raises(TypeError, lambda: ReferenceFrame('N', ['a', 'b', 'c'], 0))
    raises(ValueError, lambda: ReferenceFrame('N', ['a', 'b', 'c'], [0, 1]))
    raises(TypeError, lambda: ReferenceFrame('N', ['a', 'b', 'c'], [0, 1, 2]))
    raises(TypeError, lambda: ReferenceFrame('N', ['a', 'b', 'c'],
                                                 ['a', 'b', 'c'], 0))
    raises(ValueError, lambda: ReferenceFrame('N', ['a', 'b', 'c'],
                                              ['a', 'b', 'c'], [0, 1]))
    raises(TypeError, lambda: ReferenceFrame('N', ['a', 'b', 'c'],
                                             ['a', 'b', 'c'], [0, 1, 2]))
    N = ReferenceFrame('N')
    assert N[0] == CoordinateSym('N_x', N, 0)
    assert N[1] == CoordinateSym('N_y', N, 1)
    assert N[2] == CoordinateSym('N_z', N, 2)
    raises(ValueError, lambda: N[3])
    N = ReferenceFrame('N', ['a', 'b', 'c'])
    assert N['a'] == N.x
    assert N['b'] == N.y
    assert N['c'] == N.z
    raises(ValueError, lambda: N['d'])
    assert str(N) == 'N'

    A = ReferenceFrame('A')
    B = ReferenceFrame('B')
    q0, q1, q2, q3 = symbols('q0 q1 q2 q3')
    raises(TypeError, lambda: A.orient(B, 'DCM', 0))
    raises(TypeError, lambda: B.orient(N, 'Space', [q1, q2, q3], '222'))
    raises(TypeError, lambda: B.orient(N, 'Axis', [q1, N.x + 2 * N.y], '222'))
    raises(TypeError, lambda: B.orient(N, 'Axis', q1))
    raises(TypeError, lambda: B.orient(N, 'Axis', [q1]))
    raises(TypeError, lambda: B.orient(N, 'Quaternion', [q0, q1, q2, q3], '222'))
    raises(TypeError, lambda: B.orient(N, 'Quaternion', q0))
    raises(TypeError, lambda: B.orient(N, 'Quaternion', [q0, q1, q2]))
    raises(NotImplementedError, lambda: B.orient(N, 'Foo', [q0, q1, q2]))
    raises(TypeError, lambda: B.orient(N, 'Body', [q1, q2], '232'))
    raises(TypeError, lambda: B.orient(N, 'Space', [q1, q2], '232'))

    N.set_ang_acc(B, 0)
    assert N.ang_acc_in(B) == Vector(0)
    N.set_ang_vel(B, 0)
    assert N.ang_vel_in(B) == Vector(0)


def test_check_frame():
    raises(VectorTypeError, lambda: _check_frame(0))
