"""
Chatwork OAuth2 backend
"""
import base64

from .oauth import BaseOAuth2


class ChatworkOAuth2(BaseOAuth2):
    """Chatwork OAuth authentication backend"""
    name = 'chatwork'
    API_URL = 'https://api.chatwork.com/v2'
    AUTHORIZATION_URL = 'https://www.chatwork.com/packages/oauth2/login.php'
    ACCESS_TOKEN_URL = 'https://oauth.chatwork.com/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = True
    DEFAULT_SCOPE = ['users.profile.me:read']
    ID_KEY = 'account_id'
    EXTRA_DATA = [
        ('expires_in', 'expires'),
        ('refresh_token', 'refresh_token')
    ]

    def api_url(self, path):
        api_url = self.setting('API_URL') or self.API_URL
        return '{0}{1}'.format(api_url.rstrip('/'), path)

    def auth_headers(self):
        return {
            'Authorization': b'Basic ' + base64.b64encode(
                '{0}:{1}'.format(*self.get_key_and_secret()).encode()
            )
        }

    def auth_complete_params(self, state=None):
        return {
            'grant_type': 'authorization_code',
            'code': self.data.get('code', ''),
            'redirect_uri': self.get_redirect_uri(state)
        }

    def get_user_details(self, response):
        """Return user details from Chatwork account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name')
        )
        username = response.get('chatwork_id') or \
                   response.get('login_mail') or \
                   response.get('account_id')
        email = response.get('mail') or \
                response.get('login_mail') or \
                ''
        return {
            'username': username,
            'email': email,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        headers = {'Authorization': 'Bearer ' + access_token}
        return self.get_json(self.api_url('/me'), headers=headers)

    def refresh_token_params(self, token, *args, **kwargs):
        return {'refresh_token': token, 'grant_type': 'refresh_token'}
