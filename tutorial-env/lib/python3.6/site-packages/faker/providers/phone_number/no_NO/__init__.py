from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '+47########',
        '+47 ## ## ## ##',
        '## ## ## ##',
        '## ## ## ##',
        '########',
        '########',
        '9## ## ###',
        '4## ## ###',
        '9#######',
        '4#######',
    )
