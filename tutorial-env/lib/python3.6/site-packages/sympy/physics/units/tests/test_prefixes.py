# -*- coding: utf-8 -*-
from sympy import symbols, log, Mul, Symbol, S
from sympy.physics.units import Quantity, Dimension, length
from sympy.physics.units.prefixes import PREFIXES, Prefix, prefix_unit, kilo, \
    kibi

x = Symbol('x')

def test_prefix_operations():
    m = PREFIXES['m']
    k = PREFIXES['k']
    M = PREFIXES['M']

    dodeca = Prefix('dodeca', 'dd', 1, base=12)

    assert m * k == 1
    assert k * k == M
    assert 1 / m == k
    assert k / m == M

    assert dodeca * dodeca == 144
    assert 1 / dodeca == S(1) / 12
    assert k / dodeca == S(1000) / 12
    assert dodeca / dodeca == 1

    m = Quantity("fake_meter")
    m.set_dimension(S.One)
    m.set_scale_factor(S.One)

    assert dodeca * m == 12 * m
    assert dodeca / m == 12 / m

    expr1 = kilo * 3
    assert isinstance(expr1, Mul)
    assert (expr1).args == (3, kilo)

    expr2 = kilo * x
    assert isinstance(expr2, Mul)
    assert (expr2).args == (x, kilo)

    expr3 = kilo / 3
    assert isinstance(expr3, Mul)
    assert (expr3).args == (S(1)/3, kilo)

    expr4 = kilo / x
    assert isinstance(expr4, Mul)
    assert (expr4).args == (1/x, kilo)


def test_prefix_unit():
    m = Quantity("fake_meter", abbrev="m")
    m.set_dimension(length)
    m.set_scale_factor(1)

    pref = {"m": PREFIXES["m"], "c": PREFIXES["c"], "d": PREFIXES["d"]}

    q1 = Quantity("millifake_meter", abbrev="mm")
    q2 = Quantity("centifake_meter", abbrev="cm")
    q3 = Quantity("decifake_meter", abbrev="dm")

    q1.set_dimension(length)
    q1.set_dimension(length)
    q1.set_dimension(length)

    q1.set_scale_factor(PREFIXES["m"])
    q1.set_scale_factor(PREFIXES["c"])
    q1.set_scale_factor(PREFIXES["d"])

    res = [q1, q2, q3]

    prefs = prefix_unit(m, pref)
    assert set(prefs) == set(res)
    assert set(map(lambda x: x.abbrev, prefs)) == set(symbols("mm,cm,dm"))


def test_bases():
    assert kilo.base == 10
    assert kibi.base == 2


def test_repr():
    assert eval(repr(kilo)) == kilo
    assert eval(repr(kibi)) == kibi
