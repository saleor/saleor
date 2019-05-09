import json

from .oauth import OAuth2Test


class PodioOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.podio.PodioOAuth2'
    user_data_url = 'https://api.podio.com/user/status'
    expected_username = 'user_1010101010'
    access_token_body = json.dumps({
        'token_type': 'bearer',
        'access_token': '11309ea9016a4ad99f1a3bcb9bc7a9d1',
        'refresh_token': '52d01df8b9ac46a4a6be1333d9f81ef2',
        'expires_in': 28800,
        'ref': {
            'type': 'user',
            'id': 1010101010,
        }
    })
    user_data_body = json.dumps({
        'user': {
            'user_id': 1010101010,
            'activated_on': '2012-11-22 09:37:21',
            'created_on': '2012-11-21 12:23:47',
            'locale': 'en_GB',
            'timezone': 'Europe/Copenhagen',
            'mail': 'foo@bar.com',
            'mails': [
                {
                    'disabled': False,
                    'mail': 'foobar@example.com',
                    'primary': False,
                    'verified': True
                }, {
                    'disabled': False,
                    'mail': 'foo@bar.com',
                    'primary': True,
                    'verified': True
                }
            ],
            # more properties ...
        },
        'profile': {
            'last_seen_on': '2013-05-16 12:21:13',
            'link': 'https://podio.com/users/1010101010',
            'name': 'Foo Bar',
            # more properties ...
        }
        # more properties ...
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
