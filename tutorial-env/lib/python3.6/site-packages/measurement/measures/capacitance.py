# -*- coding: utf-8 -*-
from measurement.base import MeasureBase


__all__ = [
    'Capacitance'
]


class Capacitance(MeasureBase):
    STANDARD_UNIT = 'F'
    UNITS = {
        'F': 1.0,
    }
    ALIAS = {
        'farad': 'F',
    }
    SI_UNITS = ['F']
