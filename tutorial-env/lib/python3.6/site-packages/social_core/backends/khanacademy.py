"""
Khan Academy OAuth backend, docs at:
    https://github.com/Khan/khan-api/wiki/Khan-Academy-API-Authentication
"""
import six

from six.moves.urllib_parse import urlencode

from oauthlib.oauth1 import SIGNATURE_HMAC, SIGNATURE_TYPE_QUERY
from requests_oauthlib import OAuth1

from .oauth import BaseOAuth1


class BrowserBasedOAuth1(BaseOAuth1):
    """Browser based mechanism OAuth authentication, fill the needed
    parameters to communicate properly with authentication service.

        REQUEST_TOKEN_URL       Request token URL (opened in web browser)
        ACCESS_TOKEN_URL        Access token URL
    """
    REQUEST_TOKEN_URL = ''
    OAUTH_TOKEN_PARAMETER_NAME = 'oauth_token'
    REDIRECT_URI_PARAMETER_NAME = 'redirect_uri'
    ACCESS_TOKEN_URL = ''

    def auth_url(self):
        """Return redirect url"""
        return self.unauthorized_token_request()

    def get_unauthorized_token(self):
        return self.strategy.request_data()

    def unauthorized_token_request(self):
        """Return request for unauthorized token (first stage)"""

        params = self.request_token_extra_arguments()
        params.update(self.get_scope_argument())
        key, secret = self.get_key_and_secret()
        # decoding='utf-8' produces errors with python-requests on Python3
        # since the final URL will be of type bytes
        decoding = None if six.PY3 else 'utf-8'
        state = self.get_or_create_state()
        auth = OAuth1(
            key,
            secret,
            callback_uri=self.get_redirect_uri(state),
            decoding=decoding,
            signature_method=SIGNATURE_HMAC,
            signature_type=SIGNATURE_TYPE_QUERY
        )
        url = self.REQUEST_TOKEN_URL + '?' + urlencode(params)
        url, _, _ = auth.client.sign(url)
        return url

    def oauth_auth(self, token=None, oauth_verifier=None):
        key, secret = self.get_key_and_secret()
        oauth_verifier = oauth_verifier or self.data.get('oauth_verifier')
        token = token or {}
        # decoding='utf-8' produces errors with python-requests on Python3
        # since the final URL will be of type bytes
        decoding = None if six.PY3 else 'utf-8'
        state = self.get_or_create_state()
        return OAuth1(key, secret,
                      resource_owner_key=token.get('oauth_token'),
                      resource_owner_secret=token.get('oauth_token_secret'),
                      callback_uri=self.get_redirect_uri(state),
                      verifier=oauth_verifier,
                      signature_method=SIGNATURE_HMAC,
                      signature_type=SIGNATURE_TYPE_QUERY,
                      decoding=decoding)


class KhanAcademyOAuth1(BrowserBasedOAuth1):
    """
    Class used for autorising with Khan Academy.

    Flow of Khan Academy is a bit different than most OAuth 1.0 and consinsts
    of the following steps:
    1. Create signed params to attach to the REQUEST_TOKEN_URL
    2. Redirect user to the REQUEST_TOKEN_URL that will respond with
       oauth_secret, oauth_token, oauth_verifier that should be used with
       ACCESS_TOKEN_URL
    3. Go to ACCESS_TOKEN_URL and grab oauth_token_secret.

    Note that we don't use the AUTHORIZATION_URL.

    REQUEST_TOKEN_URL requires the following arguments:
    oauth_consumer_key - Your app's consumer key
    oauth_nonce - Random 64-bit, unsigned number encoded as an ASCII string
        in decimal format. The nonce/timestamp pair should always be unique.
    oauth_version - OAuth version used by your app. Must be "1.0" for now.
    oauth_signature - String generated using the referenced signature method.
    oauth_signature_method - Signature algorithm (currently only support
        "HMAC-SHA1")
    oauth_timestamp - Integer representing the time the request is sent.
        The timestamp should be expressed in number of seconds
        after January 1, 1970 00:00:00 GMT.
    oauth_callback (optional) - URL to redirect to after request token is
        received and authorized by the user's chosen identity provider.
    """
    name = 'khanacademy-oauth1'
    ID_KEY = 'user_id'
    REQUEST_TOKEN_URL = 'http://www.khanacademy.org/api/auth/request_token'
    ACCESS_TOKEN_URL = 'https://www.khanacademy.org/api/auth/access_token'
    REDIRECT_URI_PARAMETER_NAME = 'oauth_callback'
    USER_DATA_URL = 'https://www.khanacademy.org/api/v1/user'

    EXTRA_DATA = [('user_id', 'user_id')]

    def get_user_details(self, response):
        """Return user details from Khan Academy account"""
        return {
            'username': response.get('email'),
            'email': response.get('email'),
            'fullname': response.get('nickname'),
            'first_name': '',
            'last_name': '',
            'user_id': response.get('user_id')
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        auth = self.oauth_auth(access_token)
        url, _, _ = auth.client.sign(self.USER_DATA_URL)
        return self.get_json(url)
