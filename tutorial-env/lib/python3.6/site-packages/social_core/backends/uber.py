"""
Uber OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/uber.html
"""
from .oauth import BaseOAuth2


class UberOAuth2(BaseOAuth2):
    name = 'uber'
    ID_KEY = 'uuid'
    SCOPE_SEPARATOR = ' '
    AUTHORIZATION_URL = 'https://login.uber.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://login.uber.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'

    def auth_complete_credentials(self):
        return self.get_key_and_secret()

    def get_user_details(self, response):
        """Return user details from Uber account"""
        email = response.get('email', '')
        fullname, first_name, last_name = self.get_user_names(
            '',
            response.get('first_name', ''),
            response.get('last_name', '')
        )
        return {'username': email,
                'email': email,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        response = kwargs.pop('response')
        return self.get_json('https://api.uber.com/v1/me', headers={
            'Authorization': '{0} {1}'.format(response.get('token_type'),
                                              access_token)
        })
