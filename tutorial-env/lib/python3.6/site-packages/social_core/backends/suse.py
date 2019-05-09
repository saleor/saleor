"""
Open Suse OpenId backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/suse.html
"""
from .open_id import OpenIdAuth


class OpenSUSEOpenId(OpenIdAuth):
    name = 'opensuse'
    URL = 'https://www.opensuse.org/openid/user/'

    def get_user_id(self, details, response):
        """
        Return user unique id provided by service. For openSUSE
        the nickname is original.
        """
        return details['nickname']
