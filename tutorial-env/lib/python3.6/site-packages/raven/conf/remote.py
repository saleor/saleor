from __future__ import absolute_import

import logging
import os
import warnings

from raven.utils.compat import PY2, text_type
from raven.exceptions import InvalidDsn
from raven.utils.encoding import to_string
from raven.utils.urlparse import parse_qsl, urlparse

ERR_UNKNOWN_SCHEME = 'Unsupported Sentry DSN scheme: {0} ({1})'

logger = logging.getLogger('raven')


def discover_default_transport():
    from raven.transport.threaded import ThreadedHTTPTransport
    from raven.transport.http import HTTPTransport

    # Google App Engine
    # https://cloud.google.com/appengine/docs/python/how-requests-are-handled#Python_The_environment
    if 'CURRENT_VERSION_ID' in os.environ and 'INSTANCE_ID' in os.environ:
        logger.info('Detected environment to be Google App Engine. Using synchronous HTTP transport.')
        return HTTPTransport

    # AWS Lambda
    # https://alestic.com/2014/11/aws-lambda-environment/
    if 'LAMBDA_TASK_ROOT' in os.environ:
        logger.info('Detected environment to be AWS Lambda. Using synchronous HTTP transport.')
        return HTTPTransport

    return ThreadedHTTPTransport


DEFAULT_TRANSPORT = discover_default_transport()


class RemoteConfig(object):
    def __init__(self, base_url=None, project=None, public_key=None,
                 secret_key=None, transport=None, options=None):
        if base_url:
            base_url = base_url.rstrip('/')
            store_endpoint = '%s/api/%s/store/' % (base_url, project)
        else:
            store_endpoint = None

        self.base_url = base_url
        self.project = project
        self.public_key = public_key
        self.secret_key = secret_key
        self.options = options or {}
        self.store_endpoint = store_endpoint

        self._transport_cls = transport or DEFAULT_TRANSPORT

    def __unicode__(self):
        return text_type(self.base_url)

    def __str__(self):
        return text_type(self.base_url)

    def is_active(self):
        return all([self.base_url, self.project, self.public_key])

    def get_transport(self):
        if not self.store_endpoint:
            return

        if not hasattr(self, '_transport'):
            self._transport = self._transport_cls(**self.options)
        return self._transport

    def get_public_dsn(self):
        url = urlparse(self.base_url)
        netloc = url.hostname
        if url.port:
            netloc += ':%s' % url.port
        return '//%s@%s%s/%s' % (self.public_key, netloc, url.path, self.project)

    @classmethod
    def from_string(cls, value, transport=None, transport_registry=None):
        # in Python 2.x sending the DSN as a unicode value will eventually
        # cause issues in httplib
        if PY2:
            value = to_string(value)

        url = urlparse(value.strip())

        if url.scheme not in ('http', 'https'):
            warnings.warn('Transport selection via DSN is deprecated. You should explicitly pass the transport class to Client() instead.')

        if transport is None:
            if not transport_registry:
                from raven.transport import TransportRegistry, default_transports
                transport_registry = TransportRegistry(default_transports)

            if not transport_registry.supported_scheme(url.scheme):
                raise InvalidDsn(ERR_UNKNOWN_SCHEME.format(url.scheme, value))

            transport = transport_registry.get_transport_cls(url.scheme)

        netloc = url.hostname
        if url.port:
            netloc += ':%s' % url.port

        path_bits = url.path.rsplit('/', 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ''
        project = path_bits[-1]

        if not all([netloc, project, url.username]):
            raise InvalidDsn('Invalid Sentry DSN: %r' % url.geturl())

        base_url = '%s://%s%s' % (url.scheme.rsplit('+', 1)[-1], netloc, path)

        return cls(
            base_url=base_url,
            project=project,
            public_key=url.username,
            secret_key=url.password,
            options=dict(parse_qsl(url.query)),
            transport=transport,
        )
