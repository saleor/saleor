import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class FitbitOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.fitbit.FitbitOAuth1'
    expected_username = 'foobar'
    access_token_body = urlencode({
        'oauth_token_secret': 'a-secret',
        'encoded_user_id': '101010',
        'oauth_token': 'foobar'
    })
    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })
    user_data_url = 'https://api.fitbit.com/1/user/-/profile.json'
    user_data_body = json.dumps({
        'user': {
            'weightUnit': 'en_US',
            'strideLengthWalking': 0,
            'displayName': 'foobar',
            'weight': 62.6,
            'foodsLocale': 'en_US',
            'heightUnit': 'en_US',
            'locale': 'en_US',
            'gender': 'NA',
            'memberSince': '2011-12-26',
            'offsetFromUTCMillis': -25200000,
            'height': 0,
            'timezone': 'America/Los_Angeles',
            'dateOfBirth': '',
            'encodedId': '101010',
            'avatar': 'http://www.fitbit.com/images/profile/'
                      'defaultProfile_100_male.gif',
            'waterUnit': 'en_US',
            'distanceUnit': 'en_US',
            'glucoseUnit': 'en_US',
            'strideLengthRunning': 0
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
