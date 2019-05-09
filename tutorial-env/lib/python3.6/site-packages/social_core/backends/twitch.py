"""
Twitch OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/twitch.html
"""
from .oauth import BaseOAuth2


class TwitchOAuth2(BaseOAuth2):
    """Twitch OAuth authentication backend"""
    name = 'twitch'
    ID_KEY = '_id'
    AUTHORIZATION_URL = 'https://api.twitch.tv/kraken/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://api.twitch.tv/kraken/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['user_read']
    REDIRECT_STATE = False

    def get_user_details(self, response):
        return {
            'username': response.get('name'),
            'email': response.get('email'),
            'first_name': '',
            'last_name': ''
        }

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(
            'https://api.twitch.tv/kraken/user/',
            params={'oauth_token': access_token}
        )
