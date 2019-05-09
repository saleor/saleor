"""
raven.contrib.webpy
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import sys

import web

from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler
from raven.contrib.webpy.utils import get_data_from_request


class SentryApplication(web.application):
    """
    Web.py application for Sentry.

    >>> sentry = Sentry(client, mapping=urls, fvars=globals())

    Automatically configure logging::

    >>> sentry = Sentry(client, logging=True, mapping=urls, fvars=globals())

    Capture an exception::

    >>> try:
    >>>     1 / 0
    >>> except ZeroDivisionError:
    >>>     sentry.captureException()

    Capture a message::

    >>> sentry.captureMessage('hello, world!')
    """

    def __init__(self, client, logging=False, **kwargs):
        self.client = client
        self.logging = logging
        if self.logging:
            setup_logging(SentryHandler(self.client))
        web.application.__init__(self, **kwargs)

    def handle_exception(self, *args, **kwargs):
        self.client.captureException(
            exc_info=kwargs.get('exc_info'),
            data=get_data_from_request(),
            extra={
                'app': self,
            },
        )

    def handle(self):
        try:
            return web.application.handle(self)
        except Exception:
            self.handle_exception(exc_info=sys.exc_info())
            raise

    def captureException(self, *args, **kwargs):
        assert self.client, 'captureException called before application configured'
        data = kwargs.get('data')
        if data is None:
            kwargs['data'] = get_data_from_request()

        return self.client.captureException(*args, **kwargs)

    def captureMessage(self, *args, **kwargs):
        assert self.client, 'captureMessage called before application configured'
        data = kwargs.get('data')
        if data is None:
            kwargs['data'] = get_data_from_request()

        return self.client.captureMessage(*args, **kwargs)
