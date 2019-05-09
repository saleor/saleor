"""
MapMyFitness OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/mapmyfitness.html
"""
from .oauth import BaseOAuth2


class MapMyFitnessOAuth2(BaseOAuth2):
    """MapMyFitness OAuth authentication backend"""
    name = 'mapmyfitness'
    AUTHORIZATION_URL = 'https://www.mapmyfitness.com/v7.0/oauth2/authorize'
    ACCESS_TOKEN_URL = \
        'https://oauth2-api.mapmyapi.com/v7.0/oauth2/access_token'
    REQUEST_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token'),
    ]

    def auth_headers(self):
        key = self.get_key_and_secret()[0]
        return {
            'Api-Key': key
        }

    def get_user_id(self, details, response):
        return response['id']

    def get_user_details(self, response):
        first = response.get('first_name', '')
        last = response.get('last_name', '')
        full = (first + last).strip()
        return {
            'username': response['username'],
            'email': response['email'],
            'fullname': full,
            'first_name': first,
            'last_name': last,
        }

    def user_data(self, access_token, *args, **kwargs):
        key = self.get_key_and_secret()[0]
        url = 'https://oauth2-api.mapmyapi.com/v7.0/user/self/'
        headers = {
            'Authorization': 'Bearer {0}'.format(access_token),
            'Api-Key': key
        }
        return self.get_json(url, headers=headers)
