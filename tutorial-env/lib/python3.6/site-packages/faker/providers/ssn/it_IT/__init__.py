# coding=utf-8
"""it_IT ssn provider (yields italian fiscal codes)"""

from __future__ import unicode_literals
from string import ascii_uppercase, digits
from .. import Provider as SsnProvider


ALPHANUMERICS = sorted(digits + ascii_uppercase)
ALPHANUMERICS_DICT = {char: index for index, char in enumerate(ALPHANUMERICS)}
CHECKSUM_TABLE = (
    (1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 1, 0, 5, 7, 9, 13, 15, 17, 19,
     21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23),
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
     11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25))


def checksum(value):
    """
    Calculates the checksum char used for the 16th char.
    Author: Vincenzo Palazzo
    """
    return chr(65 + sum(CHECKSUM_TABLE[index % 2][ALPHANUMERICS_DICT[char]]
                        for index, char in enumerate(value)) % 26)


class Provider(SsnProvider):
    """
    Generates italian fiscal codes.
    """
    fiscal_code_format = '??????##?##?###'

    def ssn(self):
        code = self.bothify(self.fiscal_code_format).upper()
        return code + checksum(code)

    vat_id_formats = (
        'IT###########',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random Italian VAT ID
        """
        return self.bothify(self.random_element(self.vat_id_formats))
