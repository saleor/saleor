# -*- coding: utf-8 -*-

from sympy import (Abs, Add, Basic, Function, Number, Rational, S, Symbol,
    diff, exp, integrate, log, sin, sqrt, symbols)
from sympy.physics.units import (amount_of_substance, convert_to, find_unit,
    volume)
from sympy.physics.units.definitions import (amu, au, centimeter, coulomb,
    day, energy, foot, grams, hour, inch, kg, km, m, meter, mile, millimeter,
    minute, pressure, quart, s, second, speed_of_light, temperature, bit,
    byte, kibibyte, mebibyte, gibibyte, tebibyte, pebibyte, exbibyte,
    kilogram, gravitational_constant)

from sympy.physics.units.dimensions import Dimension, charge, length, time, dimsys_default
from sympy.physics.units.prefixes import PREFIXES, kilo
from sympy.physics.units.quantities import Quantity
from sympy.utilities.pytest import XFAIL, raises, warns_deprecated_sympy

k = PREFIXES["k"]


def test_str_repr():
    assert str(kg) == "kilogram"

def test_eq():
    # simple test
    assert 10*m == 10*m
    assert 10*m != 10*s


def test_convert_to():
    q = Quantity("q1")
    q.set_dimension(length)
    q.set_scale_factor(S(5000))

    assert q.convert_to(m) == 5000*m

    assert speed_of_light.convert_to(m / s) == 299792458 * m / s
    # TODO: eventually support this kind of conversion:
    # assert (2*speed_of_light).convert_to(m / s) == 2 * 299792458 * m / s
    assert day.convert_to(s) == 86400*s

    # Wrong dimension to convert:
    assert q.convert_to(s) == q
    assert speed_of_light.convert_to(m) == speed_of_light


def test_Quantity_definition():
    q = Quantity("s10", abbrev="sabbr")
    q.set_dimension(time)
    q.set_scale_factor(10)
    u  =  Quantity("u", abbrev="dam")
    u.set_dimension(length)
    u.set_scale_factor(10)
    km =  Quantity("km")
    km.set_dimension(length)
    km.set_scale_factor(kilo)
    v =  Quantity("u")
    v.set_dimension(length)
    v.set_scale_factor(5*kilo)

    assert q.scale_factor == 10
    assert q.dimension == time
    assert q.abbrev == Symbol("sabbr")

    assert u.dimension == length
    assert u.scale_factor == 10
    assert u.abbrev == Symbol("dam")

    assert km.scale_factor == 1000
    assert km.func(*km.args) == km
    assert km.func(*km.args).args == km.args

    assert v.dimension == length
    assert v.scale_factor == 5000

    with warns_deprecated_sympy():
        Quantity('invalid', 'dimension', 1)
    with warns_deprecated_sympy():
        Quantity('mismatch', dimension=length, scale_factor=kg)


def test_abbrev():
    u = Quantity("u")
    u.set_dimension(length)
    u.set_scale_factor(S.One)

    assert u.name == Symbol("u")
    assert u.abbrev == Symbol("u")

    u = Quantity("u", abbrev="om")
    u.set_dimension(length)
    u.set_scale_factor(S(2))

    assert u.name == Symbol("u")
    assert u.abbrev == Symbol("om")
    assert u.scale_factor == 2
    assert isinstance(u.scale_factor, Number)

    u = Quantity("u", abbrev="ikm")
    u.set_dimension(length)
    u.set_scale_factor(3*kilo)

    assert u.abbrev == Symbol("ikm")
    assert u.scale_factor == 3000


def test_print():
    u = Quantity("unitname", abbrev="dam")
    assert repr(u) == "unitname"
    assert str(u) == "unitname"


def test_Quantity_eq():
    u = Quantity("u", abbrev="dam")
    v = Quantity("v1")
    assert u != v
    v = Quantity("v2", abbrev="ds")
    assert u != v
    v = Quantity("v3", abbrev="dm")
    assert u != v


def test_add_sub():
    u = Quantity("u")
    v = Quantity("v")
    w = Quantity("w")

    u.set_dimension(length)
    v.set_dimension(length)
    w.set_dimension(time)

    u.set_scale_factor(S(10))
    v.set_scale_factor(S(5))
    w.set_scale_factor(S(2))

    assert isinstance(u + v, Add)
    assert (u + v.convert_to(u)) == (1 + S.Half)*u
    # TODO: eventually add this:
    # assert (u + v).convert_to(u) == (1 + S.Half)*u
    assert isinstance(u - v, Add)
    assert (u - v.convert_to(u)) == S.Half*u
    # TODO: eventually add this:
    # assert (u - v).convert_to(u) == S.Half*u


