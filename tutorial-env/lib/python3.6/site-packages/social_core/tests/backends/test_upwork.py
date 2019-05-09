import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class UpworkOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.upwork.UpworkOAuth'
    user_data_url = 'https://www.upwork.com/api/auth/v1/info.json'
    expected_username = '10101010'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })
    user_data_body = json.dumps({
        'info': {
            'portrait_32_img': '',
            'capacity': {
                'buyer': 'no',
                'affiliate_manager': 'no',
                'provider': 'yes'
            },
            'company_url': '',
            'has_agency': '1',
            'portrait_50_img': '',
            'portrait_100_img': '',
            'location': {
                'city': 'New York',
                'state': '',
                'country': 'USA'
            },
            'ref': '9755314',
            'profile_url': 'https://www.upwork.com/users/~10101010'
        },
        'auth_user': {
            'timezone': 'USA/New York',
            'first_name': 'Foo',
            'last_name': 'Bar',
            'timezone_offset': '10000'
        },
        'server_time': '1111111111'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
