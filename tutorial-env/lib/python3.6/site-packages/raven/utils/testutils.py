"""
raven.utils.testutils
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import raven

from exam import Exam

try:
    from unittest2 import TestCase as BaseTestCase
except ImportError:
    from unittest import TestCase as BaseTestCase  # NOQA


class TestCase(Exam, BaseTestCase):
    pass


class InMemoryClient(raven.Client):
    def __init__(self, **kwargs):
        self.events = []
        super(InMemoryClient, self).__init__(**kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)
