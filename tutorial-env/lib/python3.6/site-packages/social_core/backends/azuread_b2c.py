"""
Copyright (c) 2018 Noderabbit Inc., d.b.a. Appsembler

All rights reserved.

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

See https://nicksnettravels.builttoroam.com/post/2017/01/24/Verifying-Azure-Active-Directory-JWT-Tokens.aspx
    for verifying JWT tokens.
"""

import json
import six

from cryptography.hazmat.primitives import serialization
from jwt import DecodeError, ExpiredSignature, decode as jwt_decode
from jwt.utils import base64url_decode


try:
    from jwt.algorithms import RSAAlgorithm
except ImportError as e:
    raise Exception(
        # Python 3.3 is not supported because of compatibility in
        # Cryptography package in Python3.3 You are welcome to patch
        # and open a pull request.
        'Cryptography library is required for this backend ' \
        '(AzureADB2COAuth2) to work. Note that this backend is only ' \
        'supported on Python 2 and Python 3.4+.'
    )

from ..exceptions import AuthException, AuthTokenError
from .azuread import AzureADOAuth2


class AzureADB2COAuth2(AzureADOAuth2):
    name = 'azuread-b2c-oauth2'

    BASE_URL = 'https://login.microsoftonline.com/{tenant_id}'
    AUTHORIZATION_URL = '{base_url}/oauth2/v2.0/authorize'
    OPENID_CONFIGURATION_URL = '{base_url}/v2.0/.well-known/openid-configuration?p={policy}'
    ACCESS_TOKEN_URL = '{base_url}/oauth2/v2.0/token?p={policy}'
    JWKS_URL = '{base_url}/discovery/v2.0/keys?p={policy}'
    DEFAULT_SCOPE = ['openid', 'email']
    EXTRA_DATA = [
        ('access_token', 'access_token'),
        ('id_token', 'id_token'),
        ('refresh_token', 'refresh_token'),
        ('id_token_expires_in', 'expires'),
        ('exp', 'expires_on'),
        ('not_before', 'not_before'),
        ('given_name', 'first_name'),
        ('family_name', 'last_name'),
        ('tfp', 'policy'),
        ('token_type', 'token_type')
    ]

    @property
    def tenant_id(self):
        return self.setting('TENANT_ID', 'common')

    @property
    def policy(self):
        policy = self.setting('POLICY')
        if not policy or not policy.lower().startswith('b2c_'):
            raise AuthException('SOCIAL_AUTH_AZUREAD_B2C_OAUTH2_POLICY is '
                                'required and should start with `b2c_`')
        return policy

    @property
    def base_url(self):
        return self.BASE_URL.format(tenant_id=self.tenant_id)

    def openid_configuration_url(self):
        return self.OPENID_CONFIGURATION_URL.format(base_url=self.base_url,
                                                    policy=self.policy)

    def authorization_url(self):
        # Policy is required, but added later by `auth_extra_arguments()`
        return self.AUTHORIZATION_URL.format(base_url=self.base_url)

    def access_token_url(self):
        return self.ACCESS_TOKEN_URL.format(base_url=self.base_url,
                                            policy=self.policy)

    def jwks_url(self):
        return self.JWKS_URL.format(base_url=self.base_url,
                                    policy=self.policy)

    def request_access_token(self, *args, **kwargs):
        """
        This is probably a hack, but otherwise AzureADOAuth2 expects
        `access_token`.

        However, B2C backends provides `id_token`.
        """
        response = super(AzureADB2COAuth2, self).request_access_token(
            *args,
            **kwargs
        )
        if 'access_token' not in response:
            response['access_token'] = response['id_token']
        return response

    def auth_extra_arguments(self):
        """
        Return extra arguments needed on auth process.

        The defaults can be overridden by GET parameters.
        """
        extra_arguments = super(AzureADB2COAuth2, self).auth_extra_arguments()
        extra_arguments['p'] = self.policy or self.data.get('p')
        return extra_arguments

    def jwt_key_to_pem(self, key_json_dict):
        """
        Builds a PEM formatted key string from a JWT public key dict.
        """
        pub_key = RSAAlgorithm.from_jwk(json.dumps(key_json_dict))
        return pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def get_user_id(self, details, response):
        """Use subject (sub) claim as unique id."""
        return response.get('sub')

    def get_user_details(self, response):
        """
        Email address is returned on a different attribute for AzureAD
        B2C backends.
        """
        details = super(AzureADB2COAuth2, self).get_user_details(response)
        if not details['email'] and response.get('emails'):
            details['email'] = response['emails']
        if isinstance(details.get('email'), (list, tuple)):
            details['email'] = details['email'][0]
        return details

    def get_public_key(self, kid):
        """
        Retrieve JWT keys from the URL.
        """
        resp = self.request(self.jwks_url(), method='GET')
        resp.raise_for_status()

        # find the proper key for the kid
        for key in resp.json()['keys']:
            if key['kid'] == kid:
                return self.jwt_key_to_pem(key)
        raise DecodeError('Cannot find kid={}'.format(kid))

    def user_data(self, access_token, *args, **kwargs):
        response = kwargs.get('response')

        id_token = response.get('id_token')
        if six.PY2:
            # str() to fix a bug in Python's base64
            # https://stackoverflow.com/a/2230623/161278
            id_token = str(id_token)

        jwt_header_json = base64url_decode(id_token.split('.')[0])
        jwt_header = json.loads(jwt_header_json.decode('ascii'))

        # `kid` is short for key id
        key = self.get_public_key(jwt_header['kid'])

        try:
            return jwt_decode(
                id_token,
                key=key,
                algorithms=jwt_header['alg'],
                audience=self.setting('KEY'),
                leeway=self.setting('JWT_LEEWAY', default=0),
            )
        except (DecodeError, ExpiredSignature) as error:
            raise AuthTokenError(self, error)
