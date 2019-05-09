import time

from .oauth import BaseOAuth2
from ..utils import handle_http_errors


class ItembaseOAuth2(BaseOAuth2):
    name = 'itembase'
    ID_KEY = 'uuid'
    AUTHORIZATION_URL = 'https://accounts.itembase.com/oauth/v2/auth'
    ACCESS_TOKEN_URL = 'https://accounts.itembase.com/oauth/v2/token'
    USER_DETAILS_URL = 'https://users.itembase.com/v1/me'
    ACTIVATION_ENDPOINT = 'https://solutionservice.itembase.com/activate'
    DEFAULT_SCOPE = ['user.minimal']
    EXTRA_DATA = [
        ('access_token', 'access_token'),
        ('token_type', 'token_type'),
        ('refresh_token', 'refresh_token'),
        ('expires_in', 'expires_in'),  # seconds to expiration
        ('expires', 'expires'),  # expiration timestamp in UTC
        ('uuid', 'uuid'),
        ('username', 'username'),
        ('email', 'email'),
        ('first_name', 'first_name'),
        ('middle_name', 'middle_name'),
        ('last_name', 'last_name'),
        ('name_format', 'name_format'),
        ('locale', 'locale'),
        ('preferred_currency', 'preferred_currency'),
    ]

    def add_expires(self, data):
        data['expires'] = int(time.time()) + data.get('expires_in', 0)
        return data

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        data = BaseOAuth2.extra_data(self, user, uid, response,
                                     details=details,
                                     *args, **kwargs)
        return self.add_expires(data)

    def process_refresh_token_response(self, response, *args, **kwargs):
        data = BaseOAuth2.process_refresh_token_response(self, response,
                                                         *args, **kwargs)
        return self.add_expires(data)

    def get_user_details(self, response):
        """Return user details from Itembase account"""
        return response

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(self.USER_DETAILS_URL, headers={
            'Authorization': 'Bearer {0}'.format(access_token)
        })

    def activation_data(self, response):
        # returns activation_data dict with activation_url inside
        # see http://developers.itembase.com/authentication/activation
        return self.get_json(self.ACTIVATION_ENDPOINT, headers={
            'Authorization': 'Bearer {0}'.format(response['access_token'])
        })

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        state = self.validate_state()
        self.process_error(self.data)
        # itembase needs GET request with params instead of just data
        response = self.request_access_token(
            self.access_token_url(),
            params=self.auth_complete_params(state),
            headers=self.auth_headers(),
            auth=self.auth_complete_credentials(),
            method=self.ACCESS_TOKEN_METHOD
        )
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)


class ItembaseOAuth2Sandbox(ItembaseOAuth2):
    name = 'itembase-sandbox'
    AUTHORIZATION_URL = 'http://sandbox.accounts.itembase.io/oauth/v2/auth'
    ACCESS_TOKEN_URL = 'http://sandbox.accounts.itembase.io/oauth/v2/token'
    USER_DETAILS_URL = 'http://sandbox.users.itembase.io/v1/me'
    ACTIVATION_ENDPOINT = 'http://sandbox.solutionservice.itembase.io/activate'
