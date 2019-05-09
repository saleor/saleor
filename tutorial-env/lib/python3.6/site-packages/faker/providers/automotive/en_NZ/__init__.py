# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    # See https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_New_Zealand
    license_formats = (
        # Old plates
        '??%##',
        '??%###',
        '??%###',
        # Three letters since 2002
        'A??%##',
        'B??%##',
        'C??%##',
        'D??%##',
        'E??%##',
        'F??%##',
        'G??%##',
        'H??%##',
        'J??%##',
        'K??%##',
        'L??%##',
        'M??%##',
        # After 2018
        'N??%##',
    )
