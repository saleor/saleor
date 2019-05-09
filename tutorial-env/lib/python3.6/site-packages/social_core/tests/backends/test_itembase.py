import json

from .oauth import OAuth2Test


class ItembaseOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.itembase.ItembaseOAuth2'
    user_data_url = 'https://users.itembase.com/v1/me'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        "access_token": "foobar-token",
        "expires_in": 2592000,
        "token_type": "bearer",
        "scope": "user.minimal",
        "refresh_token": "foobar-refresh-token"
    })
    user_data_body = json.dumps({
        "uuid": "a4b91ee7-ec1a-49b9-afce-371dc8797749",
        "username": "foobar",
        "email": "foobar@itembase.biz",
        "first_name": "Foo",
        "middle_name": None,
        "last_name": "Bar",
        "name_format": "first middle last",
        "locale": "en",
        "preferred_currency": "EUR"
    })
    refresh_token_body = json.dumps({
        "access_token": "foobar-new-token",
        "expires_in": 2592000,
        "token_type": "bearer",
        "scope": "user.minimal",
        "refresh_token": "foobar-new-refresh-token"
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class ItembaseOAuth2SandboxTest(OAuth2Test):
    backend_path = 'social_core.backends.itembase.ItembaseOAuth2Sandbox'
    user_data_url = 'http://sandbox.users.itembase.io/v1/me'
