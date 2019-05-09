"""
Fundamental arithmetic of dense matrices. The dense matrix is stored
as a list of lists.

"""
from sympy.core.compatibility import range

from sympy.utilities.exceptions import SymPyDeprecationWarning

SymPyDeprecationWarning(
    feature="densearith",
    issue=12695,
    deprecated_since_version="1.1").warn()

def add(matlist1, matlist2, K):
    """
    Adds matrices row-wise.

    Examples
    ========

    >>> from sympy.matrices.densearith import add
    >>> from sympy import ZZ
    >>> e = [
    ... [ZZ(12), ZZ(78)],
    ... [ZZ(56), ZZ(79)]]
    >>> f = [
    ... [ZZ(1), ZZ(2)],
    ... [ZZ(3), ZZ(4)]]
    >>> g = [
    ... [ZZ.zero, ZZ.zero],
    ... [ZZ.zero, ZZ.zero]]
    >>> add(e, f, ZZ)
    [[13, 80], [59, 83]]
    >>> add(f, g, ZZ)
    [[1, 2], [3, 4]]

    See Also
    ========

    addrow
    """
    return [addrow(row1, row2, K) for row1, row2 in zip(matlist1, matlist2)]

def addrow(row1, row2, K):
    """
    Adds two rows of a matrix element-wise.

    Examples
    ========

    >>> from sympy.matrices.densearith import addrow
    >>> from sympy import ZZ

    >>> a = [ZZ(12), ZZ(34), ZZ(56)]
    >>> b = [ZZ(14), ZZ(56), ZZ(63)]
    >>> c = [ZZ(0), ZZ(0), ZZ(0)]

    >>> addrow(a, b, ZZ)
    [26, 90, 119]
    >>> addrow(b, c, ZZ)
    [14, 56, 63]

    """
    return [element1 + element2 for element1, element2 in zip(row1, row2)]


def sub(matlist1, matlist2, K):
    """
    Subtracts two matrices by first negating the second matrix and
    then adding it to first matrix.

    Examples
    ========

    >>> from sympy.matrices.densearith import sub
    >>> from sympy import ZZ
    >>> e = [
    ... [ZZ(12), ZZ(78)],
    ... [ZZ(56), ZZ(79)]]
    >>> f = [
    ... [ZZ(1), ZZ(2)],
    ... [ZZ(3), ZZ(4)]]
    >>> g = [
    ... [ZZ.zero, ZZ.zero],
    ... [ZZ.zero, ZZ.zero]]
    >>> sub(e, f, ZZ)
    [[11, 76], [53, 75]]
    >>> sub(f, g, ZZ)
    [[1, 2], [3, 4]]

    See Also
    ========

    negate
    negaterow
    """
    return add(matlist1, negate(matlist2, K), K)


def negate(matlist, K):
    """
    Negates the elements of a matrix row-wise.

    Examples
    ========

    >>> from sympy.matrices.densearith import negate
    >>> from sympy import ZZ
    >>> a = [
    ... [ZZ(2), ZZ(3)],
    ... [ZZ(4), ZZ(5)]]
    >>> b = [
    ... [ZZ(0), ZZ(0)],
    ... [ZZ(0), ZZ(0)]]
    >>> negate(a, ZZ)
    [[-2, -3], [-4, -5]]
    >>> negate(b, ZZ)
    [[0, 0], [0, 0]]

    See Also
    ========

    negaterow
    """
    return [negaterow(row, K) for row in matlist]


def negaterow(row, K):
    """
    Negates a row element-wise.

    Examples
    ========

    >>> from sympy.matrices.densearith import negaterow
    >>> from sympy import ZZ
    >>> a = [ZZ(2), ZZ(3), ZZ(4)]
    >>> b = [ZZ(0), ZZ(0), ZZ(0)]
    >>> negaterow(a, ZZ)
    [-2, -3, -4]
    >>> negaterow(b, ZZ)
    [0, 0, 0]

    """
    return [-element for element in row]


def mulmatmat(matlist1, matlist2, K):
    """
    Multiplies two matrices by multiplying each row with each column at
    a time. The multiplication of row and column is done with mulrowcol.

    Firstly, the second matrix is converted from a list of rows to a
    list of columns using zip and then multiplication is done.

    Examples
    ========

    >>> from sympy.matrices.densearith import mulmatmat
    >>> from sympy import ZZ
    >>> from sympy.matrices.densetools import eye
    >>> a = [
    ... [ZZ(3), ZZ(4)],
    ... [ZZ(5), ZZ(6)]]
    >>> b = [
    ... [ZZ(1), ZZ(2)],
    ... [ZZ(7), ZZ(8)]]
    >>> c = eye(2, ZZ)
    >>> mulmatmat(a, b, ZZ)
    [[31, 38], [47, 58]]
    >>> mulmatmat(a, c, ZZ)
    [[3, 4], [5, 6]]

    See Also
    ========

    mulrowcol
    """
    matcol = [list(i) for i in zip(*matlist2)]
    result = []
    for row in matlist1:
        result.append([mulrowcol(row, col, K) for col in matcol])
    return result


def mulmatscaler(matlist, scaler, K):
    """
    Performs scaler matrix multiplication one row at at time. The row-scaler
    multiplication is done using mulrowscaler.

    Examples
    ========

    >>> from sympy import ZZ
    >>> from sympy.matrices.densearith import mulmatscaler
    >>> a = [
    ... [ZZ(3), ZZ(7), ZZ(4)],
    ... [ZZ(2), ZZ(4), ZZ(5)],
    ... [ZZ(6), ZZ(2), ZZ(3)]]
    >>> mulmatscaler(a, ZZ(1), ZZ)
    [[3, 7, 4], [2, 4, 5], [6, 2, 3]]

    See Also
    ========

    mulscalerrow
    """
    return [mulrowscaler(row, scaler, K) for row in matlist]


def mulrowscaler(row, scaler, K):
    """
    Performs the scaler-row multiplication element-wise.

    Examples
    ========

    >>> from sympy import ZZ
    >>> from sympy.matrices.densearith import mulrowscaler
    >>> a = [ZZ(3), ZZ(4), ZZ(5)]
    >>> mulrowscaler(a, 2, ZZ)
    [6, 8, 10]

    """
    return [scaler*element for element in row]


def mulrowcol(row, col, K):
    """
    Multiplies two lists representing row and column element-wise.

    Gotcha: Here the column is represented as a list contrary to the norm
    where it is represented as a list of one element lists. The reason is
    that the theoretically correct approach is too expensive. This problem
    is expected to be removed later as we have a good data structure to
    facilitate column operations.

    Examples
    ========

    >>> from sympy.matrices.densearith import mulrowcol
    >>> from sympy import ZZ

    >>> a = [ZZ(2), ZZ(4), ZZ(6)]
    >>> mulrowcol(a, a, ZZ)
    56

    """
    result = K.zero
    for i in range(len(row)):
        result += row[i]*col[i]
    return result
