import requests

from httpretty import HTTPretty

from six.moves.urllib_parse import urlencode, urlparse

from ...utils import parse_qs, url_add_parameters

from ..models import User
from .base import BaseBackendTest


class BaseOAuthTest(BaseBackendTest):
    backend = None
    backend_path = None
    user_data_body = None
    user_data_url = ''
    user_data_content_type = 'application/json'
    access_token_body = None
    access_token_status = 200
    expected_username = ''

    def extra_settings(self):
        return {'SOCIAL_AUTH_' + self.name + '_KEY': 'a-key',
                'SOCIAL_AUTH_' + self.name + '_SECRET': 'a-secret-key'}

    def _method(self, method):
        return {'GET': HTTPretty.GET,
                'POST': HTTPretty.POST}[method]

    def handle_state(self, start_url, target_url):
        start_query = parse_qs(urlparse(start_url).query)
        redirect_uri = start_query.get('redirect_uri')

        if getattr(self.backend, 'STATE_PARAMETER', False):
            if start_query.get('state'):
                target_url = url_add_parameters(target_url, {
                    'state': start_query['state']
                })

        if redirect_uri and getattr(self.backend, 'REDIRECT_STATE', False):
            redirect_query = parse_qs(urlparse(redirect_uri).query)
            if redirect_query.get('redirect_state'):
                target_url = url_add_parameters(target_url, {
                    'redirect_state': redirect_query['redirect_state']
                })
        return target_url

    def auth_handlers(self, start_url):
        target_url = self.handle_state(start_url,
                                       self.strategy.build_absolute_uri(
                                           self.complete_url
                                       ))
        HTTPretty.register_uri(HTTPretty.GET,
                               start_url,
                               status=301,
                               location=target_url)
        HTTPretty.register_uri(HTTPretty.GET,
                               target_url,
                               status=200,
                               body='foobar')
        HTTPretty.register_uri(self._method(self.backend.ACCESS_TOKEN_METHOD),
                               uri=self.backend.access_token_url(),
                               status=self.access_token_status,
                               body=self.access_token_body or '',
                               content_type='text/json')
        if self.user_data_url:
            HTTPretty.register_uri(HTTPretty.GET,
                                   self.user_data_url,
                                   body=self.user_data_body or '',
                                   content_type=self.user_data_content_type)
        return target_url

    def do_start(self):
        start_url = self.backend.start().url
        target_url = self.auth_handlers(start_url)
        response = requests.get(start_url)
        self.assertEqual(response.url, target_url)
        self.assertEqual(response.text, 'foobar')
        self.strategy.set_request_data(parse_qs(urlparse(start_url).query),
                                       self.backend)
        self.strategy.set_request_data(parse_qs(urlparse(target_url).query),
                                       self.backend)
        return self.backend.complete()


class OAuth1Test(BaseOAuthTest):
    request_token_body = None
    raw_complete_url = '/complete/{0}/?oauth_verifier=bazqux&' \
                                      'oauth_token=foobar'

    def request_token_handler(self):
        HTTPretty.register_uri(self._method(self.backend.REQUEST_TOKEN_METHOD),
                               self.backend.REQUEST_TOKEN_URL,
                               body=self.request_token_body,
                               status=200)

    def do_start(self):
        self.request_token_handler()
        return super(OAuth1Test, self).do_start()


class OAuth2Test(BaseOAuthTest):
    raw_complete_url = '/complete/{0}/?code=foobar'
    refresh_token_body = ''

    def refresh_token_arguments(self):
        return {}

    def do_refresh_token(self):
        self.do_login()
        HTTPretty.register_uri(self._method(self.backend.REFRESH_TOKEN_METHOD),
                               self.backend.refresh_token_url(),
                               status=200,
                               body=self.refresh_token_body)
        user = list(User.cache.values())[0]
        social = user.social[0]
        social.refresh_token(strategy=self.strategy,
                             **self.refresh_token_arguments())
        return user, social
