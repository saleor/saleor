from .oauth import BaseOAuth2


class EchosignOAuth2(BaseOAuth2):
    name = 'echosign'
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_METHOD = 'POST'
    REVOKE_TOKEN_METHOD = 'POST'
    AUTHORIZATION_URL = 'https://secure.echosign.com/public/oauth'
    ACCESS_TOKEN_URL = 'https://secure.echosign.com/oauth/token'
    REFRESH_TOKEN_URL = 'https://secure.echosign.com/oauth/refresh'
    REVOKE_TOKEN_URL = 'https://secure.echosign.com/oauth/revoke'

    def get_user_details(self, response):
        return response

    def get_user_id(self, details, response):
        return details['userInfoList'][0]['userId']

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(
            'https://api.echosign.com/api/rest/v3/users',
            headers={'Access-Token': access_token})
