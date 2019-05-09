from sympy.matrices.dense import Matrix
from sympy.polys.polymatrix import PolyMatrix
from sympy.polys import Poly

from sympy import S, ZZ, QQ, EX

from sympy.abc import x


def test_polymatrix():
    pm1 = PolyMatrix([[Poly(x**2, x), Poly(-x, x)], [Poly(x**3, x), Poly(-1 + x, x)]])
    v1 = PolyMatrix([[1, 0], [-1, 0]], ring='ZZ[x]')
    m1 = Matrix([[1, 0], [-1, 0]], ring='ZZ[x]')
    A = PolyMatrix([[Poly(x**2 + x, x), Poly(0, x)], \
                    [Poly(x**3 - x + 1, x), Poly(0, x)]])
    B = PolyMatrix([[Poly(x**2, x), Poly(-x, x)], [Poly(-x**2, x), Poly(x, x)]])
    assert A.ring == ZZ[x]
    assert isinstance(pm1*v1, PolyMatrix)
    assert pm1*v1 == A
    assert pm1*m1 == A
    assert v1*pm1 == B

    pm2 = PolyMatrix([[Poly(x**2, x, domain='QQ'), Poly(0, x, domain='QQ'), Poly(-x**2, x, domain='QQ'), \
                    Poly(x**3, x, domain='QQ'), Poly(0, x, domain='QQ'), Poly(-x**3, x, domain='QQ')]])
    assert pm2.ring == QQ[x]
    v2 = PolyMatrix([1, 0, 0, 0, 0, 0], ring='ZZ[x]')
    m2 = Matrix([1, 0, 0, 0, 0, 0], ring='ZZ[x]')
    C = PolyMatrix([[Poly(x**2, x, domain='QQ')]])
    assert pm2*v2 == C
    assert pm2*m2 == C

    pm3 = PolyMatrix([[Poly(x**2, x), S(1)]], ring='ZZ[x]')
    v3 = (S(1)/2)*pm3
    assert v3 == PolyMatrix([[Poly(S(1)/2*x**2, x, domain='QQ'), S(1)/2]], ring='EX')
    assert pm3*(S(1)/2) == v3
    assert v3.ring == EX

    pm4 = PolyMatrix([[Poly(x**2, x, domain='ZZ'), Poly(-x**2, x, domain='ZZ')]])
    v4 = Matrix([1, -1], ring='ZZ[x]')
    assert pm4*v4 == PolyMatrix([[Poly(2*x**2, x, domain='ZZ')]])

    assert len(PolyMatrix()) == 0
    assert PolyMatrix([1, 0, 0, 1])/(-1) == PolyMatrix([-1, 0, 0, -1])
