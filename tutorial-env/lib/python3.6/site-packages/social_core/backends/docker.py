"""
Docker Hub OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/docker.html
"""
from .oauth import BaseOAuth2


class DockerOAuth2(BaseOAuth2):
    name = 'docker'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = 'https://hub.docker.com/api/v1.1/o/authorize/'
    ACCESS_TOKEN_URL = 'https://hub.docker.com/api/v1.1/o/token/'
    REFRESH_TOKEN_URL = 'https://hub.docker.com/api/v1.1/o/token/'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('user_id', 'user_id'),
        ('email', 'email'),
        ('full_name', 'fullname'),
        ('location', 'location'),
        ('url', 'url'),
        ('company', 'company'),
        ('gravatar_email', 'gravatar_email'),
    ]

    def get_user_details(self, response):
        """Return user details from Docker Hub account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('full_name') or response.get('username') or ''
        )
        return {
            'username': response.get('username'),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
            'email': response.get('email', '')
        }

    def user_data(self, access_token, *args, **kwargs):
        """Grab user profile information from Docker Hub."""
        username = kwargs['response']['username']
        return self.get_json(
            'https://hub.docker.com/api/v1.1/users/%s/' % username,
            headers={'Authorization': 'Bearer %s' % access_token}
        )
