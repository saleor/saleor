"""A module that handles matrices.

Includes functions for fast creating matrices like zero, one/eye, random
matrix, etc.
"""
from .common import ShapeError, NonSquareMatrixError
from .dense import (
    GramSchmidt, casoratian, diag, eye, hessian, jordan_cell,
    list2numpy, matrix2numpy, matrix_multiply_elementwise, ones,
    randMatrix, rot_axis1, rot_axis2, rot_axis3, symarray, wronskian,
    zeros)
from .dense import MutableDenseMatrix
from .matrices import DeferredVector, MatrixBase

Matrix = MutableMatrix = MutableDenseMatrix

from .sparse import MutableSparseMatrix
from .immutable import ImmutableDenseMatrix, ImmutableSparseMatrix

ImmutableMatrix = ImmutableDenseMatrix
SparseMatrix = MutableSparseMatrix

from .expressions import (
    MatrixSlice, BlockDiagMatrix, BlockMatrix, FunctionMatrix, Identity,
    Inverse, MatAdd, MatMul, MatPow, MatrixExpr, MatrixSymbol, Trace,
    Transpose, ZeroMatrix, blockcut, block_collapse, matrix_symbols, Adjoint,
    hadamard_product, HadamardProduct, Determinant, det, DiagonalMatrix,
    DiagonalOf, trace, DotProduct, kronecker_product, KroneckerProduct)