def test_quantity_abs():
    v_w1 = Quantity('v_w1')
    v_w2 = Quantity('v_w2')
    v_w3 = Quantity('v_w3')

    v_w1.set_dimension(length/time)
    v_w2.set_dimension(length/time)
    v_w3.set_dimension(length/time)

    v_w1.set_scale_factor(meter/second)
    v_w2.set_scale_factor(meter/second)
    v_w3.set_scale_factor(meter/second)

    expr = v_w3 - Abs(v_w1 - v_w2)

    Dq = Dimension(Quantity.get_dimensional_expr(expr))
    assert dimsys_default.get_dimensional_dependencies(Dq) == {
        'length': 1,
        'time': -1,
    }
    assert meter == sqrt(meter**2)


def test_check_unit_consistency():
    u = Quantity("u")
    v = Quantity("v")
    w = Quantity("w")

    u.set_dimension(length)
    v.set_dimension(length)
    w.set_dimension(time)

    u.set_scale_factor(S(10))
    v.set_scale_factor(S(5))
    w.set_scale_factor(S(2))

    def check_unit_consistency(expr):
        Quantity._collect_factor_and_dimension(expr)

    raises(ValueError, lambda: check_unit_consistency(u + w))
    raises(ValueError, lambda: check_unit_consistency(u - w))
    raises(ValueError, lambda: check_unit_consistency(u + 1))
    raises(ValueError, lambda: check_unit_consistency(u - 1))


def test_mul_div():
    u = Quantity("u")
    v = Quantity("v")
    t = Quantity("t")
    ut = Quantity("ut")
    v2 = Quantity("v")

    u.set_dimension(length)
    v.set_dimension(length)
    t.set_dimension(time)
    ut.set_dimension(length*time)
    v2.set_dimension(length/time)

    u.set_scale_factor(S(10))
    v.set_scale_factor(S(5))
    t.set_scale_factor(S(2))
    ut.set_scale_factor(S(20))
    v2.set_scale_factor(S(5))

    assert 1 / u == u**(-1)
    assert u / 1 == u

    v1 = u / t
    v2 = v

    # Pow only supports structural equality:
    assert v1 != v2
    assert v1 == v2.convert_to(v1)

    # TODO: decide whether to allow such expression in the future
    # (requires somehow manipulating the core).
    # assert u / Quantity('l2', dimension=length, scale_factor=2) == 5

    assert u * 1 == u

    ut1 = u * t
    ut2 = ut

    # Mul only supports structural equality:
    assert ut1 != ut2
    assert ut1 == ut2.convert_to(ut1)

    # Mul only supports structural equality:
    lp1 = Quantity("lp1")
    lp1.set_dimension(length**-1)
    lp1.set_scale_factor(S(2))
    assert u * lp1 != 20

    assert u**0 == 1
    assert u**1 == u

    # TODO: Pow only support structural equality:
    u2 = Quantity("u2")
    u3 = Quantity("u3")
    u2.set_dimension(length**2)
    u3.set_dimension(length**-1)
    u2.set_scale_factor(S(100))
    u3.set_scale_factor(S(1)/10)

    assert u ** 2 != u2
    assert u ** -1 != u3

    assert u ** 2 == u2.convert_to(u)
    assert u ** -1 == u3.convert_to(u)


def test_units():
    assert convert_to((5*m/s * day) / km, 1) == 432
    assert convert_to(foot / meter, meter) == Rational(3048, 10000)
    # amu is a pure mass so mass/mass gives a number, not an amount (mol)
    # TODO: need better simplification routine:
    assert str(convert_to(grams/amu, grams).n(2)) == '6.0e+23'

    # Light from the sun needs about 8.3 minutes to reach earth
    t = (1*au / speed_of_light) / minute
    # TODO: need a better way to simplify expressions containing units:
    t = convert_to(convert_to(t, meter / minute), meter)
    assert t == S(49865956897)/5995849160

    # TODO: fix this, it should give `m` without `Abs`
    assert sqrt(m**2) == Abs(m)
    assert (sqrt(m))**2 == m

    t = Symbol('t')
    assert integrate(t*m/s, (t, 1*s, 5*s)) == 12*m*s
    assert (t * m/s).integrate((t, 1*s, 5*s)) == 12*m*s


