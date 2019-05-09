# -*- coding: utf-8 -*-
from sympy.utilities.pytest import warns_deprecated_sympy

from sympy import Rational, S
from sympy.physics.units.definitions import c, kg, m, s
from sympy.physics.units.dimensions import (
    Dimension, DimensionSystem, action, current, length, mass, time, velocity)
from sympy.physics.units.quantities import Quantity
from sympy.physics.units.unitsystem import UnitSystem
from sympy.utilities.pytest import raises


def test_definition():
    # want to test if the system can have several units of the same dimension
    dm = Quantity("dm")
    dm.set_dimension(length)

    dm.set_scale_factor(Rational(1, 10))

    base = (m, s)
    base_dim = (m.dimension, s.dimension)
    ms = UnitSystem(base, (c, dm), "MS", "MS system")

    assert set(ms._base_units) == set(base)
    assert set(ms._units) == set((m, s, c, dm))
    #assert ms._units == DimensionSystem._sort_dims(base + (velocity,))
    assert ms.name == "MS"
    assert ms.descr == "MS system"

    assert ms._system.base_dims == base_dim
    assert ms._system.derived_dims == (velocity,)


def test_error_definition():
    raises(ValueError, lambda: UnitSystem((m, s, c)))


def test_str_repr():
    assert str(UnitSystem((m, s), name="MS")) == "MS"
    assert str(UnitSystem((m, s))) == "UnitSystem((meter, second))"

    assert repr(UnitSystem((m, s))) == "<UnitSystem: (%s, %s)>" % (m, s)


def test_print_unit_base():
    A = Quantity("A")
    A.set_dimension(current)
    A.set_scale_factor(S.One)

    Js = Quantity("Js")
    Js.set_dimension(action)
    Js.set_scale_factor(S.One)

    mksa = UnitSystem((m, kg, s, A), (Js,))
    with warns_deprecated_sympy():
        assert mksa.print_unit_base(Js) == m**2*kg*s**-1


def test_extend():
    ms = UnitSystem((m, s), (c,))
    Js = Quantity("Js")
    Js.set_dimension(action)
    Js.set_scale_factor(1)
    mks = ms.extend((kg,), (Js,))

    res = UnitSystem((m, s, kg), (c, Js))
    assert set(mks._base_units) == set(res._base_units)
    assert set(mks._units) == set(res._units)


def test_dim():
    dimsys = UnitSystem((m, kg, s), (c,))
    assert dimsys.dim == 3


def test_is_consistent():
    assert UnitSystem((m, s)).is_consistent is True
