import collections
import random

from sympy.assumptions import Q
from sympy.core.add import Add
from sympy.core.compatibility import range
from sympy.core.function import (Function, diff)
from sympy.core.numbers import (E, Float, I, Integer, oo, pi)
from sympy.core.relational import (Eq, Lt)
from sympy.core.singleton import S
from sympy.core.symbol import (Symbol, symbols)
from sympy.functions.elementary.complexes import Abs
from sympy.functions.elementary.exponential import exp
from sympy.functions.elementary.miscellaneous import (Max, Min, sqrt)
from sympy.functions.elementary.piecewise import Piecewise
from sympy.functions.elementary.trigonometric import (cos, sin, tan)
from sympy.logic.boolalg import (And, Or)
from sympy.matrices.common import (ShapeError, MatrixError, NonSquareMatrixError,
    _MinimalMatrix, MatrixShaping, MatrixProperties, MatrixOperations, MatrixArithmetic,
    MatrixSpecial)
from sympy.matrices.matrices import (MatrixDeterminant,
    MatrixReductions, MatrixSubspaces, MatrixEigen, MatrixCalculus)
from sympy.matrices import (Matrix, diag, eye,
    matrix_multiply_elementwise, ones, zeros)
from sympy.polys.polytools import Poly
from sympy.simplify.simplify import simplify
from sympy.simplify.trigsimp import trigsimp
from sympy.utilities.iterables import flatten
from sympy.utilities.pytest import (raises, XFAIL, slow, skip,
    warns_deprecated_sympy)

from sympy.abc import a, b, c, d, x, y, z

# classes to test the basic matrix classes
class ShapingOnlyMatrix(_MinimalMatrix, MatrixShaping):
    pass


def eye_Shaping(n):
    return ShapingOnlyMatrix(n, n, lambda i, j: int(i == j))


def zeros_Shaping(n):
    return ShapingOnlyMatrix(n, n, lambda i, j: 0)


class PropertiesOnlyMatrix(_MinimalMatrix, MatrixProperties):
    pass


def eye_Properties(n):
    return PropertiesOnlyMatrix(n, n, lambda i, j: int(i == j))


def zeros_Properties(n):
    return PropertiesOnlyMatrix(n, n, lambda i, j: 0)


class OperationsOnlyMatrix(_MinimalMatrix, MatrixOperations):
    pass


def eye_Operations(n):
    return OperationsOnlyMatrix(n, n, lambda i, j: int(i == j))


def zeros_Operations(n):
    return OperationsOnlyMatrix(n, n, lambda i, j: 0)


class ArithmeticOnlyMatrix(_MinimalMatrix, MatrixArithmetic):
    pass


def eye_Arithmetic(n):
    return ArithmeticOnlyMatrix(n, n, lambda i, j: int(i == j))


def zeros_Arithmetic(n):
    return ArithmeticOnlyMatrix(n, n, lambda i, j: 0)


class DeterminantOnlyMatrix(_MinimalMatrix, MatrixDeterminant):
    pass


def eye_Determinant(n):
    return DeterminantOnlyMatrix(n, n, lambda i, j: int(i == j))


def zeros_Determinant(n):
    return DeterminantOnlyMatrix(n, n, lambda i, j: 0)


class ReductionsOnlyMatrix(_MinimalMatrix, MatrixReductions):
    pass


def eye_Reductions(n):
    return ReductionsOnlyMatrix(n, n, lambda i, j: int(i == j))


def zeros_Reductions(n):
    return ReductionsOnlyMatrix(n, n, lambda i, j: 0)


class SpecialOnlyMatrix(_MinimalMatrix, MatrixSpecial):
    pass


class SubspaceOnlyMatrix(_MinimalMatrix, MatrixSubspaces):
    pass


class EigenOnlyMatrix(_MinimalMatrix, MatrixEigen):
    pass


class CalculusOnlyMatrix(_MinimalMatrix, MatrixCalculus):
    pass


def test__MinimalMatrix():
    x = _MinimalMatrix(2, 3, [1, 2, 3, 4, 5, 6])
    assert x.rows == 2
    assert x.cols == 3
    assert x[2] == 3
    assert x[1, 1] == 5
    assert list(x) == [1, 2, 3, 4, 5, 6]
    assert list(x[1, :]) == [4, 5, 6]
    assert list(x[:, 1]) == [2, 5]
    assert list(x[:, :]) == list(x)
    assert x[:, :] == x
    assert _MinimalMatrix(x) == x
    assert _MinimalMatrix([[1, 2, 3], [4, 5, 6]]) == x
    assert _MinimalMatrix(([1, 2, 3], [4, 5, 6])) == x
    assert _MinimalMatrix([(1, 2, 3), (4, 5, 6)]) == x
    assert _MinimalMatrix(((1, 2, 3), (4, 5, 6))) == x
    assert not (_MinimalMatrix([[1, 2], [3, 4], [5, 6]]) == x)


# ShapingOnlyMatrix tests
def test_vec():
    m = ShapingOnlyMatrix(2, 2, [1, 3, 2, 4])
    m_vec = m.vec()
    assert m_vec.cols == 1
    for i in range(4):
        assert m_vec[i] == i + 1


def test_tolist():
    lst = [[S.One, S.Half, x*y, S.Zero], [x, y, z, x**2], [y, -S.One, z*x, 3]]
    flat_lst = [S.One, S.Half, x*y, S.Zero, x, y, z, x**2, y, -S.One, z*x, 3]
    m = ShapingOnlyMatrix(3, 4, flat_lst)
    assert m.tolist() == lst


