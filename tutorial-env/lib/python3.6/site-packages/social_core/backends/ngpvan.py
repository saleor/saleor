"""
NGP VAN's `ActionID` Provider

http://developers.ngpvan.com/action-id
"""
from openid.extensions import ax

from .open_id import OpenIdAuth


class ActionIDOpenID(OpenIdAuth):
    """
    NGP VAN's ActionID OpenID 1.1 authentication backend
    """
    name = 'actionid-openid'
    URL = 'https://accounts.ngpvan.com/Home/Xrds'
    USERNAME_KEY = 'email'

    def get_ax_attributes(self):
        """
        Return the AX attributes that ActionID responds with, as well as the
        user data result that it must map to.
        """
        return [
            ('http://openid.net/schema/contact/internet/email', 'email'),
            ('http://openid.net/schema/contact/phone/business', 'phone'),
            ('http://openid.net/schema/namePerson/first', 'first_name'),
            ('http://openid.net/schema/namePerson/last', 'last_name'),
            ('http://openid.net/schema/namePerson', 'fullname'),
        ]

    def setup_request(self, params=None):
        """
        Setup the OpenID request

        Because ActionID does not advertise the availiability of AX attributes
        nor use standard attribute aliases, we need to setup the attributes
        manually instead of rely on the parent OpenIdAuth.setup_request()
        """
        request = self.openid_request(params)

        fetch_request = ax.FetchRequest()
        fetch_request.add(ax.AttrInfo(
            'http://openid.net/schema/contact/internet/email',
            alias='ngpvanemail',
            required=True
        ))

        fetch_request.add(ax.AttrInfo(
            'http://openid.net/schema/contact/phone/business',
            alias='ngpvanphone',
            required=False
        ))
        fetch_request.add(ax.AttrInfo(
            'http://openid.net/schema/namePerson/first',
            alias='ngpvanfirstname',
            required=False
        ))
        fetch_request.add(ax.AttrInfo(
            'http://openid.net/schema/namePerson/last',
            alias='ngpvanlastname',
            required=False
        ))
        request.addExtension(fetch_request)

        return request
