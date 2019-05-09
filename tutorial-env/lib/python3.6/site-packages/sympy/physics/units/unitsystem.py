# -*- coding: utf-8 -*-

"""
Unit system for physical quantities; include definition of constants.
"""

from __future__ import division

from sympy import S
from sympy.core.decorators import deprecated
from sympy.physics.units.quantities import Quantity
from sympy.utilities.exceptions import SymPyDeprecationWarning

from .dimensions import DimensionSystem


class UnitSystem(object):
    """
    UnitSystem represents a coherent set of units.

    A unit system is basically a dimension system with notions of scales. Many
    of the methods are defined in the same way.

    It is much better if all base units have a symbol.
    """

    def __init__(self, base, units=(), name="", descr=""):
        self.name = name
        self.descr = descr

        # construct the associated dimension system
        base_dims = [u.dimension for u in base]
        derived_dims = [u.dimension for u in units if u.dimension not in base_dims]
        self._system = DimensionSystem(base_dims, derived_dims)

        if not self.is_consistent:
            raise ValueError("UnitSystem is not consistent")

        self._units = tuple(set(base) | set(units))

        # create a dict linkin
        # this is possible since we have already verified that the base units
        # form a coherent system
        base_dict = dict((u.dimension, u) for u in base)
        # order the base units in the same order than the dimensions in the
        # associated system, in order to ensure that we get always the same
        self._base_units = tuple(base_dict[d] for d in self._system.base_dims)

    def __str__(self):
        """
        Return the name of the system.

        If it does not exist, then it makes a list of symbols (or names) of
        the base dimensions.
        """

        if self.name != "":
            return self.name
        else:
            return "UnitSystem((%s))" % ", ".join(
                str(d) for d in self._base_units)

    def __repr__(self):
        return '<UnitSystem: %s>' % repr(self._base_units)

    def extend(self, base, units=(), name="", description=""):
        """Extend the current system into a new one.

        Take the base and normal units of the current system to merge
        them to the base and normal units given in argument.
        If not provided, name and description are overridden by empty strings.
        """

        base = self._base_units + tuple(base)
        units = self._units + tuple(units)

        return UnitSystem(base, units, name, description)

    def print_unit_base(self, unit):
        """
        Useless method.

        DO NOT USE, use instead ``convert_to``.

        Give the string expression of a unit in term of the basis.

        Units are displayed by decreasing power.
        """
        SymPyDeprecationWarning(
            deprecated_since_version="1.2",
            issue=13336,
            feature="print_unit_base",
            useinstead="convert_to",
        ).warn()
        from sympy.physics.units import convert_to
        return convert_to(unit, self._base_units)

    @property
    def dim(self):
        """
        Give the dimension of the system.

        That is return the number of units forming the basis.
        """

        return self._system.dim

    @property
    def is_consistent(self):
        """
        Check if the underlying dimension system is consistent.
        """
        # test is performed in DimensionSystem
        return self._system.is_consistent
