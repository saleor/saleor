"""
raven.transport.eventlet
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import sys

from raven.transport.http import HTTPTransport

try:
    import eventlet
    try:
        from eventlet.green import urllib2 as eventlet_urllib2
    except ImportError:
        from eventlet.green.urllib import request as eventlet_urllib2
    has_eventlet = True
except ImportError:
    has_eventlet = False


class EventletHTTPTransport(HTTPTransport):

    scheme = ['eventlet+http', 'eventlet+https']

    def __init__(self, pool_size=100, **kwargs):
        if not has_eventlet:
            raise ImportError('EventletHTTPTransport requires eventlet.')
        super(EventletHTTPTransport, self).__init__(**kwargs)

    def _send_payload(self, payload):
        url, data, headers = payload
        req = eventlet_urllib2.Request(url, headers=headers)
        try:
            if sys.version_info < (2, 6):
                response = eventlet_urllib2.urlopen(req, data).read()
            else:
                response = eventlet_urllib2.urlopen(req, data,
                                                    self.timeout).read()
            return response
        except Exception as err:
            return err

    def send(self, url, data, headers):
        """
        Spawn an async request to a remote webserver.
        """
        eventlet.spawn(self._send_payload, (url, data, headers))
