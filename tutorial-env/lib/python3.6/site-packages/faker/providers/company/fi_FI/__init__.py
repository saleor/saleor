from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{last_name}} {{last_name}} {{company_suffix}}',
        '{{last_name}} {{last_name}} {{company_suffix}}',
        '{{last_name}}',
    )

    company_suffixes = (
        'As Oy', 'Tmi', 'Oy', 'Oyj', 'Ky', 'Osk', 'ry',
    )

    def company_business_id(self):
        """
        Returns Finnish company Business Identity Code (y-tunnus).
        Format is 8 digits - e.g. FI99999999,[8] last digit is a check
        digit utilizing MOD 11-2. The first digit is zero for some old
        organizations. This function provides current codes starting with
        non-zero.
        """
        def calculate_checksum(number):
            """Calculate the checksum using mod 11,2 method"""
            factors = [7, 9, 10, 5, 8, 4, 2]
            sum_ = 0
            for x, y in zip(number, factors):
                sum_ = sum_ + int(x) * y
            if sum_ % 11 == 0:
                return '0'
            else:
                return str(11 - sum_ % 11)

        first_digit = str(self.random_digit_not_null())
        body = first_digit + self.bothify('######')
        cs = calculate_checksum(body)
        return body + '-' + str(cs)

    def company_vat(self):
        """
        Returns Finnish VAT identification number (Arvonlisaveronumero).
        This can be calculated from company business identity code by
        adding prefix "FI" and removing dash before checksum.
        """
        def convert_to_vat(business_id):
            """
            Convert business id to VATIN
            """
            return 'FI' + business_id.replace('-', '')

        return convert_to_vat(self.company_business_id())
