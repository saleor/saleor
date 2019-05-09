from __future__ import division, print_function

import copy
from collections import defaultdict

from sympy.core.compatibility import Callable, as_int, is_sequence, range
from sympy.core.containers import Dict
from sympy.core.expr import Expr
from sympy.core.singleton import S
from sympy.functions import Abs
from sympy.functions.elementary.miscellaneous import sqrt
from sympy.utilities.iterables import uniq

from .common import a2idx
from .dense import Matrix
from .matrices import MatrixBase, ShapeError


class SparseMatrix(MatrixBase):
    """
    A sparse matrix (a matrix with a large number of zero elements).

    Examples
    ========

    >>> from sympy.matrices import SparseMatrix
    >>> SparseMatrix(2, 2, range(4))
    Matrix([
    [0, 1],
    [2, 3]])
    >>> SparseMatrix(2, 2, {(1, 1): 2})
    Matrix([
    [0, 0],
    [0, 2]])

    See Also
    ========
    sympy.matrices.dense.Matrix
    """

    def __new__(cls, *args, **kwargs):
        self = object.__new__(cls)
        if len(args) == 1 and isinstance(args[0], SparseMatrix):
            self.rows = args[0].rows
            self.cols = args[0].cols
            self._smat = dict(args[0]._smat)
            return self

        self._smat = {}

        if len(args) == 3:
            self.rows = as_int(args[0])
            self.cols = as_int(args[1])

            if isinstance(args[2], Callable):
                op = args[2]
                for i in range(self.rows):
                    for j in range(self.cols):
                        value = self._sympify(
                            op(self._sympify(i), self._sympify(j)))
                        if value:
                            self._smat[(i, j)] = value
            elif isinstance(args[2], (dict, Dict)):
                # manual copy, copy.deepcopy() doesn't work
                for key in args[2].keys():
                    v = args[2][key]
                    if v:
                        self._smat[key] = self._sympify(v)
            elif is_sequence(args[2]):
                if len(args[2]) != self.rows*self.cols:
                    raise ValueError(
                        'List length (%s) != rows*columns (%s)' %
                        (len(args[2]), self.rows*self.cols))
                flat_list = args[2]
                for i in range(self.rows):
                    for j in range(self.cols):
                        value = self._sympify(flat_list[i*self.cols + j])
                        if value:
                            self._smat[(i, j)] = value
        else:
            # handle full matrix forms with _handle_creation_inputs
            r, c, _list = Matrix._handle_creation_inputs(*args)
            self.rows = r
            self.cols = c
            for i in range(self.rows):
                for j in range(self.cols):
                    value = _list[self.cols*i + j]
                    if value:
                        self._smat[(i, j)] = value
        return self

    def __eq__(self, other):
        self_shape = getattr(self, 'shape', None)
        other_shape = getattr(other, 'shape', None)
        if None in (self_shape, other_shape):
            return False
        if self_shape != other_shape:
            return False
        if isinstance(other, SparseMatrix):
            return self._smat == other._smat
        elif isinstance(other, MatrixBase):
            return self._smat == MutableSparseMatrix(other)._smat

    def __getitem__(self, key):

        if isinstance(key, tuple):
            i, j = key
            try:
                i, j = self.key2ij(key)
                return self._smat.get((i, j), S.Zero)
            except (TypeError, IndexError):
                if isinstance(i, slice):
                    # XXX remove list() when PY2 support is dropped
                    i = list(range(self.rows))[i]
                elif is_sequence(i):
                    pass
                elif isinstance(i, Expr) and not i.is_number:
                    from sympy.matrices.expressions.matexpr import MatrixElement
                    return MatrixElement(self, i, j)
                else:
                    if i >= self.rows:
                        raise IndexError('Row index out of bounds')
                    i = [i]
                if isinstance(j, slice):
                    # XXX remove list() when PY2 support is dropped
                    j = list(range(self.cols))[j]
                elif is_sequence(j):
                    pass
                elif isinstance(j, Expr) and not j.is_number:
                    from sympy.matrices.expressions.matexpr import MatrixElement
                    return MatrixElement(self, i, j)
                else:
                    if j >= self.cols:
                        raise IndexError('Col index out of bounds')
                    j = [j]
                return self.extract(i, j)

        # check for single arg, like M[:] or M[3]
        if isinstance(key, slice):
            lo, hi = key.indices(len(self))[:2]
            L = []
            for i in range(lo, hi):
                m, n = divmod(i, self.cols)
                L.append(self._smat.get((m, n), S.Zero))
            return L

        i, j = divmod(a2idx(key, len(self)), self.cols)
        return self._smat.get((i, j), S.Zero)

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def _cholesky_solve(self, rhs):
        # for speed reasons, this is not uncommented, but if you are
        # having difficulties, try uncommenting to make sure that the
        # input matrix is symmetric

        #assert self.is_symmetric()
        L = self._cholesky_sparse()
        Y = L._lower_triangular_solve(rhs)
        rv = L.T._upper_triangular_solve(Y)
        return rv

    def _cholesky_sparse(self):
        """Algorithm for numeric Cholesky factorization of a sparse matrix."""
        Crowstruc = self.row_structure_symbolic_cholesky()
        C = self.zeros(self.rows)
        for i in range(len(Crowstruc)):
            for j in Crowstruc[i]:
                if i != j:
                    C[i, j] = self[i, j]
                    summ = 0
                    for p1 in Crowstruc[i]:
                        if p1 < j:
                            for p2 in Crowstruc[j]:
                                if p2 < j:
                                    if p1 == p2:
                                        summ += C[i, p1]*C[j, p1]
                                else:
                                    break
                            else:
                                break
                    C[i, j] -= summ
                    C[i, j] /= C[j, j]
                else:
                    C[j, j] = self[j, j]
                    summ = 0
                    for k in Crowstruc[j]:
                        if k < j:
                            summ += C[j, k]**2
                        else:
                            break
                    C[j, j] -= summ
                    C[j, j] = sqrt(C[j, j])

        return C

    def _diagonal_solve(self, rhs):
        "Diagonal solve."
        return self._new(self.rows, 1, lambda i, j: rhs[i, 0] / self[i, i])

    def _eval_inverse(self, **kwargs):
        """Return the matrix inverse using Cholesky or LDL (default)
        decomposition as selected with the ``method`` keyword: 'CH' or 'LDL',
        respectively.

        Examples
        ========

        >>> from sympy import SparseMatrix, Matrix
        >>> A = SparseMatrix([
        ... [ 2, -1,  0],
        ... [-1,  2, -1],
        ... [ 0,  0,  2]])
        >>> A.inv('CH')
        Matrix([
        [2/3, 1/3, 1/6],
        [1/3, 2/3, 1/3],
        [  0,   0, 1/2]])
        >>> A.inv(method='LDL') # use of 'method=' is optional
        Matrix([
        [2/3, 1/3, 1/6],
        [1/3, 2/3, 1/3],
        [  0,   0, 1/2]])
        >>> A * _
        Matrix([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]])

        """
        sym = self.is_symmetric()
        M = self.as_mutable()
        I = M.eye(M.rows)
        if not sym:
            t = M.T
            r1 = M[0, :]
            M = t*M
            I = t*I
        method = kwargs.get('method', 'LDL')
        if method in "LDL":
            solve = M._LDL_solve
        elif method == "CH":
            solve = M._cholesky_solve
        else:
            raise NotImplementedError(
                'Method may be "CH" or "LDL", not %s.' % method)
        rv = M.hstack(*[solve(I[:, i]) for i in range(I.cols)])
        if not sym:
            scale = (r1*rv[:, 0])[0, 0]
            rv /= scale
        return self._new(rv)

    def _eval_Abs(self):
        return self.applyfunc(lambda x: Abs(x))

    def _eval_add(self, other):
        """If `other` is a SparseMatrix, add efficiently. Otherwise,
        do standard addition."""
        if not isinstance(other, SparseMatrix):
            return self + self._new(other)

        smat = {}
        zero = self._sympify(0)
        for key in set().union(self._smat.keys(), other._smat.keys()):
            sum = self._smat.get(key, zero) + other._smat.get(key, zero)
            if sum != 0:
                smat[key] = sum
        return self._new(self.rows, self.cols, smat)

    def _eval_col_insert(self, icol, other):
        if not isinstance(other, SparseMatrix):
            other = SparseMatrix(other)
        new_smat = {}
        # make room for the new rows
        for key, val in self._smat.items():
            row, col = key
            if col >= icol:
                col += other.cols
            new_smat[(row, col)] = val
        # add other's keys
        for key, val in other._smat.items():
            row, col = key
            new_smat[(row, col + icol)] = val
        return self._new(self.rows, self.cols + other.cols, new_smat)

    def _eval_conjugate(self):
        smat = {key: val.conjugate() for key,val in self._smat.items()}
        return self._new(self.rows, self.cols, smat)

    def _eval_extract(self, rowsList, colsList):
        urow = list(uniq(rowsList))
        ucol = list(uniq(colsList))
        smat = {}
        if len(urow)*len(ucol) < len(self._smat):
            # there are fewer elements requested than there are elements in the matrix
            for i, r in enumerate(urow):
                for j, c in enumerate(ucol):
                    smat[i, j] = self._smat.get((r, c), 0)
        else:
            # most of the request will be zeros so check all of self's entries,
            # keeping only the ones that are desired
            for rk, ck in self._smat:
                if rk in urow and ck in ucol:
                    smat[(urow.index(rk), ucol.index(ck))] = self._smat[(rk, ck)]

        rv = self._new(len(urow), len(ucol), smat)
        # rv is nominally correct but there might be rows/cols
        # which require duplication
        if len(rowsList) != len(urow):
            for i, r in enumerate(rowsList):
                i_previous = rowsList.index(r)
                if i_previous != i:
                    rv = rv.row_insert(i, rv.row(i_previous))
        if len(colsList) != len(ucol):
            for i, c in enumerate(colsList):
                i_previous = colsList.index(c)
                if i_previous != i:
                    rv = rv.col_insert(i, rv.col(i_previous))
        return rv

    @classmethod
    def _eval_eye(cls, rows, cols):
        entries = {(i,i): S.One for i in range(min(rows, cols))}
        return cls._new(rows, cols, entries)

    def _eval_has(self, *patterns):
        # if the matrix has any zeros, see if S.Zero
        # has the pattern.  If _smat is full length,
        # the matrix has no zeros.
        zhas = S.Zero.has(*patterns)
        if len(self._smat) == self.rows*self.cols:
            zhas = False
        return any(self[key].has(*patterns) for key in self._smat) or zhas

    def _eval_is_Identity(self):
        if not all(self[i, i] == 1 for i in range(self.rows)):
            return False
        return len(self._smat) == self.rows

    def _eval_is_symmetric(self, simpfunc):
        diff = (self - self.T).applyfunc(simpfunc)
        return len(diff.values()) == 0

    def _eval_matrix_mul(self, other):
        """Fast multiplication exploiting the sparsity of the matrix."""
        if not isinstance(other, SparseMatrix):
            return self*self._new(other)

        # if we made it here, we're both sparse matrices
        # create quick lookups for rows and cols
        row_lookup = defaultdict(dict)
        for (i,j), val in self._smat.items():
            row_lookup[i][j] = val
        col_lookup = defaultdict(dict)
        for (i,j), val in other._smat.items():
            col_lookup[j][i] = val

        smat = {}
        for row in row_lookup.keys():
            for col in col_lookup.keys():
                # find the common indices of non-zero entries.
                # these are the only things that need to be multiplied.
                indices = set(col_lookup[col].keys()) & set(row_lookup[row].keys())
                if indices:
                    val = sum(row_lookup[row][k]*col_lookup[col][k] for k in indices)
                    smat[(row, col)] = val
        return self._new(self.rows, other.cols, smat)

    def _eval_row_insert(self, irow, other):
        if not isinstance(other, SparseMatrix):
            other = SparseMatrix(other)
        new_smat = {}
        # make room for the new rows
        for key, val in self._smat.items():
            row, col = key
            if row >= irow:
                row += other.rows
            new_smat[(row, col)] = val
        # add other's keys
        for key, val in other._smat.items():
            row, col = key
            new_smat[(row + irow, col)] = val
        return self._new(self.rows + other.rows, self.cols, new_smat)

    def _eval_scalar_mul(self, other):
        return self.applyfunc(lambda x: x*other)

    def _eval_scalar_rmul(self, other):
        return self.applyfunc(lambda x: other*x)

    def _eval_transpose(self):
        """Returns the transposed SparseMatrix of this SparseMatrix.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> a = SparseMatrix(((1, 2), (3, 4)))
        >>> a
        Matrix([
        [1, 2],
        [3, 4]])
        >>> a.T
        Matrix([
        [1, 3],
        [2, 4]])
        """
        smat = {(j,i): val for (i,j),val in self._smat.items()}
        return self._new(self.cols, self.rows, smat)

    def _eval_values(self):
        return [v for k,v in self._smat.items() if not v.is_zero]

    @classmethod
    def _eval_zeros(cls, rows, cols):
        return cls._new(rows, cols, {})

    def _LDL_solve(self, rhs):
        # for speed reasons, this is not uncommented, but if you are
        # having difficulties, try uncommenting to make sure that the
        # input matrix is symmetric

        #assert self.is_symmetric()
        L, D = self._LDL_sparse()
        Z = L._lower_triangular_solve(rhs)
        Y = D._diagonal_solve(Z)
        return L.T._upper_triangular_solve(Y)

    def _LDL_sparse(self):
        """Algorithm for numeric LDL factization, exploiting sparse structure.
        """
        Lrowstruc = self.row_structure_symbolic_cholesky()
        L = self.eye(self.rows)
        D = self.zeros(self.rows, self.cols)

        for i in range(len(Lrowstruc)):
            for j in Lrowstruc[i]:
                if i != j:
                    L[i, j] = self[i, j]
                    summ = 0
                    for p1 in Lrowstruc[i]:
                        if p1 < j:
                            for p2 in Lrowstruc[j]:
                                if p2 < j:
                                    if p1 == p2:
                                        summ += L[i, p1]*L[j, p1]*D[p1, p1]
                                else:
                                    break
                        else:
                            break
                    L[i, j] -= summ
                    L[i, j] /= D[j, j]
                elif i == j:
                    D[i, i] = self[i, i]
                    summ = 0
                    for k in Lrowstruc[i]:
                        if k < i:
                            summ += L[i, k]**2*D[k, k]
                        else:
                            break
                    D[i, i] -= summ

        return L, D

    def _lower_triangular_solve(self, rhs):
        """Fast algorithm for solving a lower-triangular system,
        exploiting the sparsity of the given matrix.
        """
        rows = [[] for i in range(self.rows)]
        for i, j, v in self.row_list():
            if i > j:
                rows[i].append((j, v))
        X = rhs.copy()
        for i in range(self.rows):
            for j, v in rows[i]:
                X[i, 0] -= v*X[j, 0]
            X[i, 0] /= self[i, i]
        return self._new(X)

    @property
    def _mat(self):
        """Return a list of matrix elements.  Some routines
        in DenseMatrix use `_mat` directly to speed up operations."""
        return list(self)

    def _upper_triangular_solve(self, rhs):
        """Fast algorithm for solving an upper-triangular system,
        exploiting the sparsity of the given matrix.
        """
        rows = [[] for i in range(self.rows)]
        for i, j, v in self.row_list():
            if i < j:
                rows[i].append((j, v))
        X = rhs.copy()
        for i in range(self.rows - 1, -1, -1):
            rows[i].reverse()
            for j, v in rows[i]:
                X[i, 0] -= v*X[j, 0]
            X[i, 0] /= self[i, i]
        return self._new(X)


    def applyfunc(self, f):
        """Apply a function to each element of the matrix.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> m = SparseMatrix(2, 2, lambda i, j: i*2+j)
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

        out = self.copy()
        for k, v in self._smat.items():
            fv = f(v)
            if fv:
                out._smat[k] = fv
            else:
                out._smat.pop(k, None)
        return out

    def as_immutable(self):
        """Returns an Immutable version of this Matrix."""
        from .immutable import ImmutableSparseMatrix
        return ImmutableSparseMatrix(self)

    def as_mutable(self):
        """Returns a mutable version of this matrix.

        Examples
        ========

        >>> from sympy import ImmutableMatrix
        >>> X = ImmutableMatrix([[1, 2], [3, 4]])
        >>> Y = X.as_mutable()
        >>> Y[1, 1] = 5 # Can set values in Y
        >>> Y
        Matrix([
        [1, 2],
        [3, 5]])
        """
        return MutableSparseMatrix(self)

    def cholesky(self):
        """
        Returns the Cholesky decomposition L of a matrix A
        such that L * L.T = A

        A must be a square, symmetric, positive-definite
        and non-singular matrix

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> A = SparseMatrix(((25,15,-5),(15,18,0),(-5,0,11)))
        >>> A.cholesky()
        Matrix([
        [ 5, 0, 0],
        [ 3, 3, 0],
        [-1, 1, 3]])
        >>> A.cholesky() * A.cholesky().T == A
        True
        """

        from sympy.core.numbers import nan, oo
        if not self.is_symmetric():
            raise ValueError('Cholesky decomposition applies only to '
                'symmetric matrices.')
        M = self.as_mutable()._cholesky_sparse()
        if M.has(nan) or M.has(oo):
            raise ValueError('Cholesky decomposition applies only to '
                'positive-definite matrices')
        return self._new(M)

    def col_list(self):
        """Returns a column-sorted list of non-zero elements of the matrix.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> a=SparseMatrix(((1, 2), (3, 4)))
        >>> a
        Matrix([
        [1, 2],
        [3, 4]])
        >>> a.CL
        [(0, 0, 1), (1, 0, 3), (0, 1, 2), (1, 1, 4)]

        See Also
        ========
        col_op
        row_list
        """
        return [tuple(k + (self[k],)) for k in sorted(list(self._smat.keys()), key=lambda k: list(reversed(k)))]

    def copy(self):
        return self._new(self.rows, self.cols, self._smat)

    def LDLdecomposition(self):
        """
        Returns the LDL Decomposition (matrices ``L`` and ``D``) of matrix
        ``A``, such that ``L * D * L.T == A``. ``A`` must be a square,
        symmetric, positive-definite and non-singular.

        This method eliminates the use of square root and ensures that all
        the diagonal entries of L are 1.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> A = SparseMatrix(((25, 15, -5), (15, 18, 0), (-5, 0, 11)))
        >>> L, D = A.LDLdecomposition()
        >>> L
        Matrix([
        [   1,   0, 0],
        [ 3/5,   1, 0],
        [-1/5, 1/3, 1]])
        >>> D
        Matrix([
        [25, 0, 0],
        [ 0, 9, 0],
        [ 0, 0, 9]])
        >>> L * D * L.T == A
        True

        """
        from sympy.core.numbers import nan, oo
        if not self.is_symmetric():
            raise ValueError('LDL decomposition applies only to '
                'symmetric matrices.')
        L, D = self.as_mutable()._LDL_sparse()
        if L.has(nan) or L.has(oo) or D.has(nan) or D.has(oo):
            raise ValueError('LDL decomposition applies only to '
                'positive-definite matrices')

        return self._new(L), self._new(D)

    def liupc(self):
        """Liu's algorithm, for pre-determination of the Elimination Tree of
        the given matrix, used in row-based symbolic Cholesky factorization.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> S = SparseMatrix([
        ... [1, 0, 3, 2],
        ... [0, 0, 1, 0],
        ... [4, 0, 0, 5],
        ... [0, 6, 7, 0]])
        >>> S.liupc()
        ([[0], [], [0], [1, 2]], [4, 3, 4, 4])

        References
        ==========

        Symbolic Sparse Cholesky Factorization using Elimination Trees,
        Jeroen Van Grondelle (1999)
        http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.39.7582
        """
        # Algorithm 2.4, p 17 of reference

        # get the indices of the elements that are non-zero on or below diag
        R = [[] for r in range(self.rows)]
        for r, c, _ in self.row_list():
            if c <= r:
                R[r].append(c)

        inf = len(R)  # nothing will be this large
        parent = [inf]*self.rows
        virtual = [inf]*self.rows
        for r in range(self.rows):
            for c in R[r][:-1]:
                while virtual[c] < r:
                    t = virtual[c]
                    virtual[c] = r
                    c = t
                if virtual[c] == inf:
                    parent[c] = virtual[c] = r
        return R, parent

    def nnz(self):
        """Returns the number of non-zero elements in Matrix."""
        return len(self._smat)

    def row_list(self):
        """Returns a row-sorted list of non-zero elements of the matrix.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> a = SparseMatrix(((1, 2), (3, 4)))
        >>> a
        Matrix([
        [1, 2],
        [3, 4]])
        >>> a.RL
        [(0, 0, 1), (0, 1, 2), (1, 0, 3), (1, 1, 4)]

        See Also
        ========
        row_op
        col_list
        """
        return [tuple(k + (self[k],)) for k in
            sorted(list(self._smat.keys()), key=lambda k: list(k))]

    def row_structure_symbolic_cholesky(self):
        """Symbolic cholesky factorization, for pre-determination of the
        non-zero structure of the Cholesky factororization.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> S = SparseMatrix([
        ... [1, 0, 3, 2],
        ... [0, 0, 1, 0],
        ... [4, 0, 0, 5],
        ... [0, 6, 7, 0]])
        >>> S.row_structure_symbolic_cholesky()
        [[0], [], [0], [1, 2]]

        References
        ==========

        Symbolic Sparse Cholesky Factorization using Elimination Trees,
        Jeroen Van Grondelle (1999)
        http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.39.7582
        """

        R, parent = self.liupc()
        inf = len(R)  # this acts as infinity
        Lrow = copy.deepcopy(R)
        for k in range(self.rows):
            for j in R[k]:
                while j != inf and j != k:
                    Lrow[k].append(j)
                    j = parent[j]
            Lrow[k] = list(sorted(set(Lrow[k])))
        return Lrow

    def scalar_multiply(self, scalar):
        "Scalar element-wise multiplication"
        M = self.zeros(*self.shape)
        if scalar:
            for i in self._smat:
                v = scalar*self._smat[i]
                if v:
                    M._smat[i] = v
                else:
                    M._smat.pop(i, None)
        return M

    def solve_least_squares(self, rhs, method='LDL'):
        """Return the least-square fit to the data.

        By default the cholesky_solve routine is used (method='CH'); other
        methods of matrix inversion can be used. To find out which are
        available, see the docstring of the .inv() method.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix, Matrix, ones
        >>> A = Matrix([1, 2, 3])
        >>> B = Matrix([2, 3, 4])
        >>> S = SparseMatrix(A.row_join(B))
        >>> S
        Matrix([
        [1, 2],
        [2, 3],
        [3, 4]])

        If each line of S represent coefficients of Ax + By
        and x and y are [2, 3] then S*xy is:

        >>> r = S*Matrix([2, 3]); r
        Matrix([
        [ 8],
        [13],
        [18]])

        But let's add 1 to the middle value and then solve for the
        least-squares value of xy:

        >>> xy = S.solve_least_squares(Matrix([8, 14, 18])); xy
        Matrix([
        [ 5/3],
        [10/3]])

        The error is given by S*xy - r:

        >>> S*xy - r
        Matrix([
        [1/3],
        [1/3],
        [1/3]])
        >>> _.norm().n(2)
        0.58

        If a different xy is used, the norm will be higher:

        >>> xy += ones(2, 1)/10
        >>> (S*xy - r).norm().n(2)
        1.5

        """
        t = self.T
        return (t*self).inv(method=method)*t*rhs

    def solve(self, rhs, method='LDL'):
        """Return solution to self*soln = rhs using given inversion method.

        For a list of possible inversion methods, see the .inv() docstring.
        """
        if not self.is_square:
            if self.rows < self.cols:
                raise ValueError('Under-determined system.')
            elif self.rows > self.cols:
                raise ValueError('For over-determined system, M, having '
                    'more rows than columns, try M.solve_least_squares(rhs).')
        else:
            return self.inv(method=method)*rhs

    RL = property(row_list, None, None, "Alternate faster representation")

    CL = property(col_list, None, None, "Alternate faster representation")


class MutableSparseMatrix(SparseMatrix, MatrixBase):
    @classmethod
    def _new(cls, *args, **kwargs):
        return cls(*args)

    def __setitem__(self, key, value):
        """Assign value to position designated by key.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix, ones
        >>> M = SparseMatrix(2, 2, {})
        >>> M[1] = 1; M
        Matrix([
        [0, 1],
        [0, 0]])
        >>> M[1, 1] = 2; M
        Matrix([
        [0, 1],
        [0, 2]])
        >>> M = SparseMatrix(2, 2, {})
        >>> M[:, 1] = [1, 1]; M
        Matrix([
        [0, 1],
        [0, 1]])
        >>> M = SparseMatrix(2, 2, {})
        >>> M[1, :] = [[1, 1]]; M
        Matrix([
        [0, 0],
        [1, 1]])


        To replace row r you assign to position r*m where m
        is the number of columns:

        >>> M = SparseMatrix(4, 4, {})
        >>> m = M.cols
        >>> M[3*m] = ones(1, m)*2; M
        Matrix([
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [2, 2, 2, 2]])

        And to replace column c you can assign to position c:

        >>> M[2] = ones(m, 1)*4; M
        Matrix([
        [0, 0, 4, 0],
        [0, 0, 4, 0],
        [0, 0, 4, 0],
        [2, 2, 4, 2]])
        """
        rv = self._setitem(key, value)
        if rv is not None:
            i, j, value = rv
            if value:
                self._smat[(i, j)] = value
            elif (i, j) in self._smat:
                del self._smat[(i, j)]

    def as_mutable(self):
        return self.copy()

    __hash__ = None

    def col_del(self, k):
        """Delete the given column of the matrix.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> M = SparseMatrix([[0, 0], [0, 1]])
        >>> M
        Matrix([
        [0, 0],
        [0, 1]])
        >>> M.col_del(0)
        >>> M
        Matrix([
        [0],
        [1]])

        See Also
        ========

        row_del
        """
        newD = {}
        k = a2idx(k, self.cols)
        for (i, j) in self._smat:
            if j == k:
                pass
            elif j > k:
                newD[i, j - 1] = self._smat[i, j]
            else:
                newD[i, j] = self._smat[i, j]
        self._smat = newD
        self.cols -= 1

    def col_join(self, other):
        """Returns B augmented beneath A (row-wise joining)::

            [A]
            [B]

        Examples
        ========

        >>> from sympy import SparseMatrix, Matrix, ones
        >>> A = SparseMatrix(ones(3))
        >>> A
        Matrix([
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]])
        >>> B = SparseMatrix.eye(3)
        >>> B
        Matrix([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]])
        >>> C = A.col_join(B); C
        Matrix([
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]])
        >>> C == A.col_join(Matrix(B))
        True

        Joining along columns is the same as appending rows at the end
        of the matrix:

        >>> C == A.row_insert(A.rows, Matrix(B))
        True
        """
        # A null matrix can always be stacked (see  #10770)
        if self.rows == 0 and self.cols != other.cols:
            return self._new(0, other.cols, []).col_join(other)

        A, B = self, other
        if not A.cols == B.cols:
            raise ShapeError()
        A = A.copy()
        if not isinstance(B, SparseMatrix):
            k = 0
            b = B._mat
            for i in range(B.rows):
                for j in range(B.cols):
                    v = b[k]
                    if v:
                        A._smat[(i + A.rows, j)] = v
                    k += 1
        else:
            for (i, j), v in B._smat.items():
                A._smat[i + A.rows, j] = v
        A.rows += B.rows
        return A

    def col_op(self, j, f):
        """In-place operation on col j using two-arg functor whose args are
        interpreted as (self[i, j], i) for i in range(self.rows).

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> M = SparseMatrix.eye(3)*2
        >>> M[1, 0] = -1
        >>> M.col_op(1, lambda v, i: v + 2*M[i, 0]); M
        Matrix([
        [ 2, 4, 0],
        [-1, 0, 0],
        [ 0, 0, 2]])
        """
        for i in range(self.rows):
            v = self._smat.get((i, j), S.Zero)
            fv = f(v, i)
            if fv:
                self._smat[(i, j)] = fv
            elif v:
                self._smat.pop((i, j))

    def col_swap(self, i, j):
        """Swap, in place, columns i and j.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> S = SparseMatrix.eye(3); S[2, 1] = 2
        >>> S.col_swap(1, 0); S
        Matrix([
        [0, 1, 0],
        [1, 0, 0],
        [2, 0, 1]])
        """
        if i > j:
            i, j = j, i
        rows = self.col_list()
        temp = []
        for ii, jj, v in rows:
            if jj == i:
                self._smat.pop((ii, jj))
                temp.append((ii, v))
            elif jj == j:
                self._smat.pop((ii, jj))
                self._smat[ii, i] = v
            elif jj > j:
                break
        for k, v in temp:
            self._smat[k, j] = v

    def copyin_list(self, key, value):
        if not is_sequence(value):
            raise TypeError("`value` must be of type list or tuple.")
        self.copyin_matrix(key, Matrix(value))

    def copyin_matrix(self, key, value):
        # include this here because it's not part of BaseMatrix
        rlo, rhi, clo, chi = self.key2bounds(key)
        shape = value.shape
        dr, dc = rhi - rlo, chi - clo
        if shape != (dr, dc):
            raise ShapeError(
                "The Matrix `value` doesn't have the same dimensions "
                "as the in sub-Matrix given by `key`.")
        if not isinstance(value, SparseMatrix):
            for i in range(value.rows):
                for j in range(value.cols):
                    self[i + rlo, j + clo] = value[i, j]
        else:
            if (rhi - rlo)*(chi - clo) < len(self):
                for i in range(rlo, rhi):
                    for j in range(clo, chi):
                        self._smat.pop((i, j), None)
            else:
                for i, j, v in self.row_list():
                    if rlo <= i < rhi and clo <= j < chi:
                        self._smat.pop((i, j), None)
            for k, v in value._smat.items():
                i, j = k
                self[i + rlo, j + clo] = value[i, j]

    def fill(self, value):
        """Fill self with the given value.

        Notes
        =====

        Unless many values are going to be deleted (i.e. set to zero)
        this will create a matrix that is slower than a dense matrix in
        operations.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> M = SparseMatrix.zeros(3); M
        Matrix([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]])
        >>> M.fill(1); M
        Matrix([
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]])
        """
        if not value:
            self._smat = {}
        else:
            v = self._sympify(value)
            self._smat = {(i, j): v
                for i in range(self.rows) for j in range(self.cols)}

    def row_del(self, k):
        """Delete the given row of the matrix.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> M = SparseMatrix([[0, 0], [0, 1]])
        >>> M
        Matrix([
        [0, 0],
        [0, 1]])
        >>> M.row_del(0)
        >>> M
        Matrix([[0, 1]])

        See Also
        ========

        col_del
        """
        newD = {}
        k = a2idx(k, self.rows)
        for (i, j) in self._smat:
            if i == k:
                pass
            elif i > k:
                newD[i - 1, j] = self._smat[i, j]
            else:
                newD[i, j] = self._smat[i, j]
        self._smat = newD
        self.rows -= 1

    def row_join(self, other):
        """Returns B appended after A (column-wise augmenting)::

            [A B]

        Examples
        ========

        >>> from sympy import SparseMatrix, Matrix
        >>> A = SparseMatrix(((1, 0, 1), (0, 1, 0), (1, 1, 0)))
        >>> A
        Matrix([
        [1, 0, 1],
        [0, 1, 0],
        [1, 1, 0]])
        >>> B = SparseMatrix(((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        >>> B
        Matrix([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]])
        >>> C = A.row_join(B); C
        Matrix([
        [1, 0, 1, 1, 0, 0],
        [0, 1, 0, 0, 1, 0],
        [1, 1, 0, 0, 0, 1]])
        >>> C == A.row_join(Matrix(B))
        True

        Joining at row ends is the same as appending columns at the end
        of the matrix:

        >>> C == A.col_insert(A.cols, B)
        True
        """
        # A null matrix can always be stacked (see  #10770)
        if self.cols == 0 and self.rows != other.rows:
            return self._new(other.rows, 0, []).row_join(other)

        A, B = self, other
        if not A.rows == B.rows:
            raise ShapeError()
        A = A.copy()
        if not isinstance(B, SparseMatrix):
            k = 0
            b = B._mat
            for i in range(B.rows):
                for j in range(B.cols):
                    v = b[k]
                    if v:
                        A._smat[(i, j + A.cols)] = v
                    k += 1
        else:
            for (i, j), v in B._smat.items():
                A._smat[(i, j + A.cols)] = v
        A.cols += B.cols
        return A

    def row_op(self, i, f):
        """In-place operation on row ``i`` using two-arg functor whose args are
        interpreted as ``(self[i, j], j)``.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> M = SparseMatrix.eye(3)*2
        >>> M[0, 1] = -1
        >>> M.row_op(1, lambda v, j: v + 2*M[0, j]); M
        Matrix([
        [2, -1, 0],
        [4,  0, 0],
        [0,  0, 2]])

        See Also
        ========
        row
        zip_row_op
        col_op

        """
        for j in range(self.cols):
            v = self._smat.get((i, j), S.Zero)
            fv = f(v, j)
            if fv:
                self._smat[(i, j)] = fv
            elif v:
                self._smat.pop((i, j))

    def row_swap(self, i, j):
        """Swap, in place, columns i and j.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> S = SparseMatrix.eye(3); S[2, 1] = 2
        >>> S.row_swap(1, 0); S
        Matrix([
        [0, 1, 0],
        [1, 0, 0],
        [0, 2, 1]])
        """
        if i > j:
            i, j = j, i
        rows = self.row_list()
        temp = []
        for ii, jj, v in rows:
            if ii == i:
                self._smat.pop((ii, jj))
                temp.append((jj, v))
            elif ii == j:
                self._smat.pop((ii, jj))
                self._smat[i, jj] = v
            elif ii > j:
                break
        for k, v in temp:
            self._smat[j, k] = v

    def zip_row_op(self, i, k, f):
        """In-place operation on row ``i`` using two-arg functor whose args are
        interpreted as ``(self[i, j], self[k, j])``.

        Examples
        ========

        >>> from sympy.matrices import SparseMatrix
        >>> M = SparseMatrix.eye(3)*2
        >>> M[0, 1] = -1
        >>> M.zip_row_op(1, 0, lambda v, u: v + 2*u); M
        Matrix([
        [2, -1, 0],
        [4,  0, 0],
        [0,  0, 2]])

        See Also
        ========
        row
        row_op
        col_op

        """
        self.row_op(i, lambda v, j: f(v, self[k, j]))
