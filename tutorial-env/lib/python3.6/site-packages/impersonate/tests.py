# -*- coding: utf-8 -*-
'''
    Tests
    Factory creates 4 User accounts.
    user1:
        id = 1
        is_superuser = True
        is_staff = True
    user2:
        id = 2
        is_superuser = True
        is_staff = True
    user3:
        id = 3
        is_superuser = False
        is_staff = True
    user4:
        id = 4
        is_superuser = False
        is_staff = False
'''
import datetime
from collections import namedtuple
from distutils.version import LooseVersion
from unittest.mock import patch, PropertyMock

import django
from django.test import TestCase
from django.http import HttpResponse
from django.utils import six, timezone
from django.conf.urls import url, include
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.contrib.admin.sites import AdminSite
from django.test.client import Client, RequestFactory

from .models import ImpersonationLog
from .signals import session_begin, session_end
from .helpers import duration_string, users_impersonable, is_authenticated
from .admin import (
    SessionStateFilter, ImpersonatorFilter, ImpersonationLogAdmin,
)


try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

try:
    # Python 3
    from urllib.parse import urlencode, urlsplit
except ImportError:
    import factory
    from urllib import urlencode
    from urlparse import urlsplit

User = get_user_model()
django_version_loose = LooseVersion(django.get_version())


def test_view(request):
    return HttpResponse('OK {0}'.format(request.user))


urlpatterns = [
    url(r'^test-view/$',
        test_view,
        name='impersonate-test'),
    url(r'^another-view/$',
        test_view,
        name='another-test-view'),
    url('^', include('impersonate.urls')),
]


def test_allow(request):
    ''' Used via the IMPERSONATE['CUSTOM_ALLOW'] setting.
        Simple check for the user to be auth'd and a staff member.
    '''
    return is_authenticated(request.user) and request.user.is_staff


def test_allow2(request):
    ''' Used via the IMPERSONATE['CUSTOM_ALLOW'] setting.
        Always return False
    '''
    return False


def test_qs(request):
    ''' Used via the IMPERSONAT['CUSTOM_USER_QUERYSET'] setting.
        Simple function to return all users.
    '''
    return User.objects.all()


if six.PY3:
    # Temporary until factory_boy gets Py3k support
    class UserFactory(object):
        @staticmethod
        def create(**kwargs):
            password = kwargs.pop('password', None)
            kwargs['email'] = \
                '{0}@test-email.com'.format(kwargs['username']).lower()
            user = User.objects.create(**kwargs)
            if password:
                user.set_password(password)
                user.save()
            return user
else:
    class UserFactory(factory.Factory):
        FACTORY_FOR = User

        email = factory.LazyAttribute(
            lambda a: '{0}@test-email.com'.format(a.username).lower()
        )

        @classmethod
        def _prepare(cls, create, **kwargs):
            password = kwargs.pop('password', None)
            user = super(UserFactory, cls)._prepare(create, **kwargs)
            if password:
                user.set_password(password)
                if create:
                    user.save()
            return user


class TestMiddleware(TestCase):
    def setUp(self):
        from impersonate.middleware import ImpersonateMiddleware

        self.superuser = UserFactory.create(
            username='superuser',
            is_superuser=True,
        )
        self.user = UserFactory.create(username='regular')
        self.factory = RequestFactory()
        self.middleware = ImpersonateMiddleware()

    def _impersonated_request(self, use_id=True):
        request = self.factory.get('/')
        request.user = self.superuser
        request.session = {
            '_impersonate': self.user.pk if use_id else self.user,
        }
        self.middleware.process_request(request)

        # Check request.user and request.user.real_user
        self.assertEqual(request.user, self.user)
        self.assertEqual(request.impersonator, self.superuser)
        self.assertEqual(request.real_user, self.superuser)
        self.assertTrue(request.user.is_impersonate)

    def test_impersonated_request(self):
        self._impersonated_request()

    def test_impersonated_request_non_id(self):
        ''' Test to ensure User objects don't kill the app.
            See Issue #15
        '''
        self._impersonated_request(use_id=False)

    def test_not_impersonated_request(self, use_id=True):
        """Check the real_user request attr is set correctly when **not** impersonating."""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        self.middleware.process_request(request)
        # Check request.user and request.user.real_user
        self.assertEqual(request.user, self.user)
        self.assertIsNone(request.impersonator, None)
        self.assertEqual(request.real_user, self.user)
        self.assertFalse(request.user.is_impersonate)


