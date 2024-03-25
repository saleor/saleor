from unittest.mock import patch

import pytest
from django.db import connections

from ....graphql.context import SaleorContext
from ....tests.models import Book
from ..connection import (
    UnsafeWriterAccessError,
    _log_writer_usage,
    _restrict_writer,
    allow_writer,
    allow_writer_in_context,
)


def test_allow_writer(settings):
    default_connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]
    assert not getattr(default_connection, "_allow_writer", False)

    with allow_writer():
        assert hasattr(default_connection, "_allow_writer")
        assert default_connection._allow_writer


def test_allow_writer_yield_exception(settings):
    default_connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]

    def example_function():
        raise Exception()

    try:
        with allow_writer():
            example_function()
    except Exception:
        pass

    assert hasattr(default_connection, "_allow_writer")
    assert not default_connection._allow_writer


def test_allow_writer_in_context_writer(settings):
    context = SaleorContext()
    context.allow_replica = False

    with allow_writer_in_context(context):
        connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]
        assert hasattr(connection, "_allow_writer")
        assert connection._allow_writer


@patch("saleor.core.db.connection.get_database_connection_name")
def test_allow_writer_in_context_replica(mocked_get_database_connection_name, settings):
    mocked_get_database_connection_name.return_value = "replica"

    context = SaleorContext()
    context.allow_replica = True

    with allow_writer_in_context(context):
        connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]
        assert not getattr(connection, "_allow_writer")


def test_restrict_writer_raises_error(settings):
    connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]

    with pytest.raises(UnsafeWriterAccessError):
        with connection.execute_wrapper(_restrict_writer):
            Book.objects.first()


def test_restrict_writer_in_allow_writer(settings):
    connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]

    with connection.execute_wrapper(_restrict_writer):
        with allow_writer():
            Book.objects.first()


def test_log_writer_usage(settings, caplog):
    connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]

    with connection.execute_wrapper(_log_writer_usage):
        Book.objects.first()

    assert caplog.records
    msg = caplog.records[0].getMessage()
    assert "Unsafe access to the writer DB detected" in msg
