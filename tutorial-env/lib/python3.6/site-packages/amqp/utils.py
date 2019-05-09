"""Compatibility utilities."""
from __future__ import absolute_import, unicode_literals

import logging

# enables celery 3.1.23 to start again
from vine import promise  # noqa
from vine.utils import wraps

from .five import PY3, string_t, text_t

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None   # noqa

try:
    from os import set_cloexec  # Python 3.4?
except ImportError:  # pragma: no cover
    def set_cloexec(fd, cloexec):  # noqa
        """Set flag to close fd after exec."""
        if fcntl is None:
            return
        try:
            FD_CLOEXEC = fcntl.FD_CLOEXEC
        except AttributeError:
            raise NotImplementedError(
                'close-on-exec flag not supported on this platform',
            )
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        if cloexec:
            flags |= FD_CLOEXEC
        else:
            flags &= ~FD_CLOEXEC
        return fcntl.fcntl(fd, fcntl.F_SETFD, flags)


def get_errno(exc):
    """Get exception errno (if set).

    Notes:
        :exc:`socket.error` and :exc:`IOError` first got
        the ``.errno`` attribute in Py2.7.
    """
    try:
        return exc.errno
    except AttributeError:
        try:
            # e.args = (errno, reason)
            if isinstance(exc.args, tuple) and len(exc.args) == 2:
                return exc.args[0]
        except AttributeError:
            pass
    return 0


def coro(gen):
    """Decorator to mark generator as a co-routine."""
    @wraps(gen)
    def _boot(*args, **kwargs):
        co = gen(*args, **kwargs)
        next(co)
        return co

    return _boot


if PY3:  # pragma: no cover

    def str_to_bytes(s):
        """Convert str to bytes."""
        if isinstance(s, str):
            return s.encode('utf-8', 'surrogatepass')
        return s

    def bytes_to_str(s):
        """Convert bytes to str."""
        if isinstance(s, bytes):
            return s.decode('utf-8', 'surrogatepass')
        return s
else:

    def str_to_bytes(s):                # noqa
        """Convert str to bytes."""
        if isinstance(s, text_t):
            return s.encode('utf-8')
        return s

    def bytes_to_str(s):                # noqa
        """Convert bytes to str."""
        return s


class NullHandler(logging.Handler):
    """A logging handler that does nothing."""

    def emit(self, record):
        pass


def get_logger(logger):
    """Get logger by name."""
    if isinstance(logger, string_t):
        logger = logging.getLogger(logger)
    if not logger.handlers:
        logger.addHandler(NullHandler())
    return logger
