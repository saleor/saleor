import json

from .oauth import OAuth2Test


class EventbriteAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.eventbrite.EventbriteOAuth2'
    user_data_url = 'https://www.eventbriteapi.com/v3/users/me'
    expected_username = 'sean+awesome@eventbrite.com'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'first_name': 'sean',
        'last_name': 'rose',
        'name': 'sean rose',
        'access_token': 'YQEN5H2W2OTKQZWZMYER',
        'emails': [
            {
                'verified': True,
                'email': 'sean+awesome2@eventbrite.com',
                'primary': False,
            },
            {
                'verified': True,
                'email': 'sean+awesome@eventbrite.com',
                'primary': True,
            },
        ],
        'token_type': 'bearer',
        'image_id': None,
        'is_public': False,
        'id': '128559602587',
    })

    def test_login(self):
        self.do_login()
