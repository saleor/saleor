# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider


def checksum(digits):
    """
    Calculates and returns a control digit for given list of digits basing on PESEL standard.
    """
    weights_for_check_digit = [9, 7, 3, 1, 9, 7, 3, 1, 9, 7]
    check_digit = 0

    for i in range(0, 10):
        check_digit += weights_for_check_digit[i] * digits[i]

    check_digit %= 10

    return check_digit


def calculate_month(birth_date):
    """
    Calculates and returns a month number basing on PESEL standard.
    """
    year = int(birth_date.strftime('%Y'))
    month = int(birth_date.strftime('%m')) + ((int(year / 100) - 14) % 5) * 20

    return month


class Provider(SsnProvider):

    def ssn(self):
        """
        Returns 11 character Polish national identity code (Public Electronic Census System,
        Polish: Powszechny Elektroniczny System Ewidencji Ludności - PESEL).

        It has the form YYMMDDZZZXQ, where YYMMDD is the date of birth (with century
        encoded in month field), ZZZ is the personal identification number, X denotes sex
        (even for females, odd for males) and Q is a parity number.

        https://en.wikipedia.org/wiki/National_identification_number#Poland
        """
        birth_date = self.generator.date_time()

        year_without_century = int(birth_date.strftime('%y'))
        month = calculate_month(birth_date)
        day = int(birth_date.strftime('%d'))

        pesel_digits = [
            int(year_without_century / 10),
            year_without_century % 10,
            int(month / 10),
            month % 10,
            int(day / 10), day % 10,
        ]

        for _ in range(4):
            pesel_digits.append(self.random_digit())

        pesel_digits.append(checksum(pesel_digits))

        return ''.join(str(digit) for digit in pesel_digits)

    vat_id_formats = (
        'PL##########',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random Polish VAT ID
        """
        return self.bothify(self.random_element(self.vat_id_formats))
