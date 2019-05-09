import random

from sympy import (
    Abs, Add, E, Float, I, Integer, Max, Min, N, Poly, Pow, PurePoly, Rational,
    S, Symbol, cos, exp, expand_mul, oo, pi, signsimp, simplify, sin, sqrt, symbols,
    sympify, trigsimp, tan, sstr, diff, Function)
from sympy.matrices.matrices import (ShapeError, MatrixError,
    NonSquareMatrixError, DeferredVector, _find_reasonable_pivot_naive,
    _simplify)
from sympy.matrices import (
    GramSchmidt, ImmutableMatrix, ImmutableSparseMatrix, Matrix,
    SparseMatrix, casoratian, diag, eye, hessian,
    matrix_multiply_elementwise, ones, randMatrix, rot_axis1, rot_axis2,
    rot_axis3, wronskian, zeros, MutableDenseMatrix, ImmutableDenseMatrix, MatrixSymbol)
from sympy.core.compatibility import long, iterable, range, Hashable
from sympy.core import Tuple, Wild
from sympy.utilities.iterables import flatten, capture
from sympy.utilities.pytest import raises, XFAIL, slow, skip, warns_deprecated_sympy
from sympy.solvers import solve
from sympy.assumptions import Q
from sympy.tensor.array import Array
from sympy.matrices.expressions import MatPow

from sympy.abc import a, b, c, d, x, y, z, t

# don't re-order this list
classes = (Matrix, SparseMatrix, ImmutableMatrix, ImmutableSparseMatrix)


def test_args():
    for c, cls in enumerate(classes):
        m = cls.zeros(3, 2)
        # all should give back the same type of arguments, e.g. ints for shape
        assert m.shape == (3, 2) and all(type(i) is int for i in m.shape)
        assert m.rows == 3 and type(m.rows) is int
        assert m.cols == 2 and type(m.cols) is int
        if not c % 2:
            assert type(m._mat) in (list, tuple, Tuple)
        else:
            assert type(m._smat) is dict


def test_division():
    v = Matrix(1, 2, [x, y])
    assert v.__div__(z) == Matrix(1, 2, [x/z, y/z])
    assert v.__truediv__(z) == Matrix(1, 2, [x/z, y/z])
    assert v/z == Matrix(1, 2, [x/z, y/z])


def test_sum():
    m = Matrix([[1, 2, 3], [x, y, x], [2*y, -50, z*x]])
    assert m + m == Matrix([[2, 4, 6], [2*x, 2*y, 2*x], [4*y, -100, 2*z*x]])
    n = Matrix(1, 2, [1, 2])
    raises(ShapeError, lambda: m + n)

def test_abs():
    m = Matrix(1, 2, [-3, x])
    n = Matrix(1, 2, [3, Abs(x)])
    assert abs(m) == n

def test_addition():
    a = Matrix((
        (1, 2),
        (3, 1),
    ))

    b = Matrix((
        (1, 2),
        (3, 0),
    ))

    assert a + b == a.add(b) == Matrix([[2, 4], [6, 1]])


def test_fancy_index_matrix():
    for M in (Matrix, SparseMatrix):
        a = M(3, 3, range(9))
        assert a == a[:, :]
        assert a[1, :] == Matrix(1, 3, [3, 4, 5])
        assert a[:, 1] == Matrix([1, 4, 7])
        assert a[[0, 1], :] == Matrix([[0, 1, 2], [3, 4, 5]])
        assert a[[0, 1], 2] == a[[0, 1], [2]]
        assert a[2, [0, 1]] == a[[2], [0, 1]]
        assert a[:, [0, 1]] == Matrix([[0, 1], [3, 4], [6, 7]])
        assert a[0, 0] == 0
        assert a[0:2, :] == Matrix([[0, 1, 2], [3, 4, 5]])
        assert a[:, 0:2] == Matrix([[0, 1], [3, 4], [6, 7]])
        assert a[::2, 1] == a[[0, 2], 1]
        assert a[1, ::2] == a[1, [0, 2]]
        a = M(3, 3, range(9))
        assert a[[0, 2, 1, 2, 1], :] == Matrix([
            [0, 1, 2],
            [6, 7, 8],
            [3, 4, 5],
            [6, 7, 8],
            [3, 4, 5]])
        assert a[:, [0,2,1,2,1]] == Matrix([
            [0, 2, 1, 2, 1],
            [3, 5, 4, 5, 4],
            [6, 8, 7, 8, 7]])

    a = SparseMatrix.zeros(3)
    a[1, 2] = 2
    a[0, 1] = 3
    a[2, 0] = 4
    assert a.extract([1, 1], [2]) == Matrix([
    [2],
    [2]])
    assert a.extract([1, 0], [2, 2, 2]) == Matrix([
    [2, 2, 2],
    [0, 0, 0]])
    assert a.extract([1, 0, 1, 2], [2, 0, 1, 0]) == Matrix([
        [2, 0, 0, 0],
        [0, 0, 3, 0],
        [2, 0, 0, 0],
        [0, 4, 0, 4]])


def test_multiplication():
    a = Matrix((
        (1, 2),
        (3, 1),
        (0, 6),
    ))

    b = Matrix((
        (1, 2),
        (3, 0),
    ))

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

    h = matrix_multiply_elementwise(a, c)
    assert h == a.multiply_elementwise(c)
    assert h[0, 0] == 7
    assert h[0, 1] == 4
    assert h[1, 0] == 18
    assert h[1, 1] == 6
    assert h[2, 0] == 0
    assert h[2, 1] == 0
    raises(ShapeError, lambda: matrix_multiply_elementwise(a, b))

    c = b * Symbol("x")
    assert isinstance(c, Matrix)
    assert c[0, 0] == x
    assert c[0, 1] == 2*x
    assert c[1, 0] == 3*x
    assert c[1, 1] == 0

    c2 = x * b
    assert c == c2

    c = 5 * b
    assert isinstance(c, Matrix)
    assert c[0, 0] == 5
    assert c[0, 1] == 2*5
    assert c[1, 0] == 3*5
    assert c[1, 1] == 0

    try:
        eval('c = 5 @ b')
    except SyntaxError:
        pass
    else:
        assert isinstance(c, Matrix)
        assert c[0, 0] == 5
        assert c[0, 1] == 2*5
        assert c[1, 0] == 3*5
        assert c[1, 1] == 0


def test_power():
    raises(NonSquareMatrixError, lambda: Matrix((1, 2))**2)

    R = Rational
    A = Matrix([[2, 3], [4, 5]])
    assert (A**-3)[:] == [R(-269)/8, R(153)/8, R(51)/2, R(-29)/2]
    assert (A**5)[:] == [6140, 8097, 10796, 14237]
    A = Matrix([[2, 1, 3], [4, 2, 4], [6, 12, 1]])
    assert (A**3)[:] == [290, 262, 251, 448, 440, 368, 702, 954, 433]
    assert A**0 == eye(3)
    assert A**1 == A
    assert (Matrix([[2]]) ** 100)[0, 0] == 2**100
    assert eye(2)**10000000 == eye(2)
    assert Matrix([[1, 2], [3, 4]])**Integer(2) == Matrix([[7, 10], [15, 22]])

    A = Matrix([[33, 24], [48, 57]])
    assert (A**(S(1)/2))[:] == [5, 2, 4, 7]
    A = Matrix([[0, 4], [-1, 5]])
    assert (A**(S(1)/2))**2 == A

    assert Matrix([[1, 0], [1, 1]])**(S(1)/2) == Matrix([[1, 0], [S.Half, 1]])
    assert Matrix([[1, 0], [1, 1]])**0.5 == Matrix([[1.0, 0], [0.5, 1.0]])
    from sympy.abc import a, b, n
    assert Matrix([[1, a], [0, 1]])**n == Matrix([[1, a*n], [0, 1]])
    assert Matrix([[b, a], [0, b]])**n == Matrix([[b**n, a*b**(n-1)*n], [0, b**n]])
    assert Matrix([[a, 1, 0], [0, a, 1], [0, 0, a]])**n == Matrix([
        [a**n, a**(n-1)*n, a**(n-2)*(n-1)*n/2],
        [0, a**n, a**(n-1)*n],
        [0, 0, a**n]])
    assert Matrix([[a, 1, 0], [0, a, 0], [0, 0, b]])**n == Matrix([
        [a**n, a**(n-1)*n, 0],
        [0, a**n, 0],
        [0, 0, b**n]])

    A = Matrix([[1, 0], [1, 7]])
    assert A._matrix_pow_by_jordan_blocks(3) == A._eval_pow_by_recursion(3)
    A = Matrix([[2]])
    assert A**10 == Matrix([[2**10]]) == A._matrix_pow_by_jordan_blocks(10) == \
        A._eval_pow_by_recursion(10)

    # testing a matrix that cannot be jordan blocked issue 11766
    m = Matrix([[3, 0, 0, 0, -3], [0, -3, -3, 0, 3], [0, 3, 0, 3, 0], [0, 0, 3, 0, 3], [3, 0, 0, 3, 0]])
    raises(MatrixError, lambda: m._matrix_pow_by_jordan_blocks(10))

    # test issue 11964
    raises(ValueError, lambda: Matrix([[1, 1], [3, 3]])._matrix_pow_by_jordan_blocks(-10))
    A = Matrix([[0, 1, 0], [0, 0, 1], [0, 0, 0]])  # Nilpotent jordan block size 3
    assert A**10.0 == Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    raises(ValueError, lambda: A**2.1)
    raises(ValueError, lambda: A**(S(3)/2))
    A = Matrix([[8, 1], [3, 2]])
    assert A**10.0 == Matrix([[1760744107, 272388050], [817164150, 126415807]])
    A = Matrix([[0, 0, 1], [0, 0, 1], [0, 0, 1]])  # Nilpotent jordan block size 1
    assert A**10.2 == Matrix([[0, 0, 1], [0, 0, 1], [0, 0, 1]])
    A = Matrix([[0, 1, 0], [0, 0, 1], [0, 0, 1]])  # Nilpotent jordan block size 2
    assert A**10.0 == Matrix([[0, 0, 1], [0, 0, 1], [0, 0, 1]])
    n = Symbol('n', integer=True)
    assert isinstance(A**n, MatPow)
    n = Symbol('n', integer=True, nonnegative=True)
    raises(ValueError, lambda: A**n)
    assert A**(n + 2) == Matrix([[0, 0, 1], [0, 0, 1], [0, 0, 1]])
    raises(ValueError, lambda: A**(S(3)/2))
    A = Matrix([[0, 0, 1], [3, 0, 1], [4, 3, 1]])
    assert A**5.0 == Matrix([[168,  72,  89], [291, 144, 161], [572, 267, 329]])
    assert A**5.0 == A**5
    A = Matrix([[0, 1, 0],[-1, 0, 0],[0, 0, 0]])
    n = Symbol("n")
    An = A**n
    assert An.subs(n, 2).doit() == A**2
    raises(ValueError, lambda: An.subs(n, -2).doit())
    assert An * An == A**(2*n)


def test_creation():
    raises(ValueError, lambda: Matrix(5, 5, range(20)))
    raises(ValueError, lambda: Matrix(5, -1, []))
    raises(IndexError, lambda: Matrix((1, 2))[2])
    with raises(IndexError):
        Matrix((1, 2))[1:2] = 5
    with raises(IndexError):
        Matrix((1, 2))[3] = 5

    assert Matrix() == Matrix([]) == Matrix([[]]) == Matrix(0, 0, [])

    a = Matrix([[x, 0], [0, 0]])
    m = a
    assert m.cols == m.rows
    assert m.cols == 2
    assert m[:] == [x, 0, 0, 0]

    b = Matrix(2, 2, [x, 0, 0, 0])
    m = b
    assert m.cols == m.rows
    assert m.cols == 2
    assert m[:] == [x, 0, 0, 0]

    assert a == b

    assert Matrix(b) == b

    c = Matrix((
        Matrix((
            (1, 2, 3),
            (4, 5, 6)
        )),
        (7, 8, 9)
    ))
    assert c.cols == 3
    assert c.rows == 3
    assert c[:] == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    assert Matrix(eye(2)) == eye(2)
    assert ImmutableMatrix(ImmutableMatrix(eye(2))) == ImmutableMatrix(eye(2))
    assert ImmutableMatrix(c) == c.as_immutable()
    assert Matrix(ImmutableMatrix(c)) == ImmutableMatrix(c).as_mutable()

    assert c is not Matrix(c)


def test_tolist():
    lst = [[S.One, S.Half, x*y, S.Zero], [x, y, z, x**2], [y, -S.One, z*x, 3]]
    m = Matrix(lst)
    assert m.tolist() == lst


def test_as_mutable():
    assert zeros(0, 3).as_mutable() == zeros(0, 3)
    assert zeros(0, 3).as_immutable() == ImmutableMatrix(zeros(0, 3))
    assert zeros(3, 0).as_immutable() == ImmutableMatrix(zeros(3, 0))


def test_determinant():

    for M in [Matrix(), Matrix([[1]])]:
        assert (
            M.det() ==
            M._eval_det_bareiss() ==
            M._eval_det_berkowitz() ==
            M._eval_det_lu() ==
            1)

    M = Matrix(( (-3,  2),
                 ( 8, -5) ))

    assert M.det(method="bareiss") == -1
    assert M.det(method="berkowitz") == -1
    assert M.det(method="lu") == -1

    M = Matrix(( (x,   1),
                 (y, 2*y) ))

    assert M.det(method="bareiss") == 2*x*y - y
    assert M.det(method="berkowitz") == 2*x*y - y
    assert M.det(method="lu") == 2*x*y - y

    M = Matrix(( (1, 1, 1),
                 (1, 2, 3),
                 (1, 3, 6) ))

    assert M.det(method="bareiss") == 1
    assert M.det(method="berkowitz") == 1
    assert M.det(method="lu") == 1

    M = Matrix(( ( 3, -2,  0, 5),
                 (-2,  1, -2, 2),
                 ( 0, -2,  5, 0),
                 ( 5,  0,  3, 4) ))

    assert M.det(method="bareiss") == -289
    assert M.det(method="berkowitz") == -289
    assert M.det(method="lu") == -289

    M = Matrix(( ( 1,  2,  3,  4),
                 ( 5,  6,  7,  8),
                 ( 9, 10, 11, 12),
                 (13, 14, 15, 16) ))

    assert M.det(method="bareiss") == 0
    assert M.det(method="berkowitz") == 0
    assert M.det(method="lu") == 0

    M = Matrix(( (3, 2, 0, 0, 0),
                 (0, 3, 2, 0, 0),
                 (0, 0, 3, 2, 0),
                 (0, 0, 0, 3, 2),
                 (2, 0, 0, 0, 3) ))

    assert M.det(method="bareiss") == 275
    assert M.det(method="berkowitz") == 275
    assert M.det(method="lu") == 275

    M = Matrix(( (1, 0,  1,  2, 12),
                 (2, 0,  1,  1,  4),
                 (2, 1,  1, -1,  3),
                 (3, 2, -1,  1,  8),
                 (1, 1,  1,  0,  6) ))

    assert M.det(method="bareiss") == -55
    assert M.det(method="berkowitz") == -55
    assert M.det(method="lu") == -55

    M = Matrix(( (-5,  2,  3,  4,  5),
                 ( 1, -4,  3,  4,  5),
                 ( 1,  2, -3,  4,  5),
                 ( 1,  2,  3, -2,  5),
                 ( 1,  2,  3,  4, -1) ))

    assert M.det(method="bareiss") == 11664
    assert M.det(method="berkowitz") == 11664
    assert M.det(method="lu") == 11664

    M = Matrix(( ( 2,  7, -1, 3, 2),
                 ( 0,  0,  1, 0, 1),
                 (-2,  0,  7, 0, 2),
                 (-3, -2,  4, 5, 3),
                 ( 1,  0,  0, 0, 1) ))

    assert M.det(method="bareiss") == 123
    assert M.det(method="berkowitz") == 123
    assert M.det(method="lu") == 123

    M = Matrix(( (x, y, z),
                 (1, 0, 0),
                 (y, z, x) ))

    assert M.det(method="bareiss") == z**2 - x*y
    assert M.det(method="berkowitz") == z**2 - x*y
    assert M.det(method="lu") == z**2 - x*y

    # issue 13835
    a = symbols('a')
    M = lambda n: Matrix([[i + a*j for i in range(n)]
                          for j in range(n)])
    assert M(5).det() == 0
    assert M(6).det() == 0
    assert M(7).det() == 0


def test_slicing():
    m0 = eye(4)
    assert m0[:3, :3] == eye(3)
    assert m0[2:4, 0:2] == zeros(2)

    m1 = Matrix(3, 3, lambda i, j: i + j)
    assert m1[0, :] == Matrix(1, 3, (0, 1, 2))
    assert m1[1:3, 1] == Matrix(2, 1, (2, 3))

    m2 = Matrix([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]])
    assert m2[:, -1] == Matrix(4, 1, [3, 7, 11, 15])
    assert m2[-2:, :] == Matrix([[8, 9, 10, 11], [12, 13, 14, 15]])


