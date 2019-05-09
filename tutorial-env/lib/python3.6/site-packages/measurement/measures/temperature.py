from sympy import S, Symbol

from measurement.base import MeasureBase


__all__ = [
    'Temperature'
]


class Temperature(MeasureBase):
    SU = Symbol('kelvin')
    STANDARD_UNIT = 'k'
    UNITS = {
        'c': SU - S(273.15),
        'f': (SU - S(273.15)) * S('9/5') + 32,
        'k': 1.0
    }
    ALIAS = {
        'celsius': 'c',
        'fahrenheit': 'f',
        'kelvin': 'k',
    }
