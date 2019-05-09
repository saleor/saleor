from sympy.utilities.pytest import raises
from sympy.core import symbols, pi, S
from sympy.matrices import Identity, MatrixSymbol, ImmutableMatrix, ZeroMatrix
from sympy.matrices.expressions import MatPow, MatAdd, MatMul
from sympy.matrices.expressions.matexpr import ShapeError

n, m, l, k = symbols('n m l k', integer=True)
A = MatrixSymbol('A', n, m)
B = MatrixSymbol('B', m, l)
C = MatrixSymbol('C', n, n)
D = MatrixSymbol('D', n, n)
E = MatrixSymbol('E', m, n)


def test_entry():
    from sympy.concrete import Sum
    assert MatPow(A, 1)[0, 0] == A[0, 0]
    assert MatPow(C, 0)[0, 0] == 1
    assert MatPow(C, 0)[0, 1] == 0
    assert isinstance(MatPow(C, 2)[0, 0], Sum)


def test_as_explicit_symbol():
    X = MatrixSymbol('X', 2, 2)
    assert MatPow(X, 0).as_explicit() == ImmutableMatrix(Identity(2))
    assert MatPow(X, 1).as_explicit() == X.as_explicit()
    assert MatPow(X, 2).as_explicit() == (X.as_explicit())**2


def test_as_explicit_nonsquare_symbol():
    X = MatrixSymbol('X', 2, 3)
    assert MatPow(X, 1).as_explicit() == X.as_explicit()
    for r in [0, 2, S.Half, S.Pi]:
        raises(ShapeError, lambda: MatPow(X, r).as_explicit())


def test_as_explicit():
    A = ImmutableMatrix([[1, 2], [3, 4]])
    assert MatPow(A, 0).as_explicit() == ImmutableMatrix(Identity(2))
    assert MatPow(A, 1).as_explicit() == A
    assert MatPow(A, 2).as_explicit() == A**2
    assert MatPow(A, -1).as_explicit() == A.inv()
    assert MatPow(A, -2).as_explicit() == (A.inv())**2
    # less expensive than testing on a 2x2
    A = ImmutableMatrix([4]);
    assert MatPow(A, S.Half).as_explicit() == A**S.Half


def test_as_explicit_nonsquare():
    A = ImmutableMatrix([[1, 2, 3], [4, 5, 6]])
    assert MatPow(A, 1).as_explicit() == A
    raises(ShapeError, lambda: MatPow(A, 0).as_explicit())
    raises(ShapeError, lambda: MatPow(A, 2).as_explicit())
    raises(ShapeError, lambda: MatPow(A, -1).as_explicit())
    raises(ValueError, lambda: MatPow(A, pi).as_explicit())


def test_doit_nonsquare_MatrixSymbol():
    assert MatPow(A, 1).doit() == A
    for r in [0, 2, -1, pi]:
        assert MatPow(A, r).doit() == MatPow(A, r)


def test_doit_square_MatrixSymbol_symsize():
    assert MatPow(C, 0).doit() == Identity(n)
    assert MatPow(C, 1).doit() == C
    for r in [2, pi]:
        assert MatPow(C, r).doit() == MatPow(C, r)


def test_doit_with_MatrixBase():
    X = ImmutableMatrix([[1, 2], [3, 4]])
    assert MatPow(X, 0).doit() == ImmutableMatrix(Identity(2))
    assert MatPow(X, 1).doit() == X
    assert MatPow(X, 2).doit() == X**2
    assert MatPow(X, -1).doit() == X.inv()
    assert MatPow(X, -2).doit() == (X.inv())**2
    # less expensive than testing on a 2x2
    assert MatPow(ImmutableMatrix([4]), S.Half).doit() == ImmutableMatrix([2])


def test_doit_nonsquare():
    X = ImmutableMatrix([[1, 2, 3], [4, 5, 6]])
    assert MatPow(X, 1).doit() == X
    raises(ShapeError, lambda: MatPow(X, 0).doit())
    raises(ShapeError, lambda: MatPow(X, 2).doit())
    raises(ShapeError, lambda: MatPow(X, -1).doit())
    raises(ShapeError, lambda: MatPow(X, pi).doit())


def test_doit_nested_MatrixExpr():
    X = ImmutableMatrix([[1, 2], [3, 4]])
    Y = ImmutableMatrix([[2, 3], [4, 5]])
    assert MatPow(MatMul(X, Y), 2).doit() == (X*Y)**2
    assert MatPow(MatAdd(X, Y), 2).doit() == (X + Y)**2


def test_identity_power():
    k = Identity(n)
    assert MatPow(k, 4).doit() == k
    assert MatPow(k, n).doit() == k
    assert MatPow(k, -3).doit() == k
    assert MatPow(k, 0).doit() == k
    l = Identity(3)
    assert MatPow(l, n).doit() == l
    assert MatPow(l, -1).doit() == l
    assert MatPow(l, 0).doit() == l


def test_zero_power():
    z1 = ZeroMatrix(n, n)
    assert MatPow(z1, 3).doit() == z1
    raises(ValueError, lambda:MatPow(z1, -1).doit())
    assert MatPow(z1, 0).doit() == Identity(n)
    assert MatPow(z1, n).doit() == z1
    raises(ValueError, lambda:MatPow(z1, -2).doit())
    z2 = ZeroMatrix(4, 4)
    assert MatPow(z2, n).doit() == z2
    raises(ValueError, lambda:MatPow(z2, -3).doit())
    assert MatPow(z2, 2).doit() == z2
    assert MatPow(z2, 0).doit() == Identity(4)
    raises(ValueError, lambda:MatPow(z2, -1).doit())


def test_transpose_power():
    from sympy.matrices.expressions.transpose import Transpose as TP

    assert (C*D).T**5 == ((C*D)**5).T == (D.T * C.T)**5
    assert ((C*D).T**5).T == (C*D)**5

    assert (C.T.I.T)**7 == C**-7
    assert (C.T**l).T**k == C**(l*k)

    assert ((E.T * A.T)**5).T == (A*E)**5
    assert ((A*E).T**5).T**7 == (A*E)**35
    assert TP(TP(C**2 * D**3)**5).doit() == (C**2 * D**3)**5

    assert ((D*C)**-5).T**-5 == ((D*C)**25).T
    assert (((D*C)**l).T**k).T == (D*C)**(l*k)
