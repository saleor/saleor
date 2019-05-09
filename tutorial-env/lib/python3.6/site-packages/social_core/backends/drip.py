"""
Drip OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/drip.html
"""
from .oauth import BaseOAuth2


class DripOAuth(BaseOAuth2):
    name = 'drip'
    AUTHORIZATION_URL = 'https://www.getdrip.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.getdrip.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_id(self, details, response):
        return details['email']

    def get_user_details(self, response):
        return {'email': response['users'][0]['email'],
                'fullname': response['users'][0]['name'],
                'username': response['users'][0]['email']}

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json('https://api.getdrip.com/v2/user', headers={
            'Authorization': 'Bearer %s' % access_token
        })
