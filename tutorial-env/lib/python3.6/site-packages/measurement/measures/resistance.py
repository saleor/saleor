# -*- coding: utf-8 -*-
from measurement.base import MeasureBase


__all__ = [
    'Resistance'
]


class Resistance(MeasureBase):
    STANDARD_UNIT = 'ohm'
    UNITS = {
        'ohm': 1.0,
    }
    ALIAS = {
    }
    SI_UNITS = ['ohm']
