"""
Coinbase OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/coinbase.html
"""
from .oauth import BaseOAuth2


class CoinbaseOAuth2(BaseOAuth2):
    name = 'coinbase'
    SCOPE_SEPARATOR = '+'
    DEFAULT_SCOPE = ['user', 'balance']
    AUTHORIZATION_URL = 'https://www.coinbase.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.coinbase.com/oauth/token'
    REVOKE_TOKEN_URL = 'https://api.coinbase.com/oauth/revoke'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def get_user_id(self, details, response):
        return response['data']['id']

    def get_user_details(self, response):
        """Return user details from Coinbase account"""
        user_data = response['data']
        email = user_data.get('email', '')
        name = user_data['name']
        username = user_data.get('username')
        fullname, first_name, last_name = self.get_user_names(name)
        return {'username': username,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://api.coinbase.com/v2/user',
                headers={'Authorization': 'Bearer ' + access_token})
