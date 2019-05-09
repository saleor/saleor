# coding=utf-8


from __future__ import unicode_literals
from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    # from https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Hungary
    license_formats = (
        '???-###',
    )
