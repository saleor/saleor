"""
Angel OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/angel.html
"""
from .oauth import BaseOAuth2


class AngelOAuth2(BaseOAuth2):
    name = 'angel'
    AUTHORIZATION_URL = 'https://angel.co/api/oauth/authorize/'
    ACCESS_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'https://angel.co/api/oauth/token/'
    REDIRECT_STATE = False

    def get_user_details(self, response):
        """Return user details from Angel account"""
        username = response['angellist_url'].split('/')[-1]
        email = response.get('email', '')
        fullname, first_name, last_name = self.get_user_names(response['name'])
        return {'username': username,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://api.angel.co/1/me/', params={
            'access_token': access_token
        })
