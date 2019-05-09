import json

from httpretty import HTTPretty

from six.moves.urllib_parse import urlencode

from ...exceptions import AuthForbidden
from .oauth import OAuth1Test, OAuth2Test


class UberOAuth2Test(OAuth2Test):
    user_data_url = 'https://api.uber.com/v1/me'
    backend_path = 'social_core.backends.uber.UberOAuth2'
    expected_username = 'foo@bar.com'

    user_data_body = json.dumps({
        "first_name": "Foo",
        "last_name": "Bar",
        "email": "foo@bar.com",
        "picture": "https://",
        "promo_code": "barfoo",
        "uuid": "91d81273-45c2-4b57-8124-d0165f8240c0"
    })

    access_token_body = json.dumps({
        "access_token": "EE1IDxytP04tJ767GbjH7ED9PpGmYvL",
        "token_type": "Bearer",
        "expires_in": 2592000,
        "refresh_token": "Zx8fJ8qdSRRseIVlsGgtgQ4wnZBehr",
        "scope": "profile history request"
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
