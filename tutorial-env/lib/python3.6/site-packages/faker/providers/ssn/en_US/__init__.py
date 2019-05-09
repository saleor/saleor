# coding=utf-8
from __future__ import unicode_literals

import random
from .. import Provider as BaseProvider


class Provider(BaseProvider):
    SSN_TYPE = 'SSN'
    ITIN_TYPE = 'ITIN'
    EIN_TYPE = 'EIN'

    def itin(self):
        """Generate a random United States Individual Taxpayer Identification Number (ITIN).

        An United States Individual Taxpayer Identification Number
        (ITIN) is a tax processing number issued by the Internal
        Revenue Service. It is a nine-digit number that always begins
        with the number 9 and has a range of 70-88 in the fourth and
        fifth digit. Effective April 12, 2011, the range was extended
        to include 900-70-0000 through 999-88-9999, 900-90-0000
        through 999-92-9999 and 900-94-0000 through 999-99-9999.
        https://www.irs.gov/individuals/international-taxpayers/general-itin-information
        """

        area = self.random_int(min=900, max=999)
        serial = self.random_int(min=0, max=9999)

        # The group number must be between 70 and 99 inclusively but not 89 or 93
        group = random.choice([x for x in range(70, 100) if x not in [89, 93]])

        itin = "{0:03d}-{1:02d}-{2:04d}".format(area, group, serial)
        return itin

    def ein(self):
        """Generate a random United States Employer Identification Number (EIN).

         An United States An Employer Identification Number (EIN) is
         also known as a Federal Tax Identification Number, and is
         used to identify a business entity. EINs follow a format of a
         two-digit prefix followed by a hyphen and a seven-digit sequence:
         ##-######

         https://www.irs.gov/businesses/small-businesses-self-employed/employer-id-numbers
        """

        # Only certain EIN Prefix values are assigned:
        #
        # https://www.irs.gov/businesses/small-businesses-self-employed/how-eins-are-assigned-and-valid-ein-prefixes

        ein_prefix_choices = [
            '01',
            '02',
            '03',
            '04',
            '05',
            '06',
            '10',
            '11',
            '12',
            '13',
            '14',
            '15',
            '16',
            '20',
            '21',
            '22',
            '23',
            '24',
            '25',
            '26',
            '27',
            '30',
            '31',
            '32',
            '33',
            '34',
            '35',
            '36',
            '37',
            '38',
            '39',
            '40',
            '41',
            '42',
            '43',
            '44',
            '45',
            '46',
            '47',
            '48',
            '50',
            '51',
            '52',
            '53',
            '54',
            '55',
            '56',
            '57',
            '58',
            '59',
            '60',
            '61',
            '62',
            '63',
            '64',
            '65',
            '66',
            '67',
            '68',
            '71',
            '72',
            '73',
            '74',
            '75',
            '76',
            '77',
            '80',
            '81',
            '82',
            '83',
            '84',
            '85',
            '86',
            '87',
            '88',
            '90',
            '91',
            '92',
            '93',
            '94',
            '95',
            '98',
            '99']

        ein_prefix = random.choice(ein_prefix_choices)
        sequence = self.random_int(min=0, max=9999999)

        ein = "{0:s}-{1:07d}".format(ein_prefix, sequence)
        return ein

    def ssn(self, taxpayer_identification_number_type=SSN_TYPE):
        """ Generate a random United States Taxpayer Identification Number of the specified type.

        If no type is specified, a US SSN is returned.
        """

        if taxpayer_identification_number_type == self.ITIN_TYPE:
            return self.itin()
        elif taxpayer_identification_number_type == self.EIN_TYPE:
            return self.ein()
        elif taxpayer_identification_number_type == self.SSN_TYPE:

            # Certain numbers are invalid for United States Social Security
            # Numbers. The area (first 3 digits) cannot be 666 or 900-999.
            # The group number (middle digits) cannot be 00. The serial
            # (last 4 digits) cannot be 0000.

            area = self.random_int(min=1, max=899)
            if area == 666:
                area += 1
            group = self.random_int(1, 99)
            serial = self.random_int(1, 9999)

            ssn = "{0:03d}-{1:02d}-{2:04d}".format(area, group, serial)
            return ssn

        else:
            raise ValueError("taxpayer_identification_number_type must be one of 'SSN', 'EIN', or 'ITIN'.")
