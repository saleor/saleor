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
