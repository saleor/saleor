"""
Fitbit OAuth backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/fitbit.html
"""
import base64

from .oauth import BaseOAuth1, BaseOAuth2


class FitbitOAuth1(BaseOAuth1):
    """Fitbit OAuth1 authentication backend"""
    name = 'fitbit'
    AUTHORIZATION_URL = 'https://www.fitbit.com/oauth/authorize'
    REQUEST_TOKEN_URL = 'https://api.fitbit.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.fitbit.com/oauth/access_token'
    ID_KEY = 'encodedId'
    EXTRA_DATA = [('encodedId', 'id'),
                  ('displayName', 'username')]

    def get_user_details(self, response):
        """Return user details from Fitbit account"""
        return {'username': response.get('displayName'),
                'email': ''}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://api.fitbit.com/1/user/-/profile.json',
            auth=self.oauth_auth(access_token)
        )['user']


class FitbitOAuth2(BaseOAuth2):
    """Fitbit OAuth2 authentication backend"""
    name = 'fitbit'
    AUTHORIZATION_URL = 'https://www.fitbit.com/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
    DEFAULT_SCOPE = ['profile']
    ID_KEY = 'encodedId'
    REDIRECT_STATE = False
    EXTRA_DATA = [('expires_in', 'expires'),
                  ('refresh_token', 'refresh_token', True),
                  ('encodedId', 'id'),
                  ('displayName', 'username')]

    def get_user_details(self, response):
        """Return user details from Fitbit account"""
        return {'username': response.get('displayName'),
                'email': ''}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        auth_header = {"Authorization": "Bearer %s" % access_token}
        return self.get_json(
            'https://api.fitbit.com/1/user/-/profile.json',
            headers=auth_header
        )['user']

    def auth_headers(self):
        tokens = '{0}:{1}'.format(*self.get_key_and_secret())
        tokens = base64.urlsafe_b64encode(tokens.encode())
        tokens = tokens.decode()
        return {
            'Authorization': 'Basic {0}'.format(tokens)
        }
