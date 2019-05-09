from __future__ import unicode_literals
from .. import Provider as PhoneNumberProvider


class Provider(PhoneNumberProvider):
    formats = (
        '+421 2 ########',
        '+421 3# ### ####',
        '+421 4# ### ####',
        '+421 5# ### ####',
        '+421 90# ### ###',
        '+421 91# ### ###',
        '+421 940 ### ###',
        '+421 944 ### ###',
        '+421 948 ### ###',
        '+421 949 ### ###',
    )
