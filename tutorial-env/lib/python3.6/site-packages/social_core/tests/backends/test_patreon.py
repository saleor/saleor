import json

from .oauth import OAuth2Test


class PatreonOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.patreon.PatreonOAuth2'
    user_data_url = 'https://api.patreon.com/oauth2/api/current_user'
    expected_username = 'JohnInterwebs'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
    })
    user_data_body = json.dumps({
        "data": {
            "relationships": {
                "pledges": {
                    "data": [{
                        "type": "pledge", "id": "123456"
                    }]
                }
            },
            "attributes": {
                "last_name": "Interwebs",
                "is_suspended": False,
                "has_password": True,
                "full_name": "John Interwebs",
                "is_nuked": False,
                "first_name": "John",
                "social_connections": {
                    "spotify": None,
                    "discord": None,
                    "twitter": None,
                    "youtube": None,
                    "facebook": None,
                    "deviantart": None,
                    "twitch": None
                },
                "twitter": None,
                "is_email_verified": True,
                "facebook_id": None,
                "email": "john@example.com",
                "facebook": None,
                "thumb_url": "https://c8.patreon.com/100/123456",
                "vanity": None,
                "about": None,
                "is_deleted": False,
                "created": "2017-05-05T05:16:34+00:00",
                "url": "https://www.patreon.com/user?u=123456",
                "gender": 0,
                "youtube": None,
                "discord_id": None,
                "image_url": "https://c8.patreon.com/400/123456",
                "twitch": None
            },
            "type": "user",
            "id": "123456"
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
