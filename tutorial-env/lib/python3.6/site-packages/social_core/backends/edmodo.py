"""
Edmodo OAuth2 Sign-in backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/edmodo.html
"""
from .oauth import BaseOAuth2


class EdmodoOAuth2(BaseOAuth2):
    """Edmodo OAuth2"""
    name = 'edmodo'
    AUTHORIZATION_URL = 'https://api.edmodo.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.edmodo.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_details(self, response):
        """Return user details from Edmodo account"""
        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get('first_name'),
            last_name=response.get('last_name')
        )
        return {
            'username': response.get('username'),
            'email': response.get('email'),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from Edmodo"""
        return self.get_json(
            'https://api.edmodo.com/users/me',
            params={'access_token': access_token}
        )
