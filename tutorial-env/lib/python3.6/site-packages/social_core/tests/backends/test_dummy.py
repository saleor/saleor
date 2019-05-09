import json
import datetime
import time

from httpretty import HTTPretty

from ...actions import do_disconnect
from ...backends.oauth import BaseOAuth2
from ...exceptions import AuthForbidden

from ..models import User
from .oauth import OAuth2Test


class DummyOAuth2(BaseOAuth2):
    name = 'dummy'
    AUTHORIZATION_URL = 'http://dummy.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'http://dummy.com/oauth/access_token'
    REVOKE_TOKEN_URL = 'https://dummy.com/oauth/revoke'
    REVOKE_TOKEN_METHOD = 'GET'
    GET_ALL_EXTRA_DATA = False
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires'),
        ('empty', 'empty', True),
        'url'
    ]

    def get_user_details(self, response):
        """Return user details from Github account"""
        return {'username': response.get('username'),
                'email': response.get('email', ''),
                'first_name': response.get('first_name', ''),
                'last_name': response.get('last_name', '')}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json('http://dummy.com/user', params={
            'access_token': access_token
        })


class Dummy2OAuth2(DummyOAuth2):
    GET_ALL_EXTRA_DATA = True


class DummyOAuth2Test(OAuth2Test):
    backend_path = 'social_core.tests.backends.test_dummy.DummyOAuth2'
    user_data_url = 'http://dummy.com/user'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'id': 1,
        'username': 'foobar',
        'url': 'http://dummy.com/user/foobar',
        'first_name': 'Foo',
        'last_name': 'Bar',
        'email': 'foo@bar.com'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def test_tokens(self):
        user = self.do_login()
        self.assertEqual(user.social[0].access_token, 'foobar')

    def test_revoke_token(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_REVOKE_TOKENS_ON_DISCONNECT': True
        })
        self.do_login()
        user = User.get(self.expected_username)
        user.password = 'password'
        HTTPretty.register_uri(self._method(self.backend.REVOKE_TOKEN_METHOD),
                               self.backend.REVOKE_TOKEN_URL,
                               status=200)
        do_disconnect(self.backend, user)


class WhitelistEmailsTest(DummyOAuth2Test):
    def test_valid_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_WHITELISTED_EMAILS': ['foo@bar.com']
        })
        self.do_login()

    def test_invalid_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_WHITELISTED_EMAILS': ['foo2@bar.com']
        })
        with self.assertRaises(AuthForbidden):
            self.do_login()


class WhitelistDomainsTest(DummyOAuth2Test):
    def test_valid_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_WHITELISTED_DOMAINS': ['bar.com']
        })
        self.do_login()

    def test_invalid_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_WHITELISTED_EMAILS': ['bar2.com']
        })
        with self.assertRaises(AuthForbidden):
            self.do_login()


DELTA = datetime.timedelta(days=1)


class ExpirationTimeTest(DummyOAuth2Test):
    user_data_body = json.dumps({
        'id': 1,
        'username': 'foobar',
        'url': 'http://dummy.com/user/foobar',
        'first_name': 'Foo',
        'last_name': 'Bar',
        'email': 'foo@bar.com',
        'expires': time.mktime((datetime.datetime.utcnow() +
                                DELTA).timetuple())
    })

    def test_expires_time(self):
        user = self.do_login()
        social = user.social[0]
        expiration = social.expiration_timedelta()
        self.assertEqual(expiration <= DELTA, True)


class AllExtraDataTest(DummyOAuth2Test):
    backend_path = 'social_core.tests.backends.test_dummy.Dummy2OAuth2'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'id': 1,
        'username': 'foobar',
        'url': 'http://dummy.com/user/foobar',
        'first_name': 'Foo',
        'last_name': 'Bar',
        'email': 'foo@bar.com',
        'not_normally_in_extra_data': 'value'
    })

    def test_get_all_extra_data(self):
        user = self.do_login()
        social = user.social[0]
        self.assertIn('not_normally_in_extra_data', social.extra_data)
        self.assertEqual(len(social.extra_data), 10)  # Includes auth_time.
