"""
Openshift OAuth2 backend
"""
import requests

from six.moves.urllib.parse import urljoin

from ..utils import append_slash
from .oauth import BaseOAuth2


class OpenshiftOAuth2(BaseOAuth2):
    name = 'openshift'
    ACCESS_TOKEN_METHOD = 'POST'

    def access_token_url(self):
        return urljoin(append_slash(self.setting('URL')), 'oauth/token')

    def authorization_url(self):
        return urljoin(append_slash(self.setting('URL')), 'oauth/authorize')

    def get_user_id(self, details, response):
        return response['metadata']['uid']

    def get_user_details(self, response):
        """Return user details from openshift account"""
        username = response['metadata']['name']
        email = response['metadata']['name']
        return {'username': username,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        headers = {'Authorization': 'Bearer ' + access_token}

        return requests.get(
            urljoin(append_slash(self.setting('URL')), 'oapi/v1/users/~'),
            headers=headers
        ).json()
