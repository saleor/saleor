# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as SsnProvider
from functools import reduce
from math import fmod


def zfix(d):
    if d < 10:
        return "0" + str(d)
    else:
        return d


class Provider(SsnProvider):
    def ssn(self, dob=None, gender=None):
        """
        Generates Hungarian SSN equivalent (személyazonosító szám or, colloquially, személyi szám)

        :param dob: date of birth as a "YYMMDD" string - this determines the checksum regime and is also encoded
            in the személyazonosító szám.
        :type dob: str
        :param gender: gender of the person - "F" for female, M for male.
        :type gender: str
        :return: személyazonosító szám in str format (11 digs)
        :rtype: str
        """
        # Hungarian SSNs consist of 11 decimal characters, of the following
        # schema:
        #
        #       M EEHHNN SSSK
        #       ↑    ↑    ↑ ↑
        #  gender  bday ser check digit
        #
        #
        #  The M (gender) character
        #  ------------------------
        #
        #  Born <= 1999        Born > 1999
        #  Male  Female        Male Female
        #   1      2             3     4
        #
        #  It also includes information on original citizenship,but this is
        #  ignored for the sake of simplicity.
        #
        #  Birthday
        #  --------
        #
        #  Simply encoded as EEHHNN.
        #
        #
        #  Serial
        #  ------
        #
        #  These digits differentiate persons born on the same date.
        #
        #
        #  Check digit
        #  -----------
        #
        #  For those born before 1996:
        #
        #  k11 = (1k1 + 2k2 + 3k3... 10k10) mod 11
        #
        #  That is, you multiply each digit with its ordinal, add it up and
        #  take it mod 11. After 1996:
        #
        #  k11 = (10k1 + 9k2 + 8k3... 1k10) mod 11
        #

        if dob:
            E = int(dob[0:2])
            H = int(dob[2:4])
            N = int(dob[4:6])

            if E <= 17:
                # => person born after '99 in all likelihood...
                if gender:
                    if gender.upper() == "F":
                        M = 4
                    elif gender.upper() == "M":
                        M = 3
                    else:
                        raise ValueError("Unknown gender - specify M or F.")
                else:
                    M = self.generator.random_int(3, 4)
            else:
                # => person born before '99.
                if gender:
                    if gender.upper() == "F":
                        M = 2
                    elif gender.upper() == "M":
                        M = 1
                    else:
                        raise ValueError("Unknown gender - specify M or F.")
                else:
                    M = self.generator.random_int(1, 2)
        elif gender:
            # => assume statistically that the person will be born before '99.
            E = self.generator.random_int(17, 99)
            H = self.generator.random_int(1, 12)
            N = self.generator.random_int(1, 30)

            if gender.upper() == "F":
                M = 2
            elif gender.upper() == "M":
                M = 1
            else:
                raise ValueError("Unknown gender - specify M or F")
        else:
            M = self.generator.random_int(1, 2)
            E = self.generator.random_int(17, 99)
            H = self.generator.random_int(1, 12)
            N = self.generator.random_int(1, 30)

        H = zfix(H)
        N = zfix(N)
        S = "{}{}{}".format(self.generator.random_digit(
        ), self.generator.random_digit(), self.generator.random_digit())

        vdig = "{M}{E}{H}{N}{S}".format(M=M, E=E, H=H, N=N, S=S)

        if 17 < E < 97:
            cum = [(k + 1) * int(v) for k, v in enumerate(vdig)]
        else:
            cum = [(10 - k) * int(v) for k, v in enumerate(vdig)]

        K = fmod(reduce(lambda x, y: x + y, cum), 11)

        return vdig + str(int(K))

    vat_id_formats = (
        'HU########',
    )

    def vat_id(self):
        """
        http://ec.europa.eu/taxation_customs/vies/faq.html#item_11
        :return: A random Hungarian VAT ID
        """
        return self.bothify(self.random_element(self.vat_id_formats))
