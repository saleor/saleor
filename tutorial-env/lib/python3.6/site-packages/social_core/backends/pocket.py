"""
Pocket OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/pocket.html
"""
from .base import BaseAuth
from ..utils import handle_http_errors


class PocketAuth(BaseAuth):
    name = 'pocket'
    AUTHORIZATION_URL = 'https://getpocket.com/auth/authorize'
    ACCESS_TOKEN_URL = 'https://getpocket.com/v3/oauth/authorize'
    REQUEST_TOKEN_URL = 'https://getpocket.com/v3/oauth/request'
    ID_KEY = 'username'

    def get_json(self, url, *args, **kwargs):
        headers = {'X-Accept': 'application/json'}
        kwargs.update({'method': 'POST', 'headers': headers})
        return super(PocketAuth, self).get_json(url, *args, **kwargs)

    def get_user_details(self, response):
        return {'username': response['username']}

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        return response

    def auth_url(self):
        data = {
            'consumer_key': self.setting('KEY'),
            'redirect_uri': self.redirect_uri,
        }
        token = self.get_json(self.REQUEST_TOKEN_URL, data=data)['code']
        self.strategy.session_set('pocket_request_token', token)
        bits = (self.AUTHORIZATION_URL, token, self.redirect_uri)
        return '%s?request_token=%s&redirect_uri=%s' % bits

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        data = {
            'consumer_key': self.setting('KEY'),
            'code': self.strategy.session_get('pocket_request_token'),
        }
        response = self.get_json(self.ACCESS_TOKEN_URL, data=data)
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)
