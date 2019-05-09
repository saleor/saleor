from __future__ import print_function, division

from .matexpr import MatrixExpr, ShapeError, Identity, ZeroMatrix
from sympy.core import S
from sympy.core.compatibility import range
from sympy.core.sympify import _sympify
from sympy.matrices import MatrixBase


class MatPow(MatrixExpr):

    def __new__(cls, base, exp):
        base = _sympify(base)
        if not base.is_Matrix:
            raise TypeError("Function parameter should be a matrix")
        exp = _sympify(exp)
        return super(MatPow, cls).__new__(cls, base, exp)

    @property
    def base(self):
        return self.args[0]

    @property
    def exp(self):
        return self.args[1]

    @property
    def shape(self):
        return self.base.shape

    def _entry(self, i, j, **kwargs):
        from sympy.matrices.expressions import MatMul
        A = self.doit()
        if isinstance(A, MatPow):
            # We still have a MatPow, make an explicit MatMul out of it.
            if not A.base.is_square:
                raise ShapeError("Power of non-square matrix %s" % A.base)
            elif A.exp.is_Integer and A.exp.is_positive:
                A = MatMul(*[A.base for k in range(A.exp)])
            #elif A.exp.is_Integer and self.exp.is_negative:
            # Note: possible future improvement: in principle we can take
            # positive powers of the inverse, but carefully avoid recursion,
            # perhaps by adding `_entry` to Inverse (as it is our subclass).
            # T = A.base.as_explicit().inverse()
            # A = MatMul(*[T for k in range(-A.exp)])
            else:
                # Leave the expression unevaluated:
                from sympy.matrices.expressions.matexpr import MatrixElement
                return MatrixElement(self, i, j)
        return A._entry(i, j)

    def doit(self, **kwargs):
        from sympy.matrices.expressions import Inverse
        deep = kwargs.get('deep', True)
        if deep:
            args = [arg.doit(**kwargs) for arg in self.args]
        else:
            args = self.args

        base, exp = args
        # combine all powers, e.g. (A**2)**3 = A**6
        while isinstance(base, MatPow):
            exp = exp*base.args[1]
            base = base.args[0]

        if exp.is_zero and base.is_square:
            if isinstance(base, MatrixBase):
                return base.func(Identity(base.shape[0]))
            return Identity(base.shape[0])
        elif isinstance(base, ZeroMatrix) and exp.is_negative:
            raise ValueError("Matrix determinant is 0, not invertible.")
        elif isinstance(base, (Identity, ZeroMatrix)):
            return base
        elif isinstance(base, MatrixBase) and exp.is_number:
            if exp is S.One:
                return base
            return base**exp
        # Note: just evaluate cases we know, return unevaluated on others.
        # E.g., MatrixSymbol('x', n, m) to power 0 is not an error.
        elif exp is S(-1) and base.is_square:
            return Inverse(base).doit(**kwargs)
        elif exp is S.One:
            return base
        return MatPow(base, exp)

    def _eval_transpose(self):
        base, exp = self.args
        return MatPow(base.T, exp)

    def _eval_derivative_matrix_lines(self, x):
        from .matmul import MatMul
        from .inverse import Inverse
        exp = self.exp
        if (exp > 0) == True:
            newexpr = MatMul.fromiter([self.base for i in range(exp)])
        elif (exp == -1) == True:
            return Inverse(self.base)._eval_derivative_matrix_lines(x)
        elif (exp < 0) == True:
            newexpr = MatMul.fromiter([Inverse(self.base) for i in range(-exp)])
        elif (exp == 0) == True:
            return self.doit()._eval_derivative_matrix_lines(x)
        else:
            raise NotImplementedError("cannot evaluate %s derived by %s" % (self, x))
        return newexpr._eval_derivative_matrix_lines(x)
