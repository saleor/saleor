"""
Flat OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/flat.html
"""
from .oauth import BaseOAuth2


class FlatOAuth2(BaseOAuth2):
    """Flat OAuth2"""
    name = 'flat'
    DEFAULT_SCOPE = ['account.public_profile']
    AUTHORIZATION_URL = 'https://flat.io/auth/oauth'
    ACCESS_TOKEN_URL = 'https://api.flat.io/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_id(self, details, response):
        return response.get('id')

    def get_user_details(self, response):
        """Return user details from Flat account"""
        return {
            'email': response.get('email'),
            'username': response.get('username'),
            'fullname': response.get('printableName')
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://api.flat.io/v2/me', headers={
            'Authorization': 'Bearer ' + access_token
        })
