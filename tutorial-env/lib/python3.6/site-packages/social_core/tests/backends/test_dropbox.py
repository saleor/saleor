import json

from six.moves.urllib_parse import urlencode

from .oauth import OAuth1Test


class DropboxOAuth1Test(OAuth1Test):
    backend_path = 'social_core.backends.dropbox.DropboxOAuth'
    user_data_url = 'https://api.dropbox.com/1/account/info'
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
        'referral_link': 'https://www.dropbox.com/referrals/foobar',
        'display_name': 'Foo Bar',
        'uid': 10101010,
        'country': 'US',
        'quota_info': {
            'shared': 138573,
            'quota': 2952790016,
            'normal': 157327
        },
        'email': 'foo@bar.com'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