def test_submatrix_assignment():
    m = zeros(4)
    m[2:4, 2:4] = eye(2)
    assert m == Matrix(((0, 0, 0, 0),
                        (0, 0, 0, 0),
                        (0, 0, 1, 0),
                        (0, 0, 0, 1)))
    m[:2, :2] = eye(2)
    assert m == eye(4)
    m[:, 0] = Matrix(4, 1, (1, 2, 3, 4))
    assert m == Matrix(((1, 0, 0, 0),
                        (2, 1, 0, 0),
                        (3, 0, 1, 0),
                        (4, 0, 0, 1)))
    m[:, :] = zeros(4)
    assert m == zeros(4)
    m[:, :] = [(1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16)]
    assert m == Matrix(((1, 2, 3, 4),
                        (5, 6, 7, 8),
                        (9, 10, 11, 12),
                        (13, 14, 15, 16)))
    m[:2, 0] = [0, 0]
    assert m == Matrix(((0, 2, 3, 4),
                        (0, 6, 7, 8),
                        (9, 10, 11, 12),
                        (13, 14, 15, 16)))


def test_extract():
    m = Matrix(4, 3, lambda i, j: i*3 + j)
    assert m.extract([0, 1, 3], [0, 1]) == Matrix(3, 2, [0, 1, 3, 4, 9, 10])
    assert m.extract([0, 3], [0, 0, 2]) == Matrix(2, 3, [0, 0, 2, 9, 9, 11])
    assert m.extract(range(4), range(3)) == m
    raises(IndexError, lambda: m.extract([4], [0]))
    raises(IndexError, lambda: m.extract([0], [3]))


def test_reshape():
    m0 = eye(3)
    assert m0.reshape(1, 9) == Matrix(1, 9, (1, 0, 0, 0, 1, 0, 0, 0, 1))
    m1 = Matrix(3, 4, lambda i, j: i + j)
    assert m1.reshape(
        4, 3) == Matrix(((0, 1, 2), (3, 1, 2), (3, 4, 2), (3, 4, 5)))
    assert m1.reshape(2, 6) == Matrix(((0, 1, 2, 3, 1, 2), (3, 4, 2, 3, 4, 5)))


def test_applyfunc():
    m0 = eye(3)
    assert m0.applyfunc(lambda x: 2*x) == eye(3)*2
    assert m0.applyfunc(lambda x: 0) == zeros(3)


def test_expand():
    m0 = Matrix([[x*(x + y), 2], [((x + y)*y)*x, x*(y + x*(x + y))]])
    # Test if expand() returns a matrix
    m1 = m0.expand()
    assert m1 == Matrix(
        [[x*y + x**2, 2], [x*y**2 + y*x**2, x*y + y*x**2 + x**3]])

    a = Symbol('a', real=True)

    assert Matrix([exp(I*a)]).expand(complex=True) == \
        Matrix([cos(a) + I*sin(a)])

    assert Matrix([[0, 1, 2], [0, 0, -1], [0, 0, 0]]).exp() == Matrix([
        [1, 1, Rational(3, 2)],
        [0, 1, -1],
        [0, 0, 1]]
    )

def test_refine():
    m0 = Matrix([[Abs(x)**2, sqrt(x**2)],
                [sqrt(x**2)*Abs(y)**2, sqrt(y**2)*Abs(x)**2]])
    m1 = m0.refine(Q.real(x) & Q.real(y))
    assert m1 == Matrix([[x**2, Abs(x)], [y**2*Abs(x), x**2*Abs(y)]])

    m1 = m0.refine(Q.positive(x) & Q.positive(y))
    assert m1 == Matrix([[x**2, x], [x*y**2, x**2*y]])

    m1 = m0.refine(Q.negative(x) & Q.negative(y))
    assert m1 == Matrix([[x**2, -x], [-x*y**2, -x**2*y]])

def test_random():
    M = randMatrix(3, 3)
    M = randMatrix(3, 3, seed=3)
    assert M == randMatrix(3, 3, seed=3)

    M = randMatrix(3, 4, 0, 150)
    M = randMatrix(3, seed=4, symmetric=True)
    assert M == randMatrix(3, seed=4, symmetric=True)

    S = M.copy()
    S.simplify()
    assert S == M  # doesn't fail when elements are Numbers, not int

    rng = random.Random(4)
    assert M == randMatrix(3, symmetric=True, prng=rng)

    # Ensure symmetry
    for size in (10, 11): # Test odd and even
        for percent in (100, 70, 30):
            M = randMatrix(size, symmetric=True, percent=percent, prng=rng)
            assert M == M.T

    M = randMatrix(10, min=1, percent=70)
    zero_count = 0
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if M[i, j] == 0:
                zero_count += 1
    assert zero_count == 30


def test_LUdecomp():
    testmat = Matrix([[0, 2, 5, 3],
                      [3, 3, 7, 4],
                      [8, 4, 0, 2],
                      [-2, 6, 3, 4]])
    L, U, p = testmat.LUdecomposition()
    assert L.is_lower
    assert U.is_upper
    assert (L*U).permute_rows(p, 'backward') - testmat == zeros(4)

    testmat = Matrix([[6, -2, 7, 4],
                      [0, 3, 6, 7],
                      [1, -2, 7, 4],
                      [-9, 2, 6, 3]])
    L, U, p = testmat.LUdecomposition()
    assert L.is_lower
    assert U.is_upper
    assert (L*U).permute_rows(p, 'backward') - testmat == zeros(4)

    # non-square
    testmat = Matrix([[1, 2, 3],
                      [4, 5, 6],
                      [7, 8, 9],
                      [10, 11, 12]])
    L, U, p = testmat.LUdecomposition(rankcheck=False)
    assert L.is_lower
    assert U.is_upper
    assert (L*U).permute_rows(p, 'backward') - testmat == zeros(4, 3)

    # square and singular
    testmat = Matrix([[1, 2, 3],
                      [2, 4, 6],
                      [4, 5, 6]])
    L, U, p = testmat.LUdecomposition(rankcheck=False)
    assert L.is_lower
    assert U.is_upper
    assert (L*U).permute_rows(p, 'backward') - testmat == zeros(3)

    M = Matrix(((1, x, 1), (2, y, 0), (y, 0, z)))
    L, U, p = M.LUdecomposition()
    assert L.is_lower
    assert U.is_upper
    assert (L*U).permute_rows(p, 'backward') - M == zeros(3)

    mL = Matrix((
        (1, 0, 0),
        (2, 3, 0),
    ))
    assert mL.is_lower is True
    assert mL.is_upper is False
    mU = Matrix((
        (1, 2, 3),
        (0, 4, 5),
    ))
    assert mU.is_lower is False
    assert mU.is_upper is True

    # test FF LUdecomp
    M = Matrix([[1, 3, 3],
                [3, 2, 6],
                [3, 2, 2]])
    P, L, Dee, U = M.LUdecompositionFF()
    assert P*M == L*Dee.inv()*U

    M = Matrix([[1,  2, 3,  4],
                [3, -1, 2,  3],
                [3,  1, 3, -2],
                [6, -1, 0,  2]])
    P, L, Dee, U = M.LUdecompositionFF()
    assert P*M == L*Dee.inv()*U

    M = Matrix([[0, 0, 1],
                [2, 3, 0],
                [3, 1, 4]])
    P, L, Dee, U = M.LUdecompositionFF()
    assert P*M == L*Dee.inv()*U

    # issue 15794
    M = Matrix(
        [[1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]]
    )
    raises(ValueError, lambda : M.LUdecomposition_Simple(rankcheck=True))

def test_LUsolve():
    A = Matrix([[2, 3, 5],
                [3, 6, 2],
                [8, 3, 6]])
    x = Matrix(3, 1, [3, 7, 5])
    b = A*x
    soln = A.LUsolve(b)
    assert soln == x
    A = Matrix([[0, -1, 2],
                [5, 10, 7],
                [8,  3, 4]])
    x = Matrix(3, 1, [-1, 2, 5])
    b = A*x
    soln = A.LUsolve(b)
    assert soln == x
    A = Matrix([[2, 1], [1, 0], [1, 0]])   # issue 14548
    b = Matrix([3, 1, 1])
    assert A.LUsolve(b) == Matrix([1, 1])
    b = Matrix([3, 1, 2])                  # inconsistent
    raises(ValueError, lambda: A.LUsolve(b))
    A = Matrix([[0, -1, 2],
                [5, 10, 7],
                [8,  3, 4],
                [2, 3, 5],
                [3, 6, 2],
                [8, 3, 6]])
    x = Matrix([2, 1, -4])
    b = A*x
    soln = A.LUsolve(b)
    assert soln == x
    A = Matrix([[0, -1, 2], [5, 10, 7]])  # underdetermined
    x = Matrix([-1, 2, 0])
    b = A*x
    raises(NotImplementedError, lambda: A.LUsolve(b))

    A = Matrix(4, 4, lambda i, j: 1/(i+j+1) if i != 3 else 0)
    b = Matrix.zeros(4, 1)
    raises(NotImplementedError, lambda: A.LUsolve(b))


def test_QRsolve():
    A = Matrix([[2, 3, 5],
                [3, 6, 2],
                [8, 3, 6]])
    x = Matrix(3, 1, [3, 7, 5])
    b = A*x
    soln = A.QRsolve(b)
    assert soln == x
    x = Matrix([[1, 2], [3, 4], [5, 6]])
    b = A*x
    soln = A.QRsolve(b)
    assert soln == x

    A = Matrix([[0, -1, 2],
                [5, 10, 7],
                [8,  3, 4]])
    x = Matrix(3, 1, [-1, 2, 5])
    b = A*x
    soln = A.QRsolve(b)
    assert soln == x
    x = Matrix([[7, 8], [9, 10], [11, 12]])
    b = A*x
    soln = A.QRsolve(b)
    assert soln == x


def test_inverse():
    A = eye(4)
    assert A.inv() == eye(4)
    assert A.inv(method="LU") == eye(4)
    assert A.inv(method="ADJ") == eye(4)
    A = Matrix([[2, 3, 5],
                [3, 6, 2],
                [8, 3, 6]])
    Ainv = A.inv()
    assert A*Ainv == eye(3)
    assert A.inv(method="LU") == Ainv
    assert A.inv(method="ADJ") == Ainv

    # test that immutability is not a problem
    cls = ImmutableMatrix
    m = cls([[48, 49, 31],
             [ 9, 71, 94],
             [59, 28, 65]])
    assert all(type(m.inv(s)) is cls for s in 'GE ADJ LU'.split())
    cls = ImmutableSparseMatrix
    m = cls([[48, 49, 31],
             [ 9, 71, 94],
             [59, 28, 65]])
    assert all(type(m.inv(s)) is cls for s in 'CH LDL'.split())


def test_matrix_inverse_mod():
    A = Matrix(2, 1, [1, 0])
    raises(NonSquareMatrixError, lambda: A.inv_mod(2))
    A = Matrix(2, 2, [1, 0, 0, 0])
    raises(ValueError, lambda: A.inv_mod(2))
    A = Matrix(2, 2, [1, 2, 3, 4])
    Ai = Matrix(2, 2, [1, 1, 0, 1])
    assert A.inv_mod(3) == Ai
    A = Matrix(2, 2, [1, 0, 0, 1])
    assert A.inv_mod(2) == A
    A = Matrix(3, 3, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    raises(ValueError, lambda: A.inv_mod(5))
    A = Matrix(3, 3, [5, 1, 3, 2, 6, 0, 2, 1, 1])
    Ai = Matrix(3, 3, [6, 8, 0, 1, 5, 6, 5, 6, 4])
    assert A.inv_mod(9) == Ai
    A = Matrix(3, 3, [1, 6, -3, 4, 1, -5, 3, -5, 5])
    Ai = Matrix(3, 3, [4, 3, 3, 1, 2, 5, 1, 5, 1])
    assert A.inv_mod(6) == Ai
    A = Matrix(3, 3, [1, 6, 1, 4, 1, 5, 3, 2, 5])
    Ai = Matrix(3, 3, [6, 0, 3, 6, 6, 4, 1, 6, 1])
    assert A.inv_mod(7) == Ai


def test_util():
    R = Rational

    v1 = Matrix(1, 3, [1, 2, 3])
    v2 = Matrix(1, 3, [3, 4, 5])
    assert v1.norm() == sqrt(14)
    assert v1.project(v2) == Matrix(1, 3, [R(39)/25, R(52)/25, R(13)/5])
    assert Matrix.zeros(1, 2) == Matrix(1, 2, [0, 0])
    assert ones(1, 2) == Matrix(1, 2, [1, 1])
    assert v1.copy() == v1
    # cofactor
    assert eye(3) == eye(3).cofactor_matrix()
    test = Matrix([[1, 3, 2], [2, 6, 3], [2, 3, 6]])
    assert test.cofactor_matrix() == \
        Matrix([[27, -6, -6], [-12, 2, 3], [-3, 1, 0]])
    test = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert test.cofactor_matrix() == \
        Matrix([[-3, 6, -3], [6, -12, 6], [-3, 6, -3]])


def test_jacobian_hessian():
    L = Matrix(1, 2, [x**2*y, 2*y**2 + x*y])
    syms = [x, y]
    assert L.jacobian(syms) == Matrix([[2*x*y, x**2], [y, 4*y + x]])

    L = Matrix(1, 2, [x, x**2*y**3])
    assert L.jacobian(syms) == Matrix([[1, 0], [2*x*y**3, x**2*3*y**2]])

    f = x**2*y
    syms = [x, y]
    assert hessian(f, syms) == Matrix([[2*y, 2*x], [2*x, 0]])

    f = x**2*y**3
    assert hessian(f, syms) == \
        Matrix([[2*y**3, 6*x*y**2], [6*x*y**2, 6*x**2*y]])

    f = z + x*y**2
    g = x**2 + 2*y**3
    ans = Matrix([[0,   2*y],
                  [2*y, 2*x]])
    assert ans == hessian(f, Matrix([x, y]))
    assert ans == hessian(f, Matrix([x, y]).T)
    assert hessian(f, (y, x), [g]) == Matrix([
        [     0, 6*y**2, 2*x],
        [6*y**2,    2*x, 2*y],
        [   2*x,    2*y,   0]])


def test_QR():
    A = Matrix([[1, 2], [2, 3]])
    Q, S = A.QRdecomposition()
    R = Rational
    assert Q == Matrix([
        [  5**R(-1, 2),  (R(2)/5)*(R(1)/5)**R(-1, 2)],
        [2*5**R(-1, 2), (-R(1)/5)*(R(1)/5)**R(-1, 2)]])
    assert S == Matrix([[5**R(1, 2), 8*5**R(-1, 2)], [0, (R(1)/5)**R(1, 2)]])
    assert Q*S == A
    assert Q.T * Q == eye(2)

    A = Matrix([[1, 1, 1], [1, 1, 3], [2, 3, 4]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R


def test_QR_non_square():
    # Narrow (cols < rows) matrices
    A = Matrix([[9, 0, 26], [12, 0, -7], [0, 4, 4], [0, -3, -3]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[1, -1, 4], [1, 4, -2], [1, 4, 2], [1, -1, 0]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix(2, 1, [1, 2])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    # Wide (cols > rows) matrices
    A = Matrix([[1, 2, 3], [4, 5, 6]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[1, 2, 3, 4], [1, 4, 9, 16], [1, 8, 27, 64]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix(1, 2, [1, 2])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

def test_QR_trivial():
    # Rank deficient matrices
    A = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]]).T
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    # Zero rank matrices
    A = Matrix([[0, 0, 0]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[0, 0, 0]]).T
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[0, 0, 0], [0, 0, 0]])
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[0, 0, 0], [0, 0, 0]]).T
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    # Rank deficient matrices with zero norm from beginning columns
    A = Matrix([[0, 0, 0], [1, 2, 3]]).T
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[0, 0, 0, 0], [1, 2, 3, 4], [0, 0, 0, 0]]).T
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[0, 0, 0, 0], [1, 2, 3, 4], [0, 0, 0, 0], [2, 4, 6, 8]]).T
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R

    A = Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0], [1, 2, 3]]).T
    Q, R = A.QRdecomposition()
    assert Q.T * Q == eye(Q.cols)
    assert R.is_upper
    assert A == Q*R


def test_nullspace():
    # first test reduced row-ech form
    R = Rational

    M = Matrix([[5, 7, 2,  1],
                [1, 6, 2, -1]])
    out, tmp = M.rref()
    assert out == Matrix([[1, 0, -R(2)/23, R(13)/23],
                          [0, 1,  R(8)/23, R(-6)/23]])

    M = Matrix([[-5, -1,  4, -3, -1],
                [ 1, -1, -1,  1,  0],
                [-1,  0,  0,  0,  0],
                [ 4,  1, -4,  3,  1],
                [-2,  0,  2, -2, -1]])
    assert M*M.nullspace()[0] == Matrix(5, 1, [0]*5)

    M = Matrix([[ 1,  3, 0,  2,  6, 3, 1],
                [-2, -6, 0, -2, -8, 3, 1],
                [ 3,  9, 0,  0,  6, 6, 2],
                [-1, -3, 0,  1,  0, 9, 3]])
    out, tmp = M.rref()
    assert out == Matrix([[1, 3, 0, 0, 2, 0, 0],
                          [0, 0, 0, 1, 2, 0, 0],
                          [0, 0, 0, 0, 0, 1, R(1)/3],
                          [0, 0, 0, 0, 0, 0, 0]])

    # now check the vectors
    basis = M.nullspace()
    assert basis[0] == Matrix([-3, 1, 0, 0, 0, 0, 0])
    assert basis[1] == Matrix([0, 0, 1, 0, 0, 0, 0])
    assert basis[2] == Matrix([-2, 0, 0, -2, 1, 0, 0])
    assert basis[3] == Matrix([0, 0, 0, 0, 0, R(-1)/3, 1])

    # issue 4797; just see that we can do it when rows > cols
    M = Matrix([[1, 2], [2, 4], [3, 6]])
    assert M.nullspace()


