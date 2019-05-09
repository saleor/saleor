"""
Solution of equations using dense matrices.

The dense matrix is stored as a list of lists.

"""

import copy

from sympy.core.compatibility import range
from sympy.core.power import isqrt
from sympy.core.symbol import symbols
from sympy.matrices.densetools import (
    augment, col, conjugate_transpose, eye, rowadd, rowmul)
from sympy.utilities.exceptions import SymPyDeprecationWarning

SymPyDeprecationWarning(
    feature="densesolve",
    issue=12695,
    deprecated_since_version="1.1").warn()


def row_echelon(matlist, K):
    """
    Returns the row echelon form of a matrix with diagonal elements
    reduced to 1.

    Examples
    ========

    >>> from sympy.matrices.densesolve import row_echelon
    >>> from sympy import QQ
    >>> a = [
    ... [QQ(3), QQ(7), QQ(4)],
    ... [QQ(2), QQ(4), QQ(5)],
    ... [QQ(6), QQ(2), QQ(3)]]
    >>> row_echelon(a, QQ)
    [[1, 7/3, 4/3], [0, 1, -7/2], [0, 0, 1]]

    See Also
    ========

    rref
    """
    result_matlist = copy.deepcopy(matlist)
    nrow = len(result_matlist)
    for i in range(nrow):
        if (result_matlist[i][i] != 1 and result_matlist[i][i] != 0):
            rowmul(result_matlist, i, 1/result_matlist[i][i], K)
        for j in range(i + 1, nrow):
            if (result_matlist[j][i] != 0):
                rowadd(result_matlist, j, i, -result_matlist[j][i], K)
    return result_matlist


def rref(matlist, K):
    """
    Returns the reduced row echelon form of a Matrix.

    Examples
    ========

    >>> from sympy.matrices.densesolve import rref
    >>> from sympy import QQ
    >>> a = [
    ... [QQ(1), QQ(2), QQ(1)],
    ... [QQ(-2), QQ(-3), QQ(1)],
    ... [QQ(3), QQ(5), QQ(0)]]
    >>> rref(a, QQ)
    [[1, 0, -5], [0, 1, 3], [0, 0, 0]]

    See Also
    ========

    row_echelon
    """
    result_matlist = copy.deepcopy(matlist)
    result_matlist = row_echelon(result_matlist, K)
    nrow = len(result_matlist)
    for i in range(nrow):
        if result_matlist[i][i] == 1:
            for j in range(i):
                rowadd(result_matlist, j, i, -result_matlist[j][i], K)
    return result_matlist


def LU(matlist, K, reverse = 0):
    """
    It computes the LU decomposition of a matrix and returns L and U
    matrices.

    Examples
    ========

    >>> from sympy.matrices.densesolve import LU
    >>> from sympy import QQ
    >>> a = [
    ... [QQ(1), QQ(2), QQ(3)],
    ... [QQ(2), QQ(-4), QQ(6)],
    ... [QQ(3), QQ(-9), QQ(-3)]]
    >>> LU(a, QQ)
    ([[1, 0, 0], [2, 1, 0], [3, 15/8, 1]], [[1, 2, 3], [0, -8, 0], [0, 0, -12]])

    See Also
    ========

    upper_triangle
    lower_triangle
    """
    nrow = len(matlist)
    new_matlist1, new_matlist2 = eye(nrow, K), copy.deepcopy(matlist)
    for i in range(nrow):
        for j in range(i + 1, nrow):
            if (new_matlist2[j][i] != 0):
                new_matlist1[j][i] = new_matlist2[j][i]/new_matlist2[i][i]
                rowadd(new_matlist2, j, i, -new_matlist2[j][i]/new_matlist2[i][i], K)
    return new_matlist1, new_matlist2


def cholesky(matlist, K):
    """
    Performs the cholesky decomposition of a Hermitian matrix and
    returns L and it's conjugate transpose.

    Examples
    ========

    >>> from sympy.matrices.densesolve import cholesky
    >>> from sympy import QQ
    >>> cholesky([[QQ(25), QQ(15), QQ(-5)], [QQ(15), QQ(18), QQ(0)], [QQ(-5), QQ(0), QQ(11)]], QQ)
    ([[5, 0, 0], [3, 3, 0], [-1, 1, 3]], [[5, 3, -1], [0, 3, 1], [0, 0, 3]])

    See Also
    ========

    cholesky_solve
    """
    new_matlist = copy.deepcopy(matlist)
    nrow = len(new_matlist)
    L = eye(nrow, K)
    for i in range(nrow):
        for j in range(i + 1):
            a = K.zero
            for k in range(j):
                a += L[i][k]*L[j][k]
            if i == j:
                L[i][j] = isqrt(new_matlist[i][j] - a)
            else:
                L[i][j] = (new_matlist[i][j] - a)/L[j][j]
    return L, conjugate_transpose(L, K)


