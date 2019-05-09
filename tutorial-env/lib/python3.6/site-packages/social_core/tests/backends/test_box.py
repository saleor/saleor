import json

from .oauth import OAuth2Test


class BoxOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.box.BoxOAuth2'
    user_data_url = 'https://api.box.com/2.0/users/me'
    expected_username = 'sean+awesome@box.com'
    access_token_body = json.dumps({
        'access_token': 'T9cE5asGnuyYCCqIZFoWjFHvNbvVqHjl',
        'expires_in': 3600,
        'restricted_to': [],
        'token_type': 'bearer',
        'refresh_token': 'J7rxTiWOHMoSC1isKZKBZWizoRXjkQzig5C6jFgCVJ9bU'
                         'nsUfGMinKBDLZWP9BgR'
    })
    user_data_body = json.dumps({
        'type': 'user',
        'id': '181216415',
        'name': 'sean rose',
        'login': 'sean+awesome@box.com',
        'created_at': '2012-05-03T21:39:11-07:00',
        'modified_at': '2012-11-14T11:21:32-08:00',
        'role': 'admin',
        'language': 'en',
        'space_amount': 11345156112,
        'space_used': 1237009912,
        'max_upload_size': 2147483648,
        'tracking_codes': [],
        'can_see_managed_users': True,
        'is_sync_enabled': True,
        'status': 'active',
        'job_title': '',
        'phone': '6509241374',
        'address': '',
        'avatar_url': 'https://www.box.com/api/avatar/large/181216415',
        'is_exempt_from_device_limits': False,
        'is_exempt_from_login_verification': False,
        'enterprise': {
            'type': 'enterprise',
            'id': '17077211',
            'name': 'seanrose enterprise'
        }
    })
    refresh_token_body = json.dumps({
        'access_token': 'T9cE5asGnuyYCCqIZFoWjFHvNbvVqHjl',
        'expires_in': 3600,
        'restricted_to': [],
        'token_type': 'bearer',
        'refresh_token': 'J7rxTiWOHMoSC1isKZKBZWizoRXjkQzig5C6jFgCVJ9b'
                         'UnsUfGMinKBDLZWP9BgR'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def refresh_token_arguments(self):
        uri = self.strategy.build_absolute_uri('/complete/box/')
        return {'redirect_uri': uri}

    def test_refresh_token(self):
        user, social = self.do_refresh_token()
        self.assertEqual(social.extra_data['access_token'],
                         'T9cE5asGnuyYCCqIZFoWjFHvNbvVqHjl')
