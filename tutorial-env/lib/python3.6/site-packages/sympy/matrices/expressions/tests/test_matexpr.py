from sympy import (KroneckerDelta, diff, Piecewise, Sum, Dummy, factor,
                   expand, zeros, gcd_terms, Eq)

from sympy.core import S, symbols, Add, Mul, SympifyError
from sympy.core.compatibility import long
from sympy.functions import transpose, sin, cos, sqrt, cbrt, exp
from sympy.simplify import simplify
from sympy.matrices import (Identity, ImmutableMatrix, Inverse, MatAdd, MatMul,
        MatPow, Matrix, MatrixExpr, MatrixSymbol, ShapeError, ZeroMatrix,
        SparseMatrix, Transpose, Adjoint)
from sympy.matrices.expressions.matexpr import (MatrixElement,
    GenericZeroMatrix, GenericIdentity)
from sympy.utilities.pytest import raises, XFAIL


n, m, l, k, p = symbols('n m l k p', integer=True)
x = symbols('x')
A = MatrixSymbol('A', n, m)
B = MatrixSymbol('B', m, l)
C = MatrixSymbol('C', n, n)
D = MatrixSymbol('D', n, n)
E = MatrixSymbol('E', m, n)
w = MatrixSymbol('w', n, 1)


def test_shape():
    assert A.shape == (n, m)
    assert (A*B).shape == (n, l)
    raises(ShapeError, lambda: B*A)


def test_matexpr():
    assert (x*A).shape == A.shape
    assert (x*A).__class__ == MatMul
    assert 2*A - A - A == ZeroMatrix(*A.shape)
    assert (A*B).shape == (n, l)


def test_subs():
    A = MatrixSymbol('A', n, m)
    B = MatrixSymbol('B', m, l)
    C = MatrixSymbol('C', m, l)

    assert A.subs(n, m).shape == (m, m)

    assert (A*B).subs(B, C) == A*C

    assert (A*B).subs(l, n).is_square


def test_ZeroMatrix():
    A = MatrixSymbol('A', n, m)
    Z = ZeroMatrix(n, m)

    assert A + Z == A
    assert A*Z.T == ZeroMatrix(n, n)
    assert Z*A.T == ZeroMatrix(n, n)
    assert A - A == ZeroMatrix(*A.shape)

    assert not Z

    assert transpose(Z) == ZeroMatrix(m, n)
    assert Z.conjugate() == Z

    assert ZeroMatrix(n, n)**0 == Identity(n)
    with raises(ShapeError):
        Z**0
    with raises(ShapeError):
        Z**2


def test_ZeroMatrix_doit():
    Znn = ZeroMatrix(Add(n, n, evaluate=False), n)
    assert isinstance(Znn.rows, Add)
    assert Znn.doit() == ZeroMatrix(2*n, n)
    assert isinstance(Znn.doit().rows, Mul)


def test_Identity():
    A = MatrixSymbol('A', n, m)
    i, j = symbols('i j')

    In = Identity(n)
    Im = Identity(m)

    assert A*Im == A
    assert In*A == A

    assert transpose(In) == In
    assert In.inverse() == In
    assert In.conjugate() == In

    assert In[i, j] != 0
    assert Sum(In[i, j], (i, 0, n-1), (j, 0, n-1)).subs(n,3).doit() == 3
    assert Sum(Sum(In[i, j], (i, 0, n-1)), (j, 0, n-1)).subs(n,3).doit() == 3


def test_Identity_doit():
    Inn = Identity(Add(n, n, evaluate=False))
    assert isinstance(Inn.rows, Add)
    assert Inn.doit() == Identity(2*n)
    assert isinstance(Inn.doit().rows, Mul)


def test_addition():
    A = MatrixSymbol('A', n, m)
    B = MatrixSymbol('B', n, m)

    assert isinstance(A + B, MatAdd)
    assert (A + B).shape == A.shape
    assert isinstance(A - A + 2*B, MatMul)

    raises(ShapeError, lambda: A + B.T)
    raises(TypeError, lambda: A + 1)
    raises(TypeError, lambda: 5 + A)
    raises(TypeError, lambda: 5 - A)

    assert A + ZeroMatrix(n, m) - A == ZeroMatrix(n, m)
    with raises(TypeError):
        ZeroMatrix(n,m) + S(0)


