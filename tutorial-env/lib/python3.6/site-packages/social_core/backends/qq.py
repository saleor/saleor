"""
Created on May 13, 2014

@author: Yong Zhang (zyfyfe@gmail.com)
"""

import json

from ..utils import parse_qs
from .oauth import BaseOAuth2


class QQOAuth2(BaseOAuth2):
    name = 'qq'
    ID_KEY = 'openid'
    AUTHORIZE_URL = 'https://graph.qq.com/oauth2.0/authorize'
    ACCESS_TOKEN_URL = 'https://graph.qq.com/oauth2.0/token'
    AUTHORIZATION_URL = 'https://graph.qq.com/oauth2.0/authorize'
    OPENID_URL = 'https://graph.qq.com/oauth2.0/me'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('nickname', 'username'),
        ('figureurl_qq_1', 'profile_image_url'),
        ('gender', 'gender')
    ]

    def get_user_details(self, response):
        """
        Return user detail from QQ account sometimes nickname will duplicate
        with another qq account, to avoid this issue it's possible to use
        openid as username.
        """
        if self.setting('USE_OPENID_AS_USERNAME', False):
            username = response.get('openid', '')
        else:
            username = response.get('nickname', '')

        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get('nickname', '')
        )

        return {
            'username': username,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def get_openid(self, access_token):
        response = self.request(self.OPENID_URL, params={
            'access_token': access_token
        })
        content = response.content.decode()
        data = json.loads(content[10:-3])
        return data['openid']

    def user_data(self, access_token, *args, **kwargs):
        openid = self.get_openid(access_token)
        response = self.get_json(
            'https://graph.qq.com/user/get_user_info', params={
                'access_token': access_token,
                'oauth_consumer_key': self.setting('KEY'),
                'openid': openid
            }
        )
        response['openid'] = openid
        return response

    def request_access_token(self, url, data, *args, **kwargs):
        response = self.request(url, *args, **kwargs)
        return parse_qs(response.content)