def LDL(matlist, K):
    """
    Performs the LDL decomposition of a hermitian matrix and returns L, D and
    transpose of L. Only applicable to rational entries.

    Examples
    ========

    >>> from sympy.matrices.densesolve import LDL
    >>> from sympy import QQ

    >>> a = [
    ... [QQ(4), QQ(12), QQ(-16)],
    ... [QQ(12), QQ(37), QQ(-43)],
    ... [QQ(-16), QQ(-43), QQ(98)]]
    >>> LDL(a, QQ)
    ([[1, 0, 0], [3, 1, 0], [-4, 5, 1]], [[4, 0, 0], [0, 1, 0], [0, 0, 9]], [[1, 3, -4], [0, 1, 5], [0, 0, 1]])

    """
    new_matlist = copy.deepcopy(matlist)
    nrow = len(new_matlist)
    L, D = eye(nrow, K), eye(nrow, K)
    for i in range(nrow):
        for j in range(i + 1):
            a = K.zero
            for k in range(j):
                a += L[i][k]*L[j][k]*D[k][k]
            if i == j:
                D[j][j] = new_matlist[j][j] - a
            else:
                L[i][j] = (new_matlist[i][j] - a)/D[j][j]
    return L, D, conjugate_transpose(L, K)


def upper_triangle(matlist, K):
    """
    Transforms a given matrix to an upper triangle matrix by performing
    row operations on it.

    Examples
    ========

    >>> from sympy.matrices.densesolve import upper_triangle
    >>> from sympy import QQ
    >>> a = [
    ... [QQ(4,1), QQ(12,1), QQ(-16,1)],
    ... [QQ(12,1), QQ(37,1), QQ(-43,1)],
    ... [QQ(-16,1), QQ(-43,1), QQ(98,1)]]
    >>> upper_triangle(a, QQ)
    [[4, 12, -16], [0, 1, 5], [0, 0, 9]]

    See Also
    ========

    LU
    """
    copy_matlist = copy.deepcopy(matlist)
    lower_triangle, upper_triangle = LU(copy_matlist, K)
    return upper_triangle


def lower_triangle(matlist, K):
    """
    Transforms a given matrix to a lower triangle matrix by performing
    row operations on it.

    Examples
    ========

    >>> from sympy.matrices.densesolve import lower_triangle
    >>> from sympy import QQ
    >>> a = [
    ... [QQ(4,1), QQ(12,1), QQ(-16)],
    ... [QQ(12,1), QQ(37,1), QQ(-43,1)],
    ... [QQ(-16,1), QQ(-43,1), QQ(98,1)]]
    >>> lower_triangle(a, QQ)
    [[1, 0, 0], [3, 1, 0], [-4, 5, 1]]

    See Also
    ========

    LU
    """
    copy_matlist = copy.deepcopy(matlist)
    lower_triangle, upper_triangle = LU(copy_matlist, K, reverse = 1)
    return lower_triangle


def rref_solve(matlist, variable, constant, K):
    """
    Solves a system of equations using reduced row echelon form given
    a matrix of coefficients, a vector of variables and a vector of constants.

    Examples
    ========

    >>> from sympy.matrices.densesolve import rref_solve
    >>> from sympy import QQ
    >>> from sympy import Dummy
    >>> x, y, z = Dummy('x'), Dummy('y'), Dummy('z')
    >>> coefficients = [
    ... [QQ(25), QQ(15), QQ(-5)],
    ... [QQ(15), QQ(18), QQ(0)],
    ... [QQ(-5), QQ(0), QQ(11)]]
    >>> constants = [
    ... [QQ(2)],
    ... [QQ(3)],
    ... [QQ(1)]]
    >>> variables = [
    ... [x],
    ... [y],
    ... [z]]
    >>> rref_solve(coefficients, variables, constants, QQ)
    [[-1/225], [23/135], [4/45]]

    See Also
    ========

    row_echelon
    augment
    """
    new_matlist = copy.deepcopy(matlist)
    augmented = augment(new_matlist, constant, K)
    solution = rref(augmented, K)
    return col(solution, -1)


def LU_solve(matlist, variable, constant, K):
    """
    Solves a system of equations using  LU decomposition given a matrix
    of coefficients, a vector of variables and a vector of constants.

    Examples
    ========

    >>> from sympy.matrices.densesolve import LU_solve
    >>> from sympy import QQ
    >>> from sympy import Dummy
    >>> x, y, z = Dummy('x'), Dummy('y'), Dummy('z')
    >>> coefficients = [
    ... [QQ(2), QQ(-1), QQ(-2)],
    ... [QQ(-4), QQ(6), QQ(3)],
    ... [QQ(-4), QQ(-2), QQ(8)]]
    >>> variables = [
    ... [x],
    ... [y],
    ... [z]]
    >>> constants = [
    ... [QQ(-1)],
    ... [QQ(13)],
    ... [QQ(-6)]]
    >>> LU_solve(coefficients, variables, constants, QQ)
    [[2], [3], [1]]

    See Also
    ========

    LU
    forward_substitution
    backward_substitution
    """
    new_matlist = copy.deepcopy(matlist)
    nrow = len(new_matlist)
    L, U = LU(new_matlist, K)
    y = [[i] for i in symbols('y:%i' % nrow)]
    forward_substitution(L, y, constant, K)
    backward_substitution(U, variable, y, K)
    return variable


