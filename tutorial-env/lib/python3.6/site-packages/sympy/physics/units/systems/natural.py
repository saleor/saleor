# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

"""
Naturalunit system.

The natural system comes from "setting c = 1, hbar = 1". From the computer
point of view it means that we use velocity and action instead of length and
time. Moreover instead of mass we use energy.
"""

from __future__ import division

from sympy.physics.units.definitions import c, eV, hbar
from sympy.physics.units.dimensions import (
    DimensionSystem, action, energy, force, frequency, length, mass, momentum,
    power, time, velocity)
from sympy.physics.units.prefixes import PREFIXES, prefix_unit
from sympy.physics.units.unitsystem import UnitSystem


# dimension system
_natural_dim = DimensionSystem(
    base_dims=(action, energy, velocity),
    derived_dims=(length, mass, time, momentum, force, power, frequency)
)

units = prefix_unit(eV, PREFIXES)

# unit system
natural = UnitSystem(base=(hbar, eV, c), units=units, name="Natural system")
