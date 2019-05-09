from __future__ import print_function

from sympy.matrices.dense import MutableDenseMatrix
from sympy.polys.polytools import Poly

from sympy.polys.domains import EX


class MutablePolyDenseMatrix(MutableDenseMatrix):
    """
    A mutable matrix of objects from poly module or to operate with them.

    Examples
    ========

    >>> from sympy.polys.polymatrix import PolyMatrix
    >>> from sympy import Symbol, Poly, ZZ
    >>> x = Symbol('x')
    >>> pm1 = PolyMatrix([[Poly(x**2, x), Poly(-x, x)], [Poly(x**3, x), Poly(-1 + x, x)]])
    >>> v1 = PolyMatrix([[1, 0], [-1, 0]])
    >>> pm1*v1
    Matrix([
    [    Poly(x**2 + x, x, domain='ZZ'), Poly(0, x, domain='ZZ')],
    [Poly(x**3 - x + 1, x, domain='ZZ'), Poly(0, x, domain='ZZ')]])

    >>> pm1.ring
    ZZ[x]

    >>> v1*pm1
    Matrix([
    [ Poly(x**2, x, domain='ZZ'), Poly(-x, x, domain='ZZ')],
    [Poly(-x**2, x, domain='ZZ'),  Poly(x, x, domain='ZZ')]])

    >>> pm2 = PolyMatrix([[Poly(x**2, x, domain='QQ'), Poly(0, x, domain='QQ'), Poly(1, x, domain='QQ'), \
            Poly(x**3, x, domain='QQ'), Poly(0, x, domain='QQ'), Poly(-x**3, x, domain='QQ')]])
    >>> v2 = PolyMatrix([1, 0, 0, 0, 0, 0], ring=ZZ)
    >>> v2.ring
    ZZ
    >>> pm2*v2
    Matrix([[Poly(x**2, x, domain='QQ')]])

    """
    _class_priority = 10
    # we don't want to sympify the elements of PolyMatrix
    _sympify = staticmethod(lambda x: x)

    def __init__(self, *args, **kwargs):
        # if any non-Poly element is given as input then
        # 'ring' defaults 'EX'
        ring = kwargs.get('ring', EX)
        if all(isinstance(p, Poly) for p in self._mat) and self._mat:
            domain = tuple([p.domain[p.gens] for p in self._mat])
            ring = domain[0]
            for i in range(1, len(domain)):
                ring = ring.unify(domain[i])
        self.ring = ring

    def _eval_matrix_mul(self, other):
        self_rows, self_cols = self.rows, self.cols
        other_rows, other_cols = other.rows, other.cols
        other_len = other_rows * other_cols
        new_mat_rows = self.rows
        new_mat_cols = other.cols

        new_mat = [0]*new_mat_rows*new_mat_cols

        if self.cols != 0 and other.rows != 0:
            mat = self._mat
            other_mat = other._mat
            for i in range(len(new_mat)):
                row, col = i // new_mat_cols, i % new_mat_cols
                row_indices = range(self_cols*row, self_cols*(row+1))
                col_indices = range(col, other_len, other_cols)
                vec = (mat[a]*other_mat[b] for a,b in zip(row_indices, col_indices))
                # 'Add' shouldn't be used here
                new_mat[i] = sum(vec)

        return self.__class__(new_mat_rows, new_mat_cols, new_mat, copy=False)

    def _eval_scalar_mul(self, other):
        mat = [Poly(a.as_expr()*other, *a.gens) if isinstance(a, Poly) else a*other for a in self._mat]
        return self.__class__(self.rows, self.cols, mat, copy=False)

    def _eval_scalar_rmul(self, other):
        mat = [Poly(other*a.as_expr(), *a.gens) if isinstance(a, Poly) else other*a for a in self._mat]
        return self.__class__(self.rows, self.cols, mat, copy=False)


MutablePolyMatrix = PolyMatrix = MutablePolyDenseMatrix
