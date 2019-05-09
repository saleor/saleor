import requests

from httpretty import HTTPretty

from ...actions import do_disconnect
from ...exceptions import NotAllowedToDisconnect
from ...utils import parse_qs

from ..models import User, TestUserSocialAuth
from .actions import BaseActionTest


class DisconnectActionTest(BaseActionTest):
    def test_not_allowed_to_disconnect(self):
        self.do_login()
        user = User.get(self.expected_username)
        with self.assertRaises(NotAllowedToDisconnect):
            do_disconnect(self.backend, user)

    def test_disconnect(self):
        self.do_login()
        user = User.get(self.expected_username)
        user.password = 'password'
        do_disconnect(self.backend, user)
        self.assertEqual(len(user.social), 0)

    def test_disconnect_with_association_id(self):
        self.do_login()
        user = User.get(self.expected_username)
        user.password = 'password'
        association_id = user.social[0].id
        second_usa = TestUserSocialAuth(user, user.social[0].provider, "uid2")
        self.assertEqual(len(user.social), 2)
        do_disconnect(self.backend, user, association_id)
        self.assertEqual(len(user.social), 1)
        self.assertEqual(user.social[0], second_usa)

    def test_disconnect_with_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_DISCONNECT_PIPELINE': (
                'social_core.tests.pipeline.ask_for_password',
                'social_core.tests.pipeline.set_password',
                'social_core.pipeline.disconnect.allowed_to_disconnect',
                'social_core.pipeline.disconnect.get_entries',
                'social_core.pipeline.disconnect.revoke_tokens',
                'social_core.pipeline.disconnect.disconnect'
            )
        })
        self.do_login()
        user = User.get(self.expected_username)
        redirect = do_disconnect(self.backend, user)

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

        redirect = do_disconnect(self.backend, user)
        self.assertEqual(len(user.social), 0)