def test_multiplication():
    A = MatrixSymbol('A', n, m)
    B = MatrixSymbol('B', m, l)
    C = MatrixSymbol('C', n, n)

    assert (2*A*B).shape == (n, l)

    assert (A*0*B) == ZeroMatrix(n, l)

    raises(ShapeError, lambda: B*A)
    assert (2*A).shape == A.shape

    assert A * ZeroMatrix(m, m) * B == ZeroMatrix(n, l)

    assert C * Identity(n) * C.I == Identity(n)

    assert B/2 == S.Half*B
    raises(NotImplementedError, lambda: 2/B)

    A = MatrixSymbol('A', n, n)
    B = MatrixSymbol('B', n, n)
    assert Identity(n) * (A + B) == A + B

    assert A**2*A == A**3
    assert A**2*(A.I)**3 == A.I
    assert A**3*(A.I)**2 == A


def test_MatPow():
    A = MatrixSymbol('A', n, n)

    AA = MatPow(A, 2)
    assert AA.exp == 2
    assert AA.base == A
    assert (A**n).exp == n

    assert A**0 == Identity(n)
    assert A**1 == A
    assert A**2 == AA
    assert A**-1 == Inverse(A)
    assert (A**-1)**-1 == A
    assert (A**2)**3 == A**6
    assert A**S.Half == sqrt(A)
    assert A**(S(1)/3) == cbrt(A)
    raises(ShapeError, lambda: MatrixSymbol('B', 3, 2)**2)


def test_MatrixSymbol():
    n, m, t = symbols('n,m,t')
    X = MatrixSymbol('X', n, m)
    assert X.shape == (n, m)
    raises(TypeError, lambda: MatrixSymbol('X', n, m)(t))  # issue 5855
    assert X.doit() == X


def test_dense_conversion():
    X = MatrixSymbol('X', 2, 2)
    assert ImmutableMatrix(X) == ImmutableMatrix(2, 2, lambda i, j: X[i, j])
    assert Matrix(X) == Matrix(2, 2, lambda i, j: X[i, j])


def test_free_symbols():
    assert (C*D).free_symbols == set((C, D))


def test_zero_matmul():
    assert isinstance(S.Zero * MatrixSymbol('X', 2, 2), MatrixExpr)


def test_matadd_simplify():
    A = MatrixSymbol('A', 1, 1)
    assert simplify(MatAdd(A, ImmutableMatrix([[sin(x)**2 + cos(x)**2]]))) == \
        MatAdd(A, ImmutableMatrix([[1]]))


def test_matmul_simplify():
    A = MatrixSymbol('A', 1, 1)
    assert simplify(MatMul(A, ImmutableMatrix([[sin(x)**2 + cos(x)**2]]))) == \
        MatMul(A, ImmutableMatrix([[1]]))


def test_invariants():
    A = MatrixSymbol('A', n, m)
    B = MatrixSymbol('B', m, l)
    X = MatrixSymbol('X', n, n)
    objs = [Identity(n), ZeroMatrix(m, n), A, MatMul(A, B), MatAdd(A, A),
            Transpose(A), Adjoint(A), Inverse(X), MatPow(X, 2), MatPow(X, -1),
            MatPow(X, 0)]
    for obj in objs:
        assert obj == obj.__class__(*obj.args)

def test_indexing():
    A = MatrixSymbol('A', n, m)
    A[1, 2]
    A[l, k]
    A[l+1, k+1]


def test_single_indexing():
    A = MatrixSymbol('A', 2, 3)
    assert A[1] == A[0, 1]
    assert A[long(1)] == A[0, 1]
    assert A[3] == A[1, 0]
    assert list(A[:2, :2]) == [A[0, 0], A[0, 1], A[1, 0], A[1, 1]]
    raises(IndexError, lambda: A[6])
    raises(IndexError, lambda: A[n])
    B = MatrixSymbol('B', n, m)
    raises(IndexError, lambda: B[1])
    B = MatrixSymbol('B', n, 3)
    assert B[3] == B[1, 0]


def test_MatrixElement_commutative():
    assert A[0, 1]*A[1, 0] == A[1, 0]*A[0, 1]


