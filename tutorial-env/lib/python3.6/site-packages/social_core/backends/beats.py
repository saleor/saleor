"""
Beats backend, docs at:
    https://developer.beatsmusic.com/docs
"""
import base64

from ..utils import handle_http_errors
from .oauth import BaseOAuth2


class BeatsOAuth2(BaseOAuth2):
    name = 'beats'
    SCOPE_SEPARATOR = ' '
    ID_KEY = 'user_context'
    AUTHORIZATION_URL = \
        'https://partner.api.beatsmusic.com/v1/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://partner.api.beatsmusic.com/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def get_user_id(self, details, response):
        return response['result'][BeatsOAuth2.ID_KEY]

    def auth_headers(self):
        return {
            'Authorization': 'Basic {0}'.format(base64.urlsafe_b64encode(
                ('{0}:{1}'.format(*self.get_key_and_secret()).encode())
            ))
        }

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        response = self.request_access_token(
            self.ACCESS_TOKEN_URL,
            data=self.auth_complete_params(self.validate_state()),
            headers=self.auth_headers(),
            method=self.ACCESS_TOKEN_METHOD
        )
        self.process_error(response)
        # mashery wraps in jsonrpc
        if response.get('jsonrpc', None):
            response = response.get('result', None)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)

    def get_user_details(self, response):
        """Return user details from Beats account"""
        response = response['result']
        fullname, first_name, last_name = self.get_user_names(
            response.get('display_name')
        )
        return {'username': response.get('id'),
                'email': response.get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://partner.api.beatsmusic.com/v1/api/me',
            headers={'Authorization': 'Bearer {0}'.format(access_token)}
        )
