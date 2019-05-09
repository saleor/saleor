"""
Ubuntu One OpenId backend
"""
from .open_id import OpenIdAuth


class UbuntuOpenId(OpenIdAuth):
    name = 'ubuntu'
    URL = 'https://login.ubuntu.com'

    def get_user_id(self, details, response):
        """
        Return user unique id provided by service. For Ubuntu One
        the nickname should be original.
        """
        return details['nickname']
