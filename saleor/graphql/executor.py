from graphql.execution import executor

original_complete_value_catching_error = executor.complete_value_catching_error


def _patched_complete_value_catching_error(*args, **kwargs):
    info = args[3]
    from saleor.core.db.connection import allow_writer_in_context

    with allow_writer_in_context(info.context):
        return original_complete_value_catching_error(*args, **kwargs)


def patch_executor():
    """Patch `complete_value_catching_error` function to allow writer DB in mutations.

    Patch the GraphQL executor's `complete_value_catching_error` function to wrap each
    call with `allow_writer_in_context`. This allows to safely use writer DB in
    mutations, while it will raise or log error when a resolver is run in a query.
    """

    executor.complete_value_catching_error = _patched_complete_value_catching_error
