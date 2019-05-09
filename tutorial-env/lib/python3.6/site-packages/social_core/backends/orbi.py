"""
Orbi OAuth2 backend
"""
from .oauth import BaseOAuth2


class OrbiOAuth2(BaseOAuth2):
    """Orbi OAuth2 authentication backend"""
    name = 'orbi'
    AUTHORIZATION_URL = 'https://login.orbi.kr/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://login.orbi.kr/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('imin', 'imin'),
        ('nick', 'nick'),
        ('photo', 'photo'),
        ('sex', 'sex'),
        ('birth', 'birth'),
    ]

    def get_user_id(self, details, response):
        return response.get('id')

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            response.get('name', ''),
            response.get('first_name', ''),
            response.get('last_name', '')
        )
        return {
            'username': response.get('username', response.get('name')),
            'email': response.get('email', ''),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }

    def user_data(self, access_token, *args, **kwargs):
        """Load user data from orbi"""
        return self.get_json('https://login.orbi.kr/oauth/user/get', params={
            'access_token': access_token
        })
