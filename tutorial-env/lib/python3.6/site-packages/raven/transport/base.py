"""
raven.transport.base
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import


# Helper for external transports
has_newstyle_transports = True


class Transport(object):
    """
    All transport implementations need to subclass this class

    You must implement a send method (or an async_send method if
    sub-classing AsyncTransport).
    """

    is_async = False
    scheme = []

    def send(self, url, data, headers):
        """
        You need to override this to do something with the actual
        data. Usually - this is sending to a server
        """
        raise NotImplementedError


class AsyncTransport(Transport):
    """
    All asynchronous transport implementations should subclass this
    class.

    You must implement a async_send method.
    """

    is_async = True

    def async_send(self, url, data, headers, success_cb, error_cb):
        """
        Override this method for asynchronous transports. Call
        `success_cb()` if the send succeeds or `error_cb(exception)`
        if the send fails.
        """
        raise NotImplementedError
