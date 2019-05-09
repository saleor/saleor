import json

from .oauth import OAuth2Test


class LiveOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.live.LiveOAuth2'
    user_data_url = 'https://apis.live.net/v5.0/me'
    expected_username = 'FooBar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'first_name': 'Foo',
        'last_name': 'Bar',
        'name': 'Foo Bar',
        'locale': 'en_US',
        'gender': None,
        'emails': {
            'personal': None,
            'account': 'foobar@live.com',
            'business': None,
            'preferred': 'foobar@live.com'
        },
        'link': 'https://profile.live.com/',
        'updated_time': '2013-03-17T05:51:30+0000',
        'id': '1010101010101010'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
