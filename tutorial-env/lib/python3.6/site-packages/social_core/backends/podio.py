"""
Podio OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/podio.html
"""
from .oauth import BaseOAuth2


class PodioOAuth2(BaseOAuth2):
    """Podio OAuth authentication backend"""
    name = 'podio'
    AUTHORIZATION_URL = 'https://podio.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://podio.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('access_token', 'access_token'),
        ('token_type', 'token_type'),
        ('expires_in', 'expires'),
        ('refresh_token', 'refresh_token'),
    ]

    def get_user_id(self, details, response):
        return response['ref']['id']

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            response['profile']['name']
        )
        return {
            'username': 'user_%d' % response['user']['user_id'],
            'email': response['user']['mail'],
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json('https://api.podio.com/user/status',
            headers={'Authorization': 'OAuth2 ' + access_token})
