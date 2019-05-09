"""
MediaWiki OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/mediawiki.html
"""

import re
import time
import six
import requests
import jwt

from six import b
from six.moves.urllib.parse import parse_qs, urlencode, urlparse
from requests_oauthlib import OAuth1

from .oauth import BaseOAuth1
from ..exceptions import AuthException


def force_unicode(value):
    """
    Return string in unicode.
    """
    if isinstance(value, six.text_type):
        return value
    else:
        if six.PY3:
            return str(value, "unicode-escape")
        else:
            return unicode(value, "unicode-escape")


class MediaWiki(BaseOAuth1):
    """
    Handles the handshake with Mediawiki and fetching of user data.
    """
    name = 'mediawiki'
    MEDIAWIKI_URL = 'https://meta.wikimedia.org/w/index.php'
    SOCIAL_AUTH_MEDIAWIKI_CALLBACK = 'oob'
    LEEWAY = 10.0

    def unauthorized_token(self):
        """
        Return request for unauthorized token (first stage)

        Mediawiki request token is requested from e.g.:
         * https://en.wikipedia.org/w/index.php?title=Special:OAuth/initiate
        """
        params = self.request_token_extra_arguments()
        params.update(self.get_scope_argument())
        params['title'] = 'Special:OAuth/initiate'
        key, secret = self.get_key_and_secret()
        decoding = None if six.PY3 else 'utf-8'
        response = self.request(
            self.setting('MEDIAWIKI_URL'),
            params=params,
            auth=OAuth1(
                key,
                secret,
                callback_uri=self.setting('CALLBACK'),
                decoding=decoding
            ),
            method=self.REQUEST_TOKEN_METHOD
        )

        if response.content.decode().startswith('Error'):
            raise AuthException(self, response.content.decode())

        return response.content.decode()

    def oauth_authorization_request(self, token):
        """
        Generates the URL for the authorization link
        """
        if not isinstance(token, dict):
            token = parse_qs(token)

        oauth_token = token.get(self.OAUTH_TOKEN_PARAMETER_NAME)[0]
        state = self.get_or_create_state()
        base_url = self.setting('MEDIAWIKI_URL')

        return '{0}?{1}'.format(base_url, urlencode({
            'title': 'Special:Oauth/authenticate',
            self.OAUTH_TOKEN_PARAMETER_NAME: oauth_token,
            self.REDIRECT_URI_PARAMETER_NAME: self.get_redirect_uri(state)
        }))

    def access_token(self, token):
        """
        Fetches the Mediawiki access token.
        """
        auth_token = self.oauth_auth(token)

        response = requests.post(
            url=self.setting('MEDIAWIKI_URL'),
            params={'title': 'Special:Oauth/token'},
            auth=auth_token
        )
        credentials = parse_qs(response.content)
        oauth_token_key = credentials.get(b('oauth_token'))[0]
        oauth_token_secret = credentials.get(b('oauth_token_secret'))[0]
        oauth_token_key = oauth_token_key.decode()
        oauth_token_secret = oauth_token_secret.decode()

        return {
            'oauth_token': oauth_token_key,
            'oauth_token_secret': oauth_token_secret
        }

    def get_user_details(self, response):
        """
        Gets the user details from Special:OAuth/identify
        """
        key, secret = self.get_key_and_secret()
        access_token = response['access_token']

        auth = OAuth1(key, client_secret=secret,
                      resource_owner_key=access_token['oauth_token'],
                      resource_owner_secret=access_token['oauth_token_secret'])

        req_resp = requests.post(url=self.setting('MEDIAWIKI_URL'),
                                 params={'title': 'Special:OAuth/identify'},
                                 auth=auth)

        try:
            identity = jwt.decode(req_resp.content, secret,
                                  audience=key, algorithms=['HS256'],
                                  leeway=self.LEEWAY)
        except jwt.InvalidTokenError as exception:
            raise AuthException(
                self,
                'An error occurred while trying to read json ' +
                'content: {0}'.format(exception)
            )

        issuer = urlparse(identity['iss']).netloc
        expected_domain = urlparse(self.setting('MEDIAWIKI_URL')).netloc

        if not issuer == expected_domain:
            raise AuthException(
                self,
                'Unexpected issuer {0}, expected {1}'.format(
                    issuer,
                    expected_domain
                )
            )

        now = time.time()
        issued_at = float(identity['iat'])
        if not now >= (issued_at - self.LEEWAY):
            raise AuthException(
                self,
                'Identity issued {0} seconds in the future'.format(
                    issued_at - now
                )
            )

        authorization_header = force_unicode(
            req_resp.request.headers['Authorization']
        )
        request_nonce = re.search(r'oauth_nonce="(.*?)"',
                                  authorization_header).group(1)

        if identity['nonce'] != request_nonce:
            raise AuthException(
                self,
                'Replay attack detected: {0} != {1}'.format(
                    identity['nonce'],
                    request_nonce
                )
            )

        return {
            'username': identity['username'],
            'userID': identity['sub'],
            'email': identity.get('email'),
            'confirmed_email': identity.get('confirmed_email'),
            'editcount': identity.get('editcount'),
            'rights': identity.get('rights'),
            'groups': identity.get('groups'),
            'registered': identity.get('registered'),
            'blocked': identity.get('blocked')
        }

    def get_user_id(self, details, response):
        """
        Get the unique Mediawiki user ID.
        """
        return details['userID']
