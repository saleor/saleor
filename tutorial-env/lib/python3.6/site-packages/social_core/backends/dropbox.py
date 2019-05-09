"""
Dropbox OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/dropbox.html
"""
import warnings

from .oauth import BaseOAuth1, BaseOAuth2


class DropboxOAuth(BaseOAuth1):
    """Dropbox OAuth authentication backend"""
    name = 'dropbox'
    ID_KEY = 'uid'
    AUTHORIZATION_URL = 'https://www.dropbox.com/1/oauth/authorize'
    REQUEST_TOKEN_URL = 'https://api.dropbox.com/1/oauth/request_token'
    REQUEST_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'https://api.dropbox.com/1/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_URI_PARAMETER_NAME = 'oauth_callback'
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires')
    ]

    def __init__(self, *args, **kwargs):
        warnings.warn(
            'Dropbox V1 api is deprecated and will be shute down 2017-06-28 '
            'https://blogs.dropbox.com/developers/2016/06/api-v1-deprecated/',
            DeprecationWarning,
            stacklevel=2
        )
        super(DropboxOAuth, self).__init__(*args, **kwargs)

    def get_user_details(self, response):
        """Return user details from Dropbox account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('display_name')
        )
        return {'username': str(response.get('uid')),
                'email': response.get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('https://api.dropbox.com/1/account/info',
                             auth=self.oauth_auth(access_token))


class DropboxOAuth2(BaseOAuth2):
    name = 'dropbox-oauth2'
    ID_KEY = 'uid'
    AUTHORIZATION_URL = 'https://www.dropbox.com/1/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://api.dropbox.com/1/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('uid', 'username'),
    ]

    def __init__(self, *args, **kwargs):
        warnings.warn(
            'Dropbox V1 api is deprecated and will be shute down 2017-06-28 '
            'https://blogs.dropbox.com/developers/2016/06/api-v1-deprecated/',
            DeprecationWarning,
            stacklevel=2
        )
        super(DropboxOAuth2, self).__init__(*args, **kwargs)

    def get_user_details(self, response):
        """Return user details from Dropbox account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('display_name')
        )
        return {'username': str(response.get('uid')),
                'email': response.get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://api.dropbox.com/1/account/info',
            headers={'Authorization': 'Bearer {0}'.format(access_token)}
        )


class DropboxOAuth2V2(BaseOAuth2):
    name = 'dropbox-oauth2'
    ID_KEY = 'uid'
    AUTHORIZATION_URL = 'https://www.dropbox.com/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://api.dropboxapi.com/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def get_user_details(self, response):
        """Return user details from Dropbox account"""
        name = response.get('name')
        return {'username': str(response.get('account_id')),
                'email': response.get('email'),
                'fullname': name.get('display_name'),
                'first_name': name.get('given_name'),
                'last_name': name.get('surname')}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://api.dropboxapi.com/2/users/get_current_account',
            headers={'Authorization': 'Bearer {0}'.format(access_token)},
            method='POST'
        )
