"""
Some examples have been taken from:

http://www.math.uwaterloo.ca/~hwolkowi//matrixcookbook.pdf
"""
from sympy import MatrixSymbol, Inverse, symbols, Determinant, Trace, Derivative
from sympy import MatAdd, Identity, MatMul, ZeroMatrix

k = symbols("k")

X = MatrixSymbol("X", k, k)
x = MatrixSymbol("x", k, 1)

A = MatrixSymbol("A", k, k)
B = MatrixSymbol("B", k, k)
C = MatrixSymbol("C", k, k)
D = MatrixSymbol("D", k, k)

a = MatrixSymbol("a", k, 1)
b = MatrixSymbol("b", k, 1)
c = MatrixSymbol("c", k, 1)
d = MatrixSymbol("d", k, 1)


def test_matrix_derivative_non_matrix_result():
    # This is a 4-dimensional array:
    assert A.diff(A) == Derivative(A, A)
    assert A.T.diff(A) == Derivative(A.T, A)
    assert (2*A).diff(A) == Derivative(2*A, A)
    assert MatAdd(A, A).diff(A) == Derivative(MatAdd(A, A), A)
    assert (A + B).diff(A) == Derivative(A + B, A)  # TODO: `B` can be removed.


def test_matrix_derivative_trivial_cases():
    # Cookbook example 33:
    # TODO: find a way to represent a four-dimensional zero-array:
    assert X.diff(A) == Derivative(X, A)


def test_matrix_derivative_with_inverse():

    # Cookbook example 61:
    expr = a.T*Inverse(X)*b
    assert expr.diff(X) == -Inverse(X).T*a*b.T*Inverse(X).T

    # Cookbook example 62:
    expr = Determinant(Inverse(X))
    # Not implemented yet:
    # assert expr.diff(X) == -Determinant(X.inv())*(X.inv()).T

    # Cookbook example 63:
    expr = Trace(A*Inverse(X)*B)
    assert expr.diff(X) == -(X**(-1)*B*A*X**(-1)).T

    # Cookbook example 64:
    expr = Trace(Inverse(X + A))
    assert expr.diff(X) == -(Inverse(X + A)).T**2


def test_matrix_derivative_vectors_and_scalars():

    assert x.diff(x) == Identity(k)
    assert x.T.diff(x) == Identity(k)

    # Cookbook example 69:
    expr = x.T*a
    assert expr.diff(x) == a
    expr = a.T*x
    assert expr.diff(x) == a

    # Cookbook example 70:
    expr = a.T*X*b
    assert expr.diff(X) == a*b.T

    # Cookbook example 71:
    expr = a.T*X.T*b
    assert expr.diff(X) == b*a.T

    # Cookbook example 72:
    expr = a.T*X*a
    assert expr.diff(X) == a*a.T
    expr = a.T*X.T*a
    assert expr.diff(X) == a*a.T

    # Cookbook example 77:
    expr = b.T*X.T*X*c
    assert expr.diff(X) == X*b*c.T + X*c*b.T

    # Cookbook example 78:
    expr = (B*x + b).T*C*(D*x + d)
    assert expr.diff(x) == B.T*C*(D*x + d) + D.T*C.T*(B*x + b)

    # Cookbook example 81:
    expr = x.T*B*x
    assert expr.diff(x) == B*x + B.T*x

    # Cookbook example 82:
    expr = b.T*X.T*D*X*c
    assert expr.diff(X) == D.T*X*b*c.T + D*X*c*b.T

    # Cookbook example 83:
    expr = (X*b + c).T*D*(X*b + c)
    assert expr.diff(X) == D*(X*b + c)*b.T + D.T*(X*b + c)*b.T


