from sympy import symbols, IndexedBase
from sympy.codegen.array_utils import (CodegenArrayContraction,
        CodegenArrayTensorProduct, CodegenArrayDiagonal,
        CodegenArrayPermuteDims, CodegenArrayElementwiseAdd,
        _codegen_array_parse, _recognize_matrix_expression, _RecognizeMatOp,
        _RecognizeMatMulLines, _unfold_recognized_expr,
        parse_indexed_expression, recognize_matrix_expression,
        _parse_matrix_expression)
from sympy import (MatrixSymbol, Sum)
from sympy.combinatorics import Permutation
from sympy.functions.special.tensor_functions import KroneckerDelta
from sympy.matrices.expressions.matexpr import MatrixElement
from sympy.matrices import (Trace, MatAdd, MatMul, Transpose)
from sympy.utilities.pytest import raises, XFAIL


A, B = symbols("A B", cls=IndexedBase)
i, j, k, l, m, n = symbols("i j k l m n")

M = MatrixSymbol("M", k, k)
N = MatrixSymbol("N", k, k)
P = MatrixSymbol("P", k, k)
Q = MatrixSymbol("Q", k, k)


def test_codegen_array_contraction_construction():
    cg = CodegenArrayContraction(A)
    assert cg == A

    s = Sum(A[i]*B[i], (i, 0, 3))
    cg = parse_indexed_expression(s)
    assert cg == CodegenArrayContraction(CodegenArrayTensorProduct(A, B), (0, 1))

    cg = CodegenArrayContraction(CodegenArrayTensorProduct(A, B), (1, 0))
    assert cg == CodegenArrayContraction(CodegenArrayTensorProduct(A, B), (0, 1))

    expr = M*N
    result = CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (1, 2))
    assert CodegenArrayContraction.from_MatMul(expr) == result
    elem = expr[i, j]
    assert parse_indexed_expression(elem) == result

    expr = M*N*M
    result = CodegenArrayContraction(CodegenArrayTensorProduct(M, N, M), (1, 2), (3, 4))
    assert CodegenArrayContraction.from_MatMul(expr) == result
    elem = expr[i, j]
    result = CodegenArrayContraction(CodegenArrayTensorProduct(M, M, N), (1, 4), (2, 5))
    cg = parse_indexed_expression(elem)
    cg = cg.sort_args_by_name()
    assert cg == result

def test_codegen_array_contraction_indices_types():
    cg = CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (0, 1))
    indtup = cg._get_contraction_tuples()
    assert indtup == [[(0, 0), (0, 1)]]
    assert cg._contraction_tuples_to_contraction_indices(cg.expr, indtup) == [(0, 1)]

    cg = CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (1, 2))
    indtup = cg._get_contraction_tuples()
    assert indtup == [[(0, 1), (1, 0)]]
    assert cg._contraction_tuples_to_contraction_indices(cg.expr, indtup) == [(1, 2)]

    cg = CodegenArrayContraction(CodegenArrayTensorProduct(M, M, N), (1, 4), (2, 5))
    indtup = cg._get_contraction_tuples()
    assert indtup == [[(0, 1), (2, 0)], [(1, 0), (2, 1)]]
    assert cg._contraction_tuples_to_contraction_indices(cg.expr, indtup) == [(1, 4), (2, 5)]


def test_codegen_array_recognize_matrix_mul_lines():

    cg = CodegenArrayContraction(CodegenArrayTensorProduct(M), (0, 1))
    assert recognize_matrix_expression(cg) == Trace(M)

    cg = CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (0, 1), (2, 3))
    assert recognize_matrix_expression(cg) == [Trace(M), Trace(N)]

    cg = CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (0, 3), (1, 2))
    assert recognize_matrix_expression(cg) == Trace(M*N)

    cg = CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (0, 2), (1, 3))
    assert recognize_matrix_expression(cg) == Trace(M*N.T)

    cg = parse_indexed_expression((M*N*P)[i,j])
    assert recognize_matrix_expression(cg) == M*N*P
    cg = CodegenArrayContraction.from_MatMul(M*N*P)
    assert recognize_matrix_expression(cg) == M*N*P

    cg = parse_indexed_expression((M*N.T*P)[i,j])
    assert recognize_matrix_expression(cg) == M*N.T*P
    cg = CodegenArrayContraction.from_MatMul(M*N.T*P)
    assert recognize_matrix_expression(cg) == M*N.T*P

    cg = CodegenArrayContraction(CodegenArrayTensorProduct(M,N,P,Q), (1, 2), (5, 6))
    assert recognize_matrix_expression(cg) == [M*N, P*Q]

    expr = -2*M*N
    elem = expr[i, j]
    cg = parse_indexed_expression(elem)
    assert recognize_matrix_expression(cg) == -2*M*N


