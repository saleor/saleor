"""
Lyft OAuth2 backend. Read more about the
    API at https://developer.lyft.com/docs
"""
from .oauth import BaseOAuth2


class LyftOAuth2(BaseOAuth2):
    name = 'lyft'
    ID_KEY = 'id'
    SCOPE_SEPARATOR = ' '
    AUTHORIZATION_URL = 'https://api.lyft.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.lyft.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_URL = 'https://api.lyft.com/oauth/token'
    USER_DATA_URL = 'https://api.lyft.com/v1/profile'
    DEFAULT_SCOPE = ['public', 'profile', 'rides.read', 'rides.request']
    RESPONSE_TYPE = 'code'
    STATE_PARAMETER = 'asdf'
    EXTRA_DATA = [
        ('id', 'id'),
        ('username', 'username'),
        ('access_token', 'access_token'),
        ('refresh_token', 'refresh_token'),
        ('token_type', 'token_type'),
        ('expires_in', 'expires_in'),
        ('scope', 'scope'),
    ]

    def get_user_details(self, response):
        """Return user details from Lyft account"""
        return {
            'id': response['id'],
            'username': response['id']
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        response = kwargs.pop('response')
        return self.get_json(self.USER_DATA_URL, headers={
          'Authorization': 'Bearer {0}'.format(access_token)
        })

    def auth_complete_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',
            'code': self.data['code']
        }

    def auth_complete_credentials(self):
        return self.get_key_and_secret()

    def refresh_token_params(self, refresh_token, *args, **kwargs):
        return {
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
