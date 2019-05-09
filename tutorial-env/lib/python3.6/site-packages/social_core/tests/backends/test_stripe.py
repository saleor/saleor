import json

from .oauth import OAuth2Test


class StripeOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.stripe.StripeOAuth2'
    access_token_body = json.dumps({
        'stripe_publishable_key': 'pk_test_foobar',
        'access_token': 'foobar',
        'livemode': False,
        'token_type': 'bearer',
        'scope': 'read_only',
        'refresh_token': 'rt_foobar',
        'stripe_user_id': 'acct_foobar'
    })
    expected_username = 'acct_foobar'

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
