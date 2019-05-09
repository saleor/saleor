"""
Appsfueld OAuth2 backend (with sandbox mode support), docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/appsfuel.html
"""
from .oauth import BaseOAuth2


class AppsfuelOAuth2(BaseOAuth2):
    name = 'appsfuel'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = 'http://app.appsfuel.com/content/permission'
    ACCESS_TOKEN_URL = 'https://api.appsfuel.com/v1/live/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    USER_DETAILS_URL = 'https://api.appsfuel.com/v1/live/user'

    def get_user_details(self, response):
        """Return user details from Appsfuel account"""
        email = response.get('email', '')
        username = email.split('@')[0] if email else ''
        fullname, first_name, last_name = self.get_user_names(
            response.get('display_name', '')
        )
        return {
            'username': username,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(self.USER_DETAILS_URL, params={
            'access_token': access_token
        })


class AppsfuelOAuth2Sandbox(AppsfuelOAuth2):
    name = 'appsfuel-sandbox'
    AUTHORIZATION_URL = 'https://api.appsfuel.com/v1/sandbox/choose'
    ACCESS_TOKEN_URL = 'https://api.appsfuel.com/v1/sandbox/oauth/token'
    USER_DETAILS_URL = 'https://api.appsfuel.com/v1/sandbox/user'
