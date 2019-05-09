import json

from .oauth import OAuth2Test


class AsanaOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.asana.AsanaOAuth2'
    user_data_url = 'https://app.asana.com/api/1.0/users/me'
    expected_username = 'erlich@bachmanity.com'
    access_token_body = json.dumps({
        'access_token': 'aviato',
        'token_type': 'bearer'
    })
    # https://asana.com/developers/api-reference/users
    user_data_body = json.dumps({
        'data': {
            'id': 12345,
            'name': 'Erlich Bachman',
            'email': 'erlich@bachmanity.com',
            'photo': None,
            'workspaces': [
                {
                    'id': 123456,
                    'name': 'Pied Piper'
                }
            ]
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
