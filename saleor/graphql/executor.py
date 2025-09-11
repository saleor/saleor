from graphql_core_promise import PromiseExecutionContext


def wrap_complete_func(complete_func):
    def wrapped_func(*args, **kwargs):
        info = args[3]
        from saleor.core.db.connection import allow_writer_in_context

        with allow_writer_in_context(info.context):
            return complete_func(*args, **kwargs)

    return wrapped_func


def patch_executor():
    """Patch `complete_value_catching_error` function to allow writer DB in mutations.

    The `complete_value_catching_error` function is called when resolving a field in
    GraphQL. This patch wraps each call with `allow_writer_in_context` context manager.
    This allows to use writer DB in resolvers, when they are called via mutation, while
    they will still raise or log error when a resolver is run in a query.
    """

    PromiseExecutionContext.complete_object_value = wrap_complete_func(
        PromiseExecutionContext.complete_object_value
    )
