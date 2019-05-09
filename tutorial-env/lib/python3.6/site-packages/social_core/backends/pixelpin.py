import json
from .open_id_connect import OpenIdConnectAuth


class PixelPinOpenIDConnect(OpenIdConnectAuth):
    """PixelPin OpenID Connect authentication backend"""
    name = 'pixelpin-openidconnect'
    ID_KEY = 'sub'
    AUTHORIZATION_URL = 'https://login.pixelpin.io/connect/authorize'
    ACCESS_TOKEN_URL = 'https://login.pixelpin.io/connect/token'
    OIDC_ENDPOINT = 'https://login.pixelpin.io'
    JWKS_URI = 'https://login.pixelpin.io/.well-known/jwks'
    ACCESS_TOKEN_METHOD = 'POST'
    REQUIRES_EMAIL_VALIDATION = False

    def get_user_details(self, response):
        """Return user details from PixelPin account"""
        first_name = response.get('given_name')
        last_name = response.get('family_name')
        sub = response.get('sub')

        username = first_name + last_name + sub

        return {'username': username,
                'email': response.get('email'),
                'fullname': first_name + ' ' + last_name,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(
            'https://login.pixelpin.io/connect/userinfo',
            headers={
                'Authorization': 'Bearer {0}'.format(access_token)
            }
        )