def test_columnspace():
    M = Matrix([[ 1,  2,  0,  2,  5],
                [-2, -5,  1, -1, -8],
                [ 0, -3,  3,  4,  1],
                [ 3,  6,  0, -7,  2]])

    # now check the vectors
    basis = M.columnspace()
    assert basis[0] == Matrix([1, -2, 0, 3])
    assert basis[1] == Matrix([2, -5, -3, 6])
    assert basis[2] == Matrix([2, -1, 4, -7])

    #check by columnspace definition
    a, b, c, d, e = symbols('a b c d e')
    X = Matrix([a, b, c, d, e])
    for i in range(len(basis)):
        eq=M*X-basis[i]
        assert len(solve(eq, X)) != 0

    #check if rank-nullity theorem holds
    assert M.rank() == len(basis)
    assert len(M.nullspace()) + len(M.columnspace()) == M.cols


def test_wronskian():
    assert wronskian([cos(x), sin(x)], x) == cos(x)**2 + sin(x)**2
    assert wronskian([exp(x), exp(2*x)], x) == exp(3*x)
    assert wronskian([exp(x), x], x) == exp(x) - x*exp(x)
    assert wronskian([1, x, x**2], x) == 2
    w1 = -6*exp(x)*sin(x)*x + 6*cos(x)*exp(x)*x**2 - 6*exp(x)*cos(x)*x - \
        exp(x)*cos(x)*x**3 + exp(x)*sin(x)*x**3
    assert wronskian([exp(x), cos(x), x**3], x).expand() == w1
    assert wronskian([exp(x), cos(x), x**3], x, method='berkowitz').expand() \
        == w1
    w2 = -x**3*cos(x)**2 - x**3*sin(x)**2 - 6*x*cos(x)**2 - 6*x*sin(x)**2
    assert wronskian([sin(x), cos(x), x**3], x).expand() == w2
    assert wronskian([sin(x), cos(x), x**3], x, method='berkowitz').expand() \
        == w2
    assert wronskian([], x) == 1


def test_eigen():
    R = Rational

    assert eye(3).charpoly(x) == Poly((x - 1)**3, x)
    assert eye(3).charpoly(y) == Poly((y - 1)**3, y)

    M = Matrix([[1, 0, 0],
                [0, 1, 0],
                [0, 0, 1]])

    assert M.eigenvals(multiple=False) == {S.One: 3}
    assert M.eigenvals(multiple=True) == [1, 1, 1]

    assert M.eigenvects() == (
        [(1, 3, [Matrix([1, 0, 0]),
                 Matrix([0, 1, 0]),
                 Matrix([0, 0, 1])])])

    assert M.left_eigenvects() == (
        [(1, 3, [Matrix([[1, 0, 0]]),
                 Matrix([[0, 1, 0]]),
                 Matrix([[0, 0, 1]])])])

    M = Matrix([[0, 1, 1],
                [1, 0, 0],
                [1, 1, 1]])

    assert M.eigenvals() == {2*S.One: 1, -S.One: 1, S.Zero: 1}

    assert M.eigenvects() == (
        [
            (-1, 1, [Matrix([-1, 1, 0])]),
            ( 0, 1, [Matrix([0, -1, 1])]),
            ( 2, 1, [Matrix([R(2, 3), R(1, 3), 1])])
        ])

    assert M.left_eigenvects() == (
        [
            (-1, 1, [Matrix([[-2, 1, 1]])]),
            (0, 1, [Matrix([[-1, -1, 1]])]),
            (2, 1, [Matrix([[1, 1, 1]])])
        ])

    a = Symbol('a')
    M = Matrix([[a, 0],
                [0, 1]])

    assert M.eigenvals() == {a: 1, S.One: 1}

    M = Matrix([[1, -1],
                [1,  3]])
    assert M.eigenvects() == ([(2, 2, [Matrix(2, 1, [-1, 1])])])
    assert M.left_eigenvects() == ([(2, 2, [Matrix([[1, 1]])])])

    M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    a = R(15, 2)
    b = 3*33**R(1, 2)
    c = R(13, 2)
    d = (R(33, 8) + 3*b/8)
    e = (R(33, 8) - 3*b/8)

    def NS(e, n):
        return str(N(e, n))
    r = [
        (a - b/2, 1, [Matrix([(12 + 24/(c - b/2))/((c - b/2)*e) + 3/(c - b/2),
                              (6 + 12/(c - b/2))/e, 1])]),
        (      0, 1, [Matrix([1, -2, 1])]),
        (a + b/2, 1, [Matrix([(12 + 24/(c + b/2))/((c + b/2)*d) + 3/(c + b/2),
                              (6 + 12/(c + b/2))/d, 1])]),
    ]
    r1 = [(NS(r[i][0], 2), NS(r[i][1], 2),
        [NS(j, 2) for j in r[i][2][0]]) for i in range(len(r))]
    r = M.eigenvects()
    r2 = [(NS(r[i][0], 2), NS(r[i][1], 2),
        [NS(j, 2) for j in r[i][2][0]]) for i in range(len(r))]
    assert sorted(r1) == sorted(r2)

    eps = Symbol('eps', real=True)

    M = Matrix([[abs(eps), I*eps    ],
                [-I*eps,   abs(eps) ]])

    assert M.eigenvects() == (
        [
            ( 0, 1, [Matrix([[-I*eps/abs(eps)], [1]])]),
            ( 2*abs(eps), 1, [ Matrix([[I*eps/abs(eps)], [1]]) ] ),
        ])

    assert M.left_eigenvects() == (
        [
            (0, 1, [Matrix([[I*eps/Abs(eps), 1]])]),
            (2*Abs(eps), 1, [Matrix([[-I*eps/Abs(eps), 1]])])
        ])

    M = Matrix(3, 3, [1, 2, 0, 0, 3, 0, 2, -4, 2])
    M._eigenvects = M.eigenvects(simplify=False)
    assert max(i.q for i in M._eigenvects[0][2][0]) > 1
    M._eigenvects = M.eigenvects(simplify=True)
    assert max(i.q for i in M._eigenvects[0][2][0]) == 1
    M = Matrix([[S(1)/4, 1], [1, 1]])
    assert M.eigenvects(simplify=True) == [
        (S(5)/8 - sqrt(73)/8, 1, [Matrix([[-sqrt(73)/8 - S(3)/8], [1]])]),
        (S(5)/8 + sqrt(73)/8, 1, [Matrix([[-S(3)/8 + sqrt(73)/8], [1]])])]
    assert M.eigenvects(simplify=False) ==[
        (S(5)/8 - sqrt(73)/8, 1, [Matrix([[-1/(-S(3)/8 + sqrt(73)/8)],
                                          [                     1]])]),
        (S(5)/8 + sqrt(73)/8, 1, [Matrix([[-1/(-sqrt(73)/8 - S(3)/8)],
                                          [                     1]])])]

    m = Matrix([[1, .6, .6], [.6, .9, .9], [.9, .6, .6]])
    evals = { S(5)/4 - sqrt(385)/20: 1, sqrt(385)/20 + S(5)/4: 1, S.Zero: 1}
    assert m.eigenvals() == evals
    nevals = list(sorted(m.eigenvals(rational=False).keys()))
    sevals = list(sorted(evals.keys()))
    assert all(abs(nevals[i] - sevals[i]) < 1e-9 for i in range(len(nevals)))

    # issue 10719
    assert Matrix([]).eigenvals() == {}
    assert Matrix([]).eigenvects() == []

    # issue 15119
    raises(NonSquareMatrixError, lambda : Matrix([[1, 2], [0, 4], [0, 0]]).eigenvals())
    raises(NonSquareMatrixError, lambda : Matrix([[1, 0], [3, 4], [5, 6]]).eigenvals())
    raises(NonSquareMatrixError, lambda : Matrix([[1, 2, 3], [0, 5, 6]]).eigenvals())
    raises(NonSquareMatrixError, lambda : Matrix([[1, 0, 0], [4, 5, 0]]).eigenvals())
    raises(NonSquareMatrixError, lambda : Matrix([[1, 2, 3], [0, 5, 6]]).eigenvals(error_when_incomplete = False))
    raises(NonSquareMatrixError, lambda : Matrix([[1, 0, 0], [4, 5, 0]]).eigenvals(error_when_incomplete = False))

    # issue 15125
    from sympy.core.function import count_ops
    q = Symbol("q", positive = True)
    m = Matrix([[-2, exp(-q), 1], [exp(q), -2, 1], [1, 1, -2]])
    assert count_ops(m.eigenvals(simplify=False)) > count_ops(m.eigenvals(simplify=True))
    assert count_ops(m.eigenvals(simplify=lambda x: x)) > count_ops(m.eigenvals(simplify=True))

    assert isinstance(m.eigenvals(simplify=True, multiple=False), dict)
    assert isinstance(m.eigenvals(simplify=True, multiple=True), list)
    assert isinstance(m.eigenvals(simplify=lambda x: x, multiple=False), dict)
    assert isinstance(m.eigenvals(simplify=lambda x: x, multiple=True), list)

def test_subs():
    assert Matrix([[1, x], [x, 4]]).subs(x, 5) == Matrix([[1, 5], [5, 4]])
    assert Matrix([[x, 2], [x + y, 4]]).subs([[x, -1], [y, -2]]) == \
        Matrix([[-1, 2], [-3, 4]])
    assert Matrix([[x, 2], [x + y, 4]]).subs([(x, -1), (y, -2)]) == \
        Matrix([[-1, 2], [-3, 4]])
    assert Matrix([[x, 2], [x + y, 4]]).subs({x: -1, y: -2}) == \
        Matrix([[-1, 2], [-3, 4]])
    assert Matrix([x*y]).subs({x: y - 1, y: x - 1}, simultaneous=True) == \
        Matrix([(x - 1)*(y - 1)])

    for cls in classes:
        assert Matrix([[2, 0], [0, 2]]) == cls.eye(2).subs(1, 2)

def test_xreplace():
    assert Matrix([[1, x], [x, 4]]).xreplace({x: 5}) == \
        Matrix([[1, 5], [5, 4]])
    assert Matrix([[x, 2], [x + y, 4]]).xreplace({x: -1, y: -2}) == \
        Matrix([[-1, 2], [-3, 4]])
    for cls in classes:
        assert Matrix([[2, 0], [0, 2]]) == cls.eye(2).xreplace({1: 2})

def test_simplify():
    n = Symbol('n')
    f = Function('f')

    M = Matrix([[            1/x + 1/y,                 (x + x*y) / x  ],
                [ (f(x) + y*f(x))/f(x), 2 * (1/n - cos(n * pi)/n) / pi ]])
    M.simplify()
    assert M == Matrix([[ (x + y)/(x * y),                        1 + y ],
                        [           1 + y, 2*((1 - 1*cos(pi*n))/(pi*n)) ]])
    eq = (1 + x)**2
    M = Matrix([[eq]])
    M.simplify()
    assert M == Matrix([[eq]])
    M.simplify(ratio=oo) == M
    assert M == Matrix([[eq.simplify(ratio=oo)]])


def test_transpose():
    M = Matrix([[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]])
    assert M.T == Matrix( [ [1, 1],
                            [2, 2],
                            [3, 3],
                            [4, 4],
                            [5, 5],
                            [6, 6],
                            [7, 7],
                            [8, 8],
                            [9, 9],
                            [0, 0] ])
    assert M.T.T == M
    assert M.T == M.transpose()


