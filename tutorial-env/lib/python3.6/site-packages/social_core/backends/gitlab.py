"""
GitLab OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/gitlab.html

Thanks to [@saily](https://github.com/saily) who published an
implementation for GitLab support on his blog post [Weblate with
GitLab as OAuth provider](http://widerin.net/blog/weblate-gitlab-oauth-login/).
His code was a great reference when working on this implementation.
"""
from requests import HTTPError

from six.moves.urllib.parse import urljoin

from .oauth import BaseOAuth2
from ..exceptions import AuthFailed


class GitLabOAuth2(BaseOAuth2):
    """GitLab OAuth authentication backend"""
    name = 'gitlab'
    API_URL = 'https://gitlab.com'
    AUTHORIZATION_URL = 'https://gitlab.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://gitlab.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    DEFAULT_SCOPE = ['read_user']
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires_in', 'expires'),
        ('refresh_token', 'refresh_token')
    ]

    def api_url(self, path):
        api_url = self.setting('API_URL') or self.API_URL
        return '{0}{1}'.format(api_url.rstrip('/'), path)

    def authorization_url(self):
        return self.api_url('/oauth/authorize')

    def access_token_url(self):
        return self.api_url('/oauth/token')

    def get_user_details(self, response):
        """Return user details from GitLab account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name')
        )
        return {'username': response.get('username'),
                'email': response.get('email') or '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(self.api_url('/api/v4/user'), params={
            'access_token': access_token
        })
