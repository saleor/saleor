"""
Mixcloud OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/mixcloud.html
"""
from .oauth import BaseOAuth2


class MixcloudOAuth2(BaseOAuth2):
    name = 'mixcloud'
    ID_KEY = 'username'
    AUTHORIZATION_URL = 'https://www.mixcloud.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.mixcloud.com/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(response['name'])
        return {'username': response['username'],
                'email': None,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json('https://api.mixcloud.com/me/',
                             params={'access_token': access_token,
                                     'alt': 'json'})
