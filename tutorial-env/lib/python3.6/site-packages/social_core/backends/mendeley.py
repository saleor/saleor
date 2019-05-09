"""
Mendeley OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/mendeley.html
"""
from .oauth import BaseOAuth1, BaseOAuth2


class MendeleyMixin(object):
    SCOPE_SEPARATOR = '+'
    EXTRA_DATA = [('profile_id', 'profile_id'),
                  ('name', 'name'),
                  ('bio', 'bio')]

    def get_user_id(self, details, response):
        return response['id']

    def get_user_details(self, response):
        """Return user details from Mendeley account"""
        profile_id = response['id']
        name = response['display_name']
        bio = response['link']
        return {'profile_id': profile_id,
                'name': name,
                'bio': bio}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        values = self.get_user_data(access_token)
        values.update(values)
        return values

    def get_user_data(self, access_token):
        raise NotImplementedError('Implement in subclass')


class MendeleyOAuth(MendeleyMixin, BaseOAuth1):
    name = 'mendeley'
    AUTHORIZATION_URL = 'http://api.mendeley.com/oauth/authorize/'
    REQUEST_TOKEN_URL = 'http://api.mendeley.com/oauth/request_token/'
    ACCESS_TOKEN_URL = 'http://api.mendeley.com/oauth/access_token/'

    def get_user_data(self, access_token):
        return self.get_json(
            'http://api.mendeley.com/oapi/profiles/info/me/',
            auth=self.oauth_auth(access_token)
        )


class MendeleyOAuth2(MendeleyMixin, BaseOAuth2):
    name = 'mendeley-oauth2'
    AUTHORIZATION_URL = 'https://api-oauth2.mendeley.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api-oauth2.mendeley.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['all']
    REDIRECT_STATE = False
    EXTRA_DATA = MendeleyMixin.EXTRA_DATA + [
        ('refresh_token', 'refresh_token'),
        ('expires_in', 'expires_in'),
        ('token_type', 'token_type'),
    ]

    def get_user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://api.mendeley.com/profiles/me/',
            headers={'Authorization': 'Bearer {0}'.format(access_token)}
        )
