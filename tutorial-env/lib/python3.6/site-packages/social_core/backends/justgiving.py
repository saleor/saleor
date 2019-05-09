from requests.auth import HTTPBasicAuth
from ..utils import handle_http_errors
from .oauth import BaseOAuth2


class JustGivingOAuth2(BaseOAuth2):
    """Just Giving OAuth authentication backend"""
    name = 'justgiving'
    ID_KEY = 'userId'
    AUTHORIZATION_URL = 'https://identity.justgiving.com/connect/authorize'
    ACCESS_TOKEN_URL = 'https://identity.justgiving.com/connect/token'
    ACCESS_TOKEN_METHOD = 'POST'
    USER_DATA_URL = 'https://api.justgiving.com/v1/account'
    DEFAULT_SCOPE = ['openid', 'account', 'profile', 'email', 'fundraise']

    def get_user_details(self, response):
        """Return user details from Just Giving account"""
        fullname, first_name, last_name = self.get_user_names(
            '',
            response.get('firstName'),
            response.get('lastName'))
        return {
            'username': response.get('email'),
            'email': response.get('email'),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        key, secret = self.get_key_and_secret()
        return self.get_json(self.USER_DATA_URL, headers={
            'Authorization': 'Bearer {0}'.format(access_token),
            'Content-Type': 'application/json',
            'x-application-key': secret,
            'x-api-key': key
        })

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        state = self.validate_state()
        self.process_error(self.data)

        key, secret = self.get_key_and_secret()
        response = self.request_access_token(
            self.access_token_url(),
            data=self.auth_complete_params(state),
            headers=self.auth_headers(),
            auth=HTTPBasicAuth(key, secret),
            method=self.ACCESS_TOKEN_METHOD
        )
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)
