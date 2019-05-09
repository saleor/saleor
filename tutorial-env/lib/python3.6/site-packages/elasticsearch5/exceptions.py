__all__ = [
    'ImproperlyConfigured', 'ElasticsearchException', 'SerializationError',
    'TransportError', 'NotFoundError', 'ConflictError', 'RequestError', 'ConnectionError',
    'SSLError', 'ConnectionTimeout', 'AuthenticationException', 'AuthorizationException'
]

class ImproperlyConfigured(Exception):
    """
    Exception raised when the config passed to the client is inconsistent or invalid.
    """


class ElasticsearchException(Exception):
    """
    Base class for all exceptions raised by this package's operations (doesn't
    apply to :class:`~elasticsearch.ImproperlyConfigured`).
    """


class SerializationError(ElasticsearchException):
    """
    Data passed in failed to serialize properly in the ``Serializer`` being
    used.
    """


class TransportError(ElasticsearchException):
    """
    Exception raised when ES returns a non-OK (>=400) HTTP status code. Or when
    an actual connection error happens; in that case the ``status_code`` will
    be set to ``'N/A'``.
    """
    @property
    def status_code(self):
        """
        The HTTP status code of the response that precipitated the error or
        ``'N/A'`` if not applicable.
        """
        return self.args[0]

    @property
    def error(self):
        """ A string error message. """
        return self.args[1]

    @property
    def info(self):
        """ Dict of returned error info from ES, where available. """
        return self.args[2]

    def __str__(self):
        cause = ''
        try:
            if self.info:
                cause = ', %r' % self.info['error']['root_cause'][0]['reason']
        except LookupError:
            pass
        return 'TransportError(%s, %r%s)' % (self.status_code, self.error, cause)


class ConnectionError(TransportError):
    """
    Error raised when there was an exception while talking to ES. Original
    exception from the underlying :class:`~elasticsearch.Connection`
    implementation is available as ``.info.``
    """
    def __str__(self):
        return 'ConnectionError(%s) caused by: %s(%s)' % (
            self.error, self.info.__class__.__name__, self.info)


class SSLError(ConnectionError):
    """ Error raised when encountering SSL errors. """


class ConnectionTimeout(ConnectionError):
    """ A network timeout. Doesn't cause a node retry by default. """
    def __str__(self):
        return 'ConnectionTimeout caused by - %s(%s)' % (
            self.info.__class__.__name__, self.info)


class NotFoundError(TransportError):
    """ Exception representing a 404 status code. """


class ConflictError(TransportError):
    """ Exception representing a 409 status code. """


class RequestError(TransportError):
    """ Exception representing a 400 status code. """


class AuthenticationException(TransportError):
    """ Exception representing a 401 status code. """


class AuthorizationException(TransportError):
    """ Exception representing a 403 status code. """

# more generic mappings from status_code to python exceptions
HTTP_EXCEPTIONS = {
    400: RequestError,
    401: AuthenticationException,
    403: AuthorizationException,
    404: NotFoundError,
    409: ConflictError,
}
