'''Functions returning normal forms of matrices'''
from __future__ import division, print_function

from sympy.matrices.dense import diag


def smith_normal_form(m, domain = None):
    '''
    Return the Smith Normal Form of a matrix `m` over the ring `domain`.
    This will only work if the ring is a principal ideal domain.

    Examples
    ========

    >>> from sympy.polys.solvers import RawMatrix as Matrix
    >>> from sympy.polys.domains import ZZ
    >>> from sympy.matrices.normalforms import smith_normal_form
    >>> m = Matrix([[12, 6, 4], [3, 9, 6], [2, 16, 14]])
    >>> setattr(m, "ring", ZZ)
    >>> print(smith_normal_form(m))
    Matrix([[1, 0, 0], [0, 10, 0], [0, 0, -30]])

    '''
    invs = invariant_factors(m, domain=domain)
    smf = diag(*invs)
    n = len(invs)
    if m.rows > n:
        smf = smf.row_insert(m.rows, zeros(m.rows-n, m.cols))
    elif m.cols > n:
        smf = smf.col_insert(m.cols, zeros(m.rows, m.cols-n))
    return smf

def invariant_factors(m, domain = None):
    '''
    Return the tuple of abelian invariants for a matrix `m`
    (as in the Smith-Normal form)

    References
    ==========

    [1] https://en.wikipedia.org/wiki/Smith_normal_form#Algorithm
    [2] http://sierra.nmsu.edu/morandi/notes/SmithNormalForm.pdf

    '''
    if not domain:
        if not (hasattr(m, "ring") and m.ring.is_PID):
            raise ValueError(
                "The matrix entries must be over a principal ideal domain")
        else:
            domain = m.ring

    if len(m) == 0:
        return ()

    m = m[:, :]

    def add_rows(m, i, j, a, b, c, d):
        # replace m[i, :] by a*m[i, :] + b*m[j, :]
        # and m[j, :] by c*m[i, :] + d*m[j, :]
        for k in range(m.cols):
            e = m[i, k]
            m[i, k] = a*e + b*m[j, k]
            m[j, k] = c*e + d*m[j, k]

    def add_columns(m, i, j, a, b, c, d):
        # replace m[:, i] by a*m[:, i] + b*m[:, j]
        # and m[:, j] by c*m[:, i] + d*m[:, j]
        for k in range(m.rows):
            e = m[k, i]
            m[k, i] = a*e + b*m[k, j]
            m[k, j] = c*e + d*m[k, j]

    def clear_column(m):
        # make m[1:, 0] zero by row and column operations
        if m[0,0] == 0:
            return m
        pivot = m[0, 0]
        for j in range(1, m.rows):
            if m[j, 0] == 0:
                continue
            d, r = domain.div(m[j,0], pivot)
            if r == 0:
                add_rows(m, 0, j, 1, 0, -d, 1)
            else:
                a, b, g = domain.gcdex(pivot, m[j,0])
                d_0 = domain.div(m[j, 0], g)[0]
                d_j = domain.div(pivot, g)[0]
                add_rows(m, 0, j, a, b, d_0, -d_j)
                pivot = g
        return m

    def clear_row(m):
        # make m[0, 1:] zero by row and column operations
        if m[0] == 0:
            return m
        pivot = m[0, 0]
        for j in range(1, m.cols):
            if m[0, j] == 0:
                continue
            d, r = domain.div(m[0, j], pivot)
            if r == 0:
                add_columns(m, 0, j, 1, 0, -d, 1)
            else:
                a, b, g = domain.gcdex(pivot, m[0, j])
                d_0 = domain.div(m[0, j], g)[0]
                d_j = domain.div(pivot, g)[0]
                add_columns(m, 0, j, a, b, d_0, -d_j)
                pivot = g
        return m

    # permute the rows and columns until m[0,0] is non-zero if possible
    ind = [i for i in range(m.rows) if m[i,0] != 0]
    if ind:
        m = m.permute_rows([[0, ind[0]]])
    else:
        ind = [j for j in range(m.cols) if m[0,j] != 0]
        if ind:
            m = m.permute_cols([[0, ind[0]]])

    # make the first row and column except m[0,0] zero
    while (any([m[0,i] != 0 for i in range(1,m.cols)]) or
           any([m[i,0] != 0 for i in range(1,m.rows)])):
        m = clear_column(m)
        m = clear_row(m)

    if 1 in m.shape:
        invs = ()
    else:
        invs = invariant_factors(m[1:,1:], domain=domain)

    if m[0,0]:
        result = [m[0,0]]
        result.extend(invs)
        # in case m[0] doesn't divide the invariants of the rest of the matrix
        for i in range(len(result)-1):
            if result[i] and domain.div(result[i+1], result[i])[1] != 0:
                g = domain.gcd(result[i+1], result[i])
                result[i+1] = domain.div(result[i], g)[0]*result[i+1]
                result[i] = g
            else:
                break
    else:
        result = invs + (m[0,0],)
    return tuple(result)
