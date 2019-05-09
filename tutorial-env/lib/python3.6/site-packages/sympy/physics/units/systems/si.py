# -*- coding: utf-8 -*-

"""
SI unit system.
Based on MKSA, which stands for "meter, kilogram, second, ampere".
Added kelvin, candela and mole.

"""

from __future__ import division

from sympy.physics.units.definitions import (
    K, cd, lux, mol,hertz, newton, pascal, joule, watt, coulomb, volt, farad,
    ohm, siemens, weber, tesla, henry, candela, lux, becquerel, gray, katal)
from sympy.physics.units.dimensions import (
    amount_of_substance, luminous_intensity, temperature, dimsys_SI,
    frequency, force, pressure, energy, power, charge, voltage, capacitance,
    conductance, magnetic_flux, magnetic_density, inductance,
    luminous_intensity)
from sympy.physics.units.prefixes import PREFIXES, prefix_unit
from sympy.physics.units.systems.mksa import MKSA, _mksa_dim

derived_dims = (frequency, force, pressure, energy, power, charge, voltage,
                capacitance, conductance, magnetic_flux,
                magnetic_density, inductance, luminous_intensity)
base_dims = (amount_of_substance, luminous_intensity, temperature)

# dimension system
_si_dim = dimsys_SI


units = [mol, cd, K, lux, hertz, newton, pascal, joule, watt, coulomb, volt,
        farad, ohm, siemens, weber, tesla, henry, candela, lux, becquerel,
        gray, katal]
all_units = []
for u in units:
    all_units.extend(prefix_unit(u, PREFIXES))

all_units.extend([mol, cd, K, lux])

SI = MKSA.extend(base=(mol, cd, K), units=all_units, name='SI')
