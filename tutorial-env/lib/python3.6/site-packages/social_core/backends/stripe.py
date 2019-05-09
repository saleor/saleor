"""
Stripe OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/stripe.html
"""
from .oauth import BaseOAuth2


class StripeOAuth2(BaseOAuth2):
    """Stripe OAuth2 authentication backend"""
    name = 'stripe'
    ID_KEY = 'stripe_user_id'
    AUTHORIZATION_URL = 'https://connect.stripe.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://connect.stripe.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('stripe_publishable_key', 'stripe_publishable_key'),
        ('access_token', 'access_token'),
        ('livemode', 'livemode'),
        ('token_type', 'token_type'),
        ('refresh_token', 'refresh_token'),
        ('stripe_user_id', 'stripe_user_id'),
    ]

    def get_user_details(self, response):
        """Return user details from Stripe account"""
        return {'username': response.get('stripe_user_id'),
                'email': ''}

    def auth_complete_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'scope': self.SCOPE_SEPARATOR.join(self.get_scope()),
            'code': self.data['code']
        }

    def auth_headers(self):
        client_id, client_secret = self.get_key_and_secret()
        return {'Accept': 'application/json',
                'Authorization': 'Bearer {0}'.format(client_secret)}

    def refresh_token_params(self, refresh_token, *args, **kwargs):
        return {'refresh_token': refresh_token,
                'grant_type': 'refresh_token'}
