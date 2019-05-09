from .oauth import BaseOAuth2


class MineIDOAuth2(BaseOAuth2):
    """MineID OAuth2 authentication backend"""
    name = 'mineid'
    _AUTHORIZATION_URL = '%(scheme)s://%(host)s/oauth/authorize'
    _ACCESS_TOKEN_URL = '%(scheme)s://%(host)s/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    EXTRA_DATA = [
    ]

    def get_user_details(self, response):
        """Return user details"""
        return {'email': response.get('email'),
                'username': response.get('email')}

    def user_data(self, access_token, *args, **kwargs):
        return self._user_data(access_token)

    def _user_data(self, access_token, path=None):
        url = '%(scheme)s://%(host)s/api/user' % self.get_mineid_url_params()
        return self.get_json(url, params={'access_token': access_token})

    @property
    def AUTHORIZATION_URL(self):
        return self._AUTHORIZATION_URL % self.get_mineid_url_params()

    @property
    def ACCESS_TOKEN_URL(self):
        return self._ACCESS_TOKEN_URL % self.get_mineid_url_params()

    def get_mineid_url_params(self):
        return {
            'host': self.setting('HOST', 'www.mineid.org'),
            'scheme': self.setting('SCHEME', 'https'),
        }
