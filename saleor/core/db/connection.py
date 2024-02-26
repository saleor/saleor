import logging
from contextlib import contextmanager
from typing import Any

from django.conf import settings
from django.core.management.color import color_style
from django.db.backends.utils import CursorWrapper

logger = logging.getLogger(__name__)


@contextmanager
def allow_writer():
    from django.db import connections

    default_connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]

    # Check if we are already in an allow_writer block. If so we don't need to do
    # anything and we don't have to close access to the writer at the end.
    in_allow_writer_block = getattr(default_connection, "_allow_writer", False)
    if not in_allow_writer_block:
        setattr(default_connection, "_allow_writer", True)

    yield

    if not in_allow_writer_block:
        # Close writer access when exiting the outermost allow_writer block.
        setattr(default_connection, "_allow_writer", False)


def restrict_writer_middleware(get_response):
    """Middleware that restricts write access to the default database connection.

    This middleware will raise an error or log a warning if a write operation is
    attempted on the default database connection. To allow writes, use the
    `allow_writer` context manager or the `using` queryset method.
    """

    def middleware(request):
        from django.db import connections

        default_connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]
        _wrap_connection(default_connection)

        response = get_response(request)
        return response

    return middleware


def _wrap_connection(connection):
    if not hasattr(connection, "_orig_cursor"):
        connection._orig_cursor = connection.cursor

        def cursor(*args, **kwargs):
            orig_cursor = connection._orig_cursor(*args, **kwargs)
            PatchedCursor = _apply_mixin(orig_cursor.__class__, RestrictWriterWrapper)
            return PatchedCursor(orig_cursor.cursor, connection)

        connection.cursor = cursor


class UnsafeWriterAccessError(Exception):
    pass


class RestrictWriterWrapper(CursorWrapper):
    def _add_logger(self, method, sql, params):
        alias = self.db.alias
        allow_writer = getattr(self.db, "_allow_writer", False)
        if alias == settings.DATABASE_CONNECTION_DEFAULT_NAME and not allow_writer:
            if settings.RESTRICT_WRITER_RAISE_ERROR:
                raise UnsafeWriterAccessError(
                    "Unsafe writer DB access. Use `allow_writer` context manager or "
                    f"`using()` queryset method: {sql}"
                )
            else:
                msg = (
                    "Unsafe writer DB access. Use `allow_writer` context manager or "
                    "`using()` queryset method: "
                )
                logger.error("%s %s", color_style().NOTICE(msg), sql)
        return method(sql, params)

    def execute(self, sql, params=None):
        return self._add_logger(super().execute, sql, params)

    def executemany(self, sql, param_list):
        return self._add_logger(super().executemany, sql, param_list)


def _apply_mixin(base_wrapper: Any, mixin: Any):
    class _RestrictWriterWrapper(mixin, base_wrapper):
        # Purpose of this class is to combine the mixin and the base_wrapper together.
        pass

    return _RestrictWriterWrapper