def test_MatrixSymbol_determinant():
    A = MatrixSymbol('A', 4, 4)
    assert A.as_explicit().det() == A[0, 0]*A[1, 1]*A[2, 2]*A[3, 3] - \
        A[0, 0]*A[1, 1]*A[2, 3]*A[3, 2] - A[0, 0]*A[1, 2]*A[2, 1]*A[3, 3] + \
        A[0, 0]*A[1, 2]*A[2, 3]*A[3, 1] + A[0, 0]*A[1, 3]*A[2, 1]*A[3, 2] - \
        A[0, 0]*A[1, 3]*A[2, 2]*A[3, 1] - A[0, 1]*A[1, 0]*A[2, 2]*A[3, 3] + \
        A[0, 1]*A[1, 0]*A[2, 3]*A[3, 2] + A[0, 1]*A[1, 2]*A[2, 0]*A[3, 3] - \
        A[0, 1]*A[1, 2]*A[2, 3]*A[3, 0] - A[0, 1]*A[1, 3]*A[2, 0]*A[3, 2] + \
        A[0, 1]*A[1, 3]*A[2, 2]*A[3, 0] + A[0, 2]*A[1, 0]*A[2, 1]*A[3, 3] - \
        A[0, 2]*A[1, 0]*A[2, 3]*A[3, 1] - A[0, 2]*A[1, 1]*A[2, 0]*A[3, 3] + \
        A[0, 2]*A[1, 1]*A[2, 3]*A[3, 0] + A[0, 2]*A[1, 3]*A[2, 0]*A[3, 1] - \
        A[0, 2]*A[1, 3]*A[2, 1]*A[3, 0] - A[0, 3]*A[1, 0]*A[2, 1]*A[3, 2] + \
        A[0, 3]*A[1, 0]*A[2, 2]*A[3, 1] + A[0, 3]*A[1, 1]*A[2, 0]*A[3, 2] - \
        A[0, 3]*A[1, 1]*A[2, 2]*A[3, 0] - A[0, 3]*A[1, 2]*A[2, 0]*A[3, 1] + \
        A[0, 3]*A[1, 2]*A[2, 1]*A[3, 0]


def test_MatrixElement_diff():
    assert (A[3, 0]*A[0, 0]).diff(A[0, 0]) == A[3, 0]


def test_MatrixElement_doit():
    u = MatrixSymbol('u', 2, 1)
    v = ImmutableMatrix([3, 5])
    assert u[0, 0].subs(u, v).doit() == v[0, 0]


def test_identity_powers():
    M = Identity(n)
    assert MatPow(M, 3).doit() == M**3
    assert M**n == M
    assert MatPow(M, 0).doit() == M**2
    assert M**-2 == M
    assert MatPow(M, -2).doit() == M**0
    N = Identity(3)
    assert MatPow(N, 2).doit() == N**n
    assert MatPow(N, 3).doit() == N
    assert MatPow(N, -2).doit() == N**4
    assert MatPow(N, 2).doit() == N**0


def test_Zero_power():
    z1 = ZeroMatrix(n, n)
    assert z1**4 == z1
    raises(ValueError, lambda:z1**-2)
    assert z1**0 == Identity(n)
    assert MatPow(z1, 2).doit() == z1**2
    raises(ValueError, lambda:MatPow(z1, -2).doit())
    z2 = ZeroMatrix(3, 3)
    assert MatPow(z2, 4).doit() == z2**4
    raises(ValueError, lambda:z2**-3)
    assert z2**3 == MatPow(z2, 3).doit()
    assert z2**0 == Identity(3)
    raises(ValueError, lambda:MatPow(z2, -1).doit())


def test_matrixelement_diff():
    dexpr = diff((D*w)[k,0], w[p,0])

    assert w[k, p].diff(w[k, p]) == 1
    assert w[k, p].diff(w[0, 0]) == KroneckerDelta(0, k)*KroneckerDelta(0, p)
    assert str(dexpr) == "Sum(KroneckerDelta(_i_1, p)*D[k, _i_1], (_i_1, 0, n - 1))"
    assert str(dexpr.doit()) == 'Piecewise((D[k, p], (p >= 0) & (p <= n - 1)), (0, True))'
    # TODO: bug with .dummy_eq( ), the previous 2 lines should be replaced by:
    return  # stop eval
    _i_1 = Dummy("_i_1")
    assert dexpr.dummy_eq(Sum(KroneckerDelta(_i_1, p)*D[k, _i_1], (_i_1, 0, n - 1)))
    assert dexpr.doit().dummy_eq(Piecewise((D[k, p], (p >= 0) & (p <= n - 1)), (0, True)))


