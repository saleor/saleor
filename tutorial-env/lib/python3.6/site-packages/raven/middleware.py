"""
raven.middleware
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from contextlib import contextmanager

from raven.utils.compat import Iterator, next
from raven.utils.wsgi import (
    get_current_url, get_headers, get_environ)


@contextmanager
def common_exception_handling(environ, client):
    try:
        yield
    except (StopIteration, GeneratorExit):
        # Make sure we do this explicitly here. At least GeneratorExit
        # is handled implicitly by the rest of the logic but we want
        # to make sure this does not regress
        raise
    except Exception:
        client.handle_exception(environ)
        raise
    except KeyboardInterrupt:
        client.handle_exception(environ)
        raise
    except SystemExit as e:
        if e.code != 0:
            client.handle_exception(environ)
        raise


class ClosingIterator(Iterator):
    """
    An iterator that is implements a ``close`` method as-per
    WSGI recommendation.
    """

    def __init__(self, sentry, iterable, environ):
        self.sentry = sentry
        self.environ = environ
        self._close = getattr(iterable, 'close', None)
        self.iterable = iter(iterable)
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            with common_exception_handling(self.environ, self.sentry):
                return next(self.iterable)
        except StopIteration:
            # We auto close here if we reach the end because some WSGI
            # middleware does not really like to close things.  To avoid
            # massive leaks we just close automatically at the end of
            # iteration.
            self.close()
            raise

    def close(self):
        if self.closed:
            return
        try:
            if self._close is not None:
                with common_exception_handling(self.environ, self.sentry):
                    self._close()
        finally:
            self.sentry.client.context.clear()
            self.sentry.client.transaction.clear()
            self.closed = True


class Sentry(object):
    """
    A WSGI middleware which will attempt to capture any
    uncaught exceptions and send them to Sentry.

    >>> from raven.base import Client
    >>> application = Sentry(application, Client())
    """

    def __init__(self, application, client=None):
        self.application = application
        if client is None:
            from raven.base import Client
            client = Client()
        self.client = client

    def __call__(self, environ, start_response):
        # TODO(dcramer): ideally this is lazy, but the context helpers must
        # support callbacks first
        self.client.http_context(self.get_http_context(environ))
        with common_exception_handling(environ, self):
            iterable = self.application(environ, start_response)
        return ClosingIterator(self, iterable, environ)

    def get_http_context(self, environ):
        return {
            'method': environ.get('REQUEST_METHOD'),
            'url': get_current_url(environ, strip_querystring=True),
            'query_string': environ.get('QUERY_STRING'),
            # TODO
            # 'data': environ.get('wsgi.input'),
            'headers': dict(get_headers(environ)),
            'env': dict(get_environ(environ)),
        }

    def handle_exception(self, environ=None):
        return self.client.captureException()
