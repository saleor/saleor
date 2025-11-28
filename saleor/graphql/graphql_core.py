from graphql.execution import executor
from graphql.execution.base import ExecutionResult

original_complete_value_catching_error = executor.complete_value_catching_error


def _patched_complete_value_catching_error(*args, **kwargs):
    info = args[3]
    from saleor.core.db.connection import allow_writer_in_context

    with allow_writer_in_context(info.context):
        return original_complete_value_catching_error(*args, **kwargs)


def patch_executor():
    """Patch `complete_value_catching_error` function to allow writer DB in mutations.

    The `complete_value_catching_error` function is called when resolving a field in
    GraphQL. This patch wraps each call with `allow_writer_in_context` context manager.When a ValidationError is raised, the execution context does not store the error.
    This allows to use writer DB in resolvers, when they are called via mutation, while
    they will still raise or log error when a resolver is run in a query.
    """

    executor.complete_value_catching_error = _patched_complete_value_catching_error


def __del_execution_context__(self):
    # When a `ValidationError` is raised, the execution context does not store the error.
    if hasattr(self, "errors"):
        del self.errors


def patch_execution_context():
    """Patch `__del__` method of `ExecutionContext` to delete `errors` attribute.

    The `errors` attribute is used to store errors that occurred during the execution
    of the query. This patch ensures that the attribute is deleted when the execution
    context is deleted. This is to avoid reference cycles, as the attribute can hold
    references to objects that are no longer needed.
    """
    executor.ExecutionContext.__del__ = __del_execution_context__  # type: ignore[attr-defined]


def __del_execution_result__(self):
    del self.errors


def patch_execution_result():
    """Patch `__del__` method of `ExecutionResult` to delete `errors` attribute.

    The `errors` attribute is used to store errors that occurred during the execution
    of the query. This patch ensures that the attribute is deleted when the execution
    result is deleted. This is to avoid reference cycles, as the attribute can hold
    references to objects that are no longer needed.
    """

    ExecutionResult.__del__ = __del_execution_result__  # type: ignore[attr-defined]
