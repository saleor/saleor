import logging
import traceback
from contextlib import contextmanager

from django.conf import settings
from django.core.management.color import color_style
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper

from ...graphql.core.context import SaleorContext, get_database_connection_name

logger = logging.getLogger(__name__)

writer = settings.DATABASE_CONNECTION_DEFAULT_NAME
replica = settings.DATABASE_CONNECTION_REPLICA_NAME

# Limit the number of frames in the traceback in `log_writer_usage_middleware` to avoid
# excessive log size.
TRACEBACK_LIMIT = 20

UNSAFE_WRITER_ACCESS_MSG = (
    "Unsafe access to the writer DB detected. Call `using()` on the `QuerySet` "
    "to utilize a replica DB, or employ the `allow_writer` context manager to "
    "explicitly permit access to the writer."
)


class UnsafeDBUsageError(Exception):
    pass


class UnsafeWriterAccessError(UnsafeDBUsageError):
    pass


class UnsafeReplicaUsageError(UnsafeDBUsageError):
    pass


@contextmanager
def allow_writer():
    """Context manager that allows write access to the default database connection.

    This context manager works in conjunction with the `restrict_writer_middleware` and
    `log_writer_usage_middleware` middlewares. If any of these middlewares are enabled,
    use the `allow_writer` context manager to allow write access to the default
    database. Otherwise an error will be raised or a log message will be emitted.
    """

    default_connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]

    # Check if we are already in an allow_writer block. If so we don't need to do
    # anything and we don't have to close access to the writer at the end.
    in_allow_writer_block = getattr(default_connection, "_allow_writer", False)
    if not in_allow_writer_block:
        setattr(default_connection, "_allow_writer", True)
    try:
        yield
    finally:
        if not in_allow_writer_block:
            # Close writer access when exiting the outermost allow_writer block.
            setattr(default_connection, "_allow_writer", False)


@contextmanager
def allow_writer_in_context(context: SaleorContext):
    """Context manager that allows write access to the default database connection in a context (SaleorContext).

    This is a helper context manager that conditionally allows write access based on the
    database connection name in the given context.
    """
    conn_name = get_database_connection_name(context)
    if conn_name == settings.DATABASE_CONNECTION_DEFAULT_NAME:
        with allow_writer():
            yield
    else:
        yield


def restrict_writer_middleware(get_response):
    """Middleware that restricts write access to the default database connection.

    This middleware will raise an error if a write operation is attempted on the default
    database connection. To allow writes, use the `allow_writer` context manager. Make
    sure that writer is not used accidentally and always use the `using` queryset method
    with proper database connection name.
    """

    def middleware(request):
        with connections[writer].execute_wrapper(_restrict_writer):
            with connections[replica].execute_wrapper(_restrict_writer):
                return get_response(request)

    return middleware


def _restrict_writer(execute, sql, params, many, context):
    conn: BaseDatabaseWrapper = context["connection"]
    allow_writer = getattr(conn, "_allow_writer", False)
    if conn.alias == writer and not allow_writer:
        raise UnsafeWriterAccessError(f"{UNSAFE_WRITER_ACCESS_MSG} SQL: {sql}")
    return execute(sql, params, many, context)


def log_writer_usage_middleware(get_response):
    """Middleware that logs write access to the default database connection.

    This is similar to the `restrict_writer_middleware` middleware, but instead of
    raising an error, it logs a message when a write operation is attempted on the
    default database connection.
    """

    def middleware(request):
        with connections[writer].execute_wrapper(_log_writer_usage):
            return get_response(request)

    return middleware


def _log_writer_usage(execute, sql, params, many, context):
    conn: BaseDatabaseWrapper = context["connection"]
    allow_writer = getattr(conn, "_allow_writer", False)
    if conn.alias == writer and not allow_writer:
        stack_trace = traceback.extract_stack(limit=TRACEBACK_LIMIT)
        error_msg = color_style().NOTICE(UNSAFE_WRITER_ACCESS_MSG)
        log_msg = (
            f"{error_msg} SQL: {sql} \n"
            f"Traceback: \n{''.join(traceback.format_list(stack_trace))}"
        )
        logger.warning(log_msg)
    return execute(sql, params, many, context)
