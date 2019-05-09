from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    # Source: https://en.wikipedia.org/wiki/Telephone_numbers_in_Jordan

    cellphone_formats = (
        '+9627{{operator_id}}#######',
        '+962 7 {{operator_id}}### ####',
        '07{{operator_id}}#######',
        '07{{operator_id}} ### ####',
    )

    telephone_formats = (
        '+962{{area_code}}#######',
        '+962 {{area_code}} ### ####',
        '0{{area_code}}#######',
        '0{{area_code}} ### ####',
    )

    services_phones_formats = (
        '9##',
        '12##',
        '13##',
        '14##',
    )

    formats = cellphone_formats + \
        telephone_formats + \
        services_phones_formats

    def operator_id(self):
        return self.random_element([
            '4',
            '7',
            '8',
            '9',
        ])

    def area_code(self):
        return self.random_element([
            '2',
            '3',
            '5',
            '6',
            '7',
        ])

    def cellphone_number(self):
        pattern = self.random_element(self.cellphone_formats)
        return self.numerify(self.generator.parse(pattern))

    def telephone_number(self):
        pattern = self.random_element(self.telephone_formats)
        return self.numerify(self.generator.parse(pattern))

    def service_phone_number(self):
        pattern = self.random_element(self.services_phones_formats)
        return self.numerify(self.generator.parse(pattern))

    def phone_number(self):
        pattern = self.random_element(self.formats)
        return self.numerify(self.generator.parse(pattern))
