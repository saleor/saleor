from sympy import (Piecewise, lambdify, Equality, Unequality, Sum, Mod, cbrt,
        sqrt, MatrixSymbol)
from sympy import eye
from sympy.abc import x, i, j, a, b, c, d
from sympy.codegen.cfunctions import log1p, expm1, hypot, log10, exp2, log2, Cbrt, Sqrt
from sympy.codegen.array_utils import (CodegenArrayContraction,
        CodegenArrayTensorProduct, CodegenArrayDiagonal,
        CodegenArrayPermuteDims, CodegenArrayElementwiseAdd)
from sympy.printing.lambdarepr import NumPyPrinter

from sympy.utilities.pytest import warns_deprecated_sympy
from sympy.utilities.pytest import skip
from sympy.external import import_module

np = import_module('numpy')

def test_numpy_piecewise_regression():
    """
    NumPyPrinter needs to print Piecewise()'s choicelist as a list to avoid
    breaking compatibility with numpy 1.8. This is not necessary in numpy 1.9+.
    See gh-9747 and gh-9749 for details.
    """
    p = Piecewise((1, x < 0), (0, True))
    assert NumPyPrinter().doprint(p) == 'numpy.select([numpy.less(x, 0),True], [1,0], default=numpy.nan)'


def test_sum():
    if not np:
        skip("NumPy not installed")

    s = Sum(x ** i, (i, a, b))
    f = lambdify((a, b, x), s, 'numpy')

    a_, b_ = 0, 10
    x_ = np.linspace(-1, +1, 10)
    assert np.allclose(f(a_, b_, x_), sum(x_ ** i_ for i_ in range(a_, b_ + 1)))

    s = Sum(i * x, (i, a, b))
    f = lambdify((a, b, x), s, 'numpy')

    a_, b_ = 0, 10
    x_ = np.linspace(-1, +1, 10)
    assert np.allclose(f(a_, b_, x_), sum(i_ * x_ for i_ in range(a_, b_ + 1)))


def test_multiple_sums():
    if not np:
        skip("NumPy not installed")

    s = Sum((x + j) * i, (i, a, b), (j, c, d))
    f = lambdify((a, b, c, d, x), s, 'numpy')

    a_, b_ = 0, 10
    c_, d_ = 11, 21
    x_ = np.linspace(-1, +1, 10)
    assert np.allclose(f(a_, b_, c_, d_, x_),
                       sum((x_ + j_) * i_ for i_ in range(a_, b_ + 1) for j_ in range(c_, d_ + 1)))


def test_codegen_einsum():
    if not np:
        skip("NumPy not installed")

    M = MatrixSymbol("M", 2, 2)
    N = MatrixSymbol("N", 2, 2)

    cg = CodegenArrayContraction.from_MatMul(M*N)
    f = lambdify((M, N), cg, 'numpy')

    ma = np.matrix([[1, 2], [3, 4]])
    mb = np.matrix([[1,-2], [-1, 3]])
    assert (f(ma, mb) == ma*mb).all()


def test_codegen_extra():
    if not np:
        skip("NumPy not installed")

    M = MatrixSymbol("M", 2, 2)
    N = MatrixSymbol("N", 2, 2)
    P = MatrixSymbol("P", 2, 2)
    Q = MatrixSymbol("Q", 2, 2)
    ma = np.matrix([[1, 2], [3, 4]])
    mb = np.matrix([[1,-2], [-1, 3]])
    mc = np.matrix([[2, 0], [1, 2]])
    md = np.matrix([[1,-1], [4, 7]])

    cg = CodegenArrayTensorProduct(M, N)
    f = lambdify((M, N), cg, 'numpy')
    assert (f(ma, mb) == np.einsum(ma, [0, 1], mb, [2, 3])).all()

    cg = CodegenArrayElementwiseAdd(M, N)
    f = lambdify((M, N), cg, 'numpy')
    assert (f(ma, mb) == ma+mb).all()

    cg = CodegenArrayElementwiseAdd(M, N, P)
    f = lambdify((M, N, P), cg, 'numpy')
    assert (f(ma, mb, mc) == ma+mb+mc).all()

    cg = CodegenArrayElementwiseAdd(M, N, P, Q)
    f = lambdify((M, N, P, Q), cg, 'numpy')
    assert (f(ma, mb, mc, md) == ma+mb+mc+md).all()

    cg = CodegenArrayPermuteDims(M, [1, 0])
    f = lambdify((M,), cg, 'numpy')
    assert (f(ma) == ma.T).all()

    cg = CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), [1, 2, 3, 0])
    f = lambdify((M, N), cg, 'numpy')
    assert (f(ma, mb) == np.transpose(np.einsum(ma, [0, 1], mb, [2, 3]), (1, 2, 3, 0))).all()

    cg = CodegenArrayDiagonal(CodegenArrayTensorProduct(M, N), (1, 2))
    f = lambdify((M, N), cg, 'numpy')
    assert (f(ma, mb) == np.diagonal(np.einsum(ma, [0, 1], mb, [2, 3]), axis1=1, axis2=2)).all()


