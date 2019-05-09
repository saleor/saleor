# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as CompanyProvider


def regon_checksum(digits):
    """
    Calculates and returns a control digit for given list of digits basing on REGON standard.
    """
    weights_for_check_digit = [8, 9, 2, 3, 4, 5, 6, 7]
    check_digit = 0

    for i in range(0, 8):
        check_digit += weights_for_check_digit[i] * digits[i]

    check_digit %= 11

    if check_digit == 10:
        check_digit = 0

    return check_digit


def local_regon_checksum(digits):
    """
    Calculates and returns a control digit for given list of digits basing on local REGON standard.
    """
    weights_for_check_digit = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]
    check_digit = 0

    for i in range(0, 13):
        check_digit += weights_for_check_digit[i] * digits[i]

    check_digit %= 11

    if check_digit == 10:
        check_digit = 0

    return check_digit


def company_vat_checksum(digits):
    """
    Calculates and returns a control digit for given list of digits basing on NIP standard.
    """
    weights_for_check_digit = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    check_digit = 0

    for i in range(0, 9):
        check_digit += weights_for_check_digit[i] * digits[i]

    check_digit %= 11

    return check_digit


class Provider(CompanyProvider):

    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{last_name}}-{{last_name}} {{company_suffix}}',
        '{{company_prefix}} {{last_name}}',
        '{{company_prefix}} {{last_name}} {{company_suffix}}',
        '{{company_prefix}} {{last_name}}-{{last_name}} {{company_suffix}}',
    )

    company_prefixes = ('Grupa', 'Spółdzielnia', 'Stowarzyszenie', 'Fundacja', 'PPUH', 'FPUH', 'Gabinety')

    company_suffixes = ('Sp. z o.o.', 'S.A.', 'Sp. z o.o. Sp.k.', 'Sp.j.', 's.c.', 'Sp.k.', 'i syn s.c.')

    def company_prefix(self):
        """
        :example 'Grupa'
        """
        return self.random_element(self.company_prefixes)

    def regon(self):
        """
        Returns 9 character Polish National Business Registry Number,
        Polish: Rejestr Gospodarki Narodowej - REGON.

        https://pl.wikipedia.org/wiki/REGON
        """
        voivodeship_number = self.random_int(0, 49) * 2 + 1
        regon_digits = [int(voivodeship_number / 10), voivodeship_number % 10]

        for _ in range(6):
            regon_digits.append(self.random_digit())

        regon_digits.append(regon_checksum(regon_digits))

        return ''.join(str(digit) for digit in regon_digits)

    def local_regon(self):
        """
        Returns 14 character Polish National Business Registry Number,
        local entity number.

        https://pl.wikipedia.org/wiki/REGON
        """
        regon_digits = [int(digit) for digit in list(self.regon())]

        for _ in range(4):
            regon_digits.append(self.random_digit())

        regon_digits.append(local_regon_checksum(regon_digits))

        return ''.join(str(digit) for digit in regon_digits)

    def company_vat(self):
        """
        Returns 10 character tax identification number,
        Polish: Numer identyfikacji podatkowej.

        https://pl.wikipedia.org/wiki/NIP
        """
        vat_digits = []

        for _ in range(3):
            vat_digits.append(self.random_digit_not_null())

        for _ in range(6):
            vat_digits.append(self.random_digit())

        check_digit = company_vat_checksum(vat_digits)

        # in this case we must generate a tax number again, because check_digit
        # cannot be 10
        if check_digit == 10:
            return self.company_vat()

        vat_digits.append(check_digit)

        return ''.join(str(digit) for digit in vat_digits)
