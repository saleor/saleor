# Copyright (c) 2007, Robert Coup <robert.coup@onetrackmind.co.nz>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#   3. Neither the name of Distance nor the names of its contributors may be used
#      to endorse or promote products derived from this software without
#      specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from decimal import Decimal

import six
import sympy
from sympy.solvers import solve_linear

from measurement.utils import total_ordering


NUMERIC_TYPES = six.integer_types + (float, Decimal)


def pretty_name(obj):
    return obj.__name__ if obj.__class__ == type else obj.__class__.__name__


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


@total_ordering
class MeasureBase(object):
    STANDARD_UNIT = None
    ALIAS = {}
    UNITS = {}
    SI_UNITS = []
    SI_PREFIXES = {
        'yocto': 'y',
        'zepto': 'z',
        'atto': 'a',
        'femto': 'f',
        'pico': 'p',
        'nano': 'n',
        'micro': 'u',
        'milli': 'm',
        'centi': 'c',
        'deci': 'd',
        'deca': 'da',
        'hecto': 'h',
        'kilo': 'k',
        'mega': 'M',
        'giga': 'G',
        'tera': 'T',
        'peta': 'P',
        'exa': 'E',
        'zeta': 'Z',
        'yotta': 'Y',
    }
    SI_MAGNITUDES = {
        'yocto': 1e-24,
        'zepto': 1e-21,
        'atto': 1e-18,
        'femto': 1e-15,
        'pico': 1e-12,
        'nano': 1e-9,
        'micro': 1e-6,
        'milli': 1e-3,
        'centi': 1e-2,
        'deci': 1e-1,
        'deca': 1e1,
        'hecto': 1e2,
        'kilo': 1e3,
        'mega': 1e6,
        'giga': 1e9,
        'tera': 1e12,
        'peta': 1e15,
        'exa': 1e18,
        'zeta': 1e21,
        'yotta': 1e24,
    }

    def __init__(self, default_unit=None, **kwargs):
        value, default = self.default_units(kwargs)
        self._default_unit = default
        setattr(self, self.STANDARD_UNIT, value)
        if default_unit and isinstance(default_unit, six.string_types):
            self._default_unit = default_unit

    @classmethod
    def get_units(cls):
        units = cls.UNITS.copy()
        for unit in cls.SI_UNITS:
            unit_value = units[unit]
            for magnitude, value in cls.SI_MAGNITUDES.items():
                unit_abbreviation = cls.SI_PREFIXES[magnitude] + unit
                units[unit_abbreviation] = unit_value * value
        return units

    @classmethod
    def get_si_aliases(cls):
        si_aliases = {}
        for alias, abbrev in cls.ALIAS.items():
            if abbrev in cls.SI_UNITS:
                si_aliases[alias] = abbrev
        return si_aliases

    @classmethod
    def get_aliases(cls):
        aliases = cls.ALIAS.copy()
        si_aliases = cls.get_si_aliases()
        for si_alias, unit_abbrev in si_aliases.items():
            for magnitude, _ in cls.SI_MAGNITUDES.items():
                magnitude_alias = magnitude + si_alias
                prefix = cls.SI_PREFIXES[magnitude]
                aliases[magnitude_alias] = prefix + unit_abbrev
        return aliases

    @classmethod
    def get_lowercase_aliases(self):
        lowercased = {}
        for alias, value in self.get_aliases().items():
            lowercased[alias.lower()] = value
        return lowercased

    @property
    def standard(self):
        return getattr(self, self.STANDARD_UNIT)

    @standard.setter
    def standard(self, value):
        setattr(self, self.STANDARD_UNIT, value)

    @property
    def value(self):
        return getattr(self, self._default_unit)

    @value.setter
    def value(self, value):
        units = self.get_units()
        u1 = units[self.STANDARD_UNIT]
        u2 = units[self.unit]

        self.standard = value * (u2 / u1)

    @property
    def unit(self):
        return self._default_unit

    @unit.setter
    def unit(self, value):
        aliases = self.get_aliases()
        laliases = self.get_lowercase_aliases()
        units = self.get_units()
        unit = None
        if value in self.UNITS:
            unit = value
        elif value in aliases:
            unit = aliases[value]
        elif value.lower() in units:
            unit = value.lower()
        elif value.lower() in laliases:
            unit = laliases[value.lower]
        if not unit:
            raise ValueError('Invalid unit %s' % value)
        self._default_unit = unit

    def __getattr__(self, name):
        units = self.get_units()
        if name in units:
            return self._convert_value_to(
                units[name],
                self.standard,
            )
        else:
            raise AttributeError('Unknown unit type: %s' % name)

    def __repr__(self):
        return '%s(%s=%s)' % (
            pretty_name(self),
            self.unit,
            getattr(self, self._default_unit)
        )

    def __str__(self):
        return '%s %s' % (
            getattr(self, self._default_unit),
            self.unit
        )

    # **** Comparison methods ****

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.standard == other.standard
        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.standard < other.standard
        else:
            return NotImplemented

    # **** Operators methods ****

    def __add__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard + other.standard)}
            )
        else:
            raise TypeError(
                '%(class)s must be added with %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __iadd__(self, other):
        if isinstance(other, self.__class__):
            self.standard += other.standard
            return self
        else:
            raise TypeError(
                '%(class)s must be added with %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard - other.standard)}
            )
        else:
            raise TypeError(
                '%(class)s must be subtracted from %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __isub__(self, other):
        if isinstance(other, self.__class__):
            self.standard -= other.standard
            return self
        else:
            raise TypeError(
                '%(class)s must be subtracted from %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __mul__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard * other)}
            )
        else:
            raise TypeError(
                '%(class)s must be multiplied with number' % {
                    "class": pretty_name(self)
                }
            )

    def __imul__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            self.standard *= float(other)
            return self
        else:
            raise TypeError(
                '%(class)s must be multiplied with number' % {
                    "class": pretty_name(self)
                }
            )

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        if isinstance(other, self.__class__):
            return self.standard / other.standard
        if isinstance(other, NUMERIC_TYPES):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard / other)}
            )
        else:
            raise TypeError(
                '%(class)s must be divided with number or %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __div__(self, other):   # Python 2 compatibility
        return type(self).__truediv__(self, other)

    def __itruediv__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            self.standard /= float(other)
            return self
        else:
            raise TypeError(
                '%(class)s must be divided with number' % {
                    "class": pretty_name(self)
                }
            )

    def __idiv__(self, other):  # Python 2 compatibility
        return type(self).__itruediv__(self, other)

    def __bool__(self):
        return bool(self.standard)

    def __nonzero__(self):      # Python 2 compatibility
        return type(self).__bool__(self)

    def _convert_value_to(self, unit, value):
        if not isinstance(value, float):
            value = float(value)

        if isinstance(unit, sympy.Expr):
            result = unit.evalf(
                subs={
                    self.SU: value
                }
            )
            return float(result)
        return value / unit

    def _convert_value_from(self, unit, value):
        if not isinstance(value, float):
            value = float(value)

        if isinstance(unit, sympy.Expr):
            _, result = solve_linear(unit, value)
            return result
        return unit * value

    def default_units(self, kwargs):
        """
        Return the unit value and the default units specified
        from the given keyword arguments dictionary.
        """
        aliases = self.get_aliases()
        laliases = self.get_lowercase_aliases()
        units = self.get_units()
        val = 0.0
        default_unit = self.STANDARD_UNIT
        for unit, value in six.iteritems(kwargs):
            if unit in units:
                val = self._convert_value_from(units[unit], value)
                default_unit = unit
            elif unit in aliases:
                u = aliases[unit]
                val = self._convert_value_from(units[u], value)
                default_unit = u
            else:
                lower = unit.lower()
                if lower in units:
                    val = self._convert_value_from(units[lower], value)
                    default_unit = lower
                elif lower in laliases:
                    u = laliases[lower]
                    val = self._convert_value_from(units[u], value)
                    default_unit = u
                else:
                    raise AttributeError('Unknown unit type: %s' % unit)
        return val, default_unit

    @classmethod
    def unit_attname(cls, unit_str):
        """
        Retrieves the unit attribute name for the given unit string.
        For example, if the given unit string is 'metre', 'm' would be returned.
        An exception is raised if an attribute cannot be found.
        """
        laliases = cls.get_lowercase_aliases()
        units = cls.get_units()
        lower = unit_str.lower()
        if unit_str in units:
            return unit_str
        elif lower in units:
            return lower
        elif lower in laliases:
            return laliases[lower]
        else:
            raise Exception(
                'Could not find a unit keyword associated with "%s"' % (
                    unit_str,
                )
            )


@total_ordering
class BidimensionalMeasure(object):
    PRIMARY_DIMENSION = None
    REFERENCE_DIMENSION = None

    ALIAS = {
    }

    def __init__(self, **kwargs):
        if 'primary' in kwargs and 'reference' in kwargs:
            self.primary = kwargs['primary']
            self.reference = kwargs['reference']
        else:
            items = list(six.iteritems(kwargs))
            if len(items) > 1:
                raise ValueError('Only one keyword argument is expected')
            measure_string, value = items[0]

            self.primary, self.reference = self._get_measures(
                measure_string,
                value
            )

    def _get_unit_parts(self, measure_string):
        if measure_string in self.ALIAS:
            measure_string = self.ALIAS[measure_string]
        try:
            primary_unit, reference_unit = measure_string.split('__')
        except ValueError:
            raise AttributeError(
                (
                    'Unit not found: \'%s\';'
                    'Units should be expressed using double-underscore '
                    'separated units; for example: meters-per-second would be '
                    'expressed with either \'meter__second\' or \'m__sec\'.'
                ) % (
                    measure_string
                )
            )
        return primary_unit, reference_unit

    def _get_measures(self, measure_string, value):
        primary_unit, reference_unit = self._get_unit_parts(measure_string)
        primary = self.PRIMARY_DIMENSION(**{primary_unit: value})
        reference = self.REFERENCE_DIMENSION(**{reference_unit: 1})

        return primary, reference

    @property
    def standard(self):
        return self.primary.standard / self.reference.standard

    @classproperty
    @classmethod
    def STANDARD_UNIT(self):
        return '%s__%s' % (
            self.PRIMARY_DIMENSION.STANDARD_UNIT,
            self.REFERENCE_DIMENSION.STANDARD_UNIT,
        )

    @property
    def value(self):
        return self.primary.value

    @property
    def unit(self):
        return '%s__%s' % (
            self.primary.unit,
            self.reference.unit,
        )

    @unit.setter
    def unit(self, value):
        primary, reference = value.split('__')
        reference_units = self.REFERENCE_DIMENSION.get_units()
        if reference != self.reference.unit:
            reference_chg = (
                reference_units[self.reference.unit]/reference_units[reference]
            )
            self.primary.standard = self.primary.standard / reference_chg
        self.primary.unit = primary
        self.reference.unit = reference

    def _normalize(self, other):
        std_value = getattr(other, self.unit)

        primary = self.PRIMARY_DIMENSION(**{self.primary.unit: std_value})
        reference = self.REFERENCE_DIMENSION(**{self.reference.unit: 1})

        return self.__class__(primary=primary, reference=reference)

    def __getattr__(self, measure_string):
        primary_units = self.PRIMARY_DIMENSION.get_units()
        reference_units = self.REFERENCE_DIMENSION.get_units()

        p1, r1 = self.primary.unit, self.reference.unit
        p2, r2 = self._get_unit_parts(measure_string)

        primary_chg = primary_units[p2]/primary_units[p1]
        reference_chg = reference_units[r2]/reference_units[r1]

        return self.primary.value / primary_chg * reference_chg

    def __repr__(self):
        return '%s(%s__%s=%s)' % (
            pretty_name(self),
            self.primary.unit,
            self.reference.unit,
            self.primary.value,
        )

    def __str__(self):
        return '%s %s/%s' % (
            self.primary.value,
            self.primary.unit,
            self.reference.unit,
        )

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.standard == other.standard
        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.standard < other.standard
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, self.__class__):
            normalized = self._normalize(other)
            total_value = normalized.primary.value + self.primary.value
            return self.__class__(
                primary=self.PRIMARY_DIMENSION(
                    **{self.primary.unit: total_value}
                ),
                reference=self.REFERENCE_DIMENSION(
                    **{self.reference.unit: 1}
                )
            )
        else:
            raise TypeError(
                '%(class)s must be added with %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __iadd__(self, other):
        if isinstance(other, self.__class__):
            normalized = self._normalize(other)
            self.primary.standard += normalized.primary.standard
            return self
        else:
            raise TypeError(
                '%(class)s must be added with %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            normalized = self._normalize(other)
            total_value = self.primary.value - normalized.primary.value
            return self.__class__(
                primary=self.PRIMARY_DIMENSION(
                    **{self.primary.unit: total_value}
                ),
                reference=self.REFERENCE_DIMENSION(
                    **{self.reference.unit: 1}
                )
            )
        else:
            raise TypeError(
                '%(class)s must be added with %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __isub__(self, other):
        if isinstance(other, self.__class__):
            normalized = self._normalize(other)
            self.primary.standard -= normalized.primary.standard
            return self
        else:
            raise TypeError(
                '%(class)s must be added with %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __mul__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            total_value = self.primary.value * other
            return self.__class__(
                primary=self.PRIMARY_DIMENSION(
                    **{self.primary.unit: total_value}
                ),
                reference=self.REFERENCE_DIMENSION(
                    **{self.reference.unit: 1}
                )
            )
        else:
            raise TypeError(
                '%(class)s must be multiplied with number' % {
                    "class": pretty_name(self)
                }
            )

    def __rmul__(self, other):
        return self * other

    def __imul__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            self.primary.standard *= float(other)
            return self
        else:
            raise TypeError(
                '%(class)s must be multiplied with number' % {
                    "class": pretty_name(self)
                }
            )

    def __truediv__(self, other):
        if isinstance(other, self.__class__):
            normalized = self._normalize(other)
            return self.primary.standard / normalized.primary.standard
        if isinstance(other, NUMERIC_TYPES):
            total_value = self.primary.value / other
            return self.__class__(
                primary=self.PRIMARY_DIMENSION(
                    **{self.primary.unit: total_value}
                ),
                reference=self.REFERENCE_DIMENSION(
                    **{self.reference.unit: 1}
                )
            )
        else:
            raise TypeError(
                '%(class)s must be divided with number or %(class)s' % {
                    "class": pretty_name(self)
                }
            )

    def __itruediv__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            self.primary.standard /= float(other)
            return self
        else:
            raise TypeError(
                '%(class)s must be divided with number' % {
                    "class": pretty_name(self)
                }
            )

    def __div__(self, other):   # Python 2 compatibility
        return type(self).__truediv__(self, other)

    def __idiv__(self, other):  # Python 2 compatibility
        return type(self).__itruediv__(self, other)

    def __bool__(self):
        return bool(self.primary.standard)

    def __nonzero__(self):  # Python 2 compatibility
        return type(self).__bool__(self)
