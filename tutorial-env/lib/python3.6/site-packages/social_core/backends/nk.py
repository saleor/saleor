from urllib import urlencode

import six

from requests_oauthlib import OAuth1

from .oauth import BaseOAuth2


class NKOAuth2(BaseOAuth2):
    """NK OAuth authentication backend"""
    name = 'nk'
    AUTHORIZATION_URL = 'https://nk.pl/oauth2/login'
    ACCESS_TOKEN_URL = 'https://nk.pl/oauth2/token'
    SCOPE_SEPARATOR = ','
    ACCESS_TOKEN_METHOD = 'POST'
    SIGNATURE_TYPE_AUTH_HEADER = 'AUTH_HEADER'
    EXTRA_DATA = [
        ('id', 'id'),
    ]

    def get_user_details(self, response):
        """Return user details from NK account"""
        entry = response['entry']
        return {
            'username': entry.get('displayName'),
            'email': entry['emails'][0]['value'],
            'first_name': entry.get('displayName').split(' ')[0],
            'id': entry.get('id')
        }

    def auth_complete_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': self.get_redirect_uri(state),
            'scope': self.get_scope_argument()
        }

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server
        response."""
        return details.get(self.ID_KEY)

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = 'http://opensocial.nk-net.pl/v09/social/rest/people/@me?' + \
              urlencode({
                  'nk_token': access_token,
                  'fields': 'name,surname,avatar,localization,age,' +
                            'gender,emails,birthdate'
              })
        return self.get_json(
            url,
            auth=self.oauth_auth(access_token)
        )

    def oauth_auth(self, token=None, oauth_verifier=None,
                   signature_type=SIGNATURE_TYPE_AUTH_HEADER):
        key, secret = self.get_key_and_secret()
        oauth_verifier = oauth_verifier or self.data.get('oauth_verifier')
        token = token or {}
        # decoding='utf-8' produces errors with python-requests on Python3
        # since the final URL will be of type bytes
        decoding = None if six.PY3 else 'utf-8'
        state = self.get_or_create_state()
        return OAuth1(key, secret,
                      resource_owner_key=None,
                      resource_owner_secret=None,
                      callback_uri=self.get_redirect_uri(state),
                      verifier=oauth_verifier,
                      signature_type=signature_type,
                      decoding=decoding)
