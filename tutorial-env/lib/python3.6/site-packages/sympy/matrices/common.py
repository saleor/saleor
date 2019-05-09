"""
Basic methods common to all matrices to be used
when creating more advanced matrices (e.g., matrices over rings,
etc.).
"""

from __future__ import division, print_function

from collections import defaultdict
from inspect import isfunction

from sympy.assumptions.refine import refine
from sympy.core.basic import Atom
from sympy.core.compatibility import (
    Iterable, as_int, is_sequence, range, reduce)
from sympy.core.decorators import call_highest_priority
from sympy.core.expr import Expr
from sympy.core.function import count_ops
from sympy.core.singleton import S
from sympy.core.symbol import Symbol
from sympy.core.sympify import sympify
from sympy.functions import Abs
from sympy.simplify import simplify as _simplify
from sympy.utilities.exceptions import SymPyDeprecationWarning
from sympy.utilities.iterables import flatten


class MatrixError(Exception):
    pass


class ShapeError(ValueError, MatrixError):
    """Wrong matrix shape"""
    pass


class NonSquareMatrixError(ShapeError):
    pass


class MatrixRequired(object):
    """All subclasses of matrix objects must implement the
    required matrix properties listed here."""
    rows = None
    cols = None
    shape = None
    _simplify = None

    @classmethod
    def _new(cls, *args, **kwargs):
        """`_new` must, at minimum, be callable as
        `_new(rows, cols, mat) where mat is a flat list of the
        elements of the matrix."""
        raise NotImplementedError("Subclasses must implement this.")

    def __eq__(self, other):
        raise NotImplementedError("Subclasses must implement this.")

    def __getitem__(self, key):
        """Implementations of __getitem__ should accept ints, in which
        case the matrix is indexed as a flat list, tuples (i,j) in which
        case the (i,j) entry is returned, slices, or mixed tuples (a,b)
        where a and b are any combintion of slices and integers."""
        raise NotImplementedError("Subclasses must implement this.")

    def __len__(self):
        """The total number of entries in the matrix."""
        raise NotImplementedError("Subclasses must implement this.")


class MatrixShaping(MatrixRequired):
    """Provides basic matrix shaping and extracting of submatrices"""

    def _eval_col_del(self, col):
        def entry(i, j):
            return self[i, j] if j < col else self[i, j + 1]
        return self._new(self.rows, self.cols - 1, entry)

    def _eval_col_insert(self, pos, other):
        cols = self.cols

        def entry(i, j):
            if j < pos:
                return self[i, j]
            elif pos <= j < pos + other.cols:
                return other[i, j - pos]
            return self[i, j - other.cols]

        return self._new(self.rows, self.cols + other.cols,
                         lambda i, j: entry(i, j))

    def _eval_col_join(self, other):
        rows = self.rows

        def entry(i, j):
            if i < rows:
                return self[i, j]
            return other[i - rows, j]

        return classof(self, other)._new(self.rows + other.rows, self.cols,
                                         lambda i, j: entry(i, j))

    def _eval_extract(self, rowsList, colsList):
        mat = list(self)
        cols = self.cols
        indices = (i * cols + j for i in rowsList for j in colsList)
        return self._new(len(rowsList), len(colsList),
                         list(mat[i] for i in indices))

    def _eval_get_diag_blocks(self):
        sub_blocks = []

        def recurse_sub_blocks(M):
            i = 1
            while i <= M.shape[0]:
                if i == 1:
                    to_the_right = M[0, i:]
                    to_the_bottom = M[i:, 0]
                else:
                    to_the_right = M[:i, i:]
                    to_the_bottom = M[i:, :i]
                if any(to_the_right) or any(to_the_bottom):
                    i += 1
                    continue
                else:
                    sub_blocks.append(M[:i, :i])
                    if M.shape == M[:i, :i].shape:
                        return
                    else:
                        recurse_sub_blocks(M[i:, i:])
                        return

        recurse_sub_blocks(self)
        return sub_blocks

    def _eval_row_del(self, row):
        def entry(i, j):
            return self[i, j] if i < row else self[i + 1, j]
        return self._new(self.rows - 1, self.cols, entry)

    def _eval_row_insert(self, pos, other):
        entries = list(self)
        insert_pos = pos * self.cols
        entries[insert_pos:insert_pos] = list(other)
        return self._new(self.rows + other.rows, self.cols, entries)

    def _eval_row_join(self, other):
        cols = self.cols

        def entry(i, j):
            if j < cols:
                return self[i, j]
            return other[i, j - cols]

        return classof(self, other)._new(self.rows, self.cols + other.cols,
                                         lambda i, j: entry(i, j))

    def _eval_tolist(self):
        return [list(self[i,:]) for i in range(self.rows)]

    def _eval_vec(self):
        rows = self.rows

        def entry(n, _):
            # we want to read off the columns first
            j = n // rows
            i = n - j * rows
            return self[i, j]

        return self._new(len(self), 1, entry)

    def col_del(self, col):
        """Delete the specified column."""
        if col < 0:
            col += self.cols
        if not 0 <= col < self.cols:
            raise ValueError("Column {} out of range.".format(col))
        return self._eval_col_del(col)

    def col_insert(self, pos, other):
        """Insert one or more columns at the given column position.

        Examples
        ========

        >>> from sympy import zeros, ones
        >>> M = zeros(3)
        >>> V = ones(3, 1)
        >>> M.col_insert(1, V)
        Matrix([
        [0, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 0, 0]])

        See Also
        ========

        col
        row_insert
        """
        # Allows you to build a matrix even if it is null matrix
        if not self:
            return type(self)(other)

        pos = as_int(pos)

        if pos < 0:
            pos = self.cols + pos
        if pos < 0:
            pos = 0
        elif pos > self.cols:
            pos = self.cols

        if self.rows != other.rows:
            raise ShapeError(
                "`self` and `other` must have the same number of rows.")

        return self._eval_col_insert(pos, other)

    def col_join(self, other):
        """Concatenates two matrices along self's last and other's first row.

        Examples
        ========

        >>> from sympy import zeros, ones
        >>> M = zeros(3)
        >>> V = ones(1, 3)
        >>> M.col_join(V)
        Matrix([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 1]])

        See Also
        ========

        col
        row_join
        """
        # A null matrix can always be stacked (see  #10770)
        if self.rows == 0 and self.cols != other.cols:
            return self._new(0, other.cols, []).col_join(other)

        if self.cols != other.cols:
            raise ShapeError(
                "`self` and `other` must have the same number of columns.")
        return self._eval_col_join(other)

    def col(self, j):
        """Elementary column selector.

        Examples
        ========

        >>> from sympy import eye
        >>> eye(2).col(0)
        Matrix([
        [1],
        [0]])

        See Also
        ========

        row
        col_op
        col_swap
        col_del
        col_join
        col_insert
        """
        return self[:, j]

    def extract(self, rowsList, colsList):
        """Return a submatrix by specifying a list of rows and columns.
        Negative indices can be given. All indices must be in the range
        -n <= i < n where n is the number of rows or columns.

        Examples
        ========

        >>> from sympy import Matrix
        >>> m = Matrix(4, 3, range(12))
        >>> m
        Matrix([
        [0,  1,  2],
        [3,  4,  5],
        [6,  7,  8],
        [9, 10, 11]])
        >>> m.extract([0, 1, 3], [0, 1])
        Matrix([
        [0,  1],
        [3,  4],
        [9, 10]])

        Rows or columns can be repeated:

        >>> m.extract([0, 0, 1], [-1])
        Matrix([
        [2],
        [2],
        [5]])

        Every other row can be taken by using range to provide the indices:

        >>> m.extract(range(0, m.rows, 2), [-1])
        Matrix([
        [2],
        [8]])

        RowsList or colsList can also be a list of booleans, in which case
        the rows or columns corresponding to the True values will be selected:

        >>> m.extract([0, 1, 2, 3], [True, False, True])
        Matrix([
        [0,  2],
        [3,  5],
        [6,  8],
        [9, 11]])
        """

        if not is_sequence(rowsList) or not is_sequence(colsList):
            raise TypeError("rowsList and colsList must be iterable")
        # ensure rowsList and colsList are lists of integers
        if rowsList and all(isinstance(i, bool) for i in rowsList):
            rowsList = [index for index, item in enumerate(rowsList) if item]
        if colsList and all(isinstance(i, bool) for i in colsList):
            colsList = [index for index, item in enumerate(colsList) if item]

        # ensure everything is in range
        rowsList = [a2idx(k, self.rows) for k in rowsList]
        colsList = [a2idx(k, self.cols) for k in colsList]

        return self._eval_extract(rowsList, colsList)

    def get_diag_blocks(self):
        """Obtains the square sub-matrices on the main diagonal of a square matrix.

        Useful for inverting symbolic matrices or solving systems of
        linear equations which may be decoupled by having a block diagonal
        structure.

        Examples
        ========

        >>> from sympy import Matrix
        >>> from sympy.abc import x, y, z
        >>> A = Matrix([[1, 3, 0, 0], [y, z*z, 0, 0], [0, 0, x, 0], [0, 0, 0, 0]])
        >>> a1, a2, a3 = A.get_diag_blocks()
        >>> a1
        Matrix([
        [1,    3],
        [y, z**2]])
        >>> a2
        Matrix([[x]])
        >>> a3
        Matrix([[0]])

        """
        return self._eval_get_diag_blocks()

    @classmethod
    def hstack(cls, *args):
        """Return a matrix formed by joining args horizontally (i.e.
        by repeated application of row_join).

        Examples
        ========

        >>> from sympy.matrices import Matrix, eye
        >>> Matrix.hstack(eye(2), 2*eye(2))
        Matrix([
        [1, 0, 2, 0],
        [0, 1, 0, 2]])
        """
        if len(args) == 0:
            return cls._new()

        kls = type(args[0])
        return reduce(kls.row_join, args)

    def reshape(self, rows, cols):
        """Reshape the matrix. Total number of elements must remain the same.

        Examples
        ========

        >>> from sympy import Matrix
        >>> m = Matrix(2, 3, lambda i, j: 1)
        >>> m
        Matrix([
        [1, 1, 1],
        [1, 1, 1]])
        >>> m.reshape(1, 6)
        Matrix([[1, 1, 1, 1, 1, 1]])
        >>> m.reshape(3, 2)
        Matrix([
        [1, 1],
        [1, 1],
        [1, 1]])

        """
        if self.rows * self.cols != rows * cols:
            raise ValueError("Invalid reshape parameters %d %d" % (rows, cols))
        return self._new(rows, cols, lambda i, j: self[i * cols + j])

    def row_del(self, row):
        """Delete the specified row."""
        if row < 0:
            row += self.rows
        if not 0 <= row < self.rows:
            raise ValueError("Row {} out of range.".format(row))

        return self._eval_row_del(row)

    def row_insert(self, pos, other):
        """Insert one or more rows at the given row position.

        Examples
        ========

        >>> from sympy import zeros, ones
        >>> M = zeros(3)
        >>> V = ones(1, 3)
        >>> M.row_insert(1, V)
        Matrix([
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
        [0, 0, 0]])

        See Also
        ========

        row
        col_insert
        """
        # Allows you to build a matrix even if it is null matrix
        if not self:
            return self._new(other)

        pos = as_int(pos)

        if pos < 0:
            pos = self.rows + pos
        if pos < 0:
            pos = 0
        elif pos > self.rows:
            pos = self.rows

        if self.cols != other.cols:
            raise ShapeError(
                "`self` and `other` must have the same number of columns.")

        return self._eval_row_insert(pos, other)

    def row_join(self, other):
        """Concatenates two matrices along self's last and rhs's first column

        Examples
        ========

        >>> from sympy import zeros, ones
        >>> M = zeros(3)
        >>> V = ones(3, 1)
        >>> M.row_join(V)
        Matrix([
        [0, 0, 0, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 1]])

        See Also
        ========

        row
        col_join
        """
        # A null matrix can always be stacked (see  #10770)
        if self.cols == 0 and self.rows != other.rows:
            return self._new(other.rows, 0, []).row_join(other)

        if self.rows != other.rows:
            raise ShapeError(
                "`self` and `rhs` must have the same number of rows.")
        return self._eval_row_join(other)

    def row(self, i):
        """Elementary row selector.

        Examples
        ========

        >>> from sympy import eye
        >>> eye(2).row(0)
        Matrix([[1, 0]])

        See Also
        ========

        col
        row_op
        row_swap
        row_del
        row_join
        row_insert
        """
        return self[i, :]

    @property
    def shape(self):
        """The shape (dimensions) of the matrix as the 2-tuple (rows, cols).

        Examples
        ========

        >>> from sympy.matrices import zeros
        >>> M = zeros(2, 3)
        >>> M.shape
        (2, 3)
        >>> M.rows
        2
        >>> M.cols
        3
        """
        return (self.rows, self.cols)

    def tolist(self):
        """Return the Matrix as a nested Python list.

        Examples
        ========

        >>> from sympy import Matrix, ones
        >>> m = Matrix(3, 3, range(9))
        >>> m
        Matrix([
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8]])
        >>> m.tolist()
        [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        >>> ones(3, 0).tolist()
        [[], [], []]

        When there are no rows then it will not be possible to tell how
        many columns were in the original matrix:

        >>> ones(0, 3).tolist()
        []

        """
        if not self.rows:
            return []
        if not self.cols:
            return [[] for i in range(self.rows)]
        return self._eval_tolist()

    def vec(self):
        """Return the Matrix converted into a one column matrix by stacking columns

        Examples
        ========

        >>> from sympy import Matrix
        >>> m=Matrix([[1, 3], [2, 4]])
        >>> m
        Matrix([
        [1, 3],
        [2, 4]])
        >>> m.vec()
        Matrix([
        [1],
        [2],
        [3],
        [4]])

        See Also
        ========

        vech
        """
        return self._eval_vec()

    @classmethod
    def vstack(cls, *args):
        """Return a matrix formed by joining args vertically (i.e.
        by repeated application of col_join).

        Examples
        ========

        >>> from sympy.matrices import Matrix, eye
        >>> Matrix.vstack(eye(2), 2*eye(2))
        Matrix([
        [1, 0],
        [0, 1],
        [2, 0],
        [0, 2]])
        """
        if len(args) == 0:
            return cls._new()

        kls = type(args[0])
        return reduce(kls.col_join, args)


