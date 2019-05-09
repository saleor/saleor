"""
Stackoverflow OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/stackoverflow.html
"""
from .oauth import BaseOAuth2


class StackoverflowOAuth2(BaseOAuth2):
    """Stackoverflow OAuth2 authentication backend"""
    name = 'stackoverflow'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = 'https://stackexchange.com/oauth'
    ACCESS_TOKEN_URL = 'https://stackexchange.com/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires')
    ]

    def get_user_details(self, response):
        """Return user details from Stackoverflow account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('display_name')
        )
        return {'username': response.get('link').rsplit('/', 1)[-1],
                'full_name': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://api.stackexchange.com/2.1/me',
            params={
                'site': 'stackoverflow',
                'access_token': access_token,
                'key': self.setting('API_KEY')
            }
        )['items'][0]

    def request_access_token(self, *args, **kwargs):
        return self.get_querystring(*args, **kwargs)
