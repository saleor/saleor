"""
Moves OAuth2 backend, docs at:
    https://dev.moves-app.com/docs/authentication

Written by Avi Alkalay <avi at unix dot sh>
Certified to work with Django 1.6
"""
from .oauth import BaseOAuth2


class MovesOAuth2(BaseOAuth2):
    """Moves OAuth authentication backend"""
    name = 'moves'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = 'https://api.moves-app.com/oauth/v1/authorize'
    ACCESS_TOKEN_URL = 'https://api.moves-app.com/oauth/v1/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('expires_in', 'expires'),
    ]

    def get_user_details(self, response):
        """Return user details Moves account"""
        return {'username': str(response.get('user_id'))}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://api.moves-app.com/api/1.1/user/profile',
                             params={'access_token': access_token})
