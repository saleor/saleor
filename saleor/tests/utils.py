import json
import math
from decimal import Decimal

from django.conf import settings
from django.db import connections, transaction


class TestDBConnectionWrapper:
    def __init__(self, conn, default_conn):
        self._wrapped_conn = conn
        self._default_conn = default_conn

    def cursor(self, *args, **kwargs):
        cursor = self._default_conn.cursor(*args, **kwargs)
        cursor.db = self
        return cursor

    def chunked_cursor(self, *args, **kwargs):
        cursor = self._default_conn.chunked_cursor(*args, **kwargs)
        cursor.db = self
        return cursor

    def __getattr__(self, attr):
        if attr in ["alias", "settings_dict"]:
            return getattr(self._wrapped_conn, attr)
        return getattr(self._default_conn, attr)


def prepare_test_db_connections():
    replica = settings.DATABASE_CONNECTION_REPLICA_NAME
    default_conn = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]
    connections[replica] = TestDBConnectionWrapper(connections[replica], default_conn)  # type: ignore


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
