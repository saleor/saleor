import json
import math
from decimal import Decimal

from django.conf import settings
from django.db import connections

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
    connections[replica] = FakeDbReplicaConnection(connections[replica])  # type: ignore[assignment]


def dummy_editorjs(text, json_format=False):
    data = {"blocks": [{"data": {"text": text}, "type": "paragraph"}]}
    return json.dumps(data) if json_format else data


def round_down(price: Decimal) -> Decimal:
    return Decimal(math.floor(price * 100)) / 100


def round_up(price: Decimal) -> Decimal:
    return Decimal(math.ceil(price * 100)) / 100
