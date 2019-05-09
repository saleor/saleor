"""
Fundamental operations of dense matrices.
The dense matrix is stored as a list of lists

"""

from sympy.core.compatibility import range
from sympy.utilities.exceptions import SymPyDeprecationWarning

SymPyDeprecationWarning(
    feature="densetools",
    issue=12695,
    deprecated_since_version="1.1").warn()

def trace(matlist, K):
    """
    Returns the trace of a matrix.

    Examples
    ========

    >>> from sympy.matrices.densetools import trace, eye
    >>> from sympy import ZZ
    >>> a = [
    ... [ZZ(3), ZZ(7), ZZ(4)],
    ... [ZZ(2), ZZ(4), ZZ(5)],
    ... [ZZ(6), ZZ(2), ZZ(3)]]
    >>> b = eye(4, ZZ)
    >>> trace(a, ZZ)
    10
    >>> trace(b, ZZ)
    4

    """
    result = K.zero
    for i in range(len(matlist)):
        result += matlist[i][i]
    return result


def transpose(matlist, K):
    """
    Returns the transpose of a matrix

    Examples
    ========

    >>> from sympy.matrices.densetools import transpose
    >>> from sympy import ZZ
    >>> a = [
    ... [ZZ(3), ZZ(7), ZZ(4)],
    ... [ZZ(2), ZZ(4), ZZ(5)],
    ... [ZZ(6), ZZ(2), ZZ(3)]]
    >>> transpose(a, ZZ)
    [[3, 2, 6], [7, 4, 2], [4, 5, 3]]

    """
    return [list(a) for a in (zip(*matlist))]


def conjugate(matlist, K):
    """
    Returns the conjugate of a matrix row-wise.

    Examples
    ========

    >>> from sympy.matrices.densetools import conjugate
    >>> from sympy import ZZ
    >>> a = [
    ... [ZZ(3), ZZ(2), ZZ(6)],
    ... [ZZ(7), ZZ(4), ZZ(2)],
    ... [ZZ(4), ZZ(5), ZZ(3)]]
    >>> conjugate(a, ZZ)
    [[3, 2, 6], [7, 4, 2], [4, 5, 3]]

    See Also
    ========

    conjugate_row
    """
    return [conjugate_row(row, K) for row in matlist]


def conjugate_row(row, K):
    """
    Returns the conjugate of a row element-wise

    Examples
    ========

    >>> from sympy.matrices.densetools import conjugate_row
    >>> from sympy import ZZ
    >>> a = [ZZ(3), ZZ(2), ZZ(6)]
    >>> conjugate_row(a, ZZ)
    [3, 2, 6]
    """
    result = []
    for r in row:
        conj = getattr(r, 'conjugate', None)
        if conj is not None:
            conjrow = conj()
        else:
            conjrow = r
        result.append(conjrow)

    return result


def conjugate_transpose(matlist, K):
    """
    Returns the conjugate-transpose of a matrix

    Examples
    ========

    >>> from sympy import ZZ
    >>> from sympy.matrices.densetools import conjugate_transpose
    >>> a = [
    ... [ZZ(3), ZZ(7), ZZ(4)],
    ... [ZZ(2), ZZ(4), ZZ(5)],
    ... [ZZ(6), ZZ(2), ZZ(3)]]
    >>> conjugate_transpose(a, ZZ)
    [[3, 2, 6], [7, 4, 2], [4, 5, 3]]
    """
    return conjugate(transpose(matlist, K), K)


def augment(matlist, column, K):
    """
    Augments a matrix and a column.

    Examples
    ========

    >>> from sympy.matrices.densetools import augment
    >>> from sympy import ZZ
    >>> a = [
    ... [ZZ(3), ZZ(7), ZZ(4)],
    ... [ZZ(2), ZZ(4), ZZ(5)],
    ... [ZZ(6), ZZ(2), ZZ(3)]]
    >>> b = [
    ... [ZZ(4)],
    ... [ZZ(5)],
    ... [ZZ(6)]]
    >>> augment(a, b, ZZ)
    [[3, 7, 4, 4], [2, 4, 5, 5], [6, 2, 3, 6]]
    """
    return [row + element for row, element in zip(matlist, column)]


def eye(n, K):
    """
    Returns an identity matrix of size n.

    Examples
    ========

    >>> from sympy.matrices.densetools import eye
    >>> from sympy import ZZ
    >>> eye(3, ZZ)
    [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    """
    result = []
    for i in range(n):
        result.append([])
        for j in range(n):
            if (i == j):
                result[i].append(K(1))
            else:
                result[i].append(K.zero)
    return result


def row(matlist, i):
    """
    Returns the ith row of a matrix

    Examples
    ========

    >>> from sympy.matrices.densetools import row
    >>> from sympy import ZZ
    >>> a = [
    ... [ZZ(3), ZZ(7), ZZ(4)],
    ... [ZZ(2), ZZ(4), ZZ(5)],
    ... [ZZ(6), ZZ(2), ZZ(3)]]
    >>> row(a, 2)
    [6, 2, 3]
    """
    return matlist[i]


def col(matlist, i):
    """
    Returns the ith column of a matrix
    Note: Currently very expensive

    Examples
    ========

    >>> from sympy.matrices.densetools import col
    >>> from sympy import ZZ
    >>> a = [
    ... [ZZ(3), ZZ(7), ZZ(4)],
    ... [ZZ(2), ZZ(4), ZZ(5)],
    ... [ZZ(6), ZZ(2), ZZ(3)]]
    >>> col(a, 1)
    [[7], [4], [2]]
    """
    matcol = [list(l) for l in zip(*matlist)]
    return [[l] for l in matcol[i]]


def rowswap(matlist, index1, index2, K):
    """
    Returns the matrix with index1 row and index2 row swapped
    """
    matlist[index1], matlist[index2] = matlist[index2], matlist[index1]
    return matlist


def rowmul(matlist, index, k,  K):
    """
    Multiplies index row with k
    """
    for i in range(len(matlist[index])):
        matlist[index][i] = k*matlist[index][i]
    return matlist


def rowadd(matlist, index1, index2 , k, K):
    """
    Adds the index1 row with index2 row which in turn is multiplied by k
    """
    result = []
    for i in range(len(matlist[index1])):
        matlist[index1][i] = (matlist[index1][i] + k*matlist[index2][i])
    return matlist


def isHermitian(matlist, K):
    """
    Checks whether matrix is hermitian

    Examples
    ========

    >>> from sympy.matrices.densetools import isHermitian
    >>> from sympy import QQ
    >>> a = [
    ... [QQ(2,1), QQ(-1,1), QQ(-1,1)],
    ... [QQ(0,1), QQ(4,1), QQ(-1,1)],
    ... [QQ(0,1), QQ(0,1), QQ(3,1)]]
    >>> isHermitian(a, QQ)
    False
    """
    return conjugate_transpose(matlist, K) == matlist