def test_MatrixElement_with_values():
    x, y, z, w = symbols("x y z w")
    M = Matrix([[x, y], [z, w]])
    i, j = symbols("i, j")
    Mij = M[i, j]
    assert isinstance(Mij, MatrixElement)
    Ms = SparseMatrix([[2, 3], [4, 5]])
    msij = Ms[i, j]
    assert isinstance(msij, MatrixElement)
    for oi, oj in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        assert Mij.subs({i: oi, j: oj}) == M[oi, oj]
        assert msij.subs({i: oi, j: oj}) == Ms[oi, oj]
    A = MatrixSymbol("A", 2, 2)
    assert A[0, 0].subs(A, M) == x
    assert A[i, j].subs(A, M) == M[i, j]
    assert M[i, j].subs(M, A) == A[i, j]

    assert isinstance(M[3*i - 2, j], MatrixElement)
    assert M[3*i - 2, j].subs({i: 1, j: 0}) == M[1, 0]
    assert isinstance(M[i, 0], MatrixElement)
    assert M[i, 0].subs(i, 0) == M[0, 0]
    assert M[0, i].subs(i, 1) == M[0, 1]

    assert M[i, j].diff(x) == Matrix([[1, 0], [0, 0]])[i, j]

    raises(ValueError, lambda: M[i, 2])
    raises(ValueError, lambda: M[i, -1])
    raises(ValueError, lambda: M[2, i])
    raises(ValueError, lambda: M[-1, i])


def test_inv():
    B = MatrixSymbol('B', 3, 3)
    assert B.inv() == B**-1

@XFAIL
def test_factor_expand():
    A = MatrixSymbol("A", n, n)
    B = MatrixSymbol("B", n, n)
    expr1 = (A + B)*(C + D)
    expr2 = A*C + B*C + A*D + B*D
    assert expr1 != expr2
    assert expand(expr1) == expr2
    assert factor(expr2) == expr1

    expr = B**(-1)*(A**(-1)*B**(-1) - A**(-1)*C*B**(-1))**(-1)*A**(-1)
    I = Identity(n)
    # Ideally we get the first, but we at least don't want a wrong answer
    assert factor(expr) in [I - C, B**-1*(A**-1*(I - C)*B**-1)**-1*A**-1]

def test_issue_2749():
    A = MatrixSymbol("A", 5, 2)
    assert (A.T * A).I.as_explicit() == Matrix([[(A.T * A).I[0, 0], (A.T * A).I[0, 1]], \
    [(A.T * A).I[1, 0], (A.T * A).I[1, 1]]])


def test_issue_2750():
    x = MatrixSymbol('x', 1, 1)
    assert (x.T*x).as_explicit()**-1 == Matrix([[x[0, 0]**(-2)]])


def test_issue_7842():
    A = MatrixSymbol('A', 3, 1)
    B = MatrixSymbol('B', 2, 1)
    assert Eq(A, B) == False
    assert Eq(A[1,0], B[1, 0]).func is Eq
    A = ZeroMatrix(2, 3)
    B = ZeroMatrix(2, 3)
    assert Eq(A, B) == True


def test_generic_zero_matrix():
    z = GenericZeroMatrix()
    A = MatrixSymbol("A", n, n)

    assert z == z
    assert z != A
    assert A != z

    assert z.is_ZeroMatrix

    raises(TypeError, lambda: z.shape)
    raises(TypeError, lambda: z.rows)
    raises(TypeError, lambda: z.cols)

    assert MatAdd() == z
    assert MatAdd(z, A) == MatAdd(A)
    # Make sure it is hashable
    hash(z)


