from .oauth import BaseOAuth2


class TAOBAOAuth(BaseOAuth2):
    """Taobao OAuth authentication mechanism"""
    name = 'taobao'
    ID_KEY = 'taobao_user_id'
    ACCESS_TOKEN_METHOD = 'POST'
    AUTHORIZATION_URL = 'https://oauth.taobao.com/authorize'
    ACCESS_TOKEN_URL = 'https://oauth.taobao.com/token'

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        try:
            return self.get_json('https://eco.taobao.com/router/rest', params={
                'method': 'taobao.user.get',
                'fomate': 'json',
                'v': '2.0',
                'access_token': access_token
            })
        except ValueError:
            return None

    def get_user_details(self, response):
        """Return user details from Taobao account"""
        return {'username': response.get('taobao_user_nick')}
