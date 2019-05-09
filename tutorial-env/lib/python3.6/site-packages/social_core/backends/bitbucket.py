"""
Bitbucket OAuth2 and OAuth1 backends, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/bitbucket.html
"""
from ..exceptions import AuthForbidden
from .oauth import BaseOAuth1, BaseOAuth2


class BitbucketOAuthBase(object):
    ID_KEY = 'uuid'

    def get_user_id(self, details, response):
        id_key = self.ID_KEY
        if self.setting('USERNAME_AS_ID', False):
            id_key = 'username'
        return response.get(id_key)

    def get_user_details(self, response):
        """Return user details from Bitbucket account"""
        fullname, first_name, last_name = self.get_user_names(
            response['display_name']
        )

        return {'username': response.get('username', ''),
                'email': response.get('email', ''),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        emails = self._get_emails(access_token)
        email = None

        for address in reversed(emails['values']):
            email = address['email']
            if address['is_primary']:
                break

        if self.setting('VERIFIED_EMAILS_ONLY', False) and \
            not address['is_confirmed']:
            raise AuthForbidden(
                self,
                'Bitbucket account has no verified email'
            )

        user = self._get_user(access_token)
        if email:
            user['email'] = email
        return user

    def _get_user(self, access_token=None):
        raise NotImplementedError('Implement in subclass')

    def _get_emails(self, access_token=None):
        raise NotImplementedError('Implement in subclass')


class BitbucketOAuth2(BitbucketOAuthBase, BaseOAuth2):
    name = 'bitbucket-oauth2'
    SCOPE_SEPARATOR = ' '
    AUTHORIZATION_URL = 'https://bitbucket.org/site/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://bitbucket.org/site/oauth2/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('scopes', 'scopes'),
        ('expires_in', 'expires'),
        ('token_type', 'token_type'),
        ('refresh_token', 'refresh_token')
    ]

    def auth_complete_credentials(self):
        return self.get_key_and_secret()

    def _get_user(self, access_token=None):
        return self.get_json('https://api.bitbucket.org/2.0/user',
                             params={'access_token': access_token})

    def _get_emails(self, access_token=None):
        return self.get_json('https://api.bitbucket.org/2.0/user/emails',
                             params={'access_token': access_token})


class BitbucketOAuth(BitbucketOAuthBase, BaseOAuth1):
    """Bitbucket OAuth authentication backend"""
    name = 'bitbucket'
    AUTHORIZATION_URL = 'https://bitbucket.org/api/1.0/oauth/authenticate'
    REQUEST_TOKEN_URL = 'https://bitbucket.org/api/1.0/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://bitbucket.org/api/1.0/oauth/access_token'

    def oauth_auth(self, *args, **kwargs):
        return super(BitbucketOAuth, self).oauth_auth(*args, **kwargs)

    def _get_user(self, access_token=None):
        return self.get_json('https://api.bitbucket.org/2.0/user',
                             auth=self.oauth_auth(access_token))

    def _get_emails(self, access_token=None):
        return self.get_json('https://api.bitbucket.org/2.0/user/emails',
                             auth=self.oauth_auth(access_token))
