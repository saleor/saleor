from __future__ import division, print_function

from sympy.core import Basic, Dict, Integer, S, Tuple, sympify
from sympy.core.cache import cacheit
from sympy.core.sympify import converter as sympify_converter
from sympy.matrices.dense import DenseMatrix
from sympy.matrices.expressions import MatrixExpr
from sympy.matrices.matrices import MatrixBase
from sympy.matrices.sparse import MutableSparseMatrix, SparseMatrix


def sympify_matrix(arg):
    return arg.as_immutable()
sympify_converter[MatrixBase] = sympify_matrix

class ImmutableDenseMatrix(DenseMatrix, MatrixExpr):
    """Create an immutable version of a matrix.

    Examples
    ========

    >>> from sympy import eye
    >>> from sympy.matrices import ImmutableMatrix
    >>> ImmutableMatrix(eye(3))
    Matrix([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]])
    >>> _[0, 0] = 42
    Traceback (most recent call last):
    ...
    TypeError: Cannot set values of ImmutableDenseMatrix
    """

    # MatrixExpr is set as NotIterable, but we want explicit matrices to be
    # iterable
    _iterable = True
    _class_priority = 8
    _op_priority = 10.001

    def __new__(cls, *args, **kwargs):
        return cls._new(*args, **kwargs)

    __hash__ = MatrixExpr.__hash__

    @classmethod
    def _new(cls, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], ImmutableDenseMatrix):
            return args[0]
        if kwargs.get('copy', True) is False:
            if len(args) != 3:
                raise TypeError("'copy=False' requires a matrix be initialized as rows,cols,[list]")
            rows, cols, flat_list = args
        else:
            rows, cols, flat_list = cls._handle_creation_inputs(*args, **kwargs)
            flat_list = list(flat_list) # create a shallow copy
        rows = Integer(rows)
        cols = Integer(cols)
        if not isinstance(flat_list, Tuple):
            flat_list = Tuple(*flat_list)

        return Basic.__new__(cls, rows, cols, flat_list)

    @property
    def _mat(self):
        # self.args[2] is a Tuple.  Access to the elements
        # of a tuple are significantly faster than Tuple,
        # so return the internal tuple.
        return self.args[2].args

    def _entry(self, i, j):
        return DenseMatrix.__getitem__(self, (i, j))

    def __setitem__(self, *args):
        raise TypeError("Cannot set values of {}".format(self.__class__))

    def _eval_Eq(self, other):
        """Helper method for Equality with matrices.

        Relational automatically converts matrices to ImmutableDenseMatrix
        instances, so this method only applies here.  Returns True if the
        matrices are definitively the same, False if they are definitively
        different, and None if undetermined (e.g. if they contain Symbols).
        Returning None triggers default handling of Equalities.

        """
        if not hasattr(other, 'shape') or self.shape != other.shape:
            return S.false
        if isinstance(other, MatrixExpr) and not isinstance(
                other, ImmutableDenseMatrix):
            return None
        diff = self - other
        return sympify(diff.is_zero)

    def _eval_extract(self, rowsList, colsList):
        # self._mat is a Tuple.  It is slightly faster to index a
        # tuple over a Tuple, so grab the internal tuple directly
        mat = self._mat
        cols = self.cols
        indices = (i * cols + j for i in rowsList for j in colsList)
        return self._new(len(rowsList), len(colsList),
                         Tuple(*(mat[i] for i in indices), sympify=False), copy=False)

    @property
    def cols(self):
        return int(self.args[1])

    @property
    def rows(self):
        return int(self.args[0])

    @property
    def shape(self):
        return tuple(int(i) for i in self.args[:2])

    def is_diagonalizable(self, reals_only=False, **kwargs):
        return super(ImmutableDenseMatrix, self).is_diagonalizable(
            reals_only=reals_only, **kwargs)
    is_diagonalizable.__doc__ = DenseMatrix.is_diagonalizable.__doc__
    is_diagonalizable = cacheit(is_diagonalizable)


# This is included after the class definition as a workaround for issue 7213.
# See https://github.com/sympy/sympy/issues/7213
# the object is non-zero
# See https://github.com/sympy/sympy/issues/7213
ImmutableDenseMatrix.is_zero = DenseMatrix.is_zero

# make sure ImmutableDenseMatrix is aliased as ImmutableMatrix
ImmutableMatrix = ImmutableDenseMatrix


class ImmutableSparseMatrix(SparseMatrix, Basic):
    """Create an immutable version of a sparse matrix.

    Examples
    ========

    >>> from sympy import eye
    >>> from sympy.matrices.immutable import ImmutableSparseMatrix
    >>> ImmutableSparseMatrix(1, 1, {})
    Matrix([[0]])
    >>> ImmutableSparseMatrix(eye(3))
    Matrix([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]])
    >>> _[0, 0] = 42
    Traceback (most recent call last):
    ...
    TypeError: Cannot set values of ImmutableSparseMatrix
    >>> _.shape
    (3, 3)
    """
    is_Matrix = True
    _class_priority = 9

    @classmethod
    def _new(cls, *args, **kwargs):
        s = MutableSparseMatrix(*args)
        rows = Integer(s.rows)
        cols = Integer(s.cols)
        mat = Dict(s._smat)
        obj = Basic.__new__(cls, rows, cols, mat)
        obj.rows = s.rows
        obj.cols = s.cols
        obj._smat = s._smat
        return obj

    def __new__(cls, *args, **kwargs):
        return cls._new(*args, **kwargs)

    def __setitem__(self, *args):
        raise TypeError("Cannot set values of ImmutableSparseMatrix")

    def __hash__(self):
        return hash((type(self).__name__,) + (self.shape, tuple(self._smat)))

    _eval_Eq = ImmutableDenseMatrix._eval_Eq

    def is_diagonalizable(self, reals_only=False, **kwargs):
        return super(ImmutableSparseMatrix, self).is_diagonalizable(
            reals_only=reals_only, **kwargs)
    is_diagonalizable.__doc__ = SparseMatrix.is_diagonalizable.__doc__
    is_diagonalizable = cacheit(is_diagonalizable)
