# -*- coding: utf-8 -*-
"""
Professionaly OAuth 2.0 support.

This contribution adds support for professionaly.ru OAuth 2.0.
Username is retrieved from the identity returned by server.
"""
from time import time

from ..utils import parse_qs
from .oauth import BaseOAuth2


class ProfessionaliOAuth2(BaseOAuth2):
    name = 'professionali'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = 'https://api.professionali.ru/oauth/authorize.html'
    ACCESS_TOKEN_URL = 'https://api.professionali.ru/oauth/getToken.json'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('avatar_big', 'avatar_big'),
        ('link', 'link')
    ]

    def get_user_details(self, response):
        first_name, last_name = map(response.get, ('firstname', 'lastname'))
        email = ''
        if self.setting('FAKE_EMAIL'):
            email = '{0}@professionali.ru'.format(time())
        return {
            'username': '{0}_{1}'.format(last_name, first_name),
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }

    def user_data(self, access_token, response, *args, **kwargs):
        url = 'https://api.professionali.ru/v6/users/get.json'
        fields = list(set(['firstname', 'lastname', 'avatar_big', 'link'] +
                          self.setting('EXTRA_DATA', [])))
        params = {
            'fields': ','.join(fields),
            'access_token': access_token,
            'ids[]': response['user_id']
        }
        try:
            return self.get_json(url, params)[0]
        except (TypeError, KeyError, IOError, ValueError, IndexError):
            return None

    def get_json(self, url, *args, **kwargs):
        return self.request(url, verify=False, *args, **kwargs).json()

    def get_querystring(self, url, *args, **kwargs):
        return parse_qs(self.request(url, verify=False, *args, **kwargs).text)
