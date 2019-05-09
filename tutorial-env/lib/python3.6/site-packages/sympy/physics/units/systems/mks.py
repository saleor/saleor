# -*- coding: utf-8 -*-

"""
MKS unit system.

MKS stands for "meter, kilogram, second".
"""

from __future__ import division

from sympy.physics.units import DimensionSystem, UnitSystem
from sympy.physics.units.definitions import G, Hz, J, N, Pa, W, c, g, kg, m, s
from sympy.physics.units.dimensions import (
    acceleration, action, energy, force, frequency, length, mass, momentum,
    power, pressure, time, velocity, dimsys_MKS)
from sympy.physics.units.prefixes import PREFIXES, prefix_unit

dims = (velocity, acceleration, momentum, force, energy, power, pressure,
        frequency, action)

# dimension system
_mks_dim = dimsys_MKS

units = [m, g, s, J, N, W, Pa, Hz]
all_units = []

# Prefixes of units like g, J, N etc get added using `prefix_unit`
# in the for loop, but the actual units have to be added manually.
all_units.extend([g, J, N, W, Pa, Hz])

for u in units:
    all_units.extend(prefix_unit(u, PREFIXES))
all_units.extend([G, c])

# unit system
MKS = UnitSystem(base=(m, kg, s), units=all_units, name="MKS")
