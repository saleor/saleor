"""
This module contains query handlers responsible for calculus queries:
infinitesimal, bounded, etc.
"""
from __future__ import print_function, division

from sympy.logic.boolalg import conjuncts
from sympy.assumptions import Q, ask
from sympy.assumptions.handlers import CommonHandler, test_closed_group
from sympy.matrices.expressions import MatMul, MatrixExpr
from sympy.core.logic import fuzzy_and
from sympy.utilities.iterables import sift
from sympy.core import Basic
from functools import partial


def _Factorization(predicate, expr, assumptions):
    if predicate in expr.predicates:
        return True

class AskSquareHandler(CommonHandler):
    """
    Handler for key 'square'
    """

    @staticmethod
    def MatrixExpr(expr, assumptions):
        return expr.shape[0] == expr.shape[1]


class AskSymmetricHandler(CommonHandler):
    """
    Handler for key 'symmetric'
    """

    @staticmethod
    def MatMul(expr, assumptions):
        factor, mmul = expr.as_coeff_mmul()
        if all(ask(Q.symmetric(arg), assumptions) for arg in mmul.args):
            return True
        # TODO: implement sathandlers system for the matrices.
        # Now it duplicates the general fact: Implies(Q.diagonal, Q.symmetric).
        if ask(Q.diagonal(expr), assumptions):
            return True
        if len(mmul.args) >= 2 and mmul.args[0] == mmul.args[-1].T:
            if len(mmul.args) == 2:
                return True
            return ask(Q.symmetric(MatMul(*mmul.args[1:-1])), assumptions)

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if not int_exp:
            return None
        non_negative = ask(~Q.negative(exp), assumptions)
        if (non_negative or non_negative == False
                            and ask(Q.invertible(base), assumptions)):
            return ask(Q.symmetric(base), assumptions)
        return None

    @staticmethod
    def MatAdd(expr, assumptions):
        return all(ask(Q.symmetric(arg), assumptions) for arg in expr.args)

    @staticmethod
    def MatrixSymbol(expr, assumptions):
        if not expr.is_square:
            return False
        # TODO: implement sathandlers system for the matrices.
        # Now it duplicates the general fact: Implies(Q.diagonal, Q.symmetric).
        if ask(Q.diagonal(expr), assumptions):
            return True
        if Q.symmetric(expr) in conjuncts(assumptions):
            return True

    @staticmethod
    def ZeroMatrix(expr, assumptions):
        return ask(Q.square(expr), assumptions)

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.symmetric(expr.arg), assumptions)

    Inverse = Transpose

    @staticmethod
    def MatrixSlice(expr, assumptions):
        # TODO: implement sathandlers system for the matrices.
        # Now it duplicates the general fact: Implies(Q.diagonal, Q.symmetric).
        if ask(Q.diagonal(expr), assumptions):
            return True
        if not expr.on_diag:
            return None
        else:
            return ask(Q.symmetric(expr.parent), assumptions)

    Identity = staticmethod(CommonHandler.AlwaysTrue)


class AskInvertibleHandler(CommonHandler):
    """
    Handler for key 'invertible'
    """

    @staticmethod
    def MatMul(expr, assumptions):
        factor, mmul = expr.as_coeff_mmul()
        if all(ask(Q.invertible(arg), assumptions) for arg in mmul.args):
            return True
        if any(ask(Q.invertible(arg), assumptions) is False
               for arg in mmul.args):
            return False

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if not int_exp:
            return None
        if exp.is_negative == False:
            return ask(Q.invertible(base), assumptions)
        return None

    @staticmethod
    def MatAdd(expr, assumptions):
        return None

    @staticmethod
    def MatrixSymbol(expr, assumptions):
        if not expr.is_square:
            return False
        if Q.invertible(expr) in conjuncts(assumptions):
            return True

    Identity, Inverse = [staticmethod(CommonHandler.AlwaysTrue)]*2

    ZeroMatrix = staticmethod(CommonHandler.AlwaysFalse)

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.invertible(expr.arg), assumptions)

    @staticmethod
    def MatrixSlice(expr, assumptions):
        if not expr.on_diag:
            return None
        else:
            return ask(Q.invertible(expr.parent), assumptions)

