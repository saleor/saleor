"""
raven.transport.registry
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

# TODO(dcramer): we really should need to import all of these by default
from raven.transport.eventlet import EventletHTTPTransport
from raven.transport.exceptions import DuplicateScheme
from raven.transport.http import HTTPTransport
from raven.transport.gevent import GeventedHTTPTransport
from raven.transport.requests import RequestsHTTPTransport
from raven.transport.threaded import ThreadedHTTPTransport
from raven.transport.threaded_requests import ThreadedRequestsHTTPTransport
from raven.transport.twisted import TwistedHTTPTransport
from raven.transport.tornado import TornadoHTTPTransport
from raven.utils import urlparse


class TransportRegistry(object):
    def __init__(self, transports=None):
        # setup a default list of senders
        self._schemes = {}
        self._transports = {}

        if transports:
            for transport in transports:
                self.register_transport(transport)

    def register_transport(self, transport):
        if not hasattr(transport, 'scheme') or not hasattr(transport.scheme, '__iter__'):
            raise AttributeError('Transport %s must have a scheme list', transport.__class__.__name__)

        for scheme in transport.scheme:
            self.register_scheme(scheme, transport)

    def register_scheme(self, scheme, cls):
        """
        It is possible to inject new schemes at runtime
        """
        if scheme in self._schemes:
            raise DuplicateScheme()

        urlparse.register_scheme(scheme)
        # TODO (vng): verify the interface of the new class
        self._schemes[scheme] = cls

    def supported_scheme(self, scheme):
        return scheme in self._schemes

    def get_transport(self, parsed_url, **options):
        full_url = parsed_url.geturl()
        if full_url not in self._transports:
            # Remove the options from the parsed_url
            parsed_url = urlparse.urlparse(full_url.split('?')[0])
            self._transports[full_url] = self._schemes[parsed_url.scheme](parsed_url, **options)
        return self._transports[full_url]

    def get_transport_cls(self, scheme):
        return self._schemes[scheme]


default_transports = [
    HTTPTransport,
    ThreadedHTTPTransport,
    GeventedHTTPTransport,
    TwistedHTTPTransport,
    RequestsHTTPTransport,
    ThreadedRequestsHTTPTransport,
    TornadoHTTPTransport,
    EventletHTTPTransport,
]
