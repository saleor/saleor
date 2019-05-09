import json

from .oauth import OAuth2Test


class PinterestOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.pinterest.PinterestOAuth2'
    user_data_url = 'https://api.pinterest.com/v1/me/'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'id': '4788400174839062',
        'first_name': 'Foo',
        'last_name': 'Bar',
        'username': 'foobar',
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class PinterestOAuth2BrokenServerResponseTest(OAuth2Test):
    backend_path = 'social_core.backends.pinterest.PinterestOAuth2'
    user_data_url = 'https://api.pinterest.com/v1/me/'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'data': {
            'id': '4788400174839062',
            'first_name': 'Foo',
            'last_name': 'Bar',
            'url': 'https://www.pinterest.com/foobar/',
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
