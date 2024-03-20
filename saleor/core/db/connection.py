import logging
import traceback
from contextlib import contextmanager

import sqlparse
from django.conf import settings
from django.core.management.color import color_style
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper

from ...graphql.core.context import SaleorContext, get_database_connection_name

logger = logging.getLogger(__name__)

writer = settings.DATABASE_CONNECTION_DEFAULT_NAME
replica = settings.DATABASE_CONNECTION_REPLICA_NAME


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


def restrict_writer_middleware(get_response):
    """Middleware that restricts write access to the default database connection.

    This middleware will raise an error or log a warning if a write operation is
    attempted on the default database connection. To allow writes, use the
    `allow_writer` context manager or the `using` queryset method.
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
        raise UnsafeWriterAccessError(
            f"Unsafe writer DB access, use `allow_writer` context manager. SQL: {sql}"
        )
    elif conn.alias == replica:
        if not _is_read_only_query(sql):
            raise UnsafeReplicaUsageError(f"Unsafe replica usage. SQL: {sql}")
    return execute(sql, params, many, context)


def _is_read_only_query(sql_query: str) -> bool:
    for query in sqlparse.parse(sql_query):
        query_type = query.get_type().upper()
        if query_type != "SELECT":
            return False
    return True


def log_writer_usage_middleware(get_response):
    def middleware(request):
        with connections[writer].execute_wrapper(_log_writer_usage):
            return get_response(request)

    return middleware


def _log_writer_usage(execute, sql, params, many, context):
    conn: BaseDatabaseWrapper = context["connection"]
    allow_writer = getattr(conn, "_allow_writer", False)
    if conn.alias == writer and not allow_writer:
        stack_trace = traceback.extract_stack(limit=20)
        error_msg = color_style().NOTICE(
            "Unsafe writer DB access, use `allow_writer` context manager."
        )
        log_msg = (
            f"{error_msg} SQL: {sql} \n"
            f"Traceback: \n{''.join(traceback.format_list(stack_trace))}"
        )
        logger.error(log_msg)
    return execute(sql, params, many, context)


@contextmanager
def allow_writer_in_context(context: SaleorContext):
    conn_name = get_database_connection_name(context)
    if conn_name == settings.DATABASE_CONNECTION_DEFAULT_NAME:
        with allow_writer():
            yield
    else:
        yield
