# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider
import datetime


class Provider(SsnProvider):

    def ssn(self, min_age=18, max_age=90):
        """
        Returns a 10 digit Swedish SSN, "Personnummer".

        It consists of 10 digits in the form YYMMDD-SSGQ, where
        YYMMDD is the date of birth, SSS is a serial number
        and Q is a control character (Luhn checksum).

        http://en.wikipedia.org/wiki/Personal_identity_number_(Sweden)
        """
        def _luhn_checksum(number):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = 0
            checksum += sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10

        def _calculate_luhn(partial_number):
            check_digit = _luhn_checksum(int(partial_number) * 10)
            return check_digit if check_digit == 0 else 10 - check_digit

        age = datetime.timedelta(
            days=self.generator.random.randrange(min_age * 365, max_age * 365))
        birthday = datetime.datetime.now() - age
        pnr_date = birthday.strftime('%y%m%d')
        suffix = str(self.generator.random.randrange(0, 999)).zfill(3)
        luhn_checksum = str(_calculate_luhn(pnr_date + suffix))
        pnr = '{0}-{1}{2}'.format(pnr_date, suffix, luhn_checksum)

        return pnr

    vat_id_formats = (
        'SE############',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random Swedish VAT ID
        """

        return self.bothify(self.random_element(self.vat_id_formats))
