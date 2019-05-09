import json

from .oauth import OAuth2Test


class EdmodoOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.edmodo.EdmodoOAuth2'
    user_data_url = 'https://api.edmodo.com/users/me'
    expected_username = 'foobar12345'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'username': 'foobar12345',
        'coppa_verified': False,
        'first_name': 'Foo',
        'last_name': 'Bar',
        'premium': False,
        'verified_institution_member': False,
        'url': 'https://api.edmodo.com/users/12345',
        'type': 'teacher',
        'time_zone': None,
        'end_level': None,
        'start_level': None,
        'locale': 'en',
        'subjects': None,
        'utc_offset': None,
        'email': 'foo.bar@example.com',
        'gender': None,
        'about': None,
        'user_title': None,
        'id': 12345,
        'avatars': {
            'small': 'https://api.edmodo.com/users/12345/avatar?type=small&u=5a15xug93m53mi4ey3ck4fvkq',
            'large': 'https://api.edmodo.com/users/12345/avatar?type=large&u=5a15xug93m53mi4ey3ck4fvkq'
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
