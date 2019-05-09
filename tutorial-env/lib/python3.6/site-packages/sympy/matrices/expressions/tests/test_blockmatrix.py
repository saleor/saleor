from sympy.matrices.expressions.blockmatrix import (block_collapse, bc_matmul,
        bc_block_plus_ident, BlockDiagMatrix, BlockMatrix, bc_dist, bc_matadd,
        bc_transpose, blockcut, reblock_2x2, deblock)
from sympy.matrices.expressions import (MatrixSymbol, Identity,
        Inverse, trace, Transpose, det)
from sympy.matrices import Matrix, ImmutableMatrix
from sympy.core import Tuple, symbols, Expr
from sympy.core.compatibility import range
from sympy.functions import transpose

i, j, k, l, m, n, p = symbols('i:n, p', integer=True)
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
C = MatrixSymbol('C', n, n)
D = MatrixSymbol('D', n, n)
G = MatrixSymbol('G', n, n)
H = MatrixSymbol('H', n, n)
b1 = BlockMatrix([[G, H]])
b2 = BlockMatrix([[G], [H]])

def test_bc_matmul():
    assert bc_matmul(H*b1*b2*G) == BlockMatrix([[(H*G*G + H*H*H)*G]])

def test_bc_matadd():
    assert bc_matadd(BlockMatrix([[G, H]]) + BlockMatrix([[H, H]])) == \
            BlockMatrix([[G+H, H+H]])

def test_bc_transpose():
    assert bc_transpose(Transpose(BlockMatrix([[A, B], [C, D]]))) == \
            BlockMatrix([[A.T, C.T], [B.T, D.T]])

def test_bc_dist_diag():
    A = MatrixSymbol('A', n, n)
    B = MatrixSymbol('B', m, m)
    C = MatrixSymbol('C', l, l)
    X = BlockDiagMatrix(A, B, C)

    assert bc_dist(X+X).equals(BlockDiagMatrix(2*A, 2*B, 2*C))

def test_block_plus_ident():
    A = MatrixSymbol('A', n, n)
    B = MatrixSymbol('B', n, m)
    C = MatrixSymbol('C', m, n)
    D = MatrixSymbol('D', m, m)
    X = BlockMatrix([[A, B], [C, D]])
    assert bc_block_plus_ident(X+Identity(m+n)) == \
            BlockDiagMatrix(Identity(n), Identity(m)) + X

def test_BlockMatrix():
    A = MatrixSymbol('A', n, m)
    B = MatrixSymbol('B', n, k)
    C = MatrixSymbol('C', l, m)
    D = MatrixSymbol('D', l, k)
    M = MatrixSymbol('M', m + k, p)
    N = MatrixSymbol('N', l + n, k + m)
    X = BlockMatrix(Matrix([[A, B], [C, D]]))

    assert X.__class__(*X.args) == X

    # block_collapse does nothing on normal inputs
    E = MatrixSymbol('E', n, m)
    assert block_collapse(A + 2*E) == A + 2*E
    F = MatrixSymbol('F', m, m)
    assert block_collapse(E.T*A*F) == E.T*A*F

    assert X.shape == (l + n, k + m)
    assert X.blockshape == (2, 2)
    assert transpose(X) == BlockMatrix(Matrix([[A.T, C.T], [B.T, D.T]]))
    assert transpose(X).shape == X.shape[::-1]

    # Test that BlockMatrices and MatrixSymbols can still mix
    assert (X*M).is_MatMul
    assert X._blockmul(M).is_MatMul
    assert (X*M).shape == (n + l, p)
    assert (X + N).is_MatAdd
    assert X._blockadd(N).is_MatAdd
    assert (X + N).shape == X.shape

    E = MatrixSymbol('E', m, 1)
    F = MatrixSymbol('F', k, 1)

    Y = BlockMatrix(Matrix([[E], [F]]))

    assert (X*Y).shape == (l + n, 1)
    assert block_collapse(X*Y).blocks[0, 0] == A*E + B*F
    assert block_collapse(X*Y).blocks[1, 0] == C*E + D*F

    # block_collapse passes down into container objects, transposes, and inverse
    assert block_collapse(transpose(X*Y)) == transpose(block_collapse(X*Y))
    assert block_collapse(Tuple(X*Y, 2*X)) == (
        block_collapse(X*Y), block_collapse(2*X))

    # Make sure that MatrixSymbols will enter 1x1 BlockMatrix if it simplifies
    Ab = BlockMatrix([[A]])
    Z = MatrixSymbol('Z', *A.shape)
    assert block_collapse(Ab + Z) == A + Z


