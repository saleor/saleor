# -*- coding: utf-8 -*-
"""
Pinterest OAuth2 backend, docs at:
    https://developers.pinterest.com/docs/api/authentication/
"""

from __future__ import unicode_literals

import ssl

from .oauth import BaseOAuth2


class PinterestOAuth2(BaseOAuth2):
    name = 'pinterest'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = 'https://api.pinterest.com/oauth/'
    ACCESS_TOKEN_URL = 'https://api.pinterest.com/v1/oauth/token'
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'
    SSL_PROTOCOL = ssl.PROTOCOL_TLSv1

    def user_data(self, access_token, *args, **kwargs):
        response = self.get_json('https://api.pinterest.com/v1/me/',
                                 params={'access_token': access_token})

        if 'data' in response:
            username = response['data']['url'].strip('/').split('/')[-1]
            response = {
                'user_id': response['data']['id'],
                'first_name': response['data']['first_name'],
                'last_name': response['data']['last_name'],
                'username': username,
            }
        return response

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            first_name=response['first_name'],
            last_name=response['last_name'])

        return {'username': response.get('username'),
                'email': None,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}