def test_issue_quart():
    assert convert_to(4 * quart / inch ** 3, meter) == 231
    assert convert_to(4 * quart / inch ** 3, millimeter) == 231


def test_issue_5565():
    assert (m < s).is_Relational


def test_find_unit():
    assert find_unit('coulomb') == ['coulomb', 'coulombs', 'coulomb_constant']
    assert find_unit(coulomb) == ['C', 'coulomb', 'coulombs', 'planck_charge']
    assert find_unit(charge) == ['C', 'coulomb', 'coulombs', 'planck_charge']
    assert find_unit(inch) == [
        'm', 'au', 'cm', 'dm', 'ft', 'km', 'ly', 'mi', 'mm', 'nm', 'pm', 'um',
        'yd', 'nmi', 'feet', 'foot', 'inch', 'mile', 'yard', 'meter', 'miles',
        'yards', 'inches', 'meters', 'micron', 'microns', 'decimeter',
        'kilometer', 'lightyear', 'nanometer', 'picometer', 'centimeter',
        'decimeters', 'kilometers', 'lightyears', 'micrometer', 'millimeter',
        'nanometers', 'picometers', 'centimeters', 'micrometers',
        'millimeters', 'nautical_mile', 'planck_length', 'nautical_miles', 'astronomical_unit',
        'astronomical_units']
    assert find_unit(inch**-1) == ['D', 'dioptre', 'optical_power']
    assert find_unit(length**-1) == ['D', 'dioptre', 'optical_power']
    assert find_unit(inch ** 3) == [
        'l', 'cl', 'dl', 'ml', 'liter', 'quart', 'liters', 'quarts',
        'deciliter', 'centiliter', 'deciliters', 'milliliter',
        'centiliters', 'milliliters', 'planck_volume']
    assert find_unit('voltage') == ['V', 'v', 'volt', 'volts', 'planck_voltage']


def test_Quantity_derivative():
    x = symbols("x")
    assert diff(x*meter, x) == meter
    assert diff(x**3*meter**2, x) == 3*x**2*meter**2
    assert diff(meter, meter) == 1
    assert diff(meter**2, meter) == 2*meter


def test_quantity_postprocessing():
    q1 = Quantity('q1')
    q2 = Quantity('q2')

    q1.set_dimension(length*pressure**2*temperature/time)
    q2.set_dimension(energy*pressure*temperature/(length**2*time))

    assert q1 + q2
    q = q1 + q2
    Dq = Dimension(Quantity.get_dimensional_expr(q))
    assert dimsys_default.get_dimensional_dependencies(Dq) == {
        'length': -1,
        'mass': 2,
        'temperature': 1,
        'time': -5,
    }


def test_factor_and_dimension():
    assert (3000, Dimension(1)) == Quantity._collect_factor_and_dimension(3000)
    assert (1001, length) == Quantity._collect_factor_and_dimension(meter + km)
    assert (2, length/time) == Quantity._collect_factor_and_dimension(
        meter/second + 36*km/(10*hour))

    x, y = symbols('x y')
    assert (x + y/100, length) == Quantity._collect_factor_and_dimension(
        x*m + y*centimeter)

    cH = Quantity('cH')
    cH.set_dimension(amount_of_substance/volume)

    pH = -log(cH)

    assert (1, volume/amount_of_substance) == Quantity._collect_factor_and_dimension(
        exp(pH))

    v_w1 = Quantity('v_w1')
    v_w2 = Quantity('v_w2')

    v_w1.set_dimension(length/time)
    v_w2.set_dimension(length/time)
    v_w1.set_scale_factor(S(3)/2*meter/second)
    v_w2.set_scale_factor(2*meter/second)

    expr = Abs(v_w1/2 - v_w2)
    assert (S(5)/4, length/time) == \
        Quantity._collect_factor_and_dimension(expr)

    expr = S(5)/2*second/meter*v_w1 - 3000
    assert (-(2996 + S(1)/4), Dimension(1)) == \
        Quantity._collect_factor_and_dimension(expr)

    expr = v_w1**(v_w2/v_w1)
    assert ((S(3)/2)**(S(4)/3), (length/time)**(S(4)/3)) == \
        Quantity._collect_factor_and_dimension(expr)


