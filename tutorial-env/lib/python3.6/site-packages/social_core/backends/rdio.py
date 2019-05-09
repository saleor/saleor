"""
Rdio OAuth1 and OAuth2 backends, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/rdio.html
"""
from .oauth import BaseOAuth1, BaseOAuth2, OAuthAuth


RDIO_API = 'https://www.rdio.com/api/1/'


class BaseRdio(OAuthAuth):
    ID_KEY = 'key'

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            fullname=response['displayName'],
            first_name=response['firstName'],
            last_name=response['lastName']
        )
        return {
            'username': response['username'],
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }


class RdioOAuth1(BaseRdio, BaseOAuth1):
    """Rdio OAuth authentication backend"""
    name = 'rdio-oauth1'
    REQUEST_TOKEN_URL = 'http://api.rdio.com/oauth/request_token'
    AUTHORIZATION_URL = 'https://www.rdio.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'http://api.rdio.com/oauth/access_token'
    EXTRA_DATA = [
        ('key', 'rdio_id'),
        ('icon', 'rdio_icon_url'),
        ('url', 'rdio_profile_url'),
        ('username', 'rdio_username'),
        ('streamRegion', 'rdio_stream_region'),
    ]

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        params = {'method': 'currentUser',
                  'extras': 'username,displayName,streamRegion'}
        request = self.oauth_request(access_token, RDIO_API,
                                     params, method='POST')
        return self.get_json(request.url, method='POST',
                             data=request.to_postdata())['result']


class RdioOAuth2(BaseRdio, BaseOAuth2):
    name = 'rdio-oauth2'
    AUTHORIZATION_URL = 'https://www.rdio.com/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://www.rdio.com/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('key', 'rdio_id'),
        ('icon', 'rdio_icon_url'),
        ('url', 'rdio_profile_url'),
        ('username', 'rdio_username'),
        ('streamRegion', 'rdio_stream_region'),
        ('refresh_token', 'refresh_token', True),
        ('token_type', 'token_type', True),
    ]

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(RDIO_API, method='POST', data={
            'method': 'currentUser',
            'extras': 'username,displayName,streamRegion',
            'access_token': access_token
        })['result']
