import json
import math
from decimal import Decimal

from django.conf import settings
from django.db import connections, transaction

from ..core.db.connection import allow_writer


class FakeDbReplicaConnection:
    """A class used to create a fake replica DB connection for use in tests.

    This class serves as a wrapper around the writer DB connection (alias "default")
    that simulates a replica DB connection by identifying itself with a replica alias
    and overriding cursor creation methods. It effectively results in one DB connection
    identified by two separate aliases, but with shared transactions.
    """

    def __init__(self, replica_conn):
        self.replica_conn = replica_conn
        self.writer_conn = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]

    def cursor(self, *args, **kwargs):
        with allow_writer():
            # Cursor creation is wrapped in allow_writer as it is effectively created
            # using the writer DB connection
            cursor = self.writer_conn.cursor(*args, **kwargs)
            cursor.db = self
        return cursor

    def chunked_cursor(self, *args, **kwargs):
        with allow_writer():
            # Cursor creation is wrapped in allow_writer as it is effectively created
            # using the writer DB connection
            cursor = self.writer_conn.chunked_cursor(*args, **kwargs)
            cursor.db = self
        return cursor

    def __getattr__(self, attr):
        if attr == "alias":
            return getattr(self.replica_conn, attr)
        return getattr(self.writer_conn, attr)


def prepare_test_db_connections():
    """Override the replica DB connection with a fake one for testing purposes.

    This function allows simulation of replica DB usage in tests while using Django's
    TestCase, avoiding the need for the slower TransactionTestCase. For more details,
    refer to the Django documentation:
    https://docs.djangoproject.com/en/4.2/topics/testing/advanced/#testing-primary-replica-configurations
    """
    replica = settings.DATABASE_CONNECTION_REPLICA_NAME
    connections[replica] = FakeDbReplicaConnection(connections[replica])  # type: ignore


def flush_post_commit_hooks():
    """Run all pending `transaction.on_commit()` callbacks.

    Forces all `on_commit()` hooks to run even if the transaction was not committed yet.
    """
    connection = transaction.get_connection(settings.DATABASE_CONNECTION_DEFAULT_NAME)
    was_atomic = connection.in_atomic_block
    was_commit_on_exit = connection.commit_on_exit
    connection.in_atomic_block = False
    connection.run_and_clear_commit_hooks()
    connection.in_atomic_block = was_atomic
    connection.commit_on_exit = was_commit_on_exit


def dummy_editorjs(text, json_format=False):
    data = {"blocks": [{"data": {"text": text}, "type": "paragraph"}]}
    return json.dumps(data) if json_format else data


def round_down(price: Decimal) -> Decimal:
    return Decimal(math.floor(price * 100)) / 100


def round_up(price: Decimal) -> Decimal:
    return Decimal(math.ceil(price * 100)) / 100
