"""
EVE Online Single Sign-On (SSO) OAuth2 backend
Documentation at https://eveonline-third-party-documentation.readthedocs.io/en/latest/sso/index.html
"""
from .oauth import BaseOAuth2


class EVEOnlineOAuth2(BaseOAuth2):
    """EVE Online OAuth authentication backend"""
    name = 'eveonline'
    BASE_URL = 'https://login.eveonline.com/oauth'
    AUTHORIZATION_URL = BASE_URL + '/authorize'
    ACCESS_TOKEN_URL = BASE_URL + '/token'
    ID_KEY = 'CharacterID'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('CharacterID', 'id'),
        ('expires_in', 'expires'),
        ('CharacterOwnerHash', 'owner_hash', True),
        ('refresh_token', 'refresh_token', True),
    ]

    def get_user_details(self, response):
        """Return user details from EVE Online account"""
        user_data = self.user_data(response['access_token'])
        fullname, first_name, last_name = self.get_user_names(
            user_data['CharacterName']
        )
        return {
            'email': '',
            'username': fullname,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Get Character data from EVE server"""
        return self.get_json(
            'https://login.eveonline.com/oauth/verify',
            headers={'Authorization': 'Bearer {0}'.format(access_token)}
        )
