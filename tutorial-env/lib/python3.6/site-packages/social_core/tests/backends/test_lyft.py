import json

from .oauth import OAuth2Test


class LyftOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.lyft.LyftOAuth2'
    user_data_url = 'https://api.lyft.com/v1/profile'
    access_token_body = json.dumps({
        'access_token': 'atoken_foo',
        'refresh_token': 'rtoken_bar',
        'token_type': 'bearer',
        'expires_in': 3600,
        'scope': 'public profile rides.read rides.request',
        'id': 'user_foobar'
    })
    user_data_body = json.dumps({
        'id': 'user_foobar'
    })
    expected_username = 'user_foobar'

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
