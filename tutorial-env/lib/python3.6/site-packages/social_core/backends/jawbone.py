"""
Jawbone OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/jawbone.html
"""
from ..utils import handle_http_errors
from .oauth import BaseOAuth2
from ..exceptions import AuthCanceled, AuthUnknownError


class JawboneOAuth2(BaseOAuth2):
    name = 'jawbone'
    AUTHORIZATION_URL = 'https://jawbone.com/auth/oauth2/auth'
    ACCESS_TOKEN_URL = 'https://jawbone.com/auth/oauth2/token'
    SCOPE_SEPARATOR = ' '
    REDIRECT_STATE = False

    def get_user_id(self, details, response):
        return response['data']['xid']

    def get_user_details(self, response):
        """Return user details from Jawbone account"""
        data = response['data']
        fullname, first_name, last_name = self.get_user_names(
            first_name=data.get('first', ''),
            last_name=data.get('last', '')
        )
        return {
            'username': first_name + ' ' + last_name,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
            'dob': data.get('dob', ''),
            'gender': data.get('gender', ''),
            'height': data.get('height', ''),
            'weight': data.get('weight', '')
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://jawbone.com/nudge/api/users/@me',
            headers={'Authorization': 'Bearer ' + access_token},
        )

    def process_error(self, data):
        error = data.get('error')
        if error:
            if error == 'access_denied':
                raise AuthCanceled(self)
            else:
                raise AuthUnknownError(self, 'Jawbone error was {0}'.format(
                    error
                ))
        return super(JawboneOAuth2, self).process_error(data)

    def auth_complete_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'client_id': client_id,
            'client_secret': client_secret,
        }

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        response = self.request_access_token(
            self.ACCESS_TOKEN_URL,
            params=self.auth_complete_params(self.validate_state()),
            headers=self.auth_headers(),
            method=self.ACCESS_TOKEN_METHOD
        )
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)
