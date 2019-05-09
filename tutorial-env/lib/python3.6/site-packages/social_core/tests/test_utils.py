import sys
import unittest2 as unittest

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from ..utils import sanitize_redirect, user_is_authenticated, \
                    user_is_active, slugify, build_absolute_uri, \
                    partial_pipeline_data
from .models import TestPartial


PY3 = sys.version_info[0] == 3


class SanitizeRedirectTest(unittest.TestCase):
    def test_none_redirect(self):
        self.assertEqual(sanitize_redirect(['myapp.com'], None), None)

    def test_empty_redirect(self):
        self.assertEqual(sanitize_redirect(['myapp.com'], ''), None)

    def test_dict_redirect(self):
        self.assertEqual(sanitize_redirect(['myapp.com'], {}), None)

    def test_invalid_redirect(self):
        self.assertEqual(sanitize_redirect(['myapp.com'], {'foo': 'bar'}), None)

    def test_wrong_path_redirect(self):
        self.assertEqual(
            sanitize_redirect(['myapp.com'], 'http://notmyapp.com/path/'),
            None
        )

    def test_invalid_evil_redirect(self):
        self.assertEqual(sanitize_redirect(['myapp.com'], '///evil.com'), None)

    def test_valid_absolute_redirect(self):
        self.assertEqual(
            sanitize_redirect(['myapp.com'], 'http://myapp.com/path/'),
            'http://myapp.com/path/'
        )

    def test_valid_relative_redirect(self):
        self.assertEqual(sanitize_redirect(['myapp.com'], '/path/'), '/path/')

    def test_multiple_hosts(self):
        allowed_hosts = ['myapp1.com', 'myapp2.com']
        for host in allowed_hosts:
            url = 'http://{}/path/'.format(host)
            self.assertEqual(sanitize_redirect(allowed_hosts, url), url)

    def test_multiple_hosts_wrong_host(self):
        self.assertEqual(sanitize_redirect(
            ['myapp1.com', 'myapp2.com'], 'http://notmyapp.com/path/'), None)


class UserIsAuthenticatedTest(unittest.TestCase):
    def test_user_is_none(self):
        self.assertEqual(user_is_authenticated(None), False)

    def test_user_is_not_none(self):
        self.assertEqual(user_is_authenticated(object()), True)

    def test_user_has_is_authenticated(self):
        class User(object):
            is_authenticated = True
        self.assertEqual(user_is_authenticated(User()), True)

    def test_user_has_is_authenticated_callable(self):
        class User(object):
            def is_authenticated(self):
                return True
        self.assertEqual(user_is_authenticated(User()), True)


class UserIsActiveTest(unittest.TestCase):
    def test_user_is_none(self):
        self.assertEqual(user_is_active(None), False)

    def test_user_is_not_none(self):
        self.assertEqual(user_is_active(object()), True)

    def test_user_has_is_active(self):
        class User(object):
            is_active = True
        self.assertEqual(user_is_active(User()), True)

    def test_user_has_is_active_callable(self):
        class User(object):
            def is_active(self):
                return True
        self.assertEqual(user_is_active(User()), True)


class SlugifyTest(unittest.TestCase):
    def test_slugify_formats(self):
        if PY3:
            self.assertEqual(slugify('FooBar'), 'foobar')
            self.assertEqual(slugify('Foo Bar'), 'foo-bar')
            self.assertEqual(slugify('Foo (Bar)'), 'foo-bar')
        else:
            self.assertEqual(slugify('FooBar'.decode('utf-8')), 'foobar')
            self.assertEqual(slugify('Foo Bar'.decode('utf-8')), 'foo-bar')
            self.assertEqual(slugify('Foo (Bar)'.decode('utf-8')), 'foo-bar')


class BuildAbsoluteURITest(unittest.TestCase):
    def setUp(self):
        self.host = 'http://foobar.com'

    def tearDown(self):
        self.host = None

    def test_path_none(self):
        self.assertEqual(build_absolute_uri(self.host), self.host)

    def test_path_empty(self):
        self.assertEqual(build_absolute_uri(self.host, ''), self.host)

    def test_path_http(self):
        self.assertEqual(build_absolute_uri(self.host, 'http://barfoo.com'),
                         'http://barfoo.com')

    def test_path_https(self):
        self.assertEqual(build_absolute_uri(self.host, 'https://barfoo.com'),
                         'https://barfoo.com')

    def test_host_ends_with_slash_and_path_starts_with_slash(self):
        self.assertEqual(build_absolute_uri(self.host + '/', '/foo/bar'),
                         'http://foobar.com/foo/bar')

    def test_absolute_uri(self):
        self.assertEqual(build_absolute_uri(self.host, '/foo/bar'),
                         'http://foobar.com/foo/bar')


class PartialPipelineData(unittest.TestCase):
    def test_returns_partial_when_uid_and_email_do_match(self):
        email = 'foo@example.com'
        backend = self._backend({'uid': email})
        backend.strategy.request_data.return_value = {
            backend.ID_KEY: email
        }
        key, val = ('foo', 'bar')
        partial = partial_pipeline_data(backend, None,
                                        *(), **dict([(key, val)]))
        self.assertTrue(key in partial.kwargs)
        self.assertEqual(partial.kwargs[key], val)
        self.assertEqual(backend.strategy.clean_partial_pipeline.call_count, 0)

    def test_clean_pipeline_when_uid_does_not_match(self):
        backend = self._backend({'uid': 'foo@example.com'})
        backend.strategy.request_data.return_value = {
            backend.ID_KEY: 'bar@example.com'
        }
        key, val = ('foo', 'bar')
        partial = partial_pipeline_data(backend, None,
                                        *(), **dict([(key, val)]))
        self.assertIsNone(partial)
        self.assertEqual(backend.strategy.clean_partial_pipeline.call_count, 1)

    def test_kwargs_included_in_result(self):
        backend = self._backend()
        key, val = ('foo', 'bar')
        partial = partial_pipeline_data(backend, None,
                                        *(), **dict([(key, val)]))
        self.assertTrue(key in partial.kwargs)
        self.assertEqual(partial.kwargs[key], val)
        self.assertEqual(backend.strategy.clean_partial_pipeline.call_count, 0)

    def test_update_user(self):
        user = object()
        backend = self._backend(session_kwargs={'user': None})
        partial = partial_pipeline_data(backend, user)
        self.assertTrue('user' in partial.kwargs)
        self.assertEqual(partial.kwargs['user'], user)
        self.assertEqual(backend.strategy.clean_partial_pipeline.call_count, 0)

    def _backend(self, session_kwargs=None):
        backend = Mock()
        backend.ID_KEY = 'email'
        backend.name = 'mock-backend'

        strategy = Mock()
        strategy.request = None
        strategy.request_data.return_value = {}
        strategy.session_get.return_value = object()
        strategy.partial_load.return_value = TestPartial.prepare(backend.name, 0, {
            'args': [],
            'kwargs': session_kwargs or {}
        })

        backend.strategy = strategy
        return backend
