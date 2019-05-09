"""
Deezer backend, docs at:
    https://developers.deezer.com/api/oauth
    https://developers.deezer.com/api/permissions
"""
from six.moves.urllib.parse import parse_qsl

from .oauth import BaseOAuth2


class DeezerOAuth2(BaseOAuth2):
    """Deezer OAuth2 authentication backend"""
    name = 'deezer'
    ID_KEY = 'name'
    AUTHORIZATION_URL = 'https://connect.deezer.com/oauth/auth.php'
    ACCESS_TOKEN_URL = 'https://connect.deezer.com/oauth/access_token.php'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    REDIRECT_STATE = False

    def auth_complete_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'app_id': client_id,
            'secret': client_secret,
            'code': self.data.get('code')
        }

    def request_access_token(self, *args, **kwargs):
        response = self.request(*args, **kwargs)
        return dict(parse_qsl(response.text))

    def get_user_details(self, response):
        """Return user details from Deezer account"""
        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get('firstname'),
            last_name=response.get('lastname')
        )
        return {'username': response.get('name'),
                'email': response.get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('http://api.deezer.com/user/me', params={
            'access_token': access_token
        })
