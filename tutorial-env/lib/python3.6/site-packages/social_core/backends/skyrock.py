"""
Skyrock OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/skyrock.html
"""
from .oauth import BaseOAuth1


class SkyrockOAuth(BaseOAuth1):
    """Skyrock OAuth authentication backend"""
    name = 'skyrock'
    ID_KEY = 'id_user'
    AUTHORIZATION_URL = 'https://api.skyrock.com/v2/oauth/authenticate'
    REQUEST_TOKEN_URL = 'https://api.skyrock.com/v2/oauth/initiate'
    ACCESS_TOKEN_URL = 'https://api.skyrock.com/v2/oauth/token'
    EXTRA_DATA = [('id', 'id')]

    def get_user_details(self, response):
        """Return user details from Skyrock account"""
        fullname, first_name, last_name = self.get_user_names(
            first_name=response['firstname'],
            last_name=response['name']
        )
        return {'username': response['username'],
                'email': response['email'],
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token):
        """Return user data provided"""
        return self.get_json('https://api.skyrock.com/v2/user/get.json',
                             auth=self.oauth_auth(access_token))
