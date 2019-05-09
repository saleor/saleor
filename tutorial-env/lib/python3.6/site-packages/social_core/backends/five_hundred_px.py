"""
500px OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/five_hundred_px.html
"""
from .oauth import BaseOAuth1


class FiveHundredPxOAuth(BaseOAuth1):
    """500px OAuth authentication backend"""
    name = '500px'
    AUTHORIZATION_URL = 'https://api.500px.com/v1/oauth/authorize'
    REQUEST_TOKEN_URL = 'https://api.500px.com/v1/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.500px.com/v1/oauth/access_token'

    def get_user_details(self, user):
        """Return user details from 500px account"""
        fullname, first_name, last_name = self.get_user_names(
            user.get('fullname')
        )
        return {
            'username': user.get('username') or user.get('id'),
            'email': user.get('email'),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        response = self.get_json(
            'https://api.500px.com/v1/users',
            auth=self.oauth_auth(access_token)
        )
        return response.get('user')
