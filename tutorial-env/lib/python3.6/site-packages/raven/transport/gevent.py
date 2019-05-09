"""
raven.transport.gevent
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport

try:
    import gevent
    # gevent 1.0bN renamed coros to lock
    try:
        from gevent.lock import Semaphore
    except ImportError:
        from gevent.coros import Semaphore  # NOQA
    has_gevent = True
except ImportError:
    has_gevent = None


class GeventedHTTPTransport(AsyncTransport, HTTPTransport):

    scheme = ['gevent+http', 'gevent+https']

    def __init__(self, maximum_outstanding_requests=100, *args, **kwargs):
        if not has_gevent:
            raise ImportError('GeventedHTTPTransport requires gevent.')

        self._lock = Semaphore(maximum_outstanding_requests)

        super(GeventedHTTPTransport, self).__init__(*args, **kwargs)

    def async_send(self, url, data, headers, success_cb, failure_cb):
        """
        Spawn an async request to a remote webserver.
        """
        # this can be optimized by making a custom self.send that does not
        # read the response since we don't use it.
        self._lock.acquire()
        return gevent.spawn(
            super(GeventedHTTPTransport, self).send, url, data, headers
        ).link(lambda x: self._done(x, success_cb, failure_cb))

    def _done(self, greenlet, success_cb, failure_cb, *args):
        self._lock.release()
        if greenlet.successful():
            success_cb()
        else:
            failure_cb(greenlet.exception)
