import json

from .oauth import OAuth2Test


class StocktwitsOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.stocktwits.StocktwitsOAuth2'
    user_data_url = 'https://api.stocktwits.com/api/2/account/verify.json'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'response': {
            'status': 200
        },
        'user': {
            'username': 'foobar',
            'name': 'Foo Bar',
            'classification': [],
            'avatar_url': 'http://avatars.stocktwits.net/images/'
                          'default_avatar_thumb.jpg',
            'avatar_url_ssl': 'https://s3.amazonaws.com/st-avatars/images/'
                              'default_avatar_thumb.jpg',
            'id': 101010,
            'identity': 'User'
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class StocktwitsOAuth2UsernameAlternativeTest(StocktwitsOAuth2Test):
    user_data_body = json.dumps({
        'response': {
            'status': 200
        },
        'user': {
            'username': 'foobar',
            'name': 'Foobar',
            'classification': [],
            'avatar_url': 'http://avatars.stocktwits.net/images/'
                          'default_avatar_thumb.jpg',
            'avatar_url_ssl': 'https://s3.amazonaws.com/st-avatars/images/'
                              'default_avatar_thumb.jpg',
            'id': 101010,
            'identity': 'User'
        }
    })