class MatrixSpecial(MatrixRequired):
    """Construction of special matrices"""

    @classmethod
    def _eval_diag(cls, rows, cols, diag_dict):
        """diag_dict is a defaultdict containing
        all the entries of the diagonal matrix."""
        def entry(i, j):
            return diag_dict[(i,j)]
        return cls._new(rows, cols, entry)

    @classmethod
    def _eval_eye(cls, rows, cols):
        def entry(i, j):
            return S.One if i == j else S.Zero
        return cls._new(rows, cols, entry)

    @classmethod
    def _eval_jordan_block(cls, rows, cols, eigenvalue, band='upper'):
        if band == 'lower':
            def entry(i, j):
                if i == j:
                    return eigenvalue
                elif j + 1 == i:
                    return S.One
                return S.Zero
        else:
            def entry(i, j):
                if i == j:
                    return eigenvalue
                elif i + 1 == j:
                    return S.One
                return S.Zero
        return cls._new(rows, cols, entry)

    @classmethod
    def _eval_ones(cls, rows, cols):
        def entry(i, j):
            return S.One
        return cls._new(rows, cols, entry)

    @classmethod
    def _eval_zeros(cls, rows, cols):
        def entry(i, j):
            return S.Zero
        return cls._new(rows, cols, entry)

    @classmethod
    def diag(kls, *args, **kwargs):
        """Returns a matrix with the specified diagonal.
        If matrices are passed, a block-diagonal matrix
        is created.

        kwargs
        ======

        rows : rows of the resulting matrix; computed if
               not given.

        cols : columns of the resulting matrix; computed if
               not given.

        cls : class for the resulting matrix

        Examples
        ========

        >>> from sympy.matrices import Matrix
        >>> Matrix.diag(1, 2, 3)
        Matrix([
        [1, 0, 0],
        [0, 2, 0],
        [0, 0, 3]])
        >>> Matrix.diag([1, 2, 3])
        Matrix([
        [1, 0, 0],
        [0, 2, 0],
        [0, 0, 3]])

        The diagonal elements can be matrices; diagonal filling will
        continue on the diagonal from the last element of the matrix:

        >>> from sympy.abc import x, y, z
        >>> a = Matrix([x, y, z])
        >>> b = Matrix([[1, 2], [3, 4]])
        >>> c = Matrix([[5, 6]])
        >>> Matrix.diag(a, 7, b, c)
        Matrix([
        [x, 0, 0, 0, 0, 0],
        [y, 0, 0, 0, 0, 0],
        [z, 0, 0, 0, 0, 0],
        [0, 7, 0, 0, 0, 0],
        [0, 0, 1, 2, 0, 0],
        [0, 0, 3, 4, 0, 0],
        [0, 0, 0, 0, 5, 6]])

        A given band off the diagonal can be made by padding with a
        vertical or horizontal "kerning" vector:

        >>> hpad = Matrix(0, 2, [])
        >>> vpad = Matrix(2, 0, [])
        >>> Matrix.diag(vpad, 1, 2, 3, hpad) + Matrix.diag(hpad, 4, 5, 6, vpad)
        Matrix([
        [0, 0, 4, 0, 0],
        [0, 0, 0, 5, 0],
        [1, 0, 0, 0, 6],
        [0, 2, 0, 0, 0],
        [0, 0, 3, 0, 0]])

        The type of the resulting matrix can be affected with the ``cls``
        keyword.

        >>> type(Matrix.diag(1))
        <class 'sympy.matrices.dense.MutableDenseMatrix'>
        >>> from sympy.matrices import ImmutableMatrix
        >>> type(Matrix.diag(1, cls=ImmutableMatrix))
        <class 'sympy.matrices.immutable.ImmutableDenseMatrix'>
        """

        klass = kwargs.get('cls', kls)
        # allow a sequence to be passed in as the only argument
        if len(args) == 1 and is_sequence(args[0]) and not getattr(args[0], 'is_Matrix', False):
            args = args[0]

        def size(m):
            """Compute the size of the diagonal block"""
            if hasattr(m, 'rows'):
                return m.rows, m.cols
            return 1, 1
        diag_rows = sum(size(m)[0] for m in args)
        diag_cols =  sum(size(m)[1] for m in args)
        rows = kwargs.get('rows', diag_rows)
        cols = kwargs.get('cols', diag_cols)
        if rows < diag_rows or cols < diag_cols:
            raise ValueError("A {} x {} diagnal matrix cannot accommodate a"
                             "diagonal of size at least {} x {}.".format(rows, cols,
                                                                         diag_rows, diag_cols))

        # fill a default dict with the diagonal entries
        diag_entries = defaultdict(lambda: S.Zero)
        row_pos, col_pos = 0, 0
        for m in args:
            if hasattr(m, 'rows'):
                # in this case, we're a matrix
                for i in range(m.rows):
                    for j in range(m.cols):
                        diag_entries[(i + row_pos, j + col_pos)] = m[i, j]
                row_pos += m.rows
                col_pos += m.cols
            else:
                # in this case, we're a single value
                diag_entries[(row_pos, col_pos)] = m
                row_pos += 1
                col_pos += 1
        return klass._eval_diag(rows, cols, diag_entries)

    @classmethod
    def eye(kls, rows, cols=None, **kwargs):
        """Returns an identity matrix.

        Args
        ====

        rows : rows of the matrix
        cols : cols of the matrix (if None, cols=rows)

        kwargs
        ======
        cls : class of the returned matrix
        """
        if cols is None:
            cols = rows
        klass = kwargs.get('cls', kls)
        rows, cols = as_int(rows), as_int(cols)

        return klass._eval_eye(rows, cols)

    @classmethod
    def jordan_block(kls, size=None, eigenvalue=None, **kwargs):
        """Returns a Jordan block

        Parameters
        ==========

        size : Integer, optional
            Specifies the shape of the Jordan block matrix.

        eigenvalue : Number or Symbol
            Specifies the value for the main diagonal of the matrix.

            .. note::
                The keyword ``eigenval`` is also specified as an alias
                of this keyword, but it is not recommended to use.

                We may deprecate the alias in later release.

        band : 'upper' or 'lower', optional
            Specifies the position of the off-diagonal to put `1` s on.

        cls : Matrix, optional
            Specifies the matrix class of the output form.

            If it is not specified, the class type where the method is
            being executed on will be returned.

        rows, cols : Integer, optional
            Specifies the shape of the Jordan block matrix. See Notes
            section for the details of how these key works.

            .. note::
                This feature will be deprecated in the future.


        Returns
        =======

        Matrix
            A Jordan block matrix.

        Raises
        ======

        ValueError
            If insufficient arguments are given for matrix size
            specification, or no eigenvalue is given.

        Examples
        ========

        Creating a default Jordan block:

        >>> from sympy import Matrix
        >>> from sympy.abc import x
        >>> Matrix.jordan_block(4, x)
        Matrix([
        [x, 1, 0, 0],
        [0, x, 1, 0],
        [0, 0, x, 1],
        [0, 0, 0, x]])

        Creating an alternative Jordan block matrix where `1` is on
        lower off-diagonal:

        >>> Matrix.jordan_block(4, x, band='lower')
        Matrix([
        [x, 0, 0, 0],
        [1, x, 0, 0],
        [0, 1, x, 0],
        [0, 0, 1, x]])

        Creating a Jordan block with keyword arguments

        >>> Matrix.jordan_block(size=4, eigenvalue=x)
        Matrix([
        [x, 1, 0, 0],
        [0, x, 1, 0],
        [0, 0, x, 1],
        [0, 0, 0, x]])

        Notes
        =====

        .. note::
            This feature will be deprecated in the future.

        The keyword arguments ``size``, ``rows``, ``cols`` relates to
        the Jordan block size specifications.

        If you want to create a square Jordan block, specify either
        one of the three arguments.

        If you want to create a rectangular Jordan block, specify
        ``rows`` and ``cols`` individually.

        +--------------------------------+---------------------+
        |        Arguments Given         |     Matrix Shape    |
        +----------+----------+----------+----------+----------+
        |   size   |   rows   |   cols   |   rows   |   cols   |
        +==========+==========+==========+==========+==========+
        |   size   |         Any         |   size   |   size   |
        +----------+----------+----------+----------+----------+
        |          |        None         |     ValueError      |
        |          +----------+----------+----------+----------+
        |   None   |   rows   |   None   |   rows   |   rows   |
        |          +----------+----------+----------+----------+
        |          |   None   |   cols   |   cols   |   cols   |
        +          +----------+----------+----------+----------+
        |          |   rows   |   cols   |   rows   |   cols   |
        +----------+----------+----------+----------+----------+

        References
        ==========

        .. [1] https://en.wikipedia.org/wiki/Jordan_matrix
        """
        if 'rows' in kwargs or 'cols' in kwargs:
            SymPyDeprecationWarning(
                feature="Keyword arguments 'rows' or 'cols'",
                issue=16102,
                useinstead="a more generic banded matrix constructor",
                deprecated_since_version="1.4"
            ).warn()

        klass = kwargs.pop('cls', kls)
        band = kwargs.pop('band', 'upper')
        rows = kwargs.pop('rows', None)
        cols = kwargs.pop('cols', None)

        eigenval = kwargs.get('eigenval', None)
        if eigenvalue is None and eigenval is None:
            raise ValueError("Must supply an eigenvalue")
        elif eigenvalue != eigenval and None not in (eigenval, eigenvalue):
            raise ValueError(
                "Inconsistent values are given: 'eigenval'={}, "
                "'eigenvalue'={}".format(eigenval, eigenvalue))
        else:
            if eigenval is not None:
                eigenvalue = eigenval

        if (size, rows, cols) == (None, None, None):
            raise ValueError("Must supply a matrix size")

        if size is not None:
            rows, cols = size, size
        elif rows is not None and cols is None:
            cols = rows
        elif cols is not None and rows is None:
            rows = cols

        rows, cols = as_int(rows), as_int(cols)

        return klass._eval_jordan_block(rows, cols, eigenvalue, band)

    @classmethod
    def ones(kls, rows, cols=None, **kwargs):
        """Returns a matrix of ones.

        Args
        ====

        rows : rows of the matrix
        cols : cols of the matrix (if None, cols=rows)

        kwargs
        ======
        cls : class of the returned matrix
        """
        if cols is None:
            cols = rows
        klass = kwargs.get('cls', kls)
        rows, cols = as_int(rows), as_int(cols)

        return klass._eval_ones(rows, cols)

    @classmethod
    def zeros(kls, rows, cols=None, **kwargs):
        """Returns a matrix of zeros.

        Args
        ====

        rows : rows of the matrix
        cols : cols of the matrix (if None, cols=rows)

        kwargs
        ======
        cls : class of the returned matrix
        """
        if cols is None:
            cols = rows
        klass = kwargs.get('cls', kls)
        rows, cols = as_int(rows), as_int(cols)

        return klass._eval_zeros(rows, cols)


