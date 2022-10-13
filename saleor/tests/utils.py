import json

from django.db import connections, transaction


def flush_post_commit_hooks():
    """Run all pending `transaction.on_commit()` callbacks.

    Forces all `on_commit()` hooks to run even if the transaction was not committed yet.
    """
    for alias in connections:
        connection = transaction.get_connection(alias)
        was_atomic = connection.in_atomic_block
        connection.in_atomic_block = False
        connection.run_and_clear_commit_hooks()
        connection.in_atomic_block = was_atomic


def dummy_editorjs(text, json_format=False):
    data = {"blocks": [{"data": {"text": text}, "type": "paragraph"}]}
    return json.dumps(data) if json_format else data
