"""
Trello OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/trello.html
"""
from .oauth import BaseOAuth1


class TrelloOAuth(BaseOAuth1):

    """Trello OAuth authentication backend"""
    name = 'trello'
    ID_KEY = 'username'
    AUTHORIZATION_URL = 'https://trello.com/1/OAuthAuthorizeToken'
    REQUEST_TOKEN_URL = 'https://trello.com/1/OAuthGetRequestToken'
    ACCESS_TOKEN_URL = 'https://trello.com/1/OAuthGetAccessToken'

    EXTRA_DATA = [
        ('username', 'username'),
        ('email', 'email'),
        ('fullName', 'fullName')
    ]

    def get_user_details(self, response):
        """Return user details from Trello account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('fullName')
        )
        return {'username': response.get('username'),
                'email': response.get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token):
        """Return user data provided"""
        url = 'https://trello.com/1/members/me'
        try:
            return self.get_json(url, auth=self.oauth_auth(access_token))
        except ValueError:
            return None

    def auth_extra_arguments(self):
        return {
            'name': self.setting('APP_NAME', ''),
            # trello default expiration is '30days'
            'expiration': self.setting('EXPIRATION', 'never')
        }
