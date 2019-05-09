# coding: utf-8
from __future__ import unicode_literals

import json

from .oauth import OAuth2Test


class VKOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.vk.VKOAuth2'
    user_data_url = 'https://api.vk.com/method/users.get'
    expected_username = 'durov'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'response': [{
            'uid': '1',
            'first_name': 'Павел',
            'last_name': 'Дуров',
            'screen_name': 'durov',
            'nickname': '',
            'photo': "http:\/\/cs7003.vk.me\/v7003815\/22a1\/xgG9fb-IJ3Y.jpg"
        }]
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