def test_conjugate():
    M = Matrix([[0, I, 5],
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


def test_conj_dirac():
    raises(AttributeError, lambda: eye(3).D)

    M = Matrix([[1, I, I, I],
                [0, 1, I, I],
                [0, 0, 1, I],
                [0, 0, 0, 1]])

    assert M.D == Matrix([[ 1,  0,  0,  0],
                          [-I,  1,  0,  0],
                          [-I, -I, -1,  0],
                          [-I, -I,  I, -1]])


def test_trace():
    M = Matrix([[1, 0, 0],
                [0, 5, 0],
                [0, 0, 8]])
    assert M.trace() == 14


def test_shape():
    M = Matrix([[x, 0, 0],
                [0, y, 0]])
    assert M.shape == (2, 3)


def test_col_row_op():
    M = Matrix([[x, 0, 0],
                [0, y, 0]])
    M.row_op(1, lambda r, j: r + j + 1)
    assert M == Matrix([[x,     0, 0],
                        [1, y + 2, 3]])

    M.col_op(0, lambda c, j: c + y**j)
    assert M == Matrix([[x + 1,     0, 0],
                        [1 + y, y + 2, 3]])

    # neither row nor slice give copies that allow the original matrix to
    # be changed
    assert M.row(0) == Matrix([[x + 1, 0, 0]])
    r1 = M.row(0)
    r1[0] = 42
    assert M[0, 0] == x + 1
    r1 = M[0, :-1]  # also testing negative slice
    r1[0] = 42
    assert M[0, 0] == x + 1
    c1 = M.col(0)
    assert c1 == Matrix([x + 1, 1 + y])
    c1[0] = 0
    assert M[0, 0] == x + 1
    c1 = M[:, 0]
    c1[0] = 42
    assert M[0, 0] == x + 1


def test_zip_row_op():
    for cls in classes[:2]: # XXX: immutable matrices don't support row ops
        M = cls.eye(3)
        M.zip_row_op(1, 0, lambda v, u: v + 2*u)
        assert M == cls([[1, 0, 0],
                         [2, 1, 0],
                         [0, 0, 1]])

        M = cls.eye(3)*2
        M[0, 1] = -1
        M.zip_row_op(1, 0, lambda v, u: v + 2*u); M
        assert M == cls([[2, -1, 0],
                         [4,  0, 0],
                         [0,  0, 2]])

def test_issue_3950():
    m = Matrix([1, 2, 3])
    a = Matrix([1, 2, 3])
    b = Matrix([2, 2, 3])
    assert not (m in [])
    assert not (m in [1])
    assert m != 1
    assert m == a
    assert m != b


def test_issue_3981():
    class Index1(object):
        def __index__(self):
            return 1

    class Index2(object):
        def __index__(self):
            return 2
    index1 = Index1()
    index2 = Index2()

    m = Matrix([1, 2, 3])

    assert m[index2] == 3

    m[index2] = 5
    assert m[2] == 5

    m = Matrix([[1, 2, 3], [4, 5, 6]])
    assert m[index1, index2] == 6
    assert m[1, index2] == 6
    assert m[index1, 2] == 6

    m[index1, index2] = 4
    assert m[1, 2] == 4
    m[1, index2] = 6
    assert m[1, 2] == 6
    m[index1, 2] = 8
    assert m[1, 2] == 8


def test_evalf():
    a = Matrix([sqrt(5), 6])
    assert all(a.evalf()[i] == a[i].evalf() for i in range(2))
    assert all(a.evalf(2)[i] == a[i].evalf(2) for i in range(2))
    assert all(a.n(2)[i] == a[i].n(2) for i in range(2))


def test_is_symbolic():
    a = Matrix([[x, x], [x, x]])
    assert a.is_symbolic() is True
    a = Matrix([[1, 2, 3, 4], [5, 6, 7, 8]])
    assert a.is_symbolic() is False
    a = Matrix([[1, 2, 3, 4], [5, 6, x, 8]])
    assert a.is_symbolic() is True
    a = Matrix([[1, x, 3]])
    assert a.is_symbolic() is True
    a = Matrix([[1, 2, 3]])
    assert a.is_symbolic() is False
    a = Matrix([[1], [x], [3]])
    assert a.is_symbolic() is True
    a = Matrix([[1], [2], [3]])
    assert a.is_symbolic() is False


def test_is_upper():
    a = Matrix([[1, 2, 3]])
    assert a.is_upper is True
    a = Matrix([[1], [2], [3]])
    assert a.is_upper is False
    a = zeros(4, 2)
    assert a.is_upper is True


def test_is_lower():
    a = Matrix([[1, 2, 3]])
    assert a.is_lower is False
    a = Matrix([[1], [2], [3]])
    assert a.is_lower is True


def test_is_nilpotent():
    a = Matrix(4, 4, [0, 2, 1, 6, 0, 0, 1, 2, 0, 0, 0, 3, 0, 0, 0, 0])
    assert a.is_nilpotent()
    a = Matrix([[1, 0], [0, 1]])
    assert not a.is_nilpotent()
    a = Matrix([])
    assert a.is_nilpotent()


def test_zeros_ones_fill():
    n, m = 3, 5

    a = zeros(n, m)
    a.fill( 5 )

    b = 5 * ones(n, m)

    assert a == b
    assert a.rows == b.rows == 3
    assert a.cols == b.cols == 5
    assert a.shape == b.shape == (3, 5)
    assert zeros(2) == zeros(2, 2)
    assert ones(2) == ones(2, 2)
    assert zeros(2, 3) == Matrix(2, 3, [0]*6)
    assert ones(2, 3) == Matrix(2, 3, [1]*6)


def test_empty_zeros():
    a = zeros(0)
    assert a == Matrix()
    a = zeros(0, 2)
    assert a.rows == 0
    assert a.cols == 2
    a = zeros(2, 0)
    assert a.rows == 2
    assert a.cols == 0


def test_issue_3749():
    a = Matrix([[x**2, x*y], [x*sin(y), x*cos(y)]])
    assert a.diff(x) == Matrix([[2*x, y], [sin(y), cos(y)]])
    assert Matrix([
        [x, -x, x**2],
        [exp(x), 1/x - exp(-x), x + 1/x]]).limit(x, oo) == \
        Matrix([[oo, -oo, oo], [oo, 0, oo]])
    assert Matrix([
        [(exp(x) - 1)/x, 2*x + y*x, x**x ],
        [1/x, abs(x), abs(sin(x + 1))]]).limit(x, 0) == \
        Matrix([[1, 0, 1], [oo, 0, sin(1)]])
    assert a.integrate(x) == Matrix([
        [Rational(1, 3)*x**3, y*x**2/2],
        [x**2*sin(y)/2, x**2*cos(y)/2]])


def test_inv_iszerofunc():
    A = eye(4)
    A.col_swap(0, 1)
    for method in "GE", "LU":
        assert A.inv(method=method, iszerofunc=lambda x: x == 0) == \
            A.inv(method="ADJ")


def test_jacobian_metrics():
    rho, phi = symbols("rho,phi")
    X = Matrix([rho*cos(phi), rho*sin(phi)])
    Y = Matrix([rho, phi])
    J = X.jacobian(Y)
    assert J == X.jacobian(Y.T)
    assert J == (X.T).jacobian(Y)
    assert J == (X.T).jacobian(Y.T)
    g = J.T*eye(J.shape[0])*J
    g = g.applyfunc(trigsimp)
    assert g == Matrix([[1, 0], [0, rho**2]])


def test_jacobian2():
    rho, phi = symbols("rho,phi")
    X = Matrix([rho*cos(phi), rho*sin(phi), rho**2])
    Y = Matrix([rho, phi])
    J = Matrix([
        [cos(phi), -rho*sin(phi)],
        [sin(phi),  rho*cos(phi)],
        [   2*rho,             0],
    ])
    assert X.jacobian(Y) == J


def test_issue_4564():
    X = Matrix([exp(x + y + z), exp(x + y + z), exp(x + y + z)])
    Y = Matrix([x, y, z])
    for i in range(1, 3):
        for j in range(1, 3):
            X_slice = X[:i, :]
            Y_slice = Y[:j, :]
            J = X_slice.jacobian(Y_slice)
            assert J.rows == i
            assert J.cols == j
            for k in range(j):
                assert J[:, k] == X_slice


def test_nonvectorJacobian():
    X = Matrix([[exp(x + y + z), exp(x + y + z)],
                [exp(x + y + z), exp(x + y + z)]])
    raises(TypeError, lambda: X.jacobian(Matrix([x, y, z])))
    X = X[0, :]
    Y = Matrix([[x, y], [x, z]])
    raises(TypeError, lambda: X.jacobian(Y))
    raises(TypeError, lambda: X.jacobian(Matrix([ [x, y], [x, z] ])))


def test_vec():
    m = Matrix([[1, 3], [2, 4]])
    m_vec = m.vec()
    assert m_vec.cols == 1
    for i in range(4):
        assert m_vec[i] == i + 1


def test_vech():
    m = Matrix([[1, 2], [2, 3]])
    m_vech = m.vech()
    assert m_vech.cols == 1
    for i in range(3):
        assert m_vech[i] == i + 1
    m_vech = m.vech(diagonal=False)
    assert m_vech[0] == 2

    m = Matrix([[1, x*(x + y)], [y*x + x**2, 1]])
    m_vech = m.vech(diagonal=False)
    assert m_vech[0] == x*(x + y)

    m = Matrix([[1, x*(x + y)], [y*x, 1]])
    m_vech = m.vech(diagonal=False, check_symmetry=False)
    assert m_vech[0] == y*x


def test_vech_errors():
    m = Matrix([[1, 3]])
    raises(ShapeError, lambda: m.vech())
    m = Matrix([[1, 3], [2, 4]])
    raises(ValueError, lambda: m.vech())
    raises(ShapeError, lambda: Matrix([ [1, 3] ]).vech())
    raises(ValueError, lambda: Matrix([ [1, 3], [2, 4] ]).vech())


def test_diag():
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
    assert diag(1, [2, 3], [[4, 5]]) == Matrix([
        [1, 0, 0, 0],
        [0, 2, 0, 0],
        [0, 3, 0, 0],
        [0, 0, 4, 5]])


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
    assert diag(a, b, b).get_diag_blocks() == [a, b, b]
    assert diag(a, b, c).get_diag_blocks() == [a, b, c]
    assert diag(a, c, b).get_diag_blocks() == [a, c, b]
    assert diag(c, c, b).get_diag_blocks() == [c, c, b]


def test_inv_block():
    a = Matrix([[1, 2], [2, 3]])
    b = Matrix([[3, x], [y, 3]])
    c = Matrix([[3, x, 3], [y, 3, z], [x, y, z]])
    A = diag(a, b, b)
    assert A.inv(try_block_diag=True) == diag(a.inv(), b.inv(), b.inv())
    A = diag(a, b, c)
    assert A.inv(try_block_diag=True) == diag(a.inv(), b.inv(), c.inv())
    A = diag(a, c, b)
    assert A.inv(try_block_diag=True) == diag(a.inv(), c.inv(), b.inv())
    A = diag(a, a, b, a, c, a)
    assert A.inv(try_block_diag=True) == diag(
        a.inv(), a.inv(), b.inv(), a.inv(), c.inv(), a.inv())
    assert A.inv(try_block_diag=True, method="ADJ") == diag(
        a.inv(method="ADJ"), a.inv(method="ADJ"), b.inv(method="ADJ"),
        a.inv(method="ADJ"), c.inv(method="ADJ"), a.inv(method="ADJ"))


def test_creation_args():
    """
    Check that matrix dimensions can be specified using any reasonable type
    (see issue 4614).
    """
    raises(ValueError, lambda: zeros(3, -1))
    raises(TypeError, lambda: zeros(1, 2, 3, 4))
    assert zeros(long(3)) == zeros(3)
    assert zeros(Integer(3)) == zeros(3)
    raises(ValueError, lambda: zeros(3.))
    assert eye(long(3)) == eye(3)
    assert eye(Integer(3)) == eye(3)
    raises(ValueError, lambda: eye(3.))
    assert ones(long(3), Integer(4)) == ones(3, 4)
    raises(TypeError, lambda: Matrix(5))
    raises(TypeError, lambda: Matrix(1, 2))


def test_diagonal_symmetrical():
    m = Matrix(2, 2, [0, 1, 1, 0])
    assert not m.is_diagonal()
    assert m.is_symmetric()
    assert m.is_symmetric(simplify=False)

    m = Matrix(2, 2, [1, 0, 0, 1])
    assert m.is_diagonal()

    m = diag(1, 2, 3)
    assert m.is_diagonal()
    assert m.is_symmetric()

    m = Matrix(3, 3, [1, 0, 0, 0, 2, 0, 0, 0, 3])
    assert m == diag(1, 2, 3)

    m = Matrix(2, 3, zeros(2, 3))
    assert not m.is_symmetric()
    assert m.is_diagonal()

    m = Matrix(((5, 0), (0, 6), (0, 0)))
    assert m.is_diagonal()

    m = Matrix(((5, 0, 0), (0, 6, 0)))
    assert m.is_diagonal()

    m = Matrix(3, 3, [1, x**2 + 2*x + 1, y, (x + 1)**2, 2, 0, y, 0, 3])
    assert m.is_symmetric()
    assert not m.is_symmetric(simplify=False)
    assert m.expand().is_symmetric(simplify=False)


def test_diagonalization():
    m = Matrix(3, 2, [-3, 1, -3, 20, 3, 10])
    assert not m.is_diagonalizable()
    assert not m.is_symmetric()
    raises(NonSquareMatrixError, lambda: m.diagonalize())

    # diagonalizable
    m = diag(1, 2, 3)
    (P, D) = m.diagonalize()
    assert P == eye(3)
    assert D == m

    m = Matrix(2, 2, [0, 1, 1, 0])
    assert m.is_symmetric()
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D

    m = Matrix(2, 2, [1, 0, 0, 3])
    assert m.is_symmetric()
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D
    assert P == eye(2)
    assert D == m

    m = Matrix(2, 2, [1, 1, 0, 0])
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D

    m = Matrix(3, 3, [1, 2, 0, 0, 3, 0, 2, -4, 2])
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D
    for i in P:
        assert i.as_numer_denom()[1] == 1

    m = Matrix(2, 2, [1, 0, 0, 0])
    assert m.is_diagonal()
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D
    assert P == Matrix([[0, 1], [1, 0]])

    # diagonalizable, complex only
    m = Matrix(2, 2, [0, 1, -1, 0])
    assert not m.is_diagonalizable(True)
    raises(MatrixError, lambda: m.diagonalize(True))
    assert m.is_diagonalizable()
    (P, D) = m.diagonalize()
    assert P.inv() * m * P == D

    # not diagonalizable
    m = Matrix(2, 2, [0, 1, 0, 0])
    assert not m.is_diagonalizable()
    raises(MatrixError, lambda: m.diagonalize())

    m = Matrix(3, 3, [-3, 1, -3, 20, 3, 10, 2, -2, 4])
    assert not m.is_diagonalizable()
    raises(MatrixError, lambda: m.diagonalize())

    # symbolic
    a, b, c, d = symbols('a b c d')
    m = Matrix(2, 2, [a, c, c, b])
    assert m.is_symmetric()
    assert m.is_diagonalizable()


def test_issue_15887():
    # Mutable matrix should not use cache
    a = MutableDenseMatrix([[0, 1], [1, 0]])
    assert a.is_diagonalizable() is True
    a[1, 0] = 0
    assert a.is_diagonalizable() is False

    a = MutableDenseMatrix([[0, 1], [1, 0]])
    a.diagonalize()
    a[1, 0] = 0
    raises(MatrixError, lambda: a.diagonalize())

    # Test deprecated cache and kwargs
    with warns_deprecated_sympy():
        a._cache_eigenvects

    with warns_deprecated_sympy():
        a._cache_is_diagonalizable

    with warns_deprecated_sympy():
        a.is_diagonalizable(clear_cache=True)

    with warns_deprecated_sympy():
        a.is_diagonalizable(clear_subproducts=True)


@XFAIL
def test_eigen_vects():
    m = Matrix(2, 2, [1, 0, 0, I])
    raises(NotImplementedError, lambda: m.is_diagonalizable(True))
    # !!! bug because of eigenvects() or roots(x**2 + (-1 - I)*x + I, x)
    # see issue 5292
    assert not m.is_diagonalizable(True)
    raises(MatrixError, lambda: m.diagonalize(True))
    (P, D) = m.diagonalize(True)


def test_jordan_form():

    m = Matrix(3, 2, [-3, 1, -3, 20, 3, 10])
    raises(NonSquareMatrixError, lambda: m.jordan_form())

    # diagonalizable
    m = Matrix(3, 3, [7, -12, 6, 10, -19, 10, 12, -24, 13])
    Jmust = Matrix(3, 3, [-1, 0, 0, 0, 1, 0, 0, 0, 1])
    P, J = m.jordan_form()
    assert Jmust == J
    assert Jmust == m.diagonalize()[1]

    # m = Matrix(3, 3, [0, 6, 3, 1, 3, 1, -2, 2, 1])
    # m.jordan_form()  # very long
    # m.jordan_form()  #

    # diagonalizable, complex only

    # Jordan cells
    # complexity: one of eigenvalues is zero
    m = Matrix(3, 3, [0, 1, 0, -4, 4, 0, -2, 1, 2])
    # The blocks are ordered according to the value of their eigenvalues,
    # in order to make the matrix compatible with .diagonalize()
    Jmust = Matrix(3, 3, [2, 1, 0, 0, 2, 0, 0, 0, 2])
    P, J = m.jordan_form()
    assert Jmust == J

    # complexity: all of eigenvalues are equal
    m = Matrix(3, 3, [2, 6, -15, 1, 1, -5, 1, 2, -6])
    # Jmust = Matrix(3, 3, [-1, 0, 0, 0, -1, 1, 0, 0, -1])
    # same here see 1456ff
    Jmust = Matrix(3, 3, [-1, 1, 0, 0, -1, 0, 0, 0, -1])
    P, J = m.jordan_form()
    assert Jmust == J

    # complexity: two of eigenvalues are zero
    m = Matrix(3, 3, [4, -5, 2, 5, -7, 3, 6, -9, 4])
    Jmust = Matrix(3, 3, [0, 1, 0, 0, 0, 0, 0, 0, 1])
    P, J = m.jordan_form()
    assert Jmust == J

    m = Matrix(4, 4, [6, 5, -2, -3, -3, -1, 3, 3, 2, 1, -2, -3, -1, 1, 5, 5])
    Jmust = Matrix(4, 4, [2, 1, 0, 0,
                          0, 2, 0, 0,
              0, 0, 2, 1,
              0, 0, 0, 2]
              )
    P, J = m.jordan_form()
    assert Jmust == J

    m = Matrix(4, 4, [6, 2, -8, -6, -3, 2, 9, 6, 2, -2, -8, -6, -1, 0, 3, 4])
    # Jmust = Matrix(4, 4, [2, 0, 0, 0, 0, 2, 1, 0, 0, 0, 2, 0, 0, 0, 0, -2])
    # same here see 1456ff
    Jmust = Matrix(4, 4, [-2, 0, 0, 0,
                           0, 2, 1, 0,
                           0, 0, 2, 0,
                           0, 0, 0, 2])
    P, J = m.jordan_form()
    assert Jmust == J

    m = Matrix(4, 4, [5, 4, 2, 1, 0, 1, -1, -1, -1, -1, 3, 0, 1, 1, -1, 2])
    assert not m.is_diagonalizable()
    Jmust = Matrix(4, 4, [1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 4, 1, 0, 0, 0, 4])
    P, J = m.jordan_form()
    assert Jmust == J

    # checking for maximum precision to remain unchanged
    m = Matrix([[Float('1.0', precision=110), Float('2.0', precision=110)],
                [Float('3.14159265358979323846264338327', precision=110), Float('4.0', precision=110)]])
    P, J = m.jordan_form()
    for term in J._mat:
        if isinstance(term, Float):
            assert term._prec == 110


def test_jordan_form_complex_issue_9274():
    A = Matrix([[ 2,  4,  1,  0],
                [-4,  2,  0,  1],
                [ 0,  0,  2,  4],
                [ 0,  0, -4,  2]])
    p = 2 - 4*I;
    q = 2 + 4*I;
    Jmust1 = Matrix([[p, 1, 0, 0],
                     [0, p, 0, 0],
                     [0, 0, q, 1],
                     [0, 0, 0, q]])
    Jmust2 = Matrix([[q, 1, 0, 0],
                     [0, q, 0, 0],
                     [0, 0, p, 1],
                     [0, 0, 0, p]])
    P, J = A.jordan_form()
    assert J == Jmust1 or J == Jmust2
    assert simplify(P*J*P.inv()) == A

def test_issue_10220():
    # two non-orthogonal Jordan blocks with eigenvalue 1
    M = Matrix([[1, 0, 0, 1],
                [0, 1, 1, 0],
                [0, 0, 1, 1],
                [0, 0, 0, 1]])
    P, J = M.jordan_form()
    assert P == Matrix([[0, 1, 0, 1],
                        [1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0]])
    assert J == Matrix([
                        [1, 1, 0, 0],
                        [0, 1, 1, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])

def test_jordan_form_issue_15858():
    A = Matrix([
        [1, 1, 1, 0],
        [-2, -1, 0, -1],
        [0, 0, -1, -1],
        [0, 0, 2, 1]])
    (P, J) = A.jordan_form()
    assert simplify(P) == Matrix([
        [-I, -I/2, I, I/2],
        [-1 + I, 0, -1 - I, 0],
        [0, I*(-1 + I)/2, 0, I*(1 + I)/2],
        [0, 1, 0, 1]])
    assert J == Matrix([
        [-I, 1, 0, 0],
        [0, -I, 0, 0],
        [0, 0, I, 1],
        [0, 0, 0, I]])

def test_Matrix_berkowitz_charpoly():
    UA, K_i, K_w = symbols('UA K_i K_w')

    A = Matrix([[-K_i - UA + K_i**2/(K_i + K_w),       K_i*K_w/(K_i + K_w)],
                [           K_i*K_w/(K_i + K_w), -K_w + K_w**2/(K_i + K_w)]])

    charpoly = A.charpoly(x)

    assert charpoly == \
        Poly(x**2 + (K_i*UA + K_w*UA + 2*K_i*K_w)/(K_i + K_w)*x +
        K_i*K_w*UA/(K_i + K_w), x, domain='ZZ(K_i,K_w,UA)')

    assert type(charpoly) is PurePoly

    A = Matrix([[1, 3], [2, 0]])
    assert A.charpoly() == A.charpoly(x) == PurePoly(x**2 - x - 6)

    A = Matrix([[1, 2], [x, 0]])
    p = A.charpoly(x)
    assert p.gen != x
    assert p.as_expr().subs(p.gen, x) == x**2 - 3*x


def test_exp():
    m = Matrix([[3, 4], [0, -2]])
    m_exp = Matrix([[exp(3), -4*exp(-2)/5 + 4*exp(3)/5], [0, exp(-2)]])
    assert m.exp() == m_exp
    assert exp(m) == m_exp

    m = Matrix([[1, 0], [0, 1]])
    assert m.exp() == Matrix([[E, 0], [0, E]])
    assert exp(m) == Matrix([[E, 0], [0, E]])

    m = Matrix([[1, -1], [1, 1]])
    assert m.exp() == Matrix([[E*cos(1), -E*sin(1)], [E*sin(1), E*cos(1)]])


def test_has():
    A = Matrix(((x, y), (2, 3)))
    assert A.has(x)
    assert not A.has(z)
    assert A.has(Symbol)

    A = A.subs(x, 2)
    assert not A.has(x)

def test_LUdecomposition_Simple_iszerofunc():
    # Test if callable passed to matrices.LUdecomposition_Simple() as iszerofunc keyword argument is used inside
    # matrices.LUdecomposition_Simple()
    magic_string = "I got passed in!"
    def goofyiszero(value):
        raise ValueError(magic_string)

    try:
        lu, p = Matrix([[1, 0], [0, 1]]).LUdecomposition_Simple(iszerofunc=goofyiszero)
    except ValueError as err:
        assert magic_string == err.args[0]
        return

    assert False

def test_LUdecomposition_iszerofunc():
    # Test if callable passed to matrices.LUdecomposition() as iszerofunc keyword argument is used inside
    # matrices.LUdecomposition_Simple()
    magic_string = "I got passed in!"
    def goofyiszero(value):
        raise ValueError(magic_string)

    try:
        l, u, p = Matrix([[1, 0], [0, 1]]).LUdecomposition(iszerofunc=goofyiszero)
    except ValueError as err:
        assert magic_string == err.args[0]
        return

    assert False

def test_find_reasonable_pivot_naive_finds_guaranteed_nonzero1():
    # Test if matrices._find_reasonable_pivot_naive()
    # finds a guaranteed non-zero pivot when the
    # some of the candidate pivots are symbolic expressions.
    # Keyword argument: simpfunc=None indicates that no simplifications
    # should be performed during the search.
    x = Symbol('x')
    column = Matrix(3, 1, [x, cos(x)**2 + sin(x)**2, Rational(1, 2)])
    pivot_offset, pivot_val, pivot_assumed_nonzero, simplified =\
        _find_reasonable_pivot_naive(column)
    assert pivot_val == Rational(1, 2)

def test_find_reasonable_pivot_naive_finds_guaranteed_nonzero2():
    # Test if matrices._find_reasonable_pivot_naive()
    # finds a guaranteed non-zero pivot when the
    # some of the candidate pivots are symbolic expressions.
    # Keyword argument: simpfunc=_simplify indicates that the search
    # should attempt to simplify candidate pivots.
    x = Symbol('x')
    column = Matrix(3, 1,
                    [x,
                     cos(x)**2+sin(x)**2+x**2,
                     cos(x)**2+sin(x)**2])
    pivot_offset, pivot_val, pivot_assumed_nonzero, simplified =\
        _find_reasonable_pivot_naive(column, simpfunc=_simplify)
    assert pivot_val == 1

def test_find_reasonable_pivot_naive_simplifies():
    # Test if matrices._find_reasonable_pivot_naive()
    # simplifies candidate pivots, and reports
    # their offsets correctly.
    x = Symbol('x')
    column = Matrix(3, 1,
                    [x,
                     cos(x)**2+sin(x)**2+x,
                     cos(x)**2+sin(x)**2])
    pivot_offset, pivot_val, pivot_assumed_nonzero, simplified =\
        _find_reasonable_pivot_naive(column, simpfunc=_simplify)

    assert len(simplified) == 2
    assert simplified[0][0] == 1
    assert simplified[0][1] == 1+x
    assert simplified[1][0] == 2
    assert simplified[1][1] == 1

def test_errors():
    raises(ValueError, lambda: Matrix([[1, 2], [1]]))
    raises(IndexError, lambda: Matrix([[1, 2]])[1.2, 5])
    raises(IndexError, lambda: Matrix([[1, 2]])[1, 5.2])
    raises(ValueError, lambda: randMatrix(3, c=4, symmetric=True))
    raises(ValueError, lambda: Matrix([1, 2]).reshape(4, 6))
    raises(ShapeError,
        lambda: Matrix([[1, 2], [3, 4]]).copyin_matrix([1, 0], Matrix([1, 2])))
    raises(TypeError, lambda: Matrix([[1, 2], [3, 4]]).copyin_list([0,
           1], set([])))
    raises(NonSquareMatrixError, lambda: Matrix([[1, 2, 3], [2, 3, 0]]).inv())
    raises(ShapeError,
        lambda: Matrix(1, 2, [1, 2]).row_join(Matrix([[1, 2], [3, 4]])))
    raises(
        ShapeError, lambda: Matrix([1, 2]).col_join(Matrix([[1, 2], [3, 4]])))
    raises(ShapeError, lambda: Matrix([1]).row_insert(1, Matrix([[1,
           2], [3, 4]])))
    raises(ShapeError, lambda: Matrix([1]).col_insert(1, Matrix([[1,
           2], [3, 4]])))
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).trace())
    raises(TypeError, lambda: Matrix([1]).applyfunc(1))
    raises(ShapeError, lambda: Matrix([1]).LUsolve(Matrix([[1, 2], [3, 4]])))
    raises(ValueError, lambda: Matrix([[1, 2], [3, 4]]).minor(4, 5))
    raises(ValueError, lambda: Matrix([[1, 2], [3, 4]]).minor_submatrix(4, 5))
    raises(TypeError, lambda: Matrix([1, 2, 3]).cross(1))
    raises(TypeError, lambda: Matrix([1, 2, 3]).dot(1))
    raises(ShapeError, lambda: Matrix([1, 2, 3]).dot(Matrix([1, 2])))
    raises(ShapeError, lambda: Matrix([1, 2]).dot([]))
    raises(TypeError, lambda: Matrix([1, 2]).dot('a'))
    with warns_deprecated_sympy():
        Matrix([[1, 2], [3, 4]]).dot(Matrix([[4, 3], [1, 2]]))
    raises(ShapeError, lambda: Matrix([1, 2]).dot([1, 2, 3]))
    raises(NonSquareMatrixError, lambda: Matrix([1, 2, 3]).exp())
    raises(ShapeError, lambda: Matrix([[1, 2], [3, 4]]).normalized())
    raises(ValueError, lambda: Matrix([1, 2]).inv(method='not a method'))
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).inverse_GE())
    raises(ValueError, lambda: Matrix([[1, 2], [1, 2]]).inverse_GE())
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).inverse_ADJ())
    raises(ValueError, lambda: Matrix([[1, 2], [1, 2]]).inverse_ADJ())
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).inverse_LU())
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).is_nilpotent())
    raises(NonSquareMatrixError, lambda: Matrix([1, 2]).det())
    raises(ValueError,
        lambda: Matrix([[1, 2], [3, 4]]).det(method='Not a real method'))
    raises(ValueError,
        lambda: Matrix([[1, 2, 3, 4], [5, 6, 7, 8],
        [9, 10, 11, 12], [13, 14, 15, 16]]).det(iszerofunc="Not function"))
    raises(ValueError,
        lambda: Matrix([[1, 2, 3, 4], [5, 6, 7, 8],
        [9, 10, 11, 12], [13, 14, 15, 16]]).det(iszerofunc=False))
    raises(ValueError,
        lambda: hessian(Matrix([[1, 2], [3, 4]]), Matrix([[1, 2], [2, 1]])))
    raises(ValueError, lambda: hessian(Matrix([[1, 2], [3, 4]]), []))
    raises(ValueError, lambda: hessian(Symbol('x')**2, 'a'))
    raises(IndexError, lambda: eye(3)[5, 2])
    raises(IndexError, lambda: eye(3)[2, 5])
    M = Matrix(((1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16)))
    raises(ValueError, lambda: M.det('method=LU_decomposition()'))
    V = Matrix([[10, 10, 10]])
    M = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(ValueError, lambda: M.row_insert(4.7, V))
    M = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(ValueError, lambda: M.col_insert(-4.2, V))

