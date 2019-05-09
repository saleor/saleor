# -*- coding: utf-8 -*-
from sympy.utilities.pytest import warns_deprecated_sympy

from sympy import Matrix, eye, symbols
from sympy.physics.units.dimensions import (
    Dimension, DimensionSystem, action, charge, current, length, mass, time,
    velocity)
from sympy.utilities.pytest import raises


def test_call():
    mksa = DimensionSystem((length, time, mass, current), (action,))
    with warns_deprecated_sympy():
        assert mksa(action) == mksa.print_dim_base(action)


def test_extend():
    ms = DimensionSystem((length, time), (velocity,))

    mks = ms.extend((mass,), (action,))

    res = DimensionSystem((length, time, mass), (velocity, action))
    assert mks.base_dims == res.base_dims
    assert mks.derived_dims == res.derived_dims


def test_sort_dims():
    with warns_deprecated_sympy():
        assert (DimensionSystem.sort_dims((length, velocity, time))
                                      == (length, time, velocity))


def test_list_dims():
    dimsys = DimensionSystem((length, time, mass))

    assert dimsys.list_can_dims == ("length", "mass", "time")


def test_dim_can_vector():
    dimsys = DimensionSystem((length, mass, time), (velocity, action))

    assert dimsys.dim_can_vector(length) == Matrix([1, 0, 0])
    assert dimsys.dim_can_vector(velocity) == Matrix([1, 0, -1])

    dimsys = DimensionSystem((length, velocity, action), (mass, time))

    assert dimsys.dim_can_vector(length) == Matrix([1, 0, 0])
    assert dimsys.dim_can_vector(velocity) == Matrix([1, 0, -1])


def test_dim_vector():
    dimsys = DimensionSystem(
        (length, mass, time),
        (velocity, action),
        {velocity: {length: 1, time: -1},
         action: {mass: 1, length: 2, time: -1}})

    assert dimsys.dim_vector(length) == Matrix([1, 0, 0])
    assert dimsys.dim_vector(velocity) == Matrix([1, 0, -1])

    dimsys = DimensionSystem((length, velocity, action), (mass, time))

    assert dimsys.dim_vector(length) == Matrix([0, 1, 0])
    assert dimsys.dim_vector(velocity) == Matrix([0, 0, 1])
    assert dimsys.dim_vector(time) == Matrix([0, 1, -1])


def test_inv_can_transf_matrix():
    dimsys = DimensionSystem((length, mass, time))

    assert dimsys.inv_can_transf_matrix == eye(3)

    dimsys = DimensionSystem((length, velocity, action))
    assert dimsys.inv_can_transf_matrix == Matrix([[1, 2, 1], [0, 1, 0], [-1, -1, 0]])


def test_can_transf_matrix():
    dimsys = DimensionSystem((length, mass, time))

    assert dimsys.can_transf_matrix == eye(3)

    dimsys = DimensionSystem((length, velocity, action))
    assert dimsys.can_transf_matrix == Matrix([[0, 1, 0], [1, -1, 1], [0, -1, -1]])


def test_is_consistent():
    assert DimensionSystem((length, time)).is_consistent is True
    #assert DimensionSystem((length, time, velocity)).is_consistent is False


def test_print_dim_base():
    mksa = DimensionSystem(
        (length, time, mass, current),
        (action,),
        {action: {mass: 1, length: 2, time: -1}})
    L, M, T = symbols("L M T")
    assert mksa.print_dim_base(action) == L**2*M/T


def test_dim():
    dimsys = DimensionSystem(
        (length, mass, time),
        (velocity, action),
        {velocity: {length: 1, time: -1},
         action: {mass: 1, length: 2, time: -1}}
    )
    assert dimsys.dim == 3