def test_codegen_array_flatten():

    # Flatten nested CodegenArrayTensorProduct objects:
    expr1 = CodegenArrayTensorProduct(M, N)
    expr2 = CodegenArrayTensorProduct(P, Q)
    expr = CodegenArrayTensorProduct(expr1, expr2)
    assert expr == CodegenArrayTensorProduct(M, N, P, Q)
    assert expr.args == (M, N, P, Q)

    # Flatten mixed CodegenArrayTensorProduct and CodegenArrayContraction objects:
    cg1 = CodegenArrayContraction(expr1, (1, 2))
    cg2 = CodegenArrayContraction(expr2, (0, 3))

    expr = CodegenArrayTensorProduct(cg1, cg2)
    assert expr == CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P, Q), (1, 2), (4, 7))

    expr = CodegenArrayTensorProduct(M, cg1)
    assert expr == CodegenArrayContraction(CodegenArrayTensorProduct(M, M, N), (3, 4))

    # Flatten nested CodegenArrayContraction objects:
    cgnested = CodegenArrayContraction(cg1, (0, 1))
    assert cgnested == CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (0, 3), (1, 2))

    cgnested = CodegenArrayContraction(CodegenArrayTensorProduct(cg1, cg2), (0, 3))
    assert cgnested == CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P, Q), (0, 6), (1, 2), (4, 7))

    cg3 = CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P, Q), (1, 3), (2, 4))
    cgnested = CodegenArrayContraction(cg3, (0, 1))
    assert cgnested == CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P, Q), (0, 5), (1, 3), (2, 4))

    cgnested = CodegenArrayContraction(cg3, (0, 3), (1, 2))
    assert cgnested == CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P, Q), (0, 7), (1, 3), (2, 4), (5, 6))

    cg4 = CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P, Q), (1, 5), (3, 7))
    cgnested = CodegenArrayContraction(cg4, (0, 1))
    assert cgnested == CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P, Q), (0, 2), (1, 5), (3, 7))

    cgnested = CodegenArrayContraction(cg4, (0, 1), (2, 3))
    assert cgnested == CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P, Q), (0, 2), (1, 5), (3, 7), (4, 6))

    # Flatten nested CodegenArrayDiagonal objects:
    cg1 = CodegenArrayDiagonal(expr1, (1, 2))
    cg2 = CodegenArrayDiagonal(expr2, (0, 3))
    cg3 = CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N, P, Q), (1, 3), (2, 4))
    cg4 = CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N, P, Q), (1, 5), (3, 7))

    cgnested = CodegenArrayDiagonal(cg1, (0, 1))
    assert cgnested == CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N), (1, 2), (0, 3))

    cgnested = CodegenArrayDiagonal(cg3, (1, 2))
    assert cgnested == CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N, P, Q), (1, 3), (2, 4), (5, 6))

    cgnested = CodegenArrayDiagonal(cg4, (1, 2))
    assert cgnested == CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N, P, Q), (1, 5), (3, 7), (2, 4))


def test_codegen_array_parse():
    expr = M[i, j]
    assert _codegen_array_parse(expr) == (M, (i, j))
    expr = M[i, j]*N[k, l]
    assert _codegen_array_parse(expr) == (CodegenArrayTensorProduct(M, N), (i, j, k, l))
    expr = M[i, j]*N[j, k]
    assert _codegen_array_parse(expr) == (CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N), (1, 2)), (i, k, j))
    expr = Sum(M[i, j]*N[j, k], (j, 0, k-1))
    assert _codegen_array_parse(expr) == (CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (1, 2)), (i, k))
    expr = M[i, j] + N[i, j]
    assert _codegen_array_parse(expr) == (CodegenArrayElementwiseAdd(M, N), (i, j))
    expr = M[i, j] + N[j, i]
    assert _codegen_array_parse(expr) == (CodegenArrayElementwiseAdd(M, CodegenArrayPermuteDims(N, Permutation([1,0]))), (i, j))
    expr = M[i, j] + M[j, i]
    assert _codegen_array_parse(expr) == (CodegenArrayElementwiseAdd(M, CodegenArrayPermuteDims(M, Permutation([1,0]))), (i, j))
    expr = (M*N*P)[i, j]
    assert _codegen_array_parse(expr) == (CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P), (1, 2), (3, 4)), (i, j))
    expr = expr.function  # Disregard summation in previous expression
    ret1, ret2 =  _codegen_array_parse(expr)
    assert ret1 == CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N, P), (1, 2), (3, 4))
    assert str(ret2) == "(i, j, _i_1, _i_2)"
    expr = KroneckerDelta(i, j)*M[i, k]
    assert _codegen_array_parse(expr) == (M, ({i, j}, k))
    expr = KroneckerDelta(i, j)*KroneckerDelta(j, k)*M[i, l]
    assert _codegen_array_parse(expr) == (M, ({i, j, k}, l))
    expr = KroneckerDelta(j, k)*(M[i, j]*N[k, l] + N[i, j]*M[k, l])
    assert _codegen_array_parse(expr) == (CodegenArrayDiagonal(CodegenArrayElementwiseAdd(
            CodegenArrayTensorProduct(M, N),
            CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), Permutation(0, 2)(1, 3))
        ), (1, 2)), (i, l, frozenset({j, k})))
    expr = KroneckerDelta(j, m)*KroneckerDelta(m, k)*(M[i, j]*N[k, l] + N[i, j]*M[k, l])
    assert _codegen_array_parse(expr) == (CodegenArrayDiagonal(CodegenArrayElementwiseAdd(
            CodegenArrayTensorProduct(M, N),
            CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), Permutation(0, 2)(1, 3))
        ), (1, 2)), (i, l, frozenset({j, m, k})))
    expr = KroneckerDelta(i, j)*KroneckerDelta(j, k)*KroneckerDelta(k,m)*M[i, 0]*KroneckerDelta(m, n)
    assert _codegen_array_parse(expr) == (M, ({i,j,k,m,n}, 0))
    expr = M[i, i]
    assert _codegen_array_parse(expr) == (CodegenArrayDiagonal(M, (0, 1)), (i,))


