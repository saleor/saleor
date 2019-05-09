"""
raven.transport.requests
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.http import HTTPTransport

try:
    import requests
    has_requests = True
except ImportError:
    has_requests = False


class RequestsHTTPTransport(HTTPTransport):

    scheme = ['requests+http', 'requests+https']

    def __init__(self, *args, **kwargs):
        if not has_requests:
            raise ImportError('RequestsHTTPTransport requires requests.')

        super(RequestsHTTPTransport, self).__init__(*args, **kwargs)

    def send(self, url, data, headers):
        if self.verify_ssl:
            # If SSL verification is enabled use the provided CA bundle to
            # perform the verification.
            self.verify_ssl = self.ca_certs
        requests.post(url, data=data, headers=headers,
                      verify=self.verify_ssl, timeout=self.timeout)
