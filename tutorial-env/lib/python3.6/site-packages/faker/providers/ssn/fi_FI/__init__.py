# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider
import datetime


class Provider(SsnProvider):

    def ssn(self, min_age=0, max_age=105, artificial=False):
        """
        Returns 11 character Finnish personal identity code (Henkilötunnus,
        HETU, Swedish: Personbeteckning). This function assigns random
        gender to person.

        HETU consists of eleven characters of the form DDMMYYCZZZQ, where
        DDMMYY is the date of birth, C the century sign, ZZZ the individual
        number and Q the control character (checksum). The sign for the
        century is either + (1800–1899), - (1900–1999), or A (2000–2099).
        The individual number ZZZ is odd for males and even for females.
        For people born in Finland its range is 002-899
        (larger numbers may be used in special cases).
        An example of a valid code is 311280-888Y.

        https://en.wikipedia.org/wiki/National_identification_number#Finland
        """
        def _checksum(hetu):
            checksum_characters = "0123456789ABCDEFHJKLMNPRSTUVWXY"
            return checksum_characters[int(hetu) % 31]

        age = datetime.timedelta(
            days=self.generator.random.randrange(min_age * 365, max_age * 365))
        birthday = datetime.date.today() - age
        hetu_date = "%02d%02d%s" % (
            birthday.day, birthday.month, str(birthday.year)[-2:])
        range = (900, 999) if artificial is True else (2, 899)
        suffix = str(self.generator.random.randrange(*range)).zfill(3)
        checksum = _checksum(hetu_date + suffix)
        separator = self._get_century_code(birthday.year)
        hetu = "".join([hetu_date, separator, suffix, checksum])
        return hetu

    @staticmethod
    def _get_century_code(year):
        """Returns the century code for a given year"""
        if 2000 <= year < 3000:
            separator = 'A'
        elif 1900 <= year < 2000:
            separator = '-'
        elif 1800 <= year < 1900:
            separator = '+'
        else:
            raise ValueError('Finnish SSN do not support people born before the year 1800 or after the year 2999')
        return separator

    vat_id_formats = (
        'FI########',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random Finnish VAT ID
        """
        return self.bothify(self.random_element(self.vat_id_formats))
