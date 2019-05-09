import json

from ...exceptions import AuthAlreadyAssociated

from ..models import User
from .actions import BaseActionTest


class AssociateActionTest(BaseActionTest):
    expected_username = 'foobar'

    def setUp(self):
        super(AssociateActionTest, self).setUp()
        self.user = User(username='foobar', email='foo@bar.com')
        self.backend.strategy.session_set('username', self.user.username)

    def test_associate(self):
        self.do_login()
        self.assertTrue(len(self.user.social), 1)
        self.assertEqual(self.user.social[0].provider, 'github')

    def test_associate_with_partial_pipeline(self):
        self.do_login_with_partial_pipeline()
        self.assertEqual(len(self.user.social), 1)
        self.assertEqual(self.user.social[0].provider, 'github')


class MultipleAccountsTest(AssociateActionTest):
    alternative_user_data_body = json.dumps({
        'login': 'foobar2',
        'id': 2,
        'avatar_url': 'https://github.com/images/error/foobar2_happy.gif',
        'gravatar_id': 'somehexcode',
        'url': 'https://api.github.com/users/foobar2',
        'name': 'monalisa foobar2',
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
        'html_url': 'https://github.com/foobar2',
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

    def test_multiple_social_accounts(self):
        self.do_login()
        self.do_login(user_data_body=self.alternative_user_data_body)
        self.assertEqual(len(self.user.social), 2)
        self.assertEqual(self.user.social[0].provider, 'github')
        self.assertEqual(self.user.social[1].provider, 'github')


class AlreadyAssociatedErrorTest(BaseActionTest):
    def setUp(self):
        super(AlreadyAssociatedErrorTest, self).setUp()
        self.user1 = User(username='foobar', email='foo@bar.com')
        self.user = None

    def tearDown(self):
        super(AlreadyAssociatedErrorTest, self).tearDown()
        self.user1 = None
        self.user = None

    def test_already_associated_error(self):
        self.user = self.user1
        self.do_login()
        self.user = User(username='foobar2', email='foo2@bar2.com')
        with self.assertRaisesRegexp(AuthAlreadyAssociated,
                                     'This account is already in use.'):
            self.do_login()
