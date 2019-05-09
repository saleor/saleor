"""
DailyMotion OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/dailymotion.html
"""
from .oauth import BaseOAuth2


class DailymotionOAuth2(BaseOAuth2):
    """Dailymotion OAuth authentication backend"""
    name = 'dailymotion'
    EXTRA_DATA = [('id', 'id')]
    ID_KEY = 'username'
    AUTHORIZATION_URL = 'https://api.dailymotion.com/oauth/authorize'
    REQUEST_TOKEN_URL = 'https://api.dailymotion.com/oauth/token'
    ACCESS_TOKEN_URL = 'https://api.dailymotion.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_details(self, response):
        return {'username': response.get('screenname')}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        return self.get_json('https://api.dailymotion.com/auth/',
                             params={'access_token': access_token})
