from ...utils import PARTIAL_TOKEN_SESSION_NAME
from ..models import User
from .actions import BaseActionTest


class LoginActionTest(BaseActionTest):
    def test_login(self):
        self.do_login()

    def test_login_with_partial_pipeline(self):
        self.do_login_with_partial_pipeline()

    def test_fields_stored_in_session(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_FIELDS_STORED_IN_SESSION': ['foo', 'bar']
        })
        self.strategy.set_request_data({'foo': '1', 'bar': '2'}, self.backend)
        self.do_login()
        self.assertEqual(self.strategy.session_get('foo'), '1')
        self.assertEqual(self.strategy.session_get('bar'), '2')

    def test_redirect_value(self):
        self.strategy.set_request_data({'next': '/after-login'}, self.backend)
        redirect = self.do_login(after_complete_checks=False)
        self.assertEqual(redirect.url, '/after-login')

    def test_login_with_invalid_partial_pipeline(self):
        def before_complete():
            partial_token = self.strategy.session_get(
                PARTIAL_TOKEN_SESSION_NAME
            )
            partial = self.strategy.storage.partial.load(partial_token)
            partial.data['backend'] = 'foobar'
        self.do_login_with_partial_pipeline(before_complete)

    def test_new_user(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_NEW_USER_REDIRECT_URL': '/new-user'
        })
        redirect = self.do_login(after_complete_checks=False)
        self.assertEqual(redirect.url, '/new-user')

    def test_inactive_user(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_INACTIVE_USER_URL': '/inactive'
        })
        User.set_active(False)
        redirect = self.do_login(after_complete_checks=False)
        self.assertEqual(redirect.url, '/inactive')

    def test_invalid_user(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_LOGIN_ERROR_URL': '/error',
            'SOCIAL_AUTH_PIPELINE': (
                'social_core.pipeline.social_auth.social_details',
                'social_core.pipeline.social_auth.social_uid',
                'social_core.pipeline.social_auth.auth_allowed',
                'social_core.pipeline.social_auth.social_user',
                'social_core.pipeline.user.get_username',
                'social_core.pipeline.user.create_user',
                'social_core.pipeline.social_auth.associate_user',
                'social_core.pipeline.social_auth.load_extra_data',
                'social_core.pipeline.user.user_details',
                'social_core.tests.pipeline.remove_user'
            )
        })
        redirect = self.do_login(after_complete_checks=False)
        self.assertEqual(redirect.url, '/error')
