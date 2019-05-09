# coding=utf-8
from __future__ import unicode_literals

from datetime import date

from .. import Provider as SsnProvider


class Provider(SsnProvider):
    def ssn(self):
        """
        Ukrainian "Реєстраційний номер облікової картки платника податків"
        also known as "Ідентифікаційний номер фізичної особи".
        """
        digits = []

        # Number of days between 1899-12-31 and a birth date
        for digit in str((self.generator.date_object() -
                          date(1899, 12, 31)).days):
            digits.append(int(digit))

        # Person's sequence number
        for _ in range(4):
            digits.append(self.random_int(0, 9))

        checksum = (digits[0] * -1 + digits[1] * 5 + digits[2] * 7 + digits[3] * 9 +
                    digits[4] * 4 + digits[5] * 6 + digits[6] * 10 + digits[7] * 5 +
                    digits[8] * 7)
        # Remainder of a checksum divided by 11 or 1 if it equals to 10
        digits.append(checksum % 11 % 10)

        return ''.join(str(digit) for digit in digits)
