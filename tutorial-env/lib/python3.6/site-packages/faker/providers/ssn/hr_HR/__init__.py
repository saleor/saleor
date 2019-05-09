# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider


def checksum(digits):
    """
    Calculate and return control digit for given list of digits based on
    ISO7064, MOD 11,10 standard.
    """
    remainder = 10
    for digit in digits:
        remainder = (remainder + digit) % 10
        if remainder == 0:
            remainder = 10
        remainder = (remainder * 2) % 11

    control_digit = 11 - remainder
    if control_digit == 10:
        control_digit = 0
    return control_digit


class Provider(SsnProvider):
    """
    The Personal identification number (Croatian: Osobni identifikacijski
    broj or OIB) is a permanent national identification number of every
    Croatian citizen and legal persons domiciled in the Republic of Croatia.

    OIB consists of 11 digits which contain no personal information. The OIB
    is constructed from ten randomly chosen digits and one digit control number
    (international standard ISO 7064, module 11.10).
    """

    def ssn(self):
        digits = self.generator.random.sample(range(10), 10)

        digits.append(checksum(digits))

        return ''.join(map(str, digits))

    vat_id_formats = (
        'HR###########',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random Croatian VAT ID
        """
        return self.bothify(self.random_element(self.vat_id_formats))
