"""
Coding OAuth2 backend, docs at:
"""
from six.moves.urllib.parse import urljoin

from .oauth import BaseOAuth2


class CodingOAuth2(BaseOAuth2):
    """Coding OAuth authentication backend"""

    name = 'coding'
    API_URL = 'https://coding.net/api/'
    AUTHORIZATION_URL = 'https://coding.net/oauth_authorize.html'
    ACCESS_TOKEN_URL = 'https://coding.net/api/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    DEFAULT_SCOPE = ['user']
    REDIRECT_STATE = False

    def api_url(self):
        return self.API_URL

    def get_user_details(self, response):
        """Return user details from Github account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name')
        )
        return {'username': response.get('name'),
                'email': response.get('email') or '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        data = self._user_data(access_token)
        if data.get('code') != 0:
            # 获取失败
            pass
        return data.get('data')

    def _user_data(self, access_token, path=None):
        url = urljoin(
            self.api_url(),
            'account/current_user{0}'.format(path or '')
        )
        return self.get_json(url, params={'access_token': access_token})
