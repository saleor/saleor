""" SciStarter OAuth2 Auth """

from six.moves.urllib_parse import unquote, urlencode

from .oauth import BaseOAuth2


class SciStarterOAuth2(BaseOAuth2):
    name = 'scistarter'
    ID_KEY = 'email'
    SCOPE_PARAMETER_NAME = 'scope'
    DEFAULT_SCOPE = ['login', 'extensive']
    SCOPE_SEPARATOR = ' '
    AUTHORIZATION_URL = 'https://scistarter.com/authorize'
    ACCESS_TOKEN_URL = 'https://scistarter.com/token?key={key}'
    ACCESS_TOKEN_METHOD = 'POST'
    USER_ACCESS_URL = \
        'https://scistarter.com/api/user_info?client_id={clientid}&key={key}'
    REFRESH_TOKEN_URL = None
    RESPONSE_TYPE = 'code'
    STATE_PARAMETER = True
    REDIRECT_STATE = True
    EXTRA_DATA = [
        ('profile_id', 'profile_id'),
        ('expires', 'expires')
    ]

    def get_redirect_uri(self, state=None):
        """Build redirect with redirect_state parameter."""
        return self.redirect_uri.rstrip('/')

    def authorization_url(self):
        return self.AUTHORIZATION_URL

    def get_user_details(self, response):
        return {
            'username': response.get('handle'),
            'email': response.get('email') or '',
            'first_name': response.get('first_name'),
            'last_name': response.get('last_name')
        }

    def user_data(self, access_token, *args, **kwards):
        client_id, client_secret = self.get_key_and_secret()
        return self.get_json(
            self.USER_ACCESS_URL.format(clientid=client_id, key=client_secret),
            headers={
                'Authorization': 'Bearer ' + access_token
            }
        )

    def access_token(self, token):
        """Return request for access token value"""
        return self.get_querystring(self.access_token_url(),
                                    auth=self.oauth_auth(token),
                                    method=self.ACCESS_TOKEN_METHOD)

    def access_token_url(self):
        client_id, client_secret = self.get_key_and_secret()
        return self.ACCESS_TOKEN_URL.format(key=client_secret)
