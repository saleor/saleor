import six
import random
import unittest2 as unittest

from ..strategy import BaseStrategy
from ..storage import UserMixin, NonceMixin, AssociationMixin, \
                      CodeMixin, BaseStorage

from .models import User


NOT_IMPLEMENTED_MSG = 'Implement in subclass'


class BrokenUser(UserMixin):
    pass


class BrokenAssociation(AssociationMixin):
    pass


class BrokenNonce(NonceMixin):
    pass


class BrokenCode(CodeMixin):
    pass


class BrokenStrategy(BaseStrategy):
    pass


class BrokenStrategyWithSettings(BrokenStrategy):
    def get_setting(self, name):
        raise AttributeError()


class BrokenStorage(BaseStorage):
    pass


class BrokenUserTests(unittest.TestCase):

    def setUp(self):
        self.user = BrokenUser

    def tearDown(self):
        self.user = None

    def test_get_username(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.user.get_username(User('foobar'))

    def test_user_model(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.user.user_model()

    def test_username_max_length(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.user.username_max_length()

    def test_get_user(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.user.get_user(1)

    def test_get_social_auth(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.user.get_social_auth('foo', 1)

    def test_get_social_auth_for_user(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.user.get_social_auth_for_user(User('foobar'))

    def test_create_social_auth(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.user.create_social_auth(User('foobar'), 1, 'foo')

    def test_disconnect(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.user.disconnect(BrokenUser())


class BrokenAssociationTests(unittest.TestCase):
    def setUp(self):
        self.association = BrokenAssociation

    def tearDown(self):
        self.association = None

    def test_store(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.association.store('http://foobar.com', BrokenAssociation())

    def test_get(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.association.get()

    def test_remove(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.association.remove([1, 2, 3])


class BrokenNonceTests(unittest.TestCase):
    def setUp(self):
        self.nonce = BrokenNonce

    def tearDown(self):
        self.nonce = None

    def test_use(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.nonce.use('http://foobar.com', 1364951922, 'foobar123')


class BrokenCodeTest(unittest.TestCase):
    def setUp(self):
        self.code = BrokenCode

    def tearDown(self):
        self.code = None

    def test_get_code(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.code.get_code('foobar')


class BrokenStrategyTests(unittest.TestCase):
    def setUp(self):
        self.strategy = BrokenStrategy(storage=BrokenStorage)

    def tearDown(self):
        self.strategy = None

    def test_redirect(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.redirect('http://foobar.com')

    def test_get_setting(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.get_setting('foobar')

    def test_html(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.html('<p>foobar</p>')

    def test_request_data(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.request_data()

    def test_request_host(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.request_host()

    def test_session_get(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.session_get('foobar')

    def test_session_set(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.session_set('foobar', 123)

    def test_session_pop(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.session_pop('foobar')

    def test_build_absolute_uri(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.build_absolute_uri('/foobar')

    def test_render_html_with_tpl(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.render_html('foobar.html', context={})

    def test_render_html_with_html(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.render_html(html='<p>foobar</p>', context={})

    def test_render_html_with_none(self):
        with self.assertRaisesRegexp(ValueError,
                                     'Missing template or html parameters'):
            self.strategy.render_html()

    def test_is_integrity_error(self):
        with self.assertRaisesRegexp(NotImplementedError, NOT_IMPLEMENTED_MSG):
            self.strategy.storage.is_integrity_error(None)

    def test_random_string(self):
        self.assertTrue(isinstance(self.strategy.random_string(),
                                   six.string_types))

    def test_random_string_without_systemrandom(self):
        def SystemRandom():
            raise NotImplementedError()

        orig_random = getattr(random, 'SystemRandom', None)
        random.SystemRandom = SystemRandom

        strategy = BrokenStrategyWithSettings(storage=BrokenStorage)
        self.assertTrue(isinstance(strategy.random_string(), six.string_types))
        random.SystemRandom = orig_random
