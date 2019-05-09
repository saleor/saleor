"""
Upwork OAuth1 backend
"""
from .oauth import BaseOAuth1


class UpworkOAuth(BaseOAuth1):
    """Upwork OAuth authentication backend"""
    name = 'upwork'
    ID_KEY = 'id'
    AUTHORIZATION_URL = 'https://www.upwork.com/services/api/auth'
    REQUEST_TOKEN_URL = \
        'https://www.upwork.com/api/auth/v1/oauth/token/request'
    REQUEST_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'https://www.upwork.com/api/auth/v1/oauth/token/access'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_URI_PARAMETER_NAME = 'oauth_callback'

    def get_user_details(self, response):
        """Return user details from Upwork account"""
        info = response.get('info', {})
        auth_user = response.get('auth_user', {})
        first_name = auth_user.get('first_name')
        last_name = auth_user.get('last_name')
        fullname = '{} {}'.format(first_name, last_name)
        profile_url = info.get('profile_url', '')
        username = profile_url.rsplit('/')[-1].replace('~', '')
        return {
            'username': username,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://www.upwork.com/api/auth/v1/info.json',
            auth=self.oauth_auth(access_token)
        )