def test_BlockMatrix_trace():
    A, B, C, D = [MatrixSymbol(s, 3, 3) for s in 'ABCD']
    X = BlockMatrix([[A, B], [C, D]])
    assert trace(X) == trace(A) + trace(D)

def test_BlockMatrix_Determinant():
    A, B, C, D = [MatrixSymbol(s, 3, 3) for s in 'ABCD']
    X = BlockMatrix([[A, B], [C, D]])
    from sympy import assuming, Q
    with assuming(Q.invertible(A)):
        assert det(X) == det(A) * det(D - C*A.I*B)

    assert isinstance(det(X), Expr)

def test_squareBlockMatrix():
    A = MatrixSymbol('A', n, n)
    B = MatrixSymbol('B', n, m)
    C = MatrixSymbol('C', m, n)
    D = MatrixSymbol('D', m, m)
    X = BlockMatrix([[A, B], [C, D]])
    Y = BlockMatrix([[A]])

    assert X.is_square

    assert (block_collapse(X + Identity(m + n)) ==
        BlockMatrix([[A + Identity(n), B], [C, D + Identity(m)]]))
    Q = X + Identity(m + n)

    assert (X + MatrixSymbol('Q', n + m, n + m)).is_MatAdd
    assert (X * MatrixSymbol('Q', n + m, n + m)).is_MatMul

    assert block_collapse(Y.I) == A.I
    assert block_collapse(X.inverse()) == BlockMatrix([
        [(-B*D.I*C + A).I, -A.I*B*(D + -C*A.I*B).I],
        [-(D - C*A.I*B).I*C*A.I, (D - C*A.I*B).I]])

    assert isinstance(X.inverse(), Inverse)

    assert not X.is_Identity

    Z = BlockMatrix([[Identity(n), B], [C, D]])
    assert not Z.is_Identity


def test_BlockDiagMatrix():
    A = MatrixSymbol('A', n, n)
    B = MatrixSymbol('B', m, m)
    C = MatrixSymbol('C', l, l)
    M = MatrixSymbol('M', n + m + l, n + m + l)

    X = BlockDiagMatrix(A, B, C)
    Y = BlockDiagMatrix(A, 2*B, 3*C)

    assert X.blocks[1, 1] == B
    assert X.shape == (n + m + l, n + m + l)
    assert all(X.blocks[i, j].is_ZeroMatrix if i != j else X.blocks[i, j] in [A, B, C]
            for i in range(3) for j in range(3))
    assert X.__class__(*X.args) == X

    assert isinstance(block_collapse(X.I * X), Identity)

    assert bc_matmul(X*X) == BlockDiagMatrix(A*A, B*B, C*C)
    assert block_collapse(X*X) == BlockDiagMatrix(A*A, B*B, C*C)
    #XXX: should be == ??
    assert block_collapse(X + X).equals(BlockDiagMatrix(2*A, 2*B, 2*C))
    assert block_collapse(X*Y) == BlockDiagMatrix(A*A, 2*B*B, 3*C*C)
    assert block_collapse(X + Y) == BlockDiagMatrix(2*A, 3*B, 4*C)

    # Ensure that BlockDiagMatrices can still interact with normal MatrixExprs
    assert (X*(2*M)).is_MatMul
    assert (X + (2*M)).is_MatAdd

    assert (X._blockmul(M)).is_MatMul
    assert (X._blockadd(M)).is_MatAdd

def test_blockcut():
    A = MatrixSymbol('A', n, m)
    B = blockcut(A, (n/2, n/2), (m/2, m/2))
    assert A[i, j] == B[i, j]
    assert B == BlockMatrix([[A[:n/2, :m/2], A[:n/2, m/2:]],
                             [A[n/2:, :m/2], A[n/2:, m/2:]]])

    M = ImmutableMatrix(4, 4, range(16))
    B = blockcut(M, (2, 2), (2, 2))
    assert M == ImmutableMatrix(B)

    B = blockcut(M, (1, 3), (2, 2))
    assert ImmutableMatrix(B.blocks[0, 1]) == ImmutableMatrix([[2, 3]])

def test_reblock_2x2():
    B = BlockMatrix([[MatrixSymbol('A_%d%d'%(i,j), 2, 2)
                            for j in range(3)]
                            for i in range(3)])
    assert B.blocks.shape == (3, 3)

    BB = reblock_2x2(B)
    assert BB.blocks.shape == (2, 2)

    assert B.shape == BB.shape
    assert B.as_explicit() == BB.as_explicit()

def test_deblock():
    B = BlockMatrix([[MatrixSymbol('A_%d%d'%(i,j), n, n)
                    for j in range(4)]
                    for i in range(4)])

    assert deblock(reblock_2x2(B)) == B
