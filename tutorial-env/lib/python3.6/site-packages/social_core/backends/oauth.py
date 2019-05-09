import six

from requests_oauthlib import OAuth1
from oauthlib.oauth1 import SIGNATURE_TYPE_AUTH_HEADER

from six.moves.urllib_parse import urlencode, unquote

from ..utils import url_add_parameters, parse_qs, handle_http_errors, \
                    constant_time_compare
from ..exceptions import AuthFailed, AuthCanceled, AuthUnknownError, \
                         AuthMissingParameter, AuthStateMissing, \
                         AuthStateForbidden, AuthTokenError
from .base import BaseAuth


class OAuthAuth(BaseAuth):
    """OAuth authentication backend base class.

    Also settings will be inspected to get more values names that should be
    stored on extra_data field. Setting name is created from current backend
    name (all uppercase) plus _EXTRA_DATA.

    access_token is always stored.

    URLs settings:
        AUTHORIZATION_URL       Authorization service url
        ACCESS_TOKEN_URL        Access token URL
    """
    AUTHORIZATION_URL = ''
    ACCESS_TOKEN_URL = ''
    ACCESS_TOKEN_METHOD = 'GET'
    REVOKE_TOKEN_URL = None
    REVOKE_TOKEN_METHOD = 'POST'
    ID_KEY = 'id'
    SCOPE_PARAMETER_NAME = 'scope'
    DEFAULT_SCOPE = None
    SCOPE_SEPARATOR = ' '
    REDIRECT_STATE = False
    STATE_PARAMETER = False

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        """Return access_token and extra defined names to store in
        extra_data field"""
        data = super(OAuthAuth, self).extra_data(user, uid, response, details,
                                                 *args, **kwargs)
        data['access_token'] = response.get('access_token', '') or \
                               kwargs.get('access_token')
        return data

    def state_token(self):
        """Generate csrf token to include as state parameter."""
        return self.strategy.random_string(32)

    def get_or_create_state(self):
        if self.STATE_PARAMETER or self.REDIRECT_STATE:
            # Store state in session for further request validation. The state
            # value is passed as state parameter (as specified in OAuth2 spec),
            # but also added to redirect, that way we can still verify the
            # request if the provider doesn't implement the state parameter.
            # Reuse token if any.
            name = self.name + '_state'
            state = self.strategy.session_get(name)
            if state is None:
                state = self.state_token()
                self.strategy.session_set(name, state)
        else:
            state = None
        return state

    def get_session_state(self):
        return self.strategy.session_get(self.name + '_state')

    def get_request_state(self):
        request_state = self.data.get('state') or \
                        self.data.get('redirect_state')
        if request_state and isinstance(request_state, list):
            request_state = request_state[0]
        return request_state

    def validate_state(self):
        """Validate state value. Raises exception on error, returns state
        value if valid."""
        if not self.STATE_PARAMETER and not self.REDIRECT_STATE:
            return None
        state = self.get_session_state()
        request_state = self.get_request_state()
        if not request_state:
            raise AuthMissingParameter(self, 'state')
        elif not state:
            raise AuthStateMissing(self, 'state')
        elif not constant_time_compare(request_state, state):
            raise AuthStateForbidden(self)
        else:
            return state

    def get_redirect_uri(self, state=None):
        """Build redirect with redirect_state parameter."""
        uri = self.redirect_uri
        if self.REDIRECT_STATE and state:
            uri = url_add_parameters(uri, {'redirect_state': state})
        return uri

    def get_scope(self):
        """Return list with needed access scope"""
        scope = self.setting('SCOPE', [])
        if not self.setting('IGNORE_DEFAULT_SCOPE', False):
            scope = scope + (self.DEFAULT_SCOPE or [])
        return scope

    def get_scope_argument(self):
        param = {}
        scope = self.get_scope()
        if scope:
            param[self.SCOPE_PARAMETER_NAME] = self.SCOPE_SEPARATOR.join(scope)
        return param

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service. Implement in subclass"""
        return {}

    def authorization_url(self):
        return self.AUTHORIZATION_URL

    def access_token_url(self):
        return self.ACCESS_TOKEN_URL

    def revoke_token_url(self, token, uid):
        return self.REVOKE_TOKEN_URL

    def revoke_token_params(self, token, uid):
        return {}

    def revoke_token_headers(self, token, uid):
        return {}

    def process_revoke_token_response(self, response):
        return response.status_code == 200

    def revoke_token(self, token, uid):
        if self.REVOKE_TOKEN_URL:
            url = self.revoke_token_url(token, uid)
            params = self.revoke_token_params(token, uid)
            headers = self.revoke_token_headers(token, uid)
            data = urlencode(params) if self.REVOKE_TOKEN_METHOD != 'GET' \
                                     else None
            response = self.request(url, params=params, headers=headers,
                                    data=data, method=self.REVOKE_TOKEN_METHOD)
            return self.process_revoke_token_response(response)


class BaseOAuth1(OAuthAuth):
    """Consumer based mechanism OAuth authentication, fill the needed
    parameters to communicate properly with authentication service.

    URLs settings:
        REQUEST_TOKEN_URL       Request token URL

    """
    REQUEST_TOKEN_URL = ''
    REQUEST_TOKEN_METHOD = 'GET'
    OAUTH_TOKEN_PARAMETER_NAME = 'oauth_token'
    REDIRECT_URI_PARAMETER_NAME = 'redirect_uri'
    UNATHORIZED_TOKEN_SUFIX = 'unauthorized_token_name'

    def auth_url(self):
        """Return redirect url"""
        token = self.set_unauthorized_token()
        return self.oauth_authorization_request(token)

    def process_error(self, data):
        if 'oauth_problem' in data:
            if data['oauth_problem'] == 'user_refused':
                raise AuthCanceled(self, 'User refused the access')
            raise AuthUnknownError(self, 'Error was ' + data['oauth_problem'])

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Return user, might be logged in"""
        # Multiple unauthorized tokens are supported (see #521)
        self.process_error(self.data)
        self.validate_state()
        token = self.get_unauthorized_token()
        access_token = self.access_token(token)
        return self.do_auth(access_token, *args, **kwargs)

    @handle_http_errors
    def do_auth(self, access_token, *args, **kwargs):
        """Finish the auth process once the access_token was retrieved"""
        if not isinstance(access_token, dict):
            access_token = parse_qs(access_token)
        data = self.user_data(access_token)
        if data is not None and 'access_token' not in data:
            data['access_token'] = access_token
        kwargs.update({'response': data, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def get_unauthorized_token(self):
        name = self.name + self.UNATHORIZED_TOKEN_SUFIX
        unauthed_tokens = self.strategy.session_get(name, [])
        if not unauthed_tokens:
            raise AuthTokenError(self, 'Missing unauthorized token')

        data_token = self.data.get(self.OAUTH_TOKEN_PARAMETER_NAME)

        if data_token is None:
            raise AuthTokenError(self, 'Missing unauthorized token')

        token = None
        for utoken in unauthed_tokens:
            orig_utoken = utoken
            if not isinstance(utoken, dict):
                utoken = parse_qs(utoken)
            if utoken.get(self.OAUTH_TOKEN_PARAMETER_NAME) == data_token:
                self.strategy.session_set(name, list(set(unauthed_tokens) -
                                                     set([orig_utoken])))
                token = utoken
                break
        else:
            raise AuthTokenError(self, 'Incorrect tokens')
        return token

    def set_unauthorized_token(self):
        token = self.unauthorized_token()
        name = self.name + self.UNATHORIZED_TOKEN_SUFIX
        tokens = self.strategy.session_get(name, []) + [token]
        self.strategy.session_set(name, tokens)
        return token

    def request_token_extra_arguments(self):
        """Return extra arguments needed on request-token process"""
        return self.setting('REQUEST_TOKEN_EXTRA_ARGUMENTS', {})

    def unauthorized_token(self):
        """Return request for unauthorized token (first stage)"""
        params = self.request_token_extra_arguments()
        params.update(self.get_scope_argument())
        key, secret = self.get_key_and_secret()
        # decoding='utf-8' produces errors with python-requests on Python3
        # since the final URL will be of type bytes
        decoding = None if six.PY3 else 'utf-8'
        state = self.get_or_create_state()
        response = self.request(
            self.REQUEST_TOKEN_URL,
            params=params,
            auth=OAuth1(key, secret, callback_uri=self.get_redirect_uri(state),
                        decoding=decoding),
            method=self.REQUEST_TOKEN_METHOD
        )
        content = response.content
        if response.encoding or response.apparent_encoding:
            content = content.decode(response.encoding or
                                     response.apparent_encoding)
        else:
            content = response.content.decode()
        return content

    def oauth_authorization_request(self, token):
        """Generate OAuth request to authorize token."""
        if not isinstance(token, dict):
            token = parse_qs(token)
        params = self.auth_extra_arguments() or {}
        params.update(self.get_scope_argument())
        params[self.OAUTH_TOKEN_PARAMETER_NAME] = token.get(
            self.OAUTH_TOKEN_PARAMETER_NAME
        )
        state = self.get_or_create_state()
        params[self.REDIRECT_URI_PARAMETER_NAME] = self.get_redirect_uri(state)
        return '{0}?{1}'.format(self.authorization_url(), urlencode(params))

    def oauth_auth(self, token=None, oauth_verifier=None,
                   signature_type=SIGNATURE_TYPE_AUTH_HEADER):
        key, secret = self.get_key_and_secret()
        oauth_verifier = oauth_verifier or self.data.get('oauth_verifier')
        if token:
            resource_owner_key = token.get('oauth_token')
            resource_owner_secret = token.get('oauth_token_secret')
            if not resource_owner_key:
                raise AuthTokenError(self, 'Missing oauth_token')
            if not resource_owner_secret:
                raise AuthTokenError(self, 'Missing oauth_token_secret')
        else:
            resource_owner_key = None
            resource_owner_secret = None
        # decoding='utf-8' produces errors with python-requests on Python3
        # since the final URL will be of type bytes
        decoding = None if six.PY3 else 'utf-8'
        state = self.get_or_create_state()
        return OAuth1(key, secret,
                      resource_owner_key=resource_owner_key,
                      resource_owner_secret=resource_owner_secret,
                      callback_uri=self.get_redirect_uri(state),
                      verifier=oauth_verifier,
                      signature_type=signature_type,
                      decoding=decoding)

    def oauth_request(self, token, url, params=None, method='GET'):
        """Generate OAuth request, setups callback url"""
        return self.request(url, method=method, params=params,
                            auth=self.oauth_auth(token))

    def access_token(self, token):
        """Return request for access token value"""
        return self.get_querystring(self.access_token_url(),
                                    auth=self.oauth_auth(token),
                                    method=self.ACCESS_TOKEN_METHOD)


class BaseOAuth2(OAuthAuth):
    """Base class for OAuth2 providers.

    OAuth2 draft details at:
        http://tools.ietf.org/html/draft-ietf-oauth-v2-10
    """
    REFRESH_TOKEN_URL = None
    REFRESH_TOKEN_METHOD = 'POST'
    RESPONSE_TYPE = 'code'
    REDIRECT_STATE = True
    STATE_PARAMETER = True

    def auth_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        params = {
            'client_id': client_id,
            'redirect_uri': self.get_redirect_uri(state)
        }
        if self.STATE_PARAMETER and state:
            params['state'] = state
        if self.RESPONSE_TYPE:
            params['response_type'] = self.RESPONSE_TYPE
        return params

    def auth_url(self):
        """Return redirect url"""
        state = self.get_or_create_state()
        params = self.auth_params(state)
        params.update(self.get_scope_argument())
        params.update(self.auth_extra_arguments())
        params = urlencode(params)
        if not self.REDIRECT_STATE:
            # redirect_uri matching is strictly enforced, so match the
            # providers value exactly.
            params = unquote(params)
        return '{0}?{1}'.format(self.authorization_url(), params)

    def auth_complete_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': self.get_redirect_uri(state)
        }

    def auth_complete_credentials(self):
        return None

    def auth_headers(self):
        return {'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'}

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        """Return access_token, token_type, and extra defined names to store in
            extra_data field"""
        data = super(BaseOAuth2, self).extra_data(user, uid, response,
                                                  details=details,
                                                  *args, **kwargs)
        data['token_type'] = response.get('token_type') or \
                             kwargs.get('token_type')
        return data

    def request_access_token(self, *args, **kwargs):
        return self.get_json(*args, **kwargs)

    def process_error(self, data):
        if data.get('error'):
            if 'denied' in data['error'] or 'cancelled' in data['error']:
                raise AuthCanceled(self, data.get('error_description', ''))
            raise AuthFailed(self, data.get('error_description') or
                                   data['error'])
        elif 'denied' in data:
            raise AuthCanceled(self, data['denied'])

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        state = self.validate_state()
        data, params = None, None
        if self.ACCESS_TOKEN_METHOD == 'GET':
            params = self.auth_complete_params(state)
        else:
            data = self.auth_complete_params(state)

        response = self.request_access_token(
            self.access_token_url(),
            data=data,
            params=params,
            headers=self.auth_headers(),
            auth=self.auth_complete_credentials(),
            method=self.ACCESS_TOKEN_METHOD
        )
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)

    @handle_http_errors
    def do_auth(self, access_token, *args, **kwargs):
        """Finish the auth process once the access_token was retrieved"""
        data = self.user_data(access_token, *args, **kwargs)
        response = kwargs.get('response') or {}
        response.update(data or {})
        if 'access_token' not in response:
            response['access_token'] = access_token
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def refresh_token_params(self, token, *args, **kwargs):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'refresh_token': token,
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'client_secret': client_secret
        }

    def process_refresh_token_response(self, response, *args, **kwargs):
        return response.json()

    def refresh_token(self, token, *args, **kwargs):
        params = self.refresh_token_params(token, *args, **kwargs)
        url = self.refresh_token_url()
        method = self.REFRESH_TOKEN_METHOD
        key = 'params' if method == 'GET' else 'data'
        request_args = {'headers': self.auth_headers(),
                        'method': method,
                        key: params}
        request = self.request(url, **request_args)
        return self.process_refresh_token_response(request, *args, **kwargs)

    def refresh_token_url(self):
        return self.REFRESH_TOKEN_URL or self.access_token_url()
