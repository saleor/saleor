from contextlib import contextmanager

from django.db import DatabaseError

from ..core.tracing import traced_atomic_transaction


@contextmanager
def transaction_with_commit_on_errors():
    """Perform transaction and raise an error in any occurred."""
    error = None
    with traced_atomic_transaction():
        try:
            yield
        except DatabaseError:
            raise
        except Exception as e:
            error = e
    if error:
        raise error
