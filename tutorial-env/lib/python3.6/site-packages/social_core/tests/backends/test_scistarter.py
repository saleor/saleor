import json

from httpretty import HTTPretty

from ...exceptions import AuthFailed
from .oauth import OAuth2Test


class ScistarterOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.scistarter.SciStarterOAuth2'
    user_data_url = 'https://scistarter.com/api/user_info'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'profile_id': 42006,
        'user_id': 5,
        'url': 'https://scistarter.com/user/foobar',
        'result': 'success',
        'handle': 'foobar',
        'email': 'foo@bar.com',
        'first_name': 'foo',
        'last_name': 'bar'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
