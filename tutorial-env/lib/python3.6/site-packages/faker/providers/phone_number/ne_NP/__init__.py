from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '+977 ##########',
        '+977 ### #######',
        '984#######',
        '985#######',
        '980#######',
    )
