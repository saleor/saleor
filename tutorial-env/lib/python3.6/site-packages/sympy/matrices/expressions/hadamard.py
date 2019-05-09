from __future__ import print_function, division

from sympy.core import Mul, sympify
from sympy.strategies import unpack, flatten, condition, exhaust, do_one

from sympy.matrices.expressions.matexpr import MatrixExpr, ShapeError

def hadamard_product(*matrices):
    """
    Return the elementwise (aka Hadamard) product of matrices.

    Examples
    ========

    >>> from sympy.matrices import hadamard_product, MatrixSymbol
    >>> A = MatrixSymbol('A', 2, 3)
    >>> B = MatrixSymbol('B', 2, 3)
    >>> hadamard_product(A)
    A
    >>> hadamard_product(A, B)
    A.*B
    >>> hadamard_product(A, B)[0, 1]
    A[0, 1]*B[0, 1]
    """
    if not matrices:
        raise TypeError("Empty Hadamard product is undefined")
    validate(*matrices)
    if len(matrices) == 1:
        return matrices[0]
    else:
        return HadamardProduct(*matrices).doit()


class HadamardProduct(MatrixExpr):
    """
    Elementwise product of matrix expressions

    This is a symbolic object that simply stores its argument without
    evaluating it. To actually compute the product, use the function
    ``hadamard_product()``.

    >>> from sympy.matrices import hadamard_product, HadamardProduct, MatrixSymbol
    >>> A = MatrixSymbol('A', 5, 5)
    >>> B = MatrixSymbol('B', 5, 5)
    >>> isinstance(hadamard_product(A, B), HadamardProduct)
    True
    """
    is_HadamardProduct = True

    def __new__(cls, *args, **kwargs):
        args = list(map(sympify, args))
        check = kwargs.get('check'   , True)
        if check:
            validate(*args)
        return super(HadamardProduct, cls).__new__(cls, *args)

    @property
    def shape(self):
        return self.args[0].shape

    def _entry(self, i, j):
        return Mul(*[arg._entry(i, j) for arg in self.args])

    def _eval_transpose(self):
        from sympy.matrices.expressions.transpose import transpose
        return HadamardProduct(*list(map(transpose, self.args)))

    def doit(self, **ignored):
        return canonicalize(self)

def validate(*args):
    if not all(arg.is_Matrix for arg in args):
        raise TypeError("Mix of Matrix and Scalar symbols")
    A = args[0]
    for B in args[1:]:
        if A.shape != B.shape:
            raise ShapeError("Matrices %s and %s are not aligned" % (A, B))

rules = (unpack,
         flatten)

canonicalize = exhaust(condition(lambda x: isinstance(x, HadamardProduct),
                                 do_one(*rules)))
