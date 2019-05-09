"""Exceptions."""
from __future__ import absolute_import, unicode_literals

from socket import timeout as TimeoutError  # noqa

from amqp import ChannelError, ConnectionError, ResourceError

from kombu.five import python_2_unicode_compatible

__all__ = (
    'KombuError', 'OperationalError',
    'NotBoundError', 'MessageStateError', 'TimeoutError',
    'LimitExceeded', 'ConnectionLimitExceeded',
    'ChannelLimitExceeded', 'ConnectionError', 'ChannelError',
    'VersionMismatch', 'SerializerNotInstalled', 'ResourceError',
    'SerializationError', 'EncodeError', 'DecodeError', 'HttpError',
    'InconsistencyError',
)


class KombuError(Exception):
    """Common subclass for all Kombu exceptions."""


class OperationalError(KombuError):
    """Recoverable message transport connection error."""


class SerializationError(KombuError):
    """Failed to serialize/deserialize content."""


class EncodeError(SerializationError):
    """Cannot encode object."""


class DecodeError(SerializationError):
    """Cannot decode object."""


class NotBoundError(KombuError):
    """Trying to call channel dependent method on unbound entity."""


class MessageStateError(KombuError):
    """The message has already been acknowledged."""


class LimitExceeded(KombuError):
    """Limit exceeded."""


class ConnectionLimitExceeded(LimitExceeded):
    """Maximum number of simultaneous connections exceeded."""


class ChannelLimitExceeded(LimitExceeded):
    """Maximum number of simultaneous channels exceeded."""


class VersionMismatch(KombuError):
    """Library dependency version mismatch."""


class SerializerNotInstalled(KombuError):
    """Support for the requested serialization type is not installed."""


class ContentDisallowed(SerializerNotInstalled):
    """Consumer does not allow this content-type."""


class InconsistencyError(ConnectionError):
    """Data or environment has been found to be inconsistent.

    Depending on the cause it may be possible to retry the operation.
    """


@python_2_unicode_compatible
class HttpError(Exception):
    """HTTP Client Error."""

    def __init__(self, code, message=None, response=None):
        self.code = code
        self.message = message
        self.response = response
        super(HttpError, self).__init__(code, message, response)

    def __str__(self):
        return 'HTTP {0.code}: {0.message}'.format(self)
