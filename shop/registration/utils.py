from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

import logging
import requests
import urllib
import urlparse

GOOGLE, FACEBOOK = 'google', 'facebook'
JSON_MIME_TYPE = 'application/json'
logger = logging.getLogger('saleor.registration')
User = get_user_model()


def get_local_host(request):
    scheme = 'http' + ('s' if request.is_secure() else '')
    return url(scheme=scheme, host=request.get_host())


def url(scheme='', host='', path='', params='', query='', fragment=''):
    return urlparse.urlunparse((scheme, host, path, params, query, fragment))


def get_client_class_for_service(service):
    return {GOOGLE: GoogleClient, FACEBOOK: FacebookClient}[service]


def get_google_login_url(local_host):
    return get_client_class_for_service(GOOGLE)(local_host).get_login_uri()


def get_facebook_login_url(local_host):
    return get_client_class_for_service(FACEBOOK)(local_host).get_login_uri()


def parse_response(response):
    if JSON_MIME_TYPE in response.headers['Content-Type']:
        return response.json()
    else:
        content = urlparse.parse_qs(response.text)
        content = dict((x, y[0] if len(y) == 1 else y)
                       for x, y in content.iteritems())
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

    def __init__(self, local_host, code=None):
        self.local_host = local_host
        if code:
            access_token = self.get_access_token(code)
            self.authorizer = OAuth2RequestAuthorizer(
                access_token=access_token)
        else:
            self.authorizer = None

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

    def get(self, address, params=None, authorize=True):
        auth = self.authorizer if authorize else None
        response = requests.get(address, params=params, auth=auth)
        return self.handle_response(response)

    def post(self, address, data=None, authorize=True):
        auth = self.authorizer if authorize else None
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
            raise ValueError(_('Google account not verified.'))

    def extract_error_from_response(self, response_content):
        return response_content['error']


class FacebookClient(OAuth2Client):

    service = FACEBOOK

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
            raise ValueError(_('Facebook account not verified.'))

    def extract_error_from_response(self, response_content):
        return response_content['error']['message']
