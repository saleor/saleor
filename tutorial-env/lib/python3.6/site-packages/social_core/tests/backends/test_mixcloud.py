import json

from .oauth import OAuth2Test


class MixcloudOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.mixcloud.MixcloudOAuth2'
    user_data_url = 'https://api.mixcloud.com/me/'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'username': 'foobar',
        'cloudcast_count': 0,
        'following_count': 0,
        'url': 'http://www.mixcloud.com/foobar/',
        'pictures': {
            'medium': 'http://images-mix.netdna-ssl.com/w/100/h/100/q/85/'
                      'images/graphics/33_Profile/default_user_600x600-v4.png',
            '320wx320h': 'http://images-mix.netdna-ssl.com/w/320/h/320/q/85/'
                         'images/graphics/33_Profile/'
                         'default_user_600x600-v4.png',
            'extra_large': 'http://images-mix.netdna-ssl.com/w/600/h/600/q/85/'
                           'images/graphics/33_Profile/'
                           'default_user_600x600-v4.png',
            'large': 'http://images-mix.netdna-ssl.com/w/300/h/300/q/85/'
                     'images/graphics/33_Profile/default_user_600x600-v4.png',
            '640wx640h': 'http://images-mix.netdna-ssl.com/w/640/h/640/q/85/'
                         'images/graphics/33_Profile/'
                         'default_user_600x600-v4.png',
            'medium_mobile': 'http://images-mix.netdna-ssl.com/w/80/h/80/q/75/'
                             'images/graphics/33_Profile/'
                             'default_user_600x600-v4.png',
            'small': 'http://images-mix.netdna-ssl.com/w/25/h/25/q/85/images/'
                     'graphics/33_Profile/default_user_600x600-v4.png',
            'thumbnail': 'http://images-mix.netdna-ssl.com/w/50/h/50/q/85/'
                         'images/graphics/33_Profile/'
                         'default_user_600x600-v4.png'
        },
        'is_current_user': True,
        'listen_count': 0,
        'updated_time': '2013-03-17T06:26:31Z',
        'following': False,
        'follower': False,
        'key': '/foobar/',
        'created_time': '2013-03-17T06:26:31Z',
        'follower_count': 0,
        'favorite_count': 0,
        'name': 'foobar'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
