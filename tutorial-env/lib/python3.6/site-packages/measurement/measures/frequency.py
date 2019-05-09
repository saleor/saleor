from measurement.base import MeasureBase


__all__ = [
    'Frequency'
]


class Frequency(MeasureBase):
    STANDARD_UNIT = 'Hz'
    UNITS = {
        'Hz': 1.0,
        'rpm': 1.0 / 60,
    }
    ALIAS = {
        'hertz': 'Hz',
    }
    SI_UNITS = ['Hz']
