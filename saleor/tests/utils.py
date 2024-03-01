import json

from django.conf import settings
from django.db import connections, transaction
from django.db.backends.base.base import BaseDatabaseWrapper


class FakeReplicaDBConnection:
    def __init__(
        self, replica_conn: BaseDatabaseWrapper, writer_conn: BaseDatabaseWrapper
    ):
        self._replica_conn = replica_conn
        self._writer_conn = writer_conn

    def cursor(self):
        cursor = self._writer_conn.cursor()
        cursor.db = self
        return cursor

    def chunked_cursor(self):
        cursor = self._writer_conn.chunked_cursor()
        cursor.db = self
        return cursor

    def __getattr__(self, attr):
        if attr in ["alias", "settings_dict"]:
            return getattr(self._replica_conn, attr)
        return getattr(self._writer_conn, attr)


def prepare_test_db_connections():
    replica = settings.DATABASE_CONNECTION_REPLICA_NAME
    default_conn = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]
    connections[replica] = FakeReplicaDBConnection(connections[replica], default_conn)  # type: ignore[override]


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
