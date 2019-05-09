import base64
import json

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from jwt import DecodeError, ExpiredSignature, decode as jwt_decode

from ..exceptions import AuthTokenError
from .azuread import AzureADOAuth2

"""
Copyright (c) 2015 Microsoft Open Technologies, Inc.

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
"""

"""
Azure AD OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/azuread.html

See https://nicksnettravels.builttoroam.com/post/2017/01/24/Verifying-Azure-Active-Directory-JWT-Tokens.aspx
for verifying JWT tokens.
"""


class AzureADTenantOAuth2(AzureADOAuth2):
    name = 'azuread-tenant-oauth2'
    OPENID_CONFIGURATION_URL = \
        'https://login.microsoftonline.com/{tenant_id}/.well-known/openid-configuration'
    AUTHORIZATION_URL = \
        'https://login.microsoftonline.com/{tenant_id}/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://login.microsoftonline.com/{tenant_id}/oauth2/token'
    JWKS_URL = 'https://login.microsoftonline.com/{tenant_id}/discovery/keys'

    @property
    def tenant_id(self):
        return self.setting('TENANT_ID', 'common')

    def openid_configuration_url(self):
        return self.OPENID_CONFIGURATION_URL.format(tenant_id=self.tenant_id)

    def authorization_url(self):
        return self.AUTHORIZATION_URL.format(tenant_id=self.tenant_id)

    def access_token_url(self):
        return self.ACCESS_TOKEN_URL.format(tenant_id=self.tenant_id)

    def jwks_url(self):
        return self.JWKS_URL.format(tenant_id=self.tenant_id)

    def get_certificate(self, kid):
        # retrieve keys from jwks_url
        resp = self.request(self.jwks_url(), method='GET')
        resp.raise_for_status()

        # find the proper key for the kid
        for key in resp.json()['keys']:
            if key['kid'] == kid:
                x5c = key['x5c'][0]
                break
        else:
            raise DecodeError('Cannot find kid={}'.format(kid))

        certificate = '-----BEGIN CERTIFICATE-----\n' \
                      '{}\n' \
                      '-----END CERTIFICATE-----'.format(x5c)

        return load_pem_x509_certificate(certificate.encode(),
                                         default_backend())

    def get_user_id(self, details, response):
        """Use subject (sub) claim as unique id."""
        return response.get('sub')

    def user_data(self, access_token, *args, **kwargs):
        response = kwargs.get('response')
        id_token = response.get('id_token')

        # decode the JWT header as JSON dict
        jwt_header = json.loads(
            base64.b64decode(id_token.split('.', 1)[0]).decode()
        )

        # get key id and algorithm
        key_id = jwt_header['kid']
        algorithm = jwt_header['alg']

        try:
            # retrieve certificate for key_id
            certificate = self.get_certificate(key_id)

            return jwt_decode(
                id_token,
                key=certificate.public_key(),
                algorithms=algorithm,
                audience=self.setting('KEY')
            )
        except (DecodeError, ExpiredSignature) as error:
            raise AuthTokenError(self, error)
