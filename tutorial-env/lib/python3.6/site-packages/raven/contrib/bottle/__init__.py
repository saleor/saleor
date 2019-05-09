"""
raven.contrib.bottle
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import sys

from bottle import request
from raven.conf import setup_logging
from raven.contrib.bottle.utils import get_data_from_request
from raven.handlers.logging import SentryHandler


class Sentry(object):
    """
    Bottle application for Sentry.

    >>> sentry = Sentry(app, client)

    Automatically configure logging::

    >>> sentry = Sentry(app, client, logging=True)

    Capture an exception::

    >>> try:
    >>>     1 / 0
    >>> except ZeroDivisionError:
    >>>     sentry.captureException()

    Capture a message::

    >>> sentry.captureMessage('hello, world!')
    """

    def __init__(self, app, client, logging=False):
        self.app = app
        self.client = client
        self.logging = logging
        if self.logging:
            setup_logging(SentryHandler(self.client))
        self.app.sentry = self

    def handle_exception(self, *args, **kwargs):
        self.client.captureException(
            exc_info=kwargs.get('exc_info'),
            data=get_data_from_request(request),
            extra={
                'app': self.app,
            },
        )

    def __call__(self, environ, start_response):
        def session_start_response(status, headers, exc_info=None):
            if exc_info is not None:
                self.handle_exception(exc_info=exc_info)
            return start_response(status, headers, exc_info)

        try:
            return self.app(environ, session_start_response)
        # catch ANY exception that goes through...
        except Exception:
            self.handle_exception(exc_info=sys.exc_info())
            # re-raise the exception to let parent handlers deal with it
            raise

    def captureException(self, *args, **kwargs):
        assert self.client, 'captureException called before application configured'
        data = kwargs.get('data')
        if data is None:
            try:
                kwargs['data'] = get_data_from_request(request)
            except RuntimeError:
                # app is probably not configured yet
                pass
        return self.client.captureException(*args, **kwargs)

    def captureMessage(self, *args, **kwargs):
        assert self.client, 'captureMessage called before application configured'
        data = kwargs.get('data')
        if data is None:
            try:
                kwargs['data'] = get_data_from_request(request)
            except RuntimeError:
                # app is probably not configured yet
                pass
        return self.client.captureMessage(*args, **kwargs)
