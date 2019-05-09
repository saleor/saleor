# coding=utf-8
from __future__ import unicode_literals
from ..fr_FR import Provider as CompanyProvider


class Provider(CompanyProvider):
    company_suffixes = ('SA', 'Sàrl.')

    def ide(self):
        """
        Generates a IDE number (9 digits).
        http://www.bfs.admin.ch/bfs/portal/fr/index/themen/00/05/blank/03/02.html
        """
        def _checksum(digits):
            factors = (5, 4, 3, 2, 7, 6, 5, 4)
            sum_ = 0
            for i in range(len(digits)):
                sum_ += digits[i] * factors[i]
            return sum_ % 11

        while True:
            # create an array of first 8 elements initialized randomly
            digits = self.generator.random.sample(range(10), 8)
            # sum those 8 digits according to (part of) the "modulo 11"
            sum_ = _checksum(digits)
            # determine the last digit to make it qualify the test
            control_number = 11 - sum_
            if control_number != 10:
                digits.append(control_number)
                break

        digits = ''.join([str(digit) for digit in digits])
        # finally return our random but valid BSN
        return 'CHE-' + digits[0:3] + '.'\
                      + digits[3:6] + '.'\
                      + digits[6:9]
    uid = ide
    # uid: german name for ide
    idi = ide
    # idi: italian name for ide