class MatrixProperties(MatrixRequired):
    """Provides basic properties of a matrix."""

    def _eval_atoms(self, *types):
        result = set()
        for i in self:
            result.update(i.atoms(*types))
        return result

    def _eval_free_symbols(self):
        return set().union(*(i.free_symbols for i in self))

    def _eval_has(self, *patterns):
        return any(a.has(*patterns) for a in self)

    def _eval_is_anti_symmetric(self, simpfunc):
        if not all(simpfunc(self[i, j] + self[j, i]).is_zero for i in range(self.rows) for j in range(self.cols)):
            return False
        return True

    def _eval_is_diagonal(self):
        for i in range(self.rows):
            for j in range(self.cols):
                if i != j and self[i, j]:
                    return False
        return True

    # _eval_is_hermitian is called by some general sympy
    # routines and has a different *args signature.  Make
    # sure the names don't clash by adding `_matrix_` in name.
    def _eval_is_matrix_hermitian(self, simpfunc):
        mat = self._new(self.rows, self.cols, lambda i, j: simpfunc(self[i, j] - self[j, i].conjugate()))
        return mat.is_zero

    def _eval_is_Identity(self):
        def dirac(i, j):
            if i == j:
                return 1
            return 0

        return all(self[i, j] == dirac(i, j) for i in range(self.rows) for j in
                   range(self.cols))

    def _eval_is_lower_hessenberg(self):
        return all(self[i, j].is_zero
                   for i in range(self.rows)
                   for j in range(i + 2, self.cols))

    def _eval_is_lower(self):
        return all(self[i, j].is_zero
                   for i in range(self.rows)
                   for j in range(i + 1, self.cols))

    def _eval_is_symbolic(self):
        return self.has(Symbol)

    def _eval_is_symmetric(self, simpfunc):
        mat = self._new(self.rows, self.cols, lambda i, j: simpfunc(self[i, j] - self[j, i]))
        return mat.is_zero

    def _eval_is_zero(self):
        if any(i.is_zero == False for i in self):
            return False
        if any(i.is_zero is None for i in self):
            return None
        return True

    def _eval_is_upper_hessenberg(self):
        return all(self[i, j].is_zero
                   for i in range(2, self.rows)
                   for j in range(min(self.cols, (i - 1))))

    def _eval_values(self):
        return [i for i in self if not i.is_zero]

    def atoms(self, *types):
        """Returns the atoms that form the current object.

        Examples
        ========

        >>> from sympy.abc import x, y
        >>> from sympy.matrices import Matrix
        >>> Matrix([[x]])
        Matrix([[x]])
        >>> _.atoms()
        {x}
        """

        types = tuple(t if isinstance(t, type) else type(t) for t in types)
        if not types:
            types = (Atom,)
        return self._eval_atoms(*types)

    @property
    def free_symbols(self):
        """Returns the free symbols within the matrix.

        Examples
        ========

        >>> from sympy.abc import x
        >>> from sympy.matrices import Matrix
        >>> Matrix([[x], [1]]).free_symbols
        {x}
        """
        return self._eval_free_symbols()

    def has(self, *patterns):
        """Test whether any subexpression matches any of the patterns.

        Examples
        ========

        >>> from sympy import Matrix, SparseMatrix, Float
        >>> from sympy.abc import x, y
        >>> A = Matrix(((1, x), (0.2, 3)))
        >>> B = SparseMatrix(((1, x), (0.2, 3)))
        >>> A.has(x)
        True
        >>> A.has(y)
        False
        >>> A.has(Float)
        True
        >>> B.has(x)
        True
        >>> B.has(y)
        False
        >>> B.has(Float)
        True
        """
        return self._eval_has(*patterns)

    def is_anti_symmetric(self, simplify=True):
        """Check if matrix M is an antisymmetric matrix,
        that is, M is a square matrix with all M[i, j] == -M[j, i].

        When ``simplify=True`` (default), the sum M[i, j] + M[j, i] is
        simplified before testing to see if it is zero. By default,
        the SymPy simplify function is used. To use a custom function
        set simplify to a function that accepts a single argument which
        returns a simplified expression. To skip simplification, set
        simplify to False but note that although this will be faster,
        it may induce false negatives.

        Examples
        ========

        >>> from sympy import Matrix, symbols
        >>> m = Matrix(2, 2, [0, 1, -1, 0])
        >>> m
        Matrix([
        [ 0, 1],
        [-1, 0]])
        >>> m.is_anti_symmetric()
        True
        >>> x, y = symbols('x y')
        >>> m = Matrix(2, 3, [0, 0, x, -y, 0, 0])
        >>> m
        Matrix([
        [ 0, 0, x],
        [-y, 0, 0]])
        >>> m.is_anti_symmetric()
        False

        >>> from sympy.abc import x, y
        >>> m = Matrix(3, 3, [0, x**2 + 2*x + 1, y,
        ...                   -(x + 1)**2 , 0, x*y,
        ...                   -y, -x*y, 0])

        Simplification of matrix elements is done by default so even
        though two elements which should be equal and opposite wouldn't
        pass an equality test, the matrix is still reported as
        anti-symmetric:

        >>> m[0, 1] == -m[1, 0]
        False
        >>> m.is_anti_symmetric()
        True

        If 'simplify=False' is used for the case when a Matrix is already
        simplified, this will speed things up. Here, we see that without
        simplification the matrix does not appear anti-symmetric:

        >>> m.is_anti_symmetric(simplify=False)
        False

        But if the matrix were already expanded, then it would appear
        anti-symmetric and simplification in the is_anti_symmetric routine
        is not needed:

        >>> m = m.expand()
        >>> m.is_anti_symmetric(simplify=False)
        True
        """
        # accept custom simplification
        simpfunc = simplify
        if not isfunction(simplify):
            simpfunc = _simplify if simplify else lambda x: x

        if not self.is_square:
            return False
        return self._eval_is_anti_symmetric(simpfunc)

    def is_diagonal(self):
        """Check if matrix is diagonal,
        that is matrix in which the entries outside the main diagonal are all zero.

        Examples
        ========

        >>> from sympy import Matrix, diag
        >>> m = Matrix(2, 2, [1, 0, 0, 2])
        >>> m
        Matrix([
        [1, 0],
        [0, 2]])
        >>> m.is_diagonal()
        True

        >>> m = Matrix(2, 2, [1, 1, 0, 2])
        >>> m
        Matrix([
        [1, 1],
        [0, 2]])
        >>> m.is_diagonal()
        False

        >>> m = diag(1, 2, 3)
        >>> m
        Matrix([
        [1, 0, 0],
        [0, 2, 0],
        [0, 0, 3]])
        >>> m.is_diagonal()
        True

        See Also
        ========

        is_lower
        is_upper
        is_diagonalizable
        diagonalize
        """
        return self._eval_is_diagonal()

    @property
    def is_hermitian(self, simplify=True):
        """Checks if the matrix is Hermitian.

        In a Hermitian matrix element i,j is the complex conjugate of
        element j,i.

        Examples
        ========

        >>> from sympy.matrices import Matrix
        >>> from sympy import I
        >>> from sympy.abc import x
        >>> a = Matrix([[1, I], [-I, 1]])
        >>> a
        Matrix([
        [ 1, I],
        [-I, 1]])
        >>> a.is_hermitian
        True
        >>> a[0, 0] = 2*I
        >>> a.is_hermitian
        False
        >>> a[0, 0] = x
        >>> a.is_hermitian
        >>> a[0, 1] = a[1, 0]*I
        >>> a.is_hermitian
        False
        """
        if not self.is_square:
            return False

        simpfunc = simplify
        if not isfunction(simplify):
            simpfunc = _simplify if simplify else lambda x: x

        return self._eval_is_matrix_hermitian(simpfunc)

    @property
    def is_Identity(self):
        if not self.is_square:
            return False
        return self._eval_is_Identity()

    @property
    def is_lower_hessenberg(self):
        r"""Checks if the matrix is in the lower-Hessenberg form.

        The lower hessenberg matrix has zero entries
        above the first superdiagonal.

        Examples
        ========

        >>> from sympy.matrices import Matrix
        >>> a = Matrix([[1, 2, 0, 0], [5, 2, 3, 0], [3, 4, 3, 7], [5, 6, 1, 1]])
        >>> a
        Matrix([
        [1, 2, 0, 0],
        [5, 2, 3, 0],
        [3, 4, 3, 7],
        [5, 6, 1, 1]])
        >>> a.is_lower_hessenberg
        True

        See Also
        ========

        is_upper_hessenberg
        is_lower
        """
        return self._eval_is_lower_hessenberg()

    @property
    def is_lower(self):
        """Check if matrix is a lower triangular matrix. True can be returned
        even if the matrix is not square.

        Examples
        ========

        >>> from sympy import Matrix
        >>> m = Matrix(2, 2, [1, 0, 0, 1])
        >>> m
        Matrix([
        [1, 0],
        [0, 1]])
        >>> m.is_lower
        True

        >>> m = Matrix(4, 3, [0, 0, 0, 2, 0, 0, 1, 4 , 0, 6, 6, 5])
        >>> m
        Matrix([
        [0, 0, 0],
        [2, 0, 0],
        [1, 4, 0],
        [6, 6, 5]])
        >>> m.is_lower
        True

        >>> from sympy.abc import x, y
        >>> m = Matrix(2, 2, [x**2 + y, y**2 + x, 0, x + y])
        >>> m
        Matrix([
        [x**2 + y, x + y**2],
        [       0,    x + y]])
        >>> m.is_lower
        False

        See Also
        ========

        is_upper
        is_diagonal
        is_lower_hessenberg
        """
        return self._eval_is_lower()

    @property
    def is_square(self):
        """Checks if a matrix is square.

        A matrix is square if the number of rows equals the number of columns.
        The empty matrix is square by definition, since the number of rows and
        the number of columns are both zero.

        Examples
        ========

        >>> from sympy import Matrix
        >>> a = Matrix([[1, 2, 3], [4, 5, 6]])
        >>> b = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> c = Matrix([])
        >>> a.is_square
        False
        >>> b.is_square
        True
        >>> c.is_square
        True
        """
        return self.rows == self.cols

    def is_symbolic(self):
        """Checks if any elements contain Symbols.

        Examples
        ========

        >>> from sympy.matrices import Matrix
        >>> from sympy.abc import x, y
        >>> M = Matrix([[x, y], [1, 0]])
        >>> M.is_symbolic()
        True

        """
        return self._eval_is_symbolic()

    def is_symmetric(self, simplify=True):
        """Check if matrix is symmetric matrix,
        that is square matrix and is equal to its transpose.

        By default, simplifications occur before testing symmetry.
        They can be skipped using 'simplify=False'; while speeding things a bit,
        this may however induce false negatives.

        Examples
        ========

        >>> from sympy import Matrix
        >>> m = Matrix(2, 2, [0, 1, 1, 2])
        >>> m
        Matrix([
        [0, 1],
        [1, 2]])
        >>> m.is_symmetric()
        True

        >>> m = Matrix(2, 2, [0, 1, 2, 0])
        >>> m
        Matrix([
        [0, 1],
        [2, 0]])
        >>> m.is_symmetric()
        False

        >>> m = Matrix(2, 3, [0, 0, 0, 0, 0, 0])
        >>> m
        Matrix([
        [0, 0, 0],
        [0, 0, 0]])
        >>> m.is_symmetric()
        False

        >>> from sympy.abc import x, y
        >>> m = Matrix(3, 3, [1, x**2 + 2*x + 1, y, (x + 1)**2 , 2, 0, y, 0, 3])
        >>> m
        Matrix([
        [         1, x**2 + 2*x + 1, y],
        [(x + 1)**2,              2, 0],
        [         y,              0, 3]])
        >>> m.is_symmetric()
        True

        If the matrix is already simplified, you may speed-up is_symmetric()
        test by using 'simplify=False'.

        >>> bool(m.is_symmetric(simplify=False))
        False
        >>> m1 = m.expand()
        >>> m1.is_symmetric(simplify=False)
        True
        """
        simpfunc = simplify
        if not isfunction(simplify):
            simpfunc = _simplify if simplify else lambda x: x

        if not self.is_square:
            return False

        return self._eval_is_symmetric(simpfunc)

    @property
    def is_upper_hessenberg(self):
        """Checks if the matrix is the upper-Hessenberg form.

        The upper hessenberg matrix has zero entries
        below the first subdiagonal.

        Examples
        ========

        >>> from sympy.matrices import Matrix
        >>> a = Matrix([[1, 4, 2, 3], [3, 4, 1, 7], [0, 2, 3, 4], [0, 0, 1, 3]])
        >>> a
        Matrix([
        [1, 4, 2, 3],
        [3, 4, 1, 7],
        [0, 2, 3, 4],
        [0, 0, 1, 3]])
        >>> a.is_upper_hessenberg
        True

        See Also
        ========

        is_lower_hessenberg
        is_upper
        """
        return self._eval_is_upper_hessenberg()

    @property
    def is_upper(self):
        """Check if matrix is an upper triangular matrix. True can be returned
        even if the matrix is not square.

        Examples
        ========

        >>> from sympy import Matrix
        >>> m = Matrix(2, 2, [1, 0, 0, 1])
        >>> m
        Matrix([
        [1, 0],
        [0, 1]])
        >>> m.is_upper
        True

        >>> m = Matrix(4, 3, [5, 1, 9, 0, 4 , 6, 0, 0, 5, 0, 0, 0])
        >>> m
        Matrix([
        [5, 1, 9],
        [0, 4, 6],
        [0, 0, 5],
        [0, 0, 0]])
        >>> m.is_upper
        True

        >>> m = Matrix(2, 3, [4, 2, 5, 6, 1, 1])
        >>> m
        Matrix([
        [4, 2, 5],
        [6, 1, 1]])
        >>> m.is_upper
        False

        See Also
        ========

        is_lower
        is_diagonal
        is_upper_hessenberg
        """
        return all(self[i, j].is_zero
                   for i in range(1, self.rows)
                   for j in range(min(i, self.cols)))

    @property
    def is_zero(self):
        """Checks if a matrix is a zero matrix.

        A matrix is zero if every element is zero.  A matrix need not be square
        to be considered zero.  The empty matrix is zero by the principle of
        vacuous truth.  For a matrix that may or may not be zero (e.g.
        contains a symbol), this will be None

        Examples
        ========

        >>> from sympy import Matrix, zeros
        >>> from sympy.abc import x
        >>> a = Matrix([[0, 0], [0, 0]])
        >>> b = zeros(3, 4)
        >>> c = Matrix([[0, 1], [0, 0]])
        >>> d = Matrix([])
        >>> e = Matrix([[x, 0], [0, 0]])
        >>> a.is_zero
        True
        >>> b.is_zero
        True
        >>> c.is_zero
        False
        >>> d.is_zero
        True
        >>> e.is_zero
        """
        return self._eval_is_zero()

    def values(self):
        """Return non-zero values of self."""
        return self._eval_values()


