""" Linear Solver for Holonomic Functions"""

from __future__ import print_function, division

from sympy.core import S
from sympy.matrices.common import ShapeError
from sympy.matrices.dense import MutableDenseMatrix


class NewMatrix(MutableDenseMatrix):
    """
    Supports elements which can't be Sympified.
    See docstrings in sympy/matrices/matrices.py
    """

    @staticmethod
    def _sympify(a):
        return a

    def row_join(self, rhs):
        # Allows you to build a matrix even if it is null matrix
        if not self:
            return type(self)(rhs)

        if self.rows != rhs.rows:
            raise ShapeError(
                "`self` and `rhs` must have the same number of rows.")
        newmat = NewMatrix.zeros(self.rows, self.cols + rhs.cols)
        newmat[:, :self.cols] = self
        newmat[:, self.cols:] = rhs
        return type(self)(newmat)

    def col_join(self, bott):
        # Allows you to build a matrix even if it is null matrix
        if not self:
            return type(self)(bott)

        if self.cols != bott.cols:
            raise ShapeError(
                "`self` and `bott` must have the same number of columns.")
        newmat = NewMatrix.zeros(self.rows + bott.rows, self.cols)
        newmat[:self.rows, :] = self
        newmat[self.rows:, :] = bott
        return type(self)(newmat)

    def gauss_jordan_solve(self, b, freevar=False):
        from sympy.matrices import Matrix

        aug = self.hstack(self.copy(), b.copy())
        row, col = aug[:, :-1].shape

        # solve by reduced row echelon form
        A, pivots = aug.rref()
        A, v = A[:, :-1], A[:, -1]
        pivots = list(filter(lambda p: p < col, pivots))
        rank = len(pivots)

        # Bring to block form
        permutation = Matrix(range(col)).T
        A = A.vstack(A, permutation)

        for i, c in enumerate(pivots):
            A.col_swap(i, c)

        A, permutation = A[:-1, :], A[-1, :]

        # check for existence of solutions
        # rank of aug Matrix should be equal to rank of coefficient matrix
        if not v[rank:, 0].is_zero:
            raise ValueError("Linear system has no solution")

        # Get index of free symbols (free parameters)
        free_var_index = permutation[len(pivots):]  # non-pivots columns are free variables

        # Free parameters
        tau = NewMatrix([S(1) for k in range(col - rank)]).reshape(col - rank, 1)

        # Full parametric solution
        V = A[:rank, rank:]
        vt = v[:rank, 0]
        free_sol = tau.vstack(vt - V*tau, tau)

        # Undo permutation
        sol = NewMatrix.zeros(col, 1)
        for k, v in enumerate(free_sol):
            sol[permutation[k], 0] = v

        if freevar:
            return sol, tau, free_var_index
        else:
            return sol, tau
