# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider


class Provider(SsnProvider):

    def ssn(self):
        """
        Returns a 9 digits Dutch SSN called "burgerservicenummer (BSN)".

        the Dutch "burgerservicenummer (BSN)" needs to pass the "11-proef",
        which is a check digit approach; this function essentially reverses
        the checksum steps to create a random valid BSN (which is 9 digits).
        """
        # see http://nl.wikipedia.org/wiki/Burgerservicenummer (in Dutch)
        def _checksum(digits):
            factors = (9, 8, 7, 6, 5, 4, 3, 2, -1)
            s = 0
            for i in range(len(digits)):
                s += digits[i] * factors[i]
            return s

        while True:
            # create an array of first 8 elements initialized randomly
            digits = self.generator.random.sample(range(10), 8)
            # sum those 8 digits according to (part of) the "11-proef"
            s = _checksum(digits)
            # determine the last digit to make it qualify the test
            digits.append((s % 11) % 10)
            # repeat steps until it does qualify the test
            if 0 == (_checksum(digits) % 11):
                break

        # build the resulting BSN
        bsn = "".join([str(e) for e in digits])
        # finally return our random but valid BSN
        return bsn

    vat_id_formats = (
        'NL#########B##',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random Dutch VAT ID
        """
        return self.bothify(self.random_element(self.vat_id_formats))
