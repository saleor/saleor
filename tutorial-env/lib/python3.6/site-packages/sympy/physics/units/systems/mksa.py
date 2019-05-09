# -*- coding: utf-8 -*-

"""
MKS unit system.

MKS stands for "meter, kilogram, second, ampere".
"""

from __future__ import division

from sympy.physics.units.definitions import Z0, A, C, F, H, S, T, V, Wb, ohm
from sympy.physics.units.dimensions import (
    capacitance, charge, conductance, current, impedance, inductance,
    magnetic_density, magnetic_flux, voltage, dimsys_MKSA)
from sympy.physics.units.prefixes import PREFIXES, prefix_unit
from sympy.physics.units.systems.mks import MKS, _mks_dim

dims = (voltage, impedance, conductance, capacitance, inductance, charge,
        magnetic_density, magnetic_flux)

# dimension system
_mksa_dim = dimsys_MKSA


units = [A, V, ohm, S, F, H, C, T, Wb]
all_units = []
for u in units:
    all_units.extend(prefix_unit(u, PREFIXES))

all_units.extend([Z0])

MKSA = MKS.extend(base=(A,), units=all_units, name='MKSA')