def test_len():
    assert len(Matrix()) == 0
    assert len(Matrix([[1, 2]])) == len(Matrix([[1], [2]])) == 2
    assert len(Matrix(0, 2, lambda i, j: 0)) == \
        len(Matrix(2, 0, lambda i, j: 0)) == 0
    assert len(Matrix([[0, 1, 2], [3, 4, 5]])) == 6
    assert Matrix([1]) == Matrix([[1]])
    assert not Matrix()
    assert Matrix() == Matrix([])


def test_integrate():
    A = Matrix(((1, 4, x), (y, 2, 4), (10, 5, x**2)))
    assert A.integrate(x) == \
        Matrix(((x, 4*x, x**2/2), (x*y, 2*x, 4*x), (10*x, 5*x, x**3/3)))
    assert A.integrate(y) == \
        Matrix(((y, 4*y, x*y), (y**2/2, 2*y, 4*y), (10*y, 5*y, y*x**2)))


def test_limit():
    A = Matrix(((1, 4, sin(x)/x), (y, 2, 4), (10, 5, x**2 + 1)))
    assert A.limit(x, 0) == Matrix(((1, 4, 1), (y, 2, 4), (10, 5, 1)))


def test_diff():
    A = MutableDenseMatrix(((1, 4, x), (y, 2, 4), (10, 5, x**2 + 1)))
    assert isinstance(A.diff(x), type(A))
    assert A.diff(x) == MutableDenseMatrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))
    assert A.diff(y) == MutableDenseMatrix(((0, 0, 0), (1, 0, 0), (0, 0, 0)))

    assert diff(A, x) == MutableDenseMatrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))
    assert diff(A, y) == MutableDenseMatrix(((0, 0, 0), (1, 0, 0), (0, 0, 0)))

    A_imm = A.as_immutable()
    assert isinstance(A_imm.diff(x), type(A_imm))
    assert A_imm.diff(x) == ImmutableDenseMatrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))
    assert A_imm.diff(y) == ImmutableDenseMatrix(((0, 0, 0), (1, 0, 0), (0, 0, 0)))

    assert diff(A_imm, x) == ImmutableDenseMatrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))
    assert diff(A_imm, y) == ImmutableDenseMatrix(((0, 0, 0), (1, 0, 0), (0, 0, 0)))


def test_diff_by_matrix():

    # Derive matrix by matrix:

    A = MutableDenseMatrix([[x, y], [z, t]])
    assert A.diff(A) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])
    assert diff(A, A) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])

    A_imm = A.as_immutable()
    assert A_imm.diff(A_imm) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])
    assert diff(A_imm, A_imm) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])

    # Derive a constant matrix:
    assert A.diff(a) == MutableDenseMatrix([[0, 0], [0, 0]])

    B = ImmutableDenseMatrix([a, b])
    assert A.diff(B) == Array.zeros(2, 1, 2, 2)
    assert A.diff(A) == Array([[[[1, 0], [0, 0]], [[0, 1], [0, 0]]], [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]])

    # Test diff with tuples:

    dB = B.diff([[a, b]])
    assert dB.shape == (2, 2, 1)
    assert dB == Array([[[1], [0]], [[0], [1]]])

    f = Function("f")
    fxyz = f(x, y, z)
    assert fxyz.diff([[x, y, z]]) == Array([fxyz.diff(x), fxyz.diff(y), fxyz.diff(z)])
    assert fxyz.diff(([x, y, z], 2)) == Array([
        [fxyz.diff(x, 2), fxyz.diff(x, y), fxyz.diff(x, z)],
        [fxyz.diff(x, y), fxyz.diff(y, 2), fxyz.diff(y, z)],
        [fxyz.diff(x, z), fxyz.diff(z, y), fxyz.diff(z, 2)],
    ])

    expr = sin(x)*exp(y)
    assert expr.diff([[x, y]]) == Array([cos(x)*exp(y), sin(x)*exp(y)])
    assert expr.diff(y, ((x, y),)) == Array([cos(x)*exp(y), sin(x)*exp(y)])
    assert expr.diff(x, ((x, y),)) == Array([-sin(x)*exp(y), cos(x)*exp(y)])
    assert expr.diff(((y, x),), [[x, y]]) == Array([[cos(x)*exp(y), -sin(x)*exp(y)], [sin(x)*exp(y), cos(x)*exp(y)]])

    # Test different notations:

    fxyz.diff(x).diff(y).diff(x) == fxyz.diff(((x, y, z),), 3)[0, 1, 0]
    fxyz.diff(z).diff(y).diff(x) == fxyz.diff(((x, y, z),), 3)[2, 1, 0]
    fxyz.diff([[x, y, z]], ((z, y, x),)) == Array([[fxyz.diff(i).diff(j) for i in (x, y, z)] for j in (z, y, x)])

    # Test scalar derived by matrix remains matrix:
    res = x.diff(Matrix([[x, y]]))
    assert isinstance(res, ImmutableDenseMatrix)
    assert res == Matrix([[1, 0]])
    res = (x**3).diff(Matrix([[x, y]]))
    assert isinstance(res, ImmutableDenseMatrix)
    assert res == Matrix([[3*x**2, 0]])


def test_getattr():
    A = Matrix(((1, 4, x), (y, 2, 4), (10, 5, x**2 + 1)))
    raises(AttributeError, lambda: A.nonexistantattribute)
    assert getattr(A, 'diff')(x) == Matrix(((0, 0, 1), (0, 0, 0), (0, 0, 2*x)))


def test_hessenberg():
    A = Matrix([[3, 4, 1], [2, 4, 5], [0, 1, 2]])
    assert A.is_upper_hessenberg
    A = A.T
    assert A.is_lower_hessenberg
    A[0, -1] = 1
    assert A.is_lower_hessenberg is False

    A = Matrix([[3, 4, 1], [2, 4, 5], [3, 1, 2]])
    assert not A.is_upper_hessenberg

    A = zeros(5, 2)
    assert A.is_upper_hessenberg


def test_cholesky():
    raises(NonSquareMatrixError, lambda: Matrix((1, 2)).cholesky())
    raises(ValueError, lambda: Matrix(((1, 2), (3, 4))).cholesky())
    raises(ValueError, lambda: Matrix(((5 + I, 0), (0, 1))).cholesky())
    raises(ValueError, lambda: Matrix(((1, 5), (5, 1))).cholesky())
    raises(ValueError, lambda: Matrix(((1, 2), (3, 4))).cholesky(hermitian=False))
    assert Matrix(((5 + I, 0), (0, 1))).cholesky(hermitian=False) == Matrix([
        [sqrt(5 + I), 0], [0, 1]])
    A = Matrix(((1, 5), (5, 1)))
    L = A.cholesky(hermitian=False)
    assert L == Matrix([[1, 0], [5, 2*sqrt(6)*I]])
    assert L*L.T == A
    A = Matrix(((25, 15, -5), (15, 18, 0), (-5, 0, 11)))
    L = A.cholesky()
    assert L * L.T == A
    assert L.is_lower
    assert L == Matrix([[5, 0, 0], [3, 3, 0], [-1, 1, 3]])
    A = Matrix(((4, -2*I, 2 + 2*I), (2*I, 2, -1 + I), (2 - 2*I, -1 - I, 11)))
    assert A.cholesky() == Matrix(((2, 0, 0), (I, 1, 0), (1 - I, 0, 3)))


def test_LDLdecomposition():
    raises(NonSquareMatrixError, lambda: Matrix((1, 2)).LDLdecomposition())
    raises(ValueError, lambda: Matrix(((1, 2), (3, 4))).LDLdecomposition())
    raises(ValueError, lambda: Matrix(((5 + I, 0), (0, 1))).LDLdecomposition())
    raises(ValueError, lambda: Matrix(((1, 5), (5, 1))).LDLdecomposition())
    raises(ValueError, lambda: Matrix(((1, 2), (3, 4))).LDLdecomposition(hermitian=False))
    A = Matrix(((1, 5), (5, 1)))
    L, D = A.LDLdecomposition(hermitian=False)
    assert L * D * L.T == A
    A = Matrix(((25, 15, -5), (15, 18, 0), (-5, 0, 11)))
    L, D = A.LDLdecomposition()
    assert L * D * L.T == A
    assert L.is_lower
    assert L == Matrix([[1, 0, 0], [ S(3)/5, 1, 0], [S(-1)/5, S(1)/3, 1]])
    assert D.is_diagonal()
    assert D == Matrix([[25, 0, 0], [0, 9, 0], [0, 0, 9]])
    A = Matrix(((4, -2*I, 2 + 2*I), (2*I, 2, -1 + I), (2 - 2*I, -1 - I, 11)))
    L, D = A.LDLdecomposition()
    assert expand_mul(L * D * L.H) == A
    assert L == Matrix(((1, 0, 0), (I/2, 1, 0), (S(1)/2 - I/2, 0, 1)))
    assert D == Matrix(((4, 0, 0), (0, 1, 0), (0, 0, 9)))


def test_cholesky_solve():
    A = Matrix([[2, 3, 5],
                [3, 6, 2],
                [8, 3, 6]])
    x = Matrix(3, 1, [3, 7, 5])
    b = A*x
    soln = A.cholesky_solve(b)
    assert soln == x
    A = Matrix([[0, -1, 2],
                [5, 10, 7],
                [8,  3, 4]])
    x = Matrix(3, 1, [-1, 2, 5])
    b = A*x
    soln = A.cholesky_solve(b)
    assert soln == x
    A = Matrix(((1, 5), (5, 1)))
    x = Matrix((4, -3))
    b = A*x
    soln = A.cholesky_solve(b)
    assert soln == x
    A = Matrix(((9, 3*I), (-3*I, 5)))
    x = Matrix((-2, 1))
    b = A*x
    soln = A.cholesky_solve(b)
    assert expand_mul(soln) == x
    A = Matrix(((9*I, 3), (-3 + I, 5)))
    x = Matrix((2 + 3*I, -1))
    b = A*x
    soln = A.cholesky_solve(b)
    assert expand_mul(soln) == x
    a00, a01, a11, b0, b1 = symbols('a00, a01, a11, b0, b1')
    A = Matrix(((a00, a01), (a01, a11)))
    b = Matrix((b0, b1))
    x = A.cholesky_solve(b)
    assert simplify(A*x) == b


