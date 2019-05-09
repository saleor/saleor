import json
import requests
import unittest2 as unittest

from httpretty import HTTPretty

from six.moves.urllib_parse import urlparse

from ...utils import parse_qs, module_member
from ...actions import do_auth, do_complete
from ..models import TestStorage, User, TestUserSocialAuth, TestNonce, \
                     TestAssociation
from ..strategy import TestStrategy


class BaseActionTest(unittest.TestCase):
    user_data_url = 'https://api.github.com/user'
    login_redirect_url = '/success'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'login': 'foobar',
        'id': 1,
        'avatar_url': 'https://github.com/images/error/foobar_happy.gif',
        'gravatar_id': 'somehexcode',
        'url': 'https://api.github.com/users/foobar',
        'name': 'monalisa foobar',
        'company': 'GitHub',
        'blog': 'https://github.com/blog',
        'location': 'San Francisco',
        'email': 'foo@bar.com',
        'hireable': False,
        'bio': 'There once was...',
        'public_repos': 2,
        'public_gists': 1,
        'followers': 20,
        'following': 0,
        'html_url': 'https://github.com/foobar',
        'created_at': '2008-01-14T04:33:35Z',
        'type': 'User',
        'total_private_repos': 100,
        'owned_private_repos': 100,
        'private_gists': 81,
        'disk_usage': 10000,
        'collaborators': 8,
        'plan': {
            'name': 'Medium',
            'space': 400,
            'collaborators': 10,
            'private_repos': 20
        }
    })

    def __init__(self, *args, **kwargs):
        self.strategy = None
        super(BaseActionTest, self).__init__(*args, **kwargs)

    def setUp(self):
        HTTPretty.enable()
        User.reset_cache()
        TestUserSocialAuth.reset_cache()
        TestNonce.reset_cache()
        TestAssociation.reset_cache()
        Backend = module_member('social_core.backends.github.GithubOAuth2')
        self.strategy = self.strategy or TestStrategy(TestStorage)
        self.backend = Backend(self.strategy, redirect_uri='/complete/github')
        self.user = None

    def tearDown(self):
        self.backend = None
        self.strategy = None
        self.user = None
        User.reset_cache()
        User.set_active(True)
        TestUserSocialAuth.reset_cache()
        TestNonce.reset_cache()
        TestAssociation.reset_cache()
        HTTPretty.disable()

    def do_login(self, after_complete_checks=True, user_data_body=None,
                 expected_username=None):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_KEY': 'a-key',
            'SOCIAL_AUTH_GITHUB_SECRET': 'a-secret-key',
            'SOCIAL_AUTH_LOGIN_REDIRECT_URL': self.login_redirect_url,
            'SOCIAL_AUTH_AUTHENTICATION_BACKENDS': (
                'social_core.backends.github.GithubOAuth2',
            )
        })
        start_url = do_auth(self.backend).url
        target_url = self.strategy.build_absolute_uri(
            '/complete/github/?code=foobar'
        )

        start_query = parse_qs(urlparse(start_url).query)
        location_url = target_url + ('&' if '?' in target_url else '?') + \
                       'state=' + start_query['state']
        location_query = parse_qs(urlparse(location_url).query)

        HTTPretty.register_uri(HTTPretty.GET, start_url, status=301,
                               location=location_url)
        HTTPretty.register_uri(HTTPretty.GET, location_url, status=200,
                               body='foobar')

        response = requests.get(start_url)
        self.assertEqual(response.url, location_url)
        self.assertEqual(response.text, 'foobar')

        HTTPretty.register_uri(HTTPretty.POST,
                               uri=self.backend.ACCESS_TOKEN_URL,
                               status=200,
                               body=self.access_token_body or '',
                               content_type='text/json')

        if self.user_data_url:
            user_data_body = user_data_body or self.user_data_body or ''
            HTTPretty.register_uri(HTTPretty.GET, self.user_data_url,
                                   body=user_data_body,
                                   content_type='text/json')
        self.strategy.set_request_data(location_query, self.backend)

        def _login(backend, user, social_user):
            backend.strategy.session_set('username', user.username)

        redirect = do_complete(self.backend, user=self.user, login=_login)

        if after_complete_checks:
            self.assertEqual(self.strategy.session_get('username'),
                             expected_username or self.expected_username)
            self.assertEqual(redirect.url, self.login_redirect_url)
        return redirect

    def do_login_with_partial_pipeline(self, before_complete=None):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITHUB_KEY': 'a-key',
            'SOCIAL_AUTH_GITHUB_SECRET': 'a-secret-key',
            'SOCIAL_AUTH_LOGIN_REDIRECT_URL': self.login_redirect_url,
            'SOCIAL_AUTH_AUTHENTICATION_BACKENDS': (
                'social_core.backends.github.GithubOAuth2',
            ),
            'SOCIAL_AUTH_PIPELINE': (
                'social_core.pipeline.social_auth.social_details',
                'social_core.pipeline.social_auth.social_uid',
                'social_core.pipeline.social_auth.auth_allowed',
                'social_core.tests.pipeline.ask_for_password',
                'social_core.pipeline.social_auth.social_user',
                'social_core.pipeline.user.get_username',
                'social_core.pipeline.user.create_user',
                'social_core.pipeline.social_auth.associate_user',
                'social_core.pipeline.social_auth.load_extra_data',
                'social_core.tests.pipeline.set_password',
                'social_core.pipeline.user.user_details'
            )
        })
        start_url = do_auth(self.backend).url
        target_url = self.strategy.build_absolute_uri(
            '/complete/github/?code=foobar'
        )

        start_query = parse_qs(urlparse(start_url).query)
        location_url = target_url + ('&' if '?' in target_url else '?') + \
                       'state=' + start_query['state']
        location_query = parse_qs(urlparse(location_url).query)

        HTTPretty.register_uri(HTTPretty.GET, start_url, status=301,
                               location=location_url)
        HTTPretty.register_uri(HTTPretty.GET, location_url, status=200,
                               body='foobar')

        response = requests.get(start_url)
        self.assertEqual(response.url, location_url)
        self.assertEqual(response.text, 'foobar')

        HTTPretty.register_uri(HTTPretty.GET,
                               uri=self.backend.ACCESS_TOKEN_URL,
                               status=200,
                               body=self.access_token_body or '',
                               content_type='text/json')

        if self.user_data_url:
            HTTPretty.register_uri(HTTPretty.GET, self.user_data_url,
                                   body=self.user_data_body or '',
                                   content_type='text/json')
        self.strategy.set_request_data(location_query, self.backend)

        def _login(backend, user, social_user):
            backend.strategy.session_set('username', user.username)

        redirect = do_complete(self.backend, user=self.user, login=_login)
        url = self.strategy.build_absolute_uri('/password')
        self.assertEqual(redirect.url, url)
        HTTPretty.register_uri(HTTPretty.GET, redirect.url, status=200,
                               body='foobar')
        HTTPretty.register_uri(HTTPretty.POST, redirect.url, status=200)

        password = 'foobar'
        requests.get(url)
        requests.post(url, data={'password': password})
        data = parse_qs(HTTPretty.last_request.body)
        self.assertEqual(data['password'], password)
        self.strategy.session_set('password', data['password'])

        if before_complete:
            before_complete()
        redirect = do_complete(self.backend, user=self.user, login=_login)
        self.assertEqual(self.strategy.session_get('username'),
                         self.expected_username)
        self.assertEqual(redirect.url, self.login_redirect_url)
