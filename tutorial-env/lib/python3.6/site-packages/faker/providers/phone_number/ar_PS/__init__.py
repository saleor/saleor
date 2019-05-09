from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    # Source:
    # https://en.wikipedia.org/wiki/Telephone_numbers_in_the_State_of_Palestine

    cellphone_formats = (
        '{{country_code}} {{provider_code}} ### ####',
        '{{country_code}}{{provider_code}}#######',
        '0{{provider_code}} ### ####',
        '0{{provider_code}}#######',
    )

    telephone_formats = (
        '{{country_code}} 4 24# ####',
        '{{country_code}}424#####',
        '04 24# ####',
        '0424#####',

        '{{country_code}} 9 25# ####',
        '{{country_code}}925#####',
        '09 25# ####',
        '0925#####',

        '{{country_code}} 4 26# ####',
        '{{country_code}}426#####',
        '04 26# ####',
        '0426#####',

        '{{country_code}} 4 23# ####',
        '{{country_code}}423#####',
        '04 23# ####',
        '0423#####',

        '{{country_code}} 4 29# ####',
        '{{country_code}}429#####',
        '04 29# ####',
        '0429#####',

        '{{country_code}} 2 29# ####',
        '{{country_code}}229#####',
        '02 29# ####',
        '0229#####',

        '{{country_code}} 2 23# ####',
        '{{country_code}}223#####',
        '02 23# ####',
        '0223#####',

        '{{country_code}} 2 22# ####',
        '{{country_code}}222#####',
        '02 22# ####',
        '0222#####',

        '{{country_code}} 2 27# ####',
        '{{country_code}}227#####',
        '02 27# ####',
        '0227#####',

        '{{country_code}} 8 20# ####',
        '{{country_code}}820#####',
        '08 20# ####',
        '0820#####',

        '{{country_code}} 8 21# ####',
        '{{country_code}}821#####',
        '08 21# ####',
        '0821#####',

        '{{country_code}} 8 24# ####',
        '{{country_code}}824#####',
        '08 24# ####',
        '0824#####',

        '{{country_code}} 8 25# ####',
        '{{country_code}}825#####',
        '08 25# ####',
        '0825#####',

        '{{country_code}} 8 26# ####',
        '{{country_code}}826#####',
        '08 26# ####',
        '0826#####',

        '{{country_code}} 8 28# ####',
        '{{country_code}}828#####',
        '08 28# ####',
        '0828#####',

    )

    toll_foramts = (
        '1 700 ### ###',
        '1-700-###-###',
        '1 800 ### ###',
        '1-800-###-###',
    )

    services_phones_formats = (
        '100',
        '101',
        '102',
    )

    formats = cellphone_formats + \
        telephone_formats + \
        services_phones_formats + \
        toll_foramts

    def provider_code(self):
        return self.random_element([
            '59',
            '56',
        ])

    def country_code(self):
        return self.random_element([
            '00972',
            '+972',
            '00970',
            '+970',
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

    def toll_number(self):
        pattern = self.random_element(self.toll_foramts)
        return self.numerify(self.generator.parse(pattern))

    def phone_number(self):
        pattern = self.random_element(self.formats)
        return self.numerify(self.generator.parse(pattern))