class MatrixOperations(MatrixRequired):
    """Provides basic matrix shape and elementwise
    operations.  Should not be instantiated directly."""

    def _eval_adjoint(self):
        return self.transpose().conjugate()

    def _eval_applyfunc(self, f):
        out = self._new(self.rows, self.cols, [f(x) for x in self])
        return out

    def _eval_as_real_imag(self):
        from sympy.functions.elementary.complexes import re, im

        return (self.applyfunc(re), self.applyfunc(im))

    def _eval_conjugate(self):
        return self.applyfunc(lambda x: x.conjugate())

    def _eval_permute_cols(self, perm):
        # apply the permutation to a list
        mapping = list(perm)

        def entry(i, j):
            return self[i, mapping[j]]

        return self._new(self.rows, self.cols, entry)

    def _eval_permute_rows(self, perm):
        # apply the permutation to a list
        mapping = list(perm)

        def entry(i, j):
            return self[mapping[i], j]

        return self._new(self.rows, self.cols, entry)

    def _eval_trace(self):
        return sum(self[i, i] for i in range(self.rows))

    def _eval_transpose(self):
        return self._new(self.cols, self.rows, lambda i, j: self[j, i])

    def adjoint(self):
        """Conjugate transpose or Hermitian conjugation."""
        return self._eval_adjoint()

    def applyfunc(self, f):
        """Apply a function to each element of the matrix.

        Examples
        ========

        >>> from sympy import Matrix
        >>> m = Matrix(2, 2, lambda i, j: i*2+j)
        >>> m
        Matrix([
        [0, 1],
        [2, 3]])
        >>> m.applyfunc(lambda i: 2*i)
        Matrix([
        [0, 2],
        [4, 6]])

        """
        if not callable(f):
            raise TypeError("`f` must be callable.")

        return self._eval_applyfunc(f)

    def as_real_imag(self):
        """Returns a tuple containing the (real, imaginary) part of matrix."""
        return self._eval_as_real_imag()

    def conjugate(self):
        """Return the by-element conjugation.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> from sympy import I
        >>> a = SparseMatrix(((1, 2 + I), (3, 4), (I, -I)))
        >>> a
        Matrix([
        [1, 2 + I],
        [3,     4],
        [I,    -I]])
        >>> a.C
        Matrix([
        [ 1, 2 - I],
        [ 3,     4],
        [-I,     I]])

        See Also
        ========

        transpose: Matrix transposition
        H: Hermite conjugation
        D: Dirac conjugation
        """
        return self._eval_conjugate()

    def doit(self, **kwargs):
        return self.applyfunc(lambda x: x.doit())

    def evalf(self, prec=None, **options):
        """Apply evalf() to each element of self."""
        return self.applyfunc(lambda i: i.evalf(prec, **options))

    def expand(self, deep=True, modulus=None, power_base=True, power_exp=True,
               mul=True, log=True, multinomial=True, basic=True, **hints):
        """Apply core.function.expand to each entry of the matrix.

        Examples
        ========

        >>> from sympy.abc import x
        >>> from sympy.matrices import Matrix
        >>> Matrix(1, 1, [x*(x+1)])
        Matrix([[x*(x + 1)]])
        >>> _.expand()
        Matrix([[x**2 + x]])

        """
        return self.applyfunc(lambda x: x.expand(
            deep, modulus, power_base, power_exp, mul, log, multinomial, basic,
            **hints))

    @property
    def H(self):
        """Return Hermite conjugate.

        Examples
        ========

        >>> from sympy import Matrix, I
        >>> m = Matrix((0, 1 + I, 2, 3))
        >>> m
        Matrix([
        [    0],
        [1 + I],
        [    2],
        [    3]])
        >>> m.H
        Matrix([[0, 1 - I, 2, 3]])

        See Also
        ========

        conjugate: By-element conjugation
        D: Dirac conjugation
        """
        return self.T.C

    def permute(self, perm, orientation='rows', direction='forward'):
        """Permute the rows or columns of a matrix by the given list of swaps.

        Parameters
        ==========

        perm : a permutation.  This may be a list swaps (e.g., `[[1, 2], [0, 3]]`),
            or any valid input to the `Permutation` constructor, including a `Permutation()`
            itself.  If `perm` is given explicitly as a list of indices or a `Permutation`,
            `direction` has no effect.
        orientation : ('rows' or 'cols') whether to permute the rows or the columns
        direction : ('forward', 'backward') whether to apply the permutations from
            the start of the list first, or from the back of the list first

        Examples
        ========

        >>> from sympy.matrices import eye
        >>> M = eye(3)
        >>> M.permute([[0, 1], [0, 2]], orientation='rows', direction='forward')
        Matrix([
        [0, 0, 1],
        [1, 0, 0],
        [0, 1, 0]])

        >>> from sympy.matrices import eye
        >>> M = eye(3)
        >>> M.permute([[0, 1], [0, 2]], orientation='rows', direction='backward')
        Matrix([
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0]])

        """

        # allow british variants and `columns`
        if direction == 'forwards':
            direction = 'forward'
        if direction == 'backwards':
            direction = 'backward'
        if orientation == 'columns':
            orientation = 'cols'

        if direction not in ('forward', 'backward'):
            raise TypeError("direction='{}' is an invalid kwarg. "
                            "Try 'forward' or 'backward'".format(direction))
        if orientation not in ('rows', 'cols'):
            raise TypeError("orientation='{}' is an invalid kwarg. "
                            "Try 'rows' or 'cols'".format(orientation))

        # ensure all swaps are in range
        max_index = self.rows if orientation == 'rows' else self.cols
        if not all(0 <= t <= max_index for t in flatten(list(perm))):
            raise IndexError("`swap` indices out of range.")

        # see if we are a list of pairs
        try:
            assert len(perm[0]) == 2
            # we are a list of swaps, so `direction` matters
            if direction == 'backward':
                perm = reversed(perm)

            # since Permutation doesn't let us have non-disjoint cycles,
            # we'll construct the explicit mapping ourselves XXX Bug #12479
            mapping = list(range(max_index))
            for (i, j) in perm:
                mapping[i], mapping[j] = mapping[j], mapping[i]
            perm = mapping
        except (TypeError, AssertionError, IndexError):
            pass

        from sympy.combinatorics import Permutation
        perm = Permutation(perm, size=max_index)

        if orientation == 'rows':
            return self._eval_permute_rows(perm)
        if orientation == 'cols':
            return self._eval_permute_cols(perm)

    def permute_cols(self, swaps, direction='forward'):
        """Alias for `self.permute(swaps, orientation='cols', direction=direction)`

        See Also
        ========

        permute
        """
        return self.permute(swaps, orientation='cols', direction=direction)

    def permute_rows(self, swaps, direction='forward'):
        """Alias for `self.permute(swaps, orientation='rows', direction=direction)`

        See Also
        ========

        permute
        """
        return self.permute(swaps, orientation='rows', direction=direction)

    def refine(self, assumptions=True):
        """Apply refine to each element of the matrix.

        Examples
        ========

        >>> from sympy import Symbol, Matrix, Abs, sqrt, Q
        >>> x = Symbol('x')
        >>> Matrix([[Abs(x)**2, sqrt(x**2)],[sqrt(x**2), Abs(x)**2]])
        Matrix([
        [ Abs(x)**2, sqrt(x**2)],
        [sqrt(x**2),  Abs(x)**2]])
        >>> _.refine(Q.real(x))
        Matrix([
        [  x**2, Abs(x)],
        [Abs(x),   x**2]])

        """
        return self.applyfunc(lambda x: refine(x, assumptions))

    def replace(self, F, G, map=False):
        """Replaces Function F in Matrix entries with Function G.

        Examples
        ========

        >>> from sympy import symbols, Function, Matrix
        >>> F, G = symbols('F, G', cls=Function)
        >>> M = Matrix(2, 2, lambda i, j: F(i+j)) ; M
        Matrix([
        [F(0), F(1)],
        [F(1), F(2)]])
        >>> N = M.replace(F,G)
        >>> N
        Matrix([
        [G(0), G(1)],
        [G(1), G(2)]])
        """
        return self.applyfunc(lambda x: x.replace(F, G, map))

    def simplify(self, ratio=1.7, measure=count_ops, rational=False, inverse=False):
        """Apply simplify to each element of the matrix.

        Examples
        ========

        >>> from sympy.abc import x, y
        >>> from sympy import sin, cos
        >>> from sympy.matrices import SparseMatrix
        >>> SparseMatrix(1, 1, [x*sin(y)**2 + x*cos(y)**2])
        Matrix([[x*sin(y)**2 + x*cos(y)**2]])
        >>> _.simplify()
        Matrix([[x]])
        """
        return self.applyfunc(lambda x: x.simplify(ratio=ratio, measure=measure,
                                                   rational=rational, inverse=inverse))

    def subs(self, *args, **kwargs):  # should mirror core.basic.subs
        """Return a new matrix with subs applied to each entry.

        Examples
        ========

        >>> from sympy.abc import x, y
        >>> from sympy.matrices import SparseMatrix, Matrix
        >>> SparseMatrix(1, 1, [x])
        Matrix([[x]])
        >>> _.subs(x, y)
        Matrix([[y]])
        >>> Matrix(_).subs(y, x)
        Matrix([[x]])
        """
        return self.applyfunc(lambda x: x.subs(*args, **kwargs))

    def trace(self):
        """
        Returns the trace of a square matrix i.e. the sum of the
        diagonal elements.

        Examples
        ========

        >>> from sympy import Matrix
        >>> A = Matrix(2, 2, [1, 2, 3, 4])
        >>> A.trace()
        5

        """
        if self.rows != self.cols:
            raise NonSquareMatrixError()
        return self._eval_trace()

    def transpose(self):
        """
        Returns the transpose of the matrix.

        Examples
        ========

        >>> from sympy import Matrix
        >>> A = Matrix(2, 2, [1, 2, 3, 4])
        >>> A.transpose()
        Matrix([
        [1, 3],
        [2, 4]])

        >>> from sympy import Matrix, I
        >>> m=Matrix(((1, 2+I), (3, 4)))
        >>> m
        Matrix([
        [1, 2 + I],
        [3,     4]])
        >>> m.transpose()
        Matrix([
        [    1, 3],
        [2 + I, 4]])
        >>> m.T == m.transpose()
        True

        See Also
        ========

        conjugate: By-element conjugation

        """
        return self._eval_transpose()

    T = property(transpose, None, None, "Matrix transposition.")

    C = property(conjugate, None, None, "By-element conjugation.")

    n = evalf

    def xreplace(self, rule):  # should mirror core.basic.xreplace
        """Return a new matrix with xreplace applied to each entry.

        Examples
        ========

        >>> from sympy.abc import x, y
        >>> from sympy.matrices import SparseMatrix, Matrix
        >>> SparseMatrix(1, 1, [x])
        Matrix([[x]])
        >>> _.xreplace({x: y})
        Matrix([[y]])
        >>> Matrix(_).xreplace({y: x})
        Matrix([[x]])
        """
        return self.applyfunc(lambda x: x.xreplace(rule))

    _eval_simplify = simplify

    def _eval_trigsimp(self, **opts):
        from sympy.simplify import trigsimp
        return self.applyfunc(lambda x: trigsimp(x, **opts))


