import json

from ..utils import PARTIAL_TOKEN_SESSION_NAME
from ..exceptions import AuthException

from .models import TestUserSocialAuth, TestStorage, User
from .strategy import TestStrategy
from .actions.actions import BaseActionTest


class IntegrityError(Exception):
    pass


class UnknownError(Exception):
    pass


class IntegrityErrorUserSocialAuth(TestUserSocialAuth):
    @classmethod
    def create_social_auth(cls, user, uid, provider):
        raise IntegrityError()

    @classmethod
    def get_social_auth(cls, provider, uid):
        if not hasattr(cls, '_called_times'):
            cls._called_times = 0
        cls._called_times += 1
        if cls._called_times == 2:
            user = list(User.cache.values())[0]
            return IntegrityErrorUserSocialAuth(user, provider, uid)
        else:
            return super(IntegrityErrorUserSocialAuth, cls).get_social_auth(
                provider, uid
            )


class IntegrityErrorStorage(TestStorage):
    user = IntegrityErrorUserSocialAuth

    @classmethod
    def is_integrity_error(cls, exception):
        """Check if given exception flags an integrity error in the DB"""
        return isinstance(exception, IntegrityError)


class UnknownErrorUserSocialAuth(TestUserSocialAuth):
    @classmethod
    def create_social_auth(cls, user, uid, provider):
        raise UnknownError()


class UnknownErrorStorage(IntegrityErrorStorage):
    user = UnknownErrorUserSocialAuth


class IntegrityErrorOnLoginTest(BaseActionTest):
    def setUp(self):
        self.strategy = TestStrategy(IntegrityErrorStorage)
        super(IntegrityErrorOnLoginTest, self).setUp()

    def test_integrity_error(self):
        self.do_login()


class UnknownErrorOnLoginTest(BaseActionTest):
    def setUp(self):
        self.strategy = TestStrategy(UnknownErrorStorage)
        super(UnknownErrorOnLoginTest, self).setUp()

    def test_unknown_error(self):
        with self.assertRaises(UnknownError):
            self.do_login()


class EmailAsUsernameTest(BaseActionTest):
    expected_username = 'foo@bar.com'

    def test_email_as_username(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL': True
        })
        self.do_login()


class RandomUsernameTest(BaseActionTest):
    user_data_body = json.dumps({
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

    def test_random_username(self):
        self.do_login(after_complete_checks=False)


class SluggedUsernameTest(BaseActionTest):
    expected_username = 'foo-bar'
    user_data_body = json.dumps({
        'login': 'Foo Bar',
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

    def test_random_username(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_CLEAN_USERNAMES': False,
            'SOCIAL_AUTH_SLUGIFY_USERNAMES': True
        })
        self.do_login()


class RepeatedUsernameTest(BaseActionTest):
    def test_random_username(self):
        User(username='foobar')
        self.do_login(after_complete_checks=False)
        self.assertTrue(self.strategy.session_get('username')
                                     .startswith('foobar'))


class AssociateByEmailTest(BaseActionTest):
    def test_multiple_accounts_with_same_email(self):
        user = User(username='foobar1')
        user.email = 'foo@bar.com'
        self.do_login(after_complete_checks=False)
        self.assertTrue(self.strategy.session_get('username')
                                     .startswith('foobar'))


class MultipleAccountsWithSameEmailTest(BaseActionTest):
    def test_multiple_accounts_with_same_email(self):
        user1 = User(username='foobar1')
        user2 = User(username='foobar2')
        user1.email = 'foo@bar.com'
        user2.email = 'foo@bar.com'
        with self.assertRaises(AuthException):
            self.do_login(after_complete_checks=False)


class UserPersistsInPartialPipeline(BaseActionTest):
    def test_user_persists_in_partial_pipeline_kwargs(self):
        user = User(username='foobar1')
        user.email = 'foo@bar.com'

        self.strategy.set_settings({
            'SOCIAL_AUTH_PIPELINE': (
                'social_core.pipeline.social_auth.social_details',
                'social_core.pipeline.social_auth.social_uid',
                'social_core.pipeline.social_auth.associate_by_email',
                'social_core.tests.pipeline.set_user_from_kwargs'
            )
        })

        self.do_login(after_complete_checks=False)

        # Handle the partial pipeline
        self.strategy.session_set('attribute', 'testing')
        token = self.strategy.session_pop(PARTIAL_TOKEN_SESSION_NAME)
        partial = self.strategy.partial_load(token)
        self.backend.continue_pipeline(partial)

    def test_user_persists_in_partial_pipeline(self):
        user = User(username='foobar1')
        user.email = 'foo@bar.com'

        self.strategy.set_settings({
            'SOCIAL_AUTH_PIPELINE': (
                'social_core.pipeline.social_auth.social_details',
                'social_core.pipeline.social_auth.social_uid',
                'social_core.pipeline.social_auth.associate_by_email',
                'social_core.tests.pipeline.set_user_from_args'
            )
        })

        self.do_login(after_complete_checks=False)

        # Handle the partial pipeline
        self.strategy.session_set('attribute', 'testing')
        token = self.strategy.session_pop(PARTIAL_TOKEN_SESSION_NAME)
        partial = self.strategy.partial_load(token)
        self.backend.continue_pipeline(partial)
