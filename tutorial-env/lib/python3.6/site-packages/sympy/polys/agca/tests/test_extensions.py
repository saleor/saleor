from sympy.polys.polytools import Poly
from sympy.polys.agca.extensions import FiniteExtension
from sympy.abc import x, t

def test_FiniteExtension():
    # Gaussian integers
    A = FiniteExtension(Poly(x**2 + 1, x))
    assert A.rank == 2
    assert str(A) == 'ZZ[x]/(x**2 + 1)'
    i = A.generator
    assert A.basis == (A.one, i)
    assert A(1) == A.one
    assert i**2 == A(-1)
    assert i**2 != -1  # no coercion
    assert (2 + i)*(1 - i) == 3 - i
    assert (1 + i)**8 == A(16)

    # Finite field of order 27
    F = FiniteExtension(Poly(x**3 - x + 1, x, modulus=3))
    assert F.rank == 3
    a = F.generator  # also generates the cyclic group F - {0}
    assert F.basis == (F(1), a, a**2)
    assert a**27 == a
    assert a**26 == F(1)
    assert a**13 == F(-1)
    assert a**9 == a + 1
    assert a**3 == a - 1
    assert a**6 == a**2 + a + 1

    # Function field of an elliptic curve
    K = FiniteExtension(Poly(t**2 - x**3 - x + 1, t, field=True))
    assert K.rank == 2
    assert str(K) == 'ZZ(x)[t]/(t**2 - x**3 - x + 1)'
    y = K.generator
    c = 1/(x**3 - x**2 + x - 1)
    assert (y + x)*(y - x)*c == K(1)  # explicit inverse of y + x
