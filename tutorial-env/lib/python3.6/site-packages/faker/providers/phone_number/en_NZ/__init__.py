# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        # Local calls
        '%## ####',
        '%##-####',
        '%######',
        # National & Mobile dialing
        '0{{area_code}} %## ####',
        '0{{area_code}} %##-####',
        '0{{area_code}}-%##-####',
        '0{{area_code}} %######',
        # Optional parenthesis
        '(0{{area_code}}) %## ####',
        '(0{{area_code}}) %##-####',
        '(0{{area_code}}) %######',
        # International drops the 0
        '+64 {{area_code}} %## ####',
        '+64 {{area_code}} %##-####',
        '+64 {{area_code}} %######',
        '+64-{{area_code}}-%##-####',
        '+64{{area_code}}%######',
    )

    area_codes = [
        # Mobiles
        '20',
        '21',
        '22',
        '27',
        '29',

        '3',  # South Island
        '4',  # Wellington
        '6',  # Lower North Island
        '7',  # Central North Island
        '9',  # Auckland
    ]

    def area_code(self):
        return self.numerify(self.random_element(self.area_codes))

    def phone_number(self):
        pattern = self.random_element(self.formats)
        return self.numerify(self.generator.parse(pattern))