class MatrixArithmetic(MatrixRequired):
    """Provides basic matrix arithmetic operations.
    Should not be instantiated directly."""

    _op_priority = 10.01

    def _eval_Abs(self):
        return self._new(self.rows, self.cols, lambda i, j: Abs(self[i, j]))

    def _eval_add(self, other):
        return self._new(self.rows, self.cols,
                         lambda i, j: self[i, j] + other[i, j])

    def _eval_matrix_mul(self, other):
        def entry(i, j):
            try:
                return sum(self[i,k]*other[k,j] for k in range(self.cols))
            except TypeError:
                # Block matrices don't work with `sum` or `Add` (ISSUE #11599)
                # They don't work with `sum` because `sum` tries to add `0`
                # initially, and for a matrix, that is a mix of a scalar and
                # a matrix, which raises a TypeError. Fall back to a
                # block-matrix-safe way to multiply if the `sum` fails.
                ret = self[i, 0]*other[0, j]
                for k in range(1, self.cols):
                    ret += self[i, k]*other[k, j]
                return ret

        return self._new(self.rows, other.cols, entry)

    def _eval_matrix_mul_elementwise(self, other):
        return self._new(self.rows, self.cols, lambda i, j: self[i,j]*other[i,j])

    def _eval_matrix_rmul(self, other):
        def entry(i, j):
            return sum(other[i,k]*self[k,j] for k in range(other.cols))
        return self._new(other.rows, self.cols, entry)

    def _eval_pow_by_recursion(self, num):
        if num == 1:
            return self
        if num % 2 == 1:
            return self * self._eval_pow_by_recursion(num - 1)
        ret = self._eval_pow_by_recursion(num // 2)
        return ret * ret

    def _eval_scalar_mul(self, other):
        return self._new(self.rows, self.cols, lambda i, j: self[i,j]*other)

    def _eval_scalar_rmul(self, other):
        return self._new(self.rows, self.cols, lambda i, j: other*self[i,j])

    def _eval_Mod(self, other):
        from sympy import Mod
        return self._new(self.rows, self.cols, lambda i, j: Mod(self[i, j], other))

    # python arithmetic functions
    def __abs__(self):
        """Returns a new matrix with entry-wise absolute values."""
        return self._eval_Abs()

    @call_highest_priority('__radd__')
    def __add__(self, other):
        """Return self + other, raising ShapeError if shapes don't match."""
        other = _matrixify(other)
        # matrix-like objects can have shapes.  This is
        # our first sanity check.
        if hasattr(other, 'shape'):
            if self.shape != other.shape:
                raise ShapeError("Matrix size mismatch: %s + %s" % (
                    self.shape, other.shape))

        # honest sympy matrices defer to their class's routine
        if getattr(other, 'is_Matrix', False):
            # call the highest-priority class's _eval_add
            a, b = self, other
            if a.__class__ != classof(a, b):
                b, a = a, b
            return a._eval_add(b)
        # Matrix-like objects can be passed to CommonMatrix routines directly.
        if getattr(other, 'is_MatrixLike', False):
            return MatrixArithmetic._eval_add(self, other)

        raise TypeError('cannot add %s and %s' % (type(self), type(other)))

    @call_highest_priority('__rdiv__')
    def __div__(self, other):
        return self * (S.One / other)

    @call_highest_priority('__rmatmul__')
    def __matmul__(self, other):
        other = _matrixify(other)
        if not getattr(other, 'is_Matrix', False) and not getattr(other, 'is_MatrixLike', False):
            return NotImplemented

        return self.__mul__(other)

    @call_highest_priority('__rmul__')
    def __mul__(self, other):
        """Return self*other where other is either a scalar or a matrix
        of compatible dimensions.

        Examples
        ========

        >>> from sympy.matrices import Matrix
        >>> A = Matrix([[1, 2, 3], [4, 5, 6]])
        >>> 2*A == A*2 == Matrix([[2, 4, 6], [8, 10, 12]])
        True
        >>> B = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> A*B
        Matrix([
        [30, 36, 42],
        [66, 81, 96]])
        >>> B*A
        Traceback (most recent call last):
        ...
        ShapeError: Matrices size mismatch.
        >>>

        See Also
        ========

        matrix_multiply_elementwise
        """
        other = _matrixify(other)
        # matrix-like objects can have shapes.  This is
        # our first sanity check.
        if hasattr(other, 'shape') and len(other.shape) == 2:
            if self.shape[1] != other.shape[0]:
                raise ShapeError("Matrix size mismatch: %s * %s." % (
                    self.shape, other.shape))

        # honest sympy matrices defer to their class's routine
        if getattr(other, 'is_Matrix', False):
            return self._eval_matrix_mul(other)
        # Matrix-like objects can be passed to CommonMatrix routines directly.
        if getattr(other, 'is_MatrixLike', False):
            return MatrixArithmetic._eval_matrix_mul(self, other)

        # if 'other' is not iterable then scalar multiplication.
        if not isinstance(other, Iterable):
            try:
                return self._eval_scalar_mul(other)
            except TypeError:
                pass

        return NotImplemented

    def __neg__(self):
        return self._eval_scalar_mul(-1)

    @call_highest_priority('__rpow__')
    def __pow__(self, num):
        if self.rows != self.cols:
            raise NonSquareMatrixError()
        a = self
        jordan_pow = getattr(a, '_matrix_pow_by_jordan_blocks', None)
        num = sympify(num)
        if num.is_Number and num % 1 == 0:
            if a.rows == 1:
                return a._new([[a[0]**num]])
            if num == 0:
                return self._new(self.rows, self.cols, lambda i, j: int(i == j))
            if num < 0:
                num = -num
                a = a.inv()
            # When certain conditions are met,
            # Jordan block algorithm is faster than
            # computation by recursion.
            elif a.rows == 2 and num > 100000 and jordan_pow is not None:
                try:
                    return jordan_pow(num)
                except MatrixError:
                    pass
            return a._eval_pow_by_recursion(num)
        elif not num.is_Number and num.is_negative is None and a.det() == 0:
            from sympy.matrices.expressions import MatPow
            return MatPow(a, num)
        elif isinstance(num, (Expr, float)):
            return jordan_pow(num)
        else:
            raise TypeError(
                "Only SymPy expressions or integers are supported as exponent for matrices")

    @call_highest_priority('__add__')
    def __radd__(self, other):
        return self + other

    @call_highest_priority('__matmul__')
    def __rmatmul__(self, other):
        other = _matrixify(other)
        if not getattr(other, 'is_Matrix', False) and not getattr(other, 'is_MatrixLike', False):
            return NotImplemented

        return self.__rmul__(other)

    @call_highest_priority('__mul__')
    def __rmul__(self, other):
        other = _matrixify(other)
        # matrix-like objects can have shapes.  This is
        # our first sanity check.
        if hasattr(other, 'shape') and len(other.shape) == 2:
            if self.shape[0] != other.shape[1]:
                raise ShapeError("Matrix size mismatch.")

        # honest sympy matrices defer to their class's routine
        if getattr(other, 'is_Matrix', False):
            return other._new(other.as_mutable() * self)
        # Matrix-like objects can be passed to CommonMatrix routines directly.
        if getattr(other, 'is_MatrixLike', False):
            return MatrixArithmetic._eval_matrix_rmul(self, other)

        # if 'other' is not iterable then scalar multiplication.
        if not isinstance(other, Iterable):
            try:
                return self._eval_scalar_rmul(other)
            except TypeError:
                pass

        return NotImplemented

    @call_highest_priority('__sub__')
    def __rsub__(self, a):
        return (-self) + a

    @call_highest_priority('__rsub__')
    def __sub__(self, a):
        return self + (-a)

    @call_highest_priority('__rtruediv__')
    def __truediv__(self, other):
        return self.__div__(other)

    def multiply_elementwise(self, other):
        """Return the Hadamard product (elementwise product) of A and B

        Examples
        ========

        >>> from sympy.matrices import Matrix
        >>> A = Matrix([[0, 1, 2], [3, 4, 5]])
        >>> B = Matrix([[1, 10, 100], [100, 10, 1]])
        >>> A.multiply_elementwise(B)
        Matrix([
        [  0, 10, 200],
        [300, 40,   5]])

        See Also
        ========

        cross
        dot
        multiply
        """
        if self.shape != other.shape:
            raise ShapeError("Matrix shapes must agree {} != {}".format(self.shape, other.shape))

        return self._eval_matrix_mul_elementwise(other)


class MatrixCommon(MatrixArithmetic, MatrixOperations, MatrixProperties,
                  MatrixSpecial, MatrixShaping):
    """All common matrix operations including basic arithmetic, shaping,
    and special matrices like `zeros`, and `eye`."""
    _diff_wrt = True


class _MinimalMatrix(object):
    """Class providing the minimum functionality
    for a matrix-like object and implementing every method
    required for a `MatrixRequired`.  This class does not have everything
    needed to become a full-fledged sympy object, but it will satisfy the
    requirements of anything inheriting from `MatrixRequired`.  If you wish
    to make a specialized matrix type, make sure to implement these
    methods and properties with the exception of `__init__` and `__repr__`
    which are included for convenience."""

    is_MatrixLike = True
    _sympify = staticmethod(sympify)
    _class_priority = 3

    is_Matrix = True
    is_MatrixExpr = False

    @classmethod
    def _new(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def __init__(self, rows, cols=None, mat=None):
        if isfunction(mat):
            # if we passed in a function, use that to populate the indices
            mat = list(mat(i, j) for i in range(rows) for j in range(cols))
        if cols is None and mat is None:
            mat = rows
        rows, cols = getattr(mat, 'shape', (rows, cols))
        try:
            # if we passed in a list of lists, flatten it and set the size
            if cols is None and mat is None:
                mat = rows
            cols = len(mat[0])
            rows = len(mat)
            mat = [x for l in mat for x in l]
        except (IndexError, TypeError):
            pass
        self.mat = tuple(self._sympify(x) for x in mat)
        self.rows, self.cols = rows, cols
        if self.rows is None or self.cols is None:
            raise NotImplementedError("Cannot initialize matrix with given parameters")

    def __getitem__(self, key):
        def _normalize_slices(row_slice, col_slice):
            """Ensure that row_slice and col_slice don't have
            `None` in their arguments.  Any integers are converted
            to slices of length 1"""
            if not isinstance(row_slice, slice):
                row_slice = slice(row_slice, row_slice + 1, None)
            row_slice = slice(*row_slice.indices(self.rows))

            if not isinstance(col_slice, slice):
                col_slice = slice(col_slice, col_slice + 1, None)
            col_slice = slice(*col_slice.indices(self.cols))

            return (row_slice, col_slice)

        def _coord_to_index(i, j):
            """Return the index in _mat corresponding
            to the (i,j) position in the matrix. """
            return i * self.cols + j

        if isinstance(key, tuple):
            i, j = key
            if isinstance(i, slice) or isinstance(j, slice):
                # if the coordinates are not slices, make them so
                # and expand the slices so they don't contain `None`
                i, j = _normalize_slices(i, j)

                rowsList, colsList = list(range(self.rows))[i], \
                                     list(range(self.cols))[j]
                indices = (i * self.cols + j for i in rowsList for j in
                           colsList)
                return self._new(len(rowsList), len(colsList),
                                 list(self.mat[i] for i in indices))

            # if the key is a tuple of ints, change
            # it to an array index
            key = _coord_to_index(i, j)
        return self.mat[key]

    def __eq__(self, other):
        try:
            classof(self, other)
        except TypeError:
            return False
        return (
            self.shape == other.shape and list(self) == list(other))

    def __len__(self):
        return self.rows*self.cols

    def __repr__(self):
        return "_MinimalMatrix({}, {}, {})".format(self.rows, self.cols,
                                                   self.mat)

    @property
    def shape(self):
        return (self.rows, self.cols)


class _MatrixWrapper(object):
    """Wrapper class providing the minimum functionality
    for a matrix-like object: .rows, .cols, .shape, indexability,
    and iterability.  CommonMatrix math operations should work
    on matrix-like objects.  For example, wrapping a numpy
    matrix in a MatrixWrapper allows it to be passed to CommonMatrix.
    """
    is_MatrixLike = True

    def __init__(self, mat, shape=None):
        self.mat = mat
        self.rows, self.cols = mat.shape if shape is None else shape

    def __getattr__(self, attr):
        """Most attribute access is passed straight through
        to the stored matrix"""
        return getattr(self.mat, attr)

    def __getitem__(self, key):
        return self.mat.__getitem__(key)


def _matrixify(mat):
    """If `mat` is a Matrix or is matrix-like,
    return a Matrix or MatrixWrapper object.  Otherwise
    `mat` is passed through without modification."""
    if getattr(mat, 'is_Matrix', False):
        return mat
    if hasattr(mat, 'shape'):
        if len(mat.shape) == 2:
            return _MatrixWrapper(mat)
    return mat


def a2idx(j, n=None):
    """Return integer after making positive and validating against n."""
    if type(j) is not int:
        jindex = getattr(j, '__index__', None)
        if jindex is not None:
            j = jindex()
        else:
            raise IndexError("Invalid index a[%r]" % (j,))
    if n is not None:
        if j < 0:
            j += n
        if not (j >= 0 and j < n):
            raise IndexError("Index out of range: a[%s]" % (j,))
    return int(j)


def classof(A, B):
    """
    Get the type of the result when combining matrices of different types.

    Currently the strategy is that immutability is contagious.

    Examples
    ========

    >>> from sympy import Matrix, ImmutableMatrix
    >>> from sympy.matrices.common import classof
    >>> M = Matrix([[1, 2], [3, 4]]) # a Mutable Matrix
    >>> IM = ImmutableMatrix([[1, 2], [3, 4]])
    >>> classof(M, IM)
    <class 'sympy.matrices.immutable.ImmutableDenseMatrix'>
    """
    priority_A = getattr(A, '_class_priority', None)
    priority_B = getattr(B, '_class_priority', None)
    if None not in (priority_A, priority_B):
        if A._class_priority > B._class_priority:
            return A.__class__
        else:
            return B.__class__

    try:
        import numpy
    except ImportError:
        pass
    else:
        if isinstance(A, numpy.ndarray):
            return B.__class__
        if isinstance(B, numpy.ndarray):
            return A.__class__

    raise TypeError("Incompatible classes %s, %s" % (A.__class__, B.__class__))
