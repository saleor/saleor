from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '02#######',
        '02-####-###',
        '03#######',
        '03-####-###',
        '04#######',
        '04-####-###',
        '08#######',
        '08-####-###',
        '09#######',
        '09-####-###',
        '05#-###-####',
        '05# ###-####',
        '05# ### ####',
        '05#-#######',
        '05# #######',
        '05########',
    )
