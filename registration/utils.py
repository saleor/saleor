from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

import logging
import requests
import urllib
import urlparse

GOOGLE, FACEBOOK = 'google', 'facebook'
User = get_user_model()
logger = logging.getLogger('saleor.registration')


def get_protocol_and_host(request):
    scheme = 'http' + ('s' if request.is_secure() else '')
    return url(scheme=scheme, host=request.get_host())


def get_client_class_for_serivce(service):
    return {GOOGLE: GoogleClient, FACEBOOK: FacebookClient}[service]


def get_google_login_url(local_host):
    return get_client_class_for_serivce(GOOGLE)(local_host).get_login_uri()


def get_facebook_login_url(local_host):
    return get_client_class_for_serivce(FACEBOOK)(local_host).get_login_uri()


def url(scheme='', host='', path='', params='', query='', fragment=''):
    return urlparse.urlunparse((scheme, host, path, params, query, fragment))


class OAuth2Authorizer(requests.auth.AuthBase):

    def __init__(self, access_token):
        self.access_token = access_token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer %s' % (self.access_token,)
        return request


class OAuth2Connection(object):

    def __init__(self, code, client):
        self.code = code
        self.client = client
        self.access_token = None
        self.refresh_token = None

    def get(self, address, params=None, auth=True):
        args, kwargs = (address,), {'params': params}
        return self._make_request(requests.get, args, kwargs, auth)

    def post(self, address, data=None, auth=True):
        args, kwargs = (address,), {'data': data}
        return self._make_request(requests.post, args, kwargs, auth)

    def _make_request(self, method, args, kwargs, auth):
        if auth:
            if not self.access_token:
                self.access_token = self.client.get_access_token(self.code)
            kwargs['auth'] = OAuth2Authorizer(access_token=self.access_token)
        response = method(*args, **kwargs)
        content = self._parse_response(response)
        if response.status_code == requests.codes.ok:
            return content
        else:
            logger.error('[%s]: %s', response.status_code, response.text)
            error = self.extract_error(content)
            raise ValueError(error)

    def _parse_response(self, response):
        if 'application/json' in response.headers['Content-Type']:
            return response.json()
        else:
            content = urlparse.parse_qsl(response.text)
            content = dict((x, y[0] if len(y) == 1 else y) for x, y in content)
            return content


class GoogleConnection(OAuth2Connection):

    def extract_error(self, content):
        return content['error']


class FacebookConnection(OAuth2Connection):

    def extract_error(self, content):
        return content['error']['message']


class OAuth2Client(object):

    service = None
    connection_class = None
    client_id = None
    client_secret = None
    auth_uri = None
    token_uri = None
    user_info_uri = None
    scope = None

    def __init__(self, local_host, code=None):
        self.local_host = local_host
        if code:
            self.connection = self.connection_class(code=code, client=self)

    def get_redirect_uri(self):
        kwargs = {'service': self.service}
        path = reverse('registration:oauth_callback', kwargs=kwargs)
        return urlparse.urljoin(self.local_host, path)

    def get_login_uri(self):
        data = {'response_type': 'code',
                'scope': self.scope,
                'redirect_uri': self.get_redirect_uri(),
                'client_id': self.client_id}
        query = urllib.urlencode(data)
        return urlparse.urljoin(self.auth_uri, url(query=query))

    def get_user_info(self):
        return self.connection.get(self.user_info_uri)

    def get_access_token(self, code):
        data = {'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': self.get_redirect_uri(),
                'scope': self.scope}
        response = self.connection.post(self.token_uri, data=data, auth=False)
        return response['access_token']


class GoogleClient(OAuth2Client):

    service = GOOGLE
    connection_class = GoogleConnection

    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_SECRET

    auth_uri = 'https://accounts.google.com/o/oauth2/auth'
    token_uri = 'https://accounts.google.com/o/oauth2/token'
    user_info_uri = 'https://www.googleapis.com/oauth2/v1/userinfo'

    scope = ' '.join(['https://www.googleapis.com/auth/userinfo.email',
                      'https://www.googleapis.com/auth/plus.me'])

    def get_user_info(self):
        response = super(GoogleClient, self).get_user_info()
        if response['verified_email']:
            return response
        else:
            raise ValueError('Google account not verified.')


class FacebookClient(OAuth2Client):

    service = FACEBOOK
    connection_class = FacebookConnection

    client_id = settings.FACEBOOK_APP_ID
    client_secret = settings.FACEBOOK_SECRET

    auth_uri = 'https://www.facebook.com/dialog/oauth'
    token_uri = 'https://graph.facebook.com/oauth/access_token'
    user_info_uri = 'https://graph.facebook.com/me'

    scope = ','.join(['email'])

    def get_user_info(self):
        response = super(FacebookClient, self).get_user_info()
        if response['verified']:
            return response
        else:
            raise ValueError('Facebook account not verified.')
