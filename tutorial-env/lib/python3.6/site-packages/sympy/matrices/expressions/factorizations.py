from __future__ import print_function, division

from sympy.matrices.expressions import MatrixExpr
from sympy import Q

class Factorization(MatrixExpr):
    arg = property(lambda self: self.args[0])
    shape = property(lambda self: self.arg.shape)

class LofLU(Factorization):
    predicates = Q.lower_triangular,
class UofLU(Factorization):
    predicates = Q.upper_triangular,

class LofCholesky(LofLU): pass
class UofCholesky(UofLU): pass

class QofQR(Factorization):
    predicates = Q.orthogonal,
class RofQR(Factorization):
    predicates = Q.upper_triangular,

class EigenVectors(Factorization):
    predicates = Q.orthogonal,
class EigenValues(Factorization):
    predicates = Q.diagonal,

class UofSVD(Factorization):
    predicates = Q.orthogonal,
class SofSVD(Factorization):
    predicates = Q.diagonal,
class VofSVD(Factorization):
    predicates = Q.orthogonal,


def lu(expr):
    return LofLU(expr), UofLU(expr)

def qr(expr):
    return QofQR(expr), RofQR(expr)

def eig(expr):
    return EigenValues(expr), EigenVectors(expr)

def svd(expr):
    return UofSVD(expr), SofSVD(expr), VofSVD(expr)
