from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):

    # Source: https://en.wikipedia.org/wiki/Telephone_numbers_in_Armenia
    formats = (
        '2##-#####',
        '3##-#####',
        '(2##) #####',
        '(3##) #####',
        '2##.#####',
        '3##.#####',
        '10-######',
        '(10) ######',
        '10.######',
        '9#-######',
        '(9#) ######',
        '9#.######',
    )
