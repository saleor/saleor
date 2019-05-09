"""
Odnoklassniki OAuth2 and Iframe Application backends, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/odnoklassnikiru.html
"""
from hashlib import md5

from six.moves.urllib_parse import unquote

from .base import BaseAuth
from .oauth import BaseOAuth2
from ..exceptions import AuthFailed


class OdnoklassnikiOAuth2(BaseOAuth2):
    """Odnoklassniki authentication backend"""
    name = 'odnoklassniki-oauth2'
    ID_KEY = 'uid'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ';'
    AUTHORIZATION_URL = 'https://connect.ok.ru/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.ok.ru/oauth/token.do'
    EXTRA_DATA = [('refresh_token', 'refresh_token'),
                  ('expires_in', 'expires')]

    def get_user_details(self, response):
        """Return user details from Odnoklassniki request"""
        fullname, first_name, last_name = self.get_user_names(
            fullname=unquote(response['name']),
            first_name=unquote(response['first_name']),
            last_name=unquote(response['last_name'])
        )
        return {
            'username': response['uid'],
            'email': response.get('email', ''),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Return user data from Odnoklassniki REST API"""
        data = {'access_token': access_token, 'method': 'users.getCurrentUser'}
        key, secret = self.get_key_and_secret()
        public_key = self.setting('PUBLIC_NAME')
        return odnoklassniki_api(self, data, 'https://api.ok.ru/',
                                 public_key, secret, 'oauth')


class OdnoklassnikiApp(BaseAuth):
    """Odnoklassniki iframe app authentication backend"""
    name = 'odnoklassniki-app'
    ID_KEY = 'uid'

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        return dict([(key, value) for key, value in response.items()
                            if key in response['extra_data_list']])

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            fullname=unquote(response['name']),
            first_name=unquote(response['first_name']),
            last_name=unquote(response['last_name'])
        )
        return {
            'username': response['uid'],
            'email': '',
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def auth_complete(self, *args, **kwargs):
        self.verify_auth_sig()
        response = self.get_response()
        fields = ('uid', 'first_name', 'last_name', 'name') + \
                 self.setting('EXTRA_USER_DATA_LIST', ())
        data = {
            'method': 'users.getInfo',
            'uids': '{0}'.format(response['logged_user_id']),
            'fields': ','.join(fields),
        }
        client_key, client_secret = self.get_key_and_secret()
        public_key = self.setting('PUBLIC_NAME')
        details = odnoklassniki_api(self, data, response['api_server'],
                                    public_key, client_secret,
                                    'iframe_nosession')
        if len(details) == 1 and 'uid' in details[0]:
            details = details[0]
            auth_data_fields = self.setting('EXTRA_AUTH_DATA_LIST',
                                            ('api_server', 'apiconnection',
                                             'session_key', 'authorized',
                                             'session_secret_key'))

            for field in auth_data_fields:
                details[field] = response[field]
            details['extra_data_list'] = fields + auth_data_fields
            kwargs.update({'backend': self, 'response': details})
        else:
            raise AuthFailed(self, 'Cannot get user details: API error')
        return self.strategy.authenticate(*args, **kwargs)

    def get_auth_sig(self):
        secret_key = self.setting('SECRET')
        hash_source = '{0:s}{1:s}{2:s}'.format(self.data['logged_user_id'],
                                               self.data['session_key'],
                                               secret_key)
        return md5(hash_source.encode('utf-8')).hexdigest()

    def get_response(self):
        fields = ('logged_user_id', 'api_server', 'application_key',
                  'session_key', 'session_secret_key', 'authorized',
                  'apiconnection')
        return dict((name, self.data[name]) for name in fields
                        if name in self.data)

    def verify_auth_sig(self):
        correct_key = self.get_auth_sig()
        key = self.data['auth_sig'].lower()
        if correct_key != key:
            raise AuthFailed(self, 'Wrong authorization key')


def odnoklassniki_oauth_sig(data, client_secret):
    """
    Calculates signature of request data access_token value must be included
    Algorithm is described at
        https://apiok.ru/wiki/pages/viewpage.action?pageId=12878032,
    search for "little bit different way"
    """
    suffix = md5(
        '{0:s}{1:s}'.format(data['access_token'],
                            client_secret).encode('utf-8')
    ).hexdigest()
    check_list = sorted(['{0:s}={1:s}'.format(key, value)
                            for key, value in data.items()
                                if key != 'access_token'])
    return md5((''.join(check_list) + suffix).encode('utf-8')).hexdigest()


def odnoklassniki_iframe_sig(data, client_secret_or_session_secret):
    """
    Calculates signature as described at:
        https://apiok.ru/wiki/display/ok/Authentication+and+Authorization
    If API method requires session context, request is signed with session
    secret key. Otherwise it is signed with application secret key
    """
    param_list = sorted(['{0:s}={1:s}'.format(key, value)
                            for key, value in data.items()])
    return md5(
        (''.join(param_list) + client_secret_or_session_secret).encode('utf-8')
    ).hexdigest()


def odnoklassniki_api(backend, data, api_url, public_key, client_secret,
                      request_type='oauth'):
    """Calls Odnoklassniki REST API method
    https://apiok.ru/wiki/display/ok/Odnoklassniki+Rest+API"""
    data.update({
        'application_key': public_key,
        'format': 'JSON'
    })
    if request_type == 'oauth':
        data['sig'] = odnoklassniki_oauth_sig(data, client_secret)
    elif request_type == 'iframe_session':
        data['sig'] = odnoklassniki_iframe_sig(data,
                                               data['session_secret_key'])
    elif request_type == 'iframe_nosession':
        data['sig'] = odnoklassniki_iframe_sig(data, client_secret)
    else:
        msg = 'Unknown request type {0}. How should it be signed?'
        raise AuthFailed(backend, msg.format(request_type))
    return backend.get_json(api_url + 'fb.do', params=data)
