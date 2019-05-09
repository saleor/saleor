"""
raven.contrib.django.handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging

from raven.handlers.logging import SentryHandler as BaseSentryHandler
from raven.utils import memoize


class SentryHandler(BaseSentryHandler):
    def __init__(self, *args, **kwargs):
        # TODO(dcramer): we'd like to avoid this duplicate code, but we need
        # to currently defer loading client due to Django loading patterns.
        self.tags = kwargs.pop('tags', None)

        logging.Handler.__init__(self, level=kwargs.get('level', logging.NOTSET))

    @memoize
    def client(self):
        # Import must be lazy for deffered Django loading
        from raven.contrib.django.models import client
        return client

    def _emit(self, record):
        request = getattr(record, 'request', None)
        return super(SentryHandler, self)._emit(record, request=request)
