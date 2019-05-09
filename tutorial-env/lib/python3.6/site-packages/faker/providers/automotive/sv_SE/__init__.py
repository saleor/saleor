# coding=utf-8


from __future__ import unicode_literals
from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    # Source: https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Sweden
    # New possible format: https://goo.gl/gSjsnV
    license_formats = (
        # Classic format
        '??? ###',
        # New possible format
        '??? ##?',
    )
