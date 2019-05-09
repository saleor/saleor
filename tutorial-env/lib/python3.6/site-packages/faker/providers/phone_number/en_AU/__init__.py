from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        # Local calls
        '#### ####',
        '####-####',
        '####.####',  # domain registrars apparently use this
        '########',
        # National dialing
        '0{{area_code}} #### ####',
        '0{{area_code}}-####-####',
        '0{{area_code}}.####.####',
        '0{{area_code}}########',
        # Optional parenthesis
        '(0{{area_code}}) #### ####',
        '(0{{area_code}})-####-####',
        '(0{{area_code}}).####.####',
        '(0{{area_code}})########',
        # International drops the 0
        '+61 {{area_code}} #### ####',
        '+61-{{area_code}}-####-####',
        '+61.{{area_code}}.####.####',
        '+61{{area_code}}########',
        # 04 Mobile telephones (Australia-wide) mostly commonly written 4 - 3 -
        # 3 instead of 2 - 4 - 4
        '04## ### ###',
        '04##-###-###',
        '04##.###.###',
        '+61 4## ### ###',
        '+61-4##-###-###',
        '+61.4##.###.###',
    )

    def area_code(self):
        return self.numerify(self.random_element(
            ['2',
             '3',
             '7',
             '8']))

    def phone_number(self):
        pattern = self.random_element(self.formats)
        return self.numerify(self.generator.parse(pattern))
