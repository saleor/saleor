import json

from .oauth import OAuth2Test


class DripOAuthTest(OAuth2Test):
    backend_path = 'social_core.backends.drip.DripOAuth'
    user_data_url = 'https://api.getdrip.com/v2/user'
    expected_username = 'other@example.com'
    access_token_body = json.dumps({
        'access_token': '822bbf7cd12243df',
        'token_type': 'bearer',
        'scope': 'public'
    })

    user_data_body = json.dumps({
        'users': [
            {
                'email': 'other@example.com',
                'name': None
            }
        ]
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
