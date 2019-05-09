import json

from .oauth import OAuth2Test


class SketchfabOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.sketchfab.SketchfabOAuth2'
    user_data_url = 'https://sketchfab.com/v2/users/me'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'uid': '42',
        'email': 'foo@bar.com',
        'displayName': 'foo bar',
        'username': 'foobar',
        'apiToken': 'XXX'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
