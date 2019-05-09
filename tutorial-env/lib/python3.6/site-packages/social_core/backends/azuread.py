import time

from jwt import DecodeError, ExpiredSignature, decode as jwt_decode

from ..exceptions import AuthTokenError
from .oauth import BaseOAuth2

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
"""


class AzureADOAuth2(BaseOAuth2):
    name = 'azuread-oauth2'
    SCOPE_SEPARATOR = ' '
    AUTHORIZATION_URL = \
        'https://login.microsoftonline.com/common/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://login.microsoftonline.com/common/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    DEFAULT_SCOPE = ['openid', 'profile', 'user_impersonation']
    EXTRA_DATA = [
        ('access_token', 'access_token'),
        ('id_token', 'id_token'),
        ('refresh_token', 'refresh_token'),
        ('expires_in', 'expires'),
        ('expires_on', 'expires_on'),
        ('not_before', 'not_before'),
        ('given_name', 'first_name'),
        ('family_name', 'last_name'),
        ('token_type', 'token_type')
    ]

    def get_user_id(self, details, response):
        """Use upn as unique id"""
        return response.get('upn')

    def get_user_details(self, response):
        """Return user details from Azure AD account"""
        fullname, first_name, last_name = (
            response.get('name', ''),
            response.get('given_name', ''),
            response.get('family_name', '')
        )
        return {'username': fullname,
                'email': response.get('upn'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        response = kwargs.get('response')
        if response and response.get('id_token'):
            id_token = response.get('id_token')
        else:
            id_token = access_token
            
        try:
            decoded_id_token = jwt_decode(id_token, verify=False)
        except (DecodeError, ExpiredSignature) as de:
            raise AuthTokenError(self, de)
        return decoded_id_token

    def auth_extra_arguments(self):
        """Return extra arguments needed on auth process. The defaults can be
        overriden by GET parameters."""
        extra_arguments = super(AzureADOAuth2, self).auth_extra_arguments()
        resource = self.setting('RESOURCE')
        if resource:
            extra_arguments.update({'resource': resource})
        return extra_arguments

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        """Return access_token and extra defined names to store in
        extra_data field"""
        data = super(AzureADOAuth2, self).extra_data(user, uid, response,
            details, *args, **kwargs)
        data['resource'] = self.setting('RESOURCE')
        return data

    def refresh_token_params(self, token, *args, **kwargs):
        return {
            'client_id': self.setting('KEY'),
            'client_secret': self.setting('SECRET'),
            'refresh_token': token,
            'grant_type': 'refresh_token',
            'resource': self.setting('RESOURCE')
        }

    def get_auth_token(self, user_id):
        """Return the access token for the given user, after ensuring that it
        has not expired, or refreshing it if so."""
        user = self.get_user(user_id=user_id)
        access_token = user.social_user.access_token
        expires_on = user.social_user.extra_data['expires_on']
        if expires_on <= int(time.time()):
            new_token_response = self.refresh_token(token=access_token)
            access_token = new_token_response['access_token']
        return access_token