def test_codegen_array_diagonal():
    cg = CodegenArrayDiagonal(M, (1, 0))
    assert cg == CodegenArrayDiagonal(M, (0, 1))

    cg = CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N, P), (4, 1), (2, 0))
    assert cg == CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N, P), (1, 4), (0, 2))


def test_codegen_recognize_matrix_expression():

    expr = CodegenArrayElementwiseAdd(M, CodegenArrayPermuteDims(M, [1, 0]))
    rec = _recognize_matrix_expression(expr)
    assert rec == _RecognizeMatOp(MatAdd, [M, _RecognizeMatOp(Transpose, [M])])
    assert _unfold_recognized_expr(rec) == M + Transpose(M)

    expr = M[i,j] + N[i,j]
    p1, p2 = _codegen_array_parse(expr)
    rec = _recognize_matrix_expression(p1)
    assert rec == _RecognizeMatOp(MatAdd, [M, N])
    assert _unfold_recognized_expr(rec) == M + N

    expr = M[i,j] + N[j,i]
    p1, p2 = _codegen_array_parse(expr)
    rec = _recognize_matrix_expression(p1)
    assert rec == _RecognizeMatOp(MatAdd, [M, _RecognizeMatOp(Transpose, [N])])
    assert _unfold_recognized_expr(rec) == M + N.T

    expr = M[i,j]*N[k,l] + N[i,j]*M[k,l]
    p1, p2 = _codegen_array_parse(expr)
    rec = _recognize_matrix_expression(p1)
    assert rec == _RecognizeMatOp(MatAdd, [_RecognizeMatMulLines([M, N]), _RecognizeMatMulLines([N, M])])
    #assert _unfold_recognized_expr(rec) == TensorProduct(M, N) + TensorProduct(N, M) maybe?

    expr = (M*N*P)[i, j]
    p1, p2 = _codegen_array_parse(expr)
    rec = _recognize_matrix_expression(p1)
    assert rec == _RecognizeMatMulLines([_RecognizeMatOp(MatMul, [M, N, P])])
    assert _unfold_recognized_expr(rec) == M*N*P

    expr = Sum(M[i,j]*(N*P)[j,m], (j, 0, k-1))
    p1, p2 = _codegen_array_parse(expr)
    rec = _recognize_matrix_expression(p1)
    assert rec == _RecognizeMatOp(MatMul, [M, N, P])
    assert _unfold_recognized_expr(rec) == M*N*P

    expr = Sum((P[j, m] + P[m, j])*(M[i,j]*N[m,n] + N[i,j]*M[m,n]), (j, 0, k-1), (m, 0, k-1))
    p1, p2 = _codegen_array_parse(expr)
    rec = _recognize_matrix_expression(p1)
    assert rec == _RecognizeMatOp(MatAdd, [
        _RecognizeMatOp(MatMul, [M, _RecognizeMatOp(MatAdd, [P, _RecognizeMatOp(Transpose, [P])]), N]),
        _RecognizeMatOp(MatMul, [N, _RecognizeMatOp(MatAdd, [P, _RecognizeMatOp(Transpose, [P])]), M])
        ])
    assert _unfold_recognized_expr(rec) == M*(P + P.T)*N + N*(P + P.T)*M


