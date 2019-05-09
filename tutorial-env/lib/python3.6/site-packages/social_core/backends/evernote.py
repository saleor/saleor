"""
Evernote OAuth1 backend (with sandbox mode support), docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/evernote.html
"""
from requests import HTTPError

from ..exceptions import AuthCanceled
from .oauth import BaseOAuth1


class EvernoteOAuth(BaseOAuth1):
    """
    Evernote OAuth authentication backend.

    Possible Values:
       {'edam_expires': ['1367525289541'],
        'edam_noteStoreUrl': [
            'https://sandbox.evernote.com/shard/s1/notestore'
        ],
        'edam_shard': ['s1'],
        'edam_userId': ['123841'],
        'edam_webApiUrlPrefix': ['https://sandbox.evernote.com/shard/s1/'],
        'oauth_token': [
            'S=s1:U=1e3c1:E=13e66dbee45:C=1370f2ac245:P=185:A=my_user:' \
            'H=411443c5e8b20f8718ed382a19d4ae38'
        ]}
    """
    name = 'evernote'
    ID_KEY = 'edam_userId'
    AUTHORIZATION_URL = 'https://www.evernote.com/OAuth.action'
    REQUEST_TOKEN_URL = 'https://www.evernote.com/oauth'
    ACCESS_TOKEN_URL = 'https://www.evernote.com/oauth'
    EXTRA_DATA = [
        ('access_token', 'access_token'),
        ('oauth_token', 'oauth_token'),
        ('edam_noteStoreUrl', 'store_url'),
        ('edam_expires', 'expires')
    ]

    def get_user_details(self, response):
        """Return user details from Evernote account"""
        return {'username': response['edam_userId'],
                'email': ''}

    def access_token(self, token):
        """Return request for access token value"""
        try:
            return self.get_querystring(self.ACCESS_TOKEN_URL,
                                        auth=self.oauth_auth(token))
        except HTTPError as err:
            # Evernote returns a 401 error when AuthCanceled
            if err.response.status_code == 401:
                raise AuthCanceled(self, response=err.response)
            else:
                raise

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        data = super(EvernoteOAuth, self).extra_data(user, uid, response,
                                                     details, *args, **kwargs)
        # Evernote returns expiration timestamp in milliseconds, so it needs to
        # be normalized.
        if 'expires' in data:
            data['expires'] = int(data['expires']) / 1000
        return data

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        return access_token.copy()


class EvernoteSandboxOAuth(EvernoteOAuth):
    name = 'evernote-sandbox'
    AUTHORIZATION_URL = 'https://sandbox.evernote.com/OAuth.action'
    REQUEST_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
    ACCESS_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
