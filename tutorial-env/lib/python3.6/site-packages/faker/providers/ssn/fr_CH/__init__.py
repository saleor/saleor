# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider


class Provider(SsnProvider):
    ssn_formats = ("###.####.####.##",)

    def ssn(self):
        """
        Returns a 13 digits Swiss SSN named AHV (German) or
                                            AVS (French and Italian)
        See: http://www.bsv.admin.ch/themen/ahv/00011/02185/
        """
        def _checksum(digits):
            evensum = sum(digits[:-1:2])
            oddsum = sum(digits[1::2])
            return (10 - ((evensum + oddsum * 3) % 10)) % 10

        digits = [7, 5, 6]
        # create an array of first 9 elements initialized randomly
        digits += self.generator.random.sample(range(10), 9)
        # determine the last digit to make it qualify the test
        digits.append(_checksum(digits))
        # repeat steps until it does qualify the test

        digits = ''.join([str(d) for d in digits])
        ssn = digits[:3] + '.' \
                         + digits[3:7] + '.' \
                         + digits[7:11] + '.' \
                         + digits[11:]
        return ssn

    def vat_id(self):
        """
        :return: Swiss UID number
        """
        def _checksum(digits):
            code = ['8', '6', '4', '2', '3', '5', '9', '7']
            remainder = 11-(sum(map(lambda x, y: int(x) * int(y), code, digits)) % 11)
            if remainder == 10:
                return 0
            elif remainder == 11:
                return 5
            return remainder

        vat_id = self.bothify('########')
        return 'CHE' + vat_id + str(_checksum(vat_id))
