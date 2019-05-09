import unittest2 as unittest

from ...backends.base import BaseAuth
from ..strategy import TestStrategy
from ..models import TestStorage


class BrokenBackendAuth(BaseAuth):
    name = 'broken'


class BrokenBackendTest(unittest.TestCase):
    def setUp(self):
        self.backend = BrokenBackendAuth(TestStrategy(TestStorage))

    def tearDown(self):
        self.backend = None

    def test_auth_url(self):
        with self.assertRaisesRegexp(NotImplementedError,
                                     'Implement in subclass'):
            self.backend.auth_url()

    def test_auth_html(self):
        with self.assertRaisesRegexp(NotImplementedError,
                                     'Implement in subclass'):
            self.backend.auth_html()

    def test_auth_complete(self):
        with self.assertRaisesRegexp(NotImplementedError,
                                     'Implement in subclass'):
            self.backend.auth_complete()

    def test_get_user_details(self):
        with self.assertRaisesRegexp(NotImplementedError,
                                     'Implement in subclass'):
            self.backend.get_user_details(None)
