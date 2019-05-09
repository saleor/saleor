import base64

from .oauth import BaseOAuth2


class PushbulletOAuth2(BaseOAuth2):
    """pushbullet OAuth authentication backend"""
    name = 'pushbullet'
    EXTRA_DATA = [('id', 'id')]
    ID_KEY = 'username'
    AUTHORIZATION_URL = 'https://www.pushbullet.com/authorize'
    REQUEST_TOKEN_URL = 'https://api.pushbullet.com/oauth2/token'
    ACCESS_TOKEN_URL = 'https://api.pushbullet.com/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    STATE_PARAMETER = False

    def get_user_details(self, response):
        return {'username': response.get('access_token')}

    def get_user_id(self, details, response):
        auth = 'Basic {0}'.format(base64.b64encode(details['username']))
        return self.get_json('https://api.pushbullet.com/v2/users/me',
                             headers={'Authorization': auth})['iden']
