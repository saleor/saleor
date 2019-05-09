"""
ExactTarget OAuth support.
Support Authentication from IMH using JWT token and pre-shared key.
Requires package pyjwt
"""
from datetime import timedelta, datetime

import jwt

from ..exceptions import AuthFailed, AuthCanceled
from .oauth import BaseOAuth2


class ExactTargetOAuth2(BaseOAuth2):
    name = 'exacttarget'

    def get_user_details(self, response):
        """Use the email address of the user, suffixed by _et"""
        user = response.get('token', {})\
                       .get('request', {})\
                       .get('user', {})
        if 'email' in user:
            user['username'] = user['email']
        return user

    def get_user_id(self, details, response):
        """
        Create a user ID from the ET user ID. Uses details rather than the
        default response, as only the token is available in response. details
        is much richer:
            {
                'expiresIn': 1200,
                'username': 'example@example.com',
                'refreshToken': '1234567890abcdef',
                'internalOauthToken': 'jwttoken.......',
                'oauthToken': 'yetanothertoken',
                'id': 123456,
                'culture': 'en-US',
                'timezone': {
                    'shortName': 'CST',
                    'offset': -6.0,
                    'dst': False,
                    'longName': '(GMT-06:00) Central Time (No Daylight Saving)'
                },
                'email': 'example@example.com'
            }
        """
        return '{0}'.format(details.get('id'))

    def uses_redirect(self):
        return False

    def auth_url(self):
        return None

    def process_error(self, data):
        if data.get('error'):
            error = self.data.get('error_description') or self.data['error']
            raise AuthFailed(self, error)

    def do_auth(self, token, *args, **kwargs):
        dummy, secret = self.get_key_and_secret()
        try:  # Decode the token, using the Application Signature from settings
            decoded = jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.DecodeError:  # Wrong signature, fail authentication
            raise AuthCanceled(self)
        kwargs.update({'response': {'token': decoded}, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        token = self.data.get('jwt', {})
        if not token:
            raise AuthFailed(self, 'Authentication Failed')
        return self.do_auth(token, *args, **kwargs)

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        """Load extra details from the JWT token"""
        data = {
            'id': details.get('id'),
            'email': details.get('email'),
            # OAuth token, for use with legacy SOAP API calls:
            #   http://bit.ly/13pRHfo
            'internalOauthToken': details.get('internalOauthToken'),
            # Token for use with the Application ClientID for the FUEL API
            'oauthToken': details.get('oauthToken'),
            # If the token has expired, use the FUEL API to get a new token see
            # http://bit.ly/10v1K5l and http://bit.ly/11IbI6F - set legacy=1
            'refreshToken': details.get('refreshToken'),
        }

        # The expiresIn value determines how long the tokens are valid for.
        # Take a bit off, then convert to an int timestamp
        expiresSeconds = details.get('expiresIn', 0) - 30
        expires = datetime.utcnow() + timedelta(seconds=expiresSeconds)
        data['expires'] = (expires - datetime(1970, 1, 1)).total_seconds()

        if response.get('token'):
            token = response['token']
            org = token.get('request', {}).get('organization')
            if org:
                data['stack'] = org.get('stackKey')
                data['enterpriseId'] = org.get('enterpriseId')
        return data
