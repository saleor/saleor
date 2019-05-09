# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '+46 (0)8 ### ### ##',
        '+46 (0)## ## ## ##',
        '+46 (0)### ### ##',
        '08-### ### ##',
        '08-### ## ##',
        '08-## ## ##',
        '0##-### ## ##',
        '0##-## ## ##',
        '0###-## ## ##',
        '0###-### ##',
    )
