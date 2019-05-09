"""
Reddit OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/reddit.html
"""
import base64

from .oauth import BaseOAuth2


class RedditOAuth2(BaseOAuth2):
    """Reddit OAuth2 authentication backend"""
    name = 'reddit'
    AUTHORIZATION_URL = 'https://ssl.reddit.com/api/v1/authorize'
    ACCESS_TOKEN_URL = 'https://ssl.reddit.com/api/v1/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    SCOPE_SEPARATOR = ','
    DEFAULT_SCOPE = ['identity']
    SEND_USER_AGENT = True
    EXTRA_DATA = [
        ('id', 'id'),
        ('name', 'username'),
        ('link_karma', 'link_karma'),
        ('comment_karma', 'comment_karma'),
        ('refresh_token', 'refresh_token'),
        ('expires_in', 'expires')
    ]

    def get_user_details(self, response):
        """Return user details from Reddit account"""
        return {'username': response.get('name'),
                'email': '', 'fullname': '',
                'first_name': '', 'last_name': ''}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://oauth.reddit.com/api/v1/me.json',
            headers={'Authorization': 'bearer ' + access_token}
        )

    def auth_headers(self):
        return {
            'Authorization': b'Basic ' + base64.urlsafe_b64encode(
                '{0}:{1}'.format(*self.get_key_and_secret()).encode()
            )
        }

    def refresh_token_params(self, token, redirect_uri=None, *args, **kwargs):
        params = super(RedditOAuth2, self).refresh_token_params(token)
        params['redirect_uri'] = self.redirect_uri or redirect_uri
        return params

    def auth_complete_credentials(self):
        return self.get_key_and_secret()
