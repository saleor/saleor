"""
LINE Login OAuth2 backend, docs at:
    https://developers.line.me/en/docs/line-login/
"""
import requests
import json

from .oauth import BaseOAuth2
from ..exceptions import AuthFailed
from ..utils import handle_http_errors


class LineOAuth2(BaseOAuth2):
    name = 'line'
    AUTHORIZATION_URL = 'https://access.line.me/oauth2/v2.1/authorize'
    ACCESS_TOKEN_URL = 'https://api.line.me/oauth2/v2.1/token'
    BASE_API_URL = 'https://api.line.me'
    USER_INFO_URL = BASE_API_URL + '/v2/profile'
    ACCESS_TOKEN_METHOD = 'POST'
    STATE_PARAMETER = True
    DEFAULT_SCOPE = ['profile']
    REDIRECT_STATE = True
    ID_KEY = 'userId'
    EXTRA_DATA = [
        ('userId', 'id'),
        ('picture_url', 'picture_url'),
        ('status_message', 'status_message'),
        ('expires_in', 'expire'),
        ('refresh_token', 'refresh_token')
    ]

    def auth_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'response_type': self.RESPONSE_TYPE,
            'client_id': client_id,
            'redirect_uri': self.get_redirect_uri(),
            'state': self.get_or_create_state(),
            'scope': self.get_scope()
        }

    def process_error(self, data):
        error_code = data.get('errorCode') or \
                     data.get('statusCode') or \
                     data.get('error')
        error_message = data.get('errorMessage') or \
                        data.get('error_description')
        if error_code is not None or error_message is not None:
            raise AuthFailed(self, error_message or error_code)

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)

        try:
            response = self.request_access_token(
                self.access_token_url(),
                method=self.ACCESS_TOKEN_METHOD,
                headers=self.auth_headers(),
                data=self.auth_complete_params()
            )
            self.process_error(response)

            return self.do_auth(response['access_token'], response=response,
                                *args, **kwargs)
        except requests.HTTPError as err:
            self.process_error(json.loads(err.response.content))

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            response.get('displayName')
        )
        username = response.get('userId')
        picture_url = response.get('pictureUrl')
        status_message = response.get('statusMessage')
        return {
            'username': username,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
            'picture_url': picture_url,
            'status_message': status_message
        }

    def get_user_id(self, details, response):
        """
        Return a unique ID for the current user, by default from
        server response.
        """
        return response.get(self.ID_KEY)

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        try:
            response = self.get_json(
                self.USER_INFO_URL,
                headers={
                    "Authorization": "Bearer {}".format(access_token)
                }
            )
            self.process_error(response)
            return response
        except requests.HTTPError as err:
            self.process_error(err.response.json())
