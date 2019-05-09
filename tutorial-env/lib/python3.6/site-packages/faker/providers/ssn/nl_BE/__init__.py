# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider

"""
For more info on rijksregisternummer, see https://nl.wikipedia.org/wiki/Rijksregisternummer
Dutch/French only for now ...
"""


class Provider(SsnProvider):

    def ssn(self):
        """
        Returns a 11 digits Belgian SSN called "rijksregisternummer" as a string

        The first 6 digits represent the birthdate with (in order) year, month and day.
        The second group of 3 digits is represents a sequence number (order of birth).
        It is even for women and odd for men.
        For men the range starts at 1 and ends 997, for women 2 until 998.
        The third group of 2 digits is a checksum based on the previous 9 digits (modulo 97).
        Divide those 9 digits by 97, subtract the remainder from 97 and that's the result.
        For persons born in or after 2000, the 9 digit number needs to be proceeded by a 2
        (add 2000000000) before the division by 97.

        """
        # see http://nl.wikipedia.org/wiki/Burgerservicenummer (in Dutch)
        def _checksum(digits):
            res = 97 - (digits % 97)
            return res

        # Generate a date (random)
        mydate = self.generator.date()
        # Convert it to an int
        elms = mydate.split("-")
        # Adjust for year 2000 if necessary
        if elms[0][0] == '2':
            above = True
        else:
            above = False
        # Only keep the last 2 digits of the year
        elms[0] = elms[0][2:4]
        # Simulate the gender/sequence - should be 3 digits
        seq = self.generator.random_int(1, 998)
        # Right justify sequence and append to list
        seq_str = "{:0>3}".format(seq)
        elms.append(seq_str)
        # Now convert list to an integer so the checksum can be calculated
        date_as_int = int("".join(elms))
        if above:
            date_as_int += 2000000000
        # Generate checksum
        s = _checksum(date_as_int)
        s_rjust = "{:0>2}".format(s)
        # return result as a string
        elms.append(s_rjust)
        return "".join(elms)

    vat_id_formats = (
        'BE##########',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random Belgian VAT ID
        """
        return self.bothify(self.random_element(self.vat_id_formats))
