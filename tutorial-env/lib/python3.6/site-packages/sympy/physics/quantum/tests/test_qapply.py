from sympy import I, Integer, sqrt, symbols, S, Mul

from sympy.physics.quantum.anticommutator import AntiCommutator
from sympy.physics.quantum.commutator import Commutator
from sympy.physics.quantum.constants import hbar
from sympy.physics.quantum.dagger import Dagger
from sympy.physics.quantum.gate import H
from sympy.physics.quantum.operator import Operator
from sympy.physics.quantum.qapply import qapply
from sympy.physics.quantum.spin import Jx, Jy, Jz, Jplus, Jminus, J2, JzKet
from sympy.physics.quantum.tensorproduct import TensorProduct
from sympy.physics.quantum.state import Ket
from sympy.physics.quantum.density import Density
from sympy.physics.quantum.qubit import Qubit
from sympy.physics.quantum.boson import BosonOp, BosonFockKet, BosonFockBra
from sympy.physics.quantum.tensorproduct import TensorProduct


j, jp, m, mp = symbols("j j' m m'")

z = JzKet(1, 0)
po = JzKet(1, 1)
mo = JzKet(1, -1)

A = Operator('A')


class Foo(Operator):
    def _apply_operator_JzKet(self, ket, **options):
        return ket


def test_basic():
    assert qapply(Jz*po) == hbar*po
    assert qapply(Jx*z) == hbar*po/sqrt(2) + hbar*mo/sqrt(2)
    assert qapply((Jplus + Jminus)*z/sqrt(2)) == hbar*po + hbar*mo
    assert qapply(Jz*(po + mo)) == hbar*po - hbar*mo
    assert qapply(Jz*po + Jz*mo) == hbar*po - hbar*mo
    assert qapply(Jminus*Jminus*po) == 2*hbar**2*mo
    assert qapply(Jplus**2*mo) == 2*hbar**2*po
    assert qapply(Jplus**2*Jminus**2*po) == 4*hbar**4*po


def test_extra():
    extra = z.dual*A*z
    assert qapply(Jz*po*extra) == hbar*po*extra
    assert qapply(Jx*z*extra) == (hbar*po/sqrt(2) + hbar*mo/sqrt(2))*extra
    assert qapply(
        (Jplus + Jminus)*z/sqrt(2)*extra) == hbar*po*extra + hbar*mo*extra
    assert qapply(Jz*(po + mo)*extra) == hbar*po*extra - hbar*mo*extra
    assert qapply(Jz*po*extra + Jz*mo*extra) == hbar*po*extra - hbar*mo*extra
    assert qapply(Jminus*Jminus*po*extra) == 2*hbar**2*mo*extra
    assert qapply(Jplus**2*mo*extra) == 2*hbar**2*po*extra
    assert qapply(Jplus**2*Jminus**2*po*extra) == 4*hbar**4*po*extra


def test_innerproduct():
    assert qapply(po.dual*Jz*po, ip_doit=False) == hbar*(po.dual*po)
    assert qapply(po.dual*Jz*po) == hbar


def test_zero():
    assert qapply(0) == 0
    assert qapply(Integer(0)) == 0


def test_commutator():
    assert qapply(Commutator(Jx, Jy)*Jz*po) == I*hbar**3*po
    assert qapply(Commutator(J2, Jz)*Jz*po) == 0
    assert qapply(Commutator(Jz, Foo('F'))*po) == 0
    assert qapply(Commutator(Foo('F'), Jz)*po) == 0


def test_anticommutator():
    assert qapply(AntiCommutator(Jz, Foo('F'))*po) == 2*hbar*po
    assert qapply(AntiCommutator(Foo('F'), Jz)*po) == 2*hbar*po


def test_outerproduct():
    e = Jz*(mo*po.dual)*Jz*po
    assert qapply(e) == -hbar**2*mo
    assert qapply(e, ip_doit=False) == -hbar**2*(po.dual*po)*mo
    assert qapply(e).doit() == -hbar**2*mo


def test_tensorproduct():
    a = BosonOp("a")
    b = BosonOp("b")
    ket1 = TensorProduct(BosonFockKet(1), BosonFockKet(2))
    ket2 = TensorProduct(BosonFockKet(0), BosonFockKet(0))
    ket3 = TensorProduct(BosonFockKet(0), BosonFockKet(2))
    bra1 = TensorProduct(BosonFockBra(0), BosonFockBra(0))
    bra2 = TensorProduct(BosonFockBra(1), BosonFockBra(2))
    assert qapply(TensorProduct(a, b ** 2) * ket1) == sqrt(2) * ket2
    assert qapply(TensorProduct(a, Dagger(b) * b) * ket1) == 2 * ket3
    assert qapply(bra1 * TensorProduct(a, b * b),
                  dagger=True) == sqrt(2) * bra2
    assert qapply(bra2 * ket1).doit() == TensorProduct(1, 1)
    assert qapply(TensorProduct(a, b * b) * ket1) == sqrt(2) * ket2
    assert qapply(Dagger(TensorProduct(a, b * b) * ket1),
                  dagger=True) == sqrt(2) * Dagger(ket2)


def test_dagger():
    lhs = Dagger(Qubit(0))*Dagger(H(0))
    rhs = Dagger(Qubit(1))/sqrt(2) + Dagger(Qubit(0))/sqrt(2)
    assert qapply(lhs, dagger=True) == rhs


def test_issue_6073():
    x, y = symbols('x y', commutative=False)
    A = Ket(x, y)
    B = Operator('B')
    assert qapply(A) == A
    assert qapply(A.dual*B) == A.dual*B


def test_density():
    d = Density([Jz*mo, 0.5], [Jz*po, 0.5])
    assert qapply(d) == Density([-hbar*mo, 0.5], [hbar*po, 0.5])


def test_issue3044():
    expr1 = TensorProduct(Jz*JzKet(S(2),S(-1))/sqrt(2), Jz*JzKet(S(1)/2,S(1)/2))
    result = Mul(S(-1), S(1)/4, (2**(S(1)/2)), hbar**2)
    result *= TensorProduct(JzKet(2,-1), JzKet(S(1)/2,S(1)/2))
    assert qapply(expr1) == result