def test_matrix_derivatives_of_traces():

    expr = Trace(A)*A
    assert expr.diff(A) == Derivative(Trace(A)*A, A)

    ## First order:

    # Cookbook example 99:
    expr = Trace(X)
    assert expr.diff(X) == Identity(k)

    # Cookbook example 100:
    expr = Trace(X*A)
    assert expr.diff(X) == A.T

    # Cookbook example 101:
    expr = Trace(A*X*B)
    assert expr.diff(X) == A.T*B.T

    # Cookbook example 102:
    expr = Trace(A*X.T*B)
    assert expr.diff(X) == B*A

    # Cookbook example 103:
    expr = Trace(X.T*A)
    assert expr.diff(X) == A

    # Cookbook example 104:
    expr = Trace(A*X.T)
    assert expr.diff(X) == A

    # Cookbook example 105:
    # TODO: TensorProduct is not supported
    #expr = Trace(TensorProduct(A, X))
    #assert expr.diff(X) == Trace(A)*Identity(k)

    ## Second order:

    # Cookbook example 106:
    expr = Trace(X**2)
    assert expr.diff(X) == 2*X.T

    # Cookbook example 107:
    expr = Trace(X**2*B)
    assert expr.diff(X) == (X*B + B*X).T
    expr = Trace(MatMul(X, X, B))
    assert expr.diff(X) == (X*B + B*X).T

    # Cookbook example 108:
    expr = Trace(X.T*B*X)
    assert expr.diff(X) == B*X + B.T*X

    # Cookbook example 109:
    expr = Trace(B*X*X.T)
    assert expr.diff(X) == B*X + B.T*X

    # Cookbook example 110:
    expr = Trace(X*X.T*B)
    assert expr.diff(X) == B*X + B.T*X

    # Cookbook example 111:
    expr = Trace(X*B*X.T)
    assert expr.diff(X) == X*B.T + X*B

    # Cookbook example 112:
    expr = Trace(B*X.T*X)
    assert expr.diff(X) == X*B.T + X*B

    # Cookbook example 113:
    expr = Trace(X.T*X*B)
    assert expr.diff(X) == X*B.T + X*B

    # Cookbook example 114:
    expr = Trace(A*X*B*X)
    assert expr.diff(X) == A.T*X.T*B.T + B.T*X.T*A.T

    # Cookbook example 115:
    expr = Trace(X.T*X)
    assert expr.diff(X) == 2*X
    expr = Trace(X*X.T)
    assert expr.diff(X) == 2*X

    # Cookbook example 116:
    expr = Trace(B.T*X.T*C*X*B)
    assert expr.diff(X) == C.T*X*B*B.T + C*X*B*B.T

    # Cookbook example 117:
    expr = Trace(X.T*B*X*C)
    assert expr.diff(X) == B*X*C + B.T*X*C.T

    # Cookbook example 118:
    expr = Trace(A*X*B*X.T*C)
    assert expr.diff(X) == A.T*C.T*X*B.T + C*A*X*B

    # Cookbook example 119:
    expr = Trace((A*X*B + C)*(A*X*B + C).T)
    assert expr.diff(X) == 2*A.T*(A*X*B + C)*B.T

    # Cookbook example 120:
    # TODO: no support for TensorProduct.
    # expr = Trace(TensorProduct(X, X))
    # expr = Trace(X)*Trace(X)
    # expr.diff(X) == 2*Trace(X)*Identity(k)

    # Higher Order

    # Cookbook example 121:
    expr = Trace(X**k)
    #assert expr.diff(X) == k*(X**(k-1)).T

    # Cookbook example 122:
    expr = Trace(A*X**k)
    #assert expr.diff(X) == # Needs indices

    # Cookbook example 123:
    expr = Trace(B.T*X.T*C*X*X.T*C*X*B)
    assert expr.diff(X) == C*X*X.T*C*X*B*B.T + C.T*X*B*B.T*X.T*C.T*X + C*X*B*B.T*X.T*C*X + C.T*X*X.T*C.T*X*B*B.T

    # Other

    # Cookbook example 124:
    expr = Trace(A*X**(-1)*B)
    assert expr.diff(X) == -Inverse(X).T*A.T*B.T*Inverse(X).T

    # Cookbook example 125:
    expr = Trace(Inverse(X.T*C*X)*A)
    # Warning: result in the cookbook is equivalent if B and C are symmetric:
    assert expr.diff(X) == - X.inv().T*A.T*X.inv()*C.inv().T*X.inv().T - X.inv().T*A*X.inv()*C.inv()*X.inv().T

    # Cookbook example 126:
    expr = Trace((X.T*C*X).inv()*(X.T*B*X))
    assert expr.diff(X) == -2*C*X*(X.T*C*X).inv()*X.T*B*X*(X.T*C*X).inv() + 2*B*X*(X.T*C*X).inv()

    # Cookbook example 127:
    expr = Trace((A + X.T*C*X).inv()*(X.T*B*X))
    # Warning: result in the cookbook is equivalent if B and C are symmetric:
    assert expr.diff(X) == B*X*Inverse(A + X.T*C*X) - C*X*Inverse(A + X.T*C*X)*X.T*B*X*Inverse(A + X.T*C*X) - C.T*X*Inverse(A.T + (C*X).T*X)*X.T*B.T*X*Inverse(A.T + (C*X).T*X) + B.T*X*Inverse(A.T + (C*X).T*X)


def test_derivatives_of_complicated_matrix_expr():
    expr = a.T*(A*X*(X.T*B + X*A) + B.T*X.T*(a*b.T*(X*D*X.T + X*(X.T*B + A*X)*D*B - X.T*C.T*A)*B + B*(X*D.T + B*A*X*A.T - 3*X*D))*B + 42*X*B*X.T*A.T*(X + X.T))*b
    result = (B*(B*A*X*A.T - 3*X*D + X*D.T) + a*b.T*(X*(A*X + X.T*B)*D*B + X*D*X.T - X.T*C.T*A)*B)*B*b*a.T*B.T + B**2*b*a.T*B.T*X.T*a*b.T*X*D + 42*A*X*B.T*X.T*a*b.T + B*D*B**3*b*a.T*B.T*X.T*a*b.T*X + B*b*a.T*A*X + 42*a*b.T*(X + X.T)*A*X*B.T + b*a.T*X*B*a*b.T*B.T**2*X*D.T + b*a.T*X*B*a*b.T*B.T**3*D.T*(B.T*X + X.T*A.T) + 42*b*a.T*X*B*X.T*A.T + 42*A.T*(X + X.T)*b*a.T*X*B + A.T*B.T**2*X*B*a*b.T*B.T*A + A.T*a*b.T*(A.T*X.T + B.T*X) + A.T*X.T*b*a.T*X*B*a*b.T*B.T**3*D.T + B.T*X*B*a*b.T*B.T*D - 3*B.T*X*B*a*b.T*B.T*D.T - C.T*A*B**2*b*a.T*B.T*X.T*a*b.T + X.T*A.T*a*b.T*A.T
    assert expr.diff(X) == result


def test_mixed_deriv_mixed_expressions():

    expr = 3*Trace(A)
    assert expr.diff(A) == 3*Identity(k)

    expr = k
    deriv = expr.diff(A)
    assert isinstance(deriv, ZeroMatrix)
    assert deriv == ZeroMatrix(k, k)

    expr = Trace(A)**2
    assert expr.diff(A) == (2*Trace(A))*Identity(k)

    expr = Trace(A)*A
    # TODO: this is not yet supported:
    assert expr.diff(A) == Derivative(expr, A)

    expr = Trace(Trace(A)*A)
    assert expr.diff(A) == (2*Trace(A))*Identity(k)

    expr = Trace(Trace(Trace(A)*A)*A)
    assert expr.diff(A) == (3*Trace(A)**2)*Identity(k)
