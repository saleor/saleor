import json
import requests
from httpretty import HTTPretty

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class YahooOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.yahoo.YahooOAuth'
    user_data_url = 'https://social.yahooapis.com/v1/user/a-guid/profile?' \
                    'format=json'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })
    guid_body = json.dumps({
        'guid': {
            'uri': 'https://social.yahooapis.com/v1/me/guid',
            'value': 'a-guid'
        }
    })
    user_data_body = json.dumps({
        'profile': {
            'bdRestricted': True,
            'memberSince': '2007-12-11T14:40:30Z',
            'image': {
                'width': 192,
                'imageUrl': 'http://l.yimg.com/dh/ap/social/profile/'
                            'profile_b192.png',
                'size': '192x192',
                'height': 192
            },
            'created': '2013-03-18T04:15:08Z',
            'uri': 'https://social.yahooapis.com/v1/user/a-guid/profile',
            'isConnected': False,
            'profileUrl': 'http://profile.yahoo.com/a-guid',
            'guid': 'a-guid',
            'nickname': 'foobar',
            'emails': [{
                'handle': 'foobar@yahoo.com',
                'id': 1,
                'primary': True,
                'type': 'HOME',
            }, {
                'handle': 'foobar@email.com',
                'id': 2,
                'type': 'HOME',
            }],
        }
    })

    def test_login(self):
        HTTPretty.register_uri(
            HTTPretty.GET,
            'https://social.yahooapis.com/v1/me/guid?format=json',
            status=200,
            body=self.guid_body
        )
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def test_get_user_details(self):
        HTTPretty.register_uri(
            HTTPretty.GET,
            self.user_data_url,
            status=200,
            body=self.user_data_body
        )
        response = requests.get(self.user_data_url)
        user_details = self.backend.get_user_details(
            response.json()['profile']
        )
        self.assertEqual(user_details['email'], 'foobar@yahoo.com')
