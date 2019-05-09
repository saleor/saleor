# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as BaseProvider


class Provider(BaseProvider):
    # Source:
    # https://en.wikipedia.org/wiki/National_Insurance_number
    # UK National Insurance numbers (NINO) follow a specific format
    # To avoid generating real NINOs, the prefix and suffix letters
    # remain static using values reserved by HMRC (never to be used).
    # Example format: "QR 12 34 56 C" or "QR123456C" - only alphanumeric
    # and whitespace characters are permitted. Whitespace is for readability
    # only and is generally included as per the above examples, but a
    # few 'styles' have been included below for the sake of realism.

    nino_formats = (
        'ZZ ## ## ## T',
        'ZZ######T',
        'ZZ ###### T',
    )

    def ssn(self):
        pattern = self.random_element(self.nino_formats)
        return self.numerify(self.generator.parse(pattern))

    vat_id_formats = (
        'GB### #### ##',
        'GB### #### ## ###',
        'GBGD###',
        'GBHA###',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random British VAT ID
        """
        return self.bothify(self.random_element(self.vat_id_formats))
