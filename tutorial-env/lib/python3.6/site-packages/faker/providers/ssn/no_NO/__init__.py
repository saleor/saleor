# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider
import datetime
import operator


def checksum(digits, scale):
    """
    Calculate checksum of Norwegian personal identity code.

    Checksum is calculated with "Module 11" method using a scale.
    The digits of the personal code are multiplied by the corresponding
    number in the scale and summed;
    if remainder of module 11 of the sum is less than 10, checksum is the
    remainder.
    If remainder is 0, the checksum is 0.

    https://no.wikipedia.org/wiki/F%C3%B8dselsnummer
    """
    chk_nbr = 11 - (sum(map(operator.mul, digits, scale)) % 11)
    if chk_nbr == 11:
        return 0
    return chk_nbr


class Provider(SsnProvider):
    scale1 = (3, 7, 6, 1, 8, 9, 4, 5, 2)
    scale2 = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)

    def ssn(self, dob=None, gender=None):
        """
        Returns 11 character Norwegian personal identity code (Fødselsnummer).

        A Norwegian personal identity code consists of 11 digits, without any
        whitespace or other delimiters. The form is DDMMYYIIICC, where III is
        a serial number separating persons born oh the same date with different
        intervals depending on the year they are born. CC is two checksums.
        https://en.wikipedia.org/wiki/National_identification_number#Norway

        :param dob: date of birth as a "YYYYMMDD" string
        :type dob: str
        :param gender: gender of the person - "F" for female, M for male.
        :type gender: str
        :return: Fødselsnummer in str format (11 digs)
        :rtype: str
        """

        if dob:
            birthday = datetime.datetime.strptime(dob, '%Y%m%d')
        else:
            age = datetime.timedelta(
                days=self.generator.random.randrange(18 * 365, 90 * 365))
            birthday = datetime.datetime.now() - age
        if not gender:
            gender = self.generator.random.choice(('F', 'M'))
        elif gender not in ('F', 'M'):
            raise ValueError('Gender must be one of F or M.')

        while True:
            if 1900 <= birthday.year <= 1999:
                suffix = str(self.generator.random.randrange(0, 49))
            elif 1854 <= birthday.year <= 1899:
                suffix = str(self.generator.random.randrange(50, 74))
            elif 2000 <= birthday.year <= 2039:
                suffix = str(self.generator.random.randrange(50, 99))
            elif 1940 <= birthday.year <= 1999:
                suffix = str(self.generator.random.randrange(90, 99))
            if gender == 'F':
                gender_num = self.generator.random.choice((0, 2, 4, 6, 8))
            elif gender == 'M':
                gender_num = self.generator.random.choice((1, 3, 5, 7, 9))
            pnr = birthday.strftime('%d%m%y') + suffix.zfill(2) + str(gender_num)
            pnr_nums = [int(ch) for ch in pnr]
            k1 = checksum(Provider.scale1, pnr_nums)
            k2 = checksum(Provider.scale2, pnr_nums + [k1])
            # Checksums with a value of 10 is rejected.
            # https://no.wikipedia.org/wiki/F%C3%B8dselsnummer
            if k1 == 10 or k2 == 10:
                continue
            pnr += '{}{}'.format(k1, k2)
            return pnr