def test_row_col_del():
    e = ShapingOnlyMatrix(3, 3, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    raises(ValueError, lambda: e.row_del(5))
    raises(ValueError, lambda: e.row_del(-5))
    raises(ValueError, lambda: e.col_del(5))
    raises(ValueError, lambda: e.col_del(-5))

    assert e.row_del(2) == e.row_del(-1) == Matrix([[1, 2, 3], [4, 5, 6]])
    assert e.col_del(2) == e.col_del(-1) == Matrix([[1, 2], [4, 5], [7, 8]])

    assert e.row_del(1) == e.row_del(-2) == Matrix([[1, 2, 3], [7, 8, 9]])
    assert e.col_del(1) == e.col_del(-2) == Matrix([[1, 3], [4, 6], [7, 9]])


def test_get_diag_blocks1():
    a = Matrix([[1, 2], [2, 3]])
    b = Matrix([[3, x], [y, 3]])
    c = Matrix([[3, x, 3], [y, 3, z], [x, y, z]])
    assert a.get_diag_blocks() == [a]
    assert b.get_diag_blocks() == [b]
    assert c.get_diag_blocks() == [c]


def test_get_diag_blocks2():
    a = Matrix([[1, 2], [2, 3]])
    b = Matrix([[3, x], [y, 3]])
    c = Matrix([[3, x, 3], [y, 3, z], [x, y, z]])
    A, B, C, D = diag(a, b, b), diag(a, b, c), diag(a, c, b), diag(c, c, b)
    A = ShapingOnlyMatrix(A.rows, A.cols, A)
    B = ShapingOnlyMatrix(B.rows, B.cols, B)
    C = ShapingOnlyMatrix(C.rows, C.cols, C)
    D = ShapingOnlyMatrix(D.rows, D.cols, D)

    assert A.get_diag_blocks() == [a, b, b]
    assert B.get_diag_blocks() == [a, b, c]
    assert C.get_diag_blocks() == [a, c, b]
    assert D.get_diag_blocks() == [c, c, b]


def test_shape():
    m = ShapingOnlyMatrix(1, 2, [0, 0])
    m.shape == (1, 2)


def test_reshape():
    m0 = eye_Shaping(3)
    assert m0.reshape(1, 9) == Matrix(1, 9, (1, 0, 0, 0, 1, 0, 0, 0, 1))
    m1 = ShapingOnlyMatrix(3, 4, lambda i, j: i + j)
    assert m1.reshape(
        4, 3) == Matrix(((0, 1, 2), (3, 1, 2), (3, 4, 2), (3, 4, 5)))
    assert m1.reshape(2, 6) == Matrix(((0, 1, 2, 3, 1, 2), (3, 4, 2, 3, 4, 5)))


def test_row_col():
    m = ShapingOnlyMatrix(3, 3, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert m.row(0) == Matrix(1, 3, [1, 2, 3])
    assert m.col(0) == Matrix(3, 1, [1, 4, 7])


def test_row_join():
    assert eye_Shaping(3).row_join(Matrix([7, 7, 7])) == \
           Matrix([[1, 0, 0, 7],
                   [0, 1, 0, 7],
                   [0, 0, 1, 7]])


def test_col_join():
    assert eye_Shaping(3).col_join(Matrix([[7, 7, 7]])) == \
           Matrix([[1, 0, 0],
                   [0, 1, 0],
                   [0, 0, 1],
                   [7, 7, 7]])


def test_row_insert():
    r4 = Matrix([[4, 4, 4]])
    for i in range(-4, 5):
        l = [1, 0, 0]
        l.insert(i, 4)
        assert flatten(eye_Shaping(3).row_insert(i, r4).col(0).tolist()) == l


def test_col_insert():
    c4 = Matrix([4, 4, 4])
    for i in range(-4, 5):
        l = [0, 0, 0]
        l.insert(i, 4)
        assert flatten(zeros_Shaping(3).col_insert(i, c4).row(0).tolist()) == l
    # issue 13643
    assert eye_Shaping(6).col_insert(3, Matrix([[2, 2], [2, 2], [2, 2], [2, 2], [2, 2], [2, 2]])) == \
           Matrix([[1, 0, 0, 2, 2, 0, 0, 0],
                   [0, 1, 0, 2, 2, 0, 0, 0],
                   [0, 0, 1, 2, 2, 0, 0, 0],
                   [0, 0, 0, 2, 2, 1, 0, 0],
                   [0, 0, 0, 2, 2, 0, 1, 0],
                   [0, 0, 0, 2, 2, 0, 0, 1]])


def test_extract():
    m = ShapingOnlyMatrix(4, 3, lambda i, j: i*3 + j)
    assert m.extract([0, 1, 3], [0, 1]) == Matrix(3, 2, [0, 1, 3, 4, 9, 10])
    assert m.extract([0, 3], [0, 0, 2]) == Matrix(2, 3, [0, 0, 2, 9, 9, 11])
    assert m.extract(range(4), range(3)) == m
    raises(IndexError, lambda: m.extract([4], [0]))
    raises(IndexError, lambda: m.extract([0], [3]))


def test_hstack():
    m = ShapingOnlyMatrix(4, 3, lambda i, j: i*3 + j)
    m2 = ShapingOnlyMatrix(3, 4, lambda i, j: i*3 + j)
    assert m == m.hstack(m)
    assert m.hstack(m, m, m) == ShapingOnlyMatrix.hstack(m, m, m) == Matrix([
                [0,  1,  2, 0,  1,  2, 0,  1,  2],
                [3,  4,  5, 3,  4,  5, 3,  4,  5],
                [6,  7,  8, 6,  7,  8, 6,  7,  8],
                [9, 10, 11, 9, 10, 11, 9, 10, 11]])
    raises(ShapeError, lambda: m.hstack(m, m2))
    assert Matrix.hstack() == Matrix()

    # test regression #12938
    M1 = Matrix.zeros(0, 0)
    M2 = Matrix.zeros(0, 1)
    M3 = Matrix.zeros(0, 2)
    M4 = Matrix.zeros(0, 3)
    m = ShapingOnlyMatrix.hstack(M1, M2, M3, M4)
    assert m.rows == 0 and m.cols == 6


def test_vstack():
    m = ShapingOnlyMatrix(4, 3, lambda i, j: i*3 + j)
    m2 = ShapingOnlyMatrix(3, 4, lambda i, j: i*3 + j)
    assert m == m.vstack(m)
    assert m.vstack(m, m, m) == ShapingOnlyMatrix.vstack(m, m, m) == Matrix([
                                [0,  1,  2],
                                [3,  4,  5],
                                [6,  7,  8],
                                [9, 10, 11],
                                [0,  1,  2],
                                [3,  4,  5],
                                [6,  7,  8],
                                [9, 10, 11],
                                [0,  1,  2],
                                [3,  4,  5],
                                [6,  7,  8],
                                [9, 10, 11]])
    raises(ShapeError, lambda: m.vstack(m, m2))
    assert Matrix.vstack() == Matrix()


# PropertiesOnlyMatrix tests
def test_atoms():
    m = PropertiesOnlyMatrix(2, 2, [1, 2, x, 1 - 1/x])
    assert m.atoms() == {S(1),S(2),S(-1), x}
    assert m.atoms(Symbol) == {x}


def test_free_symbols():
    assert PropertiesOnlyMatrix([[x], [0]]).free_symbols == {x}


def test_has():
    A = PropertiesOnlyMatrix(((x, y), (2, 3)))
    assert A.has(x)
    assert not A.has(z)
    assert A.has(Symbol)

    A = PropertiesOnlyMatrix(((2, y), (2, 3)))
    assert not A.has(x)


def test_is_anti_symmetric():
    x = symbols('x')
    assert PropertiesOnlyMatrix(2, 1, [1, 2]).is_anti_symmetric() is False
    m = PropertiesOnlyMatrix(3, 3, [0, x**2 + 2*x + 1, y, -(x + 1)**2, 0, x*y, -y, -x*y, 0])
    assert m.is_anti_symmetric() is True
    assert m.is_anti_symmetric(simplify=False) is False
    assert m.is_anti_symmetric(simplify=lambda x: x) is False

    m = PropertiesOnlyMatrix(3, 3, [x.expand() for x in m])
    assert m.is_anti_symmetric(simplify=False) is True
    m = PropertiesOnlyMatrix(3, 3, [x.expand() for x in [S.One] + list(m)[1:]])
    assert m.is_anti_symmetric() is False


def test_diagonal_symmetrical():
    m = PropertiesOnlyMatrix(2, 2, [0, 1, 1, 0])
    assert not m.is_diagonal()
    assert m.is_symmetric()
    assert m.is_symmetric(simplify=False)

    m = PropertiesOnlyMatrix(2, 2, [1, 0, 0, 1])
    assert m.is_diagonal()

    m = PropertiesOnlyMatrix(3, 3, diag(1, 2, 3))
    assert m.is_diagonal()
    assert m.is_symmetric()

    m = PropertiesOnlyMatrix(3, 3, [1, 0, 0, 0, 2, 0, 0, 0, 3])
    assert m == diag(1, 2, 3)

    m = PropertiesOnlyMatrix(2, 3, zeros(2, 3))
    assert not m.is_symmetric()
    assert m.is_diagonal()

    m = PropertiesOnlyMatrix(((5, 0), (0, 6), (0, 0)))
    assert m.is_diagonal()

    m = PropertiesOnlyMatrix(((5, 0, 0), (0, 6, 0)))
    assert m.is_diagonal()

    m = Matrix(3, 3, [1, x**2 + 2*x + 1, y, (x + 1)**2, 2, 0, y, 0, 3])
    assert m.is_symmetric()
    assert not m.is_symmetric(simplify=False)
    assert m.expand().is_symmetric(simplify=False)


def test_is_hermitian():
    a = PropertiesOnlyMatrix([[1, I], [-I, 1]])
    assert a.is_hermitian
    a = PropertiesOnlyMatrix([[2*I, I], [-I, 1]])
    assert a.is_hermitian is False
    a = PropertiesOnlyMatrix([[x, I], [-I, 1]])
    assert a.is_hermitian is None
    a = PropertiesOnlyMatrix([[x, 1], [-I, 1]])
    assert a.is_hermitian is False


def test_is_Identity():
    assert eye_Properties(3).is_Identity
    assert not PropertiesOnlyMatrix(zeros(3)).is_Identity
    assert not PropertiesOnlyMatrix(ones(3)).is_Identity
    # issue 6242
    assert not PropertiesOnlyMatrix([[1, 0, 0]]).is_Identity


def test_is_symbolic():
    a = PropertiesOnlyMatrix([[x, x], [x, x]])
    assert a.is_symbolic() is True
    a = PropertiesOnlyMatrix([[1, 2, 3, 4], [5, 6, 7, 8]])
    assert a.is_symbolic() is False
    a = PropertiesOnlyMatrix([[1, 2, 3, 4], [5, 6, x, 8]])
    assert a.is_symbolic() is True
    a = PropertiesOnlyMatrix([[1, x, 3]])
    assert a.is_symbolic() is True
    a = PropertiesOnlyMatrix([[1, 2, 3]])
    assert a.is_symbolic() is False
    a = PropertiesOnlyMatrix([[1], [x], [3]])
    assert a.is_symbolic() is True
    a = PropertiesOnlyMatrix([[1], [2], [3]])
    assert a.is_symbolic() is False


def test_is_upper():
    a = PropertiesOnlyMatrix([[1, 2, 3]])
    assert a.is_upper is True
    a = PropertiesOnlyMatrix([[1], [2], [3]])
    assert a.is_upper is False


def test_is_lower():
    a = PropertiesOnlyMatrix([[1, 2, 3]])
    assert a.is_lower is False
    a = PropertiesOnlyMatrix([[1], [2], [3]])
    assert a.is_lower is True


def test_is_square():
    m = PropertiesOnlyMatrix([[1],[1]])
    m2 = PropertiesOnlyMatrix([[2,2],[2,2]])
    assert not m.is_square
    assert m2.is_square


def test_is_symmetric():
    m = PropertiesOnlyMatrix(2, 2, [0, 1, 1, 0])
    assert m.is_symmetric()
    m = PropertiesOnlyMatrix(2, 2, [0, 1, 0, 1])
    assert not m.is_symmetric()


def test_is_hessenberg():
    A = PropertiesOnlyMatrix([[3, 4, 1], [2, 4, 5], [0, 1, 2]])
    assert A.is_upper_hessenberg
    A = PropertiesOnlyMatrix(3, 3, [3, 2, 0, 4, 4, 1, 1, 5, 2])
    assert A.is_lower_hessenberg
    A = PropertiesOnlyMatrix(3, 3, [3, 2, -1, 4, 4, 1, 1, 5, 2])
    assert A.is_lower_hessenberg is False
    assert A.is_upper_hessenberg is False

    A = PropertiesOnlyMatrix([[3, 4, 1], [2, 4, 5], [3, 1, 2]])
    assert not A.is_upper_hessenberg


def test_is_zero():
    assert PropertiesOnlyMatrix(0, 0, []).is_zero
    assert PropertiesOnlyMatrix([[0, 0], [0, 0]]).is_zero
    assert PropertiesOnlyMatrix(zeros(3, 4)).is_zero
    assert not PropertiesOnlyMatrix(eye(3)).is_zero
    assert PropertiesOnlyMatrix([[x, 0], [0, 0]]).is_zero == None
    assert PropertiesOnlyMatrix([[x, 1], [0, 0]]).is_zero == False
    a = Symbol('a', nonzero=True)
    assert PropertiesOnlyMatrix([[a, 0], [0, 0]]).is_zero == False


def test_values():
    assert set(PropertiesOnlyMatrix(2,2,[0,1,2,3]).values()) == set([1,2,3])
    x = Symbol('x', real=True)
    assert set(PropertiesOnlyMatrix(2,2,[x,0,0,1]).values()) == set([x,1])


# OperationsOnlyMatrix tests
def test_applyfunc():
    m0 = OperationsOnlyMatrix(eye(3))
    assert m0.applyfunc(lambda x: 2*x) == eye(3)*2
    assert m0.applyfunc(lambda x: 0) == zeros(3)
    assert m0.applyfunc(lambda x: 1) == ones(3)


def test_adjoint():
    dat = [[0, I], [1, 0]]
    ans = OperationsOnlyMatrix([[0, 1], [-I, 0]])
    assert ans.adjoint() == Matrix(dat)


def test_as_real_imag():
    m1 = OperationsOnlyMatrix(2,2,[1,2,3,4])
    m3 = OperationsOnlyMatrix(2,2,[1+S.ImaginaryUnit,2+2*S.ImaginaryUnit,3+3*S.ImaginaryUnit,4+4*S.ImaginaryUnit])

    a,b = m3.as_real_imag()
    assert a == m1
    assert b == m1


def test_conjugate():
    M = OperationsOnlyMatrix([[0, I, 5],
                [1, 2, 0]])

    assert M.T == Matrix([[0, 1],
                          [I, 2],
                          [5, 0]])

    assert M.C == Matrix([[0, -I, 5],
                          [1,  2, 0]])
    assert M.C == M.conjugate()

    assert M.H == M.T.C
    assert M.H == Matrix([[ 0, 1],
                          [-I, 2],
                          [ 5, 0]])


def test_doit():
    a = OperationsOnlyMatrix([[Add(x,x, evaluate=False)]])
    assert a[0] != 2*x
    assert a.doit() == Matrix([[2*x]])


def test_evalf():
    a = OperationsOnlyMatrix(2, 1, [sqrt(5), 6])
    assert all(a.evalf()[i] == a[i].evalf() for i in range(2))
    assert all(a.evalf(2)[i] == a[i].evalf(2) for i in range(2))
    assert all(a.n(2)[i] == a[i].n(2) for i in range(2))


def test_expand():
    m0 = OperationsOnlyMatrix([[x*(x + y), 2], [((x + y)*y)*x, x*(y + x*(x + y))]])
    # Test if expand() returns a matrix
    m1 = m0.expand()
    assert m1 == Matrix(
        [[x*y + x**2, 2], [x*y**2 + y*x**2, x*y + y*x**2 + x**3]])

    a = Symbol('a', real=True)

    assert OperationsOnlyMatrix(1, 1, [exp(I*a)]).expand(complex=True) == \
           Matrix([cos(a) + I*sin(a)])


def test_refine():
    m0 = OperationsOnlyMatrix([[Abs(x)**2, sqrt(x**2)],
                 [sqrt(x**2)*Abs(y)**2, sqrt(y**2)*Abs(x)**2]])
    m1 = m0.refine(Q.real(x) & Q.real(y))
    assert m1 == Matrix([[x**2, Abs(x)], [y**2*Abs(x), x**2*Abs(y)]])

    m1 = m0.refine(Q.positive(x) & Q.positive(y))
    assert m1 == Matrix([[x**2, x], [x*y**2, x**2*y]])

    m1 = m0.refine(Q.negative(x) & Q.negative(y))
    assert m1 == Matrix([[x**2, -x], [-x*y**2, -x**2*y]])


def test_replace():
    F, G = symbols('F, G', cls=Function)
    K = OperationsOnlyMatrix(2, 2, lambda i, j: G(i+j))
    M = OperationsOnlyMatrix(2, 2, lambda i, j: F(i+j))
    N = M.replace(F, G)
    assert N == K


def test_replace_map():
    F, G = symbols('F, G', cls=Function)
    K = OperationsOnlyMatrix(2, 2, [(G(0), {F(0): G(0)}), (G(1), {F(1): G(1)}), (G(1), {F(1) \
                                                                              : G(1)}), (G(2), {F(2): G(2)})])
    M = OperationsOnlyMatrix(2, 2, lambda i, j: F(i+j))
    N = M.replace(F, G, True)
    assert N == K


def test_simplify():
    n = Symbol('n')
    f = Function('f')

    M = OperationsOnlyMatrix([[            1/x + 1/y,                 (x + x*y) / x  ],
                [ (f(x) + y*f(x))/f(x), 2 * (1/n - cos(n * pi)/n) / pi ]])
    assert M.simplify() == Matrix([[ (x + y)/(x * y),                        1 + y ],
                        [           1 + y, 2*((1 - 1*cos(pi*n))/(pi*n)) ]])
    eq = (1 + x)**2
    M = OperationsOnlyMatrix([[eq]])
    assert M.simplify() == Matrix([[eq]])
    assert M.simplify(ratio=oo) == Matrix([[eq.simplify(ratio=oo)]])


def test_subs():
    assert OperationsOnlyMatrix([[1, x], [x, 4]]).subs(x, 5) == Matrix([[1, 5], [5, 4]])
    assert OperationsOnlyMatrix([[x, 2], [x + y, 4]]).subs([[x, -1], [y, -2]]) == \
           Matrix([[-1, 2], [-3, 4]])
    assert OperationsOnlyMatrix([[x, 2], [x + y, 4]]).subs([(x, -1), (y, -2)]) == \
           Matrix([[-1, 2], [-3, 4]])
    assert OperationsOnlyMatrix([[x, 2], [x + y, 4]]).subs({x: -1, y: -2}) == \
           Matrix([[-1, 2], [-3, 4]])
    assert OperationsOnlyMatrix([[x*y]]).subs({x: y - 1, y: x - 1}, simultaneous=True) == \
           Matrix([[(x - 1)*(y - 1)]])


def test_trace():
    M = OperationsOnlyMatrix([[1, 0, 0],
                [0, 5, 0],
                [0, 0, 8]])
    assert M.trace() == 14


def test_xreplace():
    assert OperationsOnlyMatrix([[1, x], [x, 4]]).xreplace({x: 5}) == \
           Matrix([[1, 5], [5, 4]])
    assert OperationsOnlyMatrix([[x, 2], [x + y, 4]]).xreplace({x: -1, y: -2}) == \
           Matrix([[-1, 2], [-3, 4]])


def test_permute():
    a = OperationsOnlyMatrix(3, 4, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    raises(IndexError, lambda: a.permute([[0,5]]))
    b = a.permute_rows([[0, 2], [0, 1]])
    assert a.permute([[0, 2], [0, 1]]) == b == Matrix([
                                            [5,  6,  7,  8],
                                            [9, 10, 11, 12],
                                            [1,  2,  3,  4]])

    b = a.permute_cols([[0, 2], [0, 1]])
    assert a.permute([[0, 2], [0, 1]], orientation='cols') == b ==\
                            Matrix([
                            [ 2,  3, 1,  4],
                            [ 6,  7, 5,  8],
                            [10, 11, 9, 12]])

    b = a.permute_cols([[0, 2], [0, 1]], direction='backward')
    assert a.permute([[0, 2], [0, 1]], orientation='cols', direction='backward') == b ==\
                            Matrix([
                            [ 3, 1,  2,  4],
                            [ 7, 5,  6,  8],
                            [11, 9, 10, 12]])

    assert a.permute([1, 2, 0, 3]) == Matrix([
                                            [5,  6,  7,  8],
                                            [9, 10, 11, 12],
                                            [1,  2,  3,  4]])

    from sympy.combinatorics import Permutation
    assert a.permute(Permutation([1, 2, 0, 3])) == Matrix([
                                            [5,  6,  7,  8],
                                            [9, 10, 11, 12],
                                            [1,  2,  3,  4]])


# ArithmeticOnlyMatrix tests
def test_abs():
    m = ArithmeticOnlyMatrix([[1, -2], [x, y]])
    assert abs(m) == ArithmeticOnlyMatrix([[1, 2], [Abs(x), Abs(y)]])


def test_add():
    m = ArithmeticOnlyMatrix([[1, 2, 3], [x, y, x], [2*y, -50, z*x]])
    assert m + m == ArithmeticOnlyMatrix([[2, 4, 6], [2*x, 2*y, 2*x], [4*y, -100, 2*z*x]])
    n = ArithmeticOnlyMatrix(1, 2, [1, 2])
    raises(ShapeError, lambda: m + n)


def test_multiplication():
    a = ArithmeticOnlyMatrix((
        (1, 2),
        (3, 1),
        (0, 6),
    ))

    b = ArithmeticOnlyMatrix((
        (1, 2),
        (3, 0),
    ))

    raises(ShapeError, lambda: b*a)
    raises(TypeError, lambda: a*{})

    c = a*b
    assert c[0, 0] == 7
    assert c[0, 1] == 2
    assert c[1, 0] == 6
    assert c[1, 1] == 6
    assert c[2, 0] == 18
    assert c[2, 1] == 0

    try:
        eval('c = a @ b')
    except SyntaxError:
        pass
    else:
        assert c[0, 0] == 7
        assert c[0, 1] == 2
        assert c[1, 0] == 6
        assert c[1, 1] == 6
        assert c[2, 0] == 18
        assert c[2, 1] == 0

    h = a.multiply_elementwise(c)
    assert h == matrix_multiply_elementwise(a, c)
    assert h[0, 0] == 7
    assert h[0, 1] == 4
    assert h[1, 0] == 18
    assert h[1, 1] == 6
    assert h[2, 0] == 0
    assert h[2, 1] == 0
    raises(ShapeError, lambda: a.multiply_elementwise(b))

    c = b * Symbol("x")
    assert isinstance(c, ArithmeticOnlyMatrix)
    assert c[0, 0] == x
    assert c[0, 1] == 2*x
    assert c[1, 0] == 3*x
    assert c[1, 1] == 0

    c2 = x * b
    assert c == c2

    c = 5 * b
    assert isinstance(c, ArithmeticOnlyMatrix)
    assert c[0, 0] == 5
    assert c[0, 1] == 2*5
    assert c[1, 0] == 3*5
    assert c[1, 1] == 0

    try:
        eval('c = 5 @ b')
    except SyntaxError:
        pass
    else:
        assert isinstance(c, ArithmeticOnlyMatrix)
        assert c[0, 0] == 5
        assert c[0, 1] == 2*5
        assert c[1, 0] == 3*5
        assert c[1, 1] == 0


def test_matmul():
    a = Matrix([[1, 2], [3, 4]])

    assert a.__matmul__(2) == NotImplemented

    assert a.__rmatmul__(2) == NotImplemented

    #This is done this way because @ is only supported in Python 3.5+
    #To check 2@a case
    try:
        eval('2 @ a')
    except SyntaxError:
        pass
    except TypeError:  #TypeError is raised in case of NotImplemented is returned
        pass

    #Check a@2 case
    try:
        eval('a @ 2')
    except SyntaxError:
        pass
    except TypeError:  #TypeError is raised in case of NotImplemented is returned
        pass


def test_power():
    raises(NonSquareMatrixError, lambda: Matrix((1, 2))**2)

    A = ArithmeticOnlyMatrix([[2, 3], [4, 5]])
    assert (A**5)[:] == (6140, 8097, 10796, 14237)
    A = ArithmeticOnlyMatrix([[2, 1, 3], [4, 2, 4], [6, 12, 1]])
    assert (A**3)[:] == (290, 262, 251, 448, 440, 368, 702, 954, 433)
    assert A**0 == eye(3)
    assert A**1 == A
    assert (ArithmeticOnlyMatrix([[2]]) ** 100)[0, 0] == 2**100
    assert ArithmeticOnlyMatrix([[1, 2], [3, 4]])**Integer(2) == ArithmeticOnlyMatrix([[7, 10], [15, 22]])


def test_neg():
    n = ArithmeticOnlyMatrix(1, 2, [1, 2])
    assert -n == ArithmeticOnlyMatrix(1, 2, [-1, -2])


def test_sub():
    n = ArithmeticOnlyMatrix(1, 2, [1, 2])
    assert n - n == ArithmeticOnlyMatrix(1, 2, [0, 0])


def test_div():
    n = ArithmeticOnlyMatrix(1, 2, [1, 2])
    assert n/2 == ArithmeticOnlyMatrix(1, 2, [S(1)/2, S(2)/2])


# DeterminantOnlyMatrix tests
def test_det():
    a = DeterminantOnlyMatrix(2,3,[1,2,3,4,5,6])
    raises(NonSquareMatrixError, lambda: a.det())

    z = zeros_Determinant(2)
    ey = eye_Determinant(2)
    assert z.det() == 0
    assert ey.det() == 1

    x = Symbol('x')
    a = DeterminantOnlyMatrix(0,0,[])
    b = DeterminantOnlyMatrix(1,1,[5])
    c = DeterminantOnlyMatrix(2,2,[1,2,3,4])
    d = DeterminantOnlyMatrix(3,3,[1,2,3,4,5,6,7,8,8])
    e = DeterminantOnlyMatrix(4,4,[x,1,2,3,4,5,6,7,2,9,10,11,12,13,14,14])

    # the method keyword for `det` doesn't kick in until 4x4 matrices,
    # so there is no need to test all methods on smaller ones

    assert a.det() == 1
    assert b.det() == 5
    assert c.det() == -2
    assert d.det() == 3
    assert e.det() == 4*x - 24
    assert e.det(method='bareiss') == 4*x - 24
    assert e.det(method='berkowitz') == 4*x - 24
    raises(ValueError, lambda: e.det(iszerofunc="test"))


def test_adjugate():
    x = Symbol('x')
    e = DeterminantOnlyMatrix(4,4,[x,1,2,3,4,5,6,7,2,9,10,11,12,13,14,14])

    adj = Matrix([
        [   4,         -8,         4,         0],
        [  76, -14*x - 68,  14*x - 8, -4*x + 24],
        [-122, 17*x + 142, -21*x + 4,  8*x - 48],
        [  48,  -4*x - 72,       8*x, -4*x + 24]])
    assert e.adjugate() == adj
    assert e.adjugate(method='bareiss') == adj
    assert e.adjugate(method='berkowitz') == adj

    a = DeterminantOnlyMatrix(2,3,[1,2,3,4,5,6])
    raises(NonSquareMatrixError, lambda: a.adjugate())


def test_cofactor_and_minors():
    x = Symbol('x')
    e = DeterminantOnlyMatrix(4,4,[x,1,2,3,4,5,6,7,2,9,10,11,12,13,14,14])

    m = Matrix([
        [ x,  1,  3],
        [ 2,  9, 11],
        [12, 13, 14]])
    cm = Matrix([
        [ 4,         76,       -122,        48],
        [-8, -14*x - 68, 17*x + 142, -4*x - 72],
        [ 4,   14*x - 8,  -21*x + 4,       8*x],
        [ 0,  -4*x + 24,   8*x - 48, -4*x + 24]])
    sub = Matrix([
            [x, 1,  2],
            [4, 5,  6],
            [2, 9, 10]])

    assert e.minor_submatrix(1,2) == m
    assert e.minor_submatrix(-1,-1) == sub
    assert e.minor(1,2) == -17*x - 142
    assert e.cofactor(1,2) == 17*x + 142
    assert e.cofactor_matrix() == cm
    assert e.cofactor_matrix(method="bareiss") == cm
    assert e.cofactor_matrix(method="berkowitz") == cm

    raises(ValueError, lambda: e.cofactor(4,5))
    raises(ValueError, lambda: e.minor(4,5))
    raises(ValueError, lambda: e.minor_submatrix(4,5))

    a = DeterminantOnlyMatrix(2,3,[1,2,3,4,5,6])
    assert a.minor_submatrix(0,0) == Matrix([[5, 6]])

    raises(ValueError, lambda: DeterminantOnlyMatrix(0,0,[]).minor_submatrix(0,0))
    raises(NonSquareMatrixError, lambda: a.cofactor(0,0))
    raises(NonSquareMatrixError, lambda: a.minor(0,0))
    raises(NonSquareMatrixError, lambda: a.cofactor_matrix())


def test_charpoly():
    x, y = Symbol('x'), Symbol('y')

    m = DeterminantOnlyMatrix(3,3,[1,2,3,4,5,6,7,8,9])

    assert eye_Determinant(3).charpoly(x) == Poly((x - 1)**3, x)
    assert eye_Determinant(3).charpoly(y) == Poly((y - 1)**3, y)
    assert m.charpoly() == Poly(x**3 - 15*x**2 - 18*x, x)
    raises(NonSquareMatrixError, lambda: Matrix([[1], [2]]).charpoly())

# ReductionsOnlyMatrix tests
def test_row_op():
    e = eye_Reductions(3)

    raises(ValueError, lambda: e.elementary_row_op("abc"))
    raises(ValueError, lambda: e.elementary_row_op())
    raises(ValueError, lambda: e.elementary_row_op('n->kn', row=5, k=5))
    raises(ValueError, lambda: e.elementary_row_op('n->kn', row=-5, k=5))
    raises(ValueError, lambda: e.elementary_row_op('n<->m', row1=1, row2=5))
    raises(ValueError, lambda: e.elementary_row_op('n<->m', row1=5, row2=1))
    raises(ValueError, lambda: e.elementary_row_op('n<->m', row1=-5, row2=1))
    raises(ValueError, lambda: e.elementary_row_op('n<->m', row1=1, row2=-5))
    raises(ValueError, lambda: e.elementary_row_op('n->n+km', row1=1, row2=5, k=5))
    raises(ValueError, lambda: e.elementary_row_op('n->n+km', row1=5, row2=1, k=5))
    raises(ValueError, lambda: e.elementary_row_op('n->n+km', row1=-5, row2=1, k=5))
    raises(ValueError, lambda: e.elementary_row_op('n->n+km', row1=1, row2=-5, k=5))
    raises(ValueError, lambda: e.elementary_row_op('n->n+km', row1=1, row2=1, k=5))

    # test various ways to set arguments
    assert e.elementary_row_op("n->kn", 0, 5) == Matrix([[5, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert e.elementary_row_op("n->kn", 1, 5) == Matrix([[1, 0, 0], [0, 5, 0], [0, 0, 1]])
    assert e.elementary_row_op("n->kn", row=1, k=5) == Matrix([[1, 0, 0], [0, 5, 0], [0, 0, 1]])
    assert e.elementary_row_op("n->kn", row1=1, k=5) == Matrix([[1, 0, 0], [0, 5, 0], [0, 0, 1]])
    assert e.elementary_row_op("n<->m", 0, 1) == Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    assert e.elementary_row_op("n<->m", row1=0, row2=1) == Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    assert e.elementary_row_op("n<->m", row=0, row2=1) == Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    assert e.elementary_row_op("n->n+km", 0, 5, 1) == Matrix([[1, 5, 0], [0, 1, 0], [0, 0, 1]])
    assert e.elementary_row_op("n->n+km", row=0, k=5, row2=1) == Matrix([[1, 5, 0], [0, 1, 0], [0, 0, 1]])
    assert e.elementary_row_op("n->n+km", row1=0, k=5, row2=1) == Matrix([[1, 5, 0], [0, 1, 0], [0, 0, 1]])

    # make sure the matrix doesn't change size
    a = ReductionsOnlyMatrix(2, 3, [0]*6)
    assert a.elementary_row_op("n->kn", 1, 5) == Matrix(2, 3, [0]*6)
    assert a.elementary_row_op("n<->m", 0, 1) == Matrix(2, 3, [0]*6)
    assert a.elementary_row_op("n->n+km", 0, 5, 1) == Matrix(2, 3, [0]*6)


def test_col_op():
    e = eye_Reductions(3)

    raises(ValueError, lambda: e.elementary_col_op("abc"))
    raises(ValueError, lambda: e.elementary_col_op())
    raises(ValueError, lambda: e.elementary_col_op('n->kn', col=5, k=5))
    raises(ValueError, lambda: e.elementary_col_op('n->kn', col=-5, k=5))
    raises(ValueError, lambda: e.elementary_col_op('n<->m', col1=1, col2=5))
    raises(ValueError, lambda: e.elementary_col_op('n<->m', col1=5, col2=1))
    raises(ValueError, lambda: e.elementary_col_op('n<->m', col1=-5, col2=1))
    raises(ValueError, lambda: e.elementary_col_op('n<->m', col1=1, col2=-5))
    raises(ValueError, lambda: e.elementary_col_op('n->n+km', col1=1, col2=5, k=5))
    raises(ValueError, lambda: e.elementary_col_op('n->n+km', col1=5, col2=1, k=5))
    raises(ValueError, lambda: e.elementary_col_op('n->n+km', col1=-5, col2=1, k=5))
    raises(ValueError, lambda: e.elementary_col_op('n->n+km', col1=1, col2=-5, k=5))
    raises(ValueError, lambda: e.elementary_col_op('n->n+km', col1=1, col2=1, k=5))

    # test various ways to set arguments
    assert e.elementary_col_op("n->kn", 0, 5) == Matrix([[5, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert e.elementary_col_op("n->kn", 1, 5) == Matrix([[1, 0, 0], [0, 5, 0], [0, 0, 1]])
    assert e.elementary_col_op("n->kn", col=1, k=5) == Matrix([[1, 0, 0], [0, 5, 0], [0, 0, 1]])
    assert e.elementary_col_op("n->kn", col1=1, k=5) == Matrix([[1, 0, 0], [0, 5, 0], [0, 0, 1]])
    assert e.elementary_col_op("n<->m", 0, 1) == Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    assert e.elementary_col_op("n<->m", col1=0, col2=1) == Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    assert e.elementary_col_op("n<->m", col=0, col2=1) == Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    assert e.elementary_col_op("n->n+km", 0, 5, 1) == Matrix([[1, 0, 0], [5, 1, 0], [0, 0, 1]])
    assert e.elementary_col_op("n->n+km", col=0, k=5, col2=1) == Matrix([[1, 0, 0], [5, 1, 0], [0, 0, 1]])
    assert e.elementary_col_op("n->n+km", col1=0, k=5, col2=1) == Matrix([[1, 0, 0], [5, 1, 0], [0, 0, 1]])

    # make sure the matrix doesn't change size
    a = ReductionsOnlyMatrix(2, 3, [0]*6)
    assert a.elementary_col_op("n->kn", 1, 5) == Matrix(2, 3, [0]*6)
    assert a.elementary_col_op("n<->m", 0, 1) == Matrix(2, 3, [0]*6)
    assert a.elementary_col_op("n->n+km", 0, 5, 1) == Matrix(2, 3, [0]*6)


def test_is_echelon():
    zro = zeros_Reductions(3)
    ident = eye_Reductions(3)

    assert zro.is_echelon
    assert ident.is_echelon

    a = ReductionsOnlyMatrix(0, 0, [])
    assert a.is_echelon

    a = ReductionsOnlyMatrix(2, 3, [3, 2, 1, 0, 0, 6])
    assert a.is_echelon

    a = ReductionsOnlyMatrix(2, 3, [0, 0, 6, 3, 2, 1])
    assert not a.is_echelon

    x = Symbol('x')
    a = ReductionsOnlyMatrix(3, 1, [x, 0, 0])
    assert a.is_echelon

    a = ReductionsOnlyMatrix(3, 1, [x, x, 0])
    assert not a.is_echelon

    a = ReductionsOnlyMatrix(3, 3, [0, 0, 0, 1, 2, 3, 0, 0, 0])
    assert not a.is_echelon


def test_echelon_form():
    # echelon form is not unique, but the result
    # must be row-equivalent to the original matrix
    # and it must be in echelon form.

    a = zeros_Reductions(3)
    e = eye_Reductions(3)

    # we can assume the zero matrix and the identity matrix shouldn't change
    assert a.echelon_form() == a
    assert e.echelon_form() == e

    a = ReductionsOnlyMatrix(0, 0, [])
    assert a.echelon_form() == a

    a = ReductionsOnlyMatrix(1, 1, [5])
    assert a.echelon_form() == a

    # now we get to the real tests

    def verify_row_null_space(mat, rows, nulls):
        for v in nulls:
            assert all(t.is_zero for t in a_echelon*v)
        for v in rows:
            if not all(t.is_zero for t in v):
                assert not all(t.is_zero for t in a_echelon*v.transpose())

    a = ReductionsOnlyMatrix(3, 3, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    nulls = [Matrix([
                     [ 1],
                     [-2],
                     [ 1]])]
    rows = [a[i,:] for i in range(a.rows)]
    a_echelon = a.echelon_form()
    assert a_echelon.is_echelon
    verify_row_null_space(a, rows, nulls)


    a = ReductionsOnlyMatrix(3, 3, [1, 2, 3, 4, 5, 6, 7, 8, 8])
    nulls = []
    rows = [a[i,:] for i in range(a.rows)]
    a_echelon = a.echelon_form()
    assert a_echelon.is_echelon
    verify_row_null_space(a, rows, nulls)

    a = ReductionsOnlyMatrix(3, 3, [2, 1, 3, 0, 0, 0, 2, 1, 3])
    nulls = [Matrix([
             [-S(1)/2],
             [   1],
             [   0]]),
             Matrix([
             [-S(3)/2],
             [   0],
             [   1]])]
    rows = [a[i,:] for i in range(a.rows)]
    a_echelon = a.echelon_form()
    assert a_echelon.is_echelon
    verify_row_null_space(a, rows, nulls)

    # this one requires a row swap
    a = ReductionsOnlyMatrix(3, 3, [2, 1, 3, 0, 0, 0, 1, 1, 3])
    nulls = [Matrix([
             [   0],
             [  -3],
             [   1]])]
    rows = [a[i,:] for i in range(a.rows)]
    a_echelon = a.echelon_form()
    assert a_echelon.is_echelon
    verify_row_null_space(a, rows, nulls)

    a = ReductionsOnlyMatrix(3, 3, [0, 3, 3, 0, 2, 2, 0, 1, 1])
    nulls = [Matrix([
             [1],
             [0],
             [0]]),
             Matrix([
             [ 0],
             [-1],
             [ 1]])]
    rows = [a[i,:] for i in range(a.rows)]
    a_echelon = a.echelon_form()
    assert a_echelon.is_echelon
    verify_row_null_space(a, rows, nulls)

    a = ReductionsOnlyMatrix(2, 3, [2, 2, 3, 3, 3, 0])
    nulls = [Matrix([
             [-1],
             [1],
             [0]])]
    rows = [a[i,:] for i in range(a.rows)]
    a_echelon = a.echelon_form()
    assert a_echelon.is_echelon
    verify_row_null_space(a, rows, nulls)


def test_rref():
    e = ReductionsOnlyMatrix(0, 0, [])
    assert e.rref(pivots=False) == e

    e = ReductionsOnlyMatrix(1, 1, [1])
    a = ReductionsOnlyMatrix(1, 1, [5])
    assert e.rref(pivots=False) == a.rref(pivots=False) == e

    a = ReductionsOnlyMatrix(3, 1, [1, 2, 3])
    assert a.rref(pivots=False) == Matrix([[1], [0], [0]])

    a = ReductionsOnlyMatrix(1, 3, [1, 2, 3])
    assert a.rref(pivots=False) == Matrix([[1, 2, 3]])

    a = ReductionsOnlyMatrix(3, 3, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert a.rref(pivots=False) == Matrix([
                                     [1, 0, -1],
                                     [0, 1,  2],
                                     [0, 0,  0]])

    a = ReductionsOnlyMatrix(3, 3, [1, 2, 3, 1, 2, 3, 1, 2, 3])
    b = ReductionsOnlyMatrix(3, 3, [1, 2, 3, 0, 0, 0, 0, 0, 0])
    c = ReductionsOnlyMatrix(3, 3, [0, 0, 0, 1, 2, 3, 0, 0, 0])
    d = ReductionsOnlyMatrix(3, 3, [0, 0, 0, 0, 0, 0, 1, 2, 3])
    assert a.rref(pivots=False) == \
            b.rref(pivots=False) == \
            c.rref(pivots=False) == \
            d.rref(pivots=False) == b

    e = eye_Reductions(3)
    z = zeros_Reductions(3)
    assert e.rref(pivots=False) == e
    assert z.rref(pivots=False) == z

    a = ReductionsOnlyMatrix([
            [ 0, 0,  1,  2,  2, -5,  3],
            [-1, 5,  2,  2,  1, -7,  5],
            [ 0, 0, -2, -3, -3,  8, -5],
            [-1, 5,  0, -1, -2,  1,  0]])
    mat, pivot_offsets = a.rref()
    assert mat == Matrix([
                     [1, -5, 0, 0, 1,  1, -1],
                     [0,  0, 1, 0, 0, -1,  1],
                     [0,  0, 0, 1, 1, -2,  1],
                     [0,  0, 0, 0, 0,  0,  0]])
    assert pivot_offsets == (0, 2, 3)

    a = ReductionsOnlyMatrix([[S(1)/19,  S(1)/5,    2,    3],
                        [   4,    5,    6,    7],
                        [   8,    9,   10,   11],
                        [  12,   13,   14,   15]])
    assert a.rref(pivots=False) == Matrix([
                                         [1, 0, 0, -S(76)/157],
                                         [0, 1, 0,  -S(5)/157],
                                         [0, 0, 1, S(238)/157],
                                         [0, 0, 0,       0]])

    x = Symbol('x')
    a = ReductionsOnlyMatrix(2, 3, [x, 1, 1, sqrt(x), x, 1])
    for i, j in zip(a.rref(pivots=False),
            [1, 0, sqrt(x)*(-x + 1)/(-x**(S(5)/2) + x),
                0, 1, 1/(sqrt(x) + x + 1)]):
        assert simplify(i - j).is_zero


# SpecialOnlyMatrix tests
def test_eye():
    assert list(SpecialOnlyMatrix.eye(2,2)) == [1, 0, 0, 1]
    assert list(SpecialOnlyMatrix.eye(2)) == [1, 0, 0, 1]
    assert type(SpecialOnlyMatrix.eye(2)) == SpecialOnlyMatrix
    assert type(SpecialOnlyMatrix.eye(2, cls=Matrix)) == Matrix


def test_ones():
    assert list(SpecialOnlyMatrix.ones(2,2)) == [1, 1, 1, 1]
    assert list(SpecialOnlyMatrix.ones(2)) == [1, 1, 1, 1]
    assert SpecialOnlyMatrix.ones(2,3) == Matrix([[1, 1, 1], [1, 1, 1]])
    assert type(SpecialOnlyMatrix.ones(2)) == SpecialOnlyMatrix
    assert type(SpecialOnlyMatrix.ones(2, cls=Matrix)) == Matrix


def test_zeros():
    assert list(SpecialOnlyMatrix.zeros(2,2)) == [0, 0, 0, 0]
    assert list(SpecialOnlyMatrix.zeros(2)) == [0, 0, 0, 0]
    assert SpecialOnlyMatrix.zeros(2,3) == Matrix([[0, 0, 0], [0, 0, 0]])
    assert type(SpecialOnlyMatrix.zeros(2)) == SpecialOnlyMatrix
    assert type(SpecialOnlyMatrix.zeros(2, cls=Matrix)) == Matrix


def test_diag_make():
    diag = SpecialOnlyMatrix.diag
    a = Matrix([[1, 2], [2, 3]])
    b = Matrix([[3, x], [y, 3]])
    c = Matrix([[3, x, 3], [y, 3, z], [x, y, z]])
    assert diag(a, b, b) == Matrix([
        [1, 2, 0, 0, 0, 0],
        [2, 3, 0, 0, 0, 0],
        [0, 0, 3, x, 0, 0],
        [0, 0, y, 3, 0, 0],
        [0, 0, 0, 0, 3, x],
        [0, 0, 0, 0, y, 3],
    ])
    assert diag(a, b, c) == Matrix([
        [1, 2, 0, 0, 0, 0, 0],
        [2, 3, 0, 0, 0, 0, 0],
        [0, 0, 3, x, 0, 0, 0],
        [0, 0, y, 3, 0, 0, 0],
        [0, 0, 0, 0, 3, x, 3],
        [0, 0, 0, 0, y, 3, z],
        [0, 0, 0, 0, x, y, z],
    ])
    assert diag(a, c, b) == Matrix([
        [1, 2, 0, 0, 0, 0, 0],
        [2, 3, 0, 0, 0, 0, 0],
        [0, 0, 3, x, 3, 0, 0],
        [0, 0, y, 3, z, 0, 0],
        [0, 0, x, y, z, 0, 0],
        [0, 0, 0, 0, 0, 3, x],
        [0, 0, 0, 0, 0, y, 3],
    ])
    a = Matrix([x, y, z])
    b = Matrix([[1, 2], [3, 4]])
    c = Matrix([[5, 6]])
    assert diag(a, 7, b, c) == Matrix([
        [x, 0, 0, 0, 0, 0],
        [y, 0, 0, 0, 0, 0],
        [z, 0, 0, 0, 0, 0],
        [0, 7, 0, 0, 0, 0],
        [0, 0, 1, 2, 0, 0],
        [0, 0, 3, 4, 0, 0],
        [0, 0, 0, 0, 5, 6],
    ])
    assert SpecialOnlyMatrix.diag([2, 3]) == Matrix([
        [2, 0],
        [0, 3]])
    assert SpecialOnlyMatrix.diag(Matrix([2, 3])) == Matrix([
        [2],
        [3]])
    assert SpecialOnlyMatrix.diag(1, rows=3, cols=2) == Matrix([
        [1, 0],
        [0, 0],
        [0, 0]])
    assert type(SpecialOnlyMatrix.diag(1)) == SpecialOnlyMatrix
    assert type(SpecialOnlyMatrix.diag(1, cls=Matrix)) == Matrix

def test_jordan_block():
    assert SpecialOnlyMatrix.jordan_block(3, 2) == SpecialOnlyMatrix.jordan_block(3, eigenvalue=2) \
            == SpecialOnlyMatrix.jordan_block(size=3, eigenvalue=2) \
            == SpecialOnlyMatrix.jordan_block(3, 2, band='upper') \
            == SpecialOnlyMatrix.jordan_block(
                size=3, eigenval=2, eigenvalue=2) \
            == Matrix([
                [2, 1, 0],
                [0, 2, 1],
                [0, 0, 2]])

    assert SpecialOnlyMatrix.jordan_block(3, 2, band='lower') == Matrix([
                    [2, 0, 0],
                    [1, 2, 0],
                    [0, 1, 2]])
    # missing eigenvalue
    raises(ValueError, lambda: SpecialOnlyMatrix.jordan_block(2))
    # non-integral size
    raises(ValueError, lambda: SpecialOnlyMatrix.jordan_block(3.5, 2))
    # size not specified
    raises(ValueError, lambda: SpecialOnlyMatrix.jordan_block(eigenvalue=2))
    # inconsistent eigenvalue
    raises(ValueError,
    lambda: SpecialOnlyMatrix.jordan_block(
        eigenvalue=2, eigenval=4))

    # Deprecated feature
    with warns_deprecated_sympy():
        assert (SpecialOnlyMatrix.jordan_block(cols=3, eigenvalue=2) ==
                SpecialOnlyMatrix(3, 3, (2, 1, 0, 0, 2, 1, 0, 0, 2)))

    with warns_deprecated_sympy():
        assert (SpecialOnlyMatrix.jordan_block(rows=3, eigenvalue=2) ==
                SpecialOnlyMatrix(3, 3, (2, 1, 0, 0, 2, 1, 0, 0, 2)))

    with warns_deprecated_sympy():
        assert SpecialOnlyMatrix.jordan_block(3, 2) == \
            SpecialOnlyMatrix.jordan_block(cols=3, eigenvalue=2) == \
            SpecialOnlyMatrix.jordan_block(rows=3, eigenvalue=2)

    with warns_deprecated_sympy():
        assert SpecialOnlyMatrix.jordan_block(
            rows=4, cols=3, eigenvalue=2) == \
            Matrix([
                [2, 1, 0],
                [0, 2, 1],
                [0, 0, 2],
                [0, 0, 0]])

    # Using alias keyword
    assert SpecialOnlyMatrix.jordan_block(size=3, eigenvalue=2) == \
        SpecialOnlyMatrix.jordan_block(size=3, eigenval=2)


# SubspaceOnlyMatrix tests
def test_columnspace():
    m = SubspaceOnlyMatrix([[ 1,  2,  0,  2,  5],
                            [-2, -5,  1, -1, -8],
                            [ 0, -3,  3,  4,  1],
                            [ 3,  6,  0, -7,  2]])

    basis = m.columnspace()
    assert basis[0] == Matrix([1, -2, 0, 3])
    assert basis[1] == Matrix([2, -5, -3, 6])
    assert basis[2] == Matrix([2, -1, 4, -7])

    assert len(basis) == 3
    assert Matrix.hstack(m, *basis).columnspace() == basis


def test_rowspace():
    m = SubspaceOnlyMatrix([[ 1,  2,  0,  2,  5],
                            [-2, -5,  1, -1, -8],
                            [ 0, -3,  3,  4,  1],
                            [ 3,  6,  0, -7,  2]])

    basis = m.rowspace()
    assert basis[0] == Matrix([[1, 2, 0, 2, 5]])
    assert basis[1] == Matrix([[0, -1, 1, 3, 2]])
    assert basis[2] == Matrix([[0, 0, 0, 5, 5]])

    assert len(basis) == 3


def test_nullspace():
    m = SubspaceOnlyMatrix([[ 1,  2,  0,  2,  5],
                            [-2, -5,  1, -1, -8],
                            [ 0, -3,  3,  4,  1],
                            [ 3,  6,  0, -7,  2]])

    basis = m.nullspace()
    assert basis[0] == Matrix([-2, 1, 1, 0, 0])
    assert basis[1] == Matrix([-1, -1, 0, -1, 1])
    # make sure the null space is really gets zeroed
    assert all(e.is_zero for e in m*basis[0])
    assert all(e.is_zero for e in m*basis[1])


def test_orthogonalize():
    m = Matrix([[1, 2], [3, 4]])
    assert m.orthogonalize(Matrix([[2], [1]])) == [Matrix([[2], [1]])]
    assert m.orthogonalize(Matrix([[2], [1]]), normalize=True) == [Matrix([[2*sqrt(5)/5], [sqrt(5)/5]])]
    assert m.orthogonalize(Matrix([[1], [2]]), Matrix([[-1], [4]])) == [Matrix([[1], [2]]), Matrix([[-S(12)/5], [S(6)/5]])]
    assert m.orthogonalize(Matrix([[0], [0]]), Matrix([[-1], [4]])) == [Matrix([[-1], [4]])]
    assert m.orthogonalize(Matrix([[0], [0]])) == []

    n = Matrix([[9, 1, 9], [3, 6, 10], [8, 5, 2]])
    vecs = [Matrix([[-5], [1]]), Matrix([[-5], [2]]), Matrix([[-5], [-2]])]
    assert n.orthogonalize(*vecs) == [Matrix([[-5], [1]]), Matrix([[S(5)/26], [S(25)/26]])]


# EigenOnlyMatrix tests
def test_eigenvals():
    M = EigenOnlyMatrix([[0, 1, 1],
                [1, 0, 0],
                [1, 1, 1]])
    assert M.eigenvals() == {2*S.One: 1, -S.One: 1, S.Zero: 1}

    # if we cannot factor the char poly, we raise an error
    m = Matrix([
        [3,  0,  0, 0, -3],
        [0, -3, -3, 0,  3],
        [0,  3,  0, 3,  0],
        [0,  0,  3, 0,  3],
        [3,  0,  0, 3,  0]])
    raises(MatrixError, lambda: m.eigenvals())


def test_eigenvects():
    M = EigenOnlyMatrix([[0, 1, 1],
                [1, 0, 0],
                [1, 1, 1]])
    vecs = M.eigenvects()
    for val, mult, vec_list in vecs:
        assert len(vec_list) == 1
        assert M*vec_list[0] == val*vec_list[0]


def test_left_eigenvects():
    M = EigenOnlyMatrix([[0, 1, 1],
                [1, 0, 0],
                [1, 1, 1]])
    vecs = M.left_eigenvects()
    for val, mult, vec_list in vecs:
        assert len(vec_list) == 1
        assert vec_list[0]*M == val*vec_list[0]


def test_diagonalize():
    m = EigenOnlyMatrix(2, 2, [0, -1, 1, 0])
    raises(MatrixError, lambda: m.diagonalize(reals_only=True))
    P, D = m.diagonalize()
    assert D.is_diagonal()
    assert D == Matrix([
                 [-I, 0],
                 [ 0, I]])

    # make sure we use floats out if floats are passed in
    m = EigenOnlyMatrix(2, 2, [0, .5, .5, 0])
    P, D = m.diagonalize()
    assert all(isinstance(e, Float) for e in D.values())
    assert all(isinstance(e, Float) for e in P.values())

    _, D2 = m.diagonalize(reals_only=True)
    assert D == D2


def test_is_diagonalizable():
    a, b, c = symbols('a b c')
    m = EigenOnlyMatrix(2, 2, [a, c, c, b])
    assert m.is_symmetric()
    assert m.is_diagonalizable()
    assert not EigenOnlyMatrix(2, 2, [1, 1, 0, 1]).is_diagonalizable()

    m = EigenOnlyMatrix(2, 2, [0, -1, 1, 0])
    assert m.is_diagonalizable()
    assert not m.is_diagonalizable(reals_only=True)


def test_jordan_form():
    m = Matrix(3, 2, [-3, 1, -3, 20, 3, 10])
    raises(NonSquareMatrixError, lambda: m.jordan_form())

    # the next two tests test the cases where the old
    # algorithm failed due to the fact that the block structure can
    # *NOT* be determined  from algebraic and geometric multiplicity alone
    # This can be seen most easily when one lets compute the J.c.f. of a matrix that
    # is in J.c.f already.
    m = EigenOnlyMatrix(4, 4, [2, 1, 0, 0,
                    0, 2, 1, 0,
                    0, 0, 2, 0,
                    0, 0, 0, 2
    ])
    P, J = m.jordan_form()
    assert m == J

    m = EigenOnlyMatrix(4, 4, [2, 1, 0, 0,
                    0, 2, 0, 0,
                    0, 0, 2, 1,
                    0, 0, 0, 2
    ])
    P, J = m.jordan_form()
    assert m == J

    A = Matrix([[ 2,  4,  1,  0],
                [-4,  2,  0,  1],
                [ 0,  0,  2,  4],
                [ 0,  0, -4,  2]])
    P, J = A.jordan_form()
    assert simplify(P*J*P.inv()) == A

    assert EigenOnlyMatrix(1,1,[1]).jordan_form() == (Matrix([1]), Matrix([1]))
    assert EigenOnlyMatrix(1,1,[1]).jordan_form(calc_transform=False) == Matrix([1])

    # make sure if we cannot factor the characteristic polynomial, we raise an error
    m = Matrix([[3, 0, 0, 0, -3], [0, -3, -3, 0, 3], [0, 3, 0, 3, 0], [0, 0, 3, 0, 3], [3, 0, 0, 3, 0]])
    raises(MatrixError, lambda: m.jordan_form())

    # make sure that if the input has floats, the output does too
    m = Matrix([
        [                0.6875, 0.125 + 0.1875*sqrt(3)],
        [0.125 + 0.1875*sqrt(3),                 0.3125]])
    P, J = m.jordan_form()
    assert all(isinstance(x, Float) or x == 0 for x in P)
    assert all(isinstance(x, Float) or x == 0 for x in J)


def test_singular_values():
    x = Symbol('x', real=True)

    A = EigenOnlyMatrix([[0, 1*I], [2, 0]])
    # if singular values can be sorted, they should be in decreasing order
    assert A.singular_values() == [2, 1]

    A = eye(3)
    A[1, 1] = x
    A[2, 2] = 5
    vals = A.singular_values()
    # since Abs(x) cannot be sorted, test set equality
    assert set(vals) == set([5, 1, Abs(x)])

    A = EigenOnlyMatrix([[sin(x), cos(x)], [-cos(x), sin(x)]])
    vals = [sv.trigsimp() for sv in A.singular_values()]
    assert vals == [S(1), S(1)]

    A = EigenOnlyMatrix([
        [2, 4],
        [1, 3],
        [0, 0],
        [0, 0]
        ])
    assert A.singular_values() == \
        [sqrt(sqrt(221) + 15), sqrt(15 - sqrt(221))]
    assert A.T.singular_values() == \
        [sqrt(sqrt(221) + 15), sqrt(15 - sqrt(221)), 0, 0]


# CalculusOnlyMatrix tests
@XFAIL
def test_diff():
    x, y = symbols('x y')
    m = CalculusOnlyMatrix(2, 1, [x, y])
    # TODO: currently not working as ``_MinimalMatrix`` cannot be sympified:
    assert m.diff(x) == Matrix(2, 1, [1, 0])


def test_integrate():
    x, y = symbols('x y')
    m = CalculusOnlyMatrix(2, 1, [x, y])
    assert m.integrate(x) == Matrix(2, 1, [x**2/2, y*x])


def test_jacobian2():
    rho, phi = symbols("rho,phi")
    X = CalculusOnlyMatrix(3, 1, [rho*cos(phi), rho*sin(phi), rho**2])
    Y = CalculusOnlyMatrix(2, 1, [rho, phi])
    J = Matrix([
        [cos(phi), -rho*sin(phi)],
        [sin(phi),  rho*cos(phi)],
        [   2*rho,             0],
    ])
    assert X.jacobian(Y) == J

    m = CalculusOnlyMatrix(2, 2, [1, 2, 3, 4])
    m2 = CalculusOnlyMatrix(4, 1, [1, 2, 3, 4])
    raises(TypeError, lambda: m.jacobian(Matrix([1,2])))
    raises(TypeError, lambda: m2.jacobian(m))


def test_limit():
    x, y = symbols('x y')
    m = CalculusOnlyMatrix(2, 1, [1/x, y])
    assert m.limit(x, 5) == Matrix(2, 1, [S(1)/5, y])


def test_issue_13774():
    M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    v = [1,1,1]
    raises(TypeError, lambda: M*v)
    raises(TypeError, lambda: v*M)


def test___eq__():
    assert (EigenOnlyMatrix(
        [[0, 1, 1],
        [1, 0, 0],
        [1, 1, 1]]) == {}) is False