class AskOrthogonalHandler(CommonHandler):
    """
    Handler for key 'orthogonal'
    """
    predicate = Q.orthogonal

    @staticmethod
    def MatMul(expr, assumptions):
        factor, mmul = expr.as_coeff_mmul()
        if (all(ask(Q.orthogonal(arg), assumptions) for arg in mmul.args) and
                factor == 1):
            return True
        if any(ask(Q.invertible(arg), assumptions) is False
                for arg in mmul.args):
            return False

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if int_exp:
            return ask(Q.orthogonal(base), assumptions)
        return None

    @staticmethod
    def MatAdd(expr, assumptions):
        if (len(expr.args) == 1 and
                ask(Q.orthogonal(expr.args[0]), assumptions)):
            return True

    @staticmethod
    def MatrixSymbol(expr, assumptions):
        if (not expr.is_square or
                        ask(Q.invertible(expr), assumptions) is False):
            return False
        if Q.orthogonal(expr) in conjuncts(assumptions):
            return True

    Identity = staticmethod(CommonHandler.AlwaysTrue)

    ZeroMatrix = staticmethod(CommonHandler.AlwaysFalse)

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.orthogonal(expr.arg), assumptions)

    Inverse = Transpose

    @staticmethod
    def MatrixSlice(expr, assumptions):
        if not expr.on_diag:
            return None
        else:
            return ask(Q.orthogonal(expr.parent), assumptions)

    Factorization = staticmethod(partial(_Factorization, Q.orthogonal))

class AskUnitaryHandler(CommonHandler):
    """
    Handler for key 'unitary'
    """
    predicate = Q.unitary

    @staticmethod
    def MatMul(expr, assumptions):
        factor, mmul = expr.as_coeff_mmul()
        if (all(ask(Q.unitary(arg), assumptions) for arg in mmul.args) and
                abs(factor) == 1):
            return True
        if any(ask(Q.invertible(arg), assumptions) is False
                for arg in mmul.args):
            return False

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if int_exp:
            return ask(Q.unitary(base), assumptions)
        return None

    @staticmethod
    def MatrixSymbol(expr, assumptions):
        if (not expr.is_square or
                        ask(Q.invertible(expr), assumptions) is False):
            return False
        if Q.unitary(expr) in conjuncts(assumptions):
            return True

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.unitary(expr.arg), assumptions)

    Inverse = Transpose

    @staticmethod
    def MatrixSlice(expr, assumptions):
        if not expr.on_diag:
            return None
        else:
            return ask(Q.unitary(expr.parent), assumptions)

    @staticmethod
    def DFT(expr, assumptions):
        return True

    Factorization = staticmethod(partial(_Factorization, Q.unitary))

    Identity = staticmethod(CommonHandler.AlwaysTrue)

    ZeroMatrix = staticmethod(CommonHandler.AlwaysFalse)

class AskFullRankHandler(CommonHandler):
    """
    Handler for key 'fullrank'
    """

    @staticmethod
    def MatMul(expr, assumptions):
        if all(ask(Q.fullrank(arg), assumptions) for arg in expr.args):
            return True

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if int_exp and ask(~Q.negative(exp), assumptions):
            return ask(Q.fullrank(base), assumptions)
        return None

    Identity = staticmethod(CommonHandler.AlwaysTrue)

    ZeroMatrix = staticmethod(CommonHandler.AlwaysFalse)

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.fullrank(expr.arg), assumptions)

    Inverse = Transpose

    @staticmethod
    def MatrixSlice(expr, assumptions):
        if ask(Q.orthogonal(expr.parent), assumptions):
            return True

class AskPositiveDefiniteHandler(CommonHandler):
    """
    Handler for key 'positive_definite'
    """

    @staticmethod
    def MatMul(expr, assumptions):
        factor, mmul = expr.as_coeff_mmul()
        if (all(ask(Q.positive_definite(arg), assumptions)
                for arg in mmul.args) and factor > 0):
            return True
        if (len(mmul.args) >= 2
                and mmul.args[0] == mmul.args[-1].T
                and ask(Q.fullrank(mmul.args[0]), assumptions)):
            return ask(Q.positive_definite(
                MatMul(*mmul.args[1:-1])), assumptions)

    @staticmethod
    def MatPow(expr, assumptions):
        # a power of a positive definite matrix is positive definite
        if ask(Q.positive_definite(expr.args[0]), assumptions):
            return True

    @staticmethod
    def MatAdd(expr, assumptions):
        if all(ask(Q.positive_definite(arg), assumptions)
                for arg in expr.args):
            return True

    @staticmethod
    def MatrixSymbol(expr, assumptions):
        if not expr.is_square:
            return False
        if Q.positive_definite(expr) in conjuncts(assumptions):
            return True

    Identity = staticmethod(CommonHandler.AlwaysTrue)

    ZeroMatrix = staticmethod(CommonHandler.AlwaysFalse)

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.positive_definite(expr.arg), assumptions)

    Inverse = Transpose

    @staticmethod
    def MatrixSlice(expr, assumptions):
        if not expr.on_diag:
            return None
        else:
            return ask(Q.positive_definite(expr.parent), assumptions)

