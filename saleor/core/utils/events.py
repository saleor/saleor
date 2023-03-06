from django.db import transaction


def call_event(func_obj, *func_args):
    """Call webhook event with given args.

    Ensures that in atomic transaction event is called on_commit.
    """
    connection = transaction.get_connection()
    if connection.in_atomic_block:
        transaction.on_commit(lambda: func_obj(*func_args))
    else:
        func_obj(*func_args)
