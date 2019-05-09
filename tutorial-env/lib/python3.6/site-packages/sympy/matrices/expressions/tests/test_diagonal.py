from sympy.matrices.expressions import MatrixSymbol
from sympy.matrices.expressions.diagonal import DiagonalMatrix, DiagonalOf
from sympy import Symbol, ask, Q, KroneckerDelta
from sympy.utilities.pytest import raises


n = Symbol('n')
m = Symbol('m')


def test_DiagonalMatrix():
    x = MatrixSymbol('x', n, m)
    D = DiagonalMatrix(x)
    assert D.diagonal_length is None
    assert D.shape == (n, m)

    x = MatrixSymbol('x', n, n)
    D = DiagonalMatrix(x)
    assert D.diagonal_length == n
    assert D.shape == (n, n)
    assert D[1, 2] == 0
    assert D[1, 1] == x[1, 1]
    i = Symbol('i')
    j = Symbol('j')
    x = MatrixSymbol('x', 3, 3)
    ij = DiagonalMatrix(x)[i, j]
    assert ij != 0
    assert ij.subs({i:0, j:0}) == x[0, 0]
    assert ij.subs({i:0, j:1}) == 0
    assert ij.subs({i:1, j:1}) == x[1, 1]
    assert ask(Q.diagonal(D))  # affirm that D is diagonal

    x = MatrixSymbol('x', n, 3)
    D = DiagonalMatrix(x)
    assert D.diagonal_length == 3
    assert D.shape == (n, 3)
    assert D[2, m] == KroneckerDelta(2, m)*x[2, m]
    assert D[3, m] == 0
    raises(IndexError, lambda: D[m, 3])

    x = MatrixSymbol('x', 3, n)
    D = DiagonalMatrix(x)
    assert D.diagonal_length == 3
    assert D.shape == (3, n)
    assert D[m, 2] == KroneckerDelta(m, 2)*x[m, 2]
    assert D[m, 3] == 0
    raises(IndexError, lambda: D[3, m])

    x = MatrixSymbol('x', n, m)
    D = DiagonalMatrix(x)
    assert D.diagonal_length is None
    assert D.shape == (n, m)
    assert D[m, 4] != 0

    x = MatrixSymbol('x', 3, 4)
    assert [DiagonalMatrix(x)[i] for i in range(12)] == [
        x[0, 0], 0, 0, 0, 0, x[1, 1], 0, 0, 0, 0, x[2, 2], 0]

    # shape is retained, issue 12427
    assert (
        DiagonalMatrix(MatrixSymbol('x', 3, 4))*
        DiagonalMatrix(MatrixSymbol('x', 4, 2))).shape == (3, 2)


def test_DiagonalOf():
    x = MatrixSymbol('x', n, n)
    d = DiagonalOf(x)
    assert d.shape == (n, 1)
    assert d.diagonal_length == n
    assert d[2, 0] == d[2] == x[2, 2]

    x = MatrixSymbol('x', n, m)
    d = DiagonalOf(x)
    assert d.shape == (None, 1)
    assert d.diagonal_length is None
    assert d[2, 0] == d[2] == x[2, 2]

    d = DiagonalOf(MatrixSymbol('x', 4, 3))
    assert d.shape == (3, 1)
    d = DiagonalOf(MatrixSymbol('x', n, 3))
    assert d.shape == (3, 1)
    d = DiagonalOf(MatrixSymbol('x', 3, n))
    assert d.shape == (3, 1)
    x = MatrixSymbol('x', n, m)
    assert [DiagonalOf(x)[i] for i in range(4)] ==[
        x[0, 0], x[1, 1], x[2, 2], x[3, 3]]
