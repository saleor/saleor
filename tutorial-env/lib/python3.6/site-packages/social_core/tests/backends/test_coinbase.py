import json

from .oauth import OAuth2Test


class CoinbaseOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.coinbase.CoinbaseOAuth2'
    user_data_url = 'https://api.coinbase.com/v2/user'
    expected_username = 'satoshi_nakomoto'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        "data": {
            "id": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            'name': "Satoshi Nakamoto",
            "username": "satoshi_nakomoto",
            "profile_location": None,
            "profile_bio": None,
            "profile_url": "https://coinbase.com/satoshi_nakomoto",
            "avatar_url": None,
            "resource": "user",
            "resource_path": "/v2/user"
          }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