def test_relational():
    if not np:
        skip("NumPy not installed")

    e = Equality(x, 1)

    f = lambdify((x,), e)
    x_ = np.array([0, 1, 2])
    assert np.array_equal(f(x_), [False, True, False])

    e = Unequality(x, 1)

    f = lambdify((x,), e)
    x_ = np.array([0, 1, 2])
    assert np.array_equal(f(x_), [True, False, True])

    e = (x < 1)

    f = lambdify((x,), e)
    x_ = np.array([0, 1, 2])
    assert np.array_equal(f(x_), [True, False, False])

    e = (x <= 1)

    f = lambdify((x,), e)
    x_ = np.array([0, 1, 2])
    assert np.array_equal(f(x_), [True, True, False])

    e = (x > 1)

    f = lambdify((x,), e)
    x_ = np.array([0, 1, 2])
    assert np.array_equal(f(x_), [False, False, True])

    e = (x >= 1)

    f = lambdify((x,), e)
    x_ = np.array([0, 1, 2])
    assert np.array_equal(f(x_), [False, True, True])


def test_mod():
    if not np:
        skip("NumPy not installed")

    e = Mod(a, b)
    f = lambdify((a, b), e)

    a_ = np.array([0, 1, 2, 3])
    b_ = 2
    assert np.array_equal(f(a_, b_), [0, 1, 0, 1])

    a_ = np.array([0, 1, 2, 3])
    b_ = np.array([2, 2, 2, 2])
    assert np.array_equal(f(a_, b_), [0, 1, 0, 1])

    a_ = np.array([2, 3, 4, 5])
    b_ = np.array([2, 3, 4, 5])
    assert np.array_equal(f(a_, b_), [0, 0, 0, 0])


def test_expm1():
    if not np:
        skip("NumPy not installed")

    f = lambdify((a,), expm1(a), 'numpy')
    assert abs(f(1e-10) - 1e-10 - 5e-21) < 1e-22


def test_log1p():
    if not np:
        skip("NumPy not installed")

    f = lambdify((a,), log1p(a), 'numpy')
    assert abs(f(1e-99) - 1e-99) < 1e-100

def test_hypot():
    if not np:
        skip("NumPy not installed")
    assert abs(lambdify((a, b), hypot(a, b), 'numpy')(3, 4) - 5) < 1e-16

def test_log10():
    if not np:
        skip("NumPy not installed")
    assert abs(lambdify((a,), log10(a), 'numpy')(100) - 2) < 1e-16


def test_exp2():
    if not np:
        skip("NumPy not installed")
    assert abs(lambdify((a,), exp2(a), 'numpy')(5) - 32) < 1e-16


def test_log2():
    if not np:
        skip("NumPy not installed")
    assert abs(lambdify((a,), log2(a), 'numpy')(256) - 8) < 1e-16


def test_Sqrt():
    if not np:
        skip("NumPy not installed")
    assert abs(lambdify((a,), Sqrt(a), 'numpy')(4) - 2) < 1e-16


def test_sqrt():
    if not np:
        skip("NumPy not installed")
    assert abs(lambdify((a,), sqrt(a), 'numpy')(4) - 2) < 1e-16

def test_issue_15601():
    if not np:
        skip("Numpy not installed")

    M = MatrixSymbol("M", 3, 3)
    N = MatrixSymbol("N", 3, 3)
    expr = M*N
    f = lambdify((M, N), expr, "numpy")

    with warns_deprecated_sympy():
        ans = f(eye(3), eye(3))
        assert np.array_equal(ans, np.array([1, 0, 0, 0, 1, 0, 0, 0, 1]))
