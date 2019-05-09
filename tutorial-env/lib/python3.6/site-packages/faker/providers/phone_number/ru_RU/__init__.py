from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '+7 ### ### ####',
        '+7 ### ### ## ##',
        '+7 (###) ###-##-##',
        '+7 (###) ###-####',
        '+7##########',
        '8 ### ### ####',
        '8 ### ### ## ##',
        '8 (###) ###-##-##',
        '8 (###) ###-####',
        '8##########',
    )