@XFAIL
def test_factor_and_dimension_with_Abs():
    with warns_deprecated_sympy():
        v_w1 = Quantity('v_w1', length/time, S(3)/2*meter/second)
    v_w1.set_dimension(length/time)
    v_w1.set_scale_factor(S(3)/2*meter/second)
    expr = v_w1 - Abs(v_w1)
    assert (0, length/time) == Quantity._collect_factor_and_dimension(expr)


def test_dimensional_expr_of_derivative():
    l = Quantity('l')
    t = Quantity('t')
    t1 = Quantity('t1')
    l.set_dimension(length)
    t.set_dimension(time)
    t1.set_dimension(time)
    l.set_scale_factor(36*km)
    t.set_scale_factor(hour)
    t1.set_scale_factor(second)
    x = Symbol('x')
    y = Symbol('y')
    f = Function('f')
    dfdx = f(x, y).diff(x, y)
    dl_dt = dfdx.subs({f(x, y): l, x: t, y: t1})
    assert Quantity.get_dimensional_expr(dl_dt) ==\
        Quantity.get_dimensional_expr(l / t / t1) ==\
        Symbol("length")/Symbol("time")**2
    assert Quantity._collect_factor_and_dimension(dl_dt) ==\
        Quantity._collect_factor_and_dimension(l / t / t1) ==\
        (10, length/time**2)


def test_get_dimensional_expr_with_function():
    v_w1 = Quantity('v_w1')
    v_w2 = Quantity('v_w2')
    v_w1.set_dimension(length/time)
    v_w2.set_dimension(length/time)
    v_w1.set_scale_factor(meter/second)
    v_w2.set_scale_factor(meter/second)

    assert Quantity.get_dimensional_expr(sin(v_w1)) == \
        sin(Quantity.get_dimensional_expr(v_w1))
    assert Quantity.get_dimensional_expr(sin(v_w1/v_w2)) == 1


def test_binary_information():
    assert convert_to(kibibyte, byte) == 1024*byte
    assert convert_to(mebibyte, byte) == 1024**2*byte
    assert convert_to(gibibyte, byte) == 1024**3*byte
    assert convert_to(tebibyte, byte) == 1024**4*byte
    assert convert_to(pebibyte, byte) == 1024**5*byte
    assert convert_to(exbibyte, byte) == 1024**6*byte

    assert kibibyte.convert_to(bit) == 8*1024*bit
    assert byte.convert_to(bit) == 8*bit

    a = 10*kibibyte*hour

    assert convert_to(a, byte) == 10240*byte*hour
    assert convert_to(a, minute) == 600*kibibyte*minute
    assert convert_to(a, [byte, minute]) == 614400*byte*minute


def test_eval_subs():
    energy, mass, force = symbols('energy mass force')
    expr1 = energy/mass
    units = {energy: kilogram*meter**2/second**2, mass: kilogram}
    assert expr1.subs(units) == meter**2/second**2
    expr2 = force/mass
    units = {force:gravitational_constant*kilogram**2/meter**2, mass:kilogram}
    assert expr2.subs(units) == gravitational_constant*kilogram/meter**2


def test_issue_14932():
    assert (log(inch) - log(2)).simplify() == log(inch/2)
    assert (log(inch) - log(foot)).simplify() == -log(12)
    p = symbols('p', positive=True)
    assert (log(inch) - log(p)).simplify() == log(inch/p)


def test_issue_14547():
    # the root issue is that an argument with dimensions should
    # not raise an error when the the `arg - 1` calculation is
    # performed in the assumptions system
    from sympy.physics.units import foot, inch
    from sympy import Eq
    assert log(foot).is_zero is None
    assert log(foot).is_positive is None
    assert log(foot).is_nonnegative is None
    assert log(foot).is_negative is None
    assert log(foot).is_algebraic is None
    assert log(foot).is_rational is None
    # doesn't raise error
    assert Eq(log(foot), log(inch)) is not None  # might be False or unevaluated

    x = Symbol('x')
    e = foot + x
    assert e.is_Add and set(e.args) == {foot, x}
    e = foot + 1
    assert e.is_Add and set(e.args) == {foot, 1}
