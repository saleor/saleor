import json

from .oauth import OAuth2Test


class UniverseAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.universe.UniverseOAuth2'
    user_data_url = 'https://www.universe.com/api/v2/current_user'
    expected_username = 'scott+awesome@universe.com'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps(
        {
            'current_user': {
                'id': '123456',
                'slug': 'scott-vitale',
                'first_name': 'Scott',
                'last_name': 'Vitale',
                'created_at': '2019-01-08T15:49:42.514Z',
                'updated_at': '2019-01-17T19:41:39.711Z',
                'email': 'scott+awesome@universe.com',
            }
        }
    )

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
