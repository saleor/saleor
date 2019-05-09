"""
ThisIsMyJam OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/thisismyjam.html
"""
from .oauth import BaseOAuth1


class ThisIsMyJamOAuth1(BaseOAuth1):
    """ThisIsMyJam OAuth1 authentication backend"""
    name = 'thisismyjam'
    REQUEST_TOKEN_URL = 'http://www.thisismyjam.com/oauth/request_token'
    AUTHORIZATION_URL = 'http://www.thisismyjam.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'http://www.thisismyjam.com/oauth/access_token'
    REDIRECT_URI_PARAMETER_NAME = 'oauth_callback'

    def get_user_details(self, response):
        """Return user details from ThisIsMyJam account"""
        info = response.get('person')
        fullname, first_name, last_name = self.get_user_names(
            info.get('fullname')
        )
        return {
            'username': info.get('name'),
            'email': '',
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('http://api.thisismyjam.com/1/verify.json',
                             auth=self.oauth_auth(access_token))
