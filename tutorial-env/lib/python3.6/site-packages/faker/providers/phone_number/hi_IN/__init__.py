from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '+91 ##########',
        '+91 ### #######',
        '0##-########',
        '0##########',
        '0#### ######',
    )
