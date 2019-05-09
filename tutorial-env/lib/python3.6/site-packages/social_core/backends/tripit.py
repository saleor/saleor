"""
Tripit OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/tripit.html
"""
from xml.dom import minidom

from .oauth import BaseOAuth1


class TripItOAuth(BaseOAuth1):
    """TripIt OAuth authentication backend"""
    name = 'tripit'
    AUTHORIZATION_URL = 'https://www.tripit.com/oauth/authorize'
    REQUEST_TOKEN_URL = 'https://api.tripit.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.tripit.com/oauth/access_token'
    EXTRA_DATA = [('screen_name', 'screen_name')]

    def get_user_details(self, response):
        """Return user details from TripIt account"""
        fullname, first_name, last_name = self.get_user_names(response['name'])
        return {'username': response['screen_name'],
                'email': response['email'],
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        dom = minidom.parseString(self.oauth_request(
            access_token,
            'https://api.tripit.com/v1/get/profile'
        ).content)
        return {
            'id': dom.getElementsByTagName('Profile')[0].getAttribute('ref'),
            'name': dom.getElementsByTagName('public_display_name')[0]
                                    .childNodes[0].data,
            'screen_name': dom.getElementsByTagName('screen_name')[0]
                                    .childNodes[0].data,
            'email': dom.getElementsByTagName('is_primary')[0]
                                    .parentNode
                                        .getElementsByTagName('address')[0]
                                            .childNodes[0].data
        }