def test_generic_identity():
    I = GenericIdentity()
    A = MatrixSymbol("A", n, n)

    assert I == I
    assert I != A
    assert A != I

    assert I.is_Identity
    assert I**-1 == I

    raises(TypeError, lambda: I.shape)
    raises(TypeError, lambda: I.rows)
    raises(TypeError, lambda: I.cols)

    assert MatMul() == I
    assert MatMul(I, A) == MatMul(A)
    # Make sure it is hashable
    hash(I)

def test_MatMul_postprocessor():
    z = zeros(2)
    z1 = ZeroMatrix(2, 2)
    assert Mul(0, z) == Mul(z, 0) in [z, z1]

    M = Matrix([[1, 2], [3, 4]])
    Mx = Matrix([[x, 2*x], [3*x, 4*x]])
    assert Mul(x, M) == Mul(M, x) == Mx

    A = MatrixSymbol("A", 2, 2)
    assert Mul(A, M) == MatMul(A, M)
    assert Mul(M, A) == MatMul(M, A)
    # Scalars should be absorbed into constant matrices
    a = Mul(x, M, A)
    b = Mul(M, x, A)
    c = Mul(M, A, x)
    assert a == b == c == MatMul(Mx, A)
    a = Mul(x, A, M)
    b = Mul(A, x, M)
    c = Mul(A, M, x)
    assert a == b == c == MatMul(A, Mx)
    assert Mul(M, M) == M**2
    assert Mul(A, M, M) == MatMul(A, M**2)
    assert Mul(M, M, A) == MatMul(M**2, A)
    assert Mul(M, A, M) == MatMul(M, A, M)

    assert Mul(A, x, M, M, x) == MatMul(A, Mx**2)

@XFAIL
def test_MatAdd_postprocessor_xfail():
    # This is difficult to get working because of the way that Add processes
    # its args.
    z = zeros(2)
    assert Add(z, S.NaN) == Add(S.NaN, z)

def test_MatAdd_postprocessor():
    # Some of these are nonsensical, but we do not raise errors for Add
    # because that breaks algorithms that want to replace matrices with dummy
    # symbols.

    z = zeros(2)

    assert Add(0, z) == Add(z, 0) == z

    a = Add(S.Infinity, z)
    assert a == Add(z, S.Infinity)
    assert isinstance(a, Add)
    assert a.args == (S.Infinity, z)

    a = Add(S.ComplexInfinity, z)
    assert a == Add(z, S.ComplexInfinity)
    assert isinstance(a, Add)
    assert a.args == (S.ComplexInfinity, z)

    a = Add(z, S.NaN)
    # assert a == Add(S.NaN, z) # See the XFAIL above
    assert isinstance(a, Add)
    assert a.args == (S.NaN, z)

    M = Matrix([[1, 2], [3, 4]])
    a = Add(x, M)
    assert a == Add(M, x)
    assert isinstance(a, Add)
    assert a.args == (x, M)

    A = MatrixSymbol("A", 2, 2)
    assert Add(A, M) == Add(M, A) == A + M

    # Scalars should be absorbed into constant matrices (producing an error)
    a = Add(x, M, A)
    assert a == Add(M, x, A) == Add(M, A, x) == Add(x, A, M) == Add(A, x, M) == Add(A, M, x)
    assert isinstance(a, Add)
    assert a.args == (x, A + M)

    assert Add(M, M) == 2*M
    assert Add(M, A, M) == Add(M, M, A) == Add(A, M, M) == A + 2*M

    a = Add(A, x, M, M, x)
    assert isinstance(a, Add)
    assert a.args == (2*x, A + 2*M)

def test_simplify_matrix_expressions():
    # Various simplification functions
    assert type(gcd_terms(C*D + D*C)) == MatAdd
    a = gcd_terms(2*C*D + 4*D*C)
    assert type(a) == MatMul
    assert a.args == (2, (C*D + 2*D*C))

def test_exp():
    A = MatrixSymbol('A', 2, 2)
    B = MatrixSymbol('B', 2, 2)
    expr1 = exp(A)*exp(B)
    expr2 = exp(B)*exp(A)
    assert expr1 != expr2
    assert expr1 - expr2 != 0
    assert not isinstance(expr1, exp)
    assert not isinstance(expr2, exp)

def test_invalid_args():
    raises(SympifyError, lambda: MatrixSymbol(1, 2, 'A'))
