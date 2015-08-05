import hashlib
import hmac
import logging
try:
    from urllib.parse import parse_qs, urlencode, urljoin, urlunparse
except ImportError:
    from urllib import urlencode
    from urlparse import parse_qs, urljoin, urlunparse

from django.core.urlresolvers import reverse
from django.conf import settings
import requests


GOOGLE, FACEBOOK = 'google', 'facebook'
JSON_MIME_TYPE = 'application/json'
logger = logging.getLogger('saleor.registration')


def get_local_host(request):
    scheme = 'http' + ('s' if request.is_secure() else '')
    return url(scheme=scheme, host=request.get_host())


def url(scheme='', host='', path='', params='', query='', fragment=''):
    return urlunparse((scheme, host, path, params, query, fragment))


def get_client_class_for_service(service):
    return {GOOGLE: GoogleClient, FACEBOOK: FacebookClient}[service]


def get_google_login_url(local_host):
    if settings.GOOGLE_CLIENT_ID:
        client_class = get_client_class_for_service(GOOGLE)(local_host)
        return client_class.get_login_uri()


def get_facebook_login_url(local_host):
    if settings.FACEBOOK_APP_ID:
        client_class = get_client_class_for_service(FACEBOOK)(local_host)
        return client_class.get_login_uri()


def parse_response(response):
    if JSON_MIME_TYPE in response.headers['Content-Type']:
        return response.json()
    else:
        content = parse_qs(response.text)
        content = dict((x, y[0] if len(y) == 1 else y)
                       for x, y in content.items())
        return content


class OAuth2RequestAuthorizer(requests.auth.AuthBase):

    def __init__(self, access_token):
        self.access_token = access_token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer %s' % (self.access_token,)
        return request


class OAuth2Client(object):

    service = None

    client_id = None
    client_secret = None

    auth_uri = None
    token_uri = None
    user_info_uri = None

    scope = None

    def __init__(self, local_host, code=None,
                 client_id=None, client_secret=None):
        self.local_host = local_host

        if client_id and client_secret:
            self.client_id = client_id
            self.client_secret = client_secret

        if code:
            access_token = self.get_access_token(code)
            self.authorizer = OAuth2RequestAuthorizer(
                access_token=access_token)
        else:
            self.authorizer = None

    def get_redirect_uri(self):
        kwargs = {'service': self.service}
        path = reverse('registration:oauth_callback', kwargs=kwargs)
        return urljoin(self.local_host, path)

    def get_login_uri(self):
        data = {'response_type': 'code',
                'scope': self.scope,
                'redirect_uri': self.get_redirect_uri(),
                'client_id': self.client_id}
        query = urlencode(data)
        return urljoin(self.auth_uri, url(query=query))

    def get_access_token(self, code):
        data = {'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': self.get_redirect_uri(),
                'scope': self.scope}
        response = self.post(self.token_uri, data=data, authorize=False)
        return response['access_token']

    def get_user_info(self):
        return self.get(self.user_info_uri)

    def get_request_params(self, data=None, authorize=True):
        auth = self.authorizer if authorize else None
        return data, auth

    def get(self, address, params=None, authorize=True):
        params, auth = self.get_request_params(params, authorize)
        response = requests.get(address, params=params, auth=auth)
        return self.handle_response(response)

    def post(self, address, data=None, authorize=True):
        data, auth = self.get_request_params(data, authorize)
        response = requests.post(address, data=data, auth=auth)
        return self.handle_response(response)

    def handle_response(self, response):
        response_content = parse_response(response)
        if response.status_code == requests.codes.ok:
            return response_content
        else:
            logger.error('[%s]: %s', response.status_code, response.text)
            error = self.extract_error_from_response(response_content)
            raise ValueError(error)

    def extract_error_from_response(self, response_content):
        raise NotImplementedError()


class GoogleClient(OAuth2Client):

    service = GOOGLE

    auth_uri = 'https://accounts.google.com/o/oauth2/auth'
    token_uri = 'https://accounts.google.com/o/oauth2/token'
    user_info_uri = 'https://www.googleapis.com/oauth2/v1/userinfo'

    scope = ' '.join(['https://www.googleapis.com/auth/userinfo.email',
                      'https://www.googleapis.com/auth/plus.me'])

    def __init__(self, *args, **kwargs):
        if not self.client_id and not self.client_secret:
            self.client_id = settings.GOOGLE_CLIENT_ID
            self.client_secret = settings.GOOGLE_CLIENT_SECRET
        super(GoogleClient, self).__init__(*args, **kwargs)

    def get_user_info(self):
        response = super(GoogleClient, self).get_user_info()
        if response.get('verified_email'):
            return response
        else:
            raise ValueError('Google account not verified.')

    def extract_error_from_response(self, response_content):
        return response_content['error']


class FacebookClient(OAuth2Client):

    service = FACEBOOK

    auth_uri = 'https://www.facebook.com/dialog/oauth'
    token_uri = 'https://graph.facebook.com/oauth/access_token'
    user_info_uri = 'https://graph.facebook.com/me?fields=name,email,verified'

    scope = ','.join(['email'])

    def __init__(self, *args, **kwargs):
        if not self.client_id and not self.client_secret:
            self.client_id = settings.FACEBOOK_APP_ID
            self.client_secret = settings.FACEBOOK_SECRET
        super(FacebookClient, self).__init__(*args, **kwargs)

    def get_request_params(self, data=None, authorize=True):
        data = data or {}
        if authorize:
            data.update({'appsecret_proof': hmac.new(
                settings.FACEBOOK_SECRET.encode('utf8'),
                msg=self.authorizer.access_token.encode('utf8'),
                digestmod=hashlib.sha256).hexdigest()})
        return super(FacebookClient, self).get_request_params(data, authorize)

    def get_user_info(self):
        response = super(FacebookClient, self).get_user_info()
        if not response.get('verified'):
            raise ValueError('Facebook account not verified.')
        if not response.get('email'):
            raise ValueError('Access to your email address is required.')
        return response

    def extract_error_from_response(self, response_content):
        return response_content['error']['message']
