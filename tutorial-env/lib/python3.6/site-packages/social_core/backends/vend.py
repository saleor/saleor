"""
Vend  OAuth2 backend:
"""
from .oauth import BaseOAuth2


class VendOAuth2(BaseOAuth2):
    name = 'vend'
    AUTHORIZATION_URL = 'https://secure.vendhq.com/connect'
    ACCESS_TOKEN_URL = 'https://{0}.vendhq.com/api/1.0/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token'),
        ('domain_prefix', 'domain_prefix')
    ]

    def access_token_url(self):
        return self.ACCESS_TOKEN_URL.format(self.data['domain_prefix'])

    def get_user_details(self, response):
        email = response['email']
        username = response.get('username') or email.split('@', 1)[0]
        return {
            'username': username,
            'email': email,
            'fullname': '',
            'first_name': '',
            'last_name': ''
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        prefix = kwargs['response']['domain_prefix']
        url = 'https://{0}.vendhq.com/api/users'.format(prefix)
        data = self.get_json(url, headers={
            'Authorization': 'Bearer {0}'.format(access_token)
        })
        return data['users'][0] if data.get('users') else {}