def test_LDLsolve():
    A = Matrix([[2, 3, 5],
                [3, 6, 2],
                [8, 3, 6]])
    x = Matrix(3, 1, [3, 7, 5])
    b = A*x
    soln = A.LDLsolve(b)
    assert soln == x

    A = Matrix([[0, -1, 2],
                [5, 10, 7],
                [8,  3, 4]])
    x = Matrix(3, 1, [-1, 2, 5])
    b = A*x
    soln = A.LDLsolve(b)
    assert soln == x

    A = Matrix(((9, 3*I), (-3*I, 5)))
    x = Matrix((-2, 1))
    b = A*x
    soln = A.LDLsolve(b)
    assert expand_mul(soln) == x

    A = Matrix(((9*I, 3), (-3 + I, 5)))
    x = Matrix((2 + 3*I, -1))
    b = A*x
    soln = A.LDLsolve(b)
    assert expand_mul(soln) == x

    A = Matrix(((9, 3), (3, 9)))
    x = Matrix((1, 1))
    b = A * x
    soln = A.LDLsolve(b)
    assert expand_mul(soln) == x

    A = Matrix([[-5, -3, -4], [-3, -7, 7]])
    x = Matrix([[8], [7], [-2]])
    b = A * x
    raises(NotImplementedError, lambda: A.LDLsolve(b))


def test_lower_triangular_solve():

    raises(NonSquareMatrixError,
        lambda: Matrix([1, 0]).lower_triangular_solve(Matrix([0, 1])))
    raises(ShapeError,
        lambda: Matrix([[1, 0], [0, 1]]).lower_triangular_solve(Matrix([1])))
    raises(ValueError,
        lambda: Matrix([[2, 1], [1, 2]]).lower_triangular_solve(
            Matrix([[1, 0], [0, 1]])))

    A = Matrix([[1, 0], [0, 1]])
    B = Matrix([[x, y], [y, x]])
    C = Matrix([[4, 8], [2, 9]])

    assert A.lower_triangular_solve(B) == B
    assert A.lower_triangular_solve(C) == C


def test_upper_triangular_solve():

    raises(NonSquareMatrixError,
        lambda: Matrix([1, 0]).upper_triangular_solve(Matrix([0, 1])))
    raises(TypeError,
        lambda: Matrix([[1, 0], [0, 1]]).upper_triangular_solve(Matrix([1])))
    raises(TypeError,
        lambda: Matrix([[2, 1], [1, 2]]).upper_triangular_solve(
            Matrix([[1, 0], [0, 1]])))

    A = Matrix([[1, 0], [0, 1]])
    B = Matrix([[x, y], [y, x]])
    C = Matrix([[2, 4], [3, 8]])

    assert A.upper_triangular_solve(B) == B
    assert A.upper_triangular_solve(C) == C


def test_diagonal_solve():
    raises(TypeError, lambda: Matrix([1, 1]).diagonal_solve(Matrix([1])))
    A = Matrix([[1, 0], [0, 1]])*2
    B = Matrix([[x, y], [y, x]])
    assert A.diagonal_solve(B) == B/2

    A = Matrix([[1, 0], [1, 2]])
    raises(TypeError, lambda: A.diagonal_solve(B))


def test_matrix_norm():
    # Vector Tests
    # Test columns and symbols
    x = Symbol('x', real=True)
    v = Matrix([cos(x), sin(x)])
    assert trigsimp(v.norm(2)) == 1
    assert v.norm(10) == Pow(cos(x)**10 + sin(x)**10, S(1)/10)

    # Test Rows
    A = Matrix([[5, Rational(3, 2)]])
    assert A.norm() == Pow(25 + Rational(9, 4), S(1)/2)
    assert A.norm(oo) == max(A._mat)
    assert A.norm(-oo) == min(A._mat)

    # Matrix Tests
    # Intuitive test
    A = Matrix([[1, 1], [1, 1]])
    assert A.norm(2) == 2
    assert A.norm(-2) == 0
    assert A.norm('frobenius') == 2
    assert eye(10).norm(2) == eye(10).norm(-2) == 1
    assert A.norm(oo) == 2

    # Test with Symbols and more complex entries
    A = Matrix([[3, y, y], [x, S(1)/2, -pi]])
    assert (A.norm('fro')
           == sqrt(S(37)/4 + 2*abs(y)**2 + pi**2 + x**2))

    # Check non-square
    A = Matrix([[1, 2, -3], [4, 5, Rational(13, 2)]])
    assert A.norm(2) == sqrt(S(389)/8 + sqrt(78665)/8)
    assert A.norm(-2) == S(0)
    assert A.norm('frobenius') == sqrt(389)/2

    # Test properties of matrix norms
    # https://en.wikipedia.org/wiki/Matrix_norm#Definition
    # Two matrices
    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[5, 5], [-2, 2]])
    C = Matrix([[0, -I], [I, 0]])
    D = Matrix([[1, 0], [0, -1]])
    L = [A, B, C, D]
    alpha = Symbol('alpha', real=True)

    for order in ['fro', 2, -2]:
        # Zero Check
        assert zeros(3).norm(order) == S(0)
        # Check Triangle Inequality for all Pairs of Matrices
        for X in L:
            for Y in L:
                dif = (X.norm(order) + Y.norm(order) -
                    (X + Y).norm(order))
                assert (dif >= 0)
        # Scalar multiplication linearity
        for M in [A, B, C, D]:
            dif = simplify((alpha*M).norm(order) -
                    abs(alpha) * M.norm(order))
            assert dif == 0

    # Test Properties of Vector Norms
    # https://en.wikipedia.org/wiki/Vector_norm
    # Two column vectors
    a = Matrix([1, 1 - 1*I, -3])
    b = Matrix([S(1)/2, 1*I, 1])
    c = Matrix([-1, -1, -1])
    d = Matrix([3, 2, I])
    e = Matrix([Integer(1e2), Rational(1, 1e2), 1])
    L = [a, b, c, d, e]
    alpha = Symbol('alpha', real=True)

    for order in [1, 2, -1, -2, S.Infinity, S.NegativeInfinity, pi]:
        # Zero Check
        if order > 0:
            assert Matrix([0, 0, 0]).norm(order) == S(0)
        # Triangle inequality on all pairs
        if order >= 1:  # Triangle InEq holds only for these norms
            for X in L:
                for Y in L:
                    dif = (X.norm(order) + Y.norm(order) -
                        (X + Y).norm(order))
                    assert simplify(dif >= 0) is S.true
        # Linear to scalar multiplication
        if order in [1, 2, -1, -2, S.Infinity, S.NegativeInfinity]:
            for X in L:
                dif = simplify((alpha*X).norm(order) -
                    (abs(alpha) * X.norm(order)))
                assert dif == 0

    # ord=1
    M = Matrix(3, 3, [1, 3, 0, -2, -1, 0, 3, 9, 6])
    assert M.norm(1) == 13


def test_condition_number():
    x = Symbol('x', real=True)
    A = eye(3)
    A[0, 0] = 10
    A[2, 2] = S(1)/10
    assert A.condition_number() == 100

    A[1, 1] = x
    assert A.condition_number() == Max(10, Abs(x)) / Min(S(1)/10, Abs(x))

    M = Matrix([[cos(x), sin(x)], [-sin(x), cos(x)]])
    Mc = M.condition_number()
    assert all(Float(1.).epsilon_eq(Mc.subs(x, val).evalf()) for val in
        [Rational(1, 5), Rational(1, 2), Rational(1, 10), pi/2, pi, 7*pi/4 ])

    #issue 10782
    assert Matrix([]).condition_number() == 0


