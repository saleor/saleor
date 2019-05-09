"""
Yahoo OpenId, OAuth1 and OAuth2 backends, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/yahoo.html
"""
from requests.auth import HTTPBasicAuth

from ..utils import handle_http_errors
from .open_id import OpenIdAuth
from .oauth import BaseOAuth2, BaseOAuth1


class YahooOpenId(OpenIdAuth):
    """Yahoo OpenID authentication backend"""
    name = 'yahoo'
    URL = 'http://me.yahoo.com'


class YahooOAuth(BaseOAuth1):
    """Yahoo OAuth authentication backend. DEPRECATED"""
    name = 'yahoo-oauth'
    ID_KEY = 'guid'
    AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth/v2/request_auth'
    REQUEST_TOKEN_URL = \
        'https://api.login.yahoo.com/oauth/v2/get_request_token'
    ACCESS_TOKEN_URL = 'https://api.login.yahoo.com/oauth/v2/get_token'
    EXTRA_DATA = [
        ('guid', 'id'),
        ('access_token', 'access_token'),
        ('expires', 'expires')
    ]

    def get_user_details(self, response):
        """Return user details from Yahoo Profile"""
        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get('givenName'),
            last_name=response.get('familyName')
        )
        emails = [email for email in response.get('emails', [])
                        if email.get('handle')]
        emails.sort(key=lambda e: e.get('primary', False), reverse=True)
        return {'username': response.get('nickname'),
                'email': emails[0]['handle'] if emails else '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = 'https://social.yahooapis.com/v1/user/{0}/profile?format=json'
        return self.get_json(
            url.format(self._get_guid(access_token)),
            auth=self.oauth_auth(access_token)
        )['profile']

    def _get_guid(self, access_token):
        """
        Beause you have to provide GUID for every API request it's also
        returned during one of OAuth calls
        """
        return self.get_json(
            'https://social.yahooapis.com/v1/me/guid?format=json',
            auth=self.oauth_auth(access_token)
        )['guid']['value']


class YahooOAuth2(BaseOAuth2):
    """Yahoo OAuth2 authentication backend"""
    name = 'yahoo-oauth2'
    ID_KEY = 'guid'
    AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth2/request_auth'
    ACCESS_TOKEN_URL = 'https://api.login.yahoo.com/oauth2/get_token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('xoauth_yahoo_guid', 'id'),
        ('access_token', 'access_token'),
        ('expires_in', 'expires'),
        ('refresh_token', 'refresh_token'),
        ('token_type', 'token_type'),
    ]

    def get_user_names(self, first_name, last_name):
        if first_name or last_name:
            return ' '.join((first_name, last_name)), first_name, last_name
        return None, None, None

    def get_user_details(self, response):
        """
        Return user details from Yahoo Profile.
        To Get user email you need the profile private read permission.
        """
        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get('givenName'),
            last_name=response.get('familyName')
        )
        emails = [email for email in response.get('emails', [])
                        if 'handle' in email]
        emails.sort(key=lambda e: e.get('primary', False), reverse=True)
        email = emails[0]['handle'] if emails else response.get('guid', '')
        return {
            'username': response.get('nickname'),
            'email': email,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = 'https://social.yahooapis.com/v1/user/{0}/profile?format=json' \
                .format(kwargs['response']['xoauth_yahoo_guid'])
        return self.get_json(url, headers={
            'Authorization': 'Bearer {0}'.format(access_token)
        }, method='GET')['profile']

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        response = self.request_access_token(
            self.ACCESS_TOKEN_URL,
            auth=HTTPBasicAuth(*self.get_key_and_secret()),
            data=self.auth_complete_params(self.validate_state()),
            headers=self.auth_headers(),
            method=self.ACCESS_TOKEN_METHOD
        )
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)

    def refresh_token_params(self, token, *args, **kwargs):
        return {
            'refresh_token': token,
            'grant_type': 'refresh_token',
            'redirect_uri': 'oob',  # out of bounds
        }

    def refresh_token(self, token, *args, **kwargs):
        params = self.refresh_token_params(token, *args, **kwargs)
        url = self.REFRESH_TOKEN_URL or self.ACCESS_TOKEN_URL
        method = self.REFRESH_TOKEN_METHOD
        key = 'params' if method == 'GET' else 'data'
        request_args = {
            'headers': self.auth_headers(),
            'method': method,
            key: params
        }
        request = self.request(
            url,
            auth=HTTPBasicAuth(*self.get_key_and_secret()),
            **request_args
        )
        return self.process_refresh_token_response(request, *args, **kwargs)

    def auth_complete_params(self, state=None):
        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'redirect_uri': self.get_redirect_uri(state)
        }