class AskUpperTriangularHandler(CommonHandler):
    """
    Handler for key 'upper_triangular'
    """

    @staticmethod
    def MatMul(expr, assumptions):
        factor, matrices = expr.as_coeff_matrices()
        if all(ask(Q.upper_triangular(m), assumptions) for m in matrices):
            return True

    @staticmethod
    def MatAdd(expr, assumptions):
        if all(ask(Q.upper_triangular(arg), assumptions) for arg in expr.args):
            return True

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if not int_exp:
            return None
        non_negative = ask(~Q.negative(exp), assumptions)
        if (non_negative or non_negative == False
                            and ask(Q.invertible(base), assumptions)):
            return ask(Q.upper_triangular(base), assumptions)
        return None

    @staticmethod
    def MatrixSymbol(expr, assumptions):
        if Q.upper_triangular(expr) in conjuncts(assumptions):
            return True

    Identity, ZeroMatrix = [staticmethod(CommonHandler.AlwaysTrue)]*2

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.lower_triangular(expr.arg), assumptions)

    @staticmethod
    def Inverse(expr, assumptions):
        return ask(Q.upper_triangular(expr.arg), assumptions)

    @staticmethod
    def MatrixSlice(expr, assumptions):
        if not expr.on_diag:
            return None
        else:
            return ask(Q.upper_triangular(expr.parent), assumptions)

    Factorization = staticmethod(partial(_Factorization, Q.upper_triangular))

class AskLowerTriangularHandler(CommonHandler):
    """
    Handler for key 'lower_triangular'
    """

    @staticmethod
    def MatMul(expr, assumptions):
        factor, matrices = expr.as_coeff_matrices()
        if all(ask(Q.lower_triangular(m), assumptions) for m in matrices):
            return True

    @staticmethod
    def MatAdd(expr, assumptions):
        if all(ask(Q.lower_triangular(arg), assumptions) for arg in expr.args):
            return True

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if not int_exp:
            return None
        non_negative = ask(~Q.negative(exp), assumptions)
        if (non_negative or non_negative == False
                            and ask(Q.invertible(base), assumptions)):
            return ask(Q.lower_triangular(base), assumptions)
        return None

    @staticmethod
    def MatrixSymbol(expr, assumptions):
        if Q.lower_triangular(expr) in conjuncts(assumptions):
            return True

    Identity, ZeroMatrix = [staticmethod(CommonHandler.AlwaysTrue)]*2

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.upper_triangular(expr.arg), assumptions)

    @staticmethod
    def Inverse(expr, assumptions):
        return ask(Q.lower_triangular(expr.arg), assumptions)

    @staticmethod
    def MatrixSlice(expr, assumptions):
        if not expr.on_diag:
            return None
        else:
            return ask(Q.lower_triangular(expr.parent), assumptions)

    Factorization = staticmethod(partial(_Factorization, Q.lower_triangular))