def test_equality():
    A = Matrix(((1, 2, 3), (4, 5, 6), (7, 8, 9)))
    B = Matrix(((9, 8, 7), (6, 5, 4), (3, 2, 1)))
    assert A == A[:, :]
    assert not A != A[:, :]
    assert not A == B
    assert A != B
    assert A != 10
    assert not A == 10

    # A SparseMatrix can be equal to a Matrix
    C = SparseMatrix(((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    D = Matrix(((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    assert C == D
    assert not C != D


def test_col_join():
    assert eye(3).col_join(Matrix([[7, 7, 7]])) == \
        Matrix([[1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
                [7, 7, 7]])


def test_row_insert():
    r4 = Matrix([[4, 4, 4]])
    for i in range(-4, 5):
        l = [1, 0, 0]
        l.insert(i, 4)
        assert flatten(eye(3).row_insert(i, r4).col(0).tolist()) == l


def test_col_insert():
    c4 = Matrix([4, 4, 4])
    for i in range(-4, 5):
        l = [0, 0, 0]
        l.insert(i, 4)
        assert flatten(zeros(3).col_insert(i, c4).row(0).tolist()) == l


def test_normalized():
    assert Matrix([3, 4]).normalized() == \
        Matrix([Rational(3, 5), Rational(4, 5)])

    # Zero vector trivial cases
    assert Matrix([0, 0, 0]).normalized() == Matrix([0, 0, 0])

    # Machine precision error truncation trivial cases
    m = Matrix([0,0,1.e-100])
    assert m.normalized(
    iszerofunc=lambda x: x.evalf(n=10, chop=True).is_zero
    ) == Matrix([0, 0, 0])


def test_print_nonzero():
    assert capture(lambda: eye(3).print_nonzero()) == \
        '[X  ]\n[ X ]\n[  X]\n'
    assert capture(lambda: eye(3).print_nonzero('.')) == \
        '[.  ]\n[ . ]\n[  .]\n'


def test_zeros_eye():
    assert Matrix.eye(3) == eye(3)
    assert Matrix.zeros(3) == zeros(3)
    assert ones(3, 4) == Matrix(3, 4, [1]*12)

    i = Matrix([[1, 0], [0, 1]])
    z = Matrix([[0, 0], [0, 0]])
    for cls in classes:
        m = cls.eye(2)
        assert i == m  # but m == i will fail if m is immutable
        assert i == eye(2, cls=cls)
        assert type(m) == cls
        m = cls.zeros(2)
        assert z == m
        assert z == zeros(2, cls=cls)
        assert type(m) == cls


def test_is_zero():
    assert Matrix().is_zero
    assert Matrix([[0, 0], [0, 0]]).is_zero
    assert zeros(3, 4).is_zero
    assert not eye(3).is_zero
    assert Matrix([[x, 0], [0, 0]]).is_zero == None
    assert SparseMatrix([[x, 0], [0, 0]]).is_zero == None
    assert ImmutableMatrix([[x, 0], [0, 0]]).is_zero == None
    assert ImmutableSparseMatrix([[x, 0], [0, 0]]).is_zero == None
    assert Matrix([[x, 1], [0, 0]]).is_zero == False
    a = Symbol('a', nonzero=True)
    assert Matrix([[a, 0], [0, 0]]).is_zero == False


def test_rotation_matrices():
    # This tests the rotation matrices by rotating about an axis and back.
    theta = pi/3
    r3_plus = rot_axis3(theta)
    r3_minus = rot_axis3(-theta)
    r2_plus = rot_axis2(theta)
    r2_minus = rot_axis2(-theta)
    r1_plus = rot_axis1(theta)
    r1_minus = rot_axis1(-theta)
    assert r3_minus*r3_plus*eye(3) == eye(3)
    assert r2_minus*r2_plus*eye(3) == eye(3)
    assert r1_minus*r1_plus*eye(3) == eye(3)

    # Check the correctness of the trace of the rotation matrix
    assert r1_plus.trace() == 1 + 2*cos(theta)
    assert r2_plus.trace() == 1 + 2*cos(theta)
    assert r3_plus.trace() == 1 + 2*cos(theta)

    # Check that a rotation with zero angle doesn't change anything.
    assert rot_axis1(0) == eye(3)
    assert rot_axis2(0) == eye(3)
    assert rot_axis3(0) == eye(3)


def test_DeferredVector():
    assert str(DeferredVector("vector")[4]) == "vector[4]"
    assert sympify(DeferredVector("d")) == DeferredVector("d")
    raises(IndexError, lambda: DeferredVector("d")[-1])
    assert str(DeferredVector("d")) == "d"
    assert repr(DeferredVector("test")) == "DeferredVector('test')"

def test_DeferredVector_not_iterable():
    assert not iterable(DeferredVector('X'))

def test_DeferredVector_Matrix():
    raises(TypeError, lambda: Matrix(DeferredVector("V")))

def test_GramSchmidt():
    R = Rational
    m1 = Matrix(1, 2, [1, 2])
    m2 = Matrix(1, 2, [2, 3])
    assert GramSchmidt([m1, m2]) == \
        [Matrix(1, 2, [1, 2]), Matrix(1, 2, [R(2)/5, R(-1)/5])]
    assert GramSchmidt([m1.T, m2.T]) == \
        [Matrix(2, 1, [1, 2]), Matrix(2, 1, [R(2)/5, R(-1)/5])]
    # from wikipedia
    assert GramSchmidt([Matrix([3, 1]), Matrix([2, 2])], True) == [
        Matrix([3*sqrt(10)/10, sqrt(10)/10]),
        Matrix([-sqrt(10)/10, 3*sqrt(10)/10])]


def test_casoratian():
    assert casoratian([1, 2, 3, 4], 1) == 0
    assert casoratian([1, 2, 3, 4], 1, zero=False) == 0


def test_zero_dimension_multiply():
    assert (Matrix()*zeros(0, 3)).shape == (0, 3)
    assert zeros(3, 0)*zeros(0, 3) == zeros(3, 3)
    assert zeros(0, 3)*zeros(3, 0) == Matrix()


def test_slice_issue_2884():
    m = Matrix(2, 2, range(4))
    assert m[1, :] == Matrix([[2, 3]])
    assert m[-1, :] == Matrix([[2, 3]])
    assert m[:, 1] == Matrix([[1, 3]]).T
    assert m[:, -1] == Matrix([[1, 3]]).T
    raises(IndexError, lambda: m[2, :])
    raises(IndexError, lambda: m[2, 2])


def test_slice_issue_3401():
    assert zeros(0, 3)[:, -1].shape == (0, 1)
    assert zeros(3, 0)[0, :] == Matrix(1, 0, [])


def test_copyin():
    s = zeros(3, 3)
    s[3] = 1
    assert s[:, 0] == Matrix([0, 1, 0])
    assert s[3] == 1
    assert s[3: 4] == [1]
    s[1, 1] = 42
    assert s[1, 1] == 42
    assert s[1, 1:] == Matrix([[42, 0]])
    s[1, 1:] = Matrix([[5, 6]])
    assert s[1, :] == Matrix([[1, 5, 6]])
    s[1, 1:] = [[42, 43]]
    assert s[1, :] == Matrix([[1, 42, 43]])
    s[0, 0] = 17
    assert s[:, :1] == Matrix([17, 1, 0])
    s[0, 0] = [1, 1, 1]
    assert s[:, 0] == Matrix([1, 1, 1])
    s[0, 0] = Matrix([1, 1, 1])
    assert s[:, 0] == Matrix([1, 1, 1])
    s[0, 0] = SparseMatrix([1, 1, 1])
    assert s[:, 0] == Matrix([1, 1, 1])


def test_invertible_check():
    # sometimes a singular matrix will have a pivot vector shorter than
    # the number of rows in a matrix...
    assert Matrix([[1, 2], [1, 2]]).rref() == (Matrix([[1, 2], [0, 0]]), (0,))
    raises(ValueError, lambda: Matrix([[1, 2], [1, 2]]).inv())
    m = Matrix([
        [-1, -1,  0],
        [ x,  1,  1],
        [ 1,  x, -1],
    ])
    assert len(m.rref()[1]) != m.rows
    # in addition, unless simplify=True in the call to rref, the identity
    # matrix will be returned even though m is not invertible
    assert m.rref()[0] != eye(3)
    assert m.rref(simplify=signsimp)[0] != eye(3)
    raises(ValueError, lambda: m.inv(method="ADJ"))
    raises(ValueError, lambda: m.inv(method="GE"))
    raises(ValueError, lambda: m.inv(method="LU"))


@XFAIL
def test_issue_3959():
    x, y = symbols('x, y')
    e = x*y
    assert e.subs(x, Matrix([3, 5, 3])) == Matrix([3, 5, 3])*y


def test_issue_5964():
    assert str(Matrix([[1, 2], [3, 4]])) == 'Matrix([[1, 2], [3, 4]])'


def test_issue_7604():
    x, y = symbols(u"x y")
    assert sstr(Matrix([[x, 2*y], [y**2, x + 3]])) == \
        'Matrix([\n[   x,   2*y],\n[y**2, x + 3]])'


def test_is_Identity():
    assert eye(3).is_Identity
    assert eye(3).as_immutable().is_Identity
    assert not zeros(3).is_Identity
    assert not ones(3).is_Identity
    # issue 6242
    assert not Matrix([[1, 0, 0]]).is_Identity
    # issue 8854
    assert SparseMatrix(3,3, {(0,0):1, (1,1):1, (2,2):1}).is_Identity
    assert not SparseMatrix(2,3, range(6)).is_Identity
    assert not SparseMatrix(3,3, {(0,0):1, (1,1):1}).is_Identity
    assert not SparseMatrix(3,3, {(0,0):1, (1,1):1, (2,2):1, (0,1):2, (0,2):3}).is_Identity


def test_dot():
    assert ones(1, 3).dot(ones(3, 1)) == 3
    assert ones(1, 3).dot([1, 1, 1]) == 3
    assert Matrix([1, 2, 3]).dot(Matrix([1, 2, 3])) == 14
    assert Matrix([1, 2, 3*I]).dot(Matrix([I, 2, 3*I])) == -5 + I
    assert Matrix([1, 2, 3*I]).dot(Matrix([I, 2, 3*I]), hermitian=False) == -5 + I
    assert Matrix([1, 2, 3*I]).dot(Matrix([I, 2, 3*I]), hermitian=True) == 13 + I
    assert Matrix([1, 2, 3*I]).dot(Matrix([I, 2, 3*I]), hermitian=True, conjugate_convention="physics") == 13 - I
    assert Matrix([1, 2, 3*I]).dot(Matrix([4, 5*I, 6]), hermitian=True, conjugate_convention="right") == 4 + 8*I
    assert Matrix([1, 2, 3*I]).dot(Matrix([4, 5*I, 6]), hermitian=True, conjugate_convention="left") == 4 - 8*I
    assert Matrix([I, 2*I]).dot(Matrix([I, 2*I]), hermitian=False, conjugate_convention="left") == -5
    assert Matrix([I, 2*I]).dot(Matrix([I, 2*I]), conjugate_convention="left") == 5
    raises(ValueError, lambda: Matrix([1, 2]).dot(Matrix([3, 4]), hermitian=True, conjugate_convention="test"))


def test_dual():
    B_x, B_y, B_z, E_x, E_y, E_z = symbols(
        'B_x B_y B_z E_x E_y E_z', real=True)
    F = Matrix((
        (   0,  E_x,  E_y,  E_z),
        (-E_x,    0,  B_z, -B_y),
        (-E_y, -B_z,    0,  B_x),
        (-E_z,  B_y, -B_x,    0)
    ))
    Fd = Matrix((
        (  0, -B_x, -B_y, -B_z),
        (B_x,    0,  E_z, -E_y),
        (B_y, -E_z,    0,  E_x),
        (B_z,  E_y, -E_x,    0)
    ))
    assert F.dual().equals(Fd)
    assert eye(3).dual().equals(zeros(3))
    assert F.dual().dual().equals(-F)


def test_anti_symmetric():
    assert Matrix([1, 2]).is_anti_symmetric() is False
    m = Matrix(3, 3, [0, x**2 + 2*x + 1, y, -(x + 1)**2, 0, x*y, -y, -x*y, 0])
    assert m.is_anti_symmetric() is True
    assert m.is_anti_symmetric(simplify=False) is False
    assert m.is_anti_symmetric(simplify=lambda x: x) is False

    # tweak to fail
    m[2, 1] = -m[2, 1]
    assert m.is_anti_symmetric() is False
    # untweak
    m[2, 1] = -m[2, 1]

    m = m.expand()
    assert m.is_anti_symmetric(simplify=False) is True
    m[0, 0] = 1
    assert m.is_anti_symmetric() is False


def test_normalize_sort_diogonalization():
    A = Matrix(((1, 2), (2, 1)))
    P, Q = A.diagonalize(normalize=True)
    assert P*P.T == P.T*P == eye(P.cols)
    P, Q = A.diagonalize(normalize=True, sort=True)
    assert P*P.T == P.T*P == eye(P.cols)
    assert P*Q*P.inv() == A


def test_issue_5321():
    raises(ValueError, lambda: Matrix([[1, 2, 3], Matrix(0, 1, [])]))


def test_issue_5320():
    assert Matrix.hstack(eye(2), 2*eye(2)) == Matrix([
        [1, 0, 2, 0],
        [0, 1, 0, 2]
    ])
    assert Matrix.vstack(eye(2), 2*eye(2)) == Matrix([
        [1, 0],
        [0, 1],
        [2, 0],
        [0, 2]
    ])
    cls = SparseMatrix
    assert cls.hstack(cls(eye(2)), cls(2*eye(2))) == Matrix([
        [1, 0, 2, 0],
        [0, 1, 0, 2]
    ])

def test_issue_11944():
    A = Matrix([[1]])
    AIm = sympify(A)
    assert Matrix.hstack(AIm, A) == Matrix([[1, 1]])
    assert Matrix.vstack(AIm, A) == Matrix([[1], [1]])

def test_cross():
    a = [1, 2, 3]
    b = [3, 4, 5]
    col = Matrix([-2, 4, -2])
    row = col.T

    def test(M, ans):
        assert ans == M
        assert type(M) == cls
    for cls in classes:
        A = cls(a)
        B = cls(b)
        test(A.cross(B), col)
        test(A.cross(B.T), col)
        test(A.T.cross(B.T), row)
        test(A.T.cross(B), row)
    raises(ShapeError, lambda:
        Matrix(1, 2, [1, 1]).cross(Matrix(1, 2, [1, 1])))


def test_hash():
    for cls in classes[-2:]:
        s = {cls.eye(1), cls.eye(1)}
        assert len(s) == 1 and s.pop() == cls.eye(1)
    # issue 3979
    for cls in classes[:2]:
        assert not isinstance(cls.eye(1), Hashable)


@XFAIL
def test_issue_3979():
    # when this passes, delete this and change the [1:2]
    # to [:2] in the test_hash above for issue 3979
    cls = classes[0]
    raises(AttributeError, lambda: hash(cls.eye(1)))


def test_adjoint():
    dat = [[0, I], [1, 0]]
    ans = Matrix([[0, 1], [-I, 0]])
    for cls in classes:
        assert ans == cls(dat).adjoint()

def test_simplify_immutable():
    from sympy import simplify, sin, cos
    assert simplify(ImmutableMatrix([[sin(x)**2 + cos(x)**2]])) == \
                    ImmutableMatrix([[1]])

def test_rank():
    from sympy.abc import x
    m = Matrix([[1, 2], [x, 1 - 1/x]])
    assert m.rank() == 2
    n = Matrix(3, 3, range(1, 10))
    assert n.rank() == 2
    p = zeros(3)
    assert p.rank() == 0

def test_issue_11434():
    ax, ay, bx, by, cx, cy, dx, dy, ex, ey, t0, t1 = \
        symbols('a_x a_y b_x b_y c_x c_y d_x d_y e_x e_y t_0 t_1')
    M = Matrix([[ax, ay, ax*t0, ay*t0, 0],
                [bx, by, bx*t0, by*t0, 0],
                [cx, cy, cx*t0, cy*t0, 1],
                [dx, dy, dx*t0, dy*t0, 1],
                [ex, ey, 2*ex*t1 - ex*t0, 2*ey*t1 - ey*t0, 0]])
    assert M.rank() == 4

def test_rank_regression_from_so():
    # see:
    # https://stackoverflow.com/questions/19072700/why-does-sympy-give-me-the-wrong-answer-when-i-row-reduce-a-symbolic-matrix

    nu, lamb = symbols('nu, lambda')
    A = Matrix([[-3*nu,         1,                  0,  0],
                [ 3*nu, -2*nu - 1,                  2,  0],
                [    0,      2*nu, (-1*nu) - lamb - 2,  3],
                [    0,         0,          nu + lamb, -3]])
    expected_reduced = Matrix([[1, 0, 0, 1/(nu**2*(-lamb - nu))],
                               [0, 1, 0,    3/(nu*(-lamb - nu))],
                               [0, 0, 1,         3/(-lamb - nu)],
                               [0, 0, 0,                      0]])
    expected_pivots = (0, 1, 2)

    reduced, pivots = A.rref()

    assert simplify(expected_reduced - reduced) == zeros(*A.shape)
    assert pivots == expected_pivots

def test_replace():
    from sympy import symbols, Function, Matrix
    F, G = symbols('F, G', cls=Function)
    K = Matrix(2, 2, lambda i, j: G(i+j))
    M = Matrix(2, 2, lambda i, j: F(i+j))
    N = M.replace(F, G)
    assert N == K

def test_replace_map():
    from sympy import symbols, Function, Matrix
    F, G = symbols('F, G', cls=Function)
    K = Matrix(2, 2, [(G(0), {F(0): G(0)}), (G(1), {F(1): G(1)}), (G(1), {F(1)\
    : G(1)}), (G(2), {F(2): G(2)})])
    M = Matrix(2, 2, lambda i, j: F(i+j))
    N = M.replace(F, G, True)
    assert N == K

def test_atoms():
    m = Matrix([[1, 2], [x, 1 - 1/x]])
    assert m.atoms() == {S(1),S(2),S(-1), x}
    assert m.atoms(Symbol) == {x}


def test_pinv():
    # Pseudoinverse of an invertible matrix is the inverse.
    A1 = Matrix([[a, b], [c, d]])
    assert simplify(A1.pinv()) == simplify(A1.inv())
    # Test the four properties of the pseudoinverse for various matrices.
    As = [Matrix([[13, 104], [2212, 3], [-3, 5]]),
          Matrix([[1, 7, 9], [11, 17, 19]]),
          Matrix([a, b])]
    for A in As:
        A_pinv = A.pinv()
        AAp = A * A_pinv
        ApA = A_pinv * A
        assert simplify(AAp * A) == A
        assert simplify(ApA * A_pinv) == A_pinv
        assert AAp.H == AAp
        assert ApA.H == ApA

def test_pinv_solve():
    # Fully determined system (unique result, identical to other solvers).
    A = Matrix([[1, 5], [7, 9]])
    B = Matrix([12, 13])
    assert A.pinv_solve(B) == A.cholesky_solve(B)
    assert A.pinv_solve(B) == A.LDLsolve(B)
    assert A.pinv_solve(B) == Matrix([sympify('-43/26'), sympify('71/26')])
    assert A * A.pinv() * B == B
    # Fully determined, with two-dimensional B matrix.
    B = Matrix([[12, 13, 14], [15, 16, 17]])
    assert A.pinv_solve(B) == A.cholesky_solve(B)
    assert A.pinv_solve(B) == A.LDLsolve(B)
    assert A.pinv_solve(B) == Matrix([[-33, -37, -41], [69, 75, 81]]) / 26
    assert A * A.pinv() * B == B
    # Underdetermined system (infinite results).
    A = Matrix([[1, 0, 1], [0, 1, 1]])
    B = Matrix([5, 7])
    solution = A.pinv_solve(B)
    w = {}
    for s in solution.atoms(Symbol):
        # Extract dummy symbols used in the solution.
        w[s.name] = s
    assert solution == Matrix([[w['w0_0']/3 + w['w1_0']/3 - w['w2_0']/3 + 1],
                               [w['w0_0']/3 + w['w1_0']/3 - w['w2_0']/3 + 3],
                               [-w['w0_0']/3 - w['w1_0']/3 + w['w2_0']/3 + 4]])
    assert A * A.pinv() * B == B
    # Overdetermined system (least squares results).
    A = Matrix([[1, 0], [0, 0], [0, 1]])
    B = Matrix([3, 2, 1])
    assert A.pinv_solve(B) == Matrix([3, 1])
    # Proof the solution is not exact.
    assert A * A.pinv() * B != B

def test_pinv_rank_deficient():
    # Test the four properties of the pseudoinverse for various matrices.
    As = [Matrix([[1, 1, 1], [2, 2, 2]]),
          Matrix([[1, 0], [0, 0]]),
          Matrix([[1, 2], [2, 4], [3, 6]])]
    for A in As:
        A_pinv = A.pinv()
        AAp = A * A_pinv
        ApA = A_pinv * A
        assert simplify(AAp * A) == A
        assert simplify(ApA * A_pinv) == A_pinv
        assert AAp.H == AAp
        assert ApA.H == ApA
    # Test solving with rank-deficient matrices.
    A = Matrix([[1, 0], [0, 0]])
    # Exact, non-unique solution.
    B = Matrix([3, 0])
    solution = A.pinv_solve(B)
    w1 = solution.atoms(Symbol).pop()
    assert w1.name == 'w1_0'
    assert solution == Matrix([3, w1])
    assert A * A.pinv() * B == B
    # Least squares, non-unique solution.
    B = Matrix([3, 1])
    solution = A.pinv_solve(B)
    w1 = solution.atoms(Symbol).pop()
    assert w1.name == 'w1_0'
    assert solution == Matrix([3, w1])
    assert A * A.pinv() * B != B

@XFAIL
def test_pinv_rank_deficient_when_diagonalization_fails():
    # Test the four properties of the pseudoinverse for matrices when
    # diagonalization of A.H*A fails.
    As = [Matrix([
        [61, 89, 55, 20, 71, 0],
        [62, 96, 85, 85, 16, 0],
        [69, 56, 17,  4, 54, 0],
        [10, 54, 91, 41, 71, 0],
        [ 7, 30, 10, 48, 90, 0],
        [0,0,0,0,0,0]])]
    for A in As:
        A_pinv = A.pinv()
        AAp = A * A_pinv
        ApA = A_pinv * A
        assert simplify(AAp * A) == A
        assert simplify(ApA * A_pinv) == A_pinv
        assert AAp.H == AAp
        assert ApA.H == ApA


def test_gauss_jordan_solve():

    # Square, full rank, unique solution
    A = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    b = Matrix([3, 6, 9])
    sol, params = A.gauss_jordan_solve(b)
    assert sol == Matrix([[-1], [2], [0]])
    assert params == Matrix(0, 1, [])

    # Square, full rank, unique solution, B has more columns than rows
    A = eye(3)
    B = Matrix([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
    sol, params = A.gauss_jordan_solve(B)
    assert sol == B
    assert params == Matrix(0, 4, [])

    # Square, reduced rank, parametrized solution
    A = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    b = Matrix([3, 6, 9])
    sol, params, freevar = A.gauss_jordan_solve(b, freevar=True)
    w = {}
    for s in sol.atoms(Symbol):
        # Extract dummy symbols used in the solution.
        w[s.name] = s
    assert sol == Matrix([[w['tau0'] - 1], [-2*w['tau0'] + 2], [w['tau0']]])
    assert params == Matrix([[w['tau0']]])
    assert freevar == [2]

    # Square, reduced rank, parametrized solution, B has two columns
    A = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    B = Matrix([[3, 4], [6, 8], [9, 12]])
    sol, params, freevar = A.gauss_jordan_solve(B, freevar=True)
    w = {}
    for s in sol.atoms(Symbol):
        # Extract dummy symbols used in the solution.
        w[s.name] = s
    assert sol == Matrix([[w['tau0'] - 1, w['tau1'] - S(4)/3],
                          [-2*w['tau0'] + 2, -2*w['tau1'] + S(8)/3],
                          [w['tau0'], w['tau1']],])
    assert params == Matrix([[w['tau0'], w['tau1']]])
    assert freevar == [2]

    # Square, reduced rank, parametrized solution
    A = Matrix([[1, 2, 3], [2, 4, 6], [3, 6, 9]])
    b = Matrix([0, 0, 0])
    sol, params = A.gauss_jordan_solve(b)
    w = {}
    for s in sol.atoms(Symbol):
        w[s.name] = s
    assert sol == Matrix([[-2*w['tau0'] - 3*w['tau1']],
                         [w['tau0']], [w['tau1']]])
    assert params == Matrix([[w['tau0']], [w['tau1']]])

    # Square, reduced rank, parametrized solution
    A = Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    b = Matrix([0, 0, 0])
    sol, params = A.gauss_jordan_solve(b)
    w = {}
    for s in sol.atoms(Symbol):
        w[s.name] = s
    assert sol == Matrix([[w['tau0']], [w['tau1']], [w['tau2']]])
    assert params == Matrix([[w['tau0']], [w['tau1']], [w['tau2']]])

    # Square, reduced rank, no solution
    A = Matrix([[1, 2, 3], [2, 4, 6], [3, 6, 9]])
    b = Matrix([0, 0, 1])
    raises(ValueError, lambda: A.gauss_jordan_solve(b))

    # Rectangular, tall, full rank, unique solution
    A = Matrix([[1, 5, 3], [2, 1, 6], [1, 7, 9], [1, 4, 3]])
    b = Matrix([0, 0, 1, 0])
    sol, params = A.gauss_jordan_solve(b)
    assert sol == Matrix([[-S(1)/2], [0], [S(1)/6]])
    assert params == Matrix(0, 1, [])

    # Rectangular, tall, full rank, unique solution, B has less columns than rows
    A = Matrix([[1, 5, 3], [2, 1, 6], [1, 7, 9], [1, 4, 3]])
    B = Matrix([[0,0], [0, 0], [1, 2], [0, 0]])
    sol, params = A.gauss_jordan_solve(B)
    assert sol == Matrix([[-S(1)/2, -S(2)/2], [0, 0], [S(1)/6, S(2)/6]])
    assert params == Matrix(0, 2, [])

    # Rectangular, tall, full rank, no solution
    A = Matrix([[1, 5, 3], [2, 1, 6], [1, 7, 9], [1, 4, 3]])
    b = Matrix([0, 0, 0, 1])
    raises(ValueError, lambda: A.gauss_jordan_solve(b))

    # Rectangular, tall, full rank, no solution, B has two columns (2nd has no solution)
    A = Matrix([[1, 5, 3], [2, 1, 6], [1, 7, 9], [1, 4, 3]])
    B = Matrix([[0,0], [0, 0], [1, 0], [0, 1]])
    raises(ValueError, lambda: A.gauss_jordan_solve(B))

    # Rectangular, tall, full rank, no solution, B has two columns (1st has no solution)
    A = Matrix([[1, 5, 3], [2, 1, 6], [1, 7, 9], [1, 4, 3]])
    B = Matrix([[0,0], [0, 0], [0, 1], [1, 0]])
    raises(ValueError, lambda: A.gauss_jordan_solve(B))

    # Rectangular, tall, reduced rank, parametrized solution
    A = Matrix([[1, 5, 3], [2, 10, 6], [3, 15, 9], [1, 4, 3]])
    b = Matrix([0, 0, 0, 1])
    sol, params = A.gauss_jordan_solve(b)
    w = {}
    for s in sol.atoms(Symbol):
        w[s.name] = s
    assert sol == Matrix([[-3*w['tau0'] + 5], [-1], [w['tau0']]])
    assert params == Matrix([[w['tau0']]])

    # Rectangular, tall, reduced rank, no solution
    A = Matrix([[1, 5, 3], [2, 10, 6], [3, 15, 9], [1, 4, 3]])
    b = Matrix([0, 0, 1, 1])
    raises(ValueError, lambda: A.gauss_jordan_solve(b))

    # Rectangular, wide, full rank, parametrized solution
    A = Matrix([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 1, 12]])
    b = Matrix([1, 1, 1])
    sol, params = A.gauss_jordan_solve(b)
    w = {}
    for s in sol.atoms(Symbol):
        w[s.name] = s
    assert sol == Matrix([[2*w['tau0'] - 1], [-3*w['tau0'] + 1], [0],
                         [w['tau0']]])
    assert params == Matrix([[w['tau0']]])

    # Rectangular, wide, reduced rank, parametrized solution
    A = Matrix([[1, 2, 3, 4], [5, 6, 7, 8], [2, 4, 6, 8]])
    b = Matrix([0, 1, 0])
    sol, params = A.gauss_jordan_solve(b)
    w = {}
    for s in sol.atoms(Symbol):
        w[s.name] = s
    assert sol == Matrix([[w['tau0'] + 2*w['tau1'] + 1/S(2)],
                         [-2*w['tau0'] - 3*w['tau1'] - 1/S(4)],
                         [w['tau0']], [w['tau1']]])
    assert params == Matrix([[w['tau0']], [w['tau1']]])
    # watch out for clashing symbols
    x0, x1, x2, _x0 = symbols('_tau0 _tau1 _tau2 tau1')
    M = Matrix([[0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, _x0]])
    A = M[:, :-1]
    b = M[:, -1:]
    sol, params = A.gauss_jordan_solve(b)
    assert params == Matrix(3, 1, [x0, x1, x2])
    assert sol == Matrix(5, 1, [x1, 0, x0, _x0, x2])

    # Rectangular, wide, reduced rank, no solution
    A = Matrix([[1, 2, 3, 4], [5, 6, 7, 8], [2, 4, 6, 8]])
    b = Matrix([1, 1, 1])
    raises(ValueError, lambda: A.gauss_jordan_solve(b))

def test_solve():
    A = Matrix([[1,2], [2,4]])
    b = Matrix([[3], [4]])
    raises(ValueError, lambda: A.solve(b)) #no solution
    b = Matrix([[ 4], [8]])
    raises(ValueError, lambda: A.solve(b)) #infinite solution

def test_issue_7201():
    assert ones(0, 1) + ones(0, 1) == Matrix(0, 1, [])
    assert ones(1, 0) + ones(1, 0) == Matrix(1, 0, [])

def test_free_symbols():
    for M in ImmutableMatrix, ImmutableSparseMatrix, Matrix, SparseMatrix:
        assert M([[x], [0]]).free_symbols == {x}

def test_from_ndarray():
    """See issue 7465."""
    try:
        from numpy import array
    except ImportError:
        skip('NumPy must be available to test creating matrices from ndarrays')

    assert Matrix(array([1, 2, 3])) == Matrix([1, 2, 3])
    assert Matrix(array([[1, 2, 3]])) == Matrix([[1, 2, 3]])
    assert Matrix(array([[1, 2, 3], [4, 5, 6]])) == \
        Matrix([[1, 2, 3], [4, 5, 6]])
    assert Matrix(array([x, y, z])) == Matrix([x, y, z])
    raises(NotImplementedError, lambda: Matrix(array([[
        [1, 2], [3, 4]], [[5, 6], [7, 8]]])))

def test_hermitian():
    a = Matrix([[1, I], [-I, 1]])
    assert a.is_hermitian
    a[0, 0] = 2*I
    assert a.is_hermitian is False
    a[0, 0] = x
    assert a.is_hermitian is None
    a[0, 1] = a[1, 0]*I
    assert a.is_hermitian is False

def test_doit():
    a = Matrix([[Add(x,x, evaluate=False)]])
    assert a[0] != 2*x
    assert a.doit() == Matrix([[2*x]])

def test_issue_9457_9467_9876():
    # for row_del(index)
    M = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    M.row_del(1)
    assert M == Matrix([[1, 2, 3], [3, 4, 5]])
    N = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    N.row_del(-2)
    assert N == Matrix([[1, 2, 3], [3, 4, 5]])
    O = Matrix([[1, 2, 3], [5, 6, 7], [9, 10, 11]])
    O.row_del(-1)
    assert O == Matrix([[1, 2, 3], [5, 6, 7]])
    P = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(IndexError, lambda: P.row_del(10))
    Q = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(IndexError, lambda: Q.row_del(-10))

    # for col_del(index)
    M = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    M.col_del(1)
    assert M == Matrix([[1, 3], [2, 4], [3, 5]])
    N = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    N.col_del(-2)
    assert N == Matrix([[1, 3], [2, 4], [3, 5]])
    P = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(IndexError, lambda: P.col_del(10))
    Q = Matrix([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    raises(IndexError, lambda: Q.col_del(-10))

def test_issue_9422():
    x, y = symbols('x y', commutative=False)
    a, b = symbols('a b')
    M = eye(2)
    M1 = Matrix(2, 2, [x, y, y, z])
    assert y*x*M != x*y*M
    assert b*a*M == a*b*M
    assert x*M1 != M1*x
    assert a*M1 == M1*a
    assert y*x*M == Matrix([[y*x, 0], [0, y*x]])


def test_issue_10770():
    M = Matrix([])
    a = ['col_insert', 'row_join'], Matrix([9, 6, 3])
    b = ['row_insert', 'col_join'], a[1].T
    c = ['row_insert', 'col_insert'], Matrix([[1, 2], [3, 4]])
    for ops, m in (a, b, c):
        for op in ops:
            f = getattr(M, op)
            new = f(m) if 'join' in op else f(42, m)
            assert new == m and id(new) != id(m)


def test_issue_10658():
    A = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert A.extract([0, 1, 2], [True, True, False]) == \
        Matrix([[1, 2], [4, 5], [7, 8]])
    assert A.extract([0, 1, 2], [True, False, False]) == Matrix([[1], [4], [7]])
    assert A.extract([True, False, False], [0, 1, 2]) == Matrix([[1, 2, 3]])
    assert A.extract([True, False, True], [0, 1, 2]) == \
        Matrix([[1, 2, 3], [7, 8, 9]])
    assert A.extract([0, 1, 2], [False, False, False]) == Matrix(3, 0, [])
    assert A.extract([False, False, False], [0, 1, 2]) == Matrix(0, 3, [])
    assert A.extract([True, False, True], [False, True, False]) == \
        Matrix([[2], [8]])

def test_opportunistic_simplification():
    # this test relates to issue #10718, #9480, #11434

    # issue #9480
    m = Matrix([[-5 + 5*sqrt(2), -5], [-5*sqrt(2)/2 + 5, -5*sqrt(2)/2]])
    assert m.rank() == 1

    # issue #10781
    m = Matrix([[3+3*sqrt(3)*I, -9],[4,-3+3*sqrt(3)*I]])
    assert simplify(m.rref()[0] - Matrix([[1, -9/(3 + 3*sqrt(3)*I)], [0, 0]])) == zeros(2, 2)

    # issue #11434
    ax,ay,bx,by,cx,cy,dx,dy,ex,ey,t0,t1 = symbols('a_x a_y b_x b_y c_x c_y d_x d_y e_x e_y t_0 t_1')
    m = Matrix([[ax,ay,ax*t0,ay*t0,0],[bx,by,bx*t0,by*t0,0],[cx,cy,cx*t0,cy*t0,1],[dx,dy,dx*t0,dy*t0,1],[ex,ey,2*ex*t1-ex*t0,2*ey*t1-ey*t0,0]])
    assert m.rank() == 4

def test_partial_pivoting():
    # example from https://en.wikipedia.org/wiki/Pivot_element
    # partial pivoting with back subsitution gives a perfect result
    # naive pivoting give an error ~1e-13, so anything better than
    # 1e-15 is good
    mm=Matrix([[0.003 ,59.14, 59.17],[ 5.291, -6.13,46.78]])
    assert (mm.rref()[0] - Matrix([[1.0,   0, 10.0], [  0, 1.0,  1.0]])).norm() < 1e-15

    # issue #11549
    m_mixed = Matrix([[6e-17, 1.0, 4],[ -1.0,   0, 8],[    0,   0, 1]])
    m_float = Matrix([[6e-17, 1.0, 4.],[ -1.0,   0., 8.],[    0.,   0., 1.]])
    m_inv = Matrix([[  0,    -1.0,  8.0],[1.0, 6.0e-17, -4.0],[  0,       0,    1]])
    # this example is numerically unstable and involves a matrix with a norm >= 8,
    # this comparing the difference of the results with 1e-15 is numerically sound.
    assert (m_mixed.inv() - m_inv).norm() < 1e-15
    assert (m_float.inv() - m_inv).norm() < 1e-15

def test_iszero_substitution():
    """ When doing numerical computations, all elements that pass
    the iszerofunc test should be set to numerically zero if they
    aren't already. """

    # Matrix from issue #9060
    m = Matrix([[0.9, -0.1, -0.2, 0],[-0.8, 0.9, -0.4, 0],[-0.1, -0.8, 0.6, 0]])
    m_rref = m.rref(iszerofunc=lambda x: abs(x)<6e-15)[0]
    m_correct = Matrix([[1.0,   0, -0.301369863013699, 0],[  0, 1.0, -0.712328767123288, 0],[  0,   0,                  0, 0]])
    m_diff = m_rref - m_correct
    assert m_diff.norm() < 1e-15
    # if a zero-substitution wasn't made, this entry will be -1.11022302462516e-16
    assert m_rref[2,2] == 0

def test_rank_decomposition():
    a = Matrix(0, 0, [])
    c, f = a.rank_decomposition()
    assert f.is_echelon
    assert c.cols == f.rows == a.rank()
    assert c * f == a

    a = Matrix(1, 1, [5])
    c, f = a.rank_decomposition()
    assert f.is_echelon
    assert c.cols == f.rows == a.rank()
    assert c * f == a

    a = Matrix(3, 3, [1, 2, 3, 1, 2, 3, 1, 2, 3])
    c, f = a.rank_decomposition()
    assert f.is_echelon
    assert c.cols == f.rows == a.rank()
    assert c * f == a

    a = Matrix([
        [0, 0, 1, 2, 2, -5, 3],
        [-1, 5, 2, 2, 1, -7, 5],
        [0, 0, -2, -3, -3, 8, -5],
        [-1, 5, 0, -1, -2, 1, 0]])
    c, f = a.rank_decomposition()
    assert f.is_echelon
    assert c.cols == f.rows == a.rank()
    assert c * f == a

@slow
def test_issue_11238():
    from sympy import Point
    xx = 8*tan(13*pi/45)/(tan(13*pi/45) + sqrt(3))
    yy = (-8*sqrt(3)*tan(13*pi/45)**2 + 24*tan(13*pi/45))/(-3 + tan(13*pi/45)**2)
    p1 = Point(0, 0)
    p2 = Point(1, -sqrt(3))
    p0 = Point(xx,yy)
    m1 = Matrix([p1 - simplify(p0), p2 - simplify(p0)])
    m2 = Matrix([p1 - p0, p2 - p0])
    m3 = Matrix([simplify(p1 - p0), simplify(p2 - p0)])

    assert m1.rank(simplify=True) == 1
    assert m2.rank(simplify=True) == 1
    assert m3.rank(simplify=True) == 1

def test_as_real_imag():
    m1 = Matrix(2,2,[1,2,3,4])
    m2 = m1*S.ImaginaryUnit
    m3 = m1 + m2

    for kls in classes:
        a,b = kls(m3).as_real_imag()
        assert list(a) == list(m1)
        assert list(b) == list(m1)

def test_deprecated():
    # Maintain tests for deprecated functions.  We must capture
    # the deprecation warnings.  When the deprecated functionality is
    # removed, the corresponding tests should be removed.

    m = Matrix(3, 3, [0, 1, 0, -4, 4, 0, -2, 1, 2])
    P, Jcells = m.jordan_cells()
    assert Jcells[1] == Matrix(1, 1, [2])
    assert Jcells[0] == Matrix(2, 2, [2, 1, 0, 2])

    with warns_deprecated_sympy():
        assert Matrix([[1,2],[3,4]]).dot(Matrix([[1,3],[4,5]])) == [10, 19, 14, 28]


def test_issue_14489():
    from sympy import Mod
    A = Matrix([-1, 1, 2])
    B = Matrix([10, 20, -15])

    assert Mod(A, 3) == Matrix([2, 1, 2])
    assert Mod(B, 4) == Matrix([2, 0, 1])

def test_issue_14517():
    M = Matrix([
        [   0, 10*I,    10*I,       0],
        [10*I,    0,       0,    10*I],
        [10*I,    0, 5 + 2*I,    10*I],
        [   0, 10*I,    10*I, 5 + 2*I]])
    ev = M.eigenvals()
    # test one random eigenvalue, the computation is a little slow
    test_ev = random.choice(list(ev.keys()))
    assert (M - test_ev*eye(4)).det() == 0

def test_issue_14943():
    # Test that __array__ accepts the optional dtype argument
    try:
        from numpy import array
    except ImportError:
        skip('NumPy must be available to test creating matrices from ndarrays')

    M = Matrix([[1,2], [3,4]])
    assert array(M, dtype=float).dtype.name == 'float64'

def test_issue_8240():
    # Eigenvalues of large triangular matrices
    n = 200

    diagonal_variables = [Symbol('x%s' % i) for i in range(n)]
    M = [[0 for i in range(n)] for j in range(n)]
    for i in range(n):
        M[i][i] = diagonal_variables[i]
    M = Matrix(M)

    eigenvals = M.eigenvals()
    assert len(eigenvals) == n
    for i in range(n):
        assert eigenvals[diagonal_variables[i]] == 1

    eigenvals = M.eigenvals(multiple=True)
    assert set(eigenvals) == set(diagonal_variables)

    # with multiplicity
    M = Matrix([[x, 0, 0], [1, y, 0], [2, 3, x]])
    eigenvals = M.eigenvals()
    assert eigenvals == {x: 2, y: 1}

    eigenvals = M.eigenvals(multiple=True)
    assert len(eigenvals) == 3
    assert eigenvals.count(x) == 2
    assert eigenvals.count(y) == 1

def test_legacy_det():
    # Minimal support for legacy keys for 'method' in det()
    # Partially copied from test_determinant()

    M = Matrix(( ( 3, -2,  0, 5),
                 (-2,  1, -2, 2),
                 ( 0, -2,  5, 0),
                 ( 5,  0,  3, 4) ))

    assert M.det(method="bareis") == -289
    assert M.det(method="det_lu") == -289
    assert M.det(method="det_LU") == -289

    M = Matrix(( (3, 2, 0, 0, 0),
                 (0, 3, 2, 0, 0),
                 (0, 0, 3, 2, 0),
                 (0, 0, 0, 3, 2),
                 (2, 0, 0, 0, 3) ))

    assert M.det(method="bareis") == 275
    assert M.det(method="det_lu") == 275
    assert M.det(method="Bareis") == 275

    M = Matrix(( (1, 0,  1,  2, 12),
                 (2, 0,  1,  1,  4),
                 (2, 1,  1, -1,  3),
                 (3, 2, -1,  1,  8),
                 (1, 1,  1,  0,  6) ))

    assert M.det(method="bareis") == -55
    assert M.det(method="det_lu") == -55
    assert M.det(method="BAREISS") == -55

    M = Matrix(( (-5,  2,  3,  4,  5),
                 ( 1, -4,  3,  4,  5),
                 ( 1,  2, -3,  4,  5),
                 ( 1,  2,  3, -2,  5),
                 ( 1,  2,  3,  4, -1) ))

    assert M.det(method="bareis") == 11664
    assert M.det(method="det_lu") == 11664
    assert M.det(method="BERKOWITZ") == 11664

    M = Matrix(( ( 2,  7, -1, 3, 2),
                 ( 0,  0,  1, 0, 1),
                 (-2,  0,  7, 0, 2),
                 (-3, -2,  4, 5, 3),
                 ( 1,  0,  0, 0, 1) ))

    assert M.det(method="bareis") == 123
    assert M.det(method="det_lu") == 123
    assert M.det(method="LU") == 123

def test_case_6913():
    m = MatrixSymbol('m', 1, 1)
    a = Symbol("a")
    a = m[0, 0]>0
    assert str(a) == 'm[0, 0] > 0'

def test_issue_15872():
    A = Matrix([[1, 1, 1, 0], [-2, -1, 0, -1], [0, 0, -1, -1], [0, 0, 2, 1]])
    B = A - Matrix.eye(4) * I
    assert B.rank() == 3
    assert (B**2).rank() == 2
    assert (B**3).rank() == 2

def test_issue_11948():
    A = MatrixSymbol('A', 3, 3)
    a = Wild('a')
    assert A.match(a) == {a: A}
