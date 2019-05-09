import json

from .oauth import OAuth2Test


class ClefOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.clef.ClefOAuth2'
    user_data_url = 'https://clef.io/api/v1/info'
    expected_username = 'test'
    access_token_body = json.dumps({
        'access_token': 'foobar'
    })
    user_data_body = json.dumps({
        'info': {
            'id': '123456789',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com'
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
