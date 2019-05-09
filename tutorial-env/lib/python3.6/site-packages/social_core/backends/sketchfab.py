"""
Sketchfab OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/sketchfab.html
    https://sketchfab.com/developers/oauth
"""
from .oauth import BaseOAuth2


class SketchfabOAuth2(BaseOAuth2):
    name = 'sketchfab'
    ID_KEY = 'uid'
    AUTHORIZATION_URL = 'https://sketchfab.com/oauth2/authorize/'
    ACCESS_TOKEN_URL = 'https://sketchfab.com/oauth2/token/'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    REQUIRES_EMAIL_VALIDATION = False
    EXTRA_DATA = [
        ('username', 'username'),
        ('apiToken', 'apiToken')
    ]

    def get_user_details(self, response):
        """Return user details from Sketchfab account"""
        user_data = response
        email = user_data.get('email', '')
        username = user_data['username']
        name = user_data.get('displayName', '')
        fullname, first_name, last_name = self.get_user_names(name)
        return {'username': username,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://sketchfab.com/v2/users/me', headers={
            'Authorization': 'Bearer {0}'.format(access_token)
        })