class AskDiagonalHandler(CommonHandler):
    """
    Handler for key 'diagonal'
    """

    @staticmethod
    def _is_empty_or_1x1(expr):
        return expr.shape == (0, 0) or expr.shape == (1, 1)

    @staticmethod
    def MatMul(expr, assumptions):
        if AskDiagonalHandler._is_empty_or_1x1(expr):
            return True
        factor, matrices = expr.as_coeff_matrices()
        if all(ask(Q.diagonal(m), assumptions) for m in matrices):
            return True

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if not int_exp:
            return None
        non_negative = ask(~Q.negative(exp), assumptions)
        if (non_negative or non_negative == False
                            and ask(Q.invertible(base), assumptions)):
            return ask(Q.diagonal(base), assumptions)
        return None

    @staticmethod
    def MatAdd(expr, assumptions):
        if all(ask(Q.diagonal(arg), assumptions) for arg in expr.args):
            return True

    @staticmethod
    def MatrixSymbol(expr, assumptions):
        if AskDiagonalHandler._is_empty_or_1x1(expr):
            return True
        if Q.diagonal(expr) in conjuncts(assumptions):
            return True

    Identity, ZeroMatrix = [staticmethod(CommonHandler.AlwaysTrue)]*2

    @staticmethod
    def Transpose(expr, assumptions):
        return ask(Q.diagonal(expr.arg), assumptions)

    @staticmethod
    def Inverse(expr, assumptions):
        return ask(Q.diagonal(expr.arg), assumptions)

    @staticmethod
    def MatrixSlice(expr, assumptions):
        if AskDiagonalHandler._is_empty_or_1x1(expr):
            return True
        if not expr.on_diag:
            return None
        else:
            return ask(Q.diagonal(expr.parent), assumptions)

    @staticmethod
    def DiagonalMatrix(expr, assumptions):
        return True

    Factorization = staticmethod(partial(_Factorization, Q.diagonal))


def BM_elements(predicate, expr, assumptions):
    """ Block Matrix elements """
    return all(ask(predicate(b), assumptions) for b in expr.blocks)

def MS_elements(predicate, expr, assumptions):
    """ Matrix Slice elements """
    return ask(predicate(expr.parent), assumptions)

def MatMul_elements(matrix_predicate, scalar_predicate, expr, assumptions):
    d = sift(expr.args, lambda x: isinstance(x, MatrixExpr))
    factors, matrices = d[False], d[True]
    return fuzzy_and([
        test_closed_group(Basic(*factors), assumptions, scalar_predicate),
        test_closed_group(Basic(*matrices), assumptions, matrix_predicate)])

class AskIntegerElementsHandler(CommonHandler):
    @staticmethod
    def MatAdd(expr, assumptions):
        return test_closed_group(expr, assumptions, Q.integer_elements)

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if not int_exp:
            return None
        if exp.is_negative == False:
            return ask(Q.integer_elements(base), assumptions)
        return None

    HadamardProduct, Determinant, Trace, Transpose = [MatAdd]*4

    ZeroMatrix, Identity = [staticmethod(CommonHandler.AlwaysTrue)]*2

    MatMul = staticmethod(partial(MatMul_elements, Q.integer_elements,
                                                   Q.integer))
    MatrixSlice = staticmethod(partial(MS_elements, Q.integer_elements))
    BlockMatrix = staticmethod(partial(BM_elements, Q.integer_elements))

class AskRealElementsHandler(CommonHandler):
    @staticmethod
    def MatAdd(expr, assumptions):
        return test_closed_group(expr, assumptions, Q.real_elements)

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if not int_exp:
            return None
        non_negative = ask(~Q.negative(exp), assumptions)
        if (non_negative or non_negative == False
                            and ask(Q.invertible(base), assumptions)):
            return ask(Q.real_elements(base), assumptions)
        return None

    HadamardProduct, Determinant, Trace, Transpose, \
            Factorization = [MatAdd]*5

    MatMul = staticmethod(partial(MatMul_elements, Q.real_elements, Q.real))
    MatrixSlice = staticmethod(partial(MS_elements, Q.real_elements))
    BlockMatrix = staticmethod(partial(BM_elements, Q.real_elements))


class AskComplexElementsHandler(CommonHandler):
    @staticmethod
    def MatAdd(expr, assumptions):
        return test_closed_group(expr, assumptions, Q.complex_elements)

    @staticmethod
    def MatPow(expr, assumptions):
        # only for integer powers
        base, exp = expr.args
        int_exp = ask(Q.integer(exp), assumptions)
        if not int_exp:
            return None
        non_negative = ask(~Q.negative(exp), assumptions)
        if (non_negative or non_negative == False
                            and ask(Q.invertible(base), assumptions)):
            return ask(Q.complex_elements(base), assumptions)
        return None

    HadamardProduct, Determinant, Trace, Transpose, Inverse, \
         Factorization = [MatAdd]*6

    MatMul = staticmethod(partial(MatMul_elements, Q.complex_elements,
                                                   Q.complex))
    MatrixSlice = staticmethod(partial(MS_elements, Q.complex_elements))
    BlockMatrix = staticmethod(partial(BM_elements, Q.complex_elements))

    DFT = staticmethod(CommonHandler.AlwaysTrue)
