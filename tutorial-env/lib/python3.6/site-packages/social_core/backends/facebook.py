"""
Facebook OAuth2 and Canvas Application backends, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/facebook.html
"""
import hmac
import time
import json
import base64
import hashlib

from ..utils import parse_qs, constant_time_compare, handle_http_errors
from .oauth import BaseOAuth2
from ..exceptions import AuthException, AuthCanceled, AuthUnknownError, \
                         AuthMissingParameter


API_VERSION = 2.9


class FacebookOAuth2(BaseOAuth2):
    """Facebook OAuth2 authentication backend"""
    name = 'facebook'
    REDIRECT_STATE = False
    RESPONSE_TYPE = None
    SCOPE_SEPARATOR = ','
    AUTHORIZATION_URL = 'https://www.facebook.com/v{version}/dialog/oauth'
    ACCESS_TOKEN_URL = \
        'https://graph.facebook.com/v{version}/oauth/access_token'
    REVOKE_TOKEN_URL = \
        'https://graph.facebook.com/v{version}/{uid}/permissions'
    REVOKE_TOKEN_METHOD = 'DELETE'
    USER_DATA_URL = 'https://graph.facebook.com/v{version}/me'
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires'),
        ('granted_scopes', 'granted_scopes'),
        ('denied_scopes', 'denied_scopes')
    ]

    def auth_params(self, state=None):
        params = super(FacebookOAuth2, self).auth_params(state)
        params['return_scopes'] = 'true'
        return params

    def authorization_url(self):
        version = self.setting('API_VERSION', API_VERSION)
        return self.AUTHORIZATION_URL.format(version=version)

    def access_token_url(self):
        version = self.setting('API_VERSION', API_VERSION)
        return self.ACCESS_TOKEN_URL.format(version=version)

    def get_user_details(self, response):
        """Return user details from Facebook account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name', ''),
            response.get('first_name', ''),
            response.get('last_name', '')
        )
        return {'username': response.get('username', response.get('name')),
                'email': response.get('email', ''),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        params = self.setting('PROFILE_EXTRA_PARAMS', {})
        params['access_token'] = access_token

        if self.setting('APPSECRET_PROOF', True):
            _, secret = self.get_key_and_secret()
            params['appsecret_proof'] = hmac.new(
                secret.encode('utf8'),
                msg=access_token.encode('utf8'),
                digestmod=hashlib.sha256
            ).hexdigest()

        version = self.setting('API_VERSION', API_VERSION)
        return self.get_json(self.USER_DATA_URL.format(version=version),
                             params=params)

    def process_error(self, data):
        super(FacebookOAuth2, self).process_error(data)
        if data.get('error_code'):
            raise AuthCanceled(self, data.get('error_message') or
                                     data.get('error_code'))

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        if not self.data.get('code'):
            raise AuthMissingParameter(self, 'code')
        state = self.validate_state()
        key, secret = self.get_key_and_secret()
        response = self.request(self.access_token_url(), params={
            'client_id': key,
            'redirect_uri': self.get_redirect_uri(state),
            'client_secret': secret,
            'code': self.data['code']
        })
        # API v2.3 returns a JSON, according to the documents linked at issue
        # #592, but it seems that this needs to be enabled(?), otherwise the
        # usual querystring type response is returned.
        try:
            response = response.json()
        except ValueError:
            response = parse_qs(response.text)
        access_token = response['access_token']
        return self.do_auth(access_token, response, *args, **kwargs)

    def process_refresh_token_response(self, response, *args, **kwargs):
        try:
            return response.json()
        except ValueError:
            return parse_qs(response.content)

    def refresh_token_params(self, token, *args, **kwargs):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'fb_exchange_token': token,
            'grant_type': 'fb_exchange_token',
            'client_id': client_id,
            'client_secret': client_secret
        }

    def do_auth(self, access_token, response=None, *args, **kwargs):
        response = response or {}

        data = self.user_data(access_token)

        if not isinstance(data, dict):
            # From time to time Facebook responds back a JSON with just
            # False as value, the reason is still unknown, but since the
            # data is needed (it contains the user ID used to identify the
            # account on further logins), this app cannot allow it to
            # continue with the auth process.
            raise AuthUnknownError(self, 'An error ocurred while retrieving '
                                         'users Facebook data')

        data['access_token'] = access_token
        if 'expires_in' in response:
            data['expires'] = response['expires_in']

        if self.data.get('granted_scopes'):
            data['granted_scopes'] = self.data['granted_scopes'].split(',')

        if self.data.get('denied_scopes'):
            data['denied_scopes'] = self.data['denied_scopes'].split(',')

        kwargs.update({'backend': self, 'response': data})
        return self.strategy.authenticate(*args, **kwargs)

    def revoke_token_url(self, token, uid):
        version = self.setting('API_VERSION', API_VERSION)
        return self.REVOKE_TOKEN_URL.format(version=version, uid=uid)

    def revoke_token_params(self, token, uid):
        return {'access_token': token}

    def process_revoke_token_response(self, response):
        return super(FacebookOAuth2, self).process_revoke_token_response(
            response
        ) and response.content == 'true'


class FacebookAppOAuth2(FacebookOAuth2):
    """Facebook Application Authentication support"""
    name = 'facebook-app'

    def uses_redirect(self):
        return False

    def auth_complete(self, *args, **kwargs):
        access_token = self.data.get('access_token')
        response = {}

        if 'signed_request' in self.data:
            key, secret = self.get_key_and_secret()
            response = self.load_signed_request(self.data['signed_request'])
            if 'user_id' not in response and 'oauth_token' not in response:
                raise AuthException(self)

            if response is not None:
                access_token = response.get('access_token') or \
                               response.get('oauth_token') or \
                               self.data.get('access_token')

        if access_token is None:
            if self.data.get('error') == 'access_denied':
                raise AuthCanceled(self)
            else:
                raise AuthException(self)
        return self.do_auth(access_token, response, *args, **kwargs)

    def auth_html(self):
        key, secret = self.get_key_and_secret()
        namespace = self.setting('NAMESPACE', None)
        scope = self.setting('SCOPE', '')
        if scope:
            scope = self.SCOPE_SEPARATOR.join(scope)
        ctx = {
            'FACEBOOK_APP_NAMESPACE': namespace or key,
            'FACEBOOK_KEY': key,
            'FACEBOOK_EXTENDED_PERMISSIONS': scope,
            'FACEBOOK_COMPLETE_URI': self.redirect_uri,
        }
        tpl = self.setting('LOCAL_HTML', 'facebook.html')
        return self.strategy.render_html(tpl=tpl, context=ctx)

    def load_signed_request(self, signed_request):
        def base64_url_decode(data):
            data = data.encode('ascii')
            data += '='.encode('ascii') * (4 - (len(data) % 4))
            return base64.urlsafe_b64decode(data)

        key, secret = self.get_key_and_secret()
        try:
            sig, payload = signed_request.split('.', 1)
        except ValueError:
            pass  # ignore if can't split on dot
        else:
            sig = base64_url_decode(sig)
            payload_json_bytes = base64_url_decode(payload)
            data = json.loads(payload_json_bytes.decode('utf-8', 'replace'))
            expected_sig = hmac.new(secret.encode('ascii'),
                                    msg=payload.encode('ascii'),
                                    digestmod=hashlib.sha256).digest()
            # allow the signed_request to function for upto 1 day
            if constant_time_compare(sig, expected_sig) and \
               data['issued_at'] > (time.time() - 86400):
                return data
