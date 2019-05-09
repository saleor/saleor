"""
XING OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/xing.html
"""
import six

from requests_oauthlib import OAuth1
from oauthlib.oauth1 import SIGNATURE_TYPE_AUTH_HEADER

from .oauth import BaseOAuth1
from ..exceptions import AuthTokenError


class XingOAuth(BaseOAuth1):
    """Xing OAuth authentication backend"""
    name = 'xing'
    AUTHORIZATION_URL = 'https://api.xing.com/v1/authorize'
    REQUEST_TOKEN_URL = 'https://api.xing.com/v1/request_token'
    ACCESS_TOKEN_URL = 'https://api.xing.com/v1/access_token'
    SCOPE_SEPARATOR = '+'
    EXTRA_DATA = [
        ('id', 'id'),
        ('user_id', 'user_id')
    ]

    def get_user_details(self, response):
        """Return user details from Xing account"""
        email = response.get('email', '')
        fullname, first_name, last_name = self.get_user_names(
            first_name=response['first_name'],
            last_name=response['last_name']
        )
        return {'username': first_name + last_name,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def clean_oauth_auth(self, access_token):
        """Override of oauth_auth since Xing doesn't like callback_uri
        and oauth_verifier on authenticated API calls"""
        key, secret = self.get_key_and_secret()
        resource_owner_key = access_token.get('oauth_token')
        resource_owner_secret = access_token.get('oauth_token_secret')
        if not resource_owner_key:
            raise AuthTokenError(self, 'Missing oauth_token')
        if not resource_owner_secret:
            raise AuthTokenError(self, 'Missing oauth_token_secret')
        # decoding='utf-8' produces errors with python-requests on Python3
        # since the final URL will be of type bytes
        decoding = None if six.PY3 else 'utf-8'
        return OAuth1(key, secret,
                      resource_owner_key=resource_owner_key,
                      resource_owner_secret=resource_owner_secret,
                      signature_type=SIGNATURE_TYPE_AUTH_HEADER,
                      decoding=decoding)

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        profile = self.get_json(
            'https://api.xing.com/v1/users/me.json',
            auth=self.clean_oauth_auth(access_token)
        )['users'][0]
        return {
            'user_id': profile['id'],
            'id': profile['id'],
            'first_name': profile['first_name'],
            'last_name': profile['last_name'],
            'email': profile['active_email']
        }
