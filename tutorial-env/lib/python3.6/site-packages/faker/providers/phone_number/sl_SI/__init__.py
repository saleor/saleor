from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '040 ### ###',
        '041 ### ###',
        '031 ### ###',
        '030 ### ###',
        '070 ### ###',
        '01 #### ###',
        '02 #### ###',
        '04 #### ###',
        '05 #### ###',
        '06 #### ###',
        '08 #### ###',
    )
