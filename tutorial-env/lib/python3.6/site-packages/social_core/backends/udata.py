"""
Udata related backends.

Docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/udata.html
"""
from .oauth import BaseOAuth2


class UdataBaseOAuth2(BaseOAuth2):
    """Udata base OAuth authentication backend."""
    SCOPE_SEPARATOR = ','
    REDIRECT_STATE = False
    DEFAULT_SCOPE = ['default']
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_details(self, response):
        """Return user details from Udata account."""
        return {
            'username': response.get('first_name'),
            'email': response.get('email') or '',
            'first_name': response.get('first_name')
        }

    def user_data(self, access_token, *args, **kwargs):
        """Load user data from service."""
        return self.get_json(self.USER_DATA_URL, params={
            'access_token': access_token
        })


class DatagouvfrOAuth2(UdataBaseOAuth2):
    """Datagouvfr OAuth authentication backend."""
    name = 'datagouv'
    ACCESS_TOKEN_URL = 'https://www.data.gouv.fr/oauth/token'
    AUTHORIZATION_URL = 'https://www.data.gouv.fr/oauth/authorize'
    USER_DATA_URL = 'https://www.data.gouv.fr/api/1/me/'
