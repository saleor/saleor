"""
Patreon OAuth2 backend
https://www.patreon.com/platform/documentation/oauth
"""
from .oauth import BaseOAuth2


class PatreonOAuth2(BaseOAuth2):
    """Patreon OAuth2 authentication backend"""
    name = 'patreon'
    AUTHORIZATION_URL = 'https://www.patreon.com/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://api.patreon.com/oauth2/token'
    REVOKE_TOKEN_URL = 'https://api.patreon.com/oauth2/revoke'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    ID_KEY = 'id'
    EXTRA_DATA = [
        ('id', 'id'),
    ]

    def get_user_details(self, response):
        details = response['attributes']
        return {
            'username': details.get('full_name'),
            'email': details.get('email'),
            'fullname': details.get('full_name'),
            'first_name': details.get('first_name'),
            'last_name': details.get('last_name'),
        }

    def user_data(self, access_token, *args, **kwargs):
        return self.get_api(access_token, 'current_user')['data']

    def get_api(self, access_token, suffix):
        return self.get_json(
            'https://api.patreon.com/oauth2/api/{}'.format(suffix),
            headers=self.get_auth_header(access_token)
        )

    def get_auth_header(self, access_token):
        return {'Authorization': 'Bearer {0}'.format(access_token)}
