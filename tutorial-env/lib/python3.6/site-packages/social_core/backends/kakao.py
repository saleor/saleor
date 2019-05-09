"""
Kakao OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/kakao.html
"""
from .oauth import BaseOAuth2


class KakaoOAuth2(BaseOAuth2):
    """Kakao OAuth authentication backend"""
    name = 'kakao'
    AUTHORIZATION_URL = 'https://kauth.kakao.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('properties', 'properties'),
    ]

    def get_user_id(self, details, response):
        return response['id']

    def get_user_details(self, response):
        """Return user details from Kakao account"""
        kaccount_email = response.get('kaccount_email', '')
        properties = response.get('properties', '')
        nickname = properties.get('nickname') if properties else ''
        return {
            'username': nickname,
            'email': kaccount_email,
            'fullname': nickname,
            'first_name': nickname[1:] if nickname else '',
            'last_name': nickname[0] if nickname else '',
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://kapi.kakao.com/v1/user/me',
            headers={
                'Authorization': 'Bearer {0}'.format(access_token),
                'Content_Type': 'application/x-www-form-urlencoded;charset=utf-8',
            },
            params={'access_token': access_token}
        )

    def auth_complete_params(self, state=None):
        return {
            'grant_type': 'authorization_code',
            'code': self.data.get('code', ''),
            'client_id': self.get_key_and_secret()[0],
        }
