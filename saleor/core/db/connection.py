import logging
from contextlib import contextmanager

import sqlparse
from django.conf import settings
from django.core.management.color import color_style
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper

logger = logging.getLogger(__name__)


class UnsafeDBUsageError(Exception):
    pass


class UnsafeWriterAccessError(UnsafeDBUsageError):
    pass


class UnsafeReplicaUsageError(UnsafeDBUsageError):
    pass


@contextmanager
def allow_writer():
    from django.db import connections

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


def is_read_only_query(sql_query: str) -> bool:
    for query in sqlparse.parse(sql_query):
        query_type = query.get_type().upper()
        if query_type != "SELECT":
            return False
    return True


writer = settings.DATABASE_CONNECTION_DEFAULT_NAME
replica = settings.DATABASE_CONNECTION_REPLICA_NAME


def restrict_writer(execute, sql, params, many, context):
    conn: BaseDatabaseWrapper = context["connection"]
    allow_writer = getattr(conn, "_allow_writer", False)
    if conn.alias == writer and not allow_writer:
        raise UnsafeWriterAccessError(
            f"Unsafe writer DB access. Use `allow_writer` context manager: {sql}"
        )
    elif conn.alias == replica:
        if not is_read_only_query(sql):
            raise UnsafeReplicaUsageError(f"Unsafe replica usage: {sql}")
    return execute(sql, params, many, context)


def log_writer_usage(execute, sql, params, many, context):
    conn: BaseDatabaseWrapper = context["connection"]
    allow_writer = getattr(conn, "_allow_writer", False)
    if conn.alias == writer and not allow_writer:
        msg = "Unsafe writer DB access. Use `allow_writer` context manager."
        logger.error("%s %s", color_style().NOTICE(msg), sql)
    return execute(sql, params, many, context)


def restrict_writer_middleware(get_response):
    """Middleware that restricts write access to the default database connection.

    This middleware will raise an error or log a warning if a write operation is
    attempted on the default database connection. To allow writes, use the
    `allow_writer` context manager or the `using` queryset method.
    """

    def middleware(request):
        with connections[writer].execute_wrapper(restrict_writer):
            with connections[replica].execute_wrapper(restrict_writer):
                return get_response(request)

    return middleware


def log_writer_usage_middleware(get_response):
    def middleware(request):
        with connections[writer].execute_wrapper(log_writer_usage):
            return get_response(request)

    return middleware
