import json

from .oauth import OAuth2Test


class DigitalOceanOAuthTest(OAuth2Test):
    backend_path = 'social_core.backends.digitalocean.DigitalOceanOAuth'
    user_data_url = 'https://api.digitalocean.com/v2/account'
    expected_username = 'sammy@digitalocean.com'
    access_token_body = json.dumps({
        'access_token': '547cac21118ae7',
        'token_type': 'bearer',
        'expires_in': 2592000,
        'refresh_token': '00a3aae641658d',
        'scope': 'read write',
        'info': {
            'name': 'Sammy Shark',
            'email': 'sammy@digitalocean.com'
        }
    })
    user_data_body = json.dumps({
        "account": {
            'droplet_limit': 25,
            'email': 'sammy@digitalocean.com',
            'uuid': 'b6fr89dbf6d9156cace5f3c78dc9851d957381ef',
            'email_verified': True
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
