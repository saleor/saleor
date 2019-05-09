from measurement.base import MeasureBase


__all__ = [
    'Voltage'
]


class Voltage(MeasureBase):
    STANDARD_UNIT = 'V'
    UNITS = {
        'V': 1.0
    }
    ALIAS = {
        'volt': 'V'
    }
    SI_UNITS = ['V']
