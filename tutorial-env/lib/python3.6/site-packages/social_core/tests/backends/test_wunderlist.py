import json

from .oauth import OAuth2Test


class WunderlistOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.wunderlist.WunderlistOAuth2'
    user_data_url = 'https://a.wunderlist.com/api/v1/user'
    expected_username = '12345'
    access_token_body = json.dumps({
        'access_token': 'foobar-token',
        'token_type': 'foobar'})
    user_data_body = json.dumps({
        'created_at': '2015-01-21T00:56:51.442Z',
        'email': 'foo@bar.com',
        'id': 12345,
        'name': 'foobar',
        'revision': 1,
        'type': 'user',
        'updated_at': '2015-01-21T00:56:51.442Z'})

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
