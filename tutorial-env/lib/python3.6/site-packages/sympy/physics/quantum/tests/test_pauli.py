from sympy import I, Mul
from sympy.physics.quantum import (Dagger, Commutator, AntiCommutator, qapply,
                                   Operator)
from sympy.physics.quantum.pauli import (SigmaOpBase, SigmaX, SigmaY, SigmaZ,
                                         SigmaMinus, SigmaPlus,
                                         qsimplify_pauli)
from sympy.physics.quantum.pauli import SigmaZKet, SigmaZBra


sx, sy, sz = SigmaX(), SigmaY(), SigmaZ()
sx1, sy1, sz1 = SigmaX(1), SigmaY(1), SigmaZ(1)
sx2, sy2, sz2 = SigmaX(2), SigmaY(2), SigmaZ(2)

sm, sp = SigmaMinus(), SigmaPlus()
A, B = Operator("A"), Operator("B")


def test_pauli_operators_types():

    assert isinstance(sx, SigmaOpBase) and isinstance(sx, SigmaX)
    assert isinstance(sy, SigmaOpBase) and isinstance(sy, SigmaY)
    assert isinstance(sz, SigmaOpBase) and isinstance(sz, SigmaZ)
    assert isinstance(sm, SigmaOpBase) and isinstance(sm, SigmaMinus)
    assert isinstance(sp, SigmaOpBase) and isinstance(sp, SigmaPlus)


def test_pauli_operators_commutator():

    assert Commutator(sx, sy).doit() == 2 * I * sz
    assert Commutator(sy, sz).doit() == 2 * I * sx
    assert Commutator(sz, sx).doit() == 2 * I * sy


def test_pauli_operators_commutator_with_labels():

    assert Commutator(sx1, sy1).doit() == 2 * I * sz1
    assert Commutator(sy1, sz1).doit() == 2 * I * sx1
    assert Commutator(sz1, sx1).doit() == 2 * I * sy1

    assert Commutator(sx2, sy2).doit() == 2 * I * sz2
    assert Commutator(sy2, sz2).doit() == 2 * I * sx2
    assert Commutator(sz2, sx2).doit() == 2 * I * sy2

    assert Commutator(sx1, sy2).doit() == 0
    assert Commutator(sy1, sz2).doit() == 0
    assert Commutator(sz1, sx2).doit() == 0


def test_pauli_operators_anticommutator():

    assert AntiCommutator(sy, sz).doit() == 0
    assert AntiCommutator(sz, sx).doit() == 0
    assert AntiCommutator(sx, sm).doit() == 1
    assert AntiCommutator(sx, sp).doit() == 1


def test_pauli_operators_adjoint():

    assert Dagger(sx) == sx
    assert Dagger(sy) == sy
    assert Dagger(sz) == sz


def test_pauli_operators_adjoint_with_labels():

    assert Dagger(sx1) == sx1
    assert Dagger(sy1) == sy1
    assert Dagger(sz1) == sz1

    assert Dagger(sx1) != sx2
    assert Dagger(sy1) != sy2
    assert Dagger(sz1) != sz2


def test_pauli_operators_multiplication():

    assert qsimplify_pauli(sx * sx) == 1
    assert qsimplify_pauli(sy * sy) == 1
    assert qsimplify_pauli(sz * sz) == 1

    assert qsimplify_pauli(sx * sy) == I * sz
    assert qsimplify_pauli(sy * sz) == I * sx
    assert qsimplify_pauli(sz * sx) == I * sy

    assert qsimplify_pauli(sy * sx) == - I * sz
    assert qsimplify_pauli(sz * sy) == - I * sx
    assert qsimplify_pauli(sx * sz) == - I * sy


def test_pauli_operators_multiplication_with_labels():

    assert qsimplify_pauli(sx1 * sx1) == 1
    assert qsimplify_pauli(sy1 * sy1) == 1
    assert qsimplify_pauli(sz1 * sz1) == 1

    assert isinstance(sx1 * sx2, Mul)
    assert isinstance(sy1 * sy2, Mul)
    assert isinstance(sz1 * sz2, Mul)

    assert qsimplify_pauli(sx1 * sy1 * sx2 * sy2) == - sz1 * sz2
    assert qsimplify_pauli(sy1 * sz1 * sz2 * sx2) == - sx1 * sy2


def test_pauli_states():
    sx, sz = SigmaX(), SigmaZ()

    up = SigmaZKet(0)
    down = SigmaZKet(1)

    assert qapply(sx * up) == down
    assert qapply(sx * down) == up
    assert qapply(sz * up) == up
    assert qapply(sz * down) == - down

    up = SigmaZBra(0)
    down = SigmaZBra(1)

    assert qapply(up * sx, dagger=True) == down
    assert qapply(down * sx, dagger=True) == up
    assert qapply(up * sz, dagger=True) == up
    assert qapply(down * sz, dagger=True) == - down

    assert Dagger(SigmaZKet(0)) == SigmaZBra(0)
    assert Dagger(SigmaZBra(1)) == SigmaZKet(1)