def cholesky_solve(matlist, variable, constant, K):
    """
    Solves a system of equations using Cholesky decomposition given
    a matrix of coefficients, a vector of variables and a vector of constants.

    Examples
    ========

    >>> from sympy.matrices.densesolve import cholesky_solve
    >>> from sympy import QQ
    >>> from sympy import Dummy
    >>> x, y, z = Dummy('x'), Dummy('y'), Dummy('z')
    >>> coefficients = [
    ... [QQ(25), QQ(15), QQ(-5)],
    ... [QQ(15), QQ(18), QQ(0)],
    ... [QQ(-5), QQ(0), QQ(11)]]
    >>> variables = [
    ... [x],
    ... [y],
    ... [z]]
    >>> coefficients = [
    ... [QQ(2)],
    ... [QQ(3)],
    ... [QQ(1)]]
    >>> cholesky_solve([[QQ(25), QQ(15), QQ(-5)], [QQ(15), QQ(18), QQ(0)], [QQ(-5), QQ(0), QQ(11)]], [[x], [y], [z]], [[QQ(2)], [QQ(3)], [QQ(1)]], QQ)
    [[-1/225], [23/135], [4/45]]

    See Also
    ========

    cholesky
    forward_substitution
    backward_substitution
    """
    new_matlist = copy.deepcopy(matlist)
    nrow = len(new_matlist)
    L, Lstar = cholesky(new_matlist, K)
    y = [[i] for i in symbols('y:%i' % nrow)]
    forward_substitution(L, y, constant, K)
    backward_substitution(Lstar, variable, y, K)
    return variable


def forward_substitution(lower_triangle, variable, constant, K):
    """
    Performs forward substitution given a lower triangular matrix, a
    vector of variables and a vector of constants.

    Examples
    ========

    >>> from sympy.matrices.densesolve import forward_substitution
    >>> from sympy import QQ
    >>> from sympy import Dummy
    >>> x, y, z = Dummy('x'), Dummy('y'), Dummy('z')
    >>> a = [
    ... [QQ(1), QQ(0), QQ(0)],
    ... [QQ(-2), QQ(1), QQ(0)],
    ... [QQ(-2), QQ(-1), QQ(1)]]
    >>> variables = [
    ... [x],
    ... [y],
    ... [z]]
    >>> constants = [
    ... [QQ(-1)],
    ... [QQ(13)],
    ... [QQ(-6)]]
    >>> forward_substitution(a, variables, constants, QQ)
    [[-1], [11], [3]]

    See Also
    ========

    LU_solve
    cholesky_solve
    """
    copy_lower_triangle = copy.deepcopy(lower_triangle)
    nrow = len(copy_lower_triangle)
    result = []
    for i in range(nrow):
        a = K.zero
        for j in range(i):
            a += copy_lower_triangle[i][j]*variable[j][0]
        variable[i][0] = (constant[i][0] - a)/copy_lower_triangle[i][i]
    return variable


def backward_substitution(upper_triangle, variable, constant, K):
    """
    Performs forward substitution given a lower triangular matrix,
    a vector of variables and a vector constants.

    Examples
    ========

    >>> from sympy.matrices.densesolve import backward_substitution
    >>> from sympy import QQ
    >>> from sympy import Dummy
    >>> x, y, z = Dummy('x'), Dummy('y'), Dummy('z')
    >>> a = [
    ... [QQ(2), QQ(-1), QQ(-2)],
    ... [QQ(0), QQ(4), QQ(-1)],
    ... [QQ(0), QQ(0), QQ(3)]]
    >>> variables = [
    ... [x],
    ... [y],
    ... [z]]
    >>> constants = [
    ... [QQ(-1)],
    ... [QQ(11)],
    ... [QQ(3)]]
    >>> backward_substitution(a, variables, constants, QQ)
    [[2], [3], [1]]

    See Also
    ========

    LU_solve
    cholesky_solve
    """
    copy_upper_triangle = copy.deepcopy(upper_triangle)
    nrow = len(copy_upper_triangle)
    result = []
    for i in reversed(range(nrow)):
        a = K.zero
        for j in reversed(range(i + 1, nrow)):
            a += copy_upper_triangle[i][j]*variable[j][0]
        variable[i][0] = (constant[i][0] - a)/copy_upper_triangle[i][i]
    return variable
