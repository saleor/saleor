from measurement.base import MeasureBase


__all__ = [
    'Energy'
]


class Energy(MeasureBase):
    STANDARD_UNIT = 'J'
    UNITS = {
        'c': 4.18400,
        'C': 4184.0,
        'J': 1.0,
        'eV': 1.602177e-19,
        'tonne_tnt': 4184000000,
    }
    ALIAS = {
        'joule': 'J',
        'calorie': 'c',
        'Calorie': 'C',
    }
    SI_UNITS = ['J', 'c', 'eV', 'tonne_tnt']