def test_codegen_array_shape():
    expr = CodegenArrayTensorProduct(M, N, P, Q)
    assert expr.shape == (k, k, k, k, k, k, k, k)
    Z = MatrixSymbol("Z", m, n)
    expr = CodegenArrayTensorProduct(M, Z)
    assert expr.shape == (k, k, m, n)
    expr2 = CodegenArrayContraction(expr, (0, 1))
    assert expr2.shape == (m, n)
    expr2 = CodegenArrayDiagonal(expr, (0, 1))
    assert expr2.shape == (m, n, k)
    exprp = CodegenArrayPermuteDims(expr, [2, 1, 3, 0])
    assert exprp.shape == (m, k, n, k)
    expr3 = CodegenArrayTensorProduct(N, Z)
    expr2 = CodegenArrayElementwiseAdd(expr, expr3)
    assert expr2.shape == (k, k, m, n)

    # Contraction along axes with discordant dimensions:
    raises(ValueError, lambda: CodegenArrayContraction(expr, (1, 2)))
    # Also diagonal needs the same dimensions:
    raises(ValueError, lambda: CodegenArrayDiagonal(expr, (1, 2)))


def test_codegen_array_parse_out_of_bounds():

    expr = Sum(M[i, i], (i, 0, 4))
    raises(ValueError, lambda: parse_indexed_expression(expr))
    expr = Sum(M[i, i], (i, 0, k))
    raises(ValueError, lambda: parse_indexed_expression(expr))
    expr = Sum(M[i, i], (i, 1, k-1))
    raises(ValueError, lambda: parse_indexed_expression(expr))

    expr = Sum(M[i, j]*N[j,m], (j, 0, 4))
    raises(ValueError, lambda: parse_indexed_expression(expr))
    expr = Sum(M[i, j]*N[j,m], (j, 0, k))
    raises(ValueError, lambda: parse_indexed_expression(expr))
    expr = Sum(M[i, j]*N[j,m], (j, 1, k-1))
    raises(ValueError, lambda: parse_indexed_expression(expr))


def test_codegen_permutedims_sink():

    cg = CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), [0, 1, 3, 2])
    sunk = cg.nest_permutation()
    assert sunk == CodegenArrayTensorProduct(M, CodegenArrayPermuteDims(N, [1, 0]))
    assert recognize_matrix_expression(sunk) == [M, N.T]

    cg = CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), [1, 0, 3, 2])
    sunk = cg.nest_permutation()
    assert sunk == CodegenArrayTensorProduct(CodegenArrayPermuteDims(M, [1, 0]), CodegenArrayPermuteDims(N, [1, 0]))
    assert recognize_matrix_expression(sunk) == [M.T, N.T]

    cg = CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), [3, 2, 1, 0])
    sunk = cg.nest_permutation()
    assert sunk == CodegenArrayTensorProduct(CodegenArrayPermuteDims(N, [1, 0]), CodegenArrayPermuteDims(M, [1, 0]))
    assert recognize_matrix_expression(sunk) == [N.T, M.T]

    cg = CodegenArrayPermuteDims(CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (1, 2)), [1, 0])
    sunk = cg.nest_permutation()
    assert sunk == CodegenArrayContraction(CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), [[0, 3]]), (1, 2))

    cg = CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), [1, 0, 3, 2])
    sunk = cg.nest_permutation()
    assert sunk == CodegenArrayTensorProduct(CodegenArrayPermuteDims(M, [1, 0]), CodegenArrayPermuteDims(N, [1, 0]))

    cg = CodegenArrayPermuteDims(CodegenArrayContraction(CodegenArrayTensorProduct(M, N, P), (1, 2), (3, 4)), [1, 0])
    sunk = cg.nest_permutation()
    assert sunk == CodegenArrayContraction(CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N, P), [[0, 5]]), (1, 2), (3, 4))
    sunk2 = sunk.expr.nest_permutation()


def test_parsing_of_matrix_expressions():

    expr = M*N
    assert _parse_matrix_expression(expr) == CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (1, 2))

    expr = Transpose(M)
    assert _parse_matrix_expression(expr) == CodegenArrayPermuteDims(M, [1, 0])

    expr = M*Transpose(N)
    assert _parse_matrix_expression(expr) == CodegenArrayContraction(CodegenArrayTensorProduct(M, CodegenArrayPermuteDims(N, [1, 0])), (1, 2))


def test_special_matrices():
    a = MatrixSymbol("a", k, 1)
    b = MatrixSymbol("b", k, 1)

    expr = a.T*b
    elem = expr[0, 0]
    cg = parse_indexed_expression(elem)
    assert cg == CodegenArrayContraction(CodegenArrayTensorProduct(a, b), (0, 2))
    assert recognize_matrix_expression(cg) == a.T*b
