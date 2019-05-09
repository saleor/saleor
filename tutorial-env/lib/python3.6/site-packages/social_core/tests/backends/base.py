import unittest2 as unittest
import requests

from httpretty import HTTPretty

from ...utils import module_member, parse_qs, PARTIAL_TOKEN_SESSION_NAME
from ...backends.utils import user_backends_data, load_backends
from ..strategy import TestStrategy
from ..models import User, TestUserSocialAuth, TestNonce, \
                     TestAssociation, TestCode, TestStorage


class BaseBackendTest(unittest.TestCase):
    backend = None
    backend_path = None
    name = None
    complete_url = ''
    raw_complete_url = '/complete/{0}'

    def setUp(self):
        HTTPretty.enable()
        Backend = module_member(self.backend_path)
        self.strategy = TestStrategy(TestStorage)
        self.backend = Backend(self.strategy, redirect_uri=self.complete_url)
        self.name = self.backend.name.upper().replace('-', '_')
        self.complete_url = self.strategy.build_absolute_uri(
            self.raw_complete_url.format(self.backend.name)
        )
        backends = (self.backend_path,
                    'social_core.tests.backends.test_broken.BrokenBackendAuth')
        self.strategy.set_settings({
            'SOCIAL_AUTH_AUTHENTICATION_BACKENDS': backends
        })
        self.strategy.set_settings(self.extra_settings())
        # Force backends loading to trash PSA cache
        load_backends(backends, force_load=True)
        User.reset_cache()
        TestUserSocialAuth.reset_cache()
        TestNonce.reset_cache()
        TestAssociation.reset_cache()
        TestCode.reset_cache()

    def tearDown(self):
        HTTPretty.disable()
        self.backend = None
        self.strategy = None
        self.name = None
        self.complete_url = None
        User.reset_cache()
        TestUserSocialAuth.reset_cache()
        TestNonce.reset_cache()
        TestAssociation.reset_cache()
        TestCode.reset_cache()

    def extra_settings(self):
        return {}

    def do_start(self):
        raise NotImplementedError('Implement in subclass')

    def do_login(self):
        user = self.do_start()
        username = self.expected_username
        self.assertEqual(user.username, username)
        self.assertEqual(self.strategy.session_get('username'), username)
        self.assertEqual(self.strategy.get_user(user.id), user)
        self.assertEqual(self.backend.get_user(user.id), user)
        user_backends = user_backends_data(
            user,
            self.strategy.get_setting('SOCIAL_AUTH_AUTHENTICATION_BACKENDS'),
            self.strategy.storage
        )
        self.assertEqual(len(list(user_backends.keys())), 3)
        self.assertEqual('associated' in user_backends, True)
        self.assertEqual('not_associated' in user_backends, True)
        self.assertEqual('backends' in user_backends, True)
        self.assertEqual(len(user_backends['associated']), 1)
        self.assertEqual(len(user_backends['not_associated']), 1)
        self.assertEqual(len(user_backends['backends']), 2)
        return user

    def pipeline_settings(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_PIPELINE': (
                'social_core.pipeline.social_auth.social_details',
                'social_core.pipeline.social_auth.social_uid',
                'social_core.pipeline.social_auth.auth_allowed',
                'social_core.tests.pipeline.ask_for_password',
                'social_core.tests.pipeline.ask_for_slug',
                'social_core.pipeline.social_auth.social_user',
                'social_core.pipeline.user.get_username',
                'social_core.pipeline.social_auth.associate_by_email',
                'social_core.pipeline.user.create_user',
                'social_core.pipeline.social_auth.associate_user',
                'social_core.pipeline.social_auth.load_extra_data',
                'social_core.tests.pipeline.set_password',
                'social_core.tests.pipeline.set_slug',
                'social_core.pipeline.user.user_details'
            )
        })

    def pipeline_handlers(self, url):
        HTTPretty.register_uri(HTTPretty.GET, url, status=200, body='foobar')
        HTTPretty.register_uri(HTTPretty.POST, url, status=200)

    def pipeline_password_handling(self, url):
        password = 'foobar'
        requests.get(url)
        requests.post(url, data={'password': password})

        data = parse_qs(HTTPretty.last_request.body)
        self.assertEqual(data['password'], password)
        self.strategy.session_set('password', data['password'])
        return password

    def pipeline_slug_handling(self, url):
        slug = 'foo-bar'
        requests.get(url)
        requests.post(url, data={'slug': slug})

        data = parse_qs(HTTPretty.last_request.body)
        self.assertEqual(data['slug'], slug)
        self.strategy.session_set('slug', data['slug'])
        return slug

    def do_partial_pipeline(self):
        url = self.strategy.build_absolute_uri('/password')
        self.pipeline_settings()
        redirect = self.do_start()
        self.assertEqual(redirect.url, url)
        self.pipeline_handlers(url)

        password = self.pipeline_password_handling(url)
        token = self.strategy.session_pop(PARTIAL_TOKEN_SESSION_NAME)
        partial = self.strategy.partial_load(token)
        self.assertEqual(partial.backend, self.backend.name)
        redirect = self.backend.continue_pipeline(partial)

        url = self.strategy.build_absolute_uri('/slug')
        self.assertEqual(redirect.url, url)
        self.pipeline_handlers(url)
        slug = self.pipeline_slug_handling(url)

        token = self.strategy.session_pop(PARTIAL_TOKEN_SESSION_NAME)
        partial = self.strategy.partial_load(token)
        self.assertEqual(partial.backend, self.backend.name)
        user = self.backend.continue_pipeline(partial)

        self.assertEqual(user.username, self.expected_username)
        self.assertEqual(user.slug, slug)
        self.assertEqual(user.password, password)
        return user