class TestImpersonation(TestCase):

    def setUp(self):
        self.client = Client()
        user_data = (
            ('John', 'Smith', True, True),
            ('John', 'Doe', True, True),
            ('', '', False, True),
            ('', '', False, False),
        )
        for cnt, data in enumerate(user_data):
            UserFactory.create(**{
                'username': 'user{0}'.format(cnt + 1),
                'first_name': data[0],
                'last_name': data[1],
                'is_superuser': data[2],
                'is_staff': data[3],
                'password': 'foobar',
            })

    def _impersonate_helper(
        self,
        user,
        passwd,
        user_id_to_impersonate,
        qwargs={},
        starting_url=None
    ):
        ''' Trigger impersonate mode for a particular user id, using
            the specified authenticated user.

            The HTTP_REFERER can be simulated by passing the optional
            `starting_url` arg.
        '''

        self.client.login(username=user, password=passwd)

        url = reverse('impersonate-start', args=[user_id_to_impersonate])
        if qwargs:
            url += '?{0}'.format(urlencode(qwargs))

        args = [url]
        kwargs = {}
        if starting_url:
            kwargs['HTTP_REFERER'] = starting_url
        return self.client.get(*args, **kwargs)

    def _redirect_check(self, response, new_path):
        ''' Needed because assertRedirect fails because it checks
            that the new path is able to be fetched. That's going
            to raise a TemplateDoesNotExist exception (usually).
            This is just a work around.
        '''
        url = response['Location']
        scheme, netloc, path, query, fragment = urlsplit(url)
        self.assertEqual(path, new_path)

    def test_user_count(self):
        self.assertEqual(User.objects.count(), 4)

    def test_dont_impersonate_superuser(self):
        response = self._impersonate_helper('user1', 'foobar', 2)
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

        # Try again with normal staff user
        response = self._impersonate_helper('user3', 'foobar', 2)
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    def test_successful_impersonation(self):
        response = self._impersonate_helper('user1', 'foobar', 4)
        self.assertEqual(self.client.session['_impersonate'], 4)
        self.client.get(reverse('impersonate-stop'))
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    def test_successful_impersonation_signals(self):

        # flags used to determine that signals have been sent
        self.session_begin_fired = False
        self.session_end_fired = False

        def on_session_begin(sender, **kwargs):
            self.session_begin_fired = True
            self.assertIsNone(sender)
            self.assertIsNotNone(kwargs.pop('request', None))
            self.assertEqual(kwargs.pop('impersonator').username, 'user1')
            self.assertEqual(kwargs.pop('impersonating').username, 'user4')

        def on_session_end(sender, **kwargs):
            self.session_end_fired = True
            self.assertIsNone(sender)
            self.assertIsNotNone(kwargs.pop('request', None))
            self.assertEqual(kwargs.pop('impersonator').username, 'user1')
            impersonating = kwargs.pop('impersonating')
            self.assertEqual(impersonating.username, 'user4')

        self.assertFalse(self.session_begin_fired)
        self.assertFalse(self.session_end_fired)
        session_begin.connect(on_session_begin)
        session_end.connect(on_session_end)

        # start the impersonation and check that the _begin signal is sent
        response = self._impersonate_helper('user1', 'foobar', 4)
        self.assertEqual(self.client.session['_impersonate'], 4)
        self.assertTrue(self.session_begin_fired)
        self.assertFalse(self.session_end_fired)

        # now stop the impersonation and check that the _end signal is sent
        self.client.get(reverse('impersonate-stop'))
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.assertTrue(self.session_end_fired)

        # Reset for edge case failure. Ref Issue #34
        self.session_begin_fired = False
        self.session_end_fired = False
        self.assertFalse(self.session_begin_fired)
        self.assertFalse(self.session_end_fired)

        # Start impersonation
        response = self._impersonate_helper('user1', 'foobar', 4)
        self.assertTrue(self.session_begin_fired)
        self.assertFalse(self.session_end_fired)

        _session = self.client.session
        _session['_impersonate'] = 1234  # Invalid User ID
        _session.save()
        self.client.get(reverse('impersonate-stop'))
        self.assertFalse(self.session_end_fired)

        self.client.logout()
        session_begin.disconnect(on_session_begin)
        session_end.disconnect(on_session_end)

    def test_successsful_impersonation_by_staff(self):
        response = self._impersonate_helper('user3', 'foobar', 4)
        self.assertEqual(self.client.session['_impersonate'], 4)
        self.client.get(reverse('impersonate-stop'))
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    @override_settings(IMPERSONATE={'ALLOW_SUPERUSER': True})
    def test_successful_impersonation_of_superuser(self):
        response = self._impersonate_helper('user1', 'foobar', 2)
        self.assertEqual(self.client.session.get('_impersonate'), 2)
        user = User.objects.get(pk=self.client.session.get('_impersonate'))
        self.assertTrue(user.is_superuser)
        self.client.get(reverse('impersonate-stop'))
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    @override_settings(IMPERSONATE={'REQUIRE_SUPERUSER': True})
    def test_unsuccessful_impersonation_by_staff(self):
        response = self._impersonate_helper('user3', 'foobar', 4)
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    @override_settings(IMPERSONATE={'ALLOW_SUPERUSER': False})
    def test_unsuccessful_impersonation_of_superuser(self):
        response = self._impersonate_helper('user1', 'foobar', 2)
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    def test_unsuccessful_impersonation(self):
        response = self._impersonate_helper('user4', 'foobar', 3)
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    def test_unsuccessful_impersonation_restricted_uri(self):
        response = self._impersonate_helper('user1', 'foobar', 4)
        self.assertEqual(self.client.session['_impersonate'], 4)

        # Don't allow impersonated users to use impersonate views
        with self.settings(LOGIN_REDIRECT_URL='/test-redirect/'):
            response = self.client.get(reverse('impersonate-list'))
            self._redirect_check(response, '/test-redirect/')

        # Don't allow impersonated users to use restricted URI's
        with self.settings(IMPERSONATE={'URI_EXCLUSIONS': r'^test-view/'}):
            response = self.client.get(reverse('impersonate-test'))
            self.assertEqual(('user1' in str(response.content)), True) # !user4

        self.client.logout()

    def test_unsuccessful_request_unauth_user(self):
        response = self.client.get(reverse('impersonate-list'))
        self._redirect_check(response, '/accounts/login/')

    @override_settings(IMPERSONATE={'REDIRECT_URL': '/test-redirect/'})
    def test_successful_impersonation_redirect_url(self):
        response = self._impersonate_helper('user1', 'foobar', 4)
        self.assertEqual(self.client.session['_impersonate'], 4)
        self._redirect_check(response, '/test-redirect/')
        self.client.get(reverse('impersonate-stop'))
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    @override_settings(IMPERSONATE={'REDIRECT_FIELD_NAME': 'next'})
    def test_successful_impersonation_redirect_field_name(self):
        response = self._impersonate_helper(
            'user1',
            'foobar',
            4,
            {'next': '/test-next/'},
        )
        self.assertEqual(self.client.session['_impersonate'], 4)
        self._redirect_check(response, '/test-next/')
        self.client.get(reverse('impersonate-stop'))
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    @override_settings(LOGIN_REDIRECT_URL='/test-redirect-2/')
    def test_successful_impersonation_login_redirect_url(self):
        response = self._impersonate_helper('user1', 'foobar', 4)
        self.assertEqual(self.client.session['_impersonate'], 4)
        self._redirect_check(response, '/test-redirect-2/')
        self.client.get(reverse('impersonate-stop'))
        self.assertEqual(self.client.session.get('_impersonate'), None)
        self.client.logout()

    @override_settings(IMPERSONATE={'USE_HTTP_REFERER': True})
    def test_returned_to_original_path_after_impersonation(self):

        # show with and without querystrings works
        for starting_url in [
            reverse('another-test-view'),
            reverse('another-test-view') + '?test=true&foo=bar',
        ]:
            response = self._impersonate_helper(
                user='user1',
                passwd='foobar',
                user_id_to_impersonate=4,
                starting_url=starting_url
            )
            self.assertEqual(self.client.session['_impersonate'], 4)
            self._redirect_check(response, '/accounts/profile/')
            response = self.client.get(reverse('impersonate-stop'))

            # Can't use self._redirect_check here because it doesn't
            # compare querystrings
            self.assertEqual(
                'http://testserver{0}'.format(starting_url),
                response._headers['location'][1]
            )
            self.assertEqual(self.client.session.get('_impersonate'), None)
            self.client.logout()

    def test_successful_impersonation_end_redirect_url(self):
        for url_path, use_refer in (
            (reverse('another-test-view'), True),
            (reverse('another-test-view'), False),
        ):
            with self.settings(IMPERSONATE={
                'REDIRECT_URL': '/test-redirect/',
                'USE_HTTP_REFERER': use_refer,
            }):
                response = self._impersonate_helper(
                    'user1',
                    'foobar',
                    4,
                    starting_url=url_path,
                )
                self.assertEqual(self.client.session['_impersonate'], 4)
                self._redirect_check(response, '/test-redirect/')
                response = self.client.get(reverse('impersonate-stop'))
                use_url_path = url_path if use_refer else '/test-redirect/'

                if not use_refer and django_version_loose >= '1.9':
                    self.assertEqual(
                        use_url_path,
                        response._headers['location'][1]
                    )
                else:
                    self.assertEqual(
                        'http://testserver{0}'.format(use_url_path),
                        response._headers['location'][1]
                    )

                self.assertEqual(self.client.session.get('_impersonate'), None)
                self.client.logout()

    def test_user_listing_and_pagination(self):
        self.client.login(username='user1', password='foobar')
        response = self.client.get(reverse('impersonate-list'))
        self.assertEqual(response.context['users'].count(), 4)

        with self.settings(IMPERSONATE={'PAGINATE_COUNT': 2}):
            response = self.client.get(reverse('impersonate-list'))
            self.assertEqual(response.context['paginator'].num_pages, 2)

        # Out of range page number
        response = self.client.get(reverse('impersonate-list'), {'page': 10})
        self.assertEqual(response.context['page_number'], 10)
        self.assertEqual(response.context['page'], None)

        # Invalid integer
        response = self.client.get(reverse('impersonate-list'), {'page': 'no'})
        self.assertEqual(response.context['page_number'], 1)
        self.assertEqual(len(response.context['page'].object_list), 4)

        self.client.logout()

    def test_user_search_and_pagination(self):
        self.client.login(username='user1', password='foobar')
        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'john'},
        )
        self.assertEqual(response.context['users'].count(), 2)

        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'doe'},
        )
        self.assertEqual(response.context['users'].count(), 1)

        response = self.client.get(
            reverse('impersonate-search'),
            {'q': '   john   doe'},
        )
        self.assertEqual(response.context['users'].count(), 1)

        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'noresultsfound'},
        )
        self.assertEqual(response.context['users'].count(), 0)

        with self.settings(IMPERSONATE={'PAGINATE_COUNT': 2}):
            response = self.client.get(
                reverse('impersonate-search'),
                {'q': 'test-email'},
            )
            self.assertEqual(response.context['paginator'].num_pages, 2)
            self.assertEqual(response.context['users'].count(), 4)
        self.client.logout()

    @override_settings(
        IMPERSONATE={'SEARCH_FIELDS': ['first_name', 'last_name']})
    def test_user_search_custom_fields(self):
        self.client.login(username='user1', password='foobar')
        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'john'},
        )
        self.assertEqual(response.context['users'].count(), 2)

        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'doe'},
        )
        self.assertEqual(response.context['users'].count(), 1)

        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'user'},
        )
        self.assertEqual(response.context['users'].count(), 0)
        self.client.logout()

    @override_settings(IMPERSONATE={'LOOKUP_TYPE': 'exact'})
    def test_user_search_custom_lookup(self):
        self.client.login(username='user1', password='foobar')
        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'John'},
        )
        self.assertEqual(response.context['users'].count(), 2)

        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'Doe'},
        )
        self.assertEqual(response.context['users'].count(), 1)

        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'john'},
        )
        self.assertEqual(response.context['users'].count(), 0)

        response = self.client.get(
            reverse('impersonate-search'),
            {'q': 'doe'},
        )
        self.assertEqual(response.context['users'].count(), 0)

    @override_settings(IMPERSONATE={'REDIRECT_FIELD_NAME': 'next'})
    def test_redirect_field_name(self):
        self.client.login(username='user1', password='foobar')
        response = self.client.get(reverse('impersonate-list'))
        self.assertEqual(response.context['redirect'], '')

        # Add redirect value to query
        response = self.client.get(
            reverse('impersonate-list'),
            {'next': '/test/'},
        )
        self.assertEqual(response.context['redirect'], '?next=/test/')
        self.client.logout()

    @override_settings(IMPERSONATE={'REDIRECT_FIELD_NAME': 'next'})
    def test_redirect_field_name_unicode(self):
        ''' Specific test to account for Issue #21
        '''
        self.client.login(username='user1', password='foobar')
        response = self.client.get(reverse('impersonate-list'))
        self.assertEqual(response.context['redirect'], '')

        # Add redirect value to query
        response = self.client.get(
            reverse('impersonate-list'),
            {'next': u'/über/'},
        )
        self.assertEqual(response.context['redirect'], u'?next=/über/')
        self.client.logout()

    @override_settings(
        IMPERSONATE={'CUSTOM_ALLOW': 'impersonate.tests.test_allow'})
    def test_custom_user_allow_function(self):
        self.client.login(username='user1', password='foobar')
        response = self.client.get(reverse('impersonate-list'))
        self.assertEqual(response.context['users'].count(), 4)
        self.client.logout()

    def test_custom_user_allow_function_false(self):
        ''' Edge case test.
        '''
        response = self._impersonate_helper('user1', 'foobar', 4)
        with self.settings(
                IMPERSONATE={'CUSTOM_ALLOW': 'impersonate.tests.test_allow2'}):
            response = self.client.get(reverse('impersonate-test'))
            self.assertEqual(('user1' in str(response.content)), True) # !user4

    def test_custom_user_queryset_ordered(self):
        qs = users_impersonable(None)
        self.assertEqual(qs.ordered, True)

    @override_settings(
        IMPERSONATE={'CUSTOM_USER_QUERYSET': 'impersonate.tests.test_qs'})
    def test_custom_user_queryset_function(self):
        self.client.login(username='user1', password='foobar')
        response = self.client.get(reverse('impersonate-list'))
        self.assertEqual(response.context['users'].count(), 4)
        self.client.logout()

    def test_disable_impersonatelog_logging(self):
        self.assertFalse(ImpersonationLog.objects.exists())
        response = self._impersonate_helper('user1', 'foobar', 4)
        self.assertFalse(ImpersonationLog.objects.exists())

    @override_settings(IMPERSONATE={'DISABLE_LOGGING': False})
    def test_signals_session_begin_impersonatelog(self):
        self.assertFalse(ImpersonationLog.objects.exists())
        response = self._impersonate_helper('user1', 'foobar', 4)
        log = ImpersonationLog.objects.get()
        session_key = self.client.session.get('_impersonate_session_id')
        self.assertEqual(log.impersonator.id, 1)
        self.assertEqual(log.impersonating.id, 4)
        self.assertEqual(log.session_key, session_key)
        self.assertIsNotNone(log.session_started_at)
        self.assertIsNone(log.session_ended_at)

    @override_settings(IMPERSONATE={'DISABLE_LOGGING': False})
    def test_signals_session_end_impersonatelog(self):
        self.assertFalse(ImpersonationLog.objects.exists())
        response = self._impersonate_helper('user1', 'foobar', 4)
        session_key = self.client.session.get('_impersonate_session_id')
        self.client.get(reverse('impersonate-stop'))
        none_session_key = self.client.session.get('_impersonate_session_id')

        log = ImpersonationLog.objects.get()
        self.assertEqual(log.impersonator.id, 1)
        self.assertEqual(log.impersonating.id, 4)
        self.assertEqual(log.session_key, session_key)
        self.assertIsNotNone(log.session_started_at)
        self.assertIsNotNone(log.session_ended_at)
        self.assertIsNone(none_session_key)
        self.assertTrue(log.session_ended_at > log.session_started_at)
        self.assertEqual(
            log.duration,
            duration_string(log.session_ended_at - log.session_started_at),
        )

    @override_settings(IMPERSONATE={'DISABLE_LOGGING': False})
    def test_impersonatelog_admin_session_state_filter(self):
        ''' Based on http://stackoverflow.com/questions/16751325/test-a-custom-filter-in-admin-py
        '''
        self.assertFalse(ImpersonationLog.objects.exists())
        self._impersonate_helper('user1', 'foobar', 4)
        self.client.get(reverse('impersonate-stop'))
        self._impersonate_helper('user2', 'foobar', 4)

        _filter = SessionStateFilter(
            None,
            {},
            ImpersonationLog,
            ImpersonationLogAdmin,
        )
        qs = _filter.queryset(None, ImpersonationLog.objects.all())
        self.assertEqual(qs.count(), 2)

        _filter = SessionStateFilter(
            None,
            {'session': 'complete'},
            ImpersonationLog,
            ImpersonationLogAdmin,
        )
        qs = _filter.queryset(None, ImpersonationLog.objects.all())
        self.assertEqual(qs.count(), 1)

        _filter = SessionStateFilter(
            None,
            {'session': 'incomplete'},
            ImpersonationLog,
            ImpersonationLogAdmin,
        )
        qs = _filter.queryset(None, ImpersonationLog.objects.all())
        self.assertEqual(qs.count(), 1)

    @override_settings(IMPERSONATE={'DISABLE_LOGGING': False})
    def test_impersonatelog_admin_impersonator_filter(self):
        self.assertFalse(ImpersonationLog.objects.exists())
        self._impersonate_helper('user1', 'foobar', 4)
        self.client.get(reverse('impersonate-stop'))
        self._impersonate_helper('user2', 'foobar', 4)
        self.client.get(reverse('impersonate-stop'))
        self._impersonate_helper('user3', 'foobar', 4)
        self.client.get(reverse('impersonate-stop'))
        model_admin = ImpersonationLogAdmin(ImpersonationLog, AdminSite())

        _filter = ImpersonatorFilter(
            None,
            {},
            ImpersonationLog,
            model_admin,
        )
        qs = _filter.queryset(None, ImpersonationLog.objects.all())
        self.assertEqual(qs.count(), 3)

        _filter = ImpersonatorFilter(
            None,
            {'impersonator': '1'},
            ImpersonationLog,
            model_admin,
        )
        qs = _filter.queryset(None, ImpersonationLog.objects.all())
        self.assertEqual(qs.count(), 1)

        _filter = ImpersonatorFilter(
            None,
            {'impersonator': '2'},
            ImpersonationLog,
            model_admin,
        )
        qs = _filter.queryset(None, ImpersonationLog.objects.all())
        self.assertEqual(qs.count(), 1)

        _filter = ImpersonatorFilter(
            None,
            {'impersonator': '3'},
            ImpersonationLog,
            model_admin,
        )
        qs = _filter.queryset(None, ImpersonationLog.objects.all())
        self.assertEqual(qs.count(), 1)

        with patch(
            'django.contrib.auth.models.AbstractUser.USERNAME_FIELD',
            new_callable=PropertyMock,
            return_value='is_active',
        ):
            # Check that user1, user2, and user3 are in the lookup options
            opts = [(_id, name) for _id, name in
                        _filter.lookups(None, model_admin)]
            self.assertTrue(1 in [x[0] for x in opts])
            self.assertTrue(2 in [x[0] for x in opts])
            self.assertTrue(3 in [x[0] for x in opts])

            # Check that `USERNAME_FIELD` field is used
            # (`username` should not be hard-coded)
            self.assertTrue(True in [x[1] for x in opts])

    @override_settings(IMPERSONATE={'DISABLE_LOGGING': False,
                                    'MAX_FILTER_SIZE': 1})
    def test_impersonatelog_admin_impersonator_filter_max_filter_size(self):
        self.assertFalse(ImpersonationLog.objects.exists())
        self._impersonate_helper('user1', 'foobar', 4)
        self.client.get(reverse('impersonate-stop'))
        self._impersonate_helper('user2', 'foobar', 4)
        self.client.get(reverse('impersonate-stop'))

        model_admin = ImpersonationLogAdmin(ImpersonationLog, AdminSite())
        _filter = ImpersonatorFilter(
            None,
            {},
            ImpersonationLog,
            model_admin,
        )
        opts = [(_id, name) for _id, name in
                    _filter.lookups(None, model_admin)]
        self.assertEqual(len(opts), 0)
