import json

from django.conf import settings
from django.db import connections, transaction


class TestDBConnectionWrapper:
    def __init__(self, conn, default_conn):
        self._wrapped_conn = conn
        self._default_conn = default_conn

    def __getattr__(self, attr):
        if attr in ["alias", "settings_dict"]:
            return getattr(self._wrapped_conn, attr)
        return getattr(self._default_conn, attr)


def prepare_test_db_connections():
    default_conn = connections["default"]
    for conn in connections.all():
        if conn.alias != settings.DATABASE_CONNECTION_DEFAULT_NAME:
            connections[conn.alias] = TestDBConnectionWrapper(conn, default_conn)  # type: ignore


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
